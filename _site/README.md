# The site build

Inside a generated knowledge base, this folder turns the Markdown beside it into the 3rdBrain
reading experience.

    cd _site && VAULT=.. bash build.sh

Inside the public framework repository, validate the bundled clean-install fixture instead:

    cd _site && VAULT=starter bash build.sh

Then serve it:

    .venv/Scripts/python -m mkdocs serve      # Windows
    .venv/bin/python -m mkdocs serve          # macOS and Linux

`/3rdbrain` does all of this for you. The notes below are for anyone who wants to
change the theme or understand the pipeline.

| Path | Purpose |
| --- | --- |
| `build.sh` | The only entry point, used locally and when publishing |
| `mkdocs.yml` | Theme, navigation, search and tag configuration |
| `hooks/` | Renders the page block syntax |
| `tools/` | Transforms and checks: tags, navigation, taxonomy, search tuning, link audits |
| `tools/stalecheck.py` | Age review, report only. Run by `/3rdbrain:stalecheck` |
| `overlay/` | Theme, fonts, logo, and the generated hub pages |
| `src/discovery-semantic.worker.js` | Source for zero-LLM local meaning search |
| `tests/` | Regression checks, run on every build |
| `deploy.sh` | Used by `/3rdbrain:publish` |

The content beside this folder is never written to. Every transform runs against a
throwaway copy in `.build`, and a test enforces it.

Pages may declare `primary_section` in frontmatter. The build checks each declaration against
the page's actual top-level section in staged `SUMMARY.md`, preventing a source or vendor hub
from silently becoming the primary category for unrelated extracted workflows. Legacy pages
without the field remain valid.

Full detail lives in `skills/3rdbrain-curator/references/site-build.md`.

After changing the meaning-search worker, run `npm run build:discovery` and commit both its
source and the generated browser bundle. Published sites can use the bundled file without a
Node.js build step.
