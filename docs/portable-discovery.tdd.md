# Portable Discovery — TDD Evidence

## Source and journeys

Journeys were derived from the approved 2026-08-21 PromptOS search/layout rollout:

1. A fresh PromptOS base receives a named Discover page and one shared header/full-page engine.
2. An existing base without new config builds a safe catalog without rewriting user content.
3. Exact titles, task-language search, filters and the first-sidebar-action contract remain stable.
4. The starter is responsive, wider, keyboard reachable and free of serious automated WCAG findings.

## RED → GREEN

- RED checkpoint: `5464273` — the public package had no `tools.knowledge_index`, Discover overlay,
  catalog assets or upgrade path; the portable test failed at import for that missing implementation.
- Fresh-build relevance RED: the first starter catalog scored MRR 0.567 against the 0.75 floor.
  Exact-title retrieval was added as a dedicated RRF signal; the rebuilt starter scored 1.00.
- GREEN unit/integration: 18 tests passed; `tools.knowledge_index` statement coverage 88.71%.
- GREEN build: a clean `_site/starter` produced 7 indexed pages at Recall@5 1.00 / MRR 1.00.
- GREEN integrity: 43 passed, 3 skipped, 4 content tests deselected against the starter build.
- GREEN E2E: 2 Chromium journeys passed for shared header handoff, project naming, sizing and axe.
- Polish RED checkpoint: `1bc8dc3` — a clean starter reproduced the lingering header query,
  open Material overlay, oversized result hierarchy and narrow 42rem desktop canvas.
- Polish GREEN checkpoint: `53dd5d8` — the generic package now closes and clears the header
  during Discover handoff, keeps the query in Discover, uses the compact 11–18 px catalog
  hierarchy and expands the desktop canvas to 50rem.
- Final portable verification: 18 coverage tests at 88.71%, 43 integrity tests passing
  (3 environment-dependent skips), and 2/2 Chromium journeys including serious/critical axe.

## Test specification

| Guarantee | Type | Evidence |
| --- | --- | --- |
| Complete Discover distribution ships | Integration | `tests/test_portable_discovery.py` |
| Fresh starter emits named records/taxonomy/suggestions | Integration | `tests/test_portable_discovery.py` |
| Legacy base upgrades only in staging | Integration | `tests/test_portable_discovery.py` |
| Ranking, taxonomy, manifests and audits | Unit | `tests/test_knowledge_index.py` |
| Header and Discover return the same top result; handoff closes the header overlay | E2E | `e2e/portable-discovery.spec.js` |
| First nav action, compact typography, 50rem width and serious axe findings | E2E | `e2e/portable-discovery.spec.js` |

## Coverage and limits

- Coverage command: `python -m pytest tests/test_knowledge_index.py tests/test_portable_discovery.py --cov=tools.knowledge_index --cov-fail-under=80 -q`.
- Result: 18 passed; 88.71% statement coverage.
- Axe covers common machine-detectable failures, not a complete manual accessibility certification.
- No committed visual baseline existed for the public starter, so visual regression comparison is
  inconclusive; the private implementation carries the three-breakpoint screenshot inspection.
