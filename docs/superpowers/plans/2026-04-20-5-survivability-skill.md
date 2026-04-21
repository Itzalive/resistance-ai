# Survivability Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone local `survivability` skill, wire it into the execution-to-finish workflow, and register it in the checked-in catalog/provenance artifacts so the skill owns the survivability gate and the obsolete AGENTS template can be removed.

**Architecture:** Create one new skill doc at `skills/survivability/SKILL.md`, then integrate it into `executing-plans` and `subagent-driven-development` so survivability sits between completed implementation and branch finishing, with review remaining workflow-specific rather than mandatory in every path. Keep the review-log contract tool-agnostic by reusing the generic `.review_log.jsonl` schema, register the new local-only skill explicitly in `catalog/catalog_index.json` plus `provenance/provenance_manifest.json`, and delete the temporary inline survivability template from `AGENTS.md` once the standalone skill owns the gate.

**Tech Stack:** Markdown skill docs, JSON metadata artifacts, Python 3.12, `.venv/bin/pytest`, `python3`, `jq`, `git`.

### Risk & Confidence Assessment

**Confidence:** 89% — the approved spec is concrete, the touched surfaces are known, and the repo already has focused response-contract test patterns, but the plan must introduce the first explicit checked-in local-only skill metadata entry.

**Complexity Risk:** Medium — `catalog/catalog_index.json` and `provenance/provenance_manifest.json` have no existing standalone local-only skill entry to copy.

**Environmental Risk:** Medium — two existing baseline tests (`tests/scripts/test_validate_resistance_engine_provenance.py` and `tests/scripts/test_import_superpowers_catalog.py`) already fail for unrelated brainstorming-contract drift, so final verification must rely on exact focused commands rather than those broader files.

**Main failure modes:** survivability still gets skipped in workflow handoff, the new skill leaves “meaningful decision point” or “dependency-touching” undefined, catalog/provenance JSON omit the new entry or compute mismatched digests, or repo docs still imply `AGENTS.md` owns the survivability gate after the standalone skill lands.

**Unknown variables**:
- No checked-in example currently shows how a standalone local-only skill should be represented in `catalog/catalog_index.json` and `provenance/provenance_manifest.json`; this plan assumes a local entry should use `source_repo: "."`, `source_path: "skills/survivability"`, and a `source_revision` generated from `git rev-parse HEAD`.
- The repo’s broad provenance/import pytest files are not currently green, so this plan assumes focused survivability-specific tests are the safe acceptance surface for this shard.

---

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `skills/survivability/SKILL.md` | **Create** | Define the standalone survivability gate, including steady-state preflight, mutation slate, chaos slate, failure routing, and `.review_log.jsonl` usage |
| `skills/executing-plans/SKILL.md` | **Modify** | Insert survivability between completed task execution and `finishing-a-development-branch` |
| `skills/subagent-driven-development/SKILL.md` | **Modify** | Insert survivability between final review and `finishing-a-development-branch` in both prose and graph flow |
| `AGENTS.md` | **Modify** | Remove the temporary inline survivability template once the standalone skill owns the gate |
| `catalog/catalog_index.json` | **Modify** | Register `skill:survivability` as a local catalog entry |
| `provenance/provenance_manifest.json` | **Modify** | Register the new skill file with deterministic digest metadata |
| `tests/scripts/test_survivability_response_contract.py` | **Create** | RED/GREEN contract tests for the new skill text |
| `tests/scripts/test_survivability_workflow_contract.py` | **Create** | RED/GREEN contract tests for `executing-plans` and `subagent-driven-development` handoff order |
| `tests/scripts/test_survivability_catalog_contract.py` | **Create** | RED/GREEN contract tests for catalog/provenance registration |
| `tests/scripts/test_survivability_phase_contract.py` | **Create** | RED/GREEN contract tests proving AGENTS no longer inlines the survivability phase |

---

## Pre-plan verification evidence

Run these commands before executing the plan and refresh any affected output if paths or artifact names change during implementation:

