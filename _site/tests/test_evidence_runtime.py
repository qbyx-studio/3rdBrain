import argparse
import json
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE_ROOT))

from tools import evidence_runtime as runtime


def prepare_args(
    source_file: Path,
    cache_dir: Path,
    *,
    mode: str = "full",
    queries: list[str] | None = None,
    pipeline_version: str = "1",
    output: Path | None = None,
    receipt: Path | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        input=source_file,
        source="https://example.com/source?token=private&v=visible",
        kind="video",
        mode=mode,
        query=queries or [],
        top=8,
        max_chars=500,
        batch_token_budget=500,
        pipeline_version=pipeline_version,
        cache_dir=cache_dir,
        no_cache=False,
        output=output,
        receipt=receipt,
    )


def timed_source(blocks: int = 30) -> str:
    return "\n\n".join(
        f"[{minute:02d}:{second:02d}] Topic {index}. "
        + (f"Evidence for workflow {index}, settings, limits and result. " * 7)
        for index, (minute, second) in enumerate(divmod(value * 13, 60) for value in range(blocks))
    )


def test_full_mode_emits_every_chunk_once_in_bounded_batches(tmp_path: Path):
    source = tmp_path / "transcript.txt"
    source.write_text(timed_source(), encoding="utf-8")

    result = runtime.prepare(prepare_args(source, tmp_path / "cache"))
    pack, receipt = result["pack"], result["receipt"]
    all_ids = pack["coverage"]["all_chunk_ids"]
    emitted = [
        chunk["id"]
        for batch in pack["selection"]["batches"]
        for chunk in batch["chunks"]
    ]

    assert pack["selection"]["mode"] == "full"
    assert pack["coverage"]["full_source_emitted"]
    assert emitted == all_ids
    assert len(emitted) == len(set(emitted))
    assert receipt["chunks"]["batches"] > 1
    assert receipt["estimated_tokens"]["largest_batch"] <= 650
    assert receipt["estimated_tokens"]["raw_source"] > 0
    assert receipt["cache"]["evidence"] == "miss"


def test_selective_mode_finds_requested_evidence_and_keeps_structural_coverage(tmp_path: Path):
    source = tmp_path / "article.md"
    parts = [f"## Section {index}\nGeneral notes about ordinary planning and review." for index in range(25)]
    parts[17] += "\nNVIDIA free access to hosted NIM prototyping endpoints."
    source.write_text("\n\n".join(parts), encoding="utf-8")

    result = runtime.prepare(
        prepare_args(
            source,
            tmp_path / "cache",
            mode="selective",
            queries=["nvidia free access"],
        )
    )
    pack, receipt = result["pack"], result["receipt"]
    selected = [
        chunk for batch in pack["selection"]["batches"] for chunk in batch["chunks"]
    ]

    assert any("NVIDIA free access" in chunk["text"] for chunk in selected)
    assert pack["coverage"]["structural_coverage"]
    assert len(selected) == min(8, receipt["chunks"]["total"])
    if receipt["chunks"]["total"] > 8:
        assert receipt["chunks"]["selected"] < receipt["chunks"]["total"]
        assert (
            receipt["estimated_tokens"]["selected_evidence"]
            < receipt["estimated_tokens"]["raw_source"]
        )


def test_cache_hits_move_with_content_and_invalidate_on_edit_or_pipeline_change(tmp_path: Path):
    source = tmp_path / "original.txt"
    source.write_text(timed_source(8), encoding="utf-8")
    cache = tmp_path / "cache"

    first = runtime.prepare(prepare_args(source, cache))["receipt"]
    second = runtime.prepare(prepare_args(source, cache))["receipt"]
    renamed = tmp_path / "renamed.txt"
    source.rename(renamed)
    moved = runtime.prepare(prepare_args(renamed, cache))["receipt"]
    changed_pipeline = runtime.prepare(
        prepare_args(renamed, cache, pipeline_version="2")
    )["receipt"]
    renamed.write_text(timed_source(8) + "\n[09:59] Edited ending.", encoding="utf-8")
    edited = runtime.prepare(prepare_args(renamed, cache))["receipt"]

    assert first["cache"]["evidence"] == "miss"
    assert second["cache"]["evidence"] == "hit"
    assert moved["cache"]["evidence"] == "hit"
    assert changed_pipeline["cache"]["evidence"] == "miss"
    assert edited["cache"]["evidence"] == "miss"


