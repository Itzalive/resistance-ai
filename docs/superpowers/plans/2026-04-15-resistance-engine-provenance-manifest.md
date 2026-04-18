# Resistance Engine Provenance Manifest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build shard 2 of the resistance-engine rewrite by adding a central provenance manifest for every skill and agent, extending the importer to emit it, and adding a validator that reconciles local drift and missing-file states against the current local tree.

**Architecture:** Extend `scripts/import_superpowers_catalog.py` so one importer run emits the existing catalog snapshot plus `resistance-engine/provenance/provenance_manifest.json`, including stable entry IDs, file-level provenance, and source-missing carry-forward from prior manifest state. Add `scripts/validate_resistance_engine_provenance.py` as a separate validator that checks catalog/manifest consistency, updates manifest states for missing or drifted local files, and fails explicitly when the manifest and observed local tree disagree.

**Tech Stack:** Python 3.12, pathlib, json, hashlib, shutil, pytest, `.venv/bin/pytest`, `python3`.

**Spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-provenance-manifest-design.md`
**Primary worktree:** create a fresh task worktree before editing, e.g. `.worktrees/resistance-engine-provenance`
**Run focused tests:** `timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q`
**Run full suite:** `timeout 180 .venv/bin/pytest --override-ini="addopts=" -q`

---

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `scripts/import_superpowers_catalog.py` | **Modify** | Emit the central provenance manifest alongside the existing catalog snapshot and carry forward source-missing entries from prior manifest state |
| `scripts/validate_resistance_engine_provenance.py` | **Create** | Reconcile manifest entries against the current local tree, update manifest states for missing/drifted files, and fail on contradictions |
| `tests/scripts/test_import_superpowers_catalog.py` | **Modify** | Cover manifest emission, manifest schema basics, and source-missing carry-forward |
| `tests/scripts/test_validate_resistance_engine_provenance.py` | **Create** | Cover clean validation plus catalog/manifest mismatch, missing local files, drifted local files, and state disagreement |
| `resistance-engine/provenance/provenance_manifest.json` | **Create via script** | Central provenance registry for all skill and agent entries |
| `resistance-engine/README.md` | **Modify** | Document the provenance manifest and validator workflow |

---

## Task 1: Emit a baseline provenance manifest from the importer

**Files:**
- Modify: `tests/scripts/test_import_superpowers_catalog.py`
- Modify later in GREEN: `scripts/import_superpowers_catalog.py`

- [ ] **Step 1: Write the failing importer tests for manifest emission**

```python
def test_import_superpowers_catalog_builds_provenance_manifest(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert result["provenance_manifest"] == [
        {
            "entry_id": "skill:brainstorming",
            "entry_type": "skill",
            "name": "brainstorming",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "skills/brainstorming",
            "local_path": "skills/brainstorming",
            "manifest_state": "imported",
            "source_revision": "fixture-rev",
            "last_imported_at": "2026-04-15T00:00:00Z",
            "last_verified_at": "2026-04-15T00:00:00Z",
            "files": [
                {
                    "source_file": "skills/brainstorming/SKILL.md",
                    "local_file": "skills/brainstorming/SKILL.md",
                    "file_state": "imported",
                    "source_digest": "sha256:99694ffe2b46a3ac37ad2a4c501fa795b5aa723e255aa1f5b99ebe198efb5f73",
                    "local_digest": "sha256:99694ffe2b46a3ac37ad2a4c501fa795b5aa723e255aa1f5b99ebe198efb5f73",
                    "last_verified_at": "2026-04-15T00:00:00Z",
                },
                {
                    "source_file": "skills/brainstorming/scripts/helper.js",
                    "local_file": "skills/brainstorming/scripts/helper.js",
                    "file_state": "imported",
                    "source_digest": "sha256:080aa3dd805c3665de0e06f0267ef9f71c06bbd62ff9a8a17afeceadf635a0be",
                    "local_digest": "sha256:080aa3dd805c3665de0e06f0267ef9f71c06bbd62ff9a8a17afeceadf635a0be",
                    "last_verified_at": "2026-04-15T00:00:00Z",
                },
            ],
        },
        {
            "entry_id": "agent:code-reviewer",
            "entry_type": "agent",
            "name": "code-reviewer",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "agents/code-reviewer.md",
            "local_path": "agents/code-reviewer.md",
            "manifest_state": "imported",
            "source_revision": "fixture-rev",
            "last_imported_at": "2026-04-15T00:00:00Z",
            "last_verified_at": "2026-04-15T00:00:00Z",
            "files": [
                {
                    "source_file": "agents/code-reviewer.md",
                    "local_file": "agents/code-reviewer.md",
                    "file_state": "imported",
                    "source_digest": "sha256:bca5dc168dad2bb212e430262dd973adf0c16c96315e876831e7a7983d051902",
                    "local_digest": "sha256:bca5dc168dad2bb212e430262dd973adf0c16c96315e876831e7a7983d051902",
                    "last_verified_at": "2026-04-15T00:00:00Z",
                }
            ],
        },
    ]


def test_main_writes_catalog_and_provenance_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from import_superpowers_catalog import main

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    exit_code = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "fixture-rev",
            "--imported-at",
            "2026-04-15T00:00:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "imported 2 entries into" in captured.out

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )

    assert [entry["entry_id"] for entry in manifest] == [
        "skill:brainstorming",
        "agent:code-reviewer",
    ]