```bash
cd /home/pete/source/resistance-ai
ls skills
ls tests/scripts
ls docs/superpowers/plans
test ! -e skills/survivability
.venv/bin/pytest --version
python3 -m pytest --version
```

Expected observations:

- `skills/survivability` does not exist yet.
- `tests/scripts/` exists for new response-contract test files.
- `.venv/bin/pytest` and `python3 -m pytest` are available.

Broader baseline note:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_brainstorming_response_contract.py -q
.venv/bin/pytest tests/test_repo_layout.py -q
```

Expected: both commands PASS.

Known unrelated baseline drift:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_validate_resistance_engine_provenance.py -q
.venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py -q
```

Expected today: one unrelated failure in each file caused by pre-existing brainstorming-contract assertions, not by the survivability shard. Do **not** expand this shard to fix those unrelated failures.

---

### Task 1: Create the standalone survivability skill contract

**Files:**
- Create: `skills/survivability/SKILL.md`
- Create: `tests/scripts/test_survivability_response_contract.py`

- Satisfies Spec AC: 1, 2, 3, 4, 5, 6, 7, 8

- [ ] **Step 1: Write the RED failing test and at least two failure modes**

```python
from __future__ import annotations

from pathlib import Path


def _section_text(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.index(marker) + len(marker)
    rest = text[start:]
    next_heading = rest.find("\n## ")
    if next_heading == -1:
        return rest
    return rest[:next_heading]


def test_survivability_skill_defines_bounded_mutation_slate() -> None:
    skill_text = Path("skills/survivability/SKILL.md").read_text()

    mutation_lane = _section_text(skill_text, "Mutation Probe Lane")

    assert "3 representative probes" in mutation_lane
    assert "capped at 5 total" in mutation_lane
    assert "meaningful decision point" in mutation_lane
    assert "route the work back to implementation hardening" in mutation_lane


def test_survivability_skill_defines_chaos_thresholds() -> None:
    skill_text = Path("skills/survivability/SKILL.md").read_text()

    chaos_lane = _section_text(skill_text, "Chaos Probe Lane")

    assert "1 chaos probe minimum for local-only changes" in chaos_lane
    assert "2 for dependency-touching changes" in chaos_lane
    assert "capped at 3 total" in chaos_lane
    assert "abort/restore steps" in chaos_lane


def test_survivability_skill_uses_generic_review_log_contract() -> None:
    skill_text = Path("skills/survivability/SKILL.md").read_text()

    review_log = _section_text(skill_text, "Review Log Submission")

    assert ".review_log.jsonl" in review_log
    assert "bounded experiment summary" in review_log
    assert "generic append template" in review_log
    assert "survivability score" in review_log
```

- [ ] **Step 2: Run focused RED verification command**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_response_contract.py -q
```

Expected: FAIL with `FileNotFoundError` or `No such file or directory: 'skills/survivability/SKILL.md'`.

- [ ] **Step 3: Write minimal implementation for GREEN**

```markdown
---
name: survivability
description: Use when implementation is complete and you must prove tests resist realistic faults before finishing the branch
---

# Survivability

## Overview

Survivability is the local gate between “implementation finished” and “safe to finish.”
It proves two things: the tests actually catch faults, and the system degrades safely
under realistic disruption.

## When to Use

- After implementation is complete
- After review if your workflow includes one
- Before `finishing-a-development-branch`
- When the change touched executable logic

## Steady-State Preflight

Before any experiment:

1. name one explicit steady-state verification command
2. name the expected healthy signal for that command
3. name one focused test command for the changed logic

If any item is missing, stop. No experiment runs without a measurable baseline.

## Mutation Probe Lane

Mutation testing measures test effectiveness, not line coverage.

For a small change, run 3 representative probes:

1. boundary/condition mutation
2. failure-path removal or happy-path bias mutation
3. returned-value or state mutation

For broader changes, add 1 probe per additional meaningful decision point, capped at
5 total.

Treat a meaningful decision point as a modified branch condition, guard clause, or
early-return path that can independently change control flow.

