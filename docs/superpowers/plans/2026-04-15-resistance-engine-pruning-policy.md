# Resistance Engine Pruning Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit pruning-policy support so intentionally omitted imported files remain provenance-aware, survive importer refreshes, and validate cleanly.

**Architecture:** Introduce one shared override helper module for loading and validating `resistance-engine/consolidation/consolidation_overrides.json`, then thread its `local_sync_policy` values through the importer and provenance validator. Keep lineage state (`manifest_state` / `file_state`) separate from pruning intent so the manifest still describes the imported source set even when a local copy is intentionally absent.

**Tech Stack:** Python 3.12, stdlib `json`/`pathlib`, pytest, existing import/validation scripts

---

## File Map

- Create: `scripts/resistance_engine_consolidation.py` - shared constants and helpers for reading, validating, indexing, and restoring consolidation override policy.
- Create: `resistance-engine/consolidation/consolidation_overrides.json` - checked-in local override file; start with an empty list.
- Modify: `scripts/import_superpowers_catalog.py` - preserve the override file during refresh, default every manifest file record to `local_sync_policy: "required"`, and apply validated overrides.
- Modify: `scripts/validate_resistance_engine_provenance.py` - load override policy, require manifest/override agreement, and make `required` vs `pruned` change whether local-file absence/presence is valid.
- Modify: `tests/scripts/test_import_superpowers_catalog.py` - importer RED/GREEN coverage for default policy, explicit pruning, malformed overrides, unknown targets, override preservation, and source-missing carry-forward.
- Modify: `tests/scripts/test_validate_resistance_engine_provenance.py` - validator RED/GREEN coverage for pruned absence, pruned presence, malformed policy in manifest, and override/manifest mismatches.
- Modify: `resistance-engine/README.md` - document the new override file and the meaning of `required` / `pruned`.
- Modify: `resistance-engine/provenance/provenance_manifest.json` - refresh the committed manifest so every file record includes `local_sync_policy`.

### Task 1: Importer policy support and override preservation

**Files:**
- Create: `scripts/resistance_engine_consolidation.py`
- Create: `resistance-engine/consolidation/consolidation_overrides.json`
- Modify: `scripts/import_superpowers_catalog.py`
- Test: `tests/scripts/test_import_superpowers_catalog.py`

- [ ] **Step 1: Write the failing importer tests**

```python
def test_import_superpowers_catalog_defaults_local_sync_policy_to_required(
    tmp_path: Path,
) -> None:
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

    brainstorming = next(
        entry for entry in result["provenance_manifest"] if entry["entry_id"] == "skill:brainstorming"
    )

    assert [file_record["local_sync_policy"] for file_record in brainstorming["files"]] == [
        "required",
        "required",
    ]


def test_import_superpowers_catalog_applies_pruned_override(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    override_path = output_root / "consolidation" / "consolidation_overrides.json"
    _write(
        override_path,
        json.dumps(
            [
                {
                    "entry_id": "skill:brainstorming",
                    "source_file": "skills/brainstorming/scripts/helper.js",
                    "local_sync_policy": "pruned",
                }
            ],
            indent=2,
        )
        + "\n",
    )

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    brainstorming = next(
        entry for entry in result["provenance_manifest"] if entry["entry_id"] == "skill:brainstorming"
    )
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )

    assert helper_record["local_sync_policy"] == "pruned"


def test_import_superpowers_catalog_preserves_override_file(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    override_path = output_root / "consolidation" / "consolidation_overrides.json"
    override_text = '[{"entry_id":"skill:brainstorming","source_file":"skills/brainstorming/scripts/helper.js","local_sync_policy":"pruned"}]\n'
    _write(override_path, override_text)

    import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert override_path.read_text() == override_text


def test_import_superpowers_catalog_rejects_unknown_override_target(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    _write(
        output_root / "consolidation" / "consolidation_overrides.json",
        json.dumps(
            [
                {
                    "entry_id": "skill:brainstorming",
                    "source_file": "skills/brainstorming/scripts/missing.js",
                    "local_sync_policy": "pruned",
                }
            ],
            indent=2,
        )
        + "\n",
    )

    with pytest.raises(
        ValueError,
        match="override references unknown imported file: skill:brainstorming -> skills/brainstorming/scripts/missing.js",
    ):
        import_superpowers_catalog(
            source_root=source_root,
            output_root=output_root,
            source_repo="vendor/obra-superpowers",
            source_revision="fixture-rev",
            imported_at="2026-04-15T00:00:00Z",
        )


def test_import_superpowers_catalog_rejects_non_list_override_payload(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    _write(
        output_root / "consolidation" / "consolidation_overrides.json",
        '{"entry_id":"skill:brainstorming"}\n',
    )

    with pytest.raises(ValueError, match="consolidation overrides must be a JSON list"):
        import_superpowers_catalog(
            source_root=source_root,
            output_root=output_root,
            source_repo="vendor/obra-superpowers",
            source_revision="fixture-rev",
            imported_at="2026-04-15T00:00:00Z",
        )


def test_import_superpowers_catalog_carries_forward_pruned_policy_for_source_missing_entry(
    tmp_path: Path,
) -> None:
    from import_superpowers_catalog import main

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    _write(
        output_root / "consolidation" / "consolidation_overrides.json",
        json.dumps(
            [
                {
                    "entry_id": "skill:brainstorming",
                    "source_file": "skills/brainstorming/scripts/helper.js",
                    "local_sync_policy": "pruned",
                }
            ],
            indent=2,
        )
        + "\n",
    )

    assert (
        main(
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
        == 0
    )

    shutil.rmtree(source_root / "skills" / "brainstorming")

    assert (
        main(
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
        == 0
    )

    manifest = json.loads((output_root / "provenance" / "provenance_manifest.json").read_text())
    brainstorming = next(entry for entry in manifest if entry["entry_id"] == "skill:brainstorming")
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )

    assert brainstorming["manifest_state"] == "source-missing"
    assert helper_record["local_sync_policy"] == "pruned"
    assert helper_record["file_state"] == "source-missing"
```

