# The Other Skills Read the Record Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `planning-features`, `specifying-features` and `specifying-work-items` read the architecture model as records: the rule map is the elements' `rules` in `export`, cross-cutting decisions are the decisions with `obligations`, and the "unchanged" checks name the `.c4` files, the records and the change files instead of `architecture.md`.

**Architecture:** This repository has no architecture model. Wording only, in three skills; one permanent test keeps the old file name out of the two feature skills.

**Tech Stack:** Markdown skill files; pytest via `uv run`.

**Spec:** `docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md` ("The other skills"; the skills' line in "Scope") — decisions applied: none. Plan 4 of the four plans.

Spec ingested: `ls docs/superpowers/specs/`; `cat docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md`.

**Open decisions:** none

**Size:** 3 tasks, no entry path changed (wording read by three skills; the owner's four-plan split puts them in one plan), lines reported in the self-review commit (reported, not a target)

**Trust boundary:** unchanged. No code changes.

### Risk & Confidence Assessment

**Confidence:** 95% — exact line edits, each found by the sweep below.

**Complexity Risk:** Low — driving variable: a wording edit that changes a rule instead of only its source (each edit keeps the rule and names its new place).

**Environmental Risk:** Low — docs only.

**Main failure modes:** an old-layout name left in a feature skill (pinned by `test_other_skills_read_the_record_layout`); "cross-cutting" in the sense of an AC or a change touched by mistake (the sweep lists the uses that stay).

---

## Caller and test sweep

Searched: `skills/` with `grep -rn "architecture\.md\|decision log\|rule map\|cross-cutting\|Cross-cutting\|two or more capabilities" skills --include=*.md`, outside `skills/defining-architecture/`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `planning-features/FEATURES_REVIEW_MANIFEST.md` Inputs and "Unchanged" name `architecture.md` | the review that loads it | caller | 1 | below |
| `planning-features/FEATURES_STANDARDS.md` Signals read "the model's rule map" | the run's step 3 | caller | 1 | below |
| `planning-features/SKILL.md` rule 1 names cross-cutting decisions without saying what they are | the run | caller | 1 | below |
| the same file | `tests/scripts/test_feature_skills_contract.py::test_skill_md_fits_the_word_cap[planning-features]` (at most 1000 words) | assert | 1 | none: the new rule 1 keeps the word count |
| `specifying-features/FEATURE_REVIEW_MANIFEST.md` Inputs name `architecture.md` | the review | caller | 2 | below |
| `specifying-features/FEATURE_RUBRIC.md` "The decision log only grew." | the review | assert | 2 | the line removed |
| `specifying-features/FEATURE_STANDARDS.md` "The feature's elements" reads the rule map and cross-cutting decisions | the run | caller | 2 | below |
| `specifying-work-items/SKILL.md` "For a shard": the cross-cutting decisions that bind the elements | the run | caller | 3 | below |
| Not changed: "marked cross-cutting" for an epic AC (`planning-features` SKILL, STANDARDS, MANIFEST, RUBRIC), "the first feature to build on each cross-cutting decision" (`FEATURES_RUBRIC.md`, `FEATURES_STANDARDS.md`), cross-cutting changes in `subagent-driven-development` and `writing-plans`, and both `field-evidence.md` files | — | — | — | none |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| none | — | 1–3 | no strong-tier task (owner's rule); survivability and the plan-end code review check every item |

---

### Task 1: `planning-features` reads the records

**Tier:** fast — exact line edits.

**Files:**
- Modify: `skills/planning-features/FEATURES_REVIEW_MANIFEST.md`, `skills/planning-features/FEATURES_STANDARDS.md`, `skills/planning-features/SKILL.md` (one atomic wording change: the three files name the same model inputs)
- Test: `tests/scripts/test_defining_architecture_contract.py` (append)

**Callers that move with this task:** sweep rows 1 to 3.

**Reviewer looks at:**
- no old-layout name is left — mutation: put `architecture.md` back in the manifest's Inputs — killed by: `test_other_skills_read_the_record_layout[planning-features]`

- Satisfies Spec AC: none ("The other skills")
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** In `tests/scripts/test_defining_architecture_contract.py`, replace

```python
import subprocess

```

with

```python
import subprocess

import pytest

```

and append:

```python
OLD_LAYOUT = re.compile(r"architecture\.md|decision log only grew|model's rule map")


@pytest.mark.parametrize("skill", ["planning-features", "specifying-features"])
def test_other_skills_read_the_record_layout(skill: str) -> None:
    folder = ENGINE / "skills" / skill
    hits = [f"{path.name}:{number}" for path in sorted(folder.glob("*.md")) if path.name != "field-evidence.md"
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if OLD_LAYOUT.search(line)]
    assert hits == []
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py -k record_layout`
Expected: 2 failed (`planning-features`: `FEATURES_REVIEW_MANIFEST.md:9`, `:22`, `FEATURES_STANDARDS.md:65`; `specifying-features`: `FEATURE_REVIEW_MANIFEST.md:10`, `FEATURE_RUBRIC.md:23`, `FEATURE_STANDARDS.md:30`).

- [ ] **Step 3: GREEN.** In `skills/planning-features/FEATURES_REVIEW_MANIFEST.md`, replace

```markdown
- The model folder's `architecture.md` (rule map, cross-cutting decisions) and `known-gap.json`.
```

with

```markdown
- The model's `export` (the elements' `rules` as the rule map, the decisions with `obligations` as the cross-cutting decisions, the change files) and `known-gap.json`. The generated pack (`<model>/generated/pack/`) holds the same facts by area.
```

and replace

```markdown
No other key of a gap entry, no `.c4` file, no part of `architecture.md`, no epic text and no code changed.
```

with

```markdown
No other key of a gap entry, no `.c4` file, no record (`decisions/`, `contracts/`, `coverage.json`), no change file, no epic text and no code changed.
```

In `skills/planning-features/FEATURES_STANDARDS.md`, replace

```markdown
Counted per capability at step 3, from the model's rule map, the dependency file and a reading of the code:
```

with

```markdown
Counted per capability at step 3, from the elements' `rules` in `export` (the rule map), the dependency file and a reading of the code:
```

In `skills/planning-features/SKILL.md`, replace the whole line

```markdown
1. **Decisions first.** Cross-cutting decisions are already taken whole by `defining-architecture`. The first feature that builds on one lays its foundation, so later features add to it and do not reshape it.
```

with

```markdown
1. **Decisions first.** Cross-cutting decisions (decisions with `obligations`) are taken whole by `defining-architecture`. The first feature that builds on one lays its foundation; later features add to it, never reshape it.
```

(the word cap of `tests/scripts/test_feature_skills_contract.py` holds `SKILL.md` to 1000 words; this line keeps the count unchanged, and step 1 names the cross-cutting decisions as rule 1 defines them).

- [ ] **Step 4: run.**

Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py -k record_layout`
Expected: 1 passed (`planning-features`), 1 failed (`specifying-features`, Task 2's).

- [ ] **Step 5: commit.**

```bash
git add skills/planning-features tests/scripts/test_defining_architecture_contract.py
git commit -m "docs(#31): planning-features reads the rule map and the cross-cutting decisions from the records"
```

---

### Task 2: `specifying-features` reads the records

**Tier:** fast — exact line edits.

**Files:**
- Modify: `skills/specifying-features/FEATURE_REVIEW_MANIFEST.md`, `skills/specifying-features/FEATURE_RUBRIC.md`, `skills/specifying-features/FEATURE_STANDARDS.md` (one atomic wording change)

**Callers that move with this task:** sweep rows 4 to 6.

**Reviewer looks at:**
- the decision-log item is gone — mutation: restore `- [ ] The decision log only grew. [whole]` — killed by: `test_other_skills_read_the_record_layout[specifying-features]`

- Satisfies Spec AC: none ("The other skills")
- **Test retention:** **Permanent** (Task 1's test)

- [ ] **Step 1: GREEN.** In `skills/specifying-features/FEATURE_REVIEW_MANIFEST.md`, replace

```markdown
- The model folder's `architecture.md` (rule map, cross-cutting decisions) and `known-gap.json`.
```

with

```markdown
- The model's `export` (the elements' `rules` as the rule map, the decisions with `obligations` as the cross-cutting decisions, the change files) and `known-gap.json`. The generated pack (`<model>/generated/pack/`) holds the same facts by area.
```

In `skills/specifying-features/FEATURE_RUBRIC.md`, delete the line

```markdown
- [ ] The decision log only grew. [whole]
```

In `skills/specifying-features/FEATURE_STANDARDS.md`, replace

```markdown
- the elements that own, in the model's rule map, the rules behind the feature's epic ACs;
- the elements bound by the cross-cutting decisions the feature builds on;
```

with

```markdown
- the elements whose `rules` (in `export`) hold the rules behind the feature's epic ACs;
- the elements bound by the cross-cutting decisions (the decisions with `obligations`) the feature builds on;
```

- [ ] **Step 2: run.**

Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py`
Expected: all passed.

- [ ] **Step 3: commit.**

```bash
git add skills/specifying-features
git commit -m "docs(#31): specifying-features reads the records; the decision-log item is gone"
```

---

### Task 3: `specifying-work-items` names the decisions that bind a shard

**Tier:** fast — one line edit.

**Files:**
- Modify: `skills/specifying-work-items/SKILL.md`

**Callers that move with this task:** sweep row 7.

**Reviewer looks at:** none (wording; pinned by the grep below and the code review).

- Satisfies Spec AC: none ("The other skills")
- **Test retention:** n/a

- [ ] **Step 1: edit.** In `skills/specifying-work-items/SKILL.md`, replace

```markdown
  relationships, and the cross-cutting decisions that bind them.
```

with

```markdown
  relationships, and the cross-cutting decisions that bind them (the decisions with
  `obligations` whose `binds` names them) and the principles (decisions with `obligations`
  and empty `binds`).
```

- [ ] **Step 2: check.**

Run: `grep -n "decisions with" skills/specifying-work-items/SKILL.md`
Expected: the new lines.

Run: `uv run pytest -q` (about 3 minutes)
Expected: all pass.

- [ ] **Step 3: commit.**

```bash
git add skills/specifying-work-items/SKILL.md
git commit -m "docs(#31): specifying-work-items names the cross-cutting decisions and principles that bind a shard"
```

## Task 4: the owner decisions of 2026-11-22

**Tier:** standard. **Files:** `skills/specifying-features/FEATURE_RUBRIC.md`, `skills/planning-features/FEATURES_STANDARDS.md`, `skills/planning-features/FEATURES_REVIEW_MANIFEST.md`, `skills/planning-features/FEATURES_RUBRIC.md`, `skills/specifying-features/close-run.md`, `skills/specifying-work-items/SKILL.md`, `tests/scripts/test_defining_architecture_contract.py`. One atomic change: the three spec amendments of commit 6ed5839 (spec, "The other skills").

**Sweep additions** (case-insensitive `grep -rni "decision log\|known-gap\|change nothing else in the model" skills/planning-features skills/specifying-features skills/specifying-work-items`):

| Changed | Site | Kind | Literal edit |
|---|---|---|---|
| the design's decision-log guard | `specifying-features/FEATURE_RUBRIC.md` Hard rules | rubric | add after "The epic, the model, the code and other features' rows are unchanged. [whole]": `- [ ] The design's decision log only grew: no earlier entry was edited or removed. [whole]` |
| the old-layout pin | `test_defining_architecture_contract.py` `OLD_LAYOUT` | assert | `decision log only grew` becomes `(?<!design's )decision log only grew` |
| `close_by` writer | `planning-features/FEATURES_STANDARDS.md` "`close_by`" | caller | "Change nothing else in the model folder." becomes "Change nothing else in the model folder, then run `node <skills-dir>/shared/scripts/architecture-docs.mjs build --repo . --model <model>` so `generated/` shows the new values." |
| close-run gap removal | `specifying-features/close-run.md` step 2 | caller | same replacement for its "Change nothing else in the model folder." |
| planning review "Unchanged" | `planning-features/FEATURES_REVIEW_MANIFEST.md` | caller | "touches only the map and the `close_by` values." becomes "touches only the map, the `close_by` values and `generated/`, and `architecture-docs check` exits 0." |
| planning rubric | `planning-features/FEATURES_RUBRIC.md` | rubric | "(apart from `close_by`)" becomes "(apart from `close_by` and the rebuilt `generated/`)" |
| shard read-first | `specifying-work-items/SKILL.md` "Shard of a feature" | caller | "whose `binds` names them) and the principles (decisions with `obligations` and empty `binds`)" becomes "whose `binds` or `owner` names them) and the principles (decisions with `obligations`, empty `binds` and no `owner`)" |

The specifying-features design-run "Unchanged" items stay: a design run edits no model file; the close run has no review.

**Reviewer looks at:** the regex lookbehind. Mutation: drop `(?<!design's )` - the test fails on the restored rubric item. Mutation: restore the bare `The decision log only grew.` - the test fails. Killed by `test_other_skills_read_the_record_layout[specifying-features]`.

- [ ] **Step 1: RED.** Add the rubric item only. Run `uv run pytest -q tests/scripts/test_defining_architecture_contract.py -k record_layout`. Expected: the `specifying-features` case fails on `FEATURE_RUBRIC.md`.
- [ ] **Step 2: GREEN.** Apply the regex and the other rows. Rerun: 2 passed.
- [ ] **Step 3: check.** `uv run pytest -q tests/scripts/test_feature_skills_contract.py tests/scripts/test_defining_architecture_contract.py`, then `uv run pytest -q` (about 3 minutes). Expected: all pass.
- [ ] **Step 4: commit** the seven files.

## Task 5: the rebuild decision's other callers (alignment r2)

**Tier:** standard. One atomic change for the spec amendment of commit 874cacb: every writer of `known-gap.json` rebuilds `generated/`, and no ownership line forbids it. No test: wording only (owner's lean-tests rule); the word-cap test pins both feature `SKILL.md` files, and each edit keeps its word count or shrinks it.

Sweep: `grep -rni "known-gap\|close_by\|change nothing else in the model" skills --include=*.md`, outside `defining-architecture/`.

| File | Replace | With |
|---|---|---|
| `finishing-a-development-branch/SKILL.md` | "`<model>/known-gap.json`, change nothing else in the model folder, commit, and re-run  `check`:" | "`<model>/known-gap.json`, change nothing else in the model folder, run  `node <skills-dir>/shared/scripts/architecture-docs.mjs build --repo . --model <model>` so `generated/` matches, commit both, and re-run  `check`:" |
| `planning-features/SKILL.md` | "It never changes the epic, the model (apart from `close_by`), code or any feature design." | "It changes no epic, code, feature design or model file but `close_by` and the rebuilt `generated/`." |
| `specifying-features/SKILL.md` | "and removing any still-stale known-gap entries at close." | "and, at close, removing still-stale known-gap entries and rebuilding `generated/`." |
| `planning-features/replan-run.md` | "update `close_by` on any known-gap entry whose closing feature changed," | "update `close_by` on any known-gap entry whose closing feature changed and rebuild `generated/` (`FEATURES_STANDARDS.md`, "`close_by`")," |
| `specifying-features/close-run.md` | "reports stale. Change nothing else in the model folder, then run `node <skills-dir>/shared/scripts/architecture-docs.mjs build --repo . --model <model>` so `generated/` shows the new values." | "reports stale. Change nothing else in the model folder. If you removed any, run `node <skills-dir>/shared/scripts/architecture-docs.mjs build --repo . --model <model>` so `generated/` shows the new values, then `node <skills-dir>/shared/scripts/architecture-docs.mjs check --repo . --model <model>` and quote its output: it must exit 0." |

- [ ] **Step 1: edit** the five rows.
- [ ] **Step 2: check.** `uv run pytest -q tests/scripts/test_feature_skills_contract.py tests/scripts/test_defining_architecture_contract.py`, then `uv run pytest -q`. Expected: all pass.
- [ ] **Step 3: commit** the five files.

## Plan end

After Task 5: the code review of the whole branch on fresh-context Opus, survivability, the run record, then the merge when the owner says merge.
