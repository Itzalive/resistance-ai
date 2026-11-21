# Review-log Architecture Finding Kinds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The review-log CLI accepts the finding kinds `model-drift`, `deps-defect` and `unsourced`, and its schema doc lists them.

**Architecture:** This repository has no architecture model. One tuple in `skills/shared/scripts/review-log.py` (`KINDS`) gates every finding kind, for `append --finding` and for `run-record` `findings`; the doc table in `skills/shared/review-log-jsonl.md` gains three rows, and a new test pins the table to the tuple, as `test_schema_doc_matches_cli` already does for skills and phases.

**Tech Stack:** Python 3, pytest via `uv run`.

**Spec:** `docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md` ("Review-log kinds (F10)", AC-15) — decisions applied: none. Plan 1 of 4.

**Open decisions:** none

**Size:** 1 task, 2 entry paths (`review-log.py append`, `review-log.py run-record`), lines reported in the self-review commit (reported, not a target)

**Trust boundary:** unchanged. A kind is checked against a fixed tuple before anything is written; three more fixed strings change no parsing.

### Risk & Confidence Assessment

**Confidence:** 98% — three strings in one tuple and three table rows.

**Complexity Risk:** Low — `one_of("finding kind", kind, KINDS)` is the only check, used by both commands (`review-log.py:106`, `:213`).

**Environmental Risk:** Low — the CLI tests run the script as a subprocess in `tmp_path`; nothing outside it is touched.

