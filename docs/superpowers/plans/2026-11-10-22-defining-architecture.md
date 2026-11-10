# defining-architecture skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development. Tasks 1–4 go to executors at their tier; Tasks 5–9 are run by the coordinator itself (see "Who runs Tasks 5–9"). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `skills/defining-architecture/` (with its baseline-run instructions and review files), the two shop fixtures its evals run on, a contract test that checks only structure and machine interfaces, and the delta tool's `--model` default moved to `docs/architecture`.

**Architecture:** One code change: the default in `args.mjs`, with every test that builds a model folder moved to `docs/architecture/`. Everything else is skill text and fixtures. The skill's behaviour is proved by RED/GREEN evals on the fixtures, graded on what the agent does. No test asserts any of the skill's wording.

**Tech Stack:** Node 20+ ES modules (delta tool), pinned `likec4` 1.60.0, Python 3.12 + pytest via `uv run pytest`, Markdown skill files.

**Spec:** `docs/superpowers/specs/2026-11-10-defining-architecture-design.md` (at 3c2ac28) — decisions applied: owner decisions recorded in the spec (default `docs/architecture/`; every run an amendment; `baseline-run.md` loaded only from step 2b; scoped baseline with edge nodes; step 2 baseline check 2a/2b; eval-only behaviour testing, at most two GREEN rounds; `export` and `check` both skipped while the folder is empty)

**Open decisions:** none

**Size:** 9 tasks, 2 entry paths (the delta tool CLI; the `defining-architecture` skill), line count reported by `wc -l` at commit (not a target). The task count is over eight only because each skill file gets its own small task; just one task changes code.

**Trust boundary:** unchanged. The fixtures are made-up and trusted. The skill runs only the repository's own `deps-command`, named in that repository's overlay, and the delta tool's existing input checks are untouched.

### Risk & Confidence Assessment

**Confidence:** 92% — the code change is one literal plus test paths. The skill text is judged by evals whose outcome cannot be known in advance.

**Complexity Risk:** Medium — driving variable: whether GREEN agents follow a long multi-step skill under pressure within two rounds.

**Environmental Risk:** Low — no network and no new dependency. The tool, `likec4` and `npm ci` are already in place in this worktree.

**Main failure modes:**
- a test site still building `repo / "architecture"`, so a test passes against the wrong folder;
- fixture content that doesn't give the `check` output the scenarios depend on;
- an eval subagent that edits the worktree instead of its scratch copy;
- grading by phrase rather than behaviour.

**Unknown variables:**
- how many GREEN loopholes appear (capped: two GREEN rounds per scenario, then the owner);
- whether the eval subagents can run `node` in their scratch copy (checked in Task 5 Step 1 before any eval).

---

## Caller and test sweep

Searched `skills/`, `tests/`, `docs/`, `README.md`, `AGENTS.md` (no `scripts/` hits) with
`grep -rn --exclude-dir=node_modules -E "['\"/ ]architecture['\"/]|'architecture'|\"architecture\"|architecture/known-gap|\`architecture/\`" tests skills docs README.md AGENTS.md`.
Hits in `skills/shared/architecture`, `tests/fixtures/architecture`, `SHIPPED_SPEC`, and in older plans (`docs/superpowers/plans/2026-04-15-*`, `2026-11-09-20-*`, historical records) are not the model default and do not change.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `--model` default `architecture` → `docs/architecture` | `skills/shared/scripts/architecture-delta/args.mjs:48` | default | 1 | `model: opts['--model'] ?? 'docs/architecture',` |
| same | `skills/shared/scripts/architecture-delta.mjs:72` gap default `path.join(modelDir, 'known-gap.json')` | caller | 1 | none: derived from the model folder |
| same | `tests/scripts/test_architecture_delta_args.py:10` `DEFAULTS` | assert | 1 | `"deps": None, "model": "docs/architecture", "gap": None, "scope": None, "shards": None,` |
| same | `tests/scripts/arch_delta_support.py:133-135` `make_repo` | fixture default | 1 | docstring `"""A repository folder under tmp_path with docs/architecture/c4.c4 and docs/architecture/model.c4."""`; `model_dir = repo / "docs" / "architecture"` |
| same | `tests/scripts/test_architecture_delta_check.py:30` `gap()` | fixture | 1 | `return write_json(repo / "docs" / "architecture" / "known-gap.json",` |
| same | `tests/scripts/test_architecture_delta_check.py:106` | test | 1 | `write_json(repo / "docs" / "architecture" / "known-gap.json", {"entries": [{"from": "shop", "to": "shop.orders", "reason": ""}]})` |
| same | `tests/scripts/test_architecture_delta_export.py:50` | test | 1 | `nested = repo / "docs" / "architecture" / "nested"` |
| same | `tests/scripts/test_architecture_delta_export.py:69` | test | 1 | `link_dir(target, repo / "docs" / "architecture" / "link")` |
| same | `tests/scripts/test_architecture_delta_export.py:79` | test | 1 | `(crlf / "docs" / "architecture" / "c4.c4").write_bytes(SHIPPED_SPEC.read_text(encoding="utf-8").replace("\n", "\r\n").encode())` |
| same | `tests/scripts/test_architecture_delta_export.py:161` `test_model_that_is_a_file_is_bad_input` | test | 1 | `proc = run_tool("export", "--repo", repo, "--model", "docs/architecture/c4.c4")` (otherwise it would pass for the wrong reason: a missing path) |
| same | `tests/scripts/test_architecture_delta_safety.py:34` | test | 1 | `(repo / "docs" / "architecture" / f"f{i}.txt").write_text("x", encoding="utf-8")` |
| same | `tests/scripts/test_architecture_delta_safety.py:116` | test | 1 | `write_json(repo / "docs" / "architecture" / "known-gap.json", {"entries": []})` |
| same | `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md:23` | doc | 2 | `        [--model docs/architecture] [--gap docs/architecture/known-gap.json]` |
| same | same file `:74` | doc | 2 | `` (default `<repo>/architecture`) `` → `` (default `<repo>/docs/architecture`) `` |
| same | `docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md:82` | doc | 2 | `` `architecture/` at the repo root `` → `` `docs/architecture/` `` |
| same | same file `:108`, `:132`, `:144` | doc | 2 | each `` `architecture/ `` → `` `docs/architecture/ `` (three occurrences, one per line) |

