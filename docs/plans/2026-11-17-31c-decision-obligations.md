# Decision Obligations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decision records accept `owner`, `obligations`, `compatibility` and `capabilities`, and a decision with an `owner` must have `obligations`.

**Architecture:** This repository has no architecture model. The decision table in `records-shape.mjs` gains four optional fields; `records.mjs` checks the decision `owner` as an element id (passes 3 and 4) and applies the obligations rule in pass 5. `export` needs no change: `owner` is already cleaned as an id and the other three as text.

**Tech Stack:** Node ESM, pytest.

**Spec:** `docs/superpowers/specs/2026-11-17-architecture-model-records-design.md` (A3c amendment: "Decisions, cross-cutting decisions and principles", pass 5, "The obligations rule and wrong types", AC-19 to AC-22) — decisions applied: none.

**Open decisions:** none

**Size:** 2 tasks, 2 entry paths (`export`, `check`), lines reported in the self-review commit (reported, not a target)

**Trust boundary:** unchanged. The new fields are read through the existing record reader and printed through the existing cleaning; no new place interprets them.

### Risk & Confidence Assessment

**Confidence:** 97% — four table rows and three small checks beside existing ones of the same form.

**Complexity Risk:** Low — the fields follow the existing table and pass patterns; line order follows the table, which the spec fixes.

**Environmental Risk:** Low — same worktree and suite (410 passing on `main`).

**Main failure modes:** the new line in the wrong place in field order (AC-20 test); a wrong-typed `owner` still triggering the rule (AC-22 test).

---

## Caller and test sweep

Searched: `skills/`, `tests/` with `grep -rn "DECISION\b\|owner" skills/shared/scripts/architecture-delta tests/scripts/test_architecture_delta_records.py`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `DECISION` table gains four optional fields | `records-shape.mjs` `TABLES.decisions` | table | 1 | see Task 1 |
| same | `tests/scripts/test_architecture_delta_records.py` `test_shape_orders_unknown_keys_after_table_fields` | assert | — | none: its unknown key is `colour` |
| decision `owner` is an element id | `report.mjs` `ID_KEYS` already holds `owner` | cleaning | — | none |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 2 | 1–2 | Task 1 items 1–2, Task 2 items 1–2; focused tests `uv run pytest -q tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_delta_safety.py` |

---

### Task 1: decisions accept the four fields; the owner is an element id

**Tier:** fast — complete edits.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/records-shape.mjs` (`DECISION`)
- Modify: `skills/shared/scripts/architecture-delta/records.mjs` (`idPass`, `linkPass`)
- Test: `tests/scripts/test_architecture_delta_records.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- the four fields accepted and exported as written — mutation: leave `owner` out of `DECISION` — killed by: `test_decisions_carry_obligations`
- the decision `owner` is checked as an element — mutation: skip the decision `owner` in `linkPass` — killed by: `test_decision_owner_problems`

- Satisfies Spec AC: AC-19, AC-21
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
def test_decisions_carry_obligations(tmp_path) -> None:  # AC-19
    cross = decision("D-1", owner="shop.orders", obligations=["Every order has an id."], compatibility="Additive only.",
                     capabilities=["Pay"])
    principle = decision("P-1", binds=[], obligations=["Data stays in the EU."])
    data = export(model_folder(tmp_path, {"decisions/a.json": dfile(cross, principle)})[0])
    assert data["decisions"] == [{**cross, "group": "a"}, {**principle, "group": "a"}]


def test_decision_owner_problems(tmp_path) -> None:  # AC-21
    files = {"decisions/a.json": dfile(decision("D-1", owner="ghost", obligations=["x"]),
                                       decision("D-2", owner="", obligations=["x"]),
                                       decision("D-3", owner="shop", obligations=[]))}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: decisions/a.json: decisions[2].obligations: needs at least one item",
        "error: record-error: decisions/a.json: decisions[1].owner: must not be empty",
        "error: record-error: decisions/a.json: decisions[0].owner: ghost is not a model element",
    ]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_delta_records.py -k "carry_obligations or owner_problems"`. Expected: FAIL (`owner`, `obligations`, `compatibility`, `capabilities` reported as unknown fields).
- [ ] **Step 3: GREEN.** In `records-shape.mjs` `DECISION`, between `field('sources', ...)` and `optional('note', 'text')`, add:

```js
  optional('owner', 'string', { id: 'element' }),
  optional('obligations', 'list', { of: TEXT, minOne: true }),
  optional('compatibility', 'text'),
  optional('capabilities', 'list', { of: TEXT }),
```

In `records.mjs` `idPass`, change `if (name === 'contracts') emptyElement(record.owner, `${at}.owner`);` so it runs for decisions too, and place the decision call after the `superseded_by` form check (table order: `binds`, `superseded_by`, `owner`):

```js
    if (name === 'decisions') emptyElement(record.owner, `${at}.owner`);
```

(added after `if (name === 'decisions') referenceForm(record.superseded_by, ...)`). In `linkPass`, after the decision `superseded_by` block, add:

```js
    if (name === 'decisions') element(record.owner, `${at}.owner`);
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_delta_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/records-shape.mjs skills/shared/scripts/architecture-delta/records.mjs tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#31): decisions carry owner, obligations, compatibility and capabilities"`

### Task 2: a decision with an owner needs obligations

**Tier:** fast — complete edit.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/records.mjs` (`valuePass`)
- Test: `tests/scripts/test_architecture_delta_records.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- the rule's place in field order — mutation: add the line before the `evidence` check — killed by: `test_owner_needs_obligations_after_evidence`
- wrong types — mutation: test `has(record, 'owner')` instead of `isString(record.owner)` — killed by: `test_obligations_rule_and_wrong_types`

- Satisfies Spec AC: AC-20, AC-22
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
def test_owner_needs_obligations_after_evidence(tmp_path) -> None:  # AC-20
    repo, _ = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-1", evidence="memory", owner="shop.orders"))})
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: decisions/a.json: decisions[0].evidence: must be one of checked, code, spec",
        "error: record-error: decisions/a.json: decisions[0].obligations: required when owner is set",
    ]


def test_obligations_rule_and_wrong_types(tmp_path) -> None:  # AC-22
    files = {"decisions/a.json": dfile(decision("D-1", owner=5), decision("D-2", owner="shop", obligations="x"),
                                       decision("D-3", compatibility="Additive only."))}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: decisions/a.json: decisions[0].owner: must be a string",
        "error: record-error: decisions/a.json: decisions[1].obligations: must be a list",
    ]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_delta_records.py -k "after_evidence or wrong_types"`. Expected: `test_owner_needs_obligations_after_evidence` FAILS (no obligations line); `test_obligations_rule_and_wrong_types` passes and pins the wrong-type behaviour.
- [ ] **Step 3: GREEN.** In `records.mjs` `valuePass`, after `fixed(record, 'evidence', DECISION_EVIDENCE, `${at}.evidence`);`, add:

```js
        if (isString(record.owner) && !has(record, 'obligations')) add(`${at}.obligations`, 'required when owner is set');
```

- [ ] **Step 4:** `uv run pytest -q`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/records.mjs tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#31): a decision with an owner needs obligations"`

## Execution note

Task 1 also added `test_decision_compatibility_and_capabilities_are_text` and `test_decision_owner_comes_after_superseded_by_in_pass_3`, from the alignment check's advisories: they pin the decision `compatibility` and `capabilities` types and the pass 3 field order, which no AC test covered.
