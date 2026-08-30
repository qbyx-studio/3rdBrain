from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_repository_sources_route_through_verified_selective_analysis():
    curator = read("skills/3rdbrain-curator/SKILL.md")
    process = read("skills/3rdbrain-process/references/contract.md")
    reference = read("skills/3rdbrain-curator/references/repository-analysis.md")

    assert "references/repository-analysis.md" in curator
    assert "references/repository-analysis.md" in process
    assert "Map before reading deeply" in reference
    assert "smallest complete set of files" in reference
    assert "Never execute setup scripts" in reference
    assert "documented" in reference and "implemented" in reference


def test_social_sources_preserve_conversation_structure_and_access_gaps():
    curator = read("skills/3rdbrain-curator/SKILL.md")
    process = read("skills/3rdbrain-process/references/contract.md")
    reference = read("skills/3rdbrain-curator/references/social-analysis.md")

    assert "references/social-analysis.md" in curator
    assert "references/social-analysis.md" in process
    assert "parent-child relationships" in reference
    assert "latest visible edits are authoritative" in reference
    assert "pagination and nested replies" in reference
    assert "Never import cookies" in reference


def test_documents_use_native_structure_before_selective_visual_or_ocr_work():
    curator = read("skills/3rdbrain-curator/SKILL.md")
    process = read("skills/3rdbrain-process/references/contract.md")
    reference = read("skills/3rdbrain-curator/references/document-analysis.md")

    assert "references/document-analysis.md" in curator
    assert "references/document-analysis.md" in process
    for format_name in ("PDF", "EPUB", "DOCX", "PPTX", "XLSX"):
        assert f"### {format_name}" in reference
    assert "Extract native text and structure first" in reference
    assert "OCR only to pages" in reference
    assert "content hash" in reference
    assert "page, chapter/section, slide or sheet/cell range" in reference
