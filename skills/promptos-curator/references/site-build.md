# The site build

How a folder of markdown becomes the PromptOS reading experience. This is the reference
implementation, proven on a live base of 330+ pages.

Stack: **MkDocs** with **Material for MkDocs**, built by one script, running entirely on the
user's machine. Publishing is optional and covered in `commands/publish.md`.

## Table of contents

1. Folder layout
2. The build script
3. The four transforms
4. Block syntax and the compat hook
5. The design system
6. Configuration
7. Tests
8. Pinning and the long term

---

## 1. Folder layout

Content and machinery live in one place, with the machinery in a single folder so the
content stays clean.

```
knowledge-base/
├── README.md            ← landing page
├── SUMMARY.md           ← the sidebar, one Markdown list
├── general/  coding/  videos/ …   ← content, one folder per topic
├── .assets/             ← images
└── _site/               ← everything below is machinery
    ├── build.sh         ← the only entry point
    ├── mkdocs.yml
    ├── hooks/           ← render-time syntax conversion
    ├── tools/           ← the four transforms
    ├── overlay/         ← theme, fonts, generated hub pages
    └── tests/           ← regression checks
```

**The content is never written to by the build.** Every transform runs against a throwaway
copy in `_site/.build`, rebuilt from scratch each run. This matters when the base is synced
with something that also writes, and it keeps the user's files exactly as they left them. A
test enforces it.

## 2. The build script

`_site/build.sh` is the single entry point, used by the local preview and by publishing, so
the two can never drift.

```bash
cd _site && VAULT=.. bash build.sh
```

Steps, in order:

1. Install pinned dependencies.
2. Stage: copy the content, then the overlay, into `.build`.
3. Derive tags from each page's facet footer.
4. Tune search relevance.
5. Convert `SUMMARY.md` into the navigation format MkDocs needs.
6. Build the site into `_site/site`.
7. Run tests. Build failures stop the run. Content warnings report and continue.

That last split matters. A half-written page must never block a publish, and a broken build
must never reach one.

## 3. The four transforms

### `tools/summary_to_nav.py`

`SUMMARY.md` uses `## Headings` for sidebar sections. The navigation plugin reads a single
Markdown list and ignores headings, which silently produces an empty sidebar. This converts
each heading into a parent list item and re-indents children from two spaces to four.

`SUMMARY.md` is left untouched, so it stays valid for any other tool reading it.

### `tools/facets_to_tags.py`

Every page already ends with a facet footer:

```markdown
**Facets:** [Skill](../facets/skill.md) · [Free](../facets/free.md) · [Claude](../facets/claude.md)
```

That is exactly the data the tag system needs, so no page is ever hand-tagged. This lifts
each footer into grouped frontmatter tags and removes the footer, since tags render at the
top of the page:

```yaml
tags:
  - Capability/Skill
  - Access/Free
  - Platform/Claude
```

Groups are `Capability`, `Type`, `Access`, `Platform`, matching the facet tables.

The facet hub pages then generate themselves, with counts that stay correct without anyone
maintaining them.

### `tools/search_tuning.py`

Two fixes for a large base:

- **Hub pages get a boost.** The Tool Index should rank first for a tool query.
- **Generated hub pages leave the index.** Pages that are lists of links match almost every
  query and bury the real answer.

### `hooks/gitbook_compat.py`

Render-time conversion of the block syntax below. Runs in memory; files on disk keep their
original form.

## 4. Block syntax and the compat hook

Pages are written with a small block vocabulary. The hook renders it. The same files also
render in GitBook, so a base can move between the two.

| Written | Renders as |
| --- | --- |
| `{% embed url="…" %}` alone on a line | A video player for YouTube, a link card otherwise |
| `{% embed url="…" %}` mid sentence | An inline link, since a block element would break the line |
| `{% prompt description="…" %} … {% endprompt %}` | A collapsible block with a copy button |
| `{% hint style="info\|warning" %} … {% endhint %}` | A coloured callout |
| `{% file src="…" %}` | A download card |