- [ ] **Step 2: Run the importer-focused tests to verify they fail**

Run: `timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q`

Expected: FAIL because file records do not contain `local_sync_policy`, the importer does not read `consolidation_overrides.json`, `_reset_output_root()` deletes the override file before validation can use it, and source-missing carry-forward currently has no pruning-policy awareness.

- [ ] **Step 3: Implement the shared override helper and importer wiring**

```python
# scripts/resistance_engine_consolidation.py
from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import TypedDict

CONSOLIDATION_OVERRIDE_RELATIVE_PATH = Path("consolidation") / "consolidation_overrides.json"
VALID_LOCAL_SYNC_POLICIES = {"required", "pruned"}


class ConsolidationOverride(TypedDict):
    entry_id: str
    source_file: str
    local_sync_policy: str


def load_consolidation_overrides(output_root: Path) -> tuple[list[ConsolidationOverride], str | None]:
    override_path = output_root / CONSOLIDATION_OVERRIDE_RELATIVE_PATH
    if not override_path.exists():
        return [], None

    raw_text = override_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw_text)
    except JSONDecodeError as exc:
        raise ValueError("invalid JSON in consolidation overrides") from exc
    if not isinstance(payload, list):
        raise ValueError("consolidation overrides must be a JSON list")

    overrides: list[ConsolidationOverride] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"override entry {index} must be a JSON object")
        entry_id = item.get("entry_id")
        source_file = item.get("source_file")
        local_sync_policy = item.get("local_sync_policy")
        if not isinstance(entry_id, str) or not isinstance(source_file, str):
            raise ValueError(f"override entry {index} must include string entry_id and source_file")
        if local_sync_policy not in VALID_LOCAL_SYNC_POLICIES:
            raise ValueError(
                f"override entry {index} has invalid local_sync_policy: {local_sync_policy!r}"
            )
        overrides.append(
            {
                "entry_id": entry_id,
                "source_file": source_file,
                "local_sync_policy": local_sync_policy,
            }
        )

    return overrides, raw_text


def write_consolidation_override_text(output_root: Path, raw_text: str | None) -> None:
    if raw_text is None:
        return
    override_path = output_root / CONSOLIDATION_OVERRIDE_RELATIVE_PATH
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_path.write_text(raw_text, encoding="utf-8")


def build_policy_index(
    overrides: list[ConsolidationOverride], *, valid_targets: set[tuple[str, str]]
) -> dict[tuple[str, str], str]:
    policy_index: dict[tuple[str, str], str] = {}
    for override in overrides:
        key = (override["entry_id"], override["source_file"])
        if key not in valid_targets:
            raise ValueError(
                f"override references unknown imported file: {override['entry_id']} -> {override['source_file']}"
            )
        policy_index[key] = override["local_sync_policy"]
    return policy_index
```