```

- [ ] **Step 2: Run the focused importer tests and confirm RED**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_builds_provenance_manifest tests/scripts/test_import_superpowers_catalog.py::test_main_writes_catalog_and_provenance_manifest --override-ini="addopts=" -q
```

Expected: FAIL because `import_superpowers_catalog()` does not yet return
`provenance_manifest` and `main()` does not yet write
`resistance-engine/provenance/provenance_manifest.json`.

- [ ] **Step 3: Implement baseline manifest generation in the importer**

```python
import hashlib


def _sha256_digest(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _entry_id(entry_type: str, name: str) -> str:
    return f"{entry_type}:{name}"


def _build_file_record(
    *,
    source_file: Path,
    local_file: Path,
    source_root: Path,
    output_root: Path,
    verified_at: str,
) -> dict[str, str]:
    return {
        "source_file": source_file.relative_to(source_root).as_posix(),
        "local_file": local_file.relative_to(output_root).as_posix(),
        "file_state": "imported",
        "source_digest": _sha256_digest(source_file),
        "local_digest": _sha256_digest(local_file),
        "last_verified_at": verified_at,
    }


def _build_manifest_entry(
    *,
    entry_type: str,
    name: str,
    source_path: str,
    local_path: str,
    source_repo: str,
    source_revision: str,
    imported_at: str,
    file_records: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "entry_id": _entry_id(entry_type, name),
        "entry_type": entry_type,
        "name": name,
        "source_repo": source_repo,
        "source_path": source_path,
        "local_path": local_path,
        "manifest_state": "imported",
        "source_revision": source_revision,
        "last_imported_at": imported_at,
        "last_verified_at": imported_at,
        "files": file_records,
    }


def import_superpowers_catalog(
    *,
    source_root: Path,
    output_root: Path,
    source_repo: str = SOURCE_REPO,
    source_revision: str | None = None,
    imported_at: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    provenance_manifest: list[dict[str, Any]] = []
    skills_root = source_root / "skills"
    agents_root = source_root / "agents"
    if not skills_root.is_dir():
        raise ValueError(f"missing required source directory: {skills_root}")
    if not agents_root.is_dir():
        raise ValueError(f"missing required source directory: {agents_root}")

    _reset_output_root(output_root)
    revision = source_revision or _detect_source_revision(source_root)
    imported_timestamp = imported_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    catalog_index: list[dict[str, Any]] = []
    claimed_paths: set[str] = set()

    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        normalized = normalize_name(skill_dir.name)
        local_relative = Path("skills") / normalized
        local_path = local_relative.as_posix()
        if local_path in claimed_paths:
            raise ValueError(f"normalized path collision for skill {normalized!r}")
        claimed_paths.add(local_path)
        destination = _safe_output_path(output_root, local_relative)
        imported_files = _copy_tree(skill_dir, destination)
        catalog_index.append(
            {
                "entry_type": "skill",
                "name": normalized,
                "source_repo": source_repo,
                "source_path": f"skills/{skill_dir.name}",
                "local_path": local_path,
                "imported_files": imported_files,
                "source_revision": revision,
                "imported_at": imported_timestamp,
            }
        )
        file_records = [
            _build_file_record(
                source_file=skill_dir / relative_path,
                local_file=destination / relative_path,
                source_root=source_root,
                output_root=output_root,
                verified_at=imported_timestamp,
            )
            for relative_path in sorted(Path(path) for path in imported_files)
        ]
        provenance_manifest.append(
            _build_manifest_entry(
                entry_type="skill",
                name=normalized,
                source_path=f"skills/{skill_dir.name}",
                local_path=local_path,
                source_repo=source_repo,
                source_revision=revision,
                imported_at=imported_timestamp,
                file_records=file_records,
            )
        )

    for agent_file in sorted(path for path in agents_root.iterdir() if path.is_file()):
        normalized = normalize_name(agent_file.stem)
        local_relative = Path("agents") / f"{normalized}.md"
        local_path = local_relative.as_posix()
        if local_path in claimed_paths:
            raise ValueError(f"normalized path collision for agent {normalized!r}")
        claimed_paths.add(local_path)
        destination = _safe_output_path(output_root, local_relative)
        imported_files = _copy_file(agent_file, destination)
        catalog_index.append(
            {
                "entry_type": "agent",
                "name": normalized,
                "source_repo": source_repo,
                "source_path": f"agents/{agent_file.name}",
                "local_path": local_path,
                "imported_files": imported_files,
                "source_revision": revision,
                "imported_at": imported_timestamp,
            }
        )
        provenance_manifest.append(
            _build_manifest_entry(
                entry_type="agent",
                name=normalized,
                source_path=f"agents/{agent_file.name}",
                local_path=local_path,
                source_repo=source_repo,
                source_revision=revision,
                imported_at=imported_timestamp,
                file_records=[
                    _build_file_record(
                        source_file=agent_file,
                        local_file=destination,
                        source_root=source_root,
                        output_root=output_root,
                        verified_at=imported_timestamp,
                    )
                ],
            )
        )

    return {
        "catalog_index": catalog_index,
        "non_skill_inventory": _inventory_non_skill_surfaces(source_root),
        "provenance_manifest": provenance_manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--source-repo", default=SOURCE_REPO)
    parser.add_argument("--source-revision")
    parser.add_argument("--imported-at")
    args = parser.parse_args(argv)

    result = import_superpowers_catalog(
        source_root=args.source_root,
        output_root=args.output_root,
        source_repo=args.source_repo,
        source_revision=args.source_revision,
        imported_at=args.imported_at,
    )

    catalog_dir = args.output_root / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    (catalog_dir / "catalog_index.json").write_text(
        json.dumps(result["catalog_index"], indent=2) + "\n"
    )
    (catalog_dir / "non_skill_inventory.json").write_text(
        json.dumps(result["non_skill_inventory"], indent=2) + "\n"
    )
    provenance_dir = args.output_root / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    (provenance_dir / "provenance_manifest.json").write_text(
        json.dumps(result["provenance_manifest"], indent=2) + "\n"
    )
```

