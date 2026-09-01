"""Prepare reusable, locator-preserving evidence packs with zero third-party dependencies.

The tool reduces repeated LLM input. It does not replace source acquisition or completeness
checks. Full mode emits every chunk once in bounded batches. Selective mode emits ranked chunks
plus structural coverage and must widen when evidence remains incomplete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


PACK_SCHEMA = "3rdbrain.evidence-pack.v1"
CACHE_SCHEMA = "3rdbrain.evidence-cache.v1"
LEDGER_SCHEMA = "3rdbrain.evidence-ledger.v1"
RECEIPT_SCHEMA = "3rdbrain.efficiency-receipt.v1"
PIPELINE_VERSION = "1"
DEFAULT_MAX_CHARS = 2400
DEFAULT_BATCH_TOKENS = 6000
DEFAULT_TOP = 8
KINDS = {
    "video",
    "web",
    "repository",
    "social",
    "document",
    "image",
    "audio",
    "interactive",
    "note",
}

TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.+#][a-z0-9]+)?", re.IGNORECASE)
TIMESTAMP_RE = re.compile(
    r"(?:^|\[|\s)(?P<time>(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)(?:\]|\s|$)"
)
VTT_RE = re.compile(r"^(?P<start>\d{1,2}:\d{2}(?::\d{2})?[.,]\d{1,3})\s+-->")
HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
DOCUMENT_LOCATOR_RE = re.compile(
    r"^(?P<label>(?:page|slide|sheet|chapter|section)\s+[^:]{1,80})(?::|$)", re.IGNORECASE
)
SECRET_QUERY_PARTS = ("token", "key", "secret", "signature", "credential", "auth", "expires")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "with",
}


def estimated_tokens(value: str) -> int:
    return math.ceil(len(value) / 4)


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_key(digest: str, kind: str, pipeline_version: str) -> str:
    payload = f"{CACHE_SCHEMA}\0{pipeline_version}\0{kind}\0{digest}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def redact_source(source: str) -> str:
    """Remove likely credentials from a source URL before it enters a receipt or pack."""
    try:
        parsed = urlsplit(source)
    except ValueError:
        return source
    if parsed.scheme not in {"http", "https"}:
        return Path(source).name if source else source
    query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if any(part in key.lower() for part in SECRET_QUERY_PARTS):
            query.append((key, "REDACTED"))
        else:
            query.append((key, value))
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit((parsed.scheme, f"{hostname}{port}", parsed.path, urlencode(query), ""))


def tokenize(value: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(value) if token.lower() not in STOP_WORDS]


def locator_from_line(line: str, line_number: int) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    if match := VTT_RE.match(stripped):
        return match.group("start").replace(",", ".")
    if match := HEADING_RE.match(stripped):
        return match.group("title").strip()
    if match := DOCUMENT_LOCATOR_RE.match(stripped):
        return match.group("label").strip()
    if match := TIMESTAMP_RE.search(stripped):
        return match.group("time").replace(",", ".")
    return None


@dataclass(frozen=True, slots=True)
class Block:
    locator: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True, slots=True)
class Chunk:
    identifier: str
    locator: str
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.identifier,
            "locator": self.locator,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "estimated_tokens": estimated_tokens(self.text),
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Chunk":
        return cls(
            identifier=str(value["id"]),
            locator=str(value["locator"]),
            start_line=int(value["start_line"]),
            end_line=int(value["end_line"]),
            text=str(value["text"]),
        )


def parse_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    buffer: list[str] = []
    current_locator = "line 1"
    start_line = 1
    in_fence = False

    def flush(end_line: int) -> None:
        nonlocal buffer, current_locator, start_line
        body = "\n".join(buffer).strip()
        if body:
            blocks.append(Block(current_locator, start_line, max(start_line, end_line), body))
        buffer = []

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        is_fence = stripped.startswith("```") or stripped.startswith("~~~")
        detected = None if in_fence else locator_from_line(line, line_number)
        if detected and buffer:
            flush(line_number - 1)
            current_locator = detected
            start_line = line_number
        elif detected:
            current_locator = detected
            start_line = line_number

        if not stripped and buffer and not in_fence:
            flush(line_number - 1)
            current_locator = f"line {line_number + 1}"
            start_line = line_number + 1
            continue

        if stripped or buffer:
            buffer.append(line)
        if is_fence:
            in_fence = not in_fence

    flush(len(lines))
    return blocks


def split_large_block(block: Block, maximum_chars: int) -> list[Block]:
    if len(block.text) <= maximum_chars:
        return [block]
    lines = block.text.splitlines() or [block.text]
    pieces: list[Block] = []
    buffer: list[str] = []
    part_start = block.start_line
    part_number = 1
    for offset, line in enumerate(lines):
        projected = len("\n".join((*buffer, line)))
        if buffer and projected > maximum_chars:
            end = block.start_line + offset - 1
            pieces.append(
                Block(f"{block.locator} part {part_number}", part_start, end, "\n".join(buffer))
            )
            buffer = []
            part_start = block.start_line + offset
            part_number += 1
        if len(line) > maximum_chars and not buffer:
            for start in range(0, len(line), maximum_chars):
                pieces.append(
                    Block(
                        f"{block.locator} part {part_number}",
                        block.start_line + offset,
                        block.start_line + offset,
                        line[start : start + maximum_chars],
                    )
                )
                part_number += 1
        else:
            buffer.append(line)
    if buffer:
        pieces.append(
            Block(
                f"{block.locator} part {part_number}",
                part_start,
                block.end_line,
                "\n".join(buffer),
            )
        )
    return pieces


def chunk_text(text: str, maximum_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    if maximum_chars < 200:
        raise ValueError("maximum_chars must be at least 200")
    units = [piece for block in parse_blocks(text) for piece in split_large_block(block, maximum_chars)]
    chunks: list[Chunk] = []
    pending: list[Block] = []

    def flush() -> None:
        nonlocal pending
        if not pending:
            return
        first, last = pending[0], pending[-1]
        locator = first.locator if first.locator == last.locator else f"{first.locator} to {last.locator}"
        chunks.append(
            Chunk(
                identifier=f"E{len(chunks) + 1:04d}",
                locator=locator,
                start_line=first.start_line,
                end_line=last.end_line,
                text="\n\n".join(block.text for block in pending),
            )
        )
        pending = []

    for unit in units:
        projected = len("\n\n".join([*(block.text for block in pending), unit.text]))
        if pending and projected > maximum_chars:
            flush()
        pending.append(unit)
    flush()
    return chunks


def source_map(chunks: Iterable[Chunk]) -> list[dict[str, Any]]:
    result = []
    for chunk in chunks:
        counts = Counter(tokenize(chunk.text))
        keywords = [token for token, _ in counts.most_common(8)]
        preview = re.sub(r"\s+", " ", chunk.text).strip()[:180]
        result.append(
            {
                "id": chunk.identifier,
                "locator": chunk.locator,
                "estimated_tokens": estimated_tokens(chunk.text),
                "keywords": keywords,
                "preview": preview,
            }
        )
    return result


def rank_chunks(chunks: list[Chunk], queries: list[str]) -> list[Chunk]:
    if not queries:
        return list(chunks)
    documents = [tokenize(chunk.text) for chunk in chunks]
    document_frequency = Counter(token for document in documents for token in set(document))
    average_length = sum(map(len, documents)) / max(1, len(documents))
    query_tokens = tokenize(" ".join(queries))
    exact_queries = [query.lower().strip() for query in queries if query.strip()]
    scored = []
    for index, document in enumerate(documents):
        counts = Counter(document)
        score = 0.0
        for token in query_tokens:
            frequency = counts[token]
            if not frequency:
                continue
            df = document_frequency[token]
            inverse_frequency = math.log(1 + (len(chunks) - df + 0.5) / (df + 0.5))
            denominator = frequency + 1.5 * (1 - 0.75 + 0.75 * len(document) / average_length)
            score += inverse_frequency * frequency * 2.5 / denominator
        lowered = chunks[index].text.lower()
        score += sum(20 for query in exact_queries if query in lowered)
        scored.append((score, chunks[index].identifier, chunks[index]))
    return [item[2] for item in sorted(scored, key=lambda item: (-item[0], item[1]))]


def select_chunks(chunks: list[Chunk], queries: list[str], top: int) -> list[Chunk]:
    if top < 3:
        raise ValueError("top must be at least 3 to preserve beginning, middle and ending coverage")
    if len(chunks) <= top:
        return list(chunks)
    anchors = {0, len(chunks) // 2, len(chunks) - 1}
    selected = {chunks[index].identifier: chunks[index] for index in anchors}
    for chunk in rank_chunks(chunks, queries):
        selected.setdefault(chunk.identifier, chunk)
        if len(selected) >= top:
            break
    positions = {chunk.identifier: index for index, chunk in enumerate(chunks)}
    return sorted(selected.values(), key=lambda chunk: positions[chunk.identifier])


def batch_chunks(chunks: list[Chunk], token_budget: int) -> list[list[Chunk]]:
    if token_budget < 500:
        raise ValueError("batch token budget must be at least 500")
    batches: list[list[Chunk]] = []
    pending: list[Chunk] = []
    used = 0
    for chunk in chunks:
        size = estimated_tokens(chunk.text)
        if pending and used + size > token_budget:
            batches.append(pending)
            pending, used = [], 0
        pending.append(chunk)
        used += size
    if pending:
        batches.append(pending)
    return batches


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.json"


def ledger_cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.ledger.json"


def read_chunk_cache(
    cache_dir: Path, key: str, digest: str, kind: str, pipeline_version: str
) -> list[Chunk] | None:
    path = cache_path(cache_dir, key)
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema") != CACHE_SCHEMA:
            return None
        if value.get("content_hash") != digest or value.get("kind") != kind:
            return None
        if value.get("pipeline_version") != pipeline_version:
            return None
        return [Chunk.from_dict(chunk) for chunk in value["chunks"]]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def write_chunk_cache(
    cache_dir: Path,
    key: str,
    digest: str,
    kind: str,
    pipeline_version: str,
    chunks: list[Chunk],
) -> None:
    write_json(
        cache_path(cache_dir, key),
        {
            "schema": CACHE_SCHEMA,
            "content_hash": digest,
            "kind": kind,
            "pipeline_version": pipeline_version,
            "chunks": [chunk.to_dict() for chunk in chunks],
        },
    )


def read_verified_ledger(cache_dir: Path, key: str, digest: str, mode: str) -> dict[str, Any] | None:
    path = ledger_cache_path(cache_dir, key)
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if value.get("schema") != LEDGER_SCHEMA or value.get("source_content_hash") != digest:
        return None
    # Only a full-source ledger is safe to reuse for another run or question.
    # A selective ledger depends on the exact query that produced its selection.
    if value.get("mode") != "full":
        return None
    return value


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    data = args.input.read_bytes()
    text = data.decode("utf-8", errors="replace").lstrip("\ufeff")
    digest = content_hash(data)
    key = cache_key(digest, args.kind, args.pipeline_version)
    cache_dir = args.cache_dir.resolve()
    chunks = None if args.no_cache else read_chunk_cache(
        cache_dir, key, digest, args.kind, args.pipeline_version
    )
    cache_status = "hit" if chunks is not None else "miss"
    if chunks is None:
        chunks = chunk_text(text, args.max_chars)
        if not chunks:
            raise ValueError("input contains no usable text")
        if not args.no_cache:
            write_chunk_cache(cache_dir, key, digest, args.kind, args.pipeline_version, chunks)

    if args.mode == "full":
        selected = list(chunks)
        batches = batch_chunks(selected, args.batch_token_budget)
    else:
        selected = select_chunks(chunks, args.query, args.top)
        batches = [selected]

    verified_ledger = None if args.no_cache else read_verified_ledger(
        cache_dir, key, digest, args.mode
    )
    map_value = source_map(chunks)
    selected_tokens = sum(estimated_tokens(chunk.text) for chunk in selected)
    raw_tokens = estimated_tokens(text)
    maximum_batch = max(
        (sum(estimated_tokens(chunk.text) for chunk in batch) for batch in batches), default=0
    )
    pack = {
        "schema": PACK_SCHEMA,
        "source": {
            "identity": redact_source(args.source),
            "input_name": args.input.name,
            "kind": args.kind,
            "content_hash": digest,
            "pipeline_version": args.pipeline_version,
        },
        "cache": {
            "key": key,
            "evidence": cache_status,
            "ledger": "hit" if verified_ledger is not None else "miss",
        },
        "map": map_value,
        "selection": {
            "mode": args.mode,
            "queries": args.query,
            "selected_chunk_ids": [chunk.identifier for chunk in selected],
            "batches": [
                {
                    "id": f"B{index + 1:03d}",
                    "estimated_tokens": sum(estimated_tokens(chunk.text) for chunk in batch),
                    "chunks": [chunk.to_dict() for chunk in batch],
                }
                for index, batch in enumerate(batches)
            ],
        },
        "coverage": {
            "all_chunk_ids": [chunk.identifier for chunk in chunks],
            "full_source_emitted": args.mode == "full" and len(selected) == len(chunks),
            "structural_coverage": args.mode == "full"
            or ({chunks[0].identifier, chunks[len(chunks) // 2].identifier, chunks[-1].identifier}
                <= {chunk.identifier for chunk in selected}),
            "full_audit_still_required": True,
        },
    }
    if verified_ledger is not None:
        pack["verified_ledger"] = verified_ledger

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "source": {
            "identity": redact_source(args.source),
            "kind": args.kind,
            "content_hash": digest,
        },
        "pipeline_version": args.pipeline_version,
        "mode": args.mode,
        "cache": pack["cache"],
        "chunks": {
            "total": len(chunks),
            "selected": len(selected),
            "batches": len(batches),
        },
        "estimated_tokens": {
            "raw_source": raw_tokens,
            "source_map": estimated_tokens(json.dumps(map_value, ensure_ascii=False)),
            "selected_evidence": selected_tokens,
            "largest_batch": maximum_batch,
            "source_reprocessing_avoided_by_verified_ledger": raw_tokens
            if verified_ledger is not None
            else 0,
        },
        "coverage": pack["coverage"],
        "provider_usage": None,
    }
    if args.output:
        write_json(args.output, pack)
    if args.receipt:
        write_json(args.receipt, receipt)
    return {"pack": pack, "receipt": receipt}


def validate_ledger_data(ledger: dict[str, Any], pack: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if ledger.get("schema") != LEDGER_SCHEMA:
        errors.append(f"ledger schema must be {LEDGER_SCHEMA}")
    digest = pack.get("source", {}).get("content_hash")
    if ledger.get("source_content_hash") != digest:
        errors.append("ledger source_content_hash differs from the evidence pack")
    if ledger.get("mode") != pack.get("selection", {}).get("mode"):
        errors.append("ledger mode differs from the evidence pack")

    all_ids = set(pack.get("coverage", {}).get("all_chunk_ids") or [])
    selected_ids = set(pack.get("selection", {}).get("selected_chunk_ids") or [])
    reviewed = set(ledger.get("reviewed_chunk_ids") or [])
    unknown_reviewed = reviewed - all_ids
    if unknown_reviewed:
        errors.append(f"unknown reviewed chunk ids: {sorted(unknown_reviewed)}")
    if pack.get("selection", {}).get("mode") == "full" and reviewed != all_ids:
        missing = sorted(all_ids - reviewed)
        errors.append(f"full ledger has not reviewed every chunk: {missing}")
    if pack.get("selection", {}).get("mode") == "selective" and not reviewed <= selected_ids:
        errors.append("selective ledger reviews chunks outside the emitted selection")

    for group in ("claims", "artifacts"):
        values = ledger.get(group) or []
        if not isinstance(values, list):
            errors.append(f"{group} must be a list")
            continue
        for index, item in enumerate(values):
            if not isinstance(item, dict) or not str(item.get("text") or "").strip():
                errors.append(f"{group}[{index}] requires text")
                continue
            evidence_ids = set(item.get("evidence_ids") or [])
            if not evidence_ids:
                errors.append(f"{group}[{index}] requires evidence_ids")
            unknown = evidence_ids - reviewed
            if unknown:
                errors.append(f"{group}[{index}] cites unreviewed chunks: {sorted(unknown)}")
    if "model_response" in ledger or "generated_page" in ledger:
        errors.append("ledger must contain evidence, not a cached model response or generated page")
    return errors


def validate_ledger(args: argparse.Namespace) -> dict[str, Any]:
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    errors = validate_ledger_data(ledger, pack)
    if errors:
        return {"status": "FAIL", "errors": errors}
    key = str(pack["cache"]["key"])
    cache_ledger = not args.no_cache and ledger.get("mode") == "full"
    if cache_ledger:
        write_json(ledger_cache_path(args.cache_dir.resolve(), key), ledger)
    return {
        "status": "PASS",
        "claims": len(ledger.get("claims") or []),
        "artifacts": len(ledger.get("artifacts") or []),
        "reviewed_chunks": len(ledger.get("reviewed_chunk_ids") or []),
        "cached": cache_ledger,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subcommands = result.add_subparsers(dest="command", required=True)

    prepare_parser = subcommands.add_parser("prepare", help="create an evidence pack and receipt")
    prepare_parser.add_argument("input", type=Path)
    prepare_parser.add_argument("--source", required=True)
    prepare_parser.add_argument("--kind", choices=sorted(KINDS), required=True)
    prepare_parser.add_argument("--mode", choices=("full", "selective"), default="selective")
    prepare_parser.add_argument("--query", action="append", default=[])
    prepare_parser.add_argument("--top", type=int, default=DEFAULT_TOP)
    prepare_parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    prepare_parser.add_argument("--batch-token-budget", type=int, default=DEFAULT_BATCH_TOKENS)
    prepare_parser.add_argument("--pipeline-version", default=PIPELINE_VERSION)
    prepare_parser.add_argument("--cache-dir", type=Path, default=Path(".3rdbrain-cache/evidence"))
    prepare_parser.add_argument("--no-cache", action="store_true")
    prepare_parser.add_argument("--output", type=Path)
    prepare_parser.add_argument("--receipt", type=Path)

    ledger_parser = subcommands.add_parser(
        "validate-ledger", help="validate and cache an evidence ledger"
    )
    ledger_parser.add_argument("ledger", type=Path)
    ledger_parser.add_argument("pack", type=Path)
    ledger_parser.add_argument("--cache-dir", type=Path, default=Path(".3rdbrain-cache/evidence"))
    ledger_parser.add_argument("--no-cache", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            value = prepare(args)
            print(json.dumps(value["receipt"], indent=2, ensure_ascii=False))
            return 0
        value = validate_ledger(args)
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return 0 if value["status"] == "PASS" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"evidence runtime: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
