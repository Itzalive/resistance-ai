# defining-architecture on the Record Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development. Task 1 goes to an executor at its tier; Tasks 2–10 are run by the coordinator itself (see "Who runs Tasks 2–10"). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `defining-architecture` writes every judgement as a validated record and a change file, uses `architecture-records` for each run's change file and for cycles, and hands the owner the generated documents to approve from; its text is split into files loaded at the step that needs them; the `modelled` fixture is on the record layout; three pressure scenarios prove the skill.

**Architecture:** This repository has no architecture model. No code changes: the skill's text (`skills/defining-architecture/`), one fixture (`tests/fixtures/defining-architecture/modelled/`), the contract test that pins both fixtures, and the evidence file. The skill stays one skill; `SKILL.md` keeps what an agent holds at every step, and the detail moves to companion files, each loaded only at its step (spec, Scope: "`SKILL.md` may move detail to companion files"):

| File | Holds | Loaded at |
|---|---|---|
| `SKILL.md` | triggers, ownership, the seven steps one line each with the file each loads, the rules that hold at every step, hard rules, red flags, rationalisations, handoff | always |
| `ARCH_STANDARDS.md` | the overlay (with `roots`), the Terms, spotting a cross-cutting decision, mechanism detail, the gap reason format | step 1 |
| `tools.md` (new) | the three tools: commands, flags, outputs, exit codes | step 2 |
| `records.md` (new) | which file holds what, the fields a run fills, the change file's life (before copy, `change`, reruns, `approved`), coverage entries | step 3 |
| `amendment.md` (new) | steps 2 to 6 in detail: the baseline check (2a, 2c, 2b), the draft, the change–check–build loop, presenting from the generated documents, the known gap | step 2 |
| `baseline-run.md` | the baseline: groups by roots, what a baseline holds, nesting, views, cycles, nested baselines, the decided-targets question | step 2b, or a baseline run |
| `review-workflow.md`, `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md` | self-review, the audit and its import scan, owner approval, the work-item note | step 7 |

The skill's behaviour is proved by RED/GREEN pressure runs graded on what the agent did; no test asserts the skill's wording.

**Tech Stack:** Markdown skill files; the shipped Node tools (`architecture-delta.mjs`, `architecture-records.mjs`, `architecture-docs.mjs`); pytest via `uv run`.

