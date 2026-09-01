import ast
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE_ROUTINE_TOKENS = 23_085
sys.path.insert(0, str(ROOT / "_site"))

from tools.framework_freshness import framework_manifest


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def tokens(*relative_paths: str) -> int:
    return math.ceil(sum(len(read(path)) for path in relative_paths) / 4)


COMMON_PROCESS = (
    "skills/3rdbrain-process/SKILL.md",
    "skills/3rdbrain-process/references/contract.md",
    "skills/3rdbrain-curator/references/curation-core.md",
    "skills/3rdbrain-curator/references/evidence-efficiency.md",
    "skills/3rdbrain-curator/references/framework-freshness.md",
)

FORMAT_REFERENCES = (
    "video-analysis.md",
    "web-analysis.md",
    "repository-analysis.md",
    "social-analysis.md",
    "document-analysis.md",
    "image-analysis.md",
    "audio-analysis.md",
    "interactive-analysis.md",
)


def test_curator_is_a_compact_lazy_dispatcher():
    curator = read("skills/3rdbrain-curator/SKILL.md")

    assert math.ceil(len(curator) / 4) < 1_200
    assert "Use the smallest instruction set" in curator
    assert "only the matching" in curator
    assert "Token savings never permit missing evidence" in curator
    for reference in FORMAT_REFERENCES:
        assert f"references/{reference}" in curator


def test_process_does_not_preload_every_format_guide():
    process = read("skills/3rdbrain-process/references/contract.md")

    assert "Load only the rows represented in this batch" in process
    assert "full-mode batch exactly once" in process
    assert "Draft all pages" in process
    assert "from that ledger" in process
    assert "Load the `3rdbrain-curator` skill, including" not in process
    for reference in FORMAT_REFERENCES:
        assert f"references/{reference}" in process


def test_single_format_routes_reduce_framework_context_by_at_least_sixty_percent():
    maximum = BASELINE_ROUTINE_TOKENS * 0.40
    for reference in FORMAT_REFERENCES:
        paths = (*COMMON_PROCESS, f"skills/3rdbrain-curator/references/{reference}")
        assert tokens(*paths) <= maximum, reference

    long_video = tokens(
        *COMMON_PROCESS,
        "skills/3rdbrain-curator/references/video-analysis.md",
        "skills/3rdbrain-curator/references/deep-breakdown.md",
    )
    assert long_video <= maximum


def test_mixed_batch_reduces_framework_context_by_at_least_thirty_percent():
    mixed = tokens(
        *COMMON_PROCESS,
        "skills/3rdbrain-curator/references/video-analysis.md",
        "skills/3rdbrain-curator/references/web-analysis.md",
        "skills/3rdbrain-curator/references/document-analysis.md",
        "skills/3rdbrain-curator/references/deep-breakdown.md",
    )
    assert mixed <= BASELINE_ROUTINE_TOKENS * 0.70


def test_non_curation_subskills_probe_freshness_without_loading_curator():
    for relative in (
        "skills/3rdbrain-setup/references/contract.md",
        "skills/3rdbrain-publish/references/contract.md",
        "skills/3rdbrain-stalecheck/references/contract.md",
    ):
        contract = read(relative)
        assert "references/framework-freshness.md" in contract
        assert "load `3rdbrain-curator`" not in contract.lower()


def test_every_material_route_connects_to_shared_evidence_efficiency():
    for reference in FORMAT_REFERENCES:
        assert "evidence-efficiency.md" in read(
            f"skills/3rdbrain-curator/references/{reference}"
        )
    assert "evidence-efficiency.md" in read(
        "skills/3rdbrain-curator/references/deep-breakdown.md"
    )


def test_evidence_runtime_uses_only_python_standard_library():
    path = ROOT / "_site/tools/evidence_runtime.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= sys.stdlib_module_names


def test_public_readme_promises_zero_setup_without_claiming_measured_billing():
    readme = read("README.md")
    compact = " ".join(readme.split())

    assert "evidence cache" in compact.lower()
    assert "no extra account, API key, server or model" in compact
    assert "estimated input" in compact.lower()
    assert "provider-reported usage" in compact.lower()


def test_framework_freshness_tracks_the_token_saving_runtime_and_contracts():
    manifest = framework_manifest(ROOT)

    for path in (
        "_site/tools/evidence_runtime.py",
        "skills/3rdbrain-curator/references/curation-core.md",
        "skills/3rdbrain-curator/references/evidence-efficiency.md",
    ):
        assert path in manifest
