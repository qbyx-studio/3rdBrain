# 3rdBrain Project Content Record

## Purpose

Factual source material about the public 3rdBrain project for future content development and
optional Creator Brain ingestion. Claims here point to repository evidence or commit history.

## Project Snapshot

- **Current status:** Active public framework at
  [`qbyx-studio/3rdBrain`](https://github.com/qbyx-studio/3rdBrain). The current recorded release
  state is commit [`b59b040`](https://github.com/qbyx-studio/3rdBrain/commit/b59b040fa033842341a6ffd7285fbc2e3505fee6), dated 2026-09-10.
- **One-sentence description:** 3rdBrain turns saved material into a local Markdown knowledge base
  with structured curation, purpose-based filing, retrieval, freshness checks, publishing, and
  read-only agent access. Source: [`README.md`](../README.md).
- **Product position:** “The inbox for everything you save.” Source:
  [`README.md`](../README.md).
- **Distribution:** One Claude Code plugin and seven cross-runtime skills. Sources:
  [marketplace manifest](../.claude-plugin/marketplace.json) and [`skills/`](../skills/).
- **Primary evidence:** Git history and tags, [`README.md`](../README.md), the seven skill contracts,
  build tools and tests under [`_site/`](../_site/), and collector tests under
  [`inbox/tests/`](../inbox/tests/).

## Verified History

| Date | Event | Evidence | Confidence |
| --- | --- | --- | --- |
| 2026-07-23 | PromptOS v1.0.0 launched as a curator skill. The repository added a trailer, preview GIF, hero frame, and Pages landing. | Commits [`9ed4851`](https://github.com/qbyx-studio/3rdBrain/commit/9ed4851), [`fe17c2e`](https://github.com/qbyx-studio/3rdBrain/commit/fe17c2e), tag `v1.0.0`, and [launch media](../docs/) | High |
| 2026-07-24 | The curator contract made transcripts mandatory for videos and set whole-source mining as the quality floor. | Commits [`d3c523e`](https://github.com/qbyx-studio/3rdBrain/commit/d3c523e) and [`c0a9897`](https://github.com/qbyx-studio/3rdBrain/commit/c0a9897), tag `v1.0.1` | High |
| 2026-08-06 | The project added a gold-standard mining contract, faceted retrieval, and a mined-page template. | Commits [`07433f6`](https://github.com/qbyx-studio/3rdBrain/commit/07433f6) and [`c92bbd1`](https://github.com/qbyx-studio/3rdBrain/commit/c92bbd1) | High |
| 2026-08-14 to 2026-08-15 | Setup, processing, revocable credentials, and machine skill reconciliation became named workflows. | Commits [`392a8e9`](https://github.com/qbyx-studio/3rdBrain/commit/392a8e9) and [`d4812e4`](https://github.com/qbyx-studio/3rdBrain/commit/d4812e4), [`commands/`](../commands/) | High |
| 2026-08-17 | The local MkDocs site became the default reading surface. The public package added the inbox, starter base, macOS and Linux support, date stamps, staleness reporting, a single-instance lock, and text-only inbox items. | Commits [`da35f6d`](https://github.com/qbyx-studio/3rdBrain/commit/da35f6d) through [`5f86f1c`](https://github.com/qbyx-studio/3rdBrain/commit/5f86f1c), [`_site/`](../_site/), [`inbox/`](../inbox/) | High |
| 2026-08-20 | Telegram edits became authoritative inbox events, including edits received after initial capture. | Commit [`310b16c`](https://github.com/qbyx-studio/3rdBrain/commit/310b16c), [`inbox/tests/test_bot_edits.py`](../inbox/tests/test_bot_edits.py) | High |
| 2026-08-21 to 2026-08-22 | Purpose-based taxonomy, portable Discover, dynamic facets, route validation, exact Cloudflare path checks, and search-state reset became build-tested safeguards. | Commits [`a2bcd71`](https://github.com/qbyx-studio/3rdBrain/commit/a2bcd71) through [`591118e`](https://github.com/qbyx-studio/3rdBrain/commit/591118e), [Discover TDD record](../docs/portable-discovery.tdd.md), [navigation TDD record](../docs/navigation-route-contract.tdd.md) | High |
| 2026-08-24 | Framework Freshness became compulsory across workflows and gained proof-bearing receipts. Codex-native skills were added. | Commits [`1ef5098`](https://github.com/qbyx-studio/3rdBrain/commit/1ef5098), [`ca65927`](https://github.com/qbyx-studio/3rdBrain/commit/ca65927), [`1f35bee`](https://github.com/qbyx-studio/3rdBrain/commit/1f35bee), and [`510df5c`](https://github.com/qbyx-studio/3rdBrain/commit/510df5c) | High |
| 2026-08-26 | PromptOS became 3rdBrain and repository ownership moved to Qbyx Studio. | Commits [`1ee29c2`](https://github.com/qbyx-studio/3rdBrain/commit/1ee29c2) and [`30d86bd`](https://github.com/qbyx-studio/3rdBrain/commit/30d86bd), tag `v2.0.0` | High |
| 2026-08-27 | Portable builds gained explicit protection against vendor-led filing and non-portable taxonomy groups. | Commits [`838d0e7`](https://github.com/qbyx-studio/3rdBrain/commit/838d0e7) and [`b1deff9`](https://github.com/qbyx-studio/3rdBrain/commit/b1deff9) | High |
| 2026-08-30 | Extraction routing expanded across videos, websites, repositories, social material, documents, images, audio, and interactive sources. Acquisition follows the cheapest reliable route first. | Commits [`2a900e2`](https://github.com/qbyx-studio/3rdBrain/commit/2a900e2) through [`f51659d`](https://github.com/qbyx-studio/3rdBrain/commit/f51659d), [curator references](../skills/3rdbrain-curator/references/) | High |
| 2026-08-31 | First-pass validation, browser-local semantic retrieval, batched embeddings, and exact source-URL indexing entered the framework. | Commits [`24414c5`](https://github.com/qbyx-studio/3rdBrain/commit/24414c5) through [`6fee6ea`](https://github.com/qbyx-studio/3rdBrain/commit/6fee6ea), [`_site/tools/knowledge_index.py`](../_site/tools/knowledge_index.py) | High |
| 2026-09-01 | The evidence runtime began caching verified complete source readings and reporting estimated input and provider usage when available. | Commits [`b2aab43`](https://github.com/qbyx-studio/3rdBrain/commit/b2aab43) through [`1e1f53a`](https://github.com/qbyx-studio/3rdBrain/commit/1e1f53a), [`_site/tools/evidence_runtime.py`](../_site/tools/evidence_runtime.py) | High |
| 2026-09-02 | Guided read-only connections were added for people and agents, including Cloudflare authorization guidance. | Commits [`f2bd7d0`](https://github.com/qbyx-studio/3rdBrain/commit/f2bd7d0) through [`1dbf2c8`](https://github.com/qbyx-studio/3rdBrain/commit/1dbf2c8), [`skills/3rdbrain-connect/`](../skills/3rdbrain-connect/) | High |
| 2026-09-06 | The public README was repositioned around the durable inbox and retrieval job. | Commit [`2b96a45`](https://github.com/qbyx-studio/3rdBrain/commit/2b96a45), [`README.md`](../README.md) | High |
| 2026-09-10 | The reading column became 20% narrower, the contents panel gained readable wrapping, and long prompt blocks gained bounded scrolling with responsive browser tests. | Commit [`b59b040`](https://github.com/qbyx-studio/3rdBrain/commit/b59b040), [layout CSS](../_site/overlay/stylesheets/brand.css), [prompt compatibility CSS](../_site/overlay/stylesheets/gitbook-compat.css), and [browser test](../_site/e2e/layout-readability.spec.js) | High |

## Decisions and Rationale

| Decision | Rationale | Evidence | Status |
| --- | --- | --- | --- |
| Keep authored knowledge as local Markdown under Git. | The content stays inspectable, portable, versioned, and editable by its owner. | [`README.md`](../README.md), [`_site/build.sh`](../_site/build.sh) | Current |
| File extracted pages by purpose. | A vendor or source hub acts as a lens while each use case keeps one topical home. | [curation core](../skills/3rdbrain-curator/references/curation-core.md), [`_site/tools/check_primary_sections.py`](../_site/tools/check_primary_sections.py) | Current |
| Reconcile framework changes before content work. | A verified receipt gives existing bases a fast path while preserving local content and configuration. | [freshness contract](../skills/3rdbrain-curator/references/framework-freshness.md), [`_site/tools/framework_freshness.py`](../_site/tools/framework_freshness.py) | Current |
| Acquire structured evidence before broad rendering or OCR. | This reduces repeated reading while maintaining whole-source completeness. | [evidence efficiency](../skills/3rdbrain-curator/references/evidence-efficiency.md), [`_site/tools/evidence_runtime.py`](../_site/tools/evidence_runtime.py) | Current |
| Run Discover retrieval inside the browser. | Exact text, source URLs, facets, and optional local semantic ranking work without an LLM call during search. | [`README.md`](../README.md), [`_site/src/discovery-semantic.worker.js`](../_site/src/discovery-semantic.worker.js) | Current |
| Separate setup, processing, curation, publishing, connections, skill parity, and age review. | Each workflow has one clear user intent and its own safety contract. | [`skills/`](../skills/), [`commands/`](../commands/) | Current |
| Keep publishing explicit. | Local curation and Cloudflare publication remain distinct operations with consent and verification. | [`skills/3rdbrain-publish/`](../skills/3rdbrain-publish/), [`_site/deploy.sh`](../_site/deploy.sh) | Current |

## Outcomes and Evidence

| Outcome | Evidence | Limits or uncertainty |
| --- | --- | --- |
| Seven named skills cover the full operating lifecycle. | [`README.md`](../README.md), [`skills/`](../skills/) | Agent menu presentation varies by runtime and can require restart after installation. |
| The collector preserves message edits and supports text or captions. | [`inbox/bot.py`](../inbox/bot.py), [`inbox/tests/test_bot_edits.py`](../inbox/tests/test_bot_edits.py) | Delivery still depends on the user's Telegram and local collector configuration. |
| Builds enforce navigation routes, declared primary sections, source embeds, and touched-page quality. | [`_site/tests/`](../_site/tests/), [`_site/tools/validate_touched_pages.py`](../_site/tools/validate_touched_pages.py) | Automated checks support review. They do not prove every editorial judgment. |
| Discover combines exact, lexical, facet, source-URL, and optional local semantic signals. | [`_site/tools/knowledge_index.py`](../_site/tools/knowledge_index.py), [`_site/overlay/javascripts/discovery.js`](../_site/overlay/javascripts/discovery.js) | Retrieval quality depends on captured evidence, page wording, and index coverage. |
| One verified evidence record can support several pages from the same complete source reading. | [`_site/tools/evidence_runtime.py`](../_site/tools/evidence_runtime.py), [evidence efficiency](../skills/3rdbrain-curator/references/evidence-efficiency.md) | Estimated input is planning data. Provider-reported usage is retained only when available. |
| Published bases can expose static read-only records for agent connections. | [`_site/tools/agent_api.py`](../_site/tools/agent_api.py), [`skills/3rdbrain-connect/`](../skills/3rdbrain-connect/) | Private access still requires the site owner's Cloudflare configuration. |

## Milestones and Visual Evidence

| Date | Milestone | Evidence | Asset | Notes |
| --- | --- | --- | --- | --- |
| 2026-07-23 | Public launch under the PromptOS name | Commit [`fe17c2e`](https://github.com/qbyx-studio/3rdBrain/commit/fe17c2e) | [Hero frame](../docs/assets/hero-frame.png), [preview GIF](../docs/assets/preview.gif), [launch video](../docs/gloat.mp4) | The README carries a former-name disclaimer for the video. Media was reviewed for visible credentials and personal data. None were observed. |
| 2026-09-10 | Current 3rdBrain Discover workspace and reading layout | Commit [`b59b040`](https://github.com/qbyx-studio/3rdBrain/commit/b59b040) | [Discover workspace screenshot](evidence/2026-09-10-discover-workspace.png) | Captured from the public starter build at 1848 by 1000 pixels in dark mode. It contains generic fixture content and no credentials. |

## Content Leads

These are source-backed directions for future creator work. Strategy and final storytelling belong
in a separate Creator Brain.

- **From curator skill to full retrieval system:** trace the movement from `v1.0.0` through the
  inbox, local site, Discover, and connections using the dated commits above.
- **Why edits matter:** use the Telegram edit test to show how a small event-type distinction can
  protect user intent after capture.
- **Purpose beats provenance:** explain the taxonomy safeguard through the validator and curator
  contract.
- **Local search without search-time LLM calls:** demonstrate the retrieval layers with the current
  Discover screenshot and index implementation.
- **Framework freshness as a trust mechanism:** compare an unchanged-receipt fast path with a fully
  verified reconciliation.
- **Token-aware deep mining:** explain structured acquisition, one complete evidence record, and
  explicit usage reporting without claiming an unmeasured billing reduction.

## CreatorBraining Integration Example

This repository now demonstrates the Project Content Capture pattern:

1. `content/CONTENT.md` owns the source-backed project history.
2. The project instruction file routes future agents here before project-story work.
3. Milestone visuals live in `content/evidence/` or remain linked to an established media owner.
4. Historical detail stays in this file while the record remains compact.
5. A future Creator Brain ingestion task may select entries from this record only after explicit
   creator authorization.

For another project, copy the structure and evidence rules. Replace every fact, date, link, and
milestone with evidence from that project's own repository.

## Ingestion Notes

- Suitable material includes the verified timeline, explicit product decisions, launch assets,
  current screenshots, and the content leads above.
- Preserve links to commits and implementation evidence during ingestion.
- Treat the older PromptOS name as historical context. Current product naming is 3rdBrain.
- Keep private deployments, credentials, personal content, and unpublished repository structure
  outside any public Creator Brain ingestion.

## Open Questions and Known Gaps

- Public Git tags currently end at `v2.0.0`, while feature commits continue through 2026-09-10.
  The next release tag and release cadence are unrecorded.
- The TDD evidence documents capture the UI dimensions and test counts that existed when each was
  written. Current CSS and current tests own the latest layout values.
- Runtime speed and token billing improvements lack a comparable historical benchmark. The project
  records deterministic work reduction and reported usage evidence instead.
- User-scale retrieval quality needs continued measurement against real remembered-intent queries.

## Maintenance Log

| Date | Change | Sources reviewed |
| --- | --- | --- |
| 2026-09-10 | Created the canonical project record and captured the current Discover workspace. | Complete 75-commit history, tags, README, marketplace manifest, skills, commands, build tools, tests, TDD records, and launch assets |
