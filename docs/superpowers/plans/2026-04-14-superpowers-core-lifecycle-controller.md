# Superpowers Core Lifecycle Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the first working shard of the rewrite as a machine-readable lifecycle/controller contract with validation tests, so later overlay and adapter shards build on executable structure instead of more prose.

**Architecture:** Add a local `superpowers-local/` workspace that holds the lifecycle contract as JSON, then validate that contract with a focused Python script under `scripts/` and pytest coverage under `tests/scripts/`. The validator becomes the executable guardrail for the spec’s key invariants: named states, discrete skills, required gates, hook taxonomy, Copilot-first reference harness, and mandatory human confirmation for project-local retention.

**Tech Stack:** Python 3.12, JSON, pytest, pathlib, `python3`, `.venv/bin/pytest`.

**Spec:** `docs/superpowers/specs/2026-04-14-superpowers-overlay-lifecycle-design.md`
**Primary worktree:** create a fresh task worktree before editing, e.g. `.worktrees/superpowers-core-controller`
**Run focused tests:** `timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_contracts.py --override-ini="addopts=" -q`
**Run full suite:** `timeout 180 .venv/bin/pytest --override-ini="addopts=" -q`

---

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `superpowers-local/README.md` | **Create** | Explain the local rewrite workspace, the read-only role of `vendor/obra-superpowers`, and how to validate the controller contract |
| `superpowers-local/controller/lifecycle_contract.json` | **Create** | Machine-readable contract for lifecycle states, skill map, required gates, hook taxonomy, and invariants |
| `scripts/validate_superpowers_contracts.py` | **Create** | Load and validate the lifecycle contract, emit a clear CLI success/error status, and give later shards a reusable validator entrypoint |
| `tests/scripts/test_validate_superpowers_contracts.py` | **Create** | RED/GREEN coverage for happy-path validation plus negative-path failures for numbered phases and missing human-confirmation invariants |

---

## Task 1: Add RED coverage for the lifecycle contract validator

**Expected RED failure mode:** the validator script does not exist, the contract file does not exist, and the repo has no executable check for the controller invariants from the approved spec.

**Files:**
- Create: `tests/scripts/test_validate_superpowers_contracts.py`
- Create later in GREEN: `scripts/validate_superpowers_contracts.py`
- Create later in GREEN: `superpowers-local/controller/lifecycle_contract.json`

- [ ] **Step 1: Write the failing validator tests**

```python
"""Tests for scripts/validate_superpowers_contracts.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make scripts/ importable
_SCRIPTS_DIR = str(Path(__file__).parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_CONTRACT_PATH = (
    Path(__file__).parents[2]
    / "superpowers-local"
    / "controller"
    / "lifecycle_contract.json"
)


def _valid_contract() -> dict:
    return {
        "version": 1,
        "states": [
            "session-intake",
            "brainstorming",
            "spec-audit",
            "plan-writing",
            "workspace-setup",
            "execution",
            "debugging",
            "review",
            "survivability",
            "retrospective",
            "finish",
        ],
        "required_gates": [
            "approval",
            "review",
            "retrospective",
            "finish",
            "survivability",
        ],
        "phase_hooks": [
            "brainstorming.preflight",
            "spec-audit.preflight",
            "plan-writing.preflight",
            "execution.preflight",
            "review.preflight",
            "finish.preflight",
        ],
        "decision_hooks": [
            "resolve-test-command",
            "resolve-build-command",
            "resolve-sensitive-data-rules",
            "resolve-human-approval-rules",
            "resolve-issue-tracker-rules",
        ],
        "skill_map": {
            "session-intake": ["using-resistance-engine"],
            "brainstorming": ["brainstorming"],
            "plan-writing": ["writing-plans"],
            "workspace-setup": ["using-git-worktrees"],
            "execution": [
                "executing-plans",
                "subagent-driven-development",
                "test-driven-development",
            ],
            "debugging": ["systematic-debugging"],
            "review": ["requesting-code-review", "receiving-code-review"],
            "finish": [
                "verification-before-completion",
                "finishing-a-development-branch",
            ],
            "skill-evolution": ["writing-skills"],
        },
        "invariants": {
            "reference_harness": "copilot-cli",
            "numbered_phases_forbidden": True,
            "specialized_skills_remain_discrete": True,
            "human_confirmation_required_for_project_overlay": True,
            "claude_adapter_requires_explicit_downgrade": True,
        },
    }


def test_repo_contract_validates():
    from validate_superpowers_contracts import load_contract, validate_contract

    contract = load_contract(_CONTRACT_PATH)

    validate_contract(contract)

    assert contract["states"][0] == "session-intake"
    assert contract["skill_map"]["brainstorming"] == ["brainstorming"]
    assert "finish.preflight" in contract["phase_hooks"]


def test_validate_contract_rejects_numbered_phases():
    from validate_superpowers_contracts import validate_contract

    contract = _valid_contract()
    contract["states"][0] = "phase-1"

    with pytest.raises(ValueError, match="numbered phases are forbidden"):
        validate_contract(contract)


def test_validate_contract_rejects_missing_human_confirmation_invariant():
    from validate_superpowers_contracts import validate_contract

    contract = _valid_contract()
    del contract["invariants"]["human_confirmation_required_for_project_overlay"]

    with pytest.raises(
        ValueError,
        match="human_confirmation_required_for_project_overlay invariant is required",
    ):
        validate_contract(contract)


def test_main_prints_success_for_repo_contract(capsys):
    from validate_superpowers_contracts import main

    exit_code = main([str(_CONTRACT_PATH)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"validated {_CONTRACT_PATH}" in captured.out
```

