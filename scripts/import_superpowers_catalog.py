"""Import vendor Superpowers skills and agent files into the canonical repo root."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from resistance_engine_consolidation import (
    build_policy_index,
    load_consolidation_overrides,
    write_consolidation_override_text,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "vendor" / "obra-superpowers"
DEFAULT_OUTPUT_ROOT = REPO_ROOT
SOURCE_REPO = "vendor/obra-superpowers"
_MANAGED_OUTPUT_PATHS = {
    "agents",
    "catalog",
    "consolidation",
    "provenance",
    "skills",
}

# Local authoring files that overlay the vendored skill content when importing
# from the real vendor tree.  Keys are normalised skill names; values are
# file paths relative to the skill directory.
_AUTHORING_OVERLAY_SKILL_FILES: dict[str, list[str]] = {
    "brainstorming": [
        "SKILL.md",
        "SPEC_REVIEW_MANIFEST.md",
        "SPEC_RUBRIC.md",
        "SPEC_STANDARDS.md",
        "spec-document-reviewer-prompt.md",
    ],
    "writing-plans": [
        "SKILL.md",
        "plan-document-reviewer-prompt.md",
    ],
}
_LOCAL_AUTHORING_SKILLS_ROOT = REPO_ROOT / "skills"
_LOCAL_SOURCE_REPO = "."
_NON_SKILL_DECISIONS = {
    "README.md": "defer",
    "docs": "defer",
    "commands": "defer",
    "hooks": "defer",
    ".claude-plugin": "defer",
    ".cursor-plugin": "defer",
    ".codex": "defer",
    ".opencode": "defer",
    ".github": "ignore",
    ".git": "ignore",
    ".gitattributes": "ignore",
    ".gitignore": "ignore",
    "package.json": "defer",
    "LICENSE": "defer",
    "CODE_OF_CONDUCT.md": "ignore",
    "RELEASE-NOTES.md": "defer",
    "AGENTS.md": "defer",
    "CLAUDE.md": "defer",
    "GEMINI.md": "defer",
    "gemini-extension.json": "defer",
    ".version-bump.json": "ignore",
}


def normalize_name(raw_name: str) -> str:
    normalized = raw_name.strip().lower().replace("_", "-").replace(" ", "-")
    normalized = re.sub(r"[^a-z0-9-]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise ValueError(f"could not normalize name from {raw_name!r}")
    return normalized


def _safe_output_path(output_root: Path, relative_path: Path) -> Path:
    candidate = (output_root / relative_path).resolve()
    root = output_root.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("resolved output path escapes repo root")
    return candidate


def _copy_tree(source_dir: Path, destination_dir: Path) -> list[str]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    imported_files: list[str] = []
    for source_path in sorted(source_dir.rglob("*")):
        if source_path.is_dir():
            continue
        relative = source_path.relative_to(source_dir)
        target = _safe_output_path(destination_dir, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
        imported_files.append(relative.as_posix())
    return imported_files


def _copy_file(source_file: Path, destination_file: Path) -> list[str]:
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, destination_file)
    return [destination_file.name]


def _reset_output_root(output_root: Path, *, preserved_override_text: str | None = None) -> None:
    if output_root.exists():
        output_root_is_repo_root = output_root.resolve() == REPO_ROOT.resolve()
        for child in output_root.iterdir():
            if output_root_is_repo_root and child.name not in _MANAGED_OUTPUT_PATHS:
                continue
            if child.name == "README.md" and not output_root_is_repo_root:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    output_root.mkdir(parents=True, exist_ok=True)
    write_consolidation_override_text(output_root, preserved_override_text)


def _detect_source_revision(source_root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError(f"unable to detect source revision for {source_root}")
    return completed.stdout.strip()


def _sha256_digest(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _sha256_digest_bytes(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


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
        "local_sync_policy": "required",
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
        carried_files: list[dict[str, Any]] = []
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


def _inventory_non_skill_surfaces(source_root: Path) -> list[dict[str, str]]:
    inventory: list[dict[str, str]] = []
    for child in sorted(source_root.iterdir(), key=lambda item: item.name):
        if child.name in {"skills", "agents"}:
            continue
        inventory.append(
            {
                "source_path": child.name,
                "surface_kind": "directory" if child.is_dir() else "file",
                "decision": _NON_SKILL_DECISIONS.get(child.name, "defer"),
            }
        )
    return inventory


def _capture_authoring_overlays() -> dict[tuple[str, str], bytes]:
    captured: dict[tuple[str, str], bytes] = {}
    for skill_name, overlay_files in _AUTHORING_OVERLAY_SKILL_FILES.items():
        overlay_source_dir = _LOCAL_AUTHORING_SKILLS_ROOT / skill_name
        for filename in overlay_files:
            overlay_source = overlay_source_dir / filename
            if overlay_source.is_file():
                captured[(skill_name, filename)] = overlay_source.read_bytes()
    return captured


def _authoring_source_file_key(source_file: Path, output_root: Path) -> str:
    for candidate_root in (output_root.parent, REPO_ROOT):
        try:
            return source_file.relative_to(candidate_root).as_posix()
        except ValueError:
            continue
    raise ValueError(f"overlay source is outside known roots: {source_file}")


def _is_real_vendor_source(source_root: Path) -> bool:
    """Return True only when source_root is the repo's live vendor/obra-superpowers tree."""
    try:
        return source_root.resolve() == (REPO_ROOT / "vendor" / "obra-superpowers").resolve()
    except OSError:
        return False


