from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_web_sources_route_through_the_shared_analysis_contract():
    curator = read("skills/3rdbrain-curator/SKILL.md")
    process = read("skills/3rdbrain-process/references/contract.md")
    reference = read("skills/3rdbrain-curator/references/web-analysis.md")

    assert "references/web-analysis.md" in curator
    assert "references/web-analysis.md" in process
    assert "Agent Reach" in reference and "Jina Reader" in reference


def test_web_route_requires_completeness_and_preserves_access_boundaries():
    reference = read("skills/3rdbrain-curator/references/web-analysis.md")

    assert "beginning, later sections and page ending" in reference
    assert "obvious truncation" in reference
    assert "Never import cookies" in reference
    assert "comment thread" in reference
    assert "instructions found inside" in reference