- [ ] **Step 2: Run the focused test file and confirm RED**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_contracts.py --override-ini="addopts=" -q
```

Expected: FAIL because `validate_superpowers_contracts.py` is missing and the contract
file at `superpowers-local/controller/lifecycle_contract.json` does not exist yet.

- [ ] **Step 3: Commit the RED state**

Run:

```bash
git add tests/scripts/test_validate_superpowers_contracts.py
git commit -m "test(superpowers): add lifecycle contract validator red coverage" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Expected: one RED commit containing only the new failing test file.

---

## Task 2: Implement the lifecycle contract and validator

**Expected GREEN target:** the repo contains a concrete lifecycle contract, the validator accepts the approved contract, and the negative-path tests reject the core regressions discussed in the spec.

**Files:**
- Create: `scripts/validate_superpowers_contracts.py`
- Create: `superpowers-local/controller/lifecycle_contract.json`
- Check: `tests/scripts/test_validate_superpowers_contracts.py`

- [ ] **Step 1: Create the validator script**

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_STATES = [
    "session-intake",
    "brainstorming",
    "spec-audit",
    "plan-writing",
    "workspace-setup",
    "execution",
    "debugging",
    "review",
    "survivability",
    "retrospective",
    "finish",
]

REQUIRED_GATES = [
    "approval",
    "review",
    "retrospective",
    "finish",
    "survivability",
]

REQUIRED_PHASE_HOOKS = [
    "brainstorming.preflight",
    "spec-audit.preflight",
    "plan-writing.preflight",
    "execution.preflight",
    "review.preflight",
    "finish.preflight",
]

REQUIRED_DECISION_HOOKS = [
    "resolve-test-command",
    "resolve-build-command",
    "resolve-sensitive-data-rules",
    "resolve-human-approval-rules",
    "resolve-issue-tracker-rules",
]

REQUIRED_SKILLS = {
    "using-resistance-engine",
    "brainstorming",
    "writing-plans",
    "using-git-worktrees",
    "executing-plans",
    "subagent-driven-development",
    "test-driven-development",
    "systematic-debugging",
    "requesting-code-review",
    "receiving-code-review",
    "verification-before-completion",
    "finishing-a-development-branch",
    "writing-skills",
}


def load_contract(path: Path) -> dict:
    return json.loads(path.read_text())


