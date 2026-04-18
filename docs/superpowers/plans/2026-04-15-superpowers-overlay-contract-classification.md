# Superpowers Overlay Contract and Classification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next local Superpowers shard as a machine-readable overlay contract plus classification worksheet validator so later adapter and migration shards can consume explicit project-overlay semantics instead of prose-only guidance.

**Architecture:** Add a new `superpowers-local/overlay/` contract surface parallel to the existing lifecycle controller contract. Store the approved overlay block names, hook taxonomies, classification fields, and human-confirmation invariants in JSON, validate them with a focused Python script under `scripts/`, and back the contract with pytest coverage under `tests/scripts/`. Document the local overlay pack in `docs/superpowers/project/` and update `superpowers-local/README.md` so later shards have a canonical entrypoint.

**Tech Stack:** Python 3.12, JSON, pathlib, `typing.Any`, pytest, `.venv/bin/pytest`, `python3`.

**Spec:** `docs/superpowers/specs/2026-04-14-superpowers-overlay-lifecycle-design.md`
**Primary worktree:** create a fresh task worktree before editing, e.g. `.worktrees/superpowers-overlay-contract`
**Run focused tests:** `timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_overlay.py --override-ini="addopts=" -q`
**Run full suite:** `timeout 180 .venv/bin/pytest --override-ini="addopts=" -q`

---

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `superpowers-local/overlay/overlay_contract.json` | **Create** | Machine-readable contract for overlay pack location, standard project blocks, hook taxonomy, classification fields, and invariants |
| `superpowers-local/overlay/classification_worksheet_template.json` | **Create** | Valid machine-readable starter worksheet proving the required classification entry shape and human-confirmation field |
| `scripts/validate_superpowers_overlay.py` | **Create** | CLI validator for the overlay contract and classification worksheet template |
| `tests/scripts/test_validate_superpowers_overlay.py` | **Create** | RED/GREEN coverage for happy-path validation and negative-path contract / worksheet failures |
| `superpowers-local/README.md` | **Modify** | Extend local shard index to include overlay artifacts and validation commands |
| `docs/superpowers/project/README.md` | **Create** | Describe the project overlay pack, companion-doc layout, and human-confirmed retention rule |

---

## Task 1: Add RED coverage for the overlay contract validator

**Expected RED failure mode:** the validator script does not exist, the overlay contract JSON does not exist, and there is no executable check for the overlay block taxonomy or the human-confirmed classification workflow.

**Files:**
- Create: `tests/scripts/test_validate_superpowers_overlay.py`
- Create later in GREEN: `scripts/validate_superpowers_overlay.py`
- Create later in GREEN: `superpowers-local/overlay/overlay_contract.json`
- Create later in GREEN: `superpowers-local/overlay/classification_worksheet_template.json`

- [ ] **Step 1: Write the failing validator tests**

