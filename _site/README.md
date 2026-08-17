# The site build

This folder turns the markdown beside it into the PromptOS reading experience.

    cd _site && VAULT=.. bash build.sh

Then serve it:

    .venv/Scripts/python -m mkdocs serve      # Windows
    .venv/bin/python -m mkdocs serve          # macOS and Linux

`/promptos` does all of this for you. The notes below are for anyone who wants to
change the theme or understand the pipeline.

| Path | Purpose |
| --- | --- |
| `build.sh` | The only entry point, used locally and when publishing |
| `mkdocs.yml` | Theme, navigation, search and tag configuration |
| `hooks/` | Renders the page block syntax |
| `tools/` | The transforms: tags, navigation, search tuning, link audits |
| `tools/stalecheck.py` | Age review, report only. Run by `/promptos:stalecheck` |
| `overlay/` | Theme, fonts, logo, and the generated hub pages |
| `tests/` | Regression checks, run on every build |
| `deploy.sh` | Used by `/promptos:publish` |

The content beside this folder is never written to. Every transform runs against a
throwaway copy in `.build`, and a test enforces it.

Full detail lives in `skills/promptos-curator/references/site-build.md`.
