# Review log: new skills, phases and run-record feature field — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (inline fast path: two tasks, no trust-boundary change).

**Goal:** The review-log CLI and its schema doc accept the architecture and feature skills, their three self-review phases, and an optional `feature` field on run records.

**Architecture:** Extend the `SKILLS` and `SELF_PHASES` tuples in `skills/shared/scripts/review-log.py`; let `validate_run_record` accept and check an optional `feature` key; update `skills/shared/review-log-jsonl.md` to match; a drift test keeps doc and CLI aligned.

**Tech Stack:** Python 3.12 standard library, pytest via `uv run pytest`.

**Spec:** `docs/superpowers/specs/2026-11-10-review-log-new-skills-design.md` — decisions applied: owner decisions 2026-11-10 (self-review phases, `FEATURES_PLAN_REVIEW` name, `feature` optional non-empty string, finding layers unchanged)

**Open decisions:** none

**Size:** 2 tasks, 2 entry paths (`append`, `run-record`), lines reported by `wc -l` at commit (not a target)

**Trust boundary:** unchanged — the CLI's inputs are the caller's own flags and record file, already validated by allow-lists and `json.dumps`

### Risk & Confidence Assessment

**Confidence:** 97% — two tuples and one optional-field check in a 264-line standard-library script with an existing test file.

**Complexity Risk:** Low — single-file logic with no branching beyond one optional key.

**Environmental Risk:** Low — runs under the existing `uv run pytest`; no network or new dependency.

**Main failure modes:** `feature` added to `RUN_RECORD_FIELDS`, making it required; doc table edited without the CLI or the reverse.

---

## Caller and test sweep

Searched `skills/`, `tests/`, `docs/`, root `*.md` with `grep -rn "SELF_PHASES\|RUN_RECORD_FIELDS\|SKILLS =\|validate_run_record" --include=*.py --include=*.md .`

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `SKILLS`, `SELF_PHASES` gain values | `build_entry` (`one_of`, self check) | caller | 1 | none: reads the tuples |
| `validate_run_record` accepts optional `feature` | `main` | caller | 2 | none |
| same | `tests/scripts/test_run_record_contract.py` | test | 2 | none: records without `feature` stay valid |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 2 | 1–2 | Task 1 items 1–3, Task 2 items 1–4; focused tests (`tests/scripts/test_review_log_cli.py tests/scripts/test_run_record_contract.py`) |

### Task 1: new skills and self-review phases

**Tier:** fast — two tuple edits and doc rows, complete code below.

**Files:** Modify `skills/shared/scripts/review-log.py` (`SKILLS`, `SELF_PHASES`), `skills/shared/review-log-jsonl.md` (skill list, phase table). Test: `tests/scripts/test_review_log_cli.py`.

**Callers that move with this task:** none

**Reviewer looks at:**
- each new skill accepted — mutation: drop `planning-features` from `SKILLS` — killed by: `test_new_skills_are_accepted[planning-features]`
- new phases are self-only — mutation: put `FEATURE_REVIEW` in `REVIEWER_PHASES` instead — killed by: `test_new_phases_accept_self[FEATURE_REVIEW]` and `test_new_phases_reject_other_independence[FEATURE_REVIEW]`
- exact names — mutation: add `FEATURES_REVIEW` as an alias — killed by: `test_near_miss_phase_is_rejected`

- Satisfies Spec AC: AC-1, AC-2, AC-3, AC-4
- **Test retention:** Permanent

- [ ] **Step 1: RED tests**

```python
NEW_SKILLS = ["defining-architecture", "planning-features", "specifying-features"]
NEW_PHASES = ["ARCH_REVIEW", "FEATURES_PLAN_REVIEW", "FEATURE_REVIEW"]


@pytest.mark.parametrize("skill", NEW_SKILLS)
def test_new_skills_are_accepted(tmp_path: Path, skill: str) -> None:
    result = run(tmp_path, *append_args(**{"--skill": skill, "--phase": "SPEC_REVIEW", "--independence": "self"}))
    assert result.returncode == 0, result.stderr
    assert read_log(tmp_path)[0]["skill"] == skill


@pytest.mark.parametrize("phase", NEW_PHASES)
def test_new_phases_accept_self(tmp_path: Path, phase: str) -> None:
    result = run(tmp_path, *append_args(**{"--phase": phase, "--independence": "self"}))
    assert result.returncode == 0, result.stderr
    assert read_log(tmp_path)[0]["phase"] == phase


@pytest.mark.parametrize("phase", NEW_PHASES)
def test_new_phases_reject_other_independence(tmp_path: Path, phase: str) -> None:
    result = run(tmp_path, *append_args(**{"--phase": phase, "--independence": "fresh-context"}))
    assert result.returncode == 2
    assert f"independence must be 'self' for {phase}" in result.stderr
    assert not (tmp_path / ".review_log.jsonl").exists()


def test_near_miss_phase_is_rejected(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--phase": "FEATURES_REVIEW", "--independence": "self"}))
    assert result.returncode == 2
    assert "phase" in result.stderr
    assert not (tmp_path / ".review_log.jsonl").exists()
```