- [ ] **Step 4: Run the focused importer tests and confirm GREEN**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_builds_provenance_manifest tests/scripts/test_import_superpowers_catalog.py::test_main_writes_catalog_and_provenance_manifest --override-ini="addopts=" -q
```

Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit the baseline manifest emission**

```bash
git add tests/scripts/test_import_superpowers_catalog.py scripts/import_superpowers_catalog.py
git commit -m "feat(resistance-engine): emit provenance manifest"
```

---

## Task 2: Carry forward source-missing entries in the importer

**Files:**
- Modify: `tests/scripts/test_import_superpowers_catalog.py`
- Modify later in GREEN: `scripts/import_superpowers_catalog.py`

- [ ] **Step 1: Write the failing importer test for source-missing carry-forward**

```python
def test_import_superpowers_catalog_marks_source_missing_entry(tmp_path: Path) -> None:
    from import_superpowers_catalog import main

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    first_exit = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "first-rev",
            "--imported-at",
            "2026-04-15T00:00:00Z",
        ]
    )
    assert first_exit == 0

    shutil.rmtree(source_root / "skills" / "brainstorming")

    second_exit = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "second-rev",
            "--imported-at",
            "2026-04-16T00:00:00Z",
        ]
    )
    assert second_exit == 0

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )

    assert brainstorming["manifest_state"] == "source-missing"
    assert brainstorming["source_revision"] == "second-rev"
    assert brainstorming["files"][0]["file_state"] == "source-missing"