```python
# scripts/import_superpowers_catalog.py
from resistance_engine_consolidation import (
    build_policy_index,
    load_consolidation_overrides,
    write_consolidation_override_text,
)


def _reset_output_root(output_root: Path, *, preserved_override_text: str | None) -> None:
    if output_root.exists():
        for child in output_root.iterdir():
            if child.name == "README.md":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    output_root.mkdir(parents=True, exist_ok=True)
    write_consolidation_override_text(output_root, preserved_override_text)


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
        "local_sync_policy": "required",
        "source_digest": _sha256_digest(source_file),
        "local_digest": _sha256_digest(local_file),
        "last_verified_at": verified_at,
    }


def import_superpowers_catalog(
    *,
    source_root: Path,
    output_root: Path,
    source_repo: str = SOURCE_REPO,
    source_revision: str | None = None,
    imported_at: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    previous_manifest = _load_existing_manifest(output_root)
    overrides, override_text = load_consolidation_overrides(output_root)
    provenance_manifest: list[dict[str, Any]] = []
    skills_root = source_root / "skills"
    agents_root = source_root / "agents"
    if not skills_root.is_dir():
        raise ValueError(f"missing required source directory: {skills_root}")
    if not agents_root.is_dir():
        raise ValueError(f"missing required source directory: {agents_root}")

    _reset_output_root(output_root, preserved_override_text=override_text)
    revision = source_revision or _detect_source_revision(source_root)
    imported_timestamp = imported_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    catalog_index: list[dict[str, Any]] = []
    claimed_paths: set[str] = set()

    # Keep the existing skill and agent import loops unchanged here.
    current_entry_ids = {entry["entry_id"] for entry in provenance_manifest}
    provenance_manifest.extend(
        _carry_forward_source_missing_entries(
            previous_manifest=previous_manifest,
            current_entry_ids=current_entry_ids,
            source_revision=revision,
            verified_at=imported_timestamp,
        )
    )
    valid_targets = {
        (entry["entry_id"], file_record["source_file"])
        for entry in provenance_manifest
        for file_record in entry["files"]
    }
    policy_index = build_policy_index(overrides, valid_targets=valid_targets)
    for entry in provenance_manifest:
        for file_record in entry["files"]:
            key = (entry["entry_id"], file_record["source_file"])
            file_record["local_sync_policy"] = policy_index.get(key, "required")

    return {
        "catalog_index": catalog_index,
        "non_skill_inventory": _inventory_non_skill_surfaces(source_root),
        "provenance_manifest": provenance_manifest,
    }
```

```json
[]
```

- [ ] **Step 4: Run the importer-focused tests to verify they pass**

Run: `timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q`

Expected: PASS, including preservation of `README.md` and `consolidation/consolidation_overrides.json`.

- [ ] **Step 5: Commit the importer policy work**

```bash
git add \
  scripts/resistance_engine_consolidation.py \
  scripts/import_superpowers_catalog.py \
  resistance-engine/consolidation/consolidation_overrides.json \
  tests/scripts/test_import_superpowers_catalog.py
git commit -m "feat: add pruning policy importer support"
```

### Task 2: Validator policy semantics and manifest agreement checks

**Files:**
- Modify: `scripts/validate_resistance_engine_provenance.py`
- Modify: `tests/scripts/test_validate_resistance_engine_provenance.py`
- Reuse: `scripts/resistance_engine_consolidation.py`

- [ ] **Step 1: Write the failing validator tests**

