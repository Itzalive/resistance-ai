# Resistance Engine Submodule Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract resistance-engine into the canonical `../resistance-ai` repository, move its importer/validator/tests and any required `vendor/obra-superpowers` dependency there, then replace this repository’s local `resistance-engine/` tree with a git submodule.

**Architecture:** Execute the migration in two phases. First, bootstrap and verify the standalone `../resistance-ai` repo with repo-root layout, plugin metadata, and the moved import/validation toolchain. Second, cut this repository over to a consumer model by removing local ownership, replacing `resistance-engine/` with a submodule, and updating contributor guidance.

**Tech Stack:** git, git submodules, Python 3.12, pytest, uv, JSON plugin manifests, Markdown docs

---

### Task 1: Bootstrap the canonical `resistance-ai` repository and packaging metadata

**Files:**
- Create: `../resistance-ai/tests/test_repo_layout.py`
- Create: `../resistance-ai/pyproject.toml`
- Create: `../resistance-ai/README.md`
- Create: `../resistance-ai/LICENSE`
- Create: `../resistance-ai/.claude-plugin/plugin.json`
- Create: `../resistance-ai/.claude-plugin/marketplace.json`
- Create: `../resistance-ai/package.json`
- Add: `../resistance-ai/vendor/obra-superpowers` (git submodule)

- [ ] **Step 1: Clone or initialize `../resistance-ai` so the RED test has a repo to live in**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
if [ ! -d ../resistance-ai/.git ]; then
  git clone git@github.com:Itzalive/resistance-ai.git ../resistance-ai
fi
mkdir -p ../resistance-ai/tests
```

- [ ] **Step 2: Write the failing repo-layout test**

```python
# ../resistance-ai/tests/test_repo_layout.py
from __future__ import annotations

from pathlib import Path


def test_canonical_repo_contains_release_surfaces() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    required = [
        "README.md",
        "LICENSE",
        "pyproject.toml",
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "package.json",
        "vendor/obra-superpowers",
    ]
    missing = [path for path in required if not (repo_root / path).exists()]
    assert missing == []
```

- [ ] **Step 3: Run the layout test to verify it fails**

Run:

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
timeout 30 .venv/bin/pytest ../resistance-ai/tests/test_repo_layout.py --override-ini="addopts=" -q
```

Expected: FAIL with missing files/directories under `../resistance-ai`.

- [ ] **Step 4: Create the canonical repo skeleton, metadata, and vendor dependency**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
if [ ! -d ../resistance-ai/.git ]; then
  git clone git@github.com:Itzalive/resistance-ai.git ../resistance-ai
fi
cd ../resistance-ai
mkdir -p .claude-plugin tests
cat > pyproject.toml <<'EOF'
[project]
name = "resistance-ai"
version = "0.1.0"
description = "Canonical resistance-engine skills library"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = ["pytest>=9.0.2"]

[tool.pytest.ini_options]
addopts = ""
testpaths = ["tests"]
EOF
cat > README.md <<'EOF'
# resistance-ai

Canonical repository for the resistance-engine skills library, plugin metadata, import/validation tooling, and contract tests.
EOF
cat > LICENSE <<'EOF'
MIT License

Copyright (c) 2026 Pete Forrest
EOF
cat > .claude-plugin/plugin.json <<'EOF'
{
  "name": "resistance-engine",
  "description": "Core skills library for Claude Code: TDD, debugging, collaboration patterns, and proven techniques",
  "version": "0.1.0",
  "author": {
    "name": "Pete Forrest",
    "email": "petemforrest@gmail.com"
  },
  "homepage": "https://github.com/Itzalive/resistance-ai",
  "repository": "https://github.com/Itzalive/resistance-ai",
  "license": "MIT",
  "keywords": ["skills", "tdd", "debugging", "collaboration", "best-practices", "workflows"]
}
EOF
cat > .claude-plugin/marketplace.json <<'EOF'
{
  "name": "resistance-dev",
  "description": "Development marketplace for Resistance Engine core skills library",
  "owner": {
    "name": "Pete Forrest",
    "email": "petemforrest@gmail.com"
  },
  "plugins": [
    {
      "name": "resistance-engine",
      "description": "Core skills library for Claude Code: TDD, debugging, collaboration patterns, and proven techniques",
      "version": "0.1.0",
      "source": "./",
      "author": {
        "name": "Pete Forrest",
        "email": "petemforrest@gmail.com"
      }
    }
  ]
}
EOF
cat > package.json <<'EOF'
{
  "name": "resistance-engine",
  "displayName": "Resistance Engine",
  "description": "Metadata-only VS Code packaging for the resistance-engine skills library",
  "version": "0.1.0",
  "publisher": "Itzalive",
  "license": "MIT",
  "homepage": "https://github.com/Itzalive/resistance-ai",
  "repository": {
    "type": "git",
    "url": "https://github.com/Itzalive/resistance-ai"
  },
  "engines": {
    "vscode": "^1.95.0"
  },
  "categories": ["Other"],
  "keywords": ["copilot", "skills", "tdd", "debugging", "workflow"],
  "private": true
}
EOF
if ! git config -f .gitmodules --get submodule.vendor/obra-superpowers.path >/dev/null 2>&1; then
  git submodule add https://github.com/obra/superpowers vendor/obra-superpowers