```

- [ ] **Step 2: Run the focused importer test and confirm RED**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_marks_source_missing_entry --override-ini="addopts=" -q
```

Expected: FAIL because the current importer resets `resistance-engine/` and drops the
prior manifest baseline instead of retaining missing source entries.

- [ ] **Step 3: Extend the importer to preserve prior manifest state and mark source-missing entries**

```python
def _load_existing_manifest(output_root: Path) -> list[dict[str, Any]]:
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    if not manifest_path.exists():
        return []
    payload = json.loads(manifest_path.read_text())
    if not isinstance(payload, list):
        raise ValueError("existing provenance manifest must be a list")
    return payload


def _carry_forward_source_missing_entries(
    *,
    previous_manifest: list[dict[str, Any]],
    current_entry_ids: set[str],
    source_revision: str,
    verified_at: str,
) -> list[dict[str, Any]]:
    carried_entries: list[dict[str, Any]] = []
    for entry in previous_manifest:
        if entry["entry_id"] in current_entry_ids:
            continue
        carried_files = []
        for file_record in entry["files"]:
            carried_files.append(
                {
                    **file_record,
                    "file_state": "source-missing",
                    "last_verified_at": verified_at,
                }
            )
        carried_entries.append(
            {
                **entry,
                "manifest_state": "source-missing",
                "source_revision": source_revision,
                "last_verified_at": verified_at,
                "files": carried_files,
            }
        )
    return carried_entries


def import_superpowers_catalog(
    *,
    source_root: Path,
    output_root: Path,
    source_repo: str = SOURCE_REPO,
    source_revision: str | None = None,
    imported_at: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    previous_manifest = _load_existing_manifest(output_root)
    _reset_output_root(output_root)
    skills_root = source_root / "skills"
    agents_root = source_root / "agents"
    if not skills_root.is_dir():
        raise ValueError(f"missing required source directory: {skills_root}")
    if not agents_root.is_dir():
        raise ValueError(f"missing required source directory: {agents_root}")

    revision = source_revision or _detect_source_revision(source_root)
    imported_timestamp = imported_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    catalog_index: list[dict[str, Any]] = []
    provenance_manifest: list[dict[str, Any]] = []
    claimed_paths: set[str] = set()

    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        normalized = normalize_name(skill_dir.name)
        local_relative = Path("skills") / normalized
        local_path = local_relative.as_posix()
        if local_path in claimed_paths:
            raise ValueError(f"normalized path collision for skill {normalized!r}")
        claimed_paths.add(local_path)
        destination = _safe_output_path(output_root, local_relative)
        imported_files = _copy_tree(skill_dir, destination)
        catalog_index.append(
            {
                "entry_type": "skill",
                "name": normalized,
                "source_repo": source_repo,
                "source_path": f"skills/{skill_dir.name}",
                "local_path": local_path,
                "imported_files": imported_files,
                "source_revision": revision,
                "imported_at": imported_timestamp,
            }
        )
        provenance_manifest.append(
            _build_manifest_entry(
                entry_type="skill",
                name=normalized,
                source_path=f"skills/{skill_dir.name}",
                local_path=local_path,
                source_repo=source_repo,
                source_revision=revision,
                imported_at=imported_timestamp,
                file_records=[
                    _build_file_record(
                        source_file=skill_dir / Path(relative_path),
                        local_file=destination / Path(relative_path),
                        source_root=source_root,
                        output_root=output_root,
                        verified_at=imported_timestamp,
                    )
                    for relative_path in imported_files
                ],
            )
        )

    for agent_file in sorted(path for path in agents_root.iterdir() if path.is_file()):
        normalized = normalize_name(agent_file.stem)
        local_relative = Path("agents") / f"{normalized}.md"
        local_path = local_relative.as_posix()
        if local_path in claimed_paths:
            raise ValueError(f"normalized path collision for agent {normalized!r}")
        claimed_paths.add(local_path)
        destination = _safe_output_path(output_root, local_relative)
        imported_files = _copy_file(agent_file, destination)
        catalog_index.append(
            {
                "entry_type": "agent",
                "name": normalized,
                "source_repo": source_repo,
                "source_path": f"agents/{agent_file.name}",
                "local_path": local_path,
                "imported_files": imported_files,
                "source_revision": revision,
                "imported_at": imported_timestamp,
            }
        )
        provenance_manifest.append(
            _build_manifest_entry(
                entry_type="agent",
                name=normalized,
                source_path=f"agents/{agent_file.name}",
                local_path=local_path,
                source_repo=source_repo,
                source_revision=revision,
                imported_at=imported_timestamp,
                file_records=[
                    _build_file_record(
                        source_file=agent_file,
                        local_file=destination,
                        source_root=source_root,
                        output_root=output_root,
                        verified_at=imported_timestamp,
                    )
                ],
            )
        )

    current_entry_ids = {entry["entry_id"] for entry in provenance_manifest}
    provenance_manifest.extend(
        _carry_forward_source_missing_entries(
            previous_manifest=previous_manifest,
            current_entry_ids=current_entry_ids,
            source_revision=revision,
            verified_at=imported_timestamp,
        )
    )
    provenance_manifest.sort(key=lambda entry: (entry["entry_type"], entry["name"]))

    return {
        "catalog_index": catalog_index,
        "non_skill_inventory": _inventory_non_skill_surfaces(source_root),
        "provenance_manifest": provenance_manifest,
    }
```

