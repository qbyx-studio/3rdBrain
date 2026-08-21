from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent


def test_python_runner_survives_from_build_into_manifest_verification():
    script = (ROOT / "deploy.sh").read_text(encoding="utf-8")
    assignment = 'PYTHON="${PYTHON:-.venv/Scripts/python.exe}"'
    verify = '"$PYTHON" tools/verify_deployment_manifest.py'
    assignment_match = re.search(rf"^{re.escape(assignment)}$", script, re.M)

    assert assignment_match, "PYTHON must be assigned in the deploy shell, not one command"
    assert assignment_match.start() < script.index(verify)
