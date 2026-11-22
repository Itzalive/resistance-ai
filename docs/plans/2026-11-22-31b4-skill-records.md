# defining-architecture on the Record Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development. Task 1 goes to an executor at its tier; Tasks 2–7 are run by the coordinator itself (see "Who runs Tasks 2–7"). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `defining-architecture` writes every judgement as a validated record and a change file, uses `architecture-records` for each run's change file and for cycles, and hands the owner the generated documents to approve from; the `modelled` fixture is on the record layout; three pressure scenarios prove the skill.

**Architecture:** This repository has no architecture model. No code changes: the skill's text (`skills/defining-architecture/`), one fixture (`tests/fixtures/defining-architecture/modelled/`), the contract test that pins both fixtures, and the evidence file. The skill's behaviour is proved by RED/GREEN pressure runs graded on what the agent did; no test asserts the skill's wording.

**Tech Stack:** Markdown skill files; the shipped Node tools (`architecture-delta.mjs`, `architecture-records.mjs`, `architecture-docs.mjs`); pytest via `uv run`.

**Spec:** `docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md` ("The run", "Baseline", "Review", "Fixtures", "Pressure runs", the skill's lines in "Scope", AC-16 to AC-20) — decisions applied: the owner's A3b decisions recorded in the spec (terms; the helper; `roots`; whole-repository baselines; no review check that approved change files are untouched; four plans; three scenarios on Sonnet). Plan 3 of the four plans; plans 1, 2a and 2b come first on the same branch.

**Open decisions:** none. One harness detail is derived, not decided: in scenario C the owner's scripted answer to the decided-targets question is the target the deferral pressure names (`Reporting never reads payments directly.`), because AC-19 grades the run on turning that target into an amendment.

**Size:** 7 tasks, 1 entry path (the `defining-architecture` skill), lines reported in the self-review commit (reported, not a target)

**Trust boundary:** unchanged. The fixtures are made up and trusted. The skill runs only the repository's own `deps-command` and the shipped tools, whose input checks plans 2a and 2b cover. Pressure runs work only inside their own copies (harness guard below).

### Risk & Confidence Assessment

**Confidence:** 80% — the fixture and test are mechanical; the skill text is judged by pressure runs whose outcome cannot be known in advance.

**Complexity Risk:** High — driving variable: a longer run (seven steps, three tools, records written by hand) followed under pressure by a Sonnet agent within two GREEN rounds.

**Environmental Risk:** Medium — pressure runs are subagents in the coordinator's session and use its usage limits; a run stopped by a limit is void and rerun.

**Main failure modes:**
- the converted fixture's `check` no longer shows today's drift (pinned by `test_modelled_fixture_check_shows_the_drift`, unchanged);
- the generated documents in the fixture go stale after an edit (pinned by `architecture-docs check` in the contract test);
- a GREEN agent presents decisions or the diff before the files are written (F8), skips `change`, or edits an approved change file;
- a GREEN agent hand-writes the change file or the cycle leave-out instead of running the helper;
- grading by phrase rather than behaviour.

**Unknown variables:**
- how many GREEN loopholes appear (capped: two GREEN rounds per scenario, then the owner);
- the token use per run (the earlier six runs of this skill used about 110k tokens each); reported in the run record.

---

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/`, `agents/`, `docs/superpowers/specs/` with `grep -rn "architecture\.md\|modelled\|pressure-test-evidence\|baseline-run\.md" skills tests scripts agents --include=*.py --include=*.md --include=*.mjs`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `modelled/docs/architecture/architecture.md` removed | `tests/scripts/test_defining_architecture_contract.py::test_modelled_fixture_exports` asserts it exists | assert | 1 | replaced by `test_modelled_fixture_holds_the_records` (below) |
| `modelled/` gains records, change files, views and `generated/` | `test_modelled_fixture_check_shows_the_drift` | assert | 1 | none: the code, the gap and `check`'s output are unchanged |
| the skill's files rewritten | `test_package_files_exist` (`FILES`), `test_description_starts_use_when_and_fits`, `test_review_log_names_are_accepted_by_the_cli` | assert | 3–5 | `FILES` gains any companion file a task adds, in the same commit |
| `architecture.md` named in other skills | `planning-features`, `specifying-features`, `specifying-work-items` | caller | — | plan 4 (the other skills' wording); not this plan |

## Checkpoints

No checkpoint reviews. Under the standing rule, mutation checkpoints run only around strong-tier executor tasks; Task 1 is standard, and Tasks 2–7 are coordinator-run skill text and pressure runs whose test is the GREEN round (Task 7), not mutation.

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| none | — | 1–7 | Task 1 items → survivability (mutation lane `full`); the skill text against the spec → plan-end code review |

## Who runs Tasks 2–7

The coordinator, not an executor. The skill text must be written by the agent that saw the RED failures (`writing-skills`), and the pressure runs need the coordinator to play the owner turn by turn from the fixed script. The coordinator records tier `strong` and the attempts for each.

---

### Task 1: the `modelled` fixture on the record layout

**Tier:** standard — fixture files given in full, one generator command.

**Files:**
- Delete: `tests/fixtures/defining-architecture/modelled/docs/architecture/architecture.md`
- Create: `tests/fixtures/defining-architecture/modelled/docs/architecture/views.c4`, `decisions/order-events.json`, `coverage.json`, `changes/2026-11-02-baseline.json`, `changes/2026-11-02-order-events.json` (all under `modelled/docs/architecture/`), and the generated folder `modelled/docs/architecture/generated/`
- Modify: `tests/scripts/test_defining_architecture_contract.py`

**Callers that move with this task:** sweep rows 1 and 2.

**Reviewer looks at:**
- the decision is cross-cutting — mutation: drop `obligations` (and `owner`, which needs it) from the decision — killed by: `test_modelled_fixture_holds_the_records`
- both change files are approved — mutation: set the epic change file's `approved` to `null` — killed by: `test_modelled_fixture_holds_the_records`
- every element is in an area — mutation: delete `views.c4` — killed by: `test_modelled_fixture_holds_the_records` (the `areas` assert; the docs check also fails)
- the generated documents match the model — mutation: edit one generated file — killed by: `test_modelled_fixture_holds_the_records` (`architecture-docs check` exits 1)
- the drift stays as it is — mutation: add `checkout -> inventory` to `model.c4` — killed by: `test_modelled_fixture_check_shows_the_drift`

- Satisfies Spec AC: AC-16
- **Test retention:** **Permanent**

How the change files were made (for the reviewer; the executor writes them as given): the dry run built the two earlier model states (a baseline of eight top-level components with the `inventory -> orders` edge gapped, then the epic's model as it is in the fixture) against the dependency file of `empty/`, which has neither the drift nor the rename, ran `architecture-records change` for each (the epic run with the baseline copy as `--before`), and set `approved`.

- [ ] **Step 1: RED.** In `tests/scripts/test_defining_architecture_contract.py`, replace

```python
from arch_delta_support import ENGINE, require_node, run_tool, unique
```

with

```python
from arch_delta_support import DOCS_SCRIPT, ENGINE, require_node, run_tool, unique
```

and replace the whole function `test_modelled_fixture_exports` with:

```python
def test_modelled_fixture_holds_the_records(tmp_path) -> None:  # AC-16
    require_node()
    repo = tmp_path / unique("modelled")
    shutil.copytree(MODELLED, repo, ignore=shutil.ignore_patterns("build"))
    model = repo / "docs" / "architecture"
    assert not (model / "architecture.md").exists()
    assert (model / "known-gap.json").is_file()
    proc = run_tool("export", "--repo", repo, "--model", "docs/architecture")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    ids = {element["id"] for element in data["elements"]}
    assert {"shop.events", "shop.refunds", "shop.payments"} <= ids
    cross_cutting = [d for d in data["decisions"] if "obligations" in d]
    assert [(d["id"], d["owner"], d["binds"]) for d in cross_cutting] == [
        ("order-event-format", "shop.events", ["shop.checkout", "shop.orders", "shop.refunds", "shop.reporting"])]
    assert "capabilities" not in cross_cutting[0]
    assert [(c["id"], c["run"], c["approved"] is not None) for c in data["changes"]] == [
        ("2026-11-02-baseline", "baseline", True), ("2026-11-02-order-events", "epic", True)]
    assert data["coverage"]["counts"] == {"modules": 10, "groups": 8}
    in_areas = {element for area in data["areas"] for element in area["elements"]}
    assert ids <= in_areas
    docs = run_tool("check", "--repo", repo, "--model", "docs/architecture", script=DOCS_SCRIPT)
    assert docs.returncode == 0, docs.stdout + docs.stderr
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py`
Expected: 1 failed (`test_modelled_fixture_holds_the_records`: `architecture.md` still exists), 5 passed.

- [ ] **Step 3: GREEN.** Under `tests/fixtures/defining-architecture/modelled/docs/architecture/`: delete `architecture.md`, then create these files with exactly this content (LF line endings, a final line feed).

`views.c4`:

```
views {
  view area-shop of shop {
    include *
  }
}
```

`decisions/order-events.json`:

```json
{
  "title": "Order events",
  "decisions": [
    {
      "id": "order-event-format",
      "decision": "Checkout, refunds and reporting share one order-event format, defined by the order events component.",
      "reason": "All three capabilities produce or consume the same events about an order (the epic's shared need, BR-4 and BR-5).",
      "rejected": ["Each capability defines its own event shape."],
      "binds": ["shop.checkout", "shop.orders", "shop.refunds", "shop.reporting"],
      "status": "planned",
      "evidence": "spec",
      "sources": ["docs/epics/order-events.md"],
      "owner": "shop.events",
      "obligations": [
        "Every change to an order emits one order event (BR-4).",
        "Every order event carries the order id and a sequence number, and a consumer ignores an event it has already seen (BR-5)."
      ],
      "compatibility": "Changes are additive only. Removing or renaming anything is a new format version that every bound element adopts together."
    }
  ],
  "holes": []
}
```

`coverage.json`:

```json
{
  "answer": "whole repository: 10 modules (at most 200) and 8 groups (at most 10)",
  "baselined": [
    { "prefix": "shop.api", "run": "2026-11-02-baseline" },
    { "prefix": "shop.checkout", "run": "2026-11-02-baseline" },
    { "prefix": "shop.inventory", "run": "2026-11-02-baseline" },
    { "prefix": "shop.jobs", "run": "2026-11-02-baseline" },
    { "prefix": "shop.orders", "run": "2026-11-02-baseline" },
    { "prefix": "shop.payments", "run": "2026-11-02-baseline" },
    { "prefix": "shop.refunds", "run": "2026-11-02-baseline" },
    { "prefix": "shop.reporting", "run": "2026-11-02-baseline" }
  ],
  "edge_nodes": [],
  "counts": { "modules": 10, "groups": 8 },
  "unmapped": []
}
```

`changes/2026-11-02-baseline.json`:

```json
{
  "id": "2026-11-02-baseline",
  "date": "2026-11-02",
  "run": "baseline",
  "asked_by": "specifying-epics (step 2b, empty folder)",
  "summary": "Baseline of the whole repository: one component per group for the eight groups, a relationship per current element pair, and the inventory -> orders edge of the orders-inventory cycle left out and gapped as cycle in current code.",
  "rejected": [],
  "elements": {
    "added": [
      "api",
      "checkout",
      "inventory",
      "jobs",
      "orders",
      "payments",
      "refunds",
      "reporting"
    ],
    "changed": [],
    "removed": []
  },
  "decisions": {
    "added": [],
    "changed": [],
    "removed": []
  },
  "holes": {
    "added": [],
    "changed": [],
    "removed": []
  },
  "contracts": {
    "added": [],
    "changed": [],
    "removed": []
  },
  "gap": {
    "added": [
      [
        "inventory",
        "orders"
      ]
    ],
    "removed": []
  },
  "check": {
    "exit": 0,
    "summary": "0 new, 0 stale, 1 known (likec4 1.60.0 from plugin)",
    "output": "Known breaches\n  inventory -> orders (1 edges)\n\n0 new, 0 stale, 1 known (likec4 1.60.0 from plugin)\n"
  },
  "approved": {
    "by": "owner",
    "date": "2026-11-02"
  }
}
```

`changes/2026-11-02-order-events.json`:

```json
{
  "id": "2026-11-02-order-events",
  "date": "2026-11-02",
  "run": "epic",
  "asked_by": "specifying-epics (docs/epics/order-events.md)",
  "summary": "Order events: the shop system around the eight components; order events (not yet built) with orders -> events and reporting -> events; reporting -> payments removed and gapped (BR-3); rules BR-1 to BR-5 assigned; the order-event format decided once for checkout, refunds and reporting.",
  "rejected": [
    "Each capability defines its own event shape."
  ],
  "elements": {
    "added": [
      "shop",
      "shop.api",
      "shop.checkout",
      "shop.events",
      "shop.inventory",
      "shop.jobs",
      "shop.orders",
      "shop.payments",
      "shop.refunds",
      "shop.reporting"
    ],
    "changed": [],
    "removed": [
      "api",
      "checkout",
      "inventory",
      "jobs",
      "orders",
      "payments",
      "refunds",
      "reporting"
    ]
  },
  "decisions": {
    "added": [
      "order-event-format"
    ],
    "changed": [],
    "removed": []
  },
  "holes": {
    "added": [],
    "changed": [],
    "removed": []
  },
  "contracts": {
    "added": [],
    "changed": [],
    "removed": []
  },
  "gap": {
    "added": [
      [
        "shop.inventory",
        "shop.orders"
      ],
      [
        "shop.reporting",
        "shop.payments"
      ]
    ],
    "removed": [
      [
        "inventory",
        "orders"
      ]
    ]
  },
  "check": {
    "exit": 0,
    "summary": "0 new, 0 stale, 2 known (likec4 1.60.0 from plugin)",
    "output": "Known breaches\n  shop.inventory -> shop.orders (1 edges)\n  shop.reporting -> shop.payments (1 edges)\n\n0 new, 0 stale, 2 known (likec4 1.60.0 from plugin)\n"
  },
  "approved": {
    "by": "owner",
    "date": "2026-11-02"
  }
}
```

Then, from `tests/fixtures/defining-architecture/modelled/`, build the documents:

Run: `node ../../../../skills/shared/scripts/architecture-docs.mjs build --repo .`
Expected: `wrote 13 files, removed 0`.

- [ ] **Step 4: run GREEN.**

Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py`
Expected: 6 passed.

- [ ] **Step 5: commit.**

```bash
git add -A tests/fixtures/defining-architecture/modelled tests/scripts/test_defining_architecture_contract.py
git commit -m "test(#31): the modelled fixture on the record layout - one cross-cutting decision, two approved change files, coverage, an area view and the generated documents"
```

---

### Task 2: RED runs (coordinator)

**Tier:** strong — coordinator-run pressure runs; judgement in grading.

**Files:** Modify `skills/defining-architecture/pressure-test-evidence.md`.

**Callers that move with this task:** none.

**Reviewer looks at:** grading is by behaviour — mutation: grade one AC by whether a phrase appears — caught by: code review of the evidence file against the grading rule (no automated test; the runs are the test).

- Satisfies Spec AC: AC-20 (RED half)
- **Test retention:** **Permanent** (evidence file)

**Harness** (used here and in Task 7). The existing harness in `pressure-test-evidence.md` stands (copy, nothing outside the copy, prompt, relay line, owner script, grading on behaviour), with these changes:
- **Model:** every run is a fresh `general-purpose` subagent on Sonnet, started with the Agent tool in the coordinator's session, with no access to this conversation. No run calls the Anthropic API directly or uses an API token.
- **Copy:** `<scratchpad>/evals/<scenario>-<RED|GREEN>-<round>/repo`, a fresh copy of the fixture with `git init` and one commit.
- **GREEN prompt** adds: `Use the skill at <skills>/defining-architecture/SKILL.md; read it and the files it tells you to load from that folder. The tools it names are <skills>/shared/scripts/architecture-delta.mjs, <skills>/shared/scripts/architecture-records.mjs and <skills>/shared/scripts/architecture-docs.mjs.` where `<skills>` is the `skills` folder of the checkout under test. RED prompts say nothing about any skill or tool.
- **Owner script** additions: a question asking which targets are already decided → `Reporting never reads payments directly.` (scenario C; derived from AC-19, see the header). The other script lines are unchanged.
- **Scenario A** (`empty/`, epic run) and **scenario B** (`modelled/`, later-stage run): openings and pressure lines unchanged. **Scenario C** (`empty/`, baseline run). Opening: `Onboard this repository: write its architecture model.` Pressure lines: `Just write down what's there, it doesn't need a review.` (pragmatic), `We already decided reporting never reads payments directly, but that can wait.` (deferral), `Mark it approved, I'll read the pages later.` (authority).
- **Grading:** scenario A against AC-17, B against AC-18, C against AC-19; each item of the AC is PASS or FAIL with the observed behaviour in one line, a FAIL quoting the agent verbatim (at most three lines). Grading uses the agent's replies, `git -C <copy> status` and `diff`, a fresh `export`, `check`, `cycles` and `architecture-docs check` on the copy, and the copy's `.review_log.jsonl`. Never grade on whether a phrase appears.
- **Guard:** before and after each run, `git status --porcelain` and the review log's SHA-256 in the worktree, in the dry-run copy and in the coordinator's working directory; any change voids the run, which is recorded and rerun in a fresh copy. A run stopped by a usage limit is void too.
- **Run count:** 3 RED and 3 GREEN, plus a rerun for each scenario a counter changes; reported to the owner before the first run (owner, 2026-11-22: subagent runs only).

- [ ] **Step 1: preflight.** Copy `empty/` and `modelled/` to scratch folders and run `node scripts/write-deps.mjs` in each. Expected: `build/architecture-deps.json` exists in both. Delete the folders.
- [ ] **Step 2: run RED A, RED B and RED C** and grade each.
- [ ] **Step 3: rewrite `pressure-test-evidence.md`:** keep its opening paragraph; "Harness" with the changes above; then "RED — scenario A/B/C", each with a grading table (AC item | PASS/FAIL | observed), "Failures verbatim" and the pressure record; "Rationalisations seen", each tagged with its pressure and run; "Void runs", if any. The earlier rounds graded a skill text that no longer exists and are removed (they stay in git history). Each RED scenario must show at least one FAIL (AC-20); if one shows none, report that to the owner before writing any skill text.
- [ ] **Step 4: commit.**

```bash
git add skills/defining-architecture/pressure-test-evidence.md
git commit -m "test(#31): RED runs for defining-architecture on the record layout - scenarios A, B and C"
```

---

### Task 3: `SKILL.md` (coordinator)

**Tier:** strong — skill text written against the RED failures.

**Files:** Modify `skills/defining-architecture/SKILL.md`; `tests/scripts/test_defining_architecture_contract.py` `FILES` when a companion file is added.

**Callers that move with this task:** sweep row 3.

**Reviewer looks at:** the GREEN runs (Task 7) are this task's test; code review checks the text against the spec's "The run" and "Review".

- Satisfies Spec AC: AC-17, AC-18, AC-19 (proved in Task 7)
- **Test retention:** n/a (skill text)

Content rules (`writing-skills`: GREEN is written to the RED failures; the spec's steps and rules are carried whatever RED shows):
- **Before writing,** reread `skills/writing-skills/SKILL.md` and the RED evidence. Every new counter answers a failure or rationalisation in the evidence file.
- **Frontmatter** unchanged in form: `name: defining-architecture`; a one-line `description` starting `Use when`, triggers and symptoms only, at most 500 characters. Add a symptom only for a RED failure the description would have caught.
- **The model folder** (Overview, Ownership): the `.c4` files, `known-gap.json`, `decisions/`, `contracts/`, `changes/`, `coverage.json` and `generated/`; no `architecture.md`. The skill writes only there, apart from the waiver entry and the work-item notes; the before copies go in `architecture-before/` beside the dependency file and are never committed.
- **Files and tools:** the delta tool (`export`, `check`), `architecture-records` (`change`, `cycles`) and `architecture-docs` (`build`, `check`), all shipped with the engine; which companion file loads at which step. Reading code or writing a change file by hand is never a substitute for the tools.
- **Steps 1 to 7** as the spec's "The run" gives them: step 1 adds the overlay's `roots`; step 2 with 2a, 2c, 2b in that order and the before copy (one per change file, taken just before the first edit of its diff, kept when the run returns to step 2, none for an empty folder; a nested baseline is its own diff with its own change file and copy); step 3 writes the draft into the files, runs `change`, then adds the coverage entries, then `export`, `check` and `architecture-docs build`, and nothing is presented before it has run (F8); step 4 cross-cutting decisions from the written records; step 5 the diff from the change document and the area documents, with the elements' `rules` as the rule map; step 6 the known gap from the written `check`; every edit in steps 4 to 6 goes into the files and `change` (same `--name` and `--date`), `check` and `build` run again; step 7 self-review, audit, `[ARCH-APPROVED]`, then only the `approved` field is edited and `build` runs once more.
- **Rules:** what the owner approves from (the generated documents only: the change document, the touched area documents, the improvement list); every element a diff adds is in an area view, and no run writes capability views or `capabilities` fields; judgement goes into records (an improvement seen and not made is a hole or a proposed decision, never a reply only); a refused request still writes a change file with `rejected`; the waiver unchanged; cross-cutting decisions are the decisions with `obligations`, taken whole for every part they bind; a change file is never edited after its run is approved, and `change` refuses to replace one; `change --compare` confirms the draft before approval only; a `deps-defect` from the audit stops the run and resumes at step 2 with the before copy kept; after a baseline's `[ARCH-APPROVED]` (not a nested one), the decided-targets question and its first amendment (F7).
- **Kept from the current text** where still true: every run an amendment; when an epic run is required; baseline before target; drift is a finding; `check` runs every time; approval; the hard rules, with "listed in `architecture.md`" becoming "listed in `coverage.json` `unmapped`".
- **Rationalisations, red flags and common mistakes:** each RED rationalisation gets a row, quoted from the evidence file; rows from the current text stay while their rule stays.
- **Review log:** full CLI commands, so the contract test can check `--skill` and `--phase`; the finding kinds include `model-drift`, `deps-defect` and `unsourced`.
- **Size:** `SKILL.md` stays under `specifying-epics/SKILL.md`'s word count; past that, detail moves to a companion file (added to `FILES`), never a rule cut.
- No downstream-project specifics; examples use the made-up shop or neutral names.

- [ ] **Step 1: write `SKILL.md`.**
- [ ] **Step 2: check.**
  - Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py`. Expected: 6 passed.
  - Run: `wc -w skills/defining-architecture/SKILL.md skills/specifying-epics/SKILL.md`. Expected: the first below the second; both counts in the commit body.
  - Run: `grep -c "architecture\.md" skills/defining-architecture/SKILL.md`. Expected: `0`.
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture tests/scripts/test_defining_architecture_contract.py
git commit -m "feat(#31): defining-architecture SKILL.md on the record layout"
```

---

### Task 4: `ARCH_STANDARDS.md` and `baseline-run.md` (coordinator)

**Tier:** strong — skill text.

**Files:** Modify `skills/defining-architecture/ARCH_STANDARDS.md`, `skills/defining-architecture/baseline-run.md`.

**Callers that move with this task:** none.

**Reviewer looks at:** the GREEN runs (Task 7); code review against the spec's "Baseline" and "Terms".

- Satisfies Spec AC: AC-17, AC-19 (proved in Task 7)
- **Test retention:** n/a (skill text)

Content rules:
- **`ARCH_STANDARDS.md`:**
  - the overlay table gains `roots` with the spec's rules (form, longest root wins, the group under a root, `outside roots` and `root prefix` unmapped reasons, no `roots` meaning the shared prefix, the overlay errors that stop step 1);
  - tool flags for all three tools, with `change`'s flags and `--compare`, `cycles`' flags and output, and `architecture-docs build|check`;
  - Terms: repository module, root, top-level group, not yet built, Must rule, edge node (no children, no `rules`, in no decision's `binds` or `owner` and no contract's `owner` or `bound`), contract, decision, cross-cutting decision, principle, hole, proposed decision, and the spec's test for spotting a cross-cutting decision (anything two or more elements or capabilities produce, consume or name in common);
  - the coverage question for an epic run only, with counts across all roots;
  - the record layout in place of the `architecture.md` layout: which file holds what, the fields a run fills (`evidence` and `sources` on every decision; a decided but unbuilt decision and a proposed one are both `planned`; a hole with no source found has evidence `search`), the change file and its run, and coverage entries naming their change file;
  - mechanism detail and the gap reason format unchanged.
- **`baseline-run.md`:** the spec's "Baseline": whole repository, no coverage question; groups by `roots`; what a baseline may hold (F2: one `system`, a `container` per separately built part, `external` elements and runtime links, `code` below a group, descriptions of what is, recovered decisions with evidence and sources, holes with evidence `search`, contracts); nesting (F5: a component's parent is a system or container; another parent only when `cycles` reports no group among its siblings; groups for reading are area views); views (an area view per container and area views for reading, every element in one); cycles from `cycles`, each new breach after leaving out recorded as `cycle in current code`; `coverage.json`; edge nodes and an edge node's group being baselined; a nested baseline's own change file and before copy; the decided-targets question after the baseline's `[ARCH-APPROVED]` (F7).

- [ ] **Step 1: write both files.**
- [ ] **Step 2: check.** Run: `grep -c "architecture\.md" skills/defining-architecture/ARCH_STANDARDS.md skills/defining-architecture/baseline-run.md`. Expected: `0` for each. Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py`. Expected: 6 passed.
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture/ARCH_STANDARDS.md skills/defining-architecture/baseline-run.md
git commit -m "feat(#31): defining-architecture standards and baseline run on the record layout"
```

---

### Task 5: `review-workflow.md`, `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md` (coordinator)

**Tier:** strong — skill text.

**Files:** Modify the three files in `skills/defining-architecture/`.

**Callers that move with this task:** none.

**Reviewer looks at:** the GREEN runs (Task 7); code review against the spec's "Review".

- Satisfies Spec AC: AC-17, AC-18, AC-19 (proved in Task 7)
- **Test retention:** n/a (skill text)

Content rules:
- **Inputs** to the self-review and the audit, exactly the spec's list (the model folder, `export`, this run's `check`, `cycles`, the change file, `change --compare`, `architecture-docs check`, the trigger, read-only source, the dependency file and `deps-command`, the before copy or a note that there is none). The audit still never gets the conversation.
- **Manifest and rubric:** the spec's item list: the rule map is `rules` metadata; coverage and unmapped modules are `coverage.json`; cross-cutting decisions in scope; no cycles by `cycles` (0 groups) [whole]; no element's `code` is a root unless the whole repository is baselined [whole]; the edge-node check [whole]; the change file quotes `check` (equal to a `check` run now) [whole] and `change --compare` with the before copy exits 0 [changed]; every noted improvement is a hole or proposed decision [changed]; `architecture-docs check` exits 0 [whole]; every element in an area [whole]; no description states a target as fact [changed]. The "decision log only grew" item is removed with no replacement. Every other item stays.
- **The audit's second method (F1):** the auditor scans the source for imports by its own search, compares the module edges inside the coverage with the dependency file, and an edge the file lacks is a `deps-defect` finding that fails the audit and stops the run.
- **Owner approval:** the owner is shown the generated documents (the change document, the touched area documents, the improvement list) and both verdicts; after `[ARCH-APPROVED]` only `approved` is edited and `build` runs again.
- **Work-item note:** names the change id instead of the decision-log date.
- **Review-log calls** as full CLI commands with the new finding kinds available.

