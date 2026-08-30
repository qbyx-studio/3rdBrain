from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_every_video_routes_through_the_shared_analysis_contract():
    curator = read("skills/3rdbrain-curator/SKILL.md")
    process = read("skills/3rdbrain-process/references/contract.md")
    reference = ROOT / "skills/3rdbrain-curator/references/video-analysis.md"

    assert reference.is_file()
    assert "references/video-analysis.md" in curator
    assert "references/video-analysis.md" in process


def test_enhanced_analysis_is_optional_verified_and_credential_free():
    setup = read("skills/3rdbrain-setup/references/contract.md")
    analysis = read("skills/3rdbrain-curator/references/video-analysis.md")
    normalized_setup = " ".join(setup.split())

    assert "Optional enhanced video analysis" in setup
    assert "scripts/run.py smoke-test" in setup
    assert "no transcription API key" in normalized_setup
    assert "portable fallback" in analysis
    assert "spoken" in analysis and "observed" in analysis and "inferred" in analysis
    assert "480p" in analysis
    assert "Raw footage" in analysis and "Video Use" in analysis