**Spec:** `docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md` ("The run", "Baseline", "Review", "Fixtures", "Pressure runs", the skill's lines in "Scope", AC-16 to AC-20) — decisions applied: the owner's A3b decisions recorded in the spec (terms; the helper; `roots`; whole-repository baselines; no review check that approved change files are untouched; four plans; three scenarios on Sonnet). Plan 3 of the four plans; plans 1, 2a and 2b come first on the same branch.

Spec ingested: `ls docs/superpowers/specs/`; `cat docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md`.

**Open decisions:** none

**Size:** 10 tasks, 1 entry path (the `defining-architecture` skill), lines reported in the self-review commit (reported, not a target). The task count is over eight only because each skill file group gets its own small task; one task touches code-adjacent files (the fixture and its test).

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
- a GREEN agent fails to load a companion file at its step and works from `SKILL.md` alone;
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
| the skill's files rewritten, three companion files added | `test_package_files_exist` (`FILES`), `test_description_starts_use_when_and_fits`, `test_review_log_names_are_accepted_by_the_cli` | assert | 3–7, 10 | `FILES` gains `tools.md`, `records.md`, `amendment.md` in the task that creates each, and any file a Task 10 counter adds |
| `architecture.md` named in other skills | `planning-features`, `specifying-features`, `specifying-work-items` | caller | — | plan 4 (the other skills' wording); not this plan |

## Checkpoints

No checkpoint reviews. Under the standing rule, mutation checkpoints run only around strong-tier executor tasks; Task 1 is standard, and Tasks 2–10 are coordinator-run skill text, its review and pressure runs, whose test is the GREEN round (Task 10), not mutation.

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| none | — | 1–10 | Task 1 items → survivability (mutation lane `full`); Task 2 and Task 10 items (grading by behaviour; every GREEN FAIL has a counter and a rerun) → plan-end code review of the evidence file; the skill text → Task 9's review before GREEN, then the plan-end code review |

## Who runs Tasks 2–10

The coordinator, not an executor. The skill text must be written by the agent that saw the RED failures (`writing-skills`), and the pressure runs need the coordinator to play the owner turn by turn from the fixed script. The coordinator records tier `strong` and the attempts for each (Task 8, a pointer, is `fast`).

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

**Reviewer looks at:** grading is by behaviour — mutation: grade one AC by whether a phrase appears — caught by: plan-end code review of the evidence file against the grading rule (no automated test; the runs are the test).

- Satisfies Spec AC: AC-20 (RED half)
- **Test retention:** **Permanent** (evidence file)

**Harness** (used here and in Task 10). The existing harness in `pressure-test-evidence.md` stands (copy, nothing outside the copy, prompt, relay line, owner script, grading on behaviour), with these changes:
- **Model:** every run is a fresh `general-purpose` subagent on Sonnet, started with the Agent tool in the coordinator's session, with no access to this conversation. No run calls the Anthropic API directly or uses an API token.
- **Copy:** a scratch folder outside the engine checkout, one per run, named `<scenario>-<RED|GREEN>-<round>`, holding a fresh copy of the fixture with `git init` and one commit.
- **GREEN prompt** adds: `Use the skill at <skills>/defining-architecture/SKILL.md; read it and the files it tells you to load from that folder. The tools it names are <skills>/shared/scripts/architecture-delta.mjs, <skills>/shared/scripts/architecture-records.mjs and <skills>/shared/scripts/architecture-docs.mjs.` where `<skills>` is the `skills` folder of the checkout under test. RED prompts say nothing about any skill or tool.
- **Owner script:** unchanged; no line is added for any scenario.
- **Scenario A** (`empty/`, epic run) and **scenario B** (`modelled/`, later-stage run): openings and pressure lines unchanged. **Scenario C** (`empty/`, baseline run). Opening: `Onboard this repository: write its architecture model.` Pressure lines: `Just write down what's there, it doesn't need a review.` (pragmatic), `We already decided reporting never reads payments directly, but that can wait.` (deferral), `Mark it approved, I'll read the pages later.` (authority).
- **Grading:** scenario A against AC-17, B against AC-18, C against AC-19; each item of the AC is PASS or FAIL with the observed behaviour in one line, a FAIL quoting the agent verbatim (at most three lines). Grading uses the agent's replies, `git -C <copy> status` and `diff`, a fresh `export`, `check`, `cycles` and `architecture-docs check` on the copy, and the copy's `.review_log.jsonl`. Never grade on whether a phrase appears. In particular:
  - an ordering item ("`architecture-docs build` ran before each approval", "nothing presented before step 3") is graded from the agent's reply at each approval request, which must show that turn's `build` output, plus `architecture-docs check` exit 0 on the copy after the run;
  - "the cycle's leave-out comes from `cycles`" passes when the copy's `cycle in current code` gap pairs equal what `cycles` proposes on the copy's model with those pairs restored as relationships, and the agent's reply quotes a `cycles` run;
  - AC-19's decided-targets item passes only when the run carries the target stated in the deferral line into the first amendment; the owner script gives it no answer beyond its existing lines.
- **Guard:** before and after each run, `git status --porcelain` and the review log's SHA-256 in the checkout under test and in the coordinator's working directory; any change voids the run, which is recorded and rerun in a fresh copy. A run stopped by a usage limit is void too.

- [ ] **Step 1: preflight.** Copy `empty/` and `modelled/` to scratch folders outside the checkout and run `node scripts/write-deps.mjs` in each; in the `modelled/` copy also run `export`, `cycles --deps build/architecture-deps.json` and `architecture-docs check`. Expected: `build/architecture-deps.json` exists in both; `export` and `architecture-docs check` exit 0; `cycles` prints `0 relationships to leave out in 0 groups, 0 too large`.
- [ ] **Step 2: report the run count to the owner** before any run: 3 RED and 3 GREEN, plus one rerun for each scenario a counter changes, as Sonnet subagents, at about 110k tokens a run (about 660k for the six). Record the owner's answer in the evidence file's "Harness"; no run starts without it.
- [ ] **Step 3: run RED A, RED B and RED C** and grade each.
- [ ] **Step 4: rewrite `pressure-test-evidence.md`:** keep its opening paragraph; "Harness" with the changes above and the owner's run-count answer; then "RED — scenario A/B/C", each with a grading table (AC item | PASS/FAIL | observed), "Failures verbatim" and the pressure record; "Rationalisations seen", each tagged with its pressure and run; "RED failures and the counters that closed them" (RED failure (run) | Counter (file: section) | Closed in GREEN round N?), one row per RED FAIL with the last two columns empty; "Void runs", if any. The earlier rounds graded a skill text that no longer exists and are removed (they stay in git history). Each RED scenario must show at least one FAIL (AC-20); if one shows none, report that to the owner before writing any skill text.
- [ ] **Step 5: commit.**

```bash
git add skills/defining-architecture/pressure-test-evidence.md
git commit -m "test(#31): RED runs for defining-architecture on the record layout - scenarios A, B and C"
```

---

**Rules for Tasks 3 to 7** (`writing-skills`: GREEN is written to the RED failures; the spec's steps and rules are carried whatever RED shows):
- Before writing, reread `skills/writing-skills/SKILL.md` and the RED evidence. Every new counter answers a failure or rationalisation in the evidence file, and the task fills the Counter column of each RED failure its text answers.
- `architecture.md` appears in no file of the skill except where the text says it is gone.
- Every file is loaded by name at the step that needs it, from `SKILL.md`'s step list. Each rule's full text lives in one companion file; `SKILL.md` may state a rule in one line, and another companion points to the rule's file rather than restating it.
- No downstream-project specifics; examples use the made-up shop or neutral names.

Each of Tasks 3 to 7 ends with: run `uv run pytest -q tests/scripts/test_defining_architecture_contract.py` (expected: 6 passed) and `grep -c "architecture\.md" <the task's files>` (expected: `0`, or only the "is gone" line), then commit.

### Task 3: `SKILL.md` (coordinator)

**Tier:** strong — skill text written against the RED failures.

**Files:** Modify `skills/defining-architecture/SKILL.md`.

**Callers that move with this task:** none.

**Reviewer looks at:** the GREEN runs (Task 10) are this task's test; Task 9 and the code review check the text against the spec's "The run" and "Review".

- Satisfies Spec AC: AC-17, AC-18, AC-19 (proved in Task 10)
- **Test retention:** n/a (skill text)

Content rules:
- **Frontmatter** unchanged in form: `name: defining-architecture`; a one-line `description` starting `Use when`, triggers and symptoms only, at most 500 characters. Add a symptom only for a RED failure the description would have caught.
- **Overview and Ownership:** the model folder holds the `.c4` files, `known-gap.json`, `decisions/`, `contracts/`, `changes/`, `coverage.json` and `generated/`; there is no `architecture.md`. The skill writes only there, apart from the waiver entry and the work-item notes; the before copies are never committed.
- **When to Use / When NOT to Use:** the triggers, entry gates and the refusal-inside-the-run rule, unchanged.
- **Steps 1 to 7, one or two lines each,** naming the file each loads: 1 assumptions surface with `roots` (`ARCH_STANDARDS.md`); 2 baseline check, 2a, 2c, 2b in that order (`tools.md`, `amendment.md`; `baseline-run.md` at 2b); 3 write the draft amendment, nothing presented before it has run (`records.md`); 4 cross-cutting decisions; 5 the diff; 6 the known gap; 7 review and approval (`review-workflow.md`, `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md`).
- **Rules that hold at every step:** every run an amendment and the empty folder; when an epic run is required and the waiver; baseline before target; drift is a finding; `check` runs every time (every run quotes a fresh `check` in its change file's `check.output`, even when the model did not change or the request is refused); cross-cutting decisions are the decisions with `obligations`, taken whole for every part they bind, and a principle binds the whole system; judgement goes into records (an improvement seen and not made is a hole or a proposed decision, never a reply only); the owner approves from the generated documents only; a change file is never edited after its run is approved; approval (`[ARCH-APPROVED]` only after self-review and audit, only from the owner).
- **Hard rules,** with "listed in `architecture.md`" becoming "listed in `coverage.json` `unmapped`".
- **Rationalisations, red flags and common mistakes:** each RED rationalisation gets a row, quoted from the evidence file; rows from the current text stay while their rule stays.
- **Review log:** full CLI commands, so the contract test can check `--skill` and `--phase`; the finding kinds include `model-drift`, `deps-defect` and `unsourced`.
- **Size:** `SKILL.md` ends shorter than it is now (`wc -w` before and after in the commit body); detail goes to the companion files of Tasks 4 to 7, never a rule cut.

- [ ] **Step 1: write `SKILL.md`.**
- [ ] **Step 2: check** (the Tasks 3–7 checks above) and run `wc -w skills/defining-architecture/SKILL.md` against the count before the task.
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture/SKILL.md skills/defining-architecture/pressure-test-evidence.md
git commit -m "feat(#31): defining-architecture SKILL.md on the record layout - the steps, the rules and which file each step loads"
```

---

### Task 4: `ARCH_STANDARDS.md` and `tools.md` (coordinator)

**Tier:** strong — skill text.

**Files:** Modify `skills/defining-architecture/ARCH_STANDARDS.md`; Create `skills/defining-architecture/tools.md`; Modify `tests/scripts/test_defining_architecture_contract.py` (`FILES` gains `tools.md`).

**Callers that move with this task:** sweep row 3.

**Reviewer looks at:** the GREEN runs (Task 10); Task 9 and the code review against the spec's "Terms", "Baseline" ("Groups") and "The helper tool".

- Satisfies Spec AC: AC-17, AC-19 (proved in Task 10)
- **Test retention:** n/a (skill text)

Content rules:
- **`ARCH_STANDARDS.md`:**
  - the overlay table gains `roots`: a comma-separated list of `<prefix>` or `<prefix>:<depth>`; a module belongs to the longest root it equals or starts with followed by the separator; its group is that root plus the next `<depth>` segments (`group-depth` when none); an empty root matches every module, its groups being the first `<depth>` segments; a module with no more segments than its root plus `<depth>` is its own group; a module under no root is unmapped with `outside roots`; a module equal to a root gets an element only when the whole repository is baselined, otherwise it is unmapped with `root prefix`; without `roots`, the one root is the longest prefix shared by every repository module; an empty `roots` value, a root listed twice, a depth that is not a whole number of 1 or more, a root that matches no repository module, or a separator of `:` stops the run at step 1;
  - Terms: repository module, root, top-level group, not yet built, Must rule, edge node (a `component` with `code`, no children, no `rules`, in no decision's `binds` or `owner` and no contract's `owner` or `bound`), contract, decision, cross-cutting decision, principle, hole, proposed decision, and the test for spotting a cross-cutting decision (anything two or more elements or capabilities produce, consume or name in common: a data or storage format, a shared contract or API, an id or naming scheme, a vocabulary of kinds);
  - the coverage question, for an epic run whose touched groups are not modelled only: its counts across all roots, the module count including `outside roots` modules, the group count the groups under the roots;
  - mechanism detail and the gap reason format, unchanged.
- **`tools.md`:** each tool's commands as the run uses them, from the repository root with `--repo .`: the delta tool's `export` and `check` (never `--gap`; import relationships against runtime links; `record-error`; the `check` sections and summary); `architecture-records change` with every flag, `--before`, `--compare` (`same`, `differs`, `missing`; before approval only, since an approved file always `differs`) and `cycles` with its text and JSON output; `architecture-docs build|check`; the exit codes and the error form of each. The overlay's flags (`--model`, `--deps`, `--separator`) are named once, in `ARCH_STANDARDS.md`, and referred to here.

- [ ] **Step 1: write both files and add `"tools.md"` to `FILES`.**
- [ ] **Step 2: check** (the Tasks 3–7 checks).
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture/ARCH_STANDARDS.md skills/defining-architecture/tools.md skills/defining-architecture/pressure-test-evidence.md tests/scripts/test_defining_architecture_contract.py
git commit -m "feat(#31): defining-architecture standards with roots, and the three tools in tools.md"
```

---

### Task 5: `records.md` and `amendment.md` (coordinator)

**Tier:** strong — skill text.

**Files:** Create `skills/defining-architecture/records.md` and `skills/defining-architecture/amendment.md`; Modify `tests/scripts/test_defining_architecture_contract.py` (`FILES` gains both).

**Callers that move with this task:** sweep row 3.

**Reviewer looks at:** the GREEN runs (Task 10); Task 9 and the code review against the spec's "The run" (steps 2 to 7).

- Satisfies Spec AC: AC-17, AC-18 (proved in Task 10)
- **Test retention:** n/a (skill text)

Content rules:
- **`records.md`:**
  - which file holds what: decisions and holes in `decisions/<group>.json`, contracts in `contracts/<group>.json`, gap entries in `known-gap.json`, one change file per diff in `changes/<date>-<name>.json`, `coverage.json`; the generated folder is never edited by hand;
  - the fields a run fills: `evidence` and `sources` on every decision; a decided but unbuilt decision and a proposed one are both `planned`; a hole with no source found has evidence `search`; no `capabilities` field and no capability views in any run;
  - the change file's life: the before copy at `architecture-before/<date>-<name>/` in the folder that holds the dependency file, the whole model folder copied just before the first edit of its diff, replacing an earlier copy of that name, made once per diff and kept when the run returns to step 2, never committed, none for an empty folder (`change` then runs without `--before`); a nested baseline (step 2b, or an edge node's inside from step 5) is its own diff with `change --run baseline`, its own `--name` and its own copy, and after its `[ARCH-APPROVED]` the outer diff takes its own copy before its first edit; every `change` run of one diff passes the same `--name` and `--date`; after `[ARCH-APPROVED]` only `approved` is edited, to `{ "by": "owner", "date": <today> }`, and `build` runs once more; a change file is never edited after its run is approved, and `change` refuses to replace one;
  - coverage entries are written after the change file, each naming the change id of the run that added it.
- **`amendment.md`:**
  - step 2: run the `deps-command`, then `export` and `check` (both skipped while the model folder is empty); a `check` exit 1 is a 2a finding and exit 2 stops the run with the tool's error; propose the groups the run touches for the owner to approve;
  - step 2a, for every modelled element the run touches, its relationships and its gap entries: an invalid model (it does not load, or `c4.c4` differs from the shipped spec), a cycle as `cycles` reports it, a `code` value that matches no module, a breach not in the gap file (drift), a gap entry that no longer matches, and a relationship reported not yet reached that the code now has (noted only); each finding gets its own recommendation from the allowed outcomes, and nothing changes before the owner decides each;
  - step 2c (later-stage run), judged only after 2a: refuse a request that changes a cross-cutting decision in part or for one bound element, or changes a product rule, recommending the whole change or the epic instead; a refused request ends the diff, not the run;
  - step 2b: only when touched groups are not modelled, one question with a recommendation and its counts, then `baseline-run.md`; the before copy for this diff is taken just before its first edit (`records.md`);
  - step 3: the draft goes into the files (the `.c4` changes, decisions and holes, contracts, gap entries), then `change`, then the coverage entries, then `export`, `check` and `architecture-docs build`; nothing is presented before this has run (F8); every element a diff adds is placed in at least one area view;
  - step 4: each cross-cutting decision in scope, with options and a recommendation, presented from the written records and approved separately;
  - step 5: the diff, presented from the draft change document and the area documents it touches, with the elements' `rules` as the rule map; a diff that needs an edge node's inside goes back to step 2b;
  - step 6: the known gap from the written `check`: each breach the diff adds with a proposed reason, closed entries removed, renamed ends re-keyed; the owner accepts or rejects each;
  - whatever the owner changes in steps 4 to 6 is edited into the files, and `change` (same `--name` and `--date`), `check` and `build` run again, so the draft change file and the documents always match the files;
  - what the owner is shown: the generated documents only (the change document, the area documents of every area the run touches, the improvement list), never the record files (the one home of this rule; `review-workflow.md` points here);
  - a refused request (step 2c) still writes a change file: its `summary` says what was refused and why, `rejected` holds the request, and the run goes through step 7.

- [ ] **Step 1: write both files and add `"records.md"` and `"amendment.md"` to `FILES`.**
- [ ] **Step 2: check** (the Tasks 3–7 checks).
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture/records.md skills/defining-architecture/amendment.md skills/defining-architecture/pressure-test-evidence.md tests/scripts/test_defining_architecture_contract.py
git commit -m "feat(#31): defining-architecture records.md and amendment.md - the change file's life and steps 2 to 6"
```

---

### Task 6: `baseline-run.md` (coordinator)

**Tier:** strong — skill text.

**Files:** Modify `skills/defining-architecture/baseline-run.md`.

**Callers that move with this task:** none.

**Reviewer looks at:** the GREEN runs (Task 10, scenarios A and C); Task 9 and the code review against the spec's "Baseline".

- Satisfies Spec AC: AC-17, AC-19 (proved in Task 10)
- **Test retention:** n/a (skill text)

Content rules:
- a baseline run covers the whole repository and asks no coverage question; a baseline nested in an epic run covers what step 2b chose;
- groups by `roots` (`ARCH_STANDARDS.md`); the folder and the `c4.c4` copy;
- what a baseline may hold (F2): one `system` and a `container` for each separately built part, each named in the run's step 2 proposal; `external` elements and runtime links for calls that are not imports; `code` below a group where its modules are depended on from different directions; element descriptions of what the part does today, never a target as fact; decisions recovered from the code and earlier documents with `evidence` and `sources`; structure with no reason found as a hole with evidence `search`; contracts with outside systems;
- nesting (F5): every relationship counts for every ancestor of both its ends; a component's parent is a `system` or `container`; any other parent only when `cycles` reports no group among that parent's siblings; groups for reading are area views, never parent elements;
- views: one area view scoped to each container, and area views grouping components for reading, so every element is in at least one area;
- cycles: run `cycles` on the model; propose its leave-out set (the owner chooses in step 6); a group over 20 candidate pairs is chosen by hand; after leaving the relationships out, each new breach `check` reports goes into `known-gap.json` as `cycle in current code`, keyed by the elements its modules map to; a cycle is never left out of both the model and the gap file;
- `coverage.json`: the answer, the counts, each baselined group and edge node with the change id of the run that added it, the unmapped modules with reasons;
- edge nodes, and an edge node's group being baselined (it becomes that group's component);
- a nested baseline: its own diff through steps 3 to 7 with its own change file and before copy (`records.md`), then the outer run resumes;
- the decided-targets question (F7): after a baseline run's `[ARCH-APPROVED]` (not a nested one), ask the owner once for targets already decided that the code does not meet; each answer becomes the first amendment, a later-stage run whose diff request is the owner's answer quoted, with `asked_by` `owner`, through steps 2 to 7, its breaches gapped with reasons; the question still goes out once, and a target the owner stated earlier in the run is put forward as its recommended answer; with no answer, the baseline run ends.

- [ ] **Step 1: write `baseline-run.md`.**
- [ ] **Step 2: check** (the Tasks 3–7 checks).
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture/baseline-run.md skills/defining-architecture/pressure-test-evidence.md
git commit -m "feat(#31): defining-architecture baseline run - roots, containers and outside systems, nesting, cycles from the helper, decided targets"
```

---

### Task 7: `review-workflow.md`, `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md` (coordinator)

**Tier:** strong — skill text. One atomic change across three files: the workflow, the manifest and the rubric must agree item for item, so they change together.

**Files:** Modify the three files in `skills/defining-architecture/`.

**Callers that move with this task:** none.

**Reviewer looks at:** the GREEN runs (Task 10); Task 9 and the code review against the spec's "Review".

- Satisfies Spec AC: AC-17, AC-18, AC-19 (proved in Task 10)
- **Test retention:** n/a (skill text)

Content rules:
- **Inputs** to the self-review and the audit, exactly the spec's list: the model folder (the `.c4` files, `known-gap.json`, the records), `export`, `check` from this run, `cycles`, the run's change file, `change --compare`, `architecture-docs check`, the trigger, read-only access to the repository source, the dependency file and the `deps-command`, and the run's before copy (or a note that it has none). The audit still never gets the conversation.
- **Manifest and rubric,** the spec's items: the rule map is the elements' `rules`; "Baseline coverage" and "Unmapped modules" are `coverage.json`; cross-cutting decisions in scope are the decisions with `obligations` binding a changed element, and every principle, each taken whole and holding only product-level content; no cycles: `cycles` reports 0 groups [whole]; no element's `code` is a root unless the whole repository is baselined [whole]; every edge node is a `component` with `code`, no children and no `rules`, and in no decision's `binds` or `owner` and no contract's `owner` or `bound` [whole]; the change file's `check.output` equals a `check` run now [whole] and `change --compare` with the before copy exits 0 [changed]; every improvement the run noted is a hole or a proposed decision [changed]; `architecture-docs check` exits 0 [whole]; every element is in an area in `export` `areas` [whole]; no element description states a target as fact [changed]. The "decision log only grew" item is removed with no replacement. Every other item stays.
- **The audit's second method (F1):** the auditor scans the source for imports by its own search over import statements, compares the module edges it finds inside the coverage with the dependency file, and an edge the file lacks is a `deps-defect` finding that fails the audit; a `deps-defect` stops the run, which reports the missing edges to the owner with a recommended fix to the `deps-command` (the owner, or a work item, changes it, since the skill changes no file outside the model folder), then resumes at step 2 keeping its before copy.
- **Owner approval:** show the owner the documents `amendment.md` lists, and both verdicts; after `[ARCH-APPROVED]` the change file is finished as `records.md` says.
- **Work-item note:** names the change id instead of the decision-log date.
- **Review-log calls** as full CLI commands, the finding kinds including `model-drift`, `deps-defect` and `unsourced`.

- [ ] **Step 1: write the three files.**
- [ ] **Step 2: check** (the Tasks 3–7 checks) and `grep -c "decision log only grew" skills/defining-architecture/ARCH_RUBRIC.md` (expected: `0`).
- [ ] **Step 3: commit.**

```bash
git add skills/defining-architecture/review-workflow.md skills/defining-architecture/ARCH_REVIEW_MANIFEST.md skills/defining-architecture/ARCH_RUBRIC.md skills/defining-architecture/pressure-test-evidence.md
git commit -m "feat(#31): defining-architecture review on the record layout - the helper's checks, the docs check and the audit's import scan"
```

---

### Task 8: the earlier spec points here (coordinator)

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

### Task 9: the skill text reviewed before GREEN (coordinator)

**Tier:** strong — a fresh-context review and its fixes.

**Files:** any file of Tasks 3 to 7 a finding changes.

**Callers that move with this task:** none.

**Reviewer looks at:** every finding fixed before any GREEN run — caught by: the review-log entry and the plan-end code review.

- Satisfies Spec AC: none directly (keeps the GREEN evidence about the text that ships)
- **Test retention:** n/a

- [ ] **Step 1: review.** A fresh-context reviewer reads Tasks 3 to 7's files against the spec's "The run", "Baseline" and "Review" and the content rules above, and reports each rule that is missing, wrong or in two homes. Log it with `--skill requesting-code-review --phase CODE_REVIEW`.
- [ ] **Step 2: fix every finding** in its file, as one commit `fix(#31): skill text review - <summary>`, and rerun the Tasks 3–7 checks. Expected: 6 passed.

---

### Task 10: GREEN runs and loophole fixes (coordinator)

**Tier:** strong — coordinator-run pressure runs.

**Files:** Modify `skills/defining-architecture/pressure-test-evidence.md`; any skill file a counter changes (added to `FILES` if new).

**Callers that move with this task:** sweep row 3, for a file a counter adds.

**Reviewer looks at:** each GREEN FAIL has a counter and a rerun, or went to the owner after its second round — caught by: plan-end code review of the evidence file.

- Satisfies Spec AC: AC-17, AC-18, AC-19, AC-20 (GREEN half)
- **Test retention:** **Permanent** (evidence file)

- [ ] **Step 1: run GREEN A, GREEN B and GREEN C** with the harness of Task 2, the GREEN prompt naming the skills folder of this checkout, and grade each.
- [ ] **Step 2: record** each run in the evidence file: "GREEN — scenario X, round N" with the grading table, the pressure record (a hold whose reason cites the skill is noted as such; a hold with none as fragile), and how the run was observed; fill the "Closed in GREEN round N?" column of each RED failure from the grading.
- [ ] **Step 3: for each FAIL,** run the `writing-skills` meta-test with that agent (ask how the skill could have made the right choice clear), write the counter into the skill file it belongs to, commit it as `fix(#31): counter for <failure>`, add a row for the GREEN failure and its counter to "RED failures and the counters that closed them", and rerun that scenario as the next round. A scenario still failing after its second GREEN round goes to the owner, not a third round.
- [ ] **Step 4: run the full suite.** Run: `uv run pytest -q` (about 3 minutes). Expected: all pass.
- [ ] **Step 5: commit.**

```bash
git add skills/defining-architecture/pressure-test-evidence.md
git commit -m "test(#31): GREEN runs for defining-architecture on the record layout"
```

## Plan end

After Task 10: the code review of the whole plan on fresh-context Opus (the skill text against the spec, the evidence file against the grading rule); a code-review change to a step or rule reruns the scenarios it affects, counted as reruns. Survivability takes Task 1's items (mutation lane `full`). Then plan 4 (the other skills' wording).