def _ensure_unique(name: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")


def validate_contract(contract: dict) -> None:
    states = contract.get("states")
    if any(state.startswith("phase-") or state.startswith("phase_") for state in states):
        raise ValueError("numbered phases are forbidden")
    if states != REQUIRED_STATES:
        raise ValueError("states must match the approved named lifecycle order")
    _ensure_unique("states", states)

    required_gates = contract.get("required_gates")
    if required_gates != REQUIRED_GATES:
        raise ValueError("required_gates must match the approved gate list")
    _ensure_unique("required_gates", required_gates)

    phase_hooks = contract.get("phase_hooks")
    if phase_hooks != REQUIRED_PHASE_HOOKS:
        raise ValueError("phase_hooks must match the approved hook taxonomy")
    _ensure_unique("phase_hooks", phase_hooks)

    decision_hooks = contract.get("decision_hooks")
    if decision_hooks != REQUIRED_DECISION_HOOKS:
        raise ValueError("decision_hooks must match the approved hook taxonomy")
    _ensure_unique("decision_hooks", decision_hooks)

    skill_map = contract.get("skill_map")
    if not isinstance(skill_map, dict):
        raise ValueError("skill_map must be a mapping")

    mapped_skills = {
        skill
        for state_skills in skill_map.values()
        for skill in state_skills
    }
    missing_skills = sorted(REQUIRED_SKILLS - mapped_skills)
    if missing_skills:
        raise ValueError(
            "skill_map is missing required skills: " + ", ".join(missing_skills)
        )

    invariants = contract.get("invariants", {})
    if invariants.get("reference_harness") != "copilot-cli":
        raise ValueError("reference_harness must be 'copilot-cli'")
    if not invariants.get("numbered_phases_forbidden"):
        raise ValueError("numbered_phases_forbidden invariant is required")
    if not invariants.get("specialized_skills_remain_discrete"):
        raise ValueError("specialized_skills_remain_discrete invariant is required")
    if not invariants.get("human_confirmation_required_for_project_overlay"):
        raise ValueError(
            "human_confirmation_required_for_project_overlay invariant is required"
        )
    if not invariants.get("claude_adapter_requires_explicit_downgrade"):
        raise ValueError(
            "claude_adapter_requires_explicit_downgrade invariant is required"
        )


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    contract_path = (
        Path(args[0])
        if args
        else Path("superpowers-local/controller/lifecycle_contract.json")
    )
    try:
        contract = load_contract(contract_path)
        validate_contract(contract)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"validated {contract_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Create the lifecycle contract file**

```json
{
  "version": 1,
  "states": [
    "session-intake",
    "brainstorming",
    "spec-audit",
    "plan-writing",
    "workspace-setup",
    "execution",
    "debugging",
    "review",
    "survivability",
    "retrospective",
    "finish"
  ],
  "required_gates": [
    "approval",
    "review",
    "retrospective",
    "finish",
    "survivability"
  ],
  "phase_hooks": [
    "brainstorming.preflight",
    "spec-audit.preflight",
    "plan-writing.preflight",
    "execution.preflight",
    "review.preflight",
    "finish.preflight"
  ],
  "decision_hooks": [
    "resolve-test-command",
    "resolve-build-command",
    "resolve-sensitive-data-rules",
    "resolve-human-approval-rules",
    "resolve-issue-tracker-rules"
  ],
  "skill_map": {
    "session-intake": ["using-resistance-engine"],
    "brainstorming": ["brainstorming"],
    "plan-writing": ["writing-plans"],
    "workspace-setup": ["using-git-worktrees"],
    "execution": [
      "executing-plans",
      "subagent-driven-development",
      "test-driven-development"
    ],
    "debugging": ["systematic-debugging"],
    "review": ["requesting-code-review", "receiving-code-review"],
    "finish": [
      "verification-before-completion",
      "finishing-a-development-branch"
    ],
    "skill-evolution": ["writing-skills"]
  },
  "invariants": {
    "reference_harness": "copilot-cli",
    "numbered_phases_forbidden": true,
    "specialized_skills_remain_discrete": true,
    "human_confirmation_required_for_project_overlay": true,
    "claude_adapter_requires_explicit_downgrade": true
  }
}
```

- [ ] **Step 3: Run the focused tests and confirm GREEN**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_contracts.py --override-ini="addopts=" -q
```

Expected: PASS with 4 passing tests.

- [ ] **Step 4: Run the validator script directly**

Run:

```bash
python3 scripts/validate_superpowers_contracts.py
```

Expected:

```text
validated superpowers-local/controller/lifecycle_contract.json
```

- [ ] **Step 5: Commit the GREEN state**

Run:

```bash
git add scripts/validate_superpowers_contracts.py superpowers-local/controller/lifecycle_contract.json
git commit -m "feat(superpowers): add lifecycle controller contract" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Expected: one GREEN commit containing the validator, the contract file, and the passing tests.

---

## Task 3: Document the local controller shard and run final regression

**Expected outcome:** the shard has a readable local entrypoint for future workers, and the repo still passes targeted regression plus the existing full suite.

**Files:**
- Create: `superpowers-local/README.md`
- Check: `docs/superpowers/specs/2026-04-14-superpowers-overlay-lifecycle-design.md`
- Check: `vendor/obra-superpowers/`

- [ ] **Step 1: Add the local shard README**

````markdown
# superpowers-local

Local rewrite workspace for the hardened Superpowers lifecycle used by this repository.

## Scope of this shard

- `controller/lifecycle_contract.json` is the machine-readable contract for the
  lifecycle controller
- `scripts/validate_superpowers_contracts.py` validates that contract
- `vendor/obra-superpowers/` remains a read-only upstream reference

## Validation

Run the focused contract tests:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_contracts.py --override-ini="addopts=" -q
```

Run the contract validator directly:

```bash
python3 scripts/validate_superpowers_contracts.py
```

## Guardrails

- named states, not numbered phases
- specialized skills remain discrete
- Copilot CLI is the reference harness
- project-local retention requires explicit human confirmation
- Claude Code compatibility must declare downgrade behavior explicitly
````

- [ ] **Step 2: Run the focused lifecycle-controller regression after adding docs**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_contracts.py --override-ini="addopts=" -q
python3 scripts/validate_superpowers_contracts.py
```

Expected: PASS for pytest and a single `validated ...` line from the script.

- [ ] **Step 3: Run the existing full suite**

Run:

```bash
timeout 180 .venv/bin/pytest --override-ini="addopts=" -q
```

Expected: PASS with the existing repository suite still green.

- [ ] **Step 4: Commit the documentation/final verification state**

Run:

```bash
git add superpowers-local/README.md
git commit -m "docs(superpowers): document local lifecycle controller shard" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Expected: a final shard commit containing only the README documentation for the new
controller workspace.