- [ ] **Step 4: Run the focused importer test and confirm GREEN**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_marks_source_missing_entry --override-ini="addopts=" -q
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit source-missing carry-forward**

```bash
git add tests/scripts/test_import_superpowers_catalog.py scripts/import_superpowers_catalog.py
git commit -m "feat(resistance-engine): retain source-missing provenance"
```

---

## Task 3: Add standalone provenance validation for local drift and missing files

**Files:**
- Create: `tests/scripts/test_validate_resistance_engine_provenance.py`
- Create later in GREEN: `scripts/validate_resistance_engine_provenance.py`
- Modify later in GREEN: `resistance-engine/README.md`

- [ ] **Step 1: Write the failing validator tests**

```python
"""Tests for scripts/validate_resistance_engine_provenance.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = str(Path(__file__).parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _run_import(tmp_path: Path) -> Path:
    from import_superpowers_catalog import main as import_main

    source_root = tmp_path / "vendor" / "obra-superpowers"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming").mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming" / "SKILL.md").write_text(
        "---\nname: brainstorming\n---\n"
    )
    (source_root / "agents").mkdir(parents=True, exist_ok=True)
    (source_root / "agents" / "code-reviewer.md").write_text("# reviewer\n")

    output_root = tmp_path / "resistance-engine"
    exit_code = import_main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "fixture-rev",
            "--imported-at",
            "2026-04-15T00:00:00Z",
        ]
    )
    assert exit_code == 0
    return output_root


def test_validate_provenance_passes_clean_import(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "provenance manifest valid" in captured.out


def test_validate_provenance_rejects_catalog_entry_without_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.pop()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "catalog entry missing manifest entry: agent:code-reviewer" in captured.err


def test_validate_provenance_rejects_imported_entry_with_missing_local_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    (output_root / "skills" / "brainstorming" / "SKILL.md").unlink()

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )

    assert exit_code == 1
    assert brainstorming["manifest_state"] == "missing-local-copy"
    assert "missing local file for imported entry: skill:brainstorming" in captured.err


def test_validate_provenance_rejects_drift_detected_file_digest_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    helper_path = output_root / "agents" / "code-reviewer.md"
    helper_path.write_text("# changed reviewer\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    reviewer = next(entry for entry in manifest if entry["entry_id"] == "agent:code-reviewer")

    assert exit_code == 1
    assert reviewer["manifest_state"] == "drift-detected"
    assert "digest mismatch for local file: agents/code-reviewer.md" in captured.err


def test_validate_provenance_rejects_file_state_entry_state_disagreement(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["files"][0]["file_state"] = "drift-detected"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "entry/file state disagreement: skill:brainstorming" in captured.err
```

