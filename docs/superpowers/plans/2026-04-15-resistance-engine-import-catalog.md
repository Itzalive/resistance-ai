# Resistance Engine Import Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build shard 1 of the resistance-engine rewrite by importing vendor Superpowers skills and agent files into a coherent local workspace, generating a minimal unified catalog index, and inventorying the rest of the vendor repo without blindly mirroring it.

**Architecture:** Add a focused Python importer under `scripts/` that reads `vendor/obra-superpowers/skills/` and `vendor/obra-superpowers/agents/`, writes bounded outputs under `resistance-engine/`, and emits JSON catalog artifacts under `resistance-engine/catalog/`. Back it with pytest coverage in `tests/scripts/`, then run the importer against the live vendor repo to commit the generated `resistance-engine/` workspace and its README.

**Tech Stack:** Python 3.12, pathlib, shutil, json, subprocess, pytest, `.venv/bin/pytest`, `python3`.

**Spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-import-catalog-design.md`
**Primary worktree:** create a fresh task worktree before editing, e.g. `.worktrees/resistance-engine-import`
**Run focused tests:** `timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q`
**Run full suite:** `timeout 180 .venv/bin/pytest --override-ini="addopts=" -q`

---

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `tests/scripts/test_import_superpowers_catalog.py` | **Create** | RED/GREEN coverage for fixture imports, collision failures, path-bounds failures, live vendor discovery counts, and non-skill inventory decisions |
| `scripts/import_superpowers_catalog.py` | **Create** | Deterministic importer for vendor skill directories and agent files, plus unified catalog and non-skill inventory writers |
| `resistance-engine/catalog/catalog_index.json` | **Create via script** | Unified minimal index for imported skills and agents |
| `resistance-engine/catalog/non_skill_inventory.json` | **Create via script** | Classification output for vendor surfaces outside `skills/` and `agents/` |
| `resistance-engine/skills/` | **Create via script** | Imported local skill directories |
| `resistance-engine/agents/` | **Create via script** | Imported local agent files |
| `resistance-engine/README.md` | **Create** | Explain layout, refresh command, and read-only vendor guardrail |

---

## Task 1: Build the importer core with fixture-based RED/GREEN coverage

**Files:**
- Create: `tests/scripts/test_import_superpowers_catalog.py`
- Create later in GREEN: `scripts/import_superpowers_catalog.py`

- [ ] **Step 1: Write the failing fixture tests**

```python
"""Tests for scripts/import_superpowers_catalog.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = str(Path(__file__).parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _fixture_vendor(tmp_path: Path) -> Path:
    source_root = tmp_path / "vendor" / "obra-superpowers"
    _write(
        source_root / "skills" / "brainstorming" / "SKILL.md",
        "---\nname: brainstorming\n---\n",
    )
    _write(
        source_root / "skills" / "brainstorming" / "scripts" / "helper.js",
        "console.log('helper');\n",
    )
    _write(
        source_root / "agents" / "code-reviewer.md",
        "# code-reviewer\n",
    )
    _write(
        source_root / "README.md",
        "# vendor readme\n",
    )
    _write(
        source_root / "docs" / "overview.md",
        "# docs\n",
    )
    return source_root


def test_import_superpowers_catalog_copies_skill_and_agent(tmp_path: Path) -> None:
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

    skill_root = output_root / "skills" / "brainstorming"
    agent_path = output_root / "agents" / "code-reviewer.md"

    assert (skill_root / "SKILL.md").read_text() == "---\nname: brainstorming\n---\n"
    assert (skill_root / "scripts" / "helper.js").read_text() == "console.log('helper');\n"
    assert agent_path.read_text() == "# code-reviewer\n"

    assert result["catalog_index"] == [
        {
            "entry_type": "skill",
            "name": "brainstorming",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "skills/brainstorming",
            "local_path": "skills/brainstorming",
            "imported_files": ["SKILL.md", "scripts/helper.js"],
            "source_revision": "fixture-rev",
            "imported_at": "2026-04-15T00:00:00Z",
        },
        {
            "entry_type": "agent",
            "name": "code-reviewer",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "agents/code-reviewer.md",
            "local_path": "agents/code-reviewer.md",
            "imported_files": ["code-reviewer.md"],
            "source_revision": "fixture-rev",
            "imported_at": "2026-04-15T00:00:00Z",
        },
    ]
    assert result["non_skill_inventory"] == [
        {"source_path": "README.md", "surface_kind": "file", "decision": "defer"},
        {"source_path": "docs", "surface_kind": "directory", "decision": "defer"},
    ]


def test_import_superpowers_catalog_rejects_name_collision(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = tmp_path / "vendor" / "obra-superpowers"
    _write(source_root / "skills" / "My Skill" / "SKILL.md", "---\nname: a\n---\n")
    _write(source_root / "skills" / "my-skill" / "SKILL.md", "---\nname: b\n---\n")
    _write(source_root / "agents" / "code-reviewer.md", "# code-reviewer\n")

    with pytest.raises(ValueError, match="normalized path collision for skill 'my-skill'"):
        import_superpowers_catalog(
            source_root=source_root,
            output_root=tmp_path / "resistance-engine",
            source_repo="vendor/obra-superpowers",
            source_revision="fixture-rev",
            imported_at="2026-04-15T00:00:00Z",
        )


def test_import_superpowers_catalog_rejects_output_escape(tmp_path: Path) -> None:
    from import_superpowers_catalog import _safe_output_path

    with pytest.raises(ValueError, match="resolved output path escapes resistance-engine root"):
        _safe_output_path(tmp_path / "resistance-engine", Path("../escape.txt"))


def test_main_writes_catalog_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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

    catalog = json.loads((output_root / "catalog" / "catalog_index.json").read_text())
    inventory = json.loads((output_root / "catalog" / "non_skill_inventory.json").read_text())

    assert [entry["entry_type"] for entry in catalog] == ["skill", "agent"]
    assert inventory == [
        {"source_path": "README.md", "surface_kind": "file", "decision": "defer"},
        {"source_path": "docs", "surface_kind": "directory", "decision": "defer"},
    ]
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'import_superpowers_catalog'`.

- [ ] **Step 3: Write the minimal importer implementation**

```python
"""Import vendor Superpowers skills and agent files into resistance-engine."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "vendor" / "obra-superpowers"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "resistance-engine"
SOURCE_REPO = "vendor/obra-superpowers"
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
        raise ValueError("resolved output path escapes resistance-engine root")
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