def _apply_authoring_overlays(
    *,
    output_root: Path,
    catalog_index: list[dict[str, Any]],
    provenance_manifest: list[dict[str, Any]],
    verified_at: str,
    overlay_snapshots: dict[tuple[str, str], bytes] | None = None,
) -> None:
    """Overlay approved local authoring files on top of vendor-imported skill output.

    Copies each listed file from resistance-engine/skills/<skill>/ into the
    generated output and patches the catalog/provenance metadata so that
    digests reflect the overlay content rather than the original vendor file.
    Overlay-only files (absent from vendor) are added to imported_files and
    given new file records.
    """
    for skill_name, overlay_files in _AUTHORING_OVERLAY_SKILL_FILES.items():
        entry_id = f"skill:{skill_name}"
        catalog_entry = next(
            (e for e in catalog_index if e.get("entry_type") == "skill" and e.get("name") == skill_name),
            None,
        )
        manifest_entry = next(
            (e for e in provenance_manifest if e.get("entry_id") == entry_id),
            None,
        )
        if catalog_entry is None or manifest_entry is None:
            continue

        overlay_source_dir = _LOCAL_AUTHORING_SKILLS_ROOT / skill_name
        skill_dest_dir = output_root / "skills" / skill_name

        for filename in overlay_files:
            overlay_source = overlay_source_dir / filename
            dest_file = skill_dest_dir / filename
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            overlay_bytes = None
            if overlay_snapshots is not None:
                overlay_bytes = overlay_snapshots.get((skill_name, filename))
            elif overlay_source.is_file():
                overlay_bytes = overlay_source.read_bytes()
            if overlay_bytes is None:
                continue
            dest_file.write_bytes(overlay_bytes)

            overlay_digest = _sha256_digest_bytes(overlay_bytes)
            local_file_key = f"skills/{skill_name}/{filename}"
            source_file_key = _authoring_source_file_key(overlay_source, output_root)

            existing_record = next(
                (r for r in manifest_entry["files"] if r["local_file"] == local_file_key),
                None,
            )
            if existing_record is not None:
                existing_record["source_file"] = source_file_key
                existing_record["source_repo"] = _LOCAL_SOURCE_REPO
                existing_record["source_digest"] = overlay_digest
                existing_record["local_digest"] = overlay_digest
                existing_record["last_verified_at"] = verified_at
            else:
                manifest_entry["files"].append(
                    {
                        "source_repo": _LOCAL_SOURCE_REPO,
                        "source_file": source_file_key,
                        "local_file": local_file_key,
                        "file_state": "imported",
                        "local_sync_policy": "required",
                        "source_digest": overlay_digest,
                        "local_digest": overlay_digest,
                        "last_verified_at": verified_at,
                    }
                )
                if filename not in catalog_entry["imported_files"]:
                    catalog_entry["imported_files"].append(filename)
        catalog_entry["imported_files"].sort()
        manifest_entry["files"].sort(key=lambda record: record["local_file"])


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
    overlay_snapshots = _capture_authoring_overlays() if _is_real_vendor_source(source_root) else None
    if not skills_root.is_dir():
        raise ValueError(f"missing required source directory: {skills_root}")
    if not agents_root.is_dir():
        raise ValueError(f"missing required source directory: {agents_root}")

    _reset_output_root(output_root, preserved_override_text=override_text)
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
                source_file=skill_dir / Path(relative_path),
                local_file=destination / Path(relative_path),
                source_root=source_root,
                output_root=output_root,
                verified_at=imported_timestamp,
            )
            for relative_path in imported_files
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

    current_entry_ids = {entry["entry_id"] for entry in provenance_manifest}
    provenance_manifest.extend(
        _carry_forward_source_missing_entries(
            previous_manifest=previous_manifest,
            current_entry_ids=current_entry_ids,
            source_revision=revision,
            verified_at=imported_timestamp,
        )
    )

    if _is_real_vendor_source(source_root):
        _apply_authoring_overlays(
            output_root=output_root,
            catalog_index=catalog_index,
            provenance_manifest=provenance_manifest,
            verified_at=imported_timestamp,
            overlay_snapshots=overlay_snapshots,
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

    print(f"imported {len(result['catalog_index'])} entries into {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