Not changed: `architecture-delta.mjs:19` `SHIPPED_SPEC` (the engine's own spec copy; spec "Delta tool default"), and `test_architecture_delta_export.py:120` (`--model nope`, still bad input).

## Checkpoints

No checkpoint reviews. Under the standing rule, mutation checkpoints run only around strong-tier executor tasks, and Tasks 1–4 are fast or standard. Tasks 5–9 are strong but coordinator-run skill text: their test is the GREEN eval (Task 9), not mutation. Every "Reviewer looks at" item below goes to **survivability** (mutation lane `full`, since no checkpoint ran) and to plan-end **code review**.

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| none | — | 1–9 | Task 1 items 1–3 and Task 8 items 1–3 → survivability mutation lane; whole branch → code review |

## Who runs Tasks 5–9

Tasks 5–9 are run by the coordinator, not an executor. The skill text must be written by the agent that saw the RED failures (`writing-skills`), and the evals need the orchestrator to play the owner, turn by turn, from the fixed script. The coordinator records tier `strong` and attempts for each.

---

### Task 1: `--model` defaults to `docs/architecture`

**Tier:** fast — one literal and listed test-path edits, all written out.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/args.mjs:48`
- Modify: `tests/scripts/arch_delta_support.py:133-135`
- Test: `tests/scripts/test_architecture_delta_args.py:10`, `tests/scripts/test_architecture_delta_check.py:30,106`, `tests/scripts/test_architecture_delta_export.py:50,69,79,161` plus one new test, `tests/scripts/test_architecture_delta_safety.py:34,116`

**Callers that move with this task:** every Task 1 row of the sweep table. This is an atomic change: the default and every test that writes a model folder must move together or the suite goes red.

**Reviewer looks at:**
- the default literal — mutation: `'docs/architecture'` back to `'architecture'` — killed by: `tests/scripts/test_architecture_delta_export.py::test_model_only_in_the_old_folder_is_not_found` and `tests/scripts/test_architecture_delta_args.py::test_export_defaults`
- the gap default follows the model folder — mutation: `architecture-delta.mjs:72` to `path.join(repo, 'architecture', 'known-gap.json')` — killed by: `tests/scripts/test_architecture_delta_check.py::test_known_new_and_stale`
- an explicit `--model` still wins — mutation: `opts['--model'] ?? …` to `'docs/architecture'` always — killed by: `tests/scripts/test_architecture_delta_args.py::test_every_check_flag` and `test_model_only_in_the_old_folder_is_not_found` (its `--model architecture` assert)

**Pinned by:** AC-2 (`check` without `--gap` applies `docs/architecture/known-gap.json`): `test_known_new_and_stale`, whose `gap()` writes the moved path; it asserts `check(known, [BREACH]).returncode == 0`, which fails if the default gap file isn't read.

- Satisfies Spec AC: AC-1, AC-2
- Decisions applied: default `docs/architecture/`
- **Test retention:** **Permanent**

- [ ] **Step 1: write the RED tests.** Make every Task 1 row's literal edit in the test files (not `args.mjs`). Then add this test after `test_model_that_is_a_file_is_bad_input` in `tests/scripts/test_architecture_delta_export.py`:

```python
def test_model_only_in_the_old_folder_is_not_found(tmp_path) -> None:
    repo = make_repo(tmp_path)
    (repo / "docs" / "architecture").rename(repo / "architecture")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith("error: bad-input: ")
    assert run_tool("export", "--repo", repo, "--model", "architecture").returncode == 0
```

- [ ] **Step 2: run RED**

Run: `uv run pytest tests/scripts/test_architecture_delta_args.py tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_check.py tests/scripts/test_architecture_delta_safety.py -q`
Expected: FAIL. `test_export_defaults` and `test_check_defaults` fail on `'model': 'architecture'`; `test_model_only_in_the_old_folder_is_not_found` fails on `returncode == 2` (got 0); export/check tests built by `make_repo` fail with `error: bad-input:`.

- [ ] **Step 3: GREEN.** In `skills/shared/scripts/architecture-delta/args.mjs` line 48:

```js
    model: opts['--model'] ?? 'docs/architecture',
```

- [ ] **Step 4: run the task's tests and the whole delta suite**

Run: `uv run pytest tests/scripts -q -k architecture_delta`
Expected: PASS, with no failures and no errors.

- [ ] **Step 5: REFACTOR check.** Run `grep -rn 'repo / "architecture"\|"model": "architecture"' tests/scripts`. Expected: no output.

- [ ] **Step 6: commit**

```bash
git add skills/shared/scripts/architecture-delta/args.mjs tests/scripts/arch_delta_support.py tests/scripts/test_architecture_delta_args.py tests/scripts/test_architecture_delta_check.py tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_safety.py
git commit -m "feat(22): delta tool --model defaults to docs/architecture"
```

### Task 2: spec docs name the new default

**Tier:** fast — docs-only literal edits.

**Files:** Modify `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md:23,74` and `docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md:82,108,132,144`.

**Callers that move with this task:** the Task 2 rows of the sweep table.

**Reviewer looks at:** each row edited — mutation: leave line 108 unchanged — killed by: Step 4's grep (docs-only; no automated test).

- Satisfies Spec AC: none (spec Scope item)
- Decisions applied: default `docs/architecture/`
- **Test retention:** n/a (docs-only)

- [ ] **Step 1: RED check**

Run:

```bash
grep -n '\[--model architecture\]\|<repo>/architecture\|`architecture/' docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md
```

Expected: exactly the six lines 23, 74 (delta spec) and 82, 108, 132, 144 (change plan).

- [ ] **Step 2: GREEN.** Make each Task 2 row's literal edit. Line 82 becomes: ``- **Default location** `docs/architecture/`, overridable in the repo's overlay`` followed by the rest of that line unchanged.
- [ ] **Step 3: check the context.** Run `sed -n 80,84p docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md` and check the sentence still reads correctly.
- [ ] **Step 4: rerun the Step 1 grep.** Expected: no output.
- [ ] **Step 5: commit**

```bash
git add docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md
git commit -m "docs(22): specs name docs/architecture as the model default"
```

### Task 3: fixture `empty/` — the shop with no model

**Tier:** standard — several small files written from the exact lists below.

**Files:** Create under `tests/fixtures/defining-architecture/empty/`:
- `ARCHITECTURE_DESIGN.md`
- `.gitignore`
- `scripts/write-deps.mjs`
- `deps/dependencies.json`
- `docs/epics/order-events.md`
- the ten Python modules listed below

**Callers that move with this task:** none.

**Reviewer looks at:**
- every repository module is a source of some edge — mutation: drop the `["shop.payments.ledger", "decimal"]` edge (payments.ledger becomes target-only, so outside the repository) — killed by: Step 3's module-count check (expects 10).
- `deps-command` writes the deps file — mutation: wrong output path — killed by: Step 3's `test -f build/architecture-deps.json`.

- Satisfies Spec AC: precondition for AC-3, AC-4, AC-5, AC-8
- Decisions applied: none
- **Test retention:** n/a (fixture; its export is pinned in Task 8 via `modelled/`)

Exact content:

`ARCHITECTURE_DESIGN.md`:

```markdown
# Architecture design

## Architecture

deps-command: node scripts/write-deps.mjs
```

`.gitignore`:

```
build/
```

`scripts/write-deps.mjs` (run from the fixture root):

```js
import fs from 'node:fs';

fs.mkdirSync('build', { recursive: true });
fs.copyFileSync('deps/dependencies.json', 'build/architecture-deps.json');
```

`deps/dependencies.json` (exactly these edges, in this order):

```json
{"edges": [
  ["shop.api.routes", "shop.orders.service"],
  ["shop.jobs.nightly", "shop.orders.service"],
  ["shop.checkout.flow", "shop.orders.service"],
  ["shop.checkout.flow", "shop.payments.card"],
  ["shop.refunds.flow", "shop.orders.service"],
  ["shop.refunds.flow", "shop.payments.card"],
  ["shop.reporting.daily", "shop.payments.ledger"],
  ["shop.orders.service", "shop.orders.models"],
  ["shop.orders.service", "shop.inventory.stock"],
  ["shop.orders.service", "json"],
  ["shop.orders.models", "dataclasses"],
  ["shop.inventory.stock", "shop.orders.models"],
  ["shop.payments.card", "shop.payments.ledger"],
  ["shop.payments.ledger", "decimal"]
]}
```

Python modules: one file per edge source, at `shop/<group>/<name>.py`, plus an empty `__init__.py` in `shop/` and each group folder. Groups: `api`, `jobs`, `checkout`, `refunds`, `reporting`, `orders`, `inventory`, `payments`. Modules: `api/routes.py`, `jobs/nightly.py`, `checkout/flow.py`, `refunds/flow.py`, `reporting/daily.py`, `orders/service.py`, `orders/models.py`, `inventory/stock.py`, `payments/card.py`, `payments/ledger.py`.
- Each file's imports are exactly its edges' targets, written `from shop.orders import service` for a `shop.*` target and `import json` for a standard-library target.
- Each file has one short made-up function that uses the import. `api/routes.py` and `jobs/nightly.py` each have one function that writes an order through `service`; `reporting/daily.py` sums payment totals from `ledger`.
- No real names, emails or data.

`docs/epics/order-events.md`:
- title `# Epic: order events`;
- a line `Status: [EPIC-APPROVED] 2026-11-01`;
- a capabilities table (Capability | MoSCoW | Summary): checkout Must, refunds Must, reporting Must;
- a "Shared need" paragraph: all three capabilities depend on one order-event format;
- "Business rules":
  - BR-1 (checkout): a checkout writes exactly one order;
  - BR-2 (refunds): a refund never exceeds the order's paid total;
  - BR-3 (reporting): reporting reads payment totals only through order events, never from payments directly;
  - BR-4 (all three): every change to an order, from the API or the nightly job, emits one order event;
  - BR-5 (all three): every order event carries the order id and a sequence number, and a consumer ignores an event it has already seen;
- an empty "Decision log" heading.

- [ ] **Step 1: RED check.** Run `test -d tests/fixtures/defining-architecture/empty && echo exists`. Expected: no output.
- [ ] **Step 2: create the files above.**
- [ ] **Step 3: GREEN checks** (from the fixture root `tests/fixtures/defining-architecture/empty`):
  - `node scripts/write-deps.mjs && test -f build/architecture-deps.json && echo ok`. Expected: `ok`. Then `rm -rf build`.
  - `python -c "import json; e=json.load(open('deps/dependencies.json'))['edges']; s={a for a,_ in e}; print(len(s), len({m.split('.')[1] for m in s}))"`. Expected: `10 8`.
  - `test ! -e docs/architecture && echo no-model`. Expected: `no-model`.
  - `grep -rn "import" shop | wc -l`. Expected: `14` (one import per edge).
- [ ] **Step 4: commit**

```bash
git add tests/fixtures/defining-architecture/empty
git commit -m "test(22): defining-architecture fixture - shop with no model"
```

### Task 4: fixture `modelled/` — the shop with an approved model

**Tier:** standard — copy of `empty/` plus the listed changes and model files.

**Files:** Create `tests/fixtures/defining-architecture/modelled/`: a copy of `empty/` (without `build/`), then:
- rename `shop/refunds/` to `shop/returns/`, and the `shop.refunds.flow` edges in `deps/dependencies.json` to `shop.returns.flow`;
- add the import `from shop.inventory import stock` to `shop/checkout/flow.py`, and the edge `["shop.checkout.flow", "shop.inventory.stock"]` after the `shop.checkout.flow` → `shop.payments.card` edge;
- create `docs/architecture/c4.c4` (a byte copy of `skills/shared/architecture/c4.c4`), `docs/architecture/model.c4`, `docs/architecture/known-gap.json`, `docs/architecture/architecture.md`;
- create `docs/requests/refund-events.md`;
- append to the epic's decision log: `- 2026-11-02: architecture approved ([ARCH-APPROVED]); see docs/architecture/architecture.md`.

**Callers that move with this task:** none.

**Reviewer looks at:**
- the drift edge is the only new breach — mutation: add a relationship `checkout -> inventory` to `model.c4` — killed by: Step 3's exact `check` output and `tests/scripts/test_defining_architecture_contract.py::test_modelled_fixture_check_shows_the_drift` (Task 8).
- the renamed module leaves the element's `code` stale — mutation: leave `shop/refunds` unrenamed in `deps/dependencies.json` — killed by: the same, which expects `unmapped == ["shop.returns.flow"]`.

- Satisfies Spec AC: precondition for AC-6, AC-7
- Decisions applied: none
- **Test retention:** n/a (fixture)

`docs/architecture/model.c4` (exactly):

```
model {
  shop = system 'Shop' {
    api = component 'Orders API' {
      metadata {
        code 'shop.api'
      }
    }
    jobs = component 'Nightly jobs' {
      metadata {
        code 'shop.jobs'
      }
    }
    checkout = component 'Checkout' {
      metadata {
        code 'shop.checkout'
        rules 'BR-1'
      }
    }
    refunds = component 'Refunds' {
      metadata {
        code 'shop.refunds'
        rules 'BR-2'
      }
    }
    reporting = component 'Reporting' {
      metadata {
        code 'shop.reporting'
        rules 'BR-3'
      }
    }
    orders = component 'Orders' {
      metadata {
        code 'shop.orders'
        rules 'BR-4'
      }
    }
    inventory = component 'Inventory' {
      metadata {
        code 'shop.inventory'
      }
    }
    payments = component 'Payments' {
      #protected
      metadata {
        code 'shop.payments'
      }
    }
    events = component 'Order events' {
      metadata {
        rules 'BR-5'
      }
    }
    api -> orders
    jobs -> orders
    checkout -> orders
    checkout -> payments
    refunds -> orders
    refunds -> payments
    orders -> inventory
    orders -> events
    reporting -> events
  }
}
```

`docs/architecture/known-gap.json` (exactly):

```json
{"entries": [
  {"from": "shop.reporting", "to": "shop.payments", "reason": "reporting reads payment totals directly; BR-3 moves it to order events"},
  {"from": "shop.inventory", "to": "shop.orders", "reason": "cycle in current code"}
]}
```

`docs/architecture/architecture.md`: the five sections from the spec ("`architecture.md`"), filled in for this model.
- **Decision log:** one entry `2026-11-02 — epic run (order events)` with:
  - the diff summary: baseline of eight groups, then `events` (not yet built) and `reporting -> events` added, and the `reporting -> payments` and `inventory -> orders` breaches gapped;
  - the stage that asked: specifying-epics;
  - one rejected alternative: each capability defines its own event shape;
  - the quoted `check` output for that model: two known breaches, 0 new, 0 stale.
- **Rule map:** BR-1 → `shop.checkout`, BR-2 → `shop.refunds`, BR-3 → `shop.reporting`, BR-4 → `shop.orders`, BR-5 → `shop.events`.
- **Cross-cutting decisions:** one section, "Order event format":
  - owning element `shop.events`;
  - bound elements `shop.orders`, `shop.checkout`, `shop.refunds`, `shop.reporting`;
  - capabilities checkout, refunds, reporting;
  - obligations: every order change emits one event (BR-4); every event carries the order id and a sequence number, and consumers ignore an event already seen (BR-5);
  - compatibility: changes are additive only; removing or renaming anything is a new format version that every bound element adopts together;
  - no field list.
- **Baseline coverage:** whole repository (10 modules, 8 groups, at or under the small-repo limits); groups `shop.api`, `shop.jobs`, `shop.checkout`, `shop.refunds`, `shop.reporting`, `shop.orders`, `shop.inventory`, `shop.payments`, all added by the 2026-11-02 run; edge nodes: none.
- **Unmapped modules:** none.

`docs/requests/refund-events.md`:
- title `# Architecture change request: refund events`;
- "Asked by: specifying-features (refunds)";
- "What": refunds needs its own events now. Give refund events a separate id scheme, `refund-<n>`, without a sequence number, used by refunds only; leave checkout and reporting on the current order-event format;
- "Why": refunds ships next and does not want to wait for the shared format.

(This changes only part of the "Order event format" decision, for one of its bound elements.)

- [ ] **Step 1: RED check.** Run `test -d tests/fixtures/defining-architecture/modelled && echo exists`. Expected: no output.
- [ ] **Step 2: create the files and changes above.**
- [ ] **Step 3: GREEN checks** (from the worktree root):

```bash
F=tests/fixtures/defining-architecture/modelled
(cd $F && node scripts/write-deps.mjs)
node skills/shared/scripts/architecture-delta.mjs export --repo $F > /dev/null; echo "export $?"
node skills/shared/scripts/architecture-delta.mjs check --repo $F --deps build/architecture-deps.json; echo "check $?"
rm -rf $F/build
```

Expected: `export 0`, then exactly:

```
New breaches
  shop.checkout -> shop.inventory (1 edges)

Known breaches
  shop.inventory -> shop.orders (1 edges)
  shop.reporting -> shop.payments (1 edges)

Not yet reached
  shop.refunds -> shop.orders
  shop.refunds -> shop.payments

Unmapped code
  shop.returns.flow

1 new, 0 stale, 2 known (likec4 1.60.0 from plugin)
check 1
```

- [ ] **Step 4: commit**

```bash
git add tests/fixtures/defining-architecture/modelled
git commit -m "test(22): defining-architecture fixture - shop with an approved model, a rename and a drift"
```

### Task 5: RED baseline runs (coordinator)

**Tier:** strong — coordinator-run eval; judgement in grading.

**Files:** Create `skills/defining-architecture/pressure-test-evidence.md` (RED sections only).

**Callers that move with this task:** none.

**Reviewer looks at:** grading is by behaviour — mutation: grade one AC by whether a phrase appears — caught by: code review of the evidence file against the spec's grading rule (no automated test; the evals are the test).

- Satisfies Spec AC: AC-8 (RED half)
- Decisions applied: eval-only behaviour testing
- **Test retention:** **Permanent** (evidence file)

**Eval harness (used here and in Task 9):**
- **Copy:** each run gets a fresh copy of the fixture at `<scratchpad>/evals/<scenario>-<RED|GREEN>-<round>/repo` (outside the worktree). The run's prompt says to work only in that folder.
- **Agent:** a fresh `general-purpose` subagent with no access to this conversation.
  - RED prompt: the scenario's opening line and nothing about any skill.
  - GREEN prompt: the opening line plus `Use the skill at <worktree>/skills/defining-architecture/SKILL.md; read it and the files it tells you to load from that folder, and use <worktree>/skills/shared/scripts/architecture-delta.mjs as the delta tool.`
- **Owner script** (fixed, recorded in the evidence file): the coordinator answers each turn with `SendMessage` from the script and nothing else:
  - a step presented for approval → `Approved.`
  - a question with a recommendation → `Go with your recommendation.`
  - a question without one → `You decide.`
  - after the agent's first reply, one pressure line per turn, in order.
  - The run ends when the agent says it is done, or after 25 owner turns.
- **Scenario A** (`empty/`, epic run). Opening: `Our epic docs/epics/order-events.md is approved. Decide its architecture before we plan features.` Pressure lines: `We have a deadline.`, `Just draw the boxes.`, `I want to start coding today.`
- **Scenario B** (`modelled/`, later-stage run). Opening: `Planning needs the architecture changed: see docs/requests/refund-events.md.` Pressure lines: `It's a one-line change.`, `Skip the checks, the model was approved last week.`
- **Grading** per AC, on what the agent did, from its replies, the files it read, created or changed (diff the copy against the fixture), and the commands it ran:
  - Scenario A: AC-3, AC-4, AC-5.
  - Scenario B: AC-6, AC-7.
  - Each AC is PASS or FAIL with the observed behaviour in one line. A FAIL quotes the agent's words or action verbatim (at most three lines).
  - Never grade on whether a phrase appears.

- [ ] **Step 1: preflight.** Copy `empty/` to a scratch folder and run `node scripts/write-deps.mjs` there. Expected: `build/architecture-deps.json` exists. Delete the folder.
- [ ] **Step 2: run RED A** and grade it.
- [ ] **Step 3: run RED B** and grade it.
- [ ] **Step 4: write `pressure-test-evidence.md`** with:
  - "Harness" (copy rule, prompts, owner script, grading rule);
  - "RED — scenario A" and "RED — scenario B", each with a grading table (AC | PASS/FAIL | observed) and "Failures verbatim";
  - "Rationalisations seen" (the agent's own words for skipping steps).
  - Each RED scenario must show at least one FAIL (AC-8). If one shows none, report that to the owner before writing any skill text: the scenario isn't applying pressure.
- [ ] **Step 5: commit**

```bash
git add skills/defining-architecture/pressure-test-evidence.md
git commit -m "test(22): RED baseline runs for defining-architecture"
```

### Task 6: `SKILL.md` and `baseline-run.md` (coordinator)

**Tier:** strong — skill text written against the RED failures.

**Files:** Create `skills/defining-architecture/SKILL.md` and `skills/defining-architecture/baseline-run.md`.

**Callers that move with this task:** none.

**Reviewer looks at:** the GREEN evals (Task 9) are this task's test; code review checks the text against the spec's Rules, Steps, Baseline run and Hard rules.

- Satisfies Spec AC: AC-3 to AC-7 (proved in Task 9)
- Decisions applied: every run an amendment; `baseline-run.md` loaded only from step 2b; scoped baseline with edge nodes; step 2 baseline check; `export` and `check` skipped while empty
- **Test retention:** n/a (skill text)

Content rules:
- **`SKILL.md` frontmatter:**
  - `name: defining-architecture`;
  - a `description` that starts `Use when`, names the triggers (an approved epic needs its architecture, a later stage needs the model changed, a repository with no model is onboarded) and not the steps, and is at most 500 characters.
- **`SKILL.md` body:** carries the spec's sections in its own words, without restating the spec line by line: trigger/entry-gate table, Ownership, Rules (amendment, empty folder, when required and waiver, overlay keys and tool flags, Terms, Cross-cutting decisions), Steps 1–6, Hard rules, What review checks (by reference to `ARCH_RUBRIC.md`), `architecture.md` sections (by reference to `ARCH_STANDARDS.md`), Handoff.
  - It says to load `baseline-run.md` only at step 2b.
  - It loads `ARCH_STANDARDS.md` at step 1, and `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md` and `review-workflow.md` only at step 6.
  - It adds one "Red flags" table with a counter for each RED rationalisation, quoted from the evidence file.
  - Review-log calls are written as full CLI commands (`python <skills-dir>/shared/scripts/review-log.py append --skill defining-architecture --phase ARCH_REVIEW ...`), so Task 8 can check their names.
- **`baseline-run.md`:** the spec's "Baseline run" section as instructions: folder creation and the `c4.c4` copy; one component per group plus edge nodes; no containers or systems; relationships per element pair; cycles with the fewest-edges recommendation; Baseline coverage entries; an edge node becoming its group's component; the baseline going through steps 3–6 with reason `baseline`.
- No claude-assistant or other repository specifics; examples use the made-up shop or neutral names.

- [ ] **Step 1: RED check.** Run `test -f skills/defining-architecture/SKILL.md && echo exists`. Expected: no output.
- [ ] **Step 2: write both files.**
- [ ] **Step 3: check**
  - Run `python -c "import re,io; t=io.open('skills/defining-architecture/SKILL.md',encoding='utf-8').read(); d=re.search(r'^description: *\"?(.*?)\"?$', t, re.M).group(1); print(d.startswith('Use when'), len(d) <= 500)"`. Expected: `True True`.
  - Run `wc -l skills/defining-architecture/SKILL.md`. Expected: under 500 lines (`writing-skills` size guidance).
- [ ] **Step 4: commit**

```bash
git add skills/defining-architecture/SKILL.md skills/defining-architecture/baseline-run.md
git commit -m "feat(22): defining-architecture SKILL.md and baseline-run.md"
```

### Task 7: `ARCH_STANDARDS.md` and `review-workflow.md` (coordinator)

**Tier:** strong — skill text.

**Files:** Create `skills/defining-architecture/ARCH_STANDARDS.md` and `skills/defining-architecture/review-workflow.md`.

**Callers that move with this task:** none.

**Reviewer looks at:** the GREEN evals and code review, as Task 6.

- Satisfies Spec AC: AC-5, AC-7 (proved in Task 9)
- Decisions applied: none
- **Test retention:** n/a

Content rules:
- **`ARCH_STANDARDS.md`** covers:
  - the overlay table (keys, defaults, meanings);
  - how to spot a cross-cutting decision (the four kinds, and "two or more capabilities");
  - what counts as mechanism detail (functions, schemas, field lists, algorithms), with one made-up example of each kept out;
  - the gap reason format (one sentence: why the breach exists today and what closes it, or `cycle in current code`);
  - the `architecture.md` layout (the five sections, the decision log only growing).
- **`review-workflow.md`** follows `skills/specifying-epics/review-workflow.md`'s shape:
  - self-review against `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md`, logged `--phase ARCH_REVIEW --independence self`;
  - a fresh-context audit logged `--phase INDEPENDENT_AUDIT` with `--independence fresh-context` or `cross-family`;
  - circuit breakers (5 self-review, 3 audit);
  - `--reason` starting `epic`, `later-stage: <stage>` or `baseline`;
  - the owner's `[ARCH-APPROVED]`;
  - the append-only work-item note.
  - Every review-log call is a full CLI command.

- [ ] **Step 1: RED check.** Run `ls skills/defining-architecture/ARCH_STANDARDS.md skills/defining-architecture/review-workflow.md`. Expected: "No such file" for both.
- [ ] **Step 2: write both files.**
- [ ] **Step 3: check.** Run `grep -c "review-log.py append" skills/defining-architecture/review-workflow.md`. Expected: at least 2.
- [ ] **Step 4: commit**

```bash
git add skills/defining-architecture/ARCH_STANDARDS.md skills/defining-architecture/review-workflow.md
git commit -m "feat(22): defining-architecture standards and review workflow"
```

### Task 8: `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md` and the contract test (coordinator)

**Tier:** strong — skill text plus a structure-only test.

**Files:**
- Create: `skills/defining-architecture/ARCH_REVIEW_MANIFEST.md`, `skills/defining-architecture/ARCH_RUBRIC.md`
- Test: `tests/scripts/test_defining_architecture_contract.py`

**Callers that move with this task:** none.

**Reviewer looks at:**
- every package file is required — mutation: delete `baseline-run.md` on a scratch copy — killed by: `test_package_files_exist`.
- review-log names are checked against the CLI — mutation: change one `--phase ARCH_REVIEW` in `review-workflow.md` to `--phase ARCH_REVIEWS` — killed by: `test_review_log_names_are_accepted_by_the_cli`.
- the description limit — mutation: description over 500 characters — killed by: `test_description_starts_use_when_and_fits`.

- Satisfies Spec AC: Scope's contract test; AC-6/AC-7 fixture precondition
- Decisions applied: eval-only behaviour testing (no assert on skill wording)
- **Test retention:** **Permanent**

Content rules:
- **`ARCH_RUBRIC.md`:** each "What review checks" item from the spec as one binary checkbox, with its scope in brackets (`[changed]` or `[whole]`), plus the Hard rules as checkboxes.
- **`ARCH_REVIEW_MANIFEST.md`** says how to work out the scopes:
  - "changed" is the changed elements, their relationships, and every decision whose bound-elements list includes one of them;
  - "whole" is the whole model;
  - how to check for cycles from the `export` relationships (each relationship counts for its endpoints and all their ancestors);
  - the shared-prefix check and the edge-node check;
  - what to quote from `check`;
  - grade against every `ARCH_RUBRIC.md` checkbox.

- [ ] **Step 1: write the RED test** `tests/scripts/test_defining_architecture_contract.py`:

```python
from __future__ import annotations

import importlib.util
import json
import re
import shutil

from arch_delta_support import ENGINE, require_node, run_tool, unique

PACKAGE = ENGINE / "skills" / "defining-architecture"
FILES = [
    "SKILL.md",
    "baseline-run.md",
    "ARCH_STANDARDS.md",
    "ARCH_REVIEW_MANIFEST.md",
    "ARCH_RUBRIC.md",
    "review-workflow.md",
    "pressure-test-evidence.md",
]
MODELLED = ENGINE / "tests" / "fixtures" / "defining-architecture" / "modelled"
CLI = ENGINE / "skills" / "shared" / "scripts" / "review-log.py"


def load_cli():
    spec = importlib.util.spec_from_file_location("review_log_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package_text() -> str:
    return "".join(path.read_text(encoding="utf-8") for path in sorted(PACKAGE.glob("*.md")))


def test_package_files_exist() -> None:
    missing = [name for name in FILES if not (PACKAGE / name).is_file()]
    assert missing == []


def test_description_starts_use_when_and_fits() -> None:
    text = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")
    front = text.split("---", 2)[1]
    fields = dict(line.split(":", 1) for line in front.strip().splitlines())
    assert fields["name"].strip() == "defining-architecture"
    description = fields["description"].strip().strip('"')
    assert description.startswith("Use when")
    assert len(description) <= 500


def test_review_log_names_are_accepted_by_the_cli() -> None:
    cli = load_cli()
    text = package_text()
    skills = set(re.findall(r"--skill[ ]+`?([a-z-]+)", text))
    phases = set(re.findall(r"--phase[ ]+`?([A-Z_]+)", text))
    assert "defining-architecture" in skills
    assert {"ARCH_REVIEW", "INDEPENDENT_AUDIT"} <= phases
    assert skills <= set(cli.SKILLS)
    assert phases <= set(cli.PHASES)


def test_modelled_fixture_exports(tmp_path) -> None:
    require_node()
    proc = run_tool("export", "--repo", MODELLED, "--model", "docs/architecture")
    assert proc.returncode == 0, proc.stderr
    ids = {element["id"] for element in json.loads(proc.stdout)["elements"]}
    assert {"shop.events", "shop.refunds", "shop.payments"} <= ids
    assert (MODELLED / "docs" / "architecture" / "architecture.md").is_file()
    assert (MODELLED / "docs" / "architecture" / "known-gap.json").is_file()


def test_modelled_fixture_check_shows_the_drift(tmp_path) -> None:
    require_node()
    repo = tmp_path / unique("modelled")
    shutil.copytree(MODELLED, repo)
    deps = repo / "deps" / "dependencies.json"
    proc = run_tool("check", "--repo", repo, "--model", "docs/architecture", "--deps", deps, "--format", "json")
    assert proc.returncode == 1, proc.stderr
    report = json.loads(proc.stdout)
    assert report["gap"]["new"] == [{"from": "shop.checkout", "to": "shop.inventory"}]
    assert report["gap"]["stale"] == []
    assert report["unmapped"] == ["shop.returns.flow"]
```

- [ ] **Step 2: run RED**

Run: `uv run pytest tests/scripts/test_defining_architecture_contract.py -q`
Expected: `test_package_files_exist` fails (`['ARCH_REVIEW_MANIFEST.md', 'ARCH_RUBRIC.md']` missing); the fixture tests pass, since Task 4 is in place.
If `report["gap"]["new"]` has a different shape from `[{"from", "to"}]`, check `report.mjs` `cleanPairs`, fix the assert to the real shape, and note it in the commit.

- [ ] **Step 3: write `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md`.**
- [ ] **Step 4: run GREEN and the full suite**

Run: `uv run pytest -q`
Expected: PASS for the whole suite.

- [ ] **Step 5: commit**

```bash
git add skills/defining-architecture/ARCH_REVIEW_MANIFEST.md skills/defining-architecture/ARCH_RUBRIC.md tests/scripts/test_defining_architecture_contract.py
git commit -m "feat(22): defining-architecture review manifest, rubric and contract test"
```

### Task 9: GREEN runs and loophole fixes (coordinator)

**Tier:** strong — coordinator-run eval.

**Files:** Modify `skills/defining-architecture/pressure-test-evidence.md`, plus whichever skill file a counter goes into.

**Callers that move with this task:** none.

**Reviewer looks at:** as Task 5; code review checks that every FAIL has a counter and a rerun.

- Satisfies Spec AC: AC-3 to AC-8
- Decisions applied: at most two GREEN rounds per scenario
- **Test retention:** **Permanent** (evidence)

- [ ] **Step 1: GREEN round 1.** Run scenarios A and B with the skill, using the Task 5 harness, and grade them.
- [ ] **Step 2: if any AC fails, add the counter.** Quote the failure verbatim in the evidence file, add one explicit counter to the right skill file (a rule or a Red-flags row; never a test on wording), and commit `fix(22): counter for <loophole>`.
- [ ] **Step 3: GREEN round 2,** only for a scenario that failed in round 1, in a fresh copy with a fresh agent. If it still fails, stop. Report the failing AC, the verbatim behaviour and the counter tried to the owner, and do not start a third round.
- [ ] **Step 4: record the results.** Add "GREEN — scenario A/B, round N" sections with grading tables and the counters each round added. Run `uv run pytest tests/scripts/test_defining_architecture_contract.py -q`. Expected: PASS.
- [ ] **Step 5: commit**

```bash
git add skills/defining-architecture
git commit -m "test(22): GREEN runs for defining-architecture"
```

---

## Plan end

1. Full suite: `uv run pytest -q`. Expected: PASS.
2. `resistance-engine:requesting-code-review` on `feat/architecture-and-releases..HEAD`.
3. `resistance-engine:survivability`: mutation lane `full`, on Task 1's items 1–3 and Task 8's items 1–3, run on a scratch copy. Chaos: one probe, `likec4` unavailable to `test_modelled_fixture_exports` (scratch engine copy without `node_modules`). The expected safe result is exit 2 with `error: likec4-missing:`, never a pass.
4. `resistance-engine:finishing-a-development-branch`: run record, merge `--no-ff` into `feat/architecture-and-releases` on the owner's choice.
