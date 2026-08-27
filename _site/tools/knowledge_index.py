"""Build and validate 3rdBrain's structured discovery index.

The content remains ordinary Markdown. This module derives a deterministic,
private search catalog from SUMMARY navigation, page frontmatter, Use-it-when
tables and facet footers. It also validates the parts curators explicitly
declare: full taxonomy paths and long-source breakdown manifests.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

import yaml


HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
BULLET_RE = re.compile(
    r"^(?P<indent>\s*)\*\s+\[(?P<title>[^]]+)\]\((?P<path>[^)]+?\.md(?:#[^)]+)?)\)"
)
PLAIN_BULLET_RE = re.compile(r"^(?P<indent>\s*)\*\s+(?!\[)(?P<title>.+?)\s*$")
FRONTMATTER_RE = re.compile(r"^---\r?\n(?P<body>[\s\S]*?)\r?\n---\r?\n")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
FACETS_RE = re.compile(r"^\*\*Facets:\*\*(?P<body>.*)$", re.MULTILINE)
LINK_LABEL_RE = re.compile(r"\[([^]]+)\]\([^)]+\)")
TYPE_LABELS = {
    "🗺": "source hub",
    "🧩": "skill",
    "📦": "tool",
    "🤖": "agent",
    "📝": "prompt",
    "⚙": "tool",
    "ℹ": "reference",
    "🛡": "security",
}
GENERIC_CLUSTER_FACETS = {
    "Agent",
    "Automation",
    "CrossPlatform",
    "Free",
    "Freemium",
    "Paid",
    "PasteReady",
    "Prompt",
    "Workflow",
}
STOP_WORDS = {
    "a", "an", "and", "are", "for", "from", "how", "i", "in", "into", "is",
    "it", "my", "no", "of", "on", "or", "3rdbrain", "such", "that", "the",
    "this", "to", "under", "with", "without", "item",
}
DEFAULT_REGISTRY: dict[str, Any] = {
    "version": 1,
    "policies": {
        "minimum_group_size": 3,
        "review_direct_children_at": 12,
        "maximum_taxonomy_depth": 4,
        "search_quality": {"recall_at_5": 0.0, "mean_reciprocal_rank": 0.0},
    },
    "concepts": {},
}


def normalize_path(value: str) -> str:
    """Return a decoded Markdown path without an anchor or leading './'."""
    return unquote(value.split("#", 1)[0]).replace("\\", "/").removeprefix("./")


def page_id(path: str) -> str:
    normalized = normalize_path(path)
    if normalized.endswith("/README.md"):
        return normalized[: -len("/README.md")]
    if normalized == "README.md":
        return "home"
    return normalized.removesuffix(".md")


def page_location(path: str) -> str:
    identifier = page_id(path)
    return "../" if identifier == "home" else f"../{identifier}/"


def parse_frontmatter(markdown: str) -> dict[str, Any]:
    match = FRONTMATTER_RE.match(markdown)
    if not match:
        return {}
    loaded = yaml.safe_load(match.group("body")) or {}
    return loaded if isinstance(loaded, dict) else {}


def parse_summary(text: str) -> dict[str, dict[str, Any]]:
    """Map every navigated Markdown page to its full parent taxonomy path."""
    pages: dict[str, dict[str, Any]] = {}
    section = "Home"
    ancestors: list[tuple[int, str, bool]] = []

    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            section = heading.group("title").strip()
            ancestors = []
            continue

        bullet = BULLET_RE.match(line)
        plain_group = PLAIN_BULLET_RE.match(line) if not bullet else None
        if not bullet and not plain_group:
            continue

        item = bullet or plain_group
        assert item is not None
        depth = len(item.group("indent")) // 2
        while ancestors and ancestors[-1][0] >= depth:
            ancestors.pop()
        title = item.group("title").strip()
        if plain_group:
            ancestors.append((depth, title, True))
            continue
        taxonomy_path = [section] + [title for _level, title, _plain in ancestors]
        path = normalize_path(bullet.group("path"))
        pages[path] = {
            "title": title,
            "taxonomy_path": taxonomy_path,
            "label_only_ancestors": [
                title for _level, title, plain in ancestors if plain
            ],
            "depth": depth,
        }
        ancestors.append((depth, title, False))

    return pages


def _declared_path(frontmatter: dict[str, Any]) -> list[str] | None:
    value = frontmatter.get("taxonomy_path")
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [item.strip() for item in value if item.strip()]
    primary = frontmatter.get("primary_section")
    if isinstance(primary, str) and primary.strip():
        return [primary.strip()]
    return None


def validate_declared_paths(
    root: Path, navigation: dict[str, dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    for page in sorted(root.rglob("*.md")):
        relative_path = page.relative_to(root)
        if any(
            part in {".git", ".build", "site", "node_modules"}
            for part in relative_path.parts
        ):
            continue
        frontmatter = parse_frontmatter(page.read_text(encoding="utf-8"))
        declared = _declared_path(frontmatter)
        if not declared:
            continue
        relative = relative_path.as_posix()
        nav = navigation.get(relative, {})
        actual = nav.get("taxonomy_path")
        if actual is None:
            errors.append(f"{relative}: declares a taxonomy path but is missing from navigation")
        elif frontmatter.get("taxonomy_path") and declared != actual:
            errors.append(f"{relative}: declared {declared!r}, placed under {actual!r}")
        elif not frontmatter.get("taxonomy_path") and declared != actual[:1]:
            errors.append(f"{relative}: declared {declared!r}, placed under {actual!r}")
        elif str(frontmatter.get("page_type", "")).strip().lower() in {
            "agent",
            "prompt",
            "recipe",
            "workflow",
        } and nav.get("label_only_ancestors"):
            group = nav["label_only_ancestors"][-1]
            errors.append(
                f"{relative}: derived {frontmatter['page_type']} is nested under "
                f"label-only organizing group {group!r}; file it by purpose"
            )
    return errors


def _normal_label(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def validate_registry(registry: dict[str, Any]) -> list[str]:
    concepts = registry.get("concepts") or {}
    errors: list[str] = []
    labels: dict[str, str] = {}

    for concept_id, concept in concepts.items():
        if not isinstance(concept, dict) or not concept.get("pref_label"):
            errors.append(f"{concept_id}: pref_label is required")
            continue
        all_labels = [concept["pref_label"]]
        all_labels += concept.get("alt_labels") or []
        all_labels += concept.get("hidden_labels") or []
        for label in all_labels:
            normalized = _normal_label(str(label))
            previous = labels.get(normalized)
            if previous and previous != concept_id:
                errors.append(f"label '{normalized}' belongs to both '{previous}' and '{concept_id}'")
            labels[normalized] = concept_id
        for relation in concept.get("related") or []:
            if relation not in concepts:
                errors.append(f"{concept_id}: related concept '{relation}' does not exist")
    return sorted(set(errors))


def tokenize(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+(?:[.+#][a-z0-9]+)?", value.lower())
        if token not in STOP_WORDS
    ]


def expand_query(query: str, registry: dict[str, Any]) -> set[str]:
    query_normal = _normal_label(query)
    query_tokens = set(tokenize(query))
    expanded = set(query_tokens)
    concepts = registry.get("concepts") or {}

    matched: set[str] = set()
    for concept_id, concept in concepts.items():
        labels = [concept.get("pref_label", "")]
        labels += concept.get("alt_labels") or []
        labels += concept.get("hidden_labels") or []
        if any(
            _normal_label(str(label)) in query_normal
            or set(tokenize(str(label))) <= query_tokens
            for label in labels
            if label
        ):
            matched.add(concept_id)
            matched.update(concept.get("related") or [])

    for concept_id in matched:
        concept = concepts.get(concept_id, {})
        labels = [concept.get("pref_label", "")]
        labels += concept.get("alt_labels") or []
        labels += concept.get("hidden_labels") or []
        for label in labels:
            if label:
                normalized = _normal_label(str(label))
                expanded.add(normalized)
                expanded.update(tokenize(normalized))
    return expanded


def _extract_jobs(markdown: str) -> list[str]:
    marker = re.search(r"^\*\*Use it when:\*\*", markdown, re.MULTILINE)
    if not marker:
        return []
    jobs: list[str] = []
    for line in markdown[marker.end() :].splitlines():
        stripped = line.strip()
        if not stripped:
            if jobs:
                break
            continue
        if not stripped.startswith("|"):
            if jobs:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2 or cells[0].lower().startswith("you want"):
            continue
        if set(cells[0]) <= {"-", ":", " "}:
            continue
        jobs.append(re.sub(r"[*_`]", "", cells[0]))
    return jobs[:5]


def _extract_facets(markdown: str) -> list[str]:
    match = FACETS_RE.search(markdown)
    return LINK_LABEL_RE.findall(match.group("body")) if match else []


def _plain_text(markdown: str) -> str:
    body = FRONTMATTER_RE.sub("", markdown, count=1)
    body = re.sub(r"```[\s\S]*?```", " ", body)
    body = re.sub(r"{%[^%]*%}", " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"!\[[^]]*\]\([^)]+\)", " ", body)
    body = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", body)
    body = re.sub(r"[#*_|>`~-]", " ", body)
    return re.sub(r"\s+", " ", body).strip()


def _infer_type(frontmatter: dict[str, Any], markdown: str, facets: list[str]) -> str:
    explicit = frontmatter.get("page_type")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()
    for icon, label in TYPE_LABELS.items():
        if re.search(rf"^>\s*{re.escape(icon)}", markdown, re.MULTILINE):
            return label
    for facet, label in (
        ("Workflow", "workflow"),
        ("Skill", "skill"),
        ("Agent", "agent"),
        ("Model", "model"),
        ("Prompt", "prompt"),
    ):
        if facet in facets:
            return label
    return "page"


def _registry_aliases(
    taxonomy_path: list[str], facets: list[str], registry: dict[str, Any]
) -> list[str]:
    targets = {_normal_label(value) for value in taxonomy_path + facets}
    aliases: list[str] = []
    for concept in (registry.get("concepts") or {}).values():
        if _normal_label(str(concept.get("pref_label", ""))) not in targets:
            continue
        aliases += [str(value) for value in concept.get("alt_labels") or []]
        aliases += [str(value) for value in concept.get("hidden_labels") or []]
    return aliases


def build_record(
    path: str,
    markdown: str,
    taxonomy_path: list[str],
    registry: dict[str, Any],
) -> dict[str, Any]:
    frontmatter = parse_frontmatter(markdown)
    title_match = H1_RE.search(markdown)
    title = title_match.group(1).strip() if title_match else Path(path).stem.replace("-", " ").title()
    facets = _extract_facets(markdown)
    jobs = _extract_jobs(markdown)
    aliases = frontmatter.get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    aliases = list(dict.fromkeys([str(item) for item in aliases] + _registry_aliases(taxonomy_path, facets, registry)))
    description = str(frontmatter.get("description") or "").strip()
    plain = _plain_text(markdown)
    identifier = page_id(path)
    search_text = " ".join(
        [title, description, *jobs, *aliases, *facets, *taxonomy_path, plain[:8000]]
    ).strip()
    return {
        "id": identifier,
        "path": normalize_path(path),
        "location": page_location(path),
        "title": title,
        "description": description,
        "page_type": _infer_type(frontmatter, markdown, facets),
        "taxonomy_path": taxonomy_path,
        "breadcrumb": " › ".join(taxonomy_path),
        "facets": facets,
        "jobs": jobs,
        "aliases": aliases,
        "source_hubs": frontmatter.get("source_hubs") or [],
        "search_text": search_text,
    }


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], rank_constant: int = 60
) -> list[tuple[str, float]]:
    scores: defaultdict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, identifier in enumerate(ranked, start=1):
            scores[identifier] += 1.0 / (rank_constant + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def _filtered(record: dict[str, Any], filters: dict[str, list[str]] | None) -> bool:
    if not filters:
        return True
    checks = {
        "facets": set(record.get("facets") or []),
        "categories": set(record.get("taxonomy_path") or []),
        "page_types": {record.get("page_type")},
    }
    for key, selected in filters.items():
        if selected and not set(selected) <= checks.get(key, set()):
            return False
    return True


def rank_records(
    records: list[dict[str, Any]],
    query: str,
    registry: dict[str, Any],
    filters: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    pool = [record for record in records if _filtered(record, filters)]
    query_tokens = tokenize(query)
    if not query_tokens:
        return pool
    expanded = expand_query(query, registry)
    document_tokens = {record["id"]: set(tokenize(record.get("search_text", ""))) for record in pool}
    document_frequency = {
        token: sum(token in values for values in document_tokens.values()) for token in query_tokens
    }
    inverse_frequency = {
        token: math.log((len(pool) + 1) / (document_frequency[token] + 1)) + 1
        for token in query_tokens
    }
    query_ngrams = {
        " ".join(query_tokens[start : start + size])
        for size in range(2, min(5, len(query_tokens) + 1))
        for start in range(0, len(query_tokens) - size + 1)
    }

    exact_titles: list[tuple[str, float]] = []
    lexical: list[tuple[str, float]] = []
    intent: list[tuple[str, float]] = []
    for record in pool:
        title = record.get("title", "").lower()
        description = record.get("description", "").lower()
        searchable = record.get("search_text", "").lower()
        jobs = " ".join(record.get("jobs", [])).lower()
        aliases = " ".join(record.get("aliases", [])).lower()
        structured = " ".join([title, description, jobs, aliases])
        lexical_score = 0.0
        for token in query_tokens:
            weight = inverse_frequency[token]
            lexical_score += title.count(token) * 10 * weight
            lexical_score += aliases.count(token) * 8 * weight
            lexical_score += jobs.count(token) * 6 * weight
            lexical_score += description.count(token) * 4 * weight
            lexical_score += min(searchable.count(token), 3) * 0.5 * weight
        lexical_score += sum(len(phrase.split()) * 5 for phrase in query_ngrams if phrase in structured)
        if title.strip() == query.strip().lower():
            exact_titles.append((record["id"], 2.0))
            lexical_score += 100
        elif title.startswith(query.strip().lower()):
            exact_titles.append((record["id"], 1.0))
            lexical_score += 30
        if query.lower() in searchable:
            lexical_score += 20
        if lexical_score:
            lexical.append((record["id"], lexical_score))

        intent_fields = " ".join(
            record.get("jobs", [])
            + record.get("aliases", [])
            + record.get("facets", [])
            + record.get("taxonomy_path", [])
            + [record.get("description", "")]
        ).lower()
        intent_score = sum(
            6 if " " in term and term in intent_fields else min(intent_fields.count(term), 3)
            for term in expanded
        )
        for alias in record.get("aliases", []):
            alias_tokens = set(tokenize(alias))
            if alias_tokens and alias_tokens <= set(query_tokens):
                intent_score += 25 + len(alias_tokens) * 3
        for job in record.get("jobs", []):
            job_tokens = set(tokenize(job))
            overlap = job_tokens & set(query_tokens)
            if overlap:
                intent_score += len(overlap) * 4 + (len(overlap) / len(job_tokens)) * 12
        if intent_score:
            intent.append((record["id"], float(intent_score)))

    exact_titles.sort(key=lambda item: (-item[1], item[0]))
    lexical.sort(key=lambda item: (-item[1], item[0]))
    intent.sort(key=lambda item: (-item[1], item[0]))
    fused = reciprocal_rank_fusion(
        [
            [identifier for identifier, _score in exact_titles],
            [identifier for identifier, _score in lexical],
            [identifier for identifier, _score in intent],
        ]
    )
    by_id = {record["id"]: record for record in pool}
    ranked: list[dict[str, Any]] = []
    for identifier, score in fused:
        record = dict(by_id[identifier])
        record["_score"] = score
        record["_match_reason"] = (
            "Exact wording + intent" if identifier in {item[0] for item in lexical} and identifier in {item[0] for item in intent}
            else "Exact wording" if identifier in {item[0] for item in lexical}
            else "Related intent"
        )
        ranked.append(record)
    return ranked


def find_group_candidates(
    records: list[dict[str, Any]], minimum_cluster_size: int = 3
) -> list[dict[str, Any]]:
    clusters: defaultdict[tuple[tuple[str, ...], str], list[str]] = defaultdict(list)
    for record in records:
        path = tuple(record.get("taxonomy_path") or [])
        if not path:
            continue
        for facet in record.get("facets") or []:
            if facet in GENERIC_CLUSTER_FACETS or facet in path:
                continue
            clusters[(path, facet)].append(record["id"])

    candidates = []
    for (parent, facet), members in sorted(clusters.items()):
        unique = sorted(set(members))
        if len(unique) < minimum_cluster_size:
            continue
        candidates.append(
            {
                "parent": list(parent),
                "suggested_group": facet,
                "members": unique,
                "reason": f"{len(unique)} direct children share the {facet} facet",
            }
        )
    return candidates


def audit_navigation_shape(
    records: list[dict[str, Any]],
    review_direct_children_at: int = 12,
    maximum_depth: int = 4,
) -> dict[str, list[Any]]:
    """Surface navigation that needs an editorial grouping decision.

    This is deliberately an audit rather than an auto-writer: GitBook remains
    authoritative, while the curator gets deterministic evidence about where
    a subgroup should be created or a catch-all should be renamed.
    """
    path_counts = Counter(
        tuple(record.get("taxonomy_path") or [])
        for record in records
        if record.get("taxonomy_path")
    )
    overfull = [
        {
            "path": list(path),
            "direct_pages": count,
            "review_at": review_direct_children_at,
        }
        for path, count in sorted(path_counts.items())
        if count > review_direct_children_at
    ]
    overdeep = [
        {
            "id": record["id"],
            "path": record["taxonomy_path"],
            "maximum_depth": maximum_depth,
        }
        for record in sorted(records, key=lambda item: item.get("id", ""))
        if len(record.get("taxonomy_path") or []) > maximum_depth
    ]
    catchall_names = {"misc", "miscellaneous", "other", "everything else", "uncategorized"}
    catchalls = sorted(
        [list(path) for path in path_counts if path and path[-1].strip().lower() in catchall_names]
    )
    return {
        "overfull_groups": overfull,
        "overdeep_pages": overdeep,
        "catchall_groups": catchalls,
    }


def validate_breakdown_manifest(manifest: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    summary = root / "SUMMARY.md"
    navigation = (
        parse_summary(summary.read_text(encoding="utf-8")) if summary.exists() else {}
    )
    hub_value = manifest.get("hub")
    hub_path = root / normalize_path(str(hub_value or ""))
    if not hub_value or not hub_path.exists():
        errors.append(f"hub page '{hub_value}' does not exist")
        hub_text = ""
    else:
        hub_text = hub_path.read_text(encoding="utf-8")

    seen_ids: set[str] = set()
    seen_starts: set[str] = set()
    for element in manifest.get("elements") or []:
        identifier = str(element.get("id") or "")
        start = str(element.get("start") or "")
        if identifier in seen_ids:
            errors.append(f"duplicate element id '{identifier}'")
        seen_ids.add(identifier)
        if start in seen_starts:
            errors.append(f"duplicate start time '{start}'")
        seen_starts.add(start)

        value = str(element.get("page") or "")
        path = root / normalize_path(value)
        if not value or not path.exists():
            errors.append(f"{identifier}: page '{value}' does not exist")
            continue
        declared_taxonomy = element.get("taxonomy_path")
        if not declared_taxonomy:
            errors.append(f"{identifier}: taxonomy_path is required")
        actual_taxonomy = navigation.get(normalize_path(value), {}).get("taxonomy_path")
        if actual_taxonomy is not None and declared_taxonomy != actual_taxonomy:
            errors.append(
                f"{identifier}: manifest taxonomy {declared_taxonomy!r}, "
                f"placed under {actual_taxonomy!r}"
            )
        if normalize_path(value) not in hub_text and Path(normalize_path(value)).name not in hub_text:
            errors.append(f"{identifier}: hub does not link to '{value}'")
        child = path.read_text(encoding="utf-8")
        hub_name = Path(normalize_path(str(hub_value))).name if hub_value else ""
        if hub_name and hub_name not in child:
            errors.append(f"{identifier}: child page does not link back to hub '{hub_value}'")
    return errors


def evaluate_search_cases(
    records: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    registry: dict[str, Any],
) -> dict[str, Any]:
    reciprocal_ranks: list[float] = []
    recalls: list[float] = []
    failures: list[dict[str, Any]] = []
    for case in cases:
        ranked = rank_records(records, str(case.get("query", "")), registry)[:5]
        actual = [record["id"] for record in ranked]
        expected = list(case.get("expected_top_5") or [])
        hits = [identifier for identifier in expected if identifier in actual]
        recalls.append(len(hits) / len(expected) if expected else 1.0)
        first = min((actual.index(identifier) + 1 for identifier in hits), default=0)
        reciprocal_ranks.append(1.0 / first if first else 0.0)
        if not hits:
            failures.append({"query": case.get("query"), "expected": expected, "actual": actual})
    count = len(cases)
    return {
        "queries": count,
        "recall_at_5": sum(recalls) / count if count else 1.0,
        "mean_reciprocal_rank": sum(reciprocal_ranks) / count if count else 1.0,
        "failures": failures,
    }


def _facet_groups(root: Path) -> dict[str, str]:
    try:
        import facets_to_tags
    except ImportError:
        return {}

    # Older 3rdBrain bases keep a static label -> "Group/Label" mapping. Keep
    # their domain language (Protein/Method/Role, for example) instead of
    # flattening every facet into the generic Capability group.
    load_groups = getattr(facets_to_tags, "load_groups", None)
    if not callable(load_groups):
        labels: dict[str, str] = {}
        for grouped in getattr(facets_to_tags, "GROUPS", {}).values():
            if not isinstance(grouped, str) or "/" not in grouped:
                continue
            group, label = grouped.split("/", 1)
            labels[label] = group
        return labels

    by_slug = load_groups(root)
    labels: dict[str, str] = {}
    hub = root / "facets" / "README.md"
    if not hub.exists():
        return labels
    for label, href in re.findall(r"\[([^]]+)\]\(([^)]+)\.md\)", hub.read_text(encoding="utf-8")):
        slug = href.rsplit("/", 1)[-1].lower()
        clean = re.sub(r"^[^A-Za-z0-9]+", "", label).strip()
        if slug in by_slug:
            labels[clean] = by_slug[slug]
    return labels


def project_name(root: Path, registry: dict[str, Any]) -> str:
    configured = registry.get("project", {}).get("name")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    readme = root / "README.md"
    if readme.exists():
        heading = H1_RE.search(readme.read_text(encoding="utf-8"))
        if heading:
            return re.sub(r"\s+", " ", heading.group(1)).strip()
    return root.name or "Knowledge Base"


def build_discovery_assets(root: Path, output: Path) -> dict[str, Any]:
    registry_path = root / "taxonomy.yml"
    cases_path = root / "search-cases.yml"
    registry = (
        yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        if registry_path.exists()
        else json.loads(json.dumps(DEFAULT_REGISTRY))
    )
    registry_errors = validate_registry(registry)
    navigation = parse_summary((root / "SUMMARY.md").read_text(encoding="utf-8"))
    path_errors = validate_declared_paths(root, navigation)

    records = []
    for path, nav in navigation.items():
        page = root / path
        if not page.exists():
            continue
        records.append(build_record(path, page.read_text(encoding="utf-8"), nav["taxonomy_path"], registry))

    manifests = []
    breakdown_errors: list[str] = []
    breakdown_root = root / "breakdowns"
    if breakdown_root.exists():
        for path in sorted(breakdown_root.glob("*.yml")):
            manifest = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            manifests.append(manifest)
            breakdown_errors += [f"{path.name}: {error}" for error in validate_breakdown_manifest(manifest, root)]

    errors = registry_errors + path_errors + breakdown_errors
    if errors:
        raise ValueError("Discovery integrity failed:\n" + "\n".join(errors))

    cases_data = (
        yaml.safe_load(cases_path.read_text(encoding="utf-8")) or {}
        if cases_path.exists()
        else {}
    )
    cases = cases_data.get("cases") or []
    evaluation = evaluate_search_cases(records, cases, registry)
    floors = registry.get("policies", {}).get("search_quality", {})
    if evaluation["recall_at_5"] < float(floors.get("recall_at_5", 0)):
        raise ValueError(f"Recall@5 below floor: {evaluation['recall_at_5']:.3f}")
    if evaluation["mean_reciprocal_rank"] < float(floors.get("mean_reciprocal_rank", 0)):
        raise ValueError(f"MRR below floor: {evaluation['mean_reciprocal_rank']:.3f}")

    facet_counts = Counter(facet for record in records for facet in record["facets"])
    category_counts = Counter(record["taxonomy_path"][0] for record in records if record["taxonomy_path"])
    taxonomy = dict(registry)
    taxonomy["project"] = {"name": project_name(root, registry)}
    taxonomy["facet_counts"] = dict(sorted(facet_counts.items()))
    taxonomy["category_counts"] = dict(sorted(category_counts.items()))
    taxonomy["facet_groups"] = _facet_groups(root)

    suggestions = sorted(
        {
            value.strip()
            for record in records
            for value in [record["title"], *record["aliases"], *record["jobs"]]
            if value.strip()
        },
        key=lambda value: (len(value), value.lower()),
    )
    policies = registry.get("policies", {})
    audit = {
        "pages": len(records),
        "group_candidates": find_group_candidates(
            records,
            int(policies.get("minimum_group_size", 3)),
        ),
        **audit_navigation_shape(
            records,
            int(policies.get("review_direct_children_at", 12)),
            int(policies.get("maximum_taxonomy_depth", 4)),
        ),
        "breakdown_manifests": len(manifests),
        "breakdown_errors": breakdown_errors,
    }

    output.mkdir(parents=True, exist_ok=True)
    payloads = {
        "records.json": records,
        "taxonomy.json": taxonomy,
        "suggestions.json": suggestions,
        "evaluation.json": evaluation,
        "taxonomy-audit.json": audit,
    }
    for name, payload in payloads.items():
        (output / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return {"records": len(records), "evaluation": evaluation, "audit": audit}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="staged 3rdBrain content root")
    parser.add_argument(
        "--output",
        type=Path,
        help="output folder (default: ROOT/assets/discovery)",
    )
    args = parser.parse_args(argv)
    output = args.output or args.root / "assets" / "discovery"
    try:
        result = build_discovery_assets(args.root, output)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    report = result["evaluation"]
    print(
        f"  discovery: {result['records']} pages, "
        f"Recall@5={report['recall_at_5']:.2f}, MRR={report['mean_reciprocal_rank']:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