```python
def _run_import(
    tmp_path: Path, *, overrides: list[dict[str, str]] | None = None
) -> Path:
    from import_superpowers_catalog import main as import_main

    source_root = tmp_path / "vendor" / "obra-superpowers"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming").mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming" / "SKILL.md").write_text(
        "---\nname: brainstorming\n---\n"
    )
    (source_root / "skills" / "brainstorming" / "scripts").mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming" / "scripts" / "helper.js").write_text(
        "console.log('helper');\n"
    )
    (source_root / "agents").mkdir(parents=True, exist_ok=True)
    (source_root / "agents" / "code-reviewer.md").write_text("# reviewer\n")

    output_root = tmp_path / "resistance-engine"
    if overrides is not None:
        override_path = output_root / "consolidation" / "consolidation_overrides.json"
        override_path.parent.mkdir(parents=True, exist_ok=True)
        override_path.write_text(json.dumps(overrides, indent=2) + "\n")

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


def test_validate_provenance_accepts_pruned_file_absence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(
        tmp_path,
        overrides=[
            {
                "entry_id": "skill:brainstorming",
                "source_file": "skills/brainstorming/scripts/helper.js",
                "local_sync_policy": "pruned",
            }
        ],
    )
    (output_root / "skills" / "brainstorming" / "scripts" / "helper.js").unlink()

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    manifest = json.loads((output_root / "provenance" / "provenance_manifest.json").read_text())
    brainstorming = next(entry for entry in manifest if entry["entry_id"] == "skill:brainstorming")
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )

    assert exit_code == 0
    assert helper_record["local_sync_policy"] == "pruned"
    assert helper_record["file_state"] == "missing-local-copy"
    assert "provenance manifest valid" in captured.out


def test_validate_provenance_rejects_present_pruned_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(
        tmp_path,
        overrides=[
            {
                "entry_id": "skill:brainstorming",
                "source_file": "skills/brainstorming/scripts/helper.js",
                "local_sync_policy": "pruned",
            }
        ],
    )

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "pruned file must be absent locally: skills/brainstorming/scripts/helper.js" in captured.err


def test_validate_provenance_rejects_manifest_policy_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["files"][1]["local_sync_policy"] = "pruned"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "manifest override mismatch for file: skill:brainstorming -> skills/brainstorming/scripts/helper.js"
        in captured.err
    )


def test_validate_provenance_rejects_invalid_manifest_policy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["files"][0]["local_sync_policy"] = "skip"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid local_sync_policy for file: skills/brainstorming/SKILL.md" in captured.err
```

- [ ] **Step 2: Run the validator-focused tests to verify they fail**

Run: `timeout 30 .venv/bin/pytest tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q`

Expected: FAIL because the validator ignores `local_sync_policy`, does not compare the manifest to the override file, and still treats every present pruned file or missing required file as the only valid interpretation.

- [ ] **Step 3: Implement policy-aware validation**

```python
# scripts/validate_resistance_engine_provenance.py
from resistance_engine_consolidation import (
    VALID_LOCAL_SYNC_POLICIES,
    build_policy_index,
    load_consolidation_overrides,
)


def _validated_manifest_entries(
    entries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    valid_entries: list[dict[str, Any]] = []
    required_entry_fields = {
        "entry_id",
        "entry_type",
        "name",
        "source_repo",
        "source_path",
        "local_path",
        "manifest_state",
        "source_revision",
        "last_imported_at",
        "last_verified_at",
        "files",
    }
    required_file_fields = {"source_file", "local_file", "file_state", "local_sync_policy"}
    for entry in entries:
        missing_fields = [field for field in required_entry_fields if field not in entry]
        if missing_fields:
            for field in sorted(missing_fields):
                errors.append(f"malformed manifest entry missing field: {field}")
            continue
        if not isinstance(entry["files"], list):
            errors.append("malformed manifest entry field is not a list: files")
            continue

        file_errors = False
        for file_record in entry["files"]:
            missing_file_fields = [
                field for field in required_file_fields if field not in file_record
            ]
            if missing_file_fields:
                for field in sorted(missing_file_fields):
                    errors.append(f"malformed manifest file record missing field: {field}")
                file_errors = True
                continue
            policy = file_record.get("local_sync_policy")
            if policy not in VALID_LOCAL_SYNC_POLICIES:
                errors.append(f"invalid local_sync_policy for file: {file_record['local_file']}")
                file_errors = True
        if file_errors:
            continue
        valid_entries.append(entry)

    return valid_entries, errors
```