Loop for each probe:

1. apply one reversible mutation
2. rerun the same focused test command
3. classify the result as killed or survived
4. restore the original state before the next probe

If any mutant survives, fail the gate and route the work back to implementation
hardening and stronger tests.

## Chaos Probe Lane

For local-only changes, run 1 chaos probe minimum.

For dependency-touching changes, run 2 chaos probes minimum, capped at 3 total.

Treat a dependency-touching change as any change that adds, removes, or modifies a
call boundary to a network service, subprocess, filesystem path outside the working
tree, or other external dependency surface.

Use realistic faults such as:

- 500ms latency
- timeout
- null response
- dependency unavailable

Every chaos probe must include the fault, expected safe degradation behavior, explicit
abort/restore steps, and a rerun of the steady-state command.

If a chaos probe causes unsafe degradation or restore cannot complete, fail the gate
and route the work back to implementation hardening before finish.

## Review Log Submission

Append a bounded experiment summary to `.review_log.jsonl` using the generic append
template from `skills/review-log-jsonl.md`.

Do not copy full stdout/stderr, full diffs, or secret-bearing output into the log.

Record the survivability score as:

- `mutation_killed=<killed>/<total>`
- `chaos_passed=<passed>/<total>`
- overall result: `PASS` or `FAIL`

If any mutant survives, log it as CRITICAL FRICTION for retrospective ingestion.

## Quick Reference

1. establish steady state
2. run the bounded mutation slate
3. run the bounded chaos slate
4. append the bounded experiment summary
5. proceed to finish only on PASS

## Red Flags

- single mutation probe offered as “enough”
- undefined “meaningful decision point”
- undefined “dependency-touching” scope
- chaos experiments with no restore path
- logging raw command output into `.review_log.jsonl`

## Integration

- called after implementation/review
- runs before `finishing-a-development-branch`
- hands the survivability score forward to retrospective work
```

- [ ] **Step 4: Run test to verify it's GREEN**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_response_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Refactor duplicated wording or structure without weakening gates**

```markdown
## Mutation Probe Lane

Mutation testing measures test effectiveness, not line coverage.

For a small change, run 3 representative probes:

1. boundary/condition mutation
2. failure-path removal or happy-path bias mutation
3. returned-value or state mutation

For broader changes, add 1 probe per additional meaningful decision point, capped at
5 total.

Treat a meaningful decision point as a modified branch condition, guard clause, or
early-return path that can independently change control flow.
```

Refactor target: keep the “meaningful decision point” definition in exactly one place
and reuse it from examples or quick-reference text rather than restating it differently.

- [ ] **Step 6: Regenerate artifacts and rerun exact verification commands**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_response_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /home/pete/source/resistance-ai
git add skills/survivability/SKILL.md tests/scripts/test_survivability_response_contract.py
git commit -m "feat(skill-5): add survivability skill contract" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: Insert survivability into the execution handoff path

**Files:**
- Create: `tests/scripts/test_survivability_workflow_contract.py`
- Modify: `skills/executing-plans/SKILL.md:32-37`
- Modify: `skills/subagent-driven-development/SKILL.md:61-64,82-83,267-271`

- Satisfies Spec AC: 1, 4, 7, 8

- [ ] **Step 1: Write the RED failing test and at least two failure modes**

```python
from __future__ import annotations

from pathlib import Path


def test_executing_plans_invokes_survivability_before_finish() -> None:
    skill_text = Path("skills/executing-plans/SKILL.md").read_text()

    assert "Use resistance-engine:survivability" in skill_text
    assert skill_text.index("Use resistance-engine:survivability") < skill_text.index(
        "Use resistance-engine:finishing-a-development-branch"
    )


def test_subagent_driven_development_invokes_survivability_before_finish() -> None:
    skill_text = Path("skills/subagent-driven-development/SKILL.md").read_text()

    assert "Use resistance-engine:survivability" in skill_text
    assert '"Use resistance-engine:survivability"' in skill_text
    assert skill_text.index("Use resistance-engine:survivability") < skill_text.index(
        "Use resistance-engine:finishing-a-development-branch"
    )
    assert (
        '"Dispatch final code reviewer subagent for entire implementation" -> "Use resistance-engine:finishing-a-development-branch";'
        not in skill_text
    )
