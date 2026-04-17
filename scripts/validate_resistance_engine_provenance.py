"""Validate resistance-engine provenance against the canonical repo root."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from import_superpowers_catalog import _sha256_digest
from resistance_engine_consolidation import (
    VALID_LOCAL_SYNC_POLICIES,
    build_policy_index,
    load_consolidation_overrides,
)

_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class ArtifactError(ValueError):
    """Raised when a provenance artifact is missing or malformed."""


def _artifact_name(path: Path, output_root: Path) -> str:
    return path.relative_to(output_root).as_posix()


def load_json(path: Path, output_root: Path) -> Any:
    artifact_name = _artifact_name(path, output_root)
    if not path.exists():
        raise ArtifactError(f"missing required artifact: {artifact_name}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ArtifactError(f"invalid JSON in artifact: {artifact_name}") from exc


def _load_entry_list(path: Path, output_root: Path) -> list[dict[str, Any]]:
    payload = load_json(path, output_root)
    if not isinstance(payload, list):
        raise ArtifactError(
            f"artifact must contain a list: {_artifact_name(path, output_root)}"
        )
    return payload


def _index_entries(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {entry["entry_id"]: entry for entry in entries}


def _duplicate_entry_ids(entries: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for entry in entries:
        entry_id = entry["entry_id"]
        if entry_id in seen:
            duplicates.add(entry_id)
        seen.add(entry_id)
    return sorted(duplicates)


def _has_valid_digest(value: Any) -> bool:
    return isinstance(value, str) and _DIGEST_PATTERN.fullmatch(value) is not None


def _validate_file_record_digests(file_record: dict[str, Any]) -> list[str]:
    if _has_valid_digest(file_record.get("source_digest")) and _has_valid_digest(
        file_record.get("local_digest")
    ):
        return []
    return [f"missing or malformed digest for file: {file_record['local_file']}"]


def _derive_manifest_state(file_states: set[str]) -> str:
    if "drift-detected" in file_states:
        return "drift-detected"
    if "missing-local-copy" in file_states:
        return "missing-local-copy"
    if "source-missing" in file_states:
        return "source-missing"
    return "imported"


def _expected_manifest_local_files(catalog_entry: dict[str, Any]) -> set[str]:
    if catalog_entry["entry_type"] == "agent":
        return {catalog_entry["local_path"]}
    return {
        f"{catalog_entry['local_path']}/{relative_path}"
        for relative_path in catalog_entry["imported_files"]
    }


def _validated_catalog_entries(
    entries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    valid_entries: list[dict[str, Any]] = []
    required_fields = (
        "entry_type",
        "name",
        "source_repo",
        "source_path",
        "local_path",
        "imported_files",
        "source_revision",
        "imported_at",
    )
    for entry in entries:
        missing_fields = [field for field in required_fields if field not in entry]
        if missing_fields:
            for field in missing_fields:
                errors.append(f"malformed catalog entry missing field: {field}")
            continue
        valid_entries.append(entry)
    return valid_entries, errors


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
    required_file_fields = {
        "source_file",
        "local_file",
        "file_state",
        "local_sync_policy",
    }

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

        if not local_file.exists():
            observed_state = "missing-local-copy"
            if recorded_file_state != observed_state and local_sync_policy != "pruned":
                errors.append(f"missing local file for imported entry: {entry['entry_id']}")
        elif not local_file.is_file():
            observed_state = recorded_file_state
            errors.append(f"expected file path is a directory: {updated_record['local_file']}")
        else:
            local_digest = _sha256_digest(local_file)
            updated_record["local_digest"] = local_digest
            if _has_valid_digest(updated_record.get("source_digest")) and updated_record["source_digest"] != local_digest:
                observed_state = "drift-detected"
                if recorded_file_state != observed_state:
                    errors.append(
                        f"digest mismatch for local file: {updated_record['local_file']}"
                    )
            else:
                observed_state = "imported"
            if local_sync_policy == "pruned":
                errors.append(
                    f"pruned file must be absent locally: {updated_record['source_file']}"
                )

        if (
            updated_record["file_state"] != observed_state
            and not (
                local_sync_policy == "pruned" and observed_state == "missing-local-copy"
            )
        ):
            errors.append(f"entry/file state disagreement: {entry['entry_id']}")

        updated_record["file_state"] = observed_state
        if not (local_sync_policy == "pruned" and observed_state == "missing-local-copy"):
            observed_file_states.add(observed_state)

        reconciled_files.append(updated_record)

    updated_entry = dict(entry)
    updated_entry["files"] = reconciled_files
    observed_manifest_state = _derive_manifest_state(observed_file_states)
    updated_entry["manifest_state"] = observed_manifest_state

    if entry["manifest_state"] != observed_manifest_state:
        errors.append(f"entry/file state disagreement: {entry['entry_id']}")

    return updated_entry, errors


def _reconcile_source_missing_entry(
    entry: dict[str, Any], output_root: Path
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    reconciled_files: list[dict[str, Any]] = []

    for file_record in entry["files"]:
        local_file = output_root / file_record["local_file"]
        updated_record = dict(file_record)
        errors.extend(_validate_file_record_digests(updated_record))
        if updated_record["file_state"] != "source-missing":
            errors.append(f"entry/file state disagreement: {entry['entry_id']}")
        if local_file.exists():
            errors.append(f"source-missing entry still has local file: {entry['entry_id']}")
        reconciled_files.append(updated_record)

    updated_entry = dict(entry)
    updated_entry["files"] = reconciled_files
    updated_entry["manifest_state"] = "source-missing"
    if entry["manifest_state"] != "source-missing":
        errors.append(f"entry/file state disagreement: {entry['entry_id']}")

    return updated_entry, errors


def validate_provenance(output_root: Path) -> tuple[list[dict[str, Any]], list[str], bool]:
    catalog_raw = _load_entry_list(output_root / "catalog" / "catalog_index.json", output_root)
    manifest_raw = _load_entry_list(
        output_root / "provenance" / "provenance_manifest.json", output_root
    )
    try:
        overrides, _ = load_consolidation_overrides(output_root)
    except ValueError as exc:
        raise ArtifactError(str(exc)) from exc
    catalog, catalog_errors = _validated_catalog_entries(catalog_raw)
    manifest, manifest_errors = _validated_manifest_entries(manifest_raw)

    catalog_entries = [
        {"entry_id": f"{entry['entry_type']}:{entry['name']}", **entry} for entry in catalog
    ]
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


def main(argv: list[str] | None = None) -> int:
    args = argv or []
    output_root = Path(args[0]) if args else Path(".")

    try:
        updated_manifest, errors, can_write = validate_provenance(output_root)
    except ArtifactError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    if can_write:
        manifest_path.write_text(json.dumps(updated_manifest, indent=2) + "\n")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("provenance manifest valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