```python
"""Tests for scripts/validate_superpowers_overlay.py."""
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
    / "overlay"
    / "overlay_contract.json"
)
_WORKSHEET_PATH = (
    Path(__file__).parents[2]
    / "superpowers-local"
    / "overlay"
    / "classification_worksheet_template.json"
)


def _valid_overlay_contract() -> dict:
    return {
        "version": 1,
        "overlay_pack": {
            "root_file": "AGENTS.md",
            "companion_root": "docs/superpowers/project",
        },
        "project_blocks": [
            "project-overview",
            "commands-and-testing",
            "architecture",
            "security-guardrails",
            "codebase-conventions",
            "issue-tracking",
            "environment-limitations",
            "branch-finish-rules",
            "retrospective-rules",
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
        "classification": {
            "allowed_classes": [
                "core-generic",
                "platform-adapter",
                "project-overlay",
            ],
            "required_fields": [
                "source_doc",
                "source_section",
                "proposed_class",
                "generic_rationale",
                "project_specific_rationale",
                "human_decision",
                "destination",
            ],
            "human_decision_values": [
                "pending-human-confirmation",
                "move-to-core",
                "move-to-platform-adapter",
                "keep-project-overlay",
                "split-before-decision",
            ],
        },
        "invariants": {
            "human_confirmation_required_for_project_overlay": True,
            "no_silent_retention_in_agents": True,
            "classification_history_must_be_visible": True,
        },
    }


def _valid_classification_worksheet() -> dict:
    return {
        "version": 1,
        "entries": [
            {
                "source_doc": "AGENTS.md",
                "source_section": "Commands & Testing",
                "proposed_class": "project-overlay",
                "generic_rationale": "Command guidance can be reusable, but only when a repository shares the same tools and verification flow.",
                "project_specific_rationale": "The exact pytest commands, timeouts, and WSL notes are specific to this repository.",
                "human_decision": "pending-human-confirmation",
                "destination": "docs/superpowers/project/commands-and-testing.md",
            }
        ],
    }


def test_repo_overlay_artifacts_validate():
    from validate_superpowers_overlay import (
        load_json,
        validate_classification_worksheet,
        validate_overlay_contract,
    )

    contract = load_json(_CONTRACT_PATH)
    worksheet = load_json(_WORKSHEET_PATH)

    validate_overlay_contract(contract)
    validate_classification_worksheet(worksheet)

    assert contract["overlay_pack"]["companion_root"] == "docs/superpowers/project"
    assert contract["project_blocks"][0] == "project-overview"
    assert worksheet["entries"][0]["human_decision"] == "pending-human-confirmation"


def test_validate_overlay_contract_rejects_missing_project_block():
    from validate_superpowers_overlay import validate_overlay_contract

    contract = _valid_overlay_contract()
    contract["project_blocks"].remove("commands-and-testing")

    with pytest.raises(
        ValueError,
        match="project_blocks must match the approved overlay block list",
    ):
        validate_overlay_contract(contract)


def test_validate_overlay_contract_rejects_wrong_companion_root():
    from validate_superpowers_overlay import validate_overlay_contract

    contract = _valid_overlay_contract()
    contract["overlay_pack"]["companion_root"] = "docs/project"

    with pytest.raises(
        ValueError,
        match="overlay_pack\\.companion_root must be 'docs/superpowers/project'",
    ):
        validate_overlay_contract(contract)


def test_validate_classification_worksheet_rejects_missing_human_decision():
    from validate_superpowers_overlay import validate_classification_worksheet

    worksheet = _valid_classification_worksheet()
    del worksheet["entries"][0]["human_decision"]

    with pytest.raises(
        ValueError,
        match="classification entry missing required fields: human_decision",
    ):
        validate_classification_worksheet(worksheet)


def test_validate_classification_worksheet_rejects_unknown_proposed_class():
    from validate_superpowers_overlay import validate_classification_worksheet

    worksheet = _valid_classification_worksheet()
    worksheet["entries"][0]["proposed_class"] = "unknown-class"

    with pytest.raises(
        ValueError,
        match="classification entry proposed_class must be one of core-generic, platform-adapter, project-overlay",
    ):
        validate_classification_worksheet(worksheet)


def test_main_prints_success_for_repo_overlay_files(capsys):
    from validate_superpowers_overlay import main

    exit_code = main([str(_CONTRACT_PATH), str(_WORKSHEET_PATH)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"validated {_CONTRACT_PATH}" in captured.out
    assert f"validated {_WORKSHEET_PATH}" in captured.out
```

- [ ] **Step 2: Run the focused test file and confirm RED**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_overlay.py --override-ini="addopts=" -q
```

Expected: FAIL because `validate_superpowers_overlay.py` is missing and the overlay
contract files do not exist yet.

- [ ] **Step 3: Commit the RED state**

Run:

```bash
git add tests/scripts/test_validate_superpowers_overlay.py
git commit -m "test(superpowers): add overlay contract validator red coverage" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Expected: one RED commit containing only the new failing test file.

---

## Task 2: Implement the overlay contract, worksheet template, and validator