def test_corrupt_cache_is_a_safe_miss(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text(timed_source(5), encoding="utf-8")
    cache = tmp_path / "cache"
    first = runtime.prepare(prepare_args(source, cache))
    key = first["pack"]["cache"]["key"]
    runtime.cache_path(cache, key).write_text("{broken", encoding="utf-8")

    recovered = runtime.prepare(prepare_args(source, cache))

    assert recovered["receipt"]["cache"]["evidence"] == "miss"
    assert runtime.cache_path(cache, key).read_text(encoding="utf-8").startswith("{")


def test_full_ledger_must_cite_reviewed_evidence_and_then_becomes_reusable(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text(timed_source(7), encoding="utf-8")
    cache = tmp_path / "cache"
    pack_file = tmp_path / "pack.json"
    first = runtime.prepare(prepare_args(source, cache, output=pack_file))
    pack = first["pack"]
    ids = pack["coverage"]["all_chunk_ids"]
    ledger = {
        "schema": runtime.LEDGER_SCHEMA,
        "source_content_hash": pack["source"]["content_hash"],
        "mode": "full",
        "reviewed_chunk_ids": ids,
        "claims": [{"text": "The source contains a workflow.", "evidence_ids": [ids[0]]}],
        "artifacts": [{"text": "Example command", "evidence_ids": [ids[-1]]}],
        "gaps": [],
    }
    ledger_file = tmp_path / "ledger.json"
    ledger_file.write_text(json.dumps(ledger), encoding="utf-8")
    ledger_args = argparse.Namespace(
        ledger=ledger_file, pack=pack_file, cache_dir=cache, no_cache=False
    )

    validation = runtime.validate_ledger(ledger_args)
    repeated = runtime.prepare(prepare_args(source, cache))

    assert validation["status"] == "PASS"
    assert repeated["receipt"]["cache"]["ledger"] == "hit"
    assert "verified_ledger" in repeated["pack"]
    assert (
        repeated["receipt"]["estimated_tokens"]["source_reprocessing_avoided_by_verified_ledger"]
        == repeated["receipt"]["estimated_tokens"]["raw_source"]
    )


def test_incomplete_full_ledger_fails(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text(timed_source(7), encoding="utf-8")
    result = runtime.prepare(prepare_args(source, tmp_path / "cache"))
    pack = result["pack"]
    ids = pack["coverage"]["all_chunk_ids"]
    ledger = {
        "schema": runtime.LEDGER_SCHEMA,
        "source_content_hash": pack["source"]["content_hash"],
        "mode": "full",
        "reviewed_chunk_ids": ids[:-1],
        "claims": [],
        "artifacts": [],
        "gaps": [],
    }

    errors = runtime.validate_ledger_data(ledger, pack)

    assert any("has not reviewed every chunk" in error for error in errors)


def test_selective_ledger_is_not_reused_for_a_different_question(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text(timed_source(12), encoding="utf-8")
    cache = tmp_path / "cache"
    pack_file = tmp_path / "pack.json"
    first = runtime.prepare(
        prepare_args(
            source,
            cache,
            mode="selective",
            queries=["workflow 2"],
            output=pack_file,
        )
    )
    pack = first["pack"]
    ids = pack["selection"]["selected_chunk_ids"]
    ledger = {
        "schema": runtime.LEDGER_SCHEMA,
        "source_content_hash": pack["source"]["content_hash"],
        "mode": "selective",
        "reviewed_chunk_ids": ids,
        "claims": [{"text": "Selected evidence", "evidence_ids": [ids[0]]}],
        "artifacts": [],
        "gaps": [],
    }
    ledger_file = tmp_path / "ledger.json"
    ledger_file.write_text(json.dumps(ledger), encoding="utf-8")

    validation = runtime.validate_ledger(
        argparse.Namespace(ledger=ledger_file, pack=pack_file, cache_dir=cache, no_cache=False)
    )
    repeated = runtime.prepare(
        prepare_args(source, cache, mode="selective", queries=["workflow 11"])
    )

    assert validation["status"] == "PASS"
    assert validation["cached"] is False
    assert repeated["receipt"]["cache"]["ledger"] == "miss"
    assert "verified_ledger" not in repeated["pack"]


def test_receipts_redact_secret_query_values_and_avoid_private_paths(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("[00:01] evidence", encoding="utf-8")
    result = runtime.prepare(prepare_args(source, tmp_path / "cache"))
    serialized = json.dumps(result["receipt"])

    assert "private" not in serialized
    assert "token=REDACTED" in result["receipt"]["source"]["identity"]
    assert str(tmp_path) not in serialized
    assert result["receipt"]["provider_usage"] is None
