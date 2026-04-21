from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_json(relative_path: str) -> object:
    return json.loads((REPO_ROOT / relative_path).read_text())


def _sha256(relative_path: str) -> str:
    digest = hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()
    return f"sha256:{digest}"


def test_catalog_registers_survivability_skill() -> None:
    catalog = _read_json("catalog/catalog_index.json")

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
    manifest = _read_json("provenance/provenance_manifest.json")
    skill_digest = _sha256("skills/survivability/SKILL.md")

    entry = next(entry for entry in manifest if entry["entry_id"] == "skill:survivability")
    file_record = entry["files"][0]

    assert entry["source_repo"] == "."
    assert entry["manifest_state"] == "imported"
    assert file_record["source_repo"] == "."
    assert file_record["source_file"] == "skills/survivability/SKILL.md"
    assert file_record["local_file"] == "skills/survivability/SKILL.md"
    assert file_record["source_digest"] == skill_digest
    assert file_record["local_digest"] == skill_digest