**Main failure modes:** a kind added to the doc but not the tuple, or the reverse (the new doc test); a typo in a kind (the parametrised append and run-record tests use the spec's exact spellings).

---

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/`, `agents/` with `grep -rn "KINDS\|missed-caller\|finding kind" skills tests scripts agents --include=*.py --include=*.md`, and the alignment reviewer's wider `git grep` for each kind name.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `KINDS` gains three kinds | `review-log.py:106` `parse_finding` | caller | — | none: reads `KINDS` |
| same | `review-log.py:213` run-record `findings` check | caller | — | none: reads `KINDS` |
| same | `tests/scripts/test_review_log_cli.py::test_rejects_finding_with_unknown_kind` (`style`) and `::test_run_record_rejects_unknown_finding_kind_and_writes_nothing` (`nit`) | assert | — | none: neither kind is added |
| same | `skills/shared/review-log-jsonl.md` "**`findings[].kind`:**" table | doc | 1 | three rows, below |
| same | skill texts that list a subset of kinds (`subagent-driven-development`, `writing-plans`, `checkpoint-reviewer-prompt.md`) | doc | — | none: they name the kinds their own reviews use |
| same | `skills/survivability/SKILL.md:123` names `real-bug` | doc | — | none: names one kind its own step logs |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 1 | 1 | Task 1 items 1–3; focused tests `uv run pytest -q tests/scripts/test_review_log_cli.py` |

Task 1 is fast tier. Under the owner's rule, no mutation checkpoint reviewer is sent for C1: the code review and survivability of the whole change check items 1–3. The meaning text of the three doc rows is checked by review only; no test pins it.

---

### Task 1: the three architecture finding kinds

**Tier:** fast — complete edits.

**Files:**
- Modify: `skills/shared/scripts/review-log.py:51` (`KINDS`)
- Modify: `skills/shared/review-log-jsonl.md` ("**`findings[].kind`:**" table)
- Test: `tests/scripts/test_review_log_cli.py` (append)

**Callers that move with this task:** the doc table row in the sweep.

**Reviewer looks at:**
- each new kind accepted by `append` — mutation: drop `deps-defect` from `KINDS` — killed by: `test_architecture_kinds_are_accepted_by_append[deps-defect]`
- each new kind accepted in a run record — mutation: misspell `unsourced` as `unsourced-claim` in `KINDS` — killed by: `test_architecture_kinds_are_accepted_by_run_record[unsourced]`
- the doc lists exactly the CLI's kinds — mutation: delete the `model-drift` doc row — killed by: `test_schema_doc_kinds_match_cli`

- Satisfies Spec AC: AC-15
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append to `tests/scripts/test_review_log_cli.py`:

```python
ARCH_KINDS = ["model-drift", "deps-defect", "unsourced"]


@pytest.mark.parametrize("kind", ARCH_KINDS)
def test_architecture_kinds_are_accepted_by_append(tmp_path: Path, kind: str) -> None:  # AC-15
    result = run(
        tmp_path,
        *append_args(**{"--verdict": "REJECTED"}),
        "--finding",
        f"important:{kind}:the dependency file lacks an import",
    )
    assert result.returncode == 0, result.stderr
    [entry] = read_log(tmp_path)
    assert entry["findings"] == [{"severity": "important", "kind": kind, "text": "the dependency file lacks an import"}]


@pytest.mark.parametrize("kind", ARCH_KINDS)
def test_architecture_kinds_are_accepted_by_run_record(tmp_path: Path, kind: str) -> None:  # AC-15
    record = {**RUN_RECORD, "findings": {"spec-audit": {kind: 2}}}
    result = run(tmp_path, "run-record", "--from", "-", stdin=json.dumps(record))
    assert result.returncode == 0, result.stderr
    [written] = read_log(tmp_path, ".run_records.jsonl")
    assert written["findings"] == {"spec-audit": {kind: 2}}


def test_near_miss_kind_is_refused(tmp_path: Path) -> None:  # AC-15: unknown kinds refused as before
    result = run(tmp_path, *append_args(**{"--verdict": "REJECTED"}), "--finding", "minor:deps:near miss")
    assert result.returncode == 2
    assert "kind" in result.stderr
    assert not (tmp_path / ".review_log.jsonl").exists()


def test_schema_doc_kinds_match_cli() -> None:
    cli = load_cli()
    doc = (CLI.parent.parent / "review-log-jsonl.md").read_text(encoding="utf-8")
    kind_text = doc.split("**`findings[].kind`:**", 1)[1].split("**Gate strings:**", 1)[0]
    assert set(re.findall(r"^\| `([^`]+)` \|", kind_text, re.M)) == set(cli.KINDS)
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_review_log_cli.py -k "architecture_kinds or near_miss_kind or schema_doc_kinds"`
Expected: 6 failed (the three append and three run-record cases, each `returncode == 2` with "finding kind" in stderr), 2 passed (`test_near_miss_kind_is_refused` and `test_schema_doc_kinds_match_cli`, which hold today and pin the change).

- [ ] **Step 3: GREEN.** In `skills/shared/scripts/review-log.py`, replace line 51:

```python
KINDS = ("missed-caller", "weak-test", "plan-hole", "spec-hole", "real-bug", "slip", "wording")
```

with:

```python
KINDS = (
    "missed-caller",
    "weak-test",
    "plan-hole",
    "spec-hole",
    "real-bug",
    "slip",
    "wording",
    "model-drift",
    "deps-defect",
    "unsourced",
)
```

In `skills/shared/review-log-jsonl.md`, after the row ``| `wording` | Clarity or consistency only; no behaviour change |`` add:

```markdown
| `model-drift` | The model states something the code does not do, or a description states a target as fact |
| `deps-defect` | The dependency file is wrong or incomplete |
| `unsourced` | A recorded reason or evidence claim has no source, or its source does not say it |
```

- [ ] **Step 4: run GREEN and the whole CLI file.**

Run: `uv run pytest -q tests/scripts/test_review_log_cli.py`
Expected: 49 passed (41 existing plus the 8 new).

- [ ] **Step 5: refactor.** None expected; confirm `git diff --stat` shows only the three files.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/review-log.py skills/shared/review-log-jsonl.md tests/scripts/test_review_log_cli.py
git commit -m "feat(#31): review-log finding kinds model-drift, deps-defect and unsourced"
```