```python
def _reconcile_local_files(
    entry: dict[str, Any], output_root: Path
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    reconciled_files: list[dict[str, Any]] = []
    observed_file_states: set[str] = set()

    for file_record in entry["files"]:
        local_file = output_root / file_record["local_file"]
        updated_record = dict(file_record)
        errors.extend(_validate_file_record_digests(updated_record))
        recorded_file_state = updated_record["file_state"]
        local_sync_policy = updated_record["local_sync_policy"]

        if local_sync_policy == "pruned" and local_file.exists():
            observed_state = recorded_file_state
            errors.append(f"pruned file must be absent locally: {updated_record['source_file']}")
        elif not local_file.exists():
            observed_state = "missing-local-copy"
            if recorded_file_state != observed_state and local_sync_policy != "pruned":
                errors.append(f"missing local file for imported entry: {entry['entry_id']}")
        elif not local_file.is_file():
            observed_state = recorded_file_state
            errors.append(f"expected file path is a directory: {updated_record['local_file']}")
        else:
            local_digest = _sha256_digest(local_file)
            updated_record["local_digest"] = local_digest
            if (
                _has_valid_digest(updated_record.get("source_digest"))
                and updated_record["source_digest"] != local_digest
            ):
                observed_state = "drift-detected"
                if recorded_file_state != observed_state:
                    errors.append(f"digest mismatch for local file: {updated_record['local_file']}")
            else:
                observed_state = "imported"

        if updated_record["file_state"] != observed_state:
            errors.append(f"entry/file state disagreement: {entry['entry_id']}")

        updated_record["file_state"] = observed_state
        observed_file_states.add(observed_state)
        reconciled_files.append(updated_record)

    updated_entry = dict(entry)
    updated_entry["files"] = reconciled_files
    observed_manifest_state = _derive_manifest_state(observed_file_states)
    updated_entry["manifest_state"] = observed_manifest_state

    if entry["manifest_state"] != observed_manifest_state:
        errors.append(f"entry/file state disagreement: {entry['entry_id']}")

    return updated_entry, errors
```

```python
def validate_provenance(output_root: Path) -> tuple[list[dict[str, Any]], list[str], bool]:
    catalog_raw = _load_entry_list(output_root / "catalog" / "catalog_index.json", output_root)
    manifest_raw = _load_entry_list(output_root / "provenance" / "provenance_manifest.json", output_root)
    overrides, _ = load_consolidation_overrides(output_root)
    catalog, catalog_errors = _validated_catalog_entries(catalog_raw)
    manifest, manifest_errors = _validated_manifest_entries(manifest_raw)
    catalog_entries = [{"entry_id": f"{entry['entry_type']}:{entry['name']}", **entry} for entry in catalog]
    structural_errors: list[str] = [*catalog_errors, *manifest_errors]
    for entry_id in _duplicate_entry_ids(catalog_entries):
        structural_errors.append(f"duplicate catalog entry_id: {entry_id}")
    for entry_id in _duplicate_entry_ids(manifest):
        structural_errors.append(f"duplicate manifest entry_id: {entry_id}")

    catalog_index = _index_entries(catalog_entries)
    manifest_index = _index_entries(manifest)
    expected_policy_index = build_policy_index(
        overrides,
        valid_targets={
            (entry["entry_id"], file_record["source_file"])
            for entry in manifest
            for file_record in entry["files"]
        },
    )
    updated_manifest: list[dict[str, Any]] = []
    state_errors: list[str] = []

    for entry_id in sorted(catalog_index):
        if entry_id not in manifest_index:
            state_errors.append(f"catalog entry missing manifest entry: {entry_id}")

    for entry in manifest:
        if entry["entry_id"] not in catalog_index and entry["manifest_state"] != "source-missing":
            state_errors.append(f"manifest entry missing catalog entry: {entry['entry_id']}")
        if entry["entry_id"] in catalog_index:
            catalog_entry = catalog_index[entry["entry_id"]]
            metadata_fields = (
                ("source_path", "source_path"),
                ("local_path", "local_path"),
                ("source_repo", "source_repo"),
                ("source_revision", "source_revision"),
                ("last_imported_at", "imported_at"),
            )
            for manifest_field, catalog_field in metadata_fields:
                if entry.get(manifest_field) != catalog_entry.get(catalog_field):
                    state_errors.append(
                        f"manifest metadata mismatch for entry: {entry['entry_id']} ({manifest_field})"
                    )
            expected_files = _expected_manifest_local_files(catalog_entry)
            actual_files = {file_record["local_file"] for file_record in entry["files"]}
            if actual_files != expected_files:
                state_errors.append(f"manifest file coverage mismatch: {entry['entry_id']}")

        for file_record in entry["files"]:
            expected_policy = expected_policy_index.get(
                (entry["entry_id"], file_record["source_file"]),
                "required",
            )
            if file_record["local_sync_policy"] != expected_policy:
                state_errors.append(
                    "manifest override mismatch for file: "
                    f"{entry['entry_id']} -> {file_record['source_file']}"
                )

        if entry["manifest_state"] == "source-missing":
            updated_entry, entry_errors = _reconcile_source_missing_entry(entry, output_root)
        else:
            updated_entry, entry_errors = _reconcile_local_files(entry, output_root)
        updated_manifest.append(updated_entry)
        state_errors.extend(entry_errors)

    return updated_manifest, [*structural_errors, *state_errors], not structural_errors
```

