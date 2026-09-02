from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMMAND_SKILLS = {
    "3rdbrain.md": "3rdbrain-setup",
    "connect.md": "3rdbrain-connect",
    "process.md": "3rdbrain-process",
    "publish.md": "3rdbrain-publish",
    "skills.md": "3rdbrain-skillsync",
    "stalecheck.md": "3rdbrain-stalecheck",
}


def test_claude_commands_delegate_to_canonical_cross_runtime_skills():
    assert {path.name for path in (ROOT / "commands").glob("*.md")} == set(COMMAND_SKILLS)

    for command_name, skill_name in COMMAND_SKILLS.items():
        command = (ROOT / "commands" / command_name).read_text(encoding="utf-8")
        skill = ROOT / "skills" / skill_name / "SKILL.md"

        assert skill.exists(), f"{command_name} delegates to missing skill {skill_name}"
        assert f"skills/{skill_name}/SKILL.md" in command
        assert len(command.splitlines()) <= 10, f"{command_name} duplicated its skill contract"


def test_operation_skills_own_their_contracts():
    for skill_name in set(COMMAND_SKILLS.values()) - {"3rdbrain-skillsync"}:
        skill_dir = ROOT / "skills" / skill_name
        assert "references/contract.md" in (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert (skill_dir / "references" / "contract.md").exists()
