---
name: 3rdbrain-curator
description: >
  Turn saved videos, repositories, articles, social posts, documents, images, audio and notes
  into a verified, purpose-filed and cross-referenced 3rdBrain knowledge base.
---

# 3rdBrain Curator

Use the smallest instruction set that completes the current job.

1. Follow `references/framework-freshness.md` once.
2. For first-time setup, use the `3rdbrain-setup` skill. Do not load curation guidance.
3. For publishing, use the `3rdbrain-publish` skill. Do not load acquisition guidance.
4. For a queued batch, use the `3rdbrain-process` skill.
5. For one-off curation, read `references/curation-core.md`, then load only the matching
   source guides below.

| Material present | Read before acquisition |
| --- | --- |
| Video | `references/video-analysis.md` |
| Website or article | `references/web-analysis.md` |
| Repository or source code | `references/repository-analysis.md` |
| Social post, discussion or comments | `references/social-analysis.md` |
| PDF, EPUB or Office document | `references/document-analysis.md` |
| Screenshot, image post, photographed slide or scan | `references/image-analysis.md` |
| Podcast, audio, RSS or Atom feed | `references/audio-analysis.md` |
| Login-gated or interactive evidence gap | `references/interactive-analysis.md` |

Read `references/deep-breakdown.md` only when the source qualifies for L2/L3 treatment or the
user asks for a full breakdown. Read `references/page-templates.md` only when the compact page
contract does not cover the required page type. Read `references/site-build.md` only for build
development or troubleshooting. Read `references/platform-setup.md` only during setup.

For long text evidence, use `_site/tools/evidence_runtime.py` as described in
`references/evidence-efficiency.md`. It caches deterministic evidence, creates locator-preserving
packs and records an efficiency receipt. Full deep mining still reviews every evidence batch once.
Token savings never permit missing evidence.
