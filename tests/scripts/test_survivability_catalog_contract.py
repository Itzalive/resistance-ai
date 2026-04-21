from __future__ import annotations

import json
from pathlib import Path


def test_catalog_registers_survivability_skill() -> None:
    catalog = json.loads(Path("catalog/catalog_index.json").read_text())

    entry = next(
        entry
        for entry in catalog
        if entry["entry_type"] == "skill" and entry["name"] == "survivability"
    )

    assert entry["source_repo"] == "."
    assert entry["source_path"] == "skills/survivability"
    assert entry["local_path"] == "skills/survivability"
    assert entry["imported_files"] == ["SKILL.md"]


def test_provenance_registers_survivability_skill_file() -> None:
    manifest = json.loads(Path("provenance/provenance_manifest.json").read_text())

    entry = next(entry for entry in manifest if entry["entry_id"] == "skill:survivability")
    file_record = entry["files"][0]

    assert entry["source_repo"] == "."
    assert entry["manifest_state"] == "imported"
    assert file_record["source_repo"] == "."
    assert file_record["source_file"] == "skills/survivability/SKILL.md"
    assert file_record["local_file"] == "skills/survivability/SKILL.md"
    assert file_record["source_digest"] == file_record["local_digest"]