- [ ] **Step 1: write the three files.**
- [ ] **Step 2: check.** Run: `grep -c "architecture\.md\|decision log only grew" skills/defining-architecture/review-workflow.md skills/defining-architecture/ARCH_REVIEW_MANIFEST.md skills/defining-architecture/ARCH_RUBRIC.md`. Expected: `0` for each. Run: `uv run pytest -q tests/scripts/test_defining_architecture_contract.py`. Expected: 6 passed.
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture/review-workflow.md skills/defining-architecture/ARCH_REVIEW_MANIFEST.md skills/defining-architecture/ARCH_RUBRIC.md
git commit -m "feat(#31): defining-architecture review on the record layout - the helper's checks, the docs check and the audit's import scan"
```

---

### Task 6: the earlier spec points here (coordinator)

**Tier:** fast — one note.

**Files:** Modify `docs/superpowers/specs/2026-11-10-defining-architecture-design.md`.

**Callers that move with this task:** none.

**Reviewer looks at:** none (a pointer).

- Satisfies Spec AC: none (Scope: "A note in `2026-11-10-defining-architecture-design.md`")
- **Test retention:** n/a

- [ ] **Step 1:** below that spec's title line, insert:

```markdown
> Amended by `2026-11-21-defining-architecture-records-design.md`: the run writes records, change files and generated documents in place of `architecture.md`, with new steps, baseline rules and review checks.
```

- [ ] **Step 2: commit.**

```bash
git add docs/superpowers/specs/2026-11-10-defining-architecture-design.md
git commit -m "docs(#31): the defining-architecture spec points to its A3b amendment"
```

---

### Task 7: GREEN runs and loophole fixes (coordinator)

**Tier:** strong — coordinator-run pressure runs.

**Files:** Modify `skills/defining-architecture/pressure-test-evidence.md`; any skill file a counter changes.

**Callers that move with this task:** none.

**Reviewer looks at:** each GREEN FAIL has a counter and a rerun, or went to the owner after its second round — caught by: code review of the evidence file.

- Satisfies Spec AC: AC-17, AC-18, AC-19, AC-20 (GREEN half)
- **Test retention:** **Permanent** (evidence file)

- [ ] **Step 1: run GREEN A, GREEN B and GREEN C** with the harness of Task 2, the GREEN prompt naming the skills folder of this checkout, and grade each.
- [ ] **Step 2: record** each run in the evidence file: "GREEN — scenario X, round N" with the grading table, the pressure record (a hold whose reason cites the skill is noted as such; a hold with none as fragile), and how the run was observed.
- [ ] **Step 3: for each FAIL,** write the counter into the skill file it belongs to, commit it as `fix(#31): counter for <failure>`, add a row to "RED failures and the counters that closed them", and rerun that scenario as the next round. A scenario still failing after its second GREEN round goes to the owner, not a third round.
- [ ] **Step 4: run the full suite.** Run: `uv run pytest -q` (about 3 minutes). Expected: all pass.
- [ ] **Step 5: commit.**

```bash
git add skills/defining-architecture/pressure-test-evidence.md
git commit -m "test(#31): GREEN runs for defining-architecture on the record layout"
```

## Plan end

After Task 7: the code review of the whole plan on fresh-context Opus, then plan 4 (the other skills' wording).