```

Failure modes covered:

- workflow skills still hand straight to finish
- process graph updated in prose but not in the DOT flow

- [ ] **Step 2: Run focused RED verification command**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_workflow_contract.py -q
```

Expected: FAIL because neither workflow skill mentions `resistance-engine:survivability`.

- [ ] **Step 3: Write minimal implementation for GREEN**

```markdown
# skills/executing-plans/SKILL.md
### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the survivability skill to run the Phase 4 gate."
- **REQUIRED SUB-SKILL:** Use resistance-engine:survivability
- Follow that skill to run the steady-state, mutation, chaos, and review-log checks
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use resistance-engine:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice
```

```markdown
# skills/subagent-driven-development/SKILL.md
"Dispatch final code reviewer subagent for entire implementation" [shape=box];
"Use resistance-engine:survivability" [shape=box style=filled fillcolor=khaki];
"Use resistance-engine:finishing-a-development-branch" [shape=box style=filled fillcolor=lightgreen];

[replace]
"Dispatch final code reviewer subagent for entire implementation" -> "Use resistance-engine:finishing-a-development-branch";
[with]
"Dispatch final code reviewer subagent for entire implementation" -> "Use resistance-engine:survivability";
"Use resistance-engine:survivability" -> "Use resistance-engine:finishing-a-development-branch";

**Required workflow skills:**
- **resistance-engine:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **resistance-engine:writing-plans** - Creates the plan this skill executes
- **resistance-engine:requesting-code-review** - Code review template for reviewer subagents
- **resistance-engine:survivability** - REQUIRED: run the Phase 4 gate before finishing
- **resistance-engine:finishing-a-development-branch** - Complete development after all tasks
```

- [ ] **Step 4: Run test to verify it's GREEN**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_workflow_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Refactor duplicated wording or structure without weakening gates**

```markdown
- Announce: "I'm using the survivability skill to run the Phase 4 gate."
- **REQUIRED SUB-SKILL:** Use resistance-engine:survivability
- Follow that skill to run the steady-state, mutation, chaos, and review-log checks
```

Refactor target: keep this handoff wording consistent between `executing-plans` prose,
`subagent-driven-development` prose, and the DOT graph, and leave no remaining direct
bypass edge from final review to `finishing-a-development-branch`.

- [ ] **Step 6: Regenerate artifacts and rerun exact verification commands**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_workflow_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /home/pete/source/resistance-ai
git add skills/executing-plans/SKILL.md skills/subagent-driven-development/SKILL.md tests/scripts/test_survivability_workflow_contract.py
git commit -m "feat(skill-5): wire survivability into execution flow" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: Register survivability in catalog and provenance artifacts

**Files:**
- Create: `tests/scripts/test_survivability_catalog_contract.py`
- Modify: `catalog/catalog_index.json`
- Modify: `provenance/provenance_manifest.json`

- Satisfies Spec AC: 4, 8

- [ ] **Step 1: Write the RED failing test and at least two failure modes**

```python
from __future__ import annotations

import json
from pathlib import Path


def test_catalog_registers_survivability_skill() -> None:
    catalog = json.loads(Path("catalog/catalog_index.json").read_text())

    entry = next(entry for entry in catalog if entry["entry_type"] == "skill" and entry["name"] == "survivability")

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
```

Failure modes covered:

- skill exists on disk but is absent from checked-in catalog metadata
- provenance entry exists but uses mismatched source/local digests or wrong source repo

- [ ] **Step 2: Run focused RED verification command**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_catalog_contract.py -q
```

Expected: FAIL with `StopIteration` because the `skill:survivability` entry does not exist yet.

- [ ] **Step 3: Write minimal implementation for GREEN**

Run this exact metadata update script after Task 1 creates `skills/survivability/SKILL.md`:

```bash
cd /home/pete/source/resistance-ai
verified_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
source_revision="$(git rev-parse HEAD)"
export verified_at source_revision
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