fi
uv sync --dev
```

- [ ] **Step 5: Run the layout test to verify it passes**

Run:

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
timeout 30 .venv/bin/pytest ../resistance-ai/tests/test_repo_layout.py --override-ini="addopts=" -q
```

Expected: PASS

- [ ] **Step 6: Commit the canonical repo skeleton**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover/../resistance-ai
git add README.md LICENSE pyproject.toml package.json .claude-plugin tests/test_repo_layout.py .gitmodules vendor/obra-superpowers
git commit -m "feat: bootstrap resistance-ai repository"
```

### Task 2: Move the resistance-engine tree and adapt importer/validator tooling to repo-root layout

**Files:**
- Create: `../resistance-ai/skills/**`
- Create: `../resistance-ai/agents/**`
- Create: `../resistance-ai/catalog/**`
- Create: `../resistance-ai/provenance/**`
- Create: `../resistance-ai/consolidation/**`
- Create: `../resistance-ai/scripts/import_superpowers_catalog.py`
- Create: `../resistance-ai/scripts/validate_resistance_engine_provenance.py`
- Create: `../resistance-ai/scripts/resistance_engine_consolidation.py`
- Create: `../resistance-ai/tests/scripts/test_import_superpowers_catalog.py`
- Create: `../resistance-ai/tests/scripts/test_validate_resistance_engine_provenance.py`
- Create: `../resistance-ai/tests/scripts/test_repo_root_paths.py`
- Modify: `../resistance-ai/README.md`

- [ ] **Step 1: Write the failing repo-root path regression test**

```python
# ../resistance-ai/tests/scripts/test_repo_root_paths.py
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def test_import_superpowers_catalog_defaults_to_repo_root_paths() -> None:
    import import_superpowers_catalog as module

    assert module.DEFAULT_OUTPUT_ROOT == module.REPO_ROOT
    assert module._LOCAL_AUTHORING_SKILLS_ROOT == module.REPO_ROOT / "skills"
```

- [ ] **Step 2: Seed the standalone repo, run the regression test, and watch it fail**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
mkdir -p ../resistance-ai/scripts ../resistance-ai/tests/scripts
cp -rf resistance-engine/. ../resistance-ai/
cp -f scripts/import_superpowers_catalog.py ../resistance-ai/scripts/import_superpowers_catalog.py
cp -f scripts/validate_resistance_engine_provenance.py ../resistance-ai/scripts/validate_resistance_engine_provenance.py
cp -f scripts/resistance_engine_consolidation.py ../resistance-ai/scripts/resistance_engine_consolidation.py
cp -f tests/scripts/test_import_superpowers_catalog.py ../resistance-ai/tests/scripts/test_import_superpowers_catalog.py
cp -f tests/scripts/test_validate_resistance_engine_provenance.py ../resistance-ai/tests/scripts/test_validate_resistance_engine_provenance.py
timeout 30 .venv/bin/pytest ../resistance-ai/tests/scripts/test_repo_root_paths.py --override-ini="addopts=" -q
```

Expected: FAIL because the copied importer still points at `REPO_ROOT / "resistance-engine"` and `REPO_ROOT / "resistance-engine" / "skills"`.

- [ ] **Step 3: Update the copied tooling for repo-root canonical layout**

```python
# ../resistance-ai/scripts/import_superpowers_catalog.py
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "vendor" / "obra-superpowers"
DEFAULT_OUTPUT_ROOT = REPO_ROOT
SOURCE_REPO = "vendor/obra-superpowers"
...
_LOCAL_AUTHORING_SKILLS_ROOT = REPO_ROOT / "skills"
```

```python
# ../resistance-ai/scripts/validate_resistance_engine_provenance.py
# Replace any comparisons that still expect files below REPO_ROOT / "resistance-engine"
# so the validator reads canonical files directly from REPO_ROOT / ...
```

```markdown
# ../resistance-ai/README.md
## Refresh

Run: `python3 scripts/import_superpowers_catalog.py`

## Provenance

Run: `python3 scripts/validate_resistance_engine_provenance.py .`
```

- [ ] **Step 4: Run focused verification for the canonical repo**

Run:

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover/../resistance-ai
uv run pytest -q -o addopts='' \
  tests/test_repo_layout.py \
  tests/scripts/test_repo_root_paths.py \
  tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_matches_live_vendor_repo_shape \
  tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_requires_authoring_default_contracts
```

Expected: PASS

- [ ] **Step 5: Commit the standalone canonical tree and repo-root tooling changes**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover/../resistance-ai
git add README.md skills agents catalog provenance consolidation scripts tests
git commit -m "feat: import resistance-engine into canonical repo"
```

### Task 3: Convert this repository into a resistance-engine submodule consumer

**Files:**
- Create: `tests/scripts/test_resistance_engine_submodule_contract.py`
- Modify: `.gitmodules`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Delete: `scripts/import_superpowers_catalog.py`
- Delete: `scripts/validate_resistance_engine_provenance.py`
- Delete: `scripts/resistance_engine_consolidation.py`
- Delete: `tests/scripts/test_import_superpowers_catalog.py`
- Delete: `tests/scripts/test_validate_resistance_engine_provenance.py`
- Replace: `resistance-engine/` with submodule
- Remove: `vendor/obra-superpowers` submodule

- [ ] **Step 1: Write the failing parent-repo submodule contract test**

```python
# tests/scripts/test_resistance_engine_submodule_contract.py
from __future__ import annotations

from pathlib import Path


def test_resistance_engine_is_tracked_as_a_submodule() -> None:
    gitmodules = Path(".gitmodules").read_text()
    assert '[submodule "resistance-engine"]' in gitmodules
    assert "path = resistance-engine" in gitmodules
    assert "url = https://github.com/Itzalive/resistance-ai" in gitmodules
    assert "vendor/obra-superpowers" not in gitmodules
```

- [ ] **Step 2: Run the submodule contract test to verify it fails**

Run:

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
timeout 30 ../../.venv/bin/pytest tests/scripts/test_resistance_engine_submodule_contract.py --override-ini="addopts=" -q
```

Expected: FAIL because `.gitmodules` still references `vendor/obra-superpowers` and does not define the `resistance-engine` submodule.

- [ ] **Step 3: Replace local ownership with the submodule and update contributor docs**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
git rm -rf vendor/obra-superpowers
git rm -rf resistance-engine
git rm -f scripts/import_superpowers_catalog.py scripts/validate_resistance_engine_provenance.py scripts/resistance_engine_consolidation.py
git rm -f tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py
git submodule add https://github.com/Itzalive/resistance-ai resistance-engine
```

```ini
# .gitmodules
[submodule "resistance-engine"]
	path = resistance-engine
	url = https://github.com/Itzalive/resistance-ai
```

```markdown
# AGENTS.md and CLAUDE.md
## Resistance engine ownership

- `resistance-engine/` is a git submodule sourced from `https://github.com/Itzalive/resistance-ai`
- make resistance-engine changes in the canonical repo, then update the submodule pointer here
- initialize it with `git submodule update --init --recursive resistance-engine`
```

- [ ] **Step 4: Run the parent-repo cutover verification**

Run:

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
timeout 30 ../../.venv/bin/pytest tests/scripts/test_resistance_engine_submodule_contract.py --override-ini="addopts=" -q
git submodule status resistance-engine
```

Expected: `1 passed` and `git submodule status` shows a checked-out commit for `resistance-engine`.

- [ ] **Step 5: Commit the parent-repo consumer cutover**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
git add .gitmodules AGENTS.md CLAUDE.md tests/scripts/test_resistance_engine_submodule_contract.py resistance-engine
git commit -m "chore: consume resistance-engine as submodule"
```

### Task 4: Verify both repositories, push the canonical repo, and merge the parent repo to `main`

**Files:**
- Modify: `resistance-engine` gitlink only if a post-Task-3 canonical repo commit changes the pinned submodule SHA

- [ ] **Step 1: Run the full standalone verification in `resistance-ai`**

Run:

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover/../resistance-ai
uv run pytest -q -o addopts='' tests/test_repo_layout.py tests/scripts/test_repo_root_paths.py tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py
```

Expected: PASS with zero failing tests.

- [ ] **Step 2: Run the parent-repo verification against the submodule consumer state**

Run:

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
timeout 180 ../../.venv/bin/pytest --override-ini="addopts=" -q
```

Expected: PASS for the parent repo test suite after the import/validation tests have been removed and the submodule contract test has been added.

- [ ] **Step 3: Push the canonical repo and only create a parent-repo follow-up commit if the submodule SHA changes**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover/../resistance-ai
git push origin main
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
git submodule status resistance-engine
# If `git -C resistance-engine rev-parse HEAD` differs from the committed gitlink,
# stage `resistance-engine` and create:
# git commit -m "chore: update resistance-engine submodule pointer"
```

- [ ] **Step 4: Merge the feature branch into `main` and push**

```bash
cd /home/pete/source/resistance-ai
git fetch origin
git pull --rebase origin main
git merge --ff-only feat/resistance-engine-authoring-pair-recover
git push origin main
git status
```

Expected: `git status` reports a clean `main` branch up to date with `origin/main`.

- [ ] **Step 5: Record completion and close the work item**

```bash
cd /home/pete/source/resistance-ai/.worktrees/resistance-engine-authoring-pair-recover
bd close resistance-ai-a2a --reason "Done"
bd dolt push
```
