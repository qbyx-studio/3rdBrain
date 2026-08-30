from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def routes() -> tuple[str, str]:
    return (
        read("skills/3rdbrain-curator/SKILL.md"),
        read("skills/3rdbrain-process/references/contract.md"),
    )


def test_images_include_photographed_slides_and_selective_verified_ocr():
    curator, process = routes()
    reference = read("skills/3rdbrain-curator/references/image-analysis.md")

    assert "references/image-analysis.md" in curator
    assert "references/image-analysis.md" in process
    assert "student's phone photo of a lecture" in reference
    assert "Do not load every full-resolution image" in reference
    assert "supplied text" in reference and "OCR text" in reference
    assert "every text-bearing region" in reference
    assert "Never open a detected URL" in reference


def test_audio_and_feeds_prefer_maps_and_existing_transcripts():
    curator, process = routes()
    reference = read("skills/3rdbrain-curator/references/audio-analysis.md")

    assert "references/audio-analysis.md" in curator
    assert "references/audio-analysis.md" in process
    assert "Prefer an existing timed transcript" in reference
    assert "private audio" in reference and "paid service" in reference
    assert "GUIDs" in reference and "enclosure URLs" in reference
    assert "reconcile the transcript with duration" in reference


def test_interactive_sources_preserve_access_and_action_boundaries():
    curator, process = routes()
    reference = read("skills/3rdbrain-curator/references/interactive-analysis.md")

    assert "references/interactive-analysis.md" in curator
    assert "references/interactive-analysis.md" in process
    assert "existing user-controlled signed-in session" in reference
    assert "Never bypass a paywall, CAPTCHA, access control" in reference
    assert "Read-only is the default" in reference
    assert "DOM or accessibility tree" in reference
    assert "name every inaccessible or untested state" in reference


def test_public_readme_explains_capabilities_without_helper_dependencies():
    readme = read("README.md")

    assert "photographed lecture slides" in readme
    assert "Podcasts and audio" in readme
    assert "Interactive or login-gated sources" in readme
    for helper_name in ("Agent Reach", "Browser Use", "Firecrawl", "OpenDataLoader"):
        assert helper_name not in readme