catalog_path = Path("catalog/catalog_index.json")
manifest_path = Path("provenance/provenance_manifest.json")
skill_path = Path("skills/survivability/SKILL.md")

digest = "sha256:" + hashlib.sha256(skill_path.read_bytes()).hexdigest()
verified_at = os.environ["verified_at"]
source_revision = os.environ["source_revision"]

catalog = json.loads(catalog_path.read_text())
catalog = [
    entry
    for entry in catalog
    if not (entry.get("entry_type") == "skill" and entry.get("name") == "survivability")
]
catalog.append(
    {
        "entry_type": "skill",
        "name": "survivability",
        "source_repo": ".",
        "source_path": "skills/survivability",
        "local_path": "skills/survivability",
        "imported_files": ["SKILL.md"],
        "source_revision": source_revision,
        "imported_at": verified_at,
    }
)
catalog.sort(key=lambda entry: (entry["entry_type"], entry["name"]))
catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")

manifest = json.loads(manifest_path.read_text())
manifest = [entry for entry in manifest if entry.get("entry_id") != "skill:survivability"]
manifest.append(
    {
        "entry_id": "skill:survivability",
        "entry_type": "skill",
        "name": "survivability",
        "source_repo": ".",
        "source_path": "skills/survivability",
        "local_path": "skills/survivability",
        "manifest_state": "imported",
        "source_revision": source_revision,
        "last_imported_at": verified_at,
        "last_verified_at": verified_at,
        "files": [
            {
                "source_repo": ".",
                "source_file": "skills/survivability/SKILL.md",
                "local_file": "skills/survivability/SKILL.md",
                "file_state": "imported",
                "local_sync_policy": "required",
                "source_digest": digest,
                "local_digest": digest,
                "last_verified_at": verified_at,
            }
        ],
    }
)
manifest.sort(key=lambda entry: entry["entry_id"])
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
PY
```

- [ ] **Step 4: Run test to verify it's GREEN**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_catalog_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Refactor duplicated wording or structure without weakening gates**

```json
{
  "entry_type": "skill",
  "name": "survivability",
  "source_repo": ".",
  "source_path": "skills/survivability",
  "local_path": "skills/survivability",
  "imported_files": ["SKILL.md"]
}
```

Refactor target: ensure the catalog entry and manifest entry use the same
`source_repo`, `source_path`, and `local_path` strings so later provenance validation
does not detect metadata drift.

- [ ] **Step 6: Regenerate artifacts and rerun exact verification commands**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_catalog_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /home/pete/source/resistance-ai
git add catalog/catalog_index.json provenance/provenance_manifest.json tests/scripts/test_survivability_catalog_contract.py
git commit -m "feat(skill-5): register survivability metadata" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: Remove the inline AGENTS survivability phase

**Files:**
- Create: `tests/scripts/test_survivability_phase_contract.py`
- Modify: `AGENTS.md:48-70`

- Satisfies Spec AC: 4, 8

- [ ] **Step 1: Write the RED failing test and at least two failure modes**

```python
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"


def test_agents_does_not_inline_survivability_phase_contract() -> None:
    agents_text = AGENTS_PATH.read_text()

    assert "## Lifecycle Phase 4: Resilience & Mutation Testing" not in agents_text
    assert "3 representative probes for a small change" not in agents_text
    assert "2 for dependency-touching changes" not in agents_text


def test_agents_does_not_inline_survivability_score_language() -> None:
    agents_text = AGENTS_PATH.read_text()

    assert 'Record the "Survivability Score" in your Phase 6 Retrospective.' not in agents_text
    assert 'Log any "survived mutations" as CRITICAL FRICTION' not in agents_text
```

Failure modes covered:

- AGENTS still inlines the survivability template after the standalone skill exists
- AGENTS still duplicates the survivability score / CRITICAL FRICTION wording that now belongs to the skill

- [ ] **Step 2: Run focused RED verification command**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_phase_contract.py -q
```

