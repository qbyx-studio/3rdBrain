"""Fresh-install and upgrade guarantees for the portable discovery package."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tools.knowledge_index import build_discovery_assets


ROOT = Path(__file__).resolve().parent.parent


def test_public_package_ships_the_complete_discovery_front_door():
    assert (ROOT / "overlay" / "discover.md").exists()
    assert (ROOT / "overlay" / "NAV-TOP.md").exists()
    assert (ROOT / "overlay" / "javascripts" / "discovery.js").exists()
    assert (ROOT / "overlay" / "stylesheets" / "discovery.css").exists()


def test_fresh_starter_generates_a_named_searchable_catalog(tmp_path: Path):
    vault = tmp_path / "MyBase"
    shutil.copytree(ROOT / "starter", vault)
    output = tmp_path / "assets" / "discovery"

    result = build_discovery_assets(vault, output)

    assert result["records"] >= 3
    taxonomy = json.loads((output / "taxonomy.json").read_text(encoding="utf-8"))
    assert taxonomy["project"]["name"] == "PromptOS by Qbyx"
    assert (output / "records.json").exists()
    assert (output / "suggestions.json").exists()


def test_existing_base_without_new_config_gets_a_non_destructive_upgrade(tmp_path: Path):
    vault = tmp_path / "ExistingBase"
    vault.mkdir()
    (vault / "README.md").write_text(
        "# RecipeOS\n\nEverything worth cooking twice.\n", encoding="utf-8"
    )
    (vault / "SUMMARY.md").write_text(
        "# Table of contents\n\n* [RecipeOS](README.md)\n", encoding="utf-8"
    )
    output = tmp_path / "assets" / "discovery"

    result = build_discovery_assets(vault, output)

    taxonomy = json.loads((output / "taxonomy.json").read_text(encoding="utf-8"))
    assert result["records"] == 1
    assert taxonomy["project"]["name"] == "RecipeOS"
    assert not (vault / "taxonomy.yml").exists(), "upgrade must not rewrite user content"
    assert not (vault / "search-cases.yml").exists(), "upgrade must not rewrite user content"
