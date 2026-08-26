from __future__ import annotations

import json
from pathlib import Path
import sys
from types import ModuleType

import pytest
import tools.knowledge_index as knowledge_index

from tools.knowledge_index import (
    audit_navigation_shape,
    build_discovery_assets,
    build_record,
    evaluate_search_cases,
    expand_query,
    find_group_candidates,
    parse_summary,
    rank_records,
    reciprocal_rank_fusion,
    validate_breakdown_manifest,
    validate_declared_paths,
    validate_registry,
)


SUMMARY = """# Table of contents

## Marketing

* [Leads & Outreach](marketing/leads.md)
  * [Revenue Email Agent](agents/email-agent.md)

## Local AI (Workstations)

* [Runtimes](local-ai/runtimes.md)
  * [Local Worker](agents/local-worker.md)
"""


REGISTRY = {
    "version": 1,
    "concepts": {
        "email": {
            "pref_label": "Email",
            "alt_labels": ["inbox", "mail", "Gmail"],
            "hidden_labels": ["e-mail"],
            "related": ["leads"],
        },
        "leads": {
            "pref_label": "Leads",
            "alt_labels": ["revenue opportunities"],
            "related": ["email"],
        },
        "local-ai": {
            "pref_label": "Local AI",
            "alt_labels": ["offline model", "local model"],
            "related": [],
        },
    },
}


def test_summary_parser_returns_the_full_primary_taxonomy_path():
    pages = parse_summary(SUMMARY)

    assert pages["agents/email-agent.md"]["taxonomy_path"] == [
        "Marketing",
        "Leads & Outreach",
    ]
    assert pages["agents/local-worker.md"]["taxonomy_path"] == [
        "Local AI (Workstations)",
        "Runtimes",
    ]


def test_declared_path_validator_rejects_a_wrong_subgroup(tmp_path: Path):
    page = tmp_path / "agents" / "email-agent.md"
    page.parent.mkdir()
    page.write_text(
        """---
description: Draft replies
taxonomy_path:
  - Marketing
  - Strategy & Planning
---
# Revenue Email Agent
""",
        encoding="utf-8",
    )

    errors = validate_declared_paths(tmp_path, parse_summary(SUMMARY))

    assert errors == [
        "agents/email-agent.md: declared ['Marketing', 'Strategy & Planning'], "
        "placed under ['Marketing', 'Leads & Outreach']"
    ]


def test_declared_path_validator_rejects_a_page_missing_from_navigation(tmp_path: Path):
    page = tmp_path / "orphan.md"
    page.write_text(
        """---
description: Lost page
taxonomy_path: [Marketing]
---
# Lost
""",
        encoding="utf-8",
    )

    assert validate_declared_paths(tmp_path, parse_summary(SUMMARY)) == [
        "orphan.md: declares a taxonomy path but is missing from navigation"
    ]


def test_registry_expands_preferred_alternative_hidden_and_related_terms():
    expanded = expand_query("triage my inbox", REGISTRY)

    assert {"email", "inbox", "mail", "gmail", "e-mail", "leads"} <= expanded


def test_registry_rejects_unknown_related_concepts_and_duplicate_labels():
    broken = json.loads(json.dumps(REGISTRY))
    broken["concepts"]["email"]["related"].append("missing")
    broken["concepts"]["leads"]["alt_labels"].append("Inbox")

    errors = validate_registry(broken)

    assert "email: related concept 'missing' does not exist" in errors
    assert "label 'inbox' belongs to both 'email' and 'leads'" in errors


def test_build_record_extracts_jobs_facets_aliases_type_and_breadcrumb():
    markdown = """---
description: Research business mail and prepare voice-matched replies
page_type: workflow
aliases: [inbox agent, reply drafter]
---
# Revenue-Ops Email Agent

**Use it when:**

| You want to… | This delivers |
| --- | --- |
| Stop manually sorting a noisy business inbox | A researched opportunity brief |
| Reply without granting send authority | Drafts for review |

**Facets:** [Workflow](../facets/workflow.md) · [Email](../facets/email.md) · [Agent](../facets/agent.md)
"""

    record = build_record(
        "agents/email-agent.md",
        markdown,
        ["Marketing", "Leads & Outreach"],
        REGISTRY,
    )

    assert record["title"] == "Revenue-Ops Email Agent"
    assert record["page_type"] == "workflow"
    assert record["breadcrumb"] == "Marketing › Leads & Outreach"
    assert record["facets"] == ["Workflow", "Email", "Agent"]
    assert record["jobs"] == [
        "Stop manually sorting a noisy business inbox",
        "Reply without granting send authority",
    ]
    assert "inbox agent" in record["aliases"]