**Expected GREEN target:** the overlay contract and starter worksheet exist, the validator accepts the approved repo artifacts, and the negative-path tests reject missing project blocks or missing human decisions.

**Files:**
- Create: `scripts/validate_superpowers_overlay.py`
- Create: `superpowers-local/overlay/overlay_contract.json`
- Create: `superpowers-local/overlay/classification_worksheet_template.json`
- Check: `tests/scripts/test_validate_superpowers_overlay.py`

- [ ] **Step 1: Create the validator script**

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONTRACT_PATH = Path("superpowers-local/overlay/overlay_contract.json")
DEFAULT_WORKSHEET_PATH = Path(
    "superpowers-local/overlay/classification_worksheet_template.json"
)

REQUIRED_PROJECT_BLOCKS = [
    "project-overview",
    "commands-and-testing",
    "architecture",
    "security-guardrails",
    "codebase-conventions",
    "issue-tracking",
    "environment-limitations",
    "branch-finish-rules",
    "retrospective-rules",
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

ALLOWED_CLASSES = [
    "core-generic",
    "platform-adapter",
    "project-overlay",
]

REQUIRED_CLASSIFICATION_FIELDS = [
    "source_doc",
    "source_section",
    "proposed_class",
    "generic_rationale",
    "project_specific_rationale",
    "human_decision",
    "destination",
]

ALLOWED_HUMAN_DECISIONS = [
    "pending-human-confirmation",
    "move-to-core",
    "move-to-platform-adapter",
    "keep-project-overlay",
    "split-before-decision",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _require_mapping(name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def _require_string_list(name: str, values: object) -> list[str]:
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError(f"{name} must be a list of strings")
    return values


def validate_overlay_contract(contract: object) -> None:
    if not isinstance(contract, dict):
        raise ValueError("overlay contract must be a mapping")
    if contract.get("version") != 1:
        raise ValueError("overlay contract version must be 1")

    overlay_pack = _require_mapping("overlay_pack", contract.get("overlay_pack"))
    if overlay_pack.get("root_file") != "AGENTS.md":
        raise ValueError("overlay_pack.root_file must be 'AGENTS.md'")
    if overlay_pack.get("companion_root") != "docs/superpowers/project":
        raise ValueError(
            "overlay_pack.companion_root must be 'docs/superpowers/project'"
        )

    project_blocks = _require_string_list("project_blocks", contract.get("project_blocks"))
    if project_blocks != REQUIRED_PROJECT_BLOCKS:
        raise ValueError("project_blocks must match the approved overlay block list")

    phase_hooks = _require_string_list("phase_hooks", contract.get("phase_hooks"))
    if phase_hooks != REQUIRED_PHASE_HOOKS:
        raise ValueError("phase_hooks must match the approved overlay hook taxonomy")

    decision_hooks = _require_string_list(
        "decision_hooks", contract.get("decision_hooks")
    )
    if decision_hooks != REQUIRED_DECISION_HOOKS:
        raise ValueError("decision_hooks must match the approved overlay hook taxonomy")

    classification = _require_mapping("classification", contract.get("classification"))
    allowed_classes = _require_string_list(
        "classification.allowed_classes",
        classification.get("allowed_classes"),
    )
    if allowed_classes != ALLOWED_CLASSES:
        raise ValueError(
            "classification.allowed_classes must match the approved class list"
        )

    required_fields = _require_string_list(
        "classification.required_fields",
        classification.get("required_fields"),
    )
    if required_fields != REQUIRED_CLASSIFICATION_FIELDS:
        raise ValueError(
            "classification.required_fields must match the approved worksheet fields"
        )

    human_decision_values = _require_string_list(
        "classification.human_decision_values",
        classification.get("human_decision_values"),
    )
    if human_decision_values != ALLOWED_HUMAN_DECISIONS:
        raise ValueError(
            "classification.human_decision_values must match the approved decision list"
        )

    invariants = _require_mapping("invariants", contract.get("invariants"))
    if not invariants.get("human_confirmation_required_for_project_overlay"):
        raise ValueError(
            "human_confirmation_required_for_project_overlay invariant is required"
        )
    if not invariants.get("no_silent_retention_in_agents"):
        raise ValueError("no_silent_retention_in_agents invariant is required")
    if not invariants.get("classification_history_must_be_visible"):
        raise ValueError("classification_history_must_be_visible invariant is required")


def validate_classification_worksheet(worksheet: object) -> None:
    if not isinstance(worksheet, dict):
        raise ValueError("classification worksheet must be a mapping")
    if worksheet.get("version") != 1:
        raise ValueError("classification worksheet version must be 1")

    entries = worksheet.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("entries must be a non-empty list")

    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("classification entry must be a mapping")
        missing_fields = [
            field for field in REQUIRED_CLASSIFICATION_FIELDS if field not in entry
        ]
        if missing_fields:
            raise ValueError(
                "classification entry missing required fields: "
                + ", ".join(missing_fields)
            )
        for field in REQUIRED_CLASSIFICATION_FIELDS:
            value = entry[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"classification entry field {field!r} must be a non-empty string"
                )
        if entry["proposed_class"] not in ALLOWED_CLASSES:
            raise ValueError(
                "classification entry proposed_class must be one of "
                + ", ".join(ALLOWED_CLASSES)
            )
        if entry["human_decision"] not in ALLOWED_HUMAN_DECISIONS:
            raise ValueError(
                "classification entry human_decision must be one of "
                + ", ".join(ALLOWED_HUMAN_DECISIONS)
            )


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if not args:
        contract_path = DEFAULT_CONTRACT_PATH
        worksheet_path = DEFAULT_WORKSHEET_PATH
    elif len(args) == 2:
        contract_path = Path(args[0])
        worksheet_path = Path(args[1])
    else:
        print("ERROR: expected 0 or 2 paths", file=sys.stderr)
        return 1

    try:
        contract = load_json(contract_path)
        worksheet = load_json(worksheet_path)
        validate_overlay_contract(contract)
        validate_classification_worksheet(worksheet)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"validated {contract_path}")
    print(f"validated {worksheet_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Create the overlay contract file**

```json
{
  "version": 1,
  "overlay_pack": {
    "root_file": "AGENTS.md",
    "companion_root": "docs/superpowers/project"
  },
  "project_blocks": [
    "project-overview",
    "commands-and-testing",
    "architecture",
    "security-guardrails",
    "codebase-conventions",
    "issue-tracking",
    "environment-limitations",
    "branch-finish-rules",
    "retrospective-rules"
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
  "classification": {
    "allowed_classes": [
      "core-generic",
      "platform-adapter",
      "project-overlay"
    ],
    "required_fields": [
      "source_doc",
      "source_section",
      "proposed_class",
      "generic_rationale",
      "project_specific_rationale",
      "human_decision",
      "destination"
    ],
    "human_decision_values": [
      "pending-human-confirmation",
      "move-to-core",
      "move-to-platform-adapter",
      "keep-project-overlay",
      "split-before-decision"
    ]
  },
  "invariants": {
    "human_confirmation_required_for_project_overlay": true,
    "no_silent_retention_in_agents": true,
    "classification_history_must_be_visible": true
  }
}
```

- [ ] **Step 3: Create the worksheet template file**

```json
{
  "version": 1,
  "entries": [
    {
      "source_doc": "AGENTS.md",
      "source_section": "Commands & Testing",
      "proposed_class": "project-overlay",
      "generic_rationale": "Command guidance can be reusable, but only when a repository shares the same tools and verification flow.",
      "project_specific_rationale": "The exact pytest commands, timeouts, and WSL notes are specific to this repository.",
      "human_decision": "pending-human-confirmation",
      "destination": "docs/superpowers/project/commands-and-testing.md"
    }
  ]
}
```

- [ ] **Step 4: Run the focused tests and direct validator**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_overlay.py --override-ini="addopts=" -q
python3 scripts/validate_superpowers_overlay.py
```

Expected:

```text
......                                                                    [100%]
6 passed
validated superpowers-local/overlay/overlay_contract.json
validated superpowers-local/overlay/classification_worksheet_template.json
```

- [ ] **Step 5: Commit the GREEN state**

Run:

```bash
git add scripts/validate_superpowers_overlay.py superpowers-local/overlay/overlay_contract.json superpowers-local/overlay/classification_worksheet_template.json
git commit -m "feat(superpowers): add overlay contract schema" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Expected: one GREEN commit containing only the validator and the two new overlay
contract files.

---

## Task 3: Document the overlay shard and rerun repository regression

**Expected outcome:** future workers can find the overlay artifacts from both `superpowers-local/README.md` and `docs/superpowers/project/README.md`, and the repository still passes focused and full regression.

**Files:**
- Modify: `superpowers-local/README.md`
- Create: `docs/superpowers/project/README.md`
- Check: `AGENTS.md`

- [ ] **Step 1: Update `superpowers-local/README.md`**

````markdown
# superpowers-local

Local rewrite workspace for the hardened Superpowers lifecycle used by this repository.

## Scope of completed shards

- `controller/lifecycle_contract.json` is the machine-readable contract for the
  lifecycle controller
- `overlay/overlay_contract.json` defines the local overlay pack, hook taxonomy,
  and classification invariants
- `overlay/classification_worksheet_template.json` is the starter machine-readable
  worksheet for human-confirmed rule classification
- `scripts/validate_superpowers_contracts.py` validates the lifecycle controller
  contract
- `scripts/validate_superpowers_overlay.py` validates the overlay contract and
  worksheet
- `vendor/obra-superpowers/` remains a read-only upstream reference

## Validation

Run the focused controller tests:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_contracts.py --override-ini="addopts=" -q
```

Run the focused overlay tests:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_overlay.py --override-ini="addopts=" -q
```

Run the validators directly:

```bash
python3 scripts/validate_superpowers_contracts.py
python3 scripts/validate_superpowers_overlay.py
```

## Guardrails

- named states, not numbered phases
- specialized skills remain discrete
- Copilot CLI is the reference harness
- project-local retention requires explicit human confirmation
- no section stays in `AGENTS.md` by silent default
- Claude Code compatibility must declare downgrade behavior explicitly
````

- [ ] **Step 2: Add `docs/superpowers/project/README.md`**

````markdown
# Project Overlay Pack

This directory holds project-specific companion docs referenced by `AGENTS.md`.

## Contract source

- `superpowers-local/overlay/overlay_contract.json` defines the approved overlay
  block names and hook taxonomy
- `superpowers-local/overlay/classification_worksheet_template.json` defines the
  machine-readable classification worksheet starter

## Human-confirmed retention rule

Project-local content stays in `AGENTS.md` or this directory only after an explicit
human decision is recorded in the classification worksheet.

## Standard companion docs

- `project-overview.md`
- `commands-and-testing.md`
- `architecture.md`
- `security-guardrails.md`
- `codebase-conventions.md`
- `issue-tracking.md`
- `environment-limitations.md`
- `branch-finish-rules.md`
- `retrospective-rules.md`
````

- [ ] **Step 3: Run focused overlay/controller checks and the full suite**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_validate_superpowers_contracts.py tests/scripts/test_validate_superpowers_overlay.py --override-ini="addopts=" -q
python3 scripts/validate_superpowers_contracts.py
python3 scripts/validate_superpowers_overlay.py
timeout 180 .venv/bin/pytest --override-ini="addopts=" -q
```

Expected:

```text
........................                                                [100%]
24 passed
validated superpowers-local/controller/lifecycle_contract.json
validated superpowers-local/overlay/overlay_contract.json
validated superpowers-local/overlay/classification_worksheet_template.json
1641 passed
```

- [ ] **Step 4: Commit the documentation/final verification state**

Run:

```bash
git add superpowers-local/README.md docs/superpowers/project/README.md
git commit -m "docs(superpowers): document overlay contract shard" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Expected: a final shard commit containing only the two documentation files.