def import_superpowers_catalog(
    *,
    source_root: Path,
    output_root: Path,
    source_repo: str = SOURCE_REPO,
    source_revision: str | None = None,
    imported_at: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    skills_root = source_root / "skills"
    agents_root = source_root / "agents"
    if not skills_root.is_dir():
        raise ValueError(f"missing required source directory: {skills_root}")
    if not agents_root.is_dir():
        raise ValueError(f"missing required source directory: {agents_root}")

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

    return {
        "catalog_index": catalog_index,
        "non_skill_inventory": _inventory_non_skill_surfaces(source_root),
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

    print(f"imported {len(result['catalog_index'])} entries into {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the focused tests and confirm GREEN**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q
```

Expected: PASS with `4 passed`.

- [ ] **Step 5: Commit the importer core**

```bash
git add tests/scripts/test_import_superpowers_catalog.py scripts/import_superpowers_catalog.py
git commit -m "feat(resistance-engine): add importer core"
```

---

## Task 2: Extend the importer for live-repo acceptance and non-skill inventory rigor

**Files:**
- Modify: `tests/scripts/test_import_superpowers_catalog.py`
- Modify: `scripts/import_superpowers_catalog.py`

- [ ] **Step 1: Add failing tests for live repo counts and repeatable output resets**

```python
def test_import_superpowers_catalog_resets_existing_output_root(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "stale.txt").write_text("stale\n")

    import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert not (output_root / "stale.txt").exists()


def test_import_superpowers_catalog_matches_live_vendor_repo_shape(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    repo_root = Path(__file__).parents[2]
    source_root = repo_root / "vendor" / "obra-superpowers"

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=tmp_path / "resistance-engine",
        source_repo="vendor/obra-superpowers",
        source_revision="test-live-revision",
        imported_at="2026-04-15T00:00:00Z",
    )

    skill_entries = [entry for entry in result["catalog_index"] if entry["entry_type"] == "skill"]
    agent_entries = [entry for entry in result["catalog_index"] if entry["entry_type"] == "agent"]
    inventory_paths = {entry["source_path"] for entry in result["non_skill_inventory"]}

    assert len(skill_entries) == 14
    assert len(agent_entries) == 1
    assert agent_entries[0]["name"] == "code-reviewer"
    assert "docs" in inventory_paths
    assert "commands" in inventory_paths
    assert "hooks" in inventory_paths
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q
```

Expected: FAIL because the importer does not yet reset an existing output root before writing fresh files.

- [ ] **Step 3: Extend the importer to reset output roots safely**

```python
def _reset_output_root(output_root: Path) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def import_superpowers_catalog(
    *,
    source_root: Path,
    output_root: Path,
    source_repo: str = SOURCE_REPO,
    source_revision: str | None = None,
    imported_at: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
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

    return {
        "catalog_index": catalog_index,
        "non_skill_inventory": _inventory_non_skill_surfaces(source_root),
    }
```

- [ ] **Step 4: Run the focused tests and confirm GREEN**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q
```

Expected: PASS with `6 passed`.

- [ ] **Step 5: Commit the live-repo importer coverage**

```bash
git add tests/scripts/test_import_superpowers_catalog.py scripts/import_superpowers_catalog.py
git commit -m "feat(resistance-engine): cover live import"
```

---

## Task 3: Generate and document the committed resistance-engine workspace

**Files:**
- Create via script: `resistance-engine/catalog/catalog_index.json`
- Create via script: `resistance-engine/catalog/non_skill_inventory.json`
- Create via script: `resistance-engine/skills/`
- Create via script: `resistance-engine/agents/`
- Create: `resistance-engine/README.md`

- [ ] **Step 1: Run the importer against the live vendor repo**

Run:

```bash
python3 scripts/import_superpowers_catalog.py
```

Expected: prints `imported 15 entries into /home/pete/source/resistance-ai/resistance-engine`.

- [ ] **Step 2: Inspect the generated catalog outputs**

Run:

```bash
python3 - <<'PY'
from __future__ import annotations
import json
from pathlib import Path

root = Path("resistance-engine/catalog")
catalog = json.loads((root / "catalog_index.json").read_text())
inventory = json.loads((root / "non_skill_inventory.json").read_text())

skill_count = sum(1 for entry in catalog if entry["entry_type"] == "skill")
agent_count = sum(1 for entry in catalog if entry["entry_type"] == "agent")
print({"skill_count": skill_count, "agent_count": agent_count, "inventory_count": len(inventory)})
PY
```

Expected: prints `{'skill_count': 14, 'agent_count': 1, 'inventory_count': ...}` with a non-zero inventory count.

- [ ] **Step 3: Write the local workspace README**

```markdown
# resistance-engine

Canonical local workspace for Superpowers-derived skills and agents imported from
`vendor/obra-superpowers/`.

## Layout

- `skills/` — imported skill directories with support files preserved
- `agents/` — imported top-level agent markdown files
- `catalog/catalog_index.json` — minimal unified index for imported skills and agents
- `catalog/non_skill_inventory.json` — classification output for vendor repo surfaces
  outside `skills/` and `agents/`

## Refresh

Run: `python3 scripts/import_superpowers_catalog.py`

## Guardrails

- `vendor/obra-superpowers/` remains read-only
- shard 1 owns import and inventory only; divergence tracking belongs to shard 2
- non-skill vendor content is inventoried and classified before any future import
```

- [ ] **Step 4: Run focused and full validation**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py --override-ini="addopts=" -q && timeout 180 .venv/bin/pytest --override-ini="addopts=" -q
```

Expected: focused importer tests PASS, then full suite PASS.

- [ ] **Step 5: Commit the generated workspace**

```bash
git add resistance-engine/ scripts/import_superpowers_catalog.py tests/scripts/test_import_superpowers_catalog.py
git commit -m "feat(resistance-engine): import initial catalog"
```

---

## Self-review checklist for the execution agent

1. **Spec coverage:** Confirm the final diff contains all required shard-1 surfaces:
   importer script, importer tests, `resistance-engine/` generated outputs, and the
   README.
2. **Boundary check:** Confirm no code writes into `vendor/obra-superpowers/`.
3. **Catalog integrity:** Confirm `catalog_index.json` contains both `skill` and
   `agent` entries and that `non_skill_inventory.json` contains only non-skill,
   non-agent surfaces.
4. **Naming check:** Confirm normalized local names remain kebab-case and that no two
   imported entries map to the same local path.
5. **Reality check:** Re-run the targeted importer tests after any change to file
   names, counts, or output paths.