Expected: FAIL because `AGENTS.md` still contains the inline survivability phase.

- [ ] **Step 3: Write minimal implementation for GREEN**

```markdown
[delete the entire inline `## Lifecycle Phase 4: Resilience & Mutation Testing` block]
```

- [ ] **Step 4: Run test to verify it's GREEN**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_phase_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Refactor duplicated wording or structure without weakening gates**

```markdown
[keep the survivability score and CRITICAL FRICTION language in the skill, not in `AGENTS.md`]
```

Refactor target: keep AGENTS limited to evergreen repo instructions instead of letting
skill-owned survivability prose drift back into the file.

- [ ] **Step 6: Regenerate artifacts and rerun exact verification commands**

Run:

```bash
cd /home/pete/source/resistance-ai
.venv/bin/pytest tests/scripts/test_survivability_phase_contract.py -q
.venv/bin/pytest tests/scripts/test_survivability_response_contract.py tests/scripts/test_survivability_workflow_contract.py tests/scripts/test_survivability_catalog_contract.py tests/scripts/test_survivability_phase_contract.py tests/scripts/test_brainstorming_response_contract.py tests/test_repo_layout.py -q
```

Expected: PASS for all focused survivability tests, the baseline-green brainstorming
response-contract file, and repo layout.

- [ ] **Step 7: Commit**

```bash
cd /home/pete/source/resistance-ai
git add AGENTS.md tests/scripts/test_survivability_phase_contract.py
git commit -m "refactor(skill-5): remove AGENTS survivability phase" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Self-Review checklist for this plan

1. Confirm no task asks the implementer to infer digests, timestamps, or JSON field names without the exact command shown above.
2. Confirm every task preserves strict RED → GREEN → REFACTOR order.
3. Confirm no task touches more than two core prose/code files plus its tests, except the JSON artifact task where the two checked-in metadata artifacts are the intended slice.
4. Confirm the plan does **not** depend on the unrelated failing baseline tests in `tests/scripts/test_validate_resistance_engine_provenance.py` or `tests/scripts/test_import_superpowers_catalog.py`.
5. Re-run the pre-plan verification commands if any file paths, test commands, or artifact names change during self-review.
6. Confirm every task includes at least two failure modes in its RED step.
7. Confirm this plan does not require `skills/review-log-jsonl.md` changes unless the generic append template proves insufficient during implementation; if you decide it is insufficient, stop and amend the plan rather than inventing an ad hoc logging shape mid-implementation.

---

## Unified Coherence Check inputs

Before marking this plan approved, provide the opposite-model reviewer:

1. Issue `#5` plus the parent/child issue context (`#4`, `#6`, `#7`).
2. `docs/superpowers/specs/2026-04-20-resistance-engine-survivability-skill-design.md`
3. `docs/superpowers/plans/2026-04-20-5-survivability-skill.md`
4. The pre-plan verification shell output from this session:
   - spec tabula-rasa ingestion
   - `ls skills`
   - `ls tests/scripts`
   - `test ! -e skills/survivability`
   - `.venv/bin/pytest --version`
   - baseline note for the unrelated failing provenance/import files
5. `.review_log.jsonl` showing the spec’s `APPROVED - CROSS-MODEL AUDIT` entry for item `5`.

Use the reviewer outcome vocabulary exactly:

- `[APPROVED - READY FOR EXECUTION]`
- `[REJECTED - PLAN DRIFT]`
- `[REJECTED - SPEC INCOMPLETE]`

If rejected, fix the plan inline, refresh any changed shell evidence, and rerun the
coherence check before execution.

---

## Execution handoff

After this plan passes review, offer:

1. **Subagent-Driven (recommended)** — use `subagent-driven-development`
2. **Inline Execution** — use `executing-plans`

Neither path may skip Tabula Rasa, RED/GREEN/REFACTOR, the survivability gate itself,
or the final approval gate.
