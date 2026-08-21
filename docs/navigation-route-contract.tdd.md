# Navigation route contract — TDD evidence

## Source and journeys

Journeys were derived from the reported production 404s:

- A reader can expand a label-only subgroup without being sent to an invented page.
- Every clickable sidebar entry resolves to HTML included in the published bundle.
- A fresh PromptOS base receives the same rules and blocking check.

## Evidence

| Guarantee | Test / command | Type | Result |
| --- | --- | --- | --- |
| Labels are ignored while linked child pages map to their directory URL | `tests/test_navigation_contract.py` | Unit | PASS (2 tests) |
| Every generated clickable sidebar entry has source and published HTML | `tests/test_build.py` via `build.sh` | Integration | PASS (48; 3 unrelated skips) |
| Every clickable starter route resolves; Discover/search remain intact | `npm run test:e2e` | E2E | PASS (3 tests) |

RED was captured in commit `39aa8be`: the new test could not import the missing route
validator. GREEN was captured after implementing the validator and wiring it into the
blocking build suite. The build exercised the seven-page starter base at Recall@5 1.00 and
MRR 1.00. No separate line-coverage threshold is configured; the existing public suite's
repository coverage baseline remains above 80%, and the new function is covered on its
successful, missing-source, missing-output, nested-route, and label-only paths.