- [ ] **Step 4: Run the validator-focused tests to verify they pass**

Run: `timeout 30 .venv/bin/pytest tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q`

Expected: PASS, including the case where `pruned` plus absent local file is valid and the case where the manifest drifts away from `consolidation_overrides.json` is rejected.

- [ ] **Step 5: Commit the validator policy work**

```bash
git add \
  scripts/validate_resistance_engine_provenance.py \
  tests/scripts/test_validate_resistance_engine_provenance.py
git commit -m "feat: validate pruning policy provenance"
```

### Task 3: Refresh committed artifacts and document the operator workflow

**Files:**
- Modify: `resistance-engine/README.md`
- Modify: `resistance-engine/provenance/provenance_manifest.json`
- Verify: `resistance-engine/consolidation/consolidation_overrides.json`

- [ ] **Step 1: Update the workspace README and keep the override file empty by default**

```markdown
## Layout

- `skills/` - imported skill directories with support files preserved
- `agents/` - imported top-level agent markdown files
- `consolidation/consolidation_overrides.json` - local pruning policy overrides for intentionally omitted imported files
- `catalog/catalog_index.json` - minimal unified index for imported skills and agents
- `catalog/non_skill_inventory.json` - classification output for vendor repo surfaces outside `skills/` and `agents/`

## Provenance

- `provenance/provenance_manifest.json` - authoritative lineage and state for every skill and agent
- every manifest file record carries `local_sync_policy`, which is `required` by default and may be set to `pruned` by the override file

## Consolidation overrides

- keep this file in git and edit it locally when intentionally pruning imported files
- `required` means the imported file must remain present locally
- `pruned` means the imported file should be absent locally while staying in provenance tracking
```

```json
[]
```

- [ ] **Step 2: Regenerate the committed manifest with policy fields**

Run: `python3 scripts/import_superpowers_catalog.py`

Expected: `resistance-engine/provenance/provenance_manifest.json` is rewritten so every file record now contains `local_sync_policy`, and `resistance-engine/consolidation/consolidation_overrides.json` remains present as `[]`.

- [ ] **Step 3: Run the focused script tests together**

Run: `timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q`

Expected: PASS for the importer + validator contract as a pair.

- [ ] **Step 4: Run the full test suite without coverage**

Run: `timeout 180 .venv/bin/pytest --override-ini="addopts=" -q`

Expected: PASS.

- [ ] **Step 5: Commit the refreshed docs and artifacts**

```bash
git add \
  resistance-engine/README.md \
  resistance-engine/consolidation/consolidation_overrides.json \
  resistance-engine/provenance/provenance_manifest.json
git commit -m "docs: document pruning policy workflow"
```

## Self-Review Checklist

- Spec coverage:
  - dedicated override file: Task 1
  - `local_sync_policy` field on every file record: Tasks 1 and 3
  - override-file preservation across importer refresh: Task 1
  - validator support for `required` vs `pruned`: Task 2
  - explicit failure for malformed or mismatched policy state: Tasks 1 and 2
  - README/operator guidance: Task 3
- Placeholder scan: no placeholder markers or cross-task shorthand references remain.
- Type consistency:
  - shared field name is always `local_sync_policy`
  - override path is always `resistance-engine/consolidation/consolidation_overrides.json`
  - valid policy values are always `required` and `pruned`