def test_home_record_links_out_of_the_discovery_directory():
    record = build_record("README.md", "# 3rdBrain 2\n", ["Home"], REGISTRY)

    assert record["id"] == "home"
    assert record["location"] == "../"


def test_rrf_rewards_results_found_by_both_exact_and_intent_retrievers():
    fused = reciprocal_rank_fusion(
        [["exact-only", "both"], ["both", "intent-only"]],
        rank_constant=10,
    )

    assert fused[0][0] == "both"
    assert {item for item, _score in fused} == {"both", "exact-only", "intent-only"}


def test_hybrid_ranking_finds_a_natural_language_job_and_applies_facets():
    records = [
        {
            "id": "email",
            "title": "Revenue Email Agent",
            "description": "Prepare replies",
            "jobs": ["research a business inbox and draft replies for approval"],
            "aliases": ["inbox agent"],
            "facets": ["Email", "Agent"],
            "taxonomy_path": ["Marketing", "Leads & Outreach"],
            "search_text": "revenue email agent prepare replies business inbox approval",
        },
        {
            "id": "local-worker",
            "title": "Local Worker",
            "description": "Use a local model for high-volume delegated work",
            "jobs": ["use a cheap local worker beneath a stronger hosted agent"],
            "aliases": ["offline executor"],
            "facets": ["Local AI", "Agent"],
            "taxonomy_path": ["Local AI (Workstations)", "Runtimes"],
            "search_text": "local worker efficient offline model hosted agent",
        },
    ]

    ranked = rank_records(records, "cheap worker under a hosted agent", REGISTRY)
    email_only = rank_records(records, "agent", REGISTRY, {"facets": ["Email"]})

    assert ranked[0]["id"] == "local-worker"
    assert [record["id"] for record in email_only] == ["email"]


def test_group_audit_surfaces_three_ungrouped_pages_sharing_a_stable_facet():
    records = [
        {
            "id": f"email-{index}",
            "title": f"Email workflow {index}",
            "facets": ["Email", "Workflow"],
            "taxonomy_path": ["Marketing"],
        }
        for index in range(3)
    ]

    candidates = find_group_candidates(records, minimum_cluster_size=3)

    assert candidates == [
        {
            "parent": ["Marketing"],
            "suggested_group": "Email",
            "members": ["email-0", "email-1", "email-2"],
            "reason": "3 direct children share the Email facet",
        }
    ]


def test_navigation_audit_flags_overfull_deep_and_catchall_groups():
    records = [
        {"id": f"item-{index}", "taxonomy_path": ["Marketing", "Other"]}
        for index in range(4)
    ] + [{"id": "deep", "taxonomy_path": ["A", "B", "C", "D", "E"]}]

    audit = audit_navigation_shape(records, review_direct_children_at=3, maximum_depth=4)

    assert audit["overfull_groups"] == [
        {"path": ["Marketing", "Other"], "direct_pages": 4, "review_at": 3}
    ]
    assert audit["overdeep_pages"] == [
        {"id": "deep", "path": ["A", "B", "C", "D", "E"], "maximum_depth": 4}
    ]
    assert audit["catchall_groups"] == [["Marketing", "Other"]]

def test_breakdown_manifest_requires_unique_elements_existing_pages_and_two_way_links(
    tmp_path: Path,
):
    (tmp_path / "hub.md").write_text("[Email](email.md)\n", encoding="utf-8")
    (tmp_path / "email.md").write_text("[Source hub](hub.md)\n", encoding="utf-8")
    manifest = {
        "source_id": "youtube:test",
        "hub": "hub.md",
        "elements": [
            {
                "id": "email",
                "start": "10:23",
                "page": "email.md",
                "page_type": "workflow",
                "taxonomy_path": ["Marketing", "Email"],
            }
        ],
    }

    assert validate_breakdown_manifest(manifest, tmp_path) == []

    manifest["elements"].append(dict(manifest["elements"][0]))
    errors = validate_breakdown_manifest(manifest, tmp_path)
    assert "duplicate element id 'email'" in errors
    assert "duplicate start time '10:23'" in errors