- [ ] **Step 2: Run the validator tests and confirm RED**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'validate_resistance_engine_provenance'`.

- [ ] **Step 3: Implement the standalone validator and README updates**

```python
"""Validate resistance-engine provenance against the current local tree."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from import_superpowers_catalog import _sha256_digest


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _index_entries(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {entry["entry_id"]: entry for entry in entries}


def _reconcile_local_files(entry: dict[str, Any], output_root: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    reconciled_files: list[dict[str, Any]] = []
    manifest_state = entry["manifest_state"]

    for file_record in entry["files"]:
        local_file = output_root / file_record["local_file"]
        updated_record = dict(file_record)

        if not local_file.exists():
            updated_record["file_state"] = "missing-local-copy"
            manifest_state = "missing-local-copy"
            errors.append(f"missing local file for imported entry: {entry['entry_id']}")
        else:
            local_digest = _sha256_digest(local_file)
            updated_record["local_digest"] = local_digest
            if updated_record["source_digest"] != local_digest:
                updated_record["file_state"] = "drift-detected"
                manifest_state = "drift-detected"
                errors.append(f"digest mismatch for local file: {updated_record['local_file']}")

        reconciled_files.append(updated_record)

    updated_entry = dict(entry)
    updated_entry["files"] = reconciled_files
    updated_entry["manifest_state"] = manifest_state

    file_states = {record["file_state"] for record in reconciled_files}
    if "drift-detected" in file_states and updated_entry["manifest_state"] != "drift-detected":
        errors.append(f"entry/file state disagreement: {entry['entry_id']}")
    if "missing-local-copy" in file_states and updated_entry["manifest_state"] == "imported":
        errors.append(f"entry/file state disagreement: {entry['entry_id']}")

    return updated_entry, errors


def validate_provenance(output_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    catalog = load_json(output_root / "catalog" / "catalog_index.json")
    manifest = load_json(output_root / "provenance" / "provenance_manifest.json")

    catalog_index = _index_entries(
        [
            {"entry_id": f"{entry['entry_type']}:{entry['name']}", **entry}
            for entry in catalog
        ]
    )
    manifest_index = _index_entries(manifest)
    errors: list[str] = []
    updated_manifest: list[dict[str, Any]] = []

    for entry_id in sorted(catalog_index):
        if entry_id not in manifest_index:
            errors.append(f"catalog entry missing manifest entry: {entry_id}")

    for entry in manifest:
        if entry["manifest_state"] == "source-missing":
            updated_manifest.append(entry)
            continue
        updated_entry, entry_errors = _reconcile_local_files(entry, output_root)
        updated_manifest.append(updated_entry)
        errors.extend(entry_errors)

    return updated_manifest, errors


def main(argv: list[str] | None = None) -> int:
    args = argv or []
    output_root = Path(args[0]) if args else Path("resistance-engine")

    updated_manifest, errors = validate_provenance(output_root)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest_path.write_text(json.dumps(updated_manifest, indent=2) + "\n")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("provenance manifest valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

```markdown
## Provenance

- `provenance/provenance_manifest.json` - authoritative lineage and state for every
  skill and agent

Validate the current local tree against the manifest:

Run: `python3 scripts/validate_resistance_engine_provenance.py`
```

- [ ] **Step 4: Run the focused importer and validator tests and confirm GREEN**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q
```

Expected: PASS with all importer and validator tests green.

- [ ] **Step 5: Commit validator support**

```bash
git add tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py scripts/import_superpowers_catalog.py scripts/validate_resistance_engine_provenance.py resistance-engine/README.md
git commit -m "feat(resistance-engine): validate provenance manifest"
```

---

## Task 4: Generate the live provenance artifact and run final verification

**Files:**
- Create via script: `resistance-engine/provenance/provenance_manifest.json`
- Modify via script: `resistance-engine/catalog/catalog_index.json`
- Modify via script: `resistance-engine/catalog/non_skill_inventory.json`
- Modify: `resistance-engine/README.md`

- [ ] **Step 1: Regenerate the live resistance-engine artifacts**

Run:

```bash
python3 scripts/import_superpowers_catalog.py
```

Expected: prints `imported 15 entries into /home/pete/source/resistance-ai/resistance-engine`.

- [ ] **Step 2: Run the standalone validator against the live workspace**

Run:

```bash
python3 scripts/validate_resistance_engine_provenance.py
```

Expected: prints `provenance manifest valid`.

- [ ] **Step 3: Inspect the live manifest counts**

Run:

```bash
python3 - <<'PY'
from __future__ import annotations
import json
from pathlib import Path

root = Path("resistance-engine/provenance")
manifest = json.loads((root / "provenance_manifest.json").read_text())
skill_count = sum(1 for entry in manifest if entry["entry_type"] == "skill")
agent_count = sum(1 for entry in manifest if entry["entry_type"] == "agent")
state_counts = {}
for entry in manifest:
    state_counts[entry["manifest_state"]] = state_counts.get(entry["manifest_state"], 0) + 1
print({"skill_count": skill_count, "agent_count": agent_count, "state_counts": state_counts})
PY
```

Expected: prints `{'skill_count': 14, 'agent_count': 1, 'state_counts': {'imported': 15}}`.

- [ ] **Step 4: Run focused and full verification**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q && timeout 180 .venv/bin/pytest --override-ini="addopts=" -q
```

Expected: focused provenance tests PASS, then the full suite PASS.

- [ ] **Step 5: Commit the live provenance workspace**

```bash
git add resistance-engine/ scripts/import_superpowers_catalog.py scripts/validate_resistance_engine_provenance.py tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py
git commit -m "feat(resistance-engine): add provenance manifest"
```

---

## Self-review checklist for the execution agent

1. **Spec coverage:** Confirm the final diff includes importer changes, validator script,
   validator tests, updated importer tests, `resistance-engine/provenance/`, and the
   README update.
2. **Boundary check:** Confirm non-skill inventory remains separate and that no
   non-skill surface is inserted into `provenance_manifest.json`.
3. **State logic:** Confirm `source-missing` is importer-owned and local
   `missing-local-copy` / `drift-detected` reconciliation is validator-owned.
4. **Catalog consistency:** Confirm every catalog entry has exactly one manifest entry.
5. **Reality check:** Re-run the targeted importer and validator tests after any change
   to manifest field names, output paths, or state names.