- [ ] **Step 2: run RED** `uv run pytest tests/scripts/test_review_log_cli.py -q` — Expected: the three new-skill and three new-phase accept tests fail; the reject tests pass already.
- [ ] **Step 3: GREEN** — append the three skills to `SKILLS`; `SELF_PHASES = ("EPIC_REVIEW", "SPEC_REVIEW", "PLAN_SELF_REVIEW", "ARCH_REVIEW", "FEATURES_PLAN_REVIEW", "FEATURE_REVIEW")`. Doc: add the three skills to the `skill` list, the three phase rows (`self`), and widen the `INDEPENDENT_AUDIT` row to "Epic, architecture, feature plan, feature or spec independent audit".
- [ ] **Step 4: run** `uv run pytest tests/scripts/test_review_log_cli.py tests/scripts/test_run_record_contract.py -q` — Expected: PASS
- [ ] **Step 5: commit** `feat(21): review-log accepts architecture and feature skills and their self-review phases`

### Task 2: optional run-record `feature` field and doc drift test

**Tier:** fast — one optional-key check and one doc row, complete code below.

**Files:** Modify `skills/shared/scripts/review-log.py` (`validate_run_record`), `skills/shared/review-log-jsonl.md` (run-record table and the "All fields" sentence). Test: `tests/scripts/test_review_log_cli.py`.

**Callers that move with this task:** `tests/scripts/test_run_record_contract.py` (run, no edit)

**Reviewer looks at:**
- optional, not required — mutation: add `feature` to `RUN_RECORD_FIELDS` — killed by: `test_run_record_feature_is_optional[absent]`
- allowed past the unknown check — mutation: leave `feature` out of the allowed keys — killed by: `test_run_record_feature_is_optional[present]`
- value checked — mutation: skip the `non_empty` check on `feature` — killed by: `test_run_record_rejects_bad_feature[*]`
- doc matches CLI — mutation: drop the `feature` row from the doc — killed by: `test_schema_doc_matches_cli`

- Satisfies Spec AC: AC-5, AC-6; Scope drift test
- **Test retention:** Permanent

- [ ] **Step 1: RED tests**

```python
@pytest.mark.parametrize("present", [True, False], ids=["present", "absent"])
def test_run_record_feature_is_optional(tmp_path: Path, present: bool) -> None:
    record = {**RUN_RECORD, "feature": "F-7"} if present else dict(RUN_RECORD)
    result = run(tmp_path, "run-record", "--from", "-", stdin=json.dumps(record))
    assert result.returncode == 0, result.stderr
    [written] = read_log(tmp_path, ".run_records.jsonl")
    if present:
        assert written["feature"] == "F-7"
    else:
        assert "feature" not in written


@pytest.mark.parametrize("value", [None, "", "  ", 7], ids=["null", "empty", "blank", "number"])
def test_run_record_rejects_bad_feature(tmp_path: Path, value: object) -> None:
    result = run(tmp_path, "run-record", "--from", "-", stdin=json.dumps({**RUN_RECORD, "feature": value}))
    assert result.returncode == 2
    assert "feature" in result.stderr
    assert not (tmp_path / ".run_records.jsonl").exists()


def load_cli():
    spec = importlib.util.spec_from_file_location("review_log_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_schema_doc_matches_cli() -> None:
    cli = load_cli()
    doc = (CLI.parent.parent / "review-log-jsonl.md").read_text(encoding="utf-8")
    skills_text = doc.split("**`skill`:**", 1)[1].split("\n\n", 1)[0]
    phase_text = doc.split("**`phase`:**", 1)[1].split("**`independence`:**", 1)[0]
    record_text = doc.split("## Run record", 1)[1].split("\n## ", 1)[0]
    row = re.compile(r"^\| `([^`]+)` \|", re.M)
    assert set(re.findall(r"`([^`]+)`", skills_text)) == set(cli.SKILLS)
    assert set(row.findall(phase_text)) == set(cli.PHASES)
    assert set(row.findall(record_text)) == set(cli.RUN_RECORD_FIELDS) | {"feature"}
```

(Add `import importlib.util`, `import re` and `import pytest` at the top of the file if absent.)

- [ ] **Step 2: run RED** `uv run pytest tests/scripts/test_review_log_cli.py -q` — Expected: `present`, the drift test and the four bad-feature cases fail (an unknown field today, so the message names `feature` only for some; the drift test fails on the missing `feature` row).
- [ ] **Step 3: GREEN** — in `validate_run_record`, compute `unknown` against `RUN_RECORD_FIELDS + ("feature",)`, and after the required checks add `if "feature" in record: non_empty("feature", record["feature"])`. Doc: change "All fields are required" to "All fields except `feature` are required" and add `` | `feature` | string, optional | Feature the plan's work item belongs to; omit when the work item is not part of a feature | `` after `item_id`.
- [ ] **Step 4: run** `uv run pytest tests/scripts/test_review_log_cli.py tests/scripts/test_run_record_contract.py -q` — Expected: PASS; then `uv run pytest -q` — Expected: PASS
- [ ] **Step 5: commit** `feat(21): optional feature field on run records; schema doc drift test`


## Changes during execution

- Task 1 Step 2: the wrong-independence tests failed at RED rather than passing, because an unknown phase is rejected before the independence rule; the tests are correct as written.
- Checkpoint C1: `test_run_record_rejects_bad_feature` asserts the exact `feature must be a non-empty string` message, so it separates the value check from the unknown-key check; `test_schema_doc_independence_matches_cli` added; `SELF_PHASES` wrapped one item per line.
- Spec future work: `finishing-a-development-branch` (#25), not the new skills, sets `feature` on run records.