def test_search_evaluation_reports_recall_and_reciprocal_rank():
    records = [
        {
            "id": "email",
            "title": "Email Agent",
            "description": "Draft replies",
            "jobs": ["triage inbox"],
            "aliases": [],
            "facets": ["Email"],
            "taxonomy_path": ["Marketing"],
            "search_text": "email agent draft replies triage inbox",
        }
    ]
    cases = [{"query": "triage inbox", "expected_top_5": ["email"]}]

    report = evaluate_search_cases(records, cases, REGISTRY)

    assert report["queries"] == 1
    assert report["recall_at_5"] == pytest.approx(1.0)
    assert report["mean_reciprocal_rank"] == pytest.approx(1.0)


def test_full_asset_builder_validates_and_writes_the_private_catalog(tmp_path: Path):
    root = tmp_path / "vault"
    output = tmp_path / "out"
    (root / "facets").mkdir(parents=True)
    (root / "breakdowns").mkdir()
    (root / "SUMMARY.md").write_text(
        """# Table of contents

## Marketing

* [Email Hub](hub.md)
* [Email Agent](email.md)
""",
        encoding="utf-8",
    )
    (root / "taxonomy.yml").write_text(
        """version: 1
policies:
  minimum_group_size: 3
  search_quality: {recall_at_5: 1.0, mean_reciprocal_rank: 1.0}
concepts:
  email:
    pref_label: Email
    alt_labels: [inbox]
    hidden_labels: []
    related: []
""",
        encoding="utf-8",
    )
    (root / "search-cases.yml").write_text(
        """cases:
  - query: triage inbox
    expected_top_5: [email]
""",
        encoding="utf-8",
    )
    (root / "facets" / "README.md").write_text(
        """## By capability

| Facet | Description | Pages |
| --- | --- | --- |
| [Email](email.md) | Inbox work | 1 |
""",
        encoding="utf-8",
    )
    (root / "hub.md").write_text("# Hub\n\n[Email](email.md)\n", encoding="utf-8")
    (root / "email.md").write_text(
        """---
description: Triage an inbox
taxonomy_path: [Marketing]
page_type: workflow
aliases: [inbox helper]
---
# Email Agent

[Hub](hub.md)

**Use it when:**

| You want to… | This delivers |
| --- | --- |
| Triage an inbox | Ranked messages |

**Facets:** [Email](facets/email.md)
""",
        encoding="utf-8",
    )
    (root / "breakdowns" / "source.yml").write_text(
        """source_id: test:source
hub: hub.md
elements:
  - id: email
    start: "1:00"
    page: email.md
    page_type: workflow
    taxonomy_path: [Marketing]
""",
        encoding="utf-8",
    )

    result = build_discovery_assets(root, output)

    assert result["records"] == 2
    assert result["evaluation"]["recall_at_5"] == pytest.approx(1.0)
    assert json.loads((output / "taxonomy.json").read_text(encoding="utf-8"))["facet_counts"] == {"Email": 1}
    assert (output / "suggestions.json").exists()
    assert (output / "taxonomy-audit.json").exists()


def test_full_asset_builder_fails_closed_on_a_broken_registry(tmp_path: Path):
    (tmp_path / "taxonomy.yml").write_text(
        """version: 1
concepts:
  email:
    pref_label: Email
    related: [missing]
""",
        encoding="utf-8",
    )
    (tmp_path / "SUMMARY.md").write_text("# Table of contents\n", encoding="utf-8")
    (tmp_path / "search-cases.yml").write_text("cases: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="related concept 'missing' does not exist"):
        build_discovery_assets(tmp_path, tmp_path / "out")


def test_legacy_static_facet_maps_keep_their_domain_group_names(monkeypatch, tmp_path: Path):
    legacy = ModuleType("facets_to_tags")
    legacy.GROUPS = {
        "tofu": "Protein/Tofu",
        "airfry": "Method/AirFry",
        "main": "Role/Main",
    }
    monkeypatch.setitem(sys.modules, "facets_to_tags", legacy)

    assert knowledge_index._facet_groups(tmp_path) == {
        "Tofu": "Protein",
        "AirFry": "Method",
        "Main": "Role",
    }