Three rules learned the hard way:

1. **Skip fenced code.** A page that documents this syntax shows it inside a code fence.
   Converting those examples corrupts the documentation. The hook ignores any match that
   starts inside a fence.
2. **Send a referrer.** A YouTube embed with `referrerpolicy="no-referrer"` fails with
   "Error 153" and shows a grey box. Leave the referrer alone and add a fallback link under
   every player.
3. **Raw HTML needs `markdown="1"`.** A block level element swallows its contents otherwise,
   and every link inside renders as literal text.

Asset paths are rewritten to absolute URLs, because MkDocs skips dot-directories and because
relative paths break under directory URLs.

## 5. The design system

Dark first. The reading surface is near black, one electric accent carries emphasis, and
panels are glass.

### Colour

| Token | Value | Use |
| --- | --- | --- |
| Ground | `#04060c` | Page background |
| Surface | `#0b1120` | Code, panels |
| Accent | `#2e8bff` | Links, active states |
| Accent bright | `#3ce1ff` | Hover, current page |
| Accent deep | `#8b5cf6` | Gradient tail |
| Foreground | `#f8fafc` | Body text |

Proportion matters more than the values: roughly 68% ground, 22% accent family, 10%
highlight. Accent used sparingly keeps it meaningful.

Gradients: headings run white to pale blue to accent. Cards carry a `120deg` accent ramp on
one edge. Glow is `0 0 40px -8px` of the accent at 60%, on players, figures and hover.

Glass: `rgba(13, 20, 36, 0.55)` with a 16px blur and a `rgba(140, 170, 220, 0.14)` hairline.

### Type

| Role | Face | Notes |
| --- | --- | --- |
| Display | Space Grotesk | 600 to 700, tracking -2% |
| Body | Glacial Indifference | Self hosted, SIL OFL |
| Technical | JetBrains Mono | Uppercase, wide tracking, for labels and tags |

Sizes are set in `rem`, and Material scales the root to 137.5% above 1220px, so `1rem` is
22px on a desktop. Body sits at `0.70rem`, which lands near 15px.

### Layout

Article measure is capped at `34rem`, near 750px, and centred in its column. Material pins
those margins with `[dir="ltr"]`-prefixed selectors, so an override has to match that
selector shape or the article stays glued to the sidebar.

Sidebar rhythm carries the hierarchy: section labels are small, uppercase, tracked and
accent coloured; page links are larger, sentence case and quieter. Wrapped titles use a
tighter line height than the gap between items, so a two line title reads as one entry.

## 6. Configuration

`mkdocs.yml` essentials:

- `docs_dir: .build`, the staging copy
- `use_directory_urls: true`
- `literate-nav` reading the generated nav file
- `search` with a separator tuned for tool names
- `tags` with hierarchy on, separator `/`, and scoped listings per group
- The compat hook, and both stylesheets

## 7. Tests

Each test exists because the thing it checks broke in production.

| Check | The failure it prevents |
| --- | --- |
| No unconverted block syntax | Inline embeds shipped raw onto 23 pages |
| Syntax template stays literal | The page template was corrupted by its own converter |
| Every asset resolves | Filenames with spaces and brackets were truncated |
| Nav covers every entry | The sidebar silently emptied |
| Link cards render anchors | 130 cards showed raw markdown |
| Players send a referrer | Every video showed an error box |
| The content is never written to | A transform edited the user's files in place |

Split them: build integrity blocks a publish, content quality reports and continues.

## 8. Pinning and the long term

Pin the versions. Material for MkDocs is in maintenance mode and MkDocs upstream plans a
version that drops the plugin system, so a floating range is a liability. A pinned build
keeps working, and upgrades happen on purpose.

The deeper protection is the shape of the thing: the content is plain markdown in folders.
Swapping the renderer later touches configuration and leaves every page alone.
