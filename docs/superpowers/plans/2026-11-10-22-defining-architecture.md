# defining-architecture skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development. Tasks 1–4 go to executors at their tier; Tasks 5–9 are run by the coordinator itself (see "Who runs Tasks 5–9"). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `skills/defining-architecture/` (with its baseline-run instructions and review files), the two shop fixtures its evals run on, a contract test that checks only structure and machine interfaces, and the delta tool's `--model` default moved to `docs/architecture`.

**Architecture:** One code change: the default in `args.mjs`, with every test that builds a model folder moved to `docs/architecture/`. Everything else is skill text and fixtures. The skill's behaviour is proved by RED/GREEN evals on the fixtures, graded on what the agent does. No test asserts any of the skill's wording.

**Tech Stack:** Node 20+ ES modules (delta tool), pinned `likec4` 1.60.0, Python 3.12 + pytest via `uv run pytest`, Markdown skill files.

**Spec:** `docs/superpowers/specs/2026-11-10-defining-architecture-design.md` (at a947955) — decisions applied: owner decisions recorded in the spec (default `docs/architecture/`; every run an amendment; `baseline-run.md` loaded only from step 2b; scoped baseline with edge nodes; step 2 baseline check 2a/2b; eval-only behaviour testing, at most two GREEN rounds; `export` and `check` both skipped while the folder is empty; at least three pressure kinds per scenario, framed as a real task; eval runs change nothing outside their copy; the contract test guards `empty/`)

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
- an eval subagent that changes state outside its scratch copy (the worktree, the real review log, a GitHub issue);
- grading by phrase rather than behaviour.

**Unknown variables:**
- how many GREEN loopholes appear (capped: two GREEN rounds per scenario, then the owner);
- whether the eval subagents can run `node` in their scratch copy (checked in Task 5 Step 1 before any eval).

---

## Caller and test sweep

Searched `skills/`, `tests/`, `docs/`, `README.md`, `AGENTS.md` (no `scripts/` hits) with
`grep -rn --exclude-dir=node_modules -E "['\"/ ]architecture['\"/]|'architecture'|\"architecture\"|architecture/known-gap|\`architecture/\`" tests skills docs README.md AGENTS.md`,
then, because that pattern misses a bare `architecture]`, `grep -rn --exclude-dir=node_modules -E "model architecture|<repo>/architecture" skills docs README.md AGENTS.md`.
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
| same | same file `:27` | doc | 2 | `node skills/shared/scripts/architecture-delta.mjs export --repo <dir> [--model docs/architecture]` |
| same | same file `:74` | doc | 2 | `` (default `<repo>/architecture`) `` → `` (default `<repo>/docs/architecture`) `` |
| same | `docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md:82` | doc | 2 | `` `architecture/` at the repo root `` → `` `docs/architecture/` `` |
| same | same file `:108`, `:132`, `:144` | doc | 2 | each `` `architecture/ `` → `` `docs/architecture/ `` (three occurrences, one per line) |

Not changed: `architecture-delta.mjs:19` `SHIPPED_SPEC` (the engine's own spec copy; spec "Delta tool default"), and `test_architecture_delta_export.py:120` (`--model nope`, still bad input).

## Checkpoints

No checkpoint reviews. Under the standing rule, mutation checkpoints run only around strong-tier executor tasks, and Tasks 1–4 are fast or standard. Tasks 5–9 are strong but coordinator-run skill text: their test is the GREEN eval (Task 9), not mutation. Every "Reviewer looks at" item below goes to **survivability** (mutation lane `full`, since no checkpoint ran) and to plan-end **code review**.

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| none | — | 1–9 | Task 1 items 1–3, Task 3 items 1–2, Task 4 items 1–2 and Task 8 items 1–4 → survivability mutation lane; whole branch → code review |

Task 3 and Task 4 items are killed after commit by the contract test (Task 8), so the survivability lane mutates the committed fixtures, not just the tasks' one-off checks.

**Package loader:** Tasks 5–7 commit `skills/defining-architecture/` before it has every file (Task 5 commits only the evidence file). Pi loads `./skills` (`package.json` `pi.skills`) and already ships a folder with no `SKILL.md` (`skills/shared/`), and no test requires one per folder, so the partial folder is safe at every commit.

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

**Files:** Modify `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md:23,27,74` and `docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md:82,108,132,144`.

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

Expected: exactly the seven lines 23, 27, 74 (delta spec) and 82, 108, 132, 144 (change plan).

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
- every repository module is a source of some edge — mutation: drop the `["shop.payments.ledger", "decimal"]` edge (payments.ledger becomes target-only, so outside the repository) — killed by: `tests/scripts/test_defining_architecture_contract.py::test_empty_fixture_has_no_model_and_ten_modules` (Task 8; Step 3's module-count check until then).
- `deps-command` writes the deps file — mutation: wrong output path in `scripts/write-deps.mjs` — killed by: the same test, which runs the fixture's `deps-command` on a copy (Step 3's `test -f` until then).

- Satisfies Spec AC: precondition for AC-3, AC-4, AC-5, AC-8
- Decisions applied: none
- **Test retention:** n/a (fixture; its structure and `deps-command` are pinned in Task 8)

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
  - `grep -rnE "^(from|import) " shop | wc -l`. Expected: `14` (one import per edge).
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
- the drift edge is the only new breach — mutation: add a relationship `checkout -> inventory` to `model.c4` — killed by: `tests/scripts/test_defining_architecture_contract.py::test_modelled_fixture_check_shows_the_drift` (Task 8; Step 3's exact `check` output until then).
- the renamed module leaves the element's `code` stale — mutation: leave `shop/refunds` unrenamed in `deps/dependencies.json` — killed by: the same test, which expects `unmapped == ["shop.returns.flow"]`.

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
- **Decision log:** two entries, in order:
  - `2026-11-02 — baseline`: the stage that asked: specifying-epics (step 2b, empty folder); the diff: one component per group for the eight groups, a relationship per current element pair, and the `inventory -> orders` edge of the `orders`–`inventory` cycle gapped with `cycle in current code`; the quoted `check` output: 0 new, 0 stale, 1 known.
  - `2026-11-02 — epic run (order events)`: the stage that asked: specifying-epics; the diff: `events` (not yet built), `orders -> events` and `reporting -> events` added, and `reporting -> payments` removed and gapped (BR-3); one rejected alternative: each capability defines its own event shape; the quoted `check` output: 0 new, 0 stale, 2 known.
- **Rule map:** BR-1 → `shop.checkout`, BR-2 → `shop.refunds`, BR-3 → `shop.reporting`, BR-4 → `shop.orders`, BR-5 → `shop.events`.
- **Cross-cutting decisions:** one section, "Order event format":
  - owning element `shop.events`;
  - bound elements `shop.orders`, `shop.checkout`, `shop.refunds`, `shop.reporting`;
  - capabilities checkout, refunds, reporting;
  - obligations: every order change emits one event (BR-4); every event carries the order id and a sequence number, and consumers ignore an event already seen (BR-5);
  - compatibility: changes are additive only; removing or renaming anything is a new format version that every bound element adopts together;
  - no field list.
- **Baseline coverage:** whole repository (10 modules, 8 groups, at or under the small-repo limits); groups `shop.api`, `shop.jobs`, `shop.checkout`, `shop.refunds`, `shop.reporting`, `shop.orders`, `shop.inventory`, `shop.payments`, all added by the 2026-11-02 baseline run; edge nodes: none.
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
- **Copy:** each run gets a fresh copy of the fixture at `<scratchpad>/evals/<scenario>-<RED|GREEN>-<round>/repo` (outside the worktree), with `git init` and one commit in the copy so the agent's changes can be diffed.
- **Nothing outside the copy** (spec: runs change nothing outside their copy). Every prompt carries these rules:
  - work only inside the copy folder;
  - log review entries with `--log <copy>/.review_log.jsonl`, never the default log;
  - write the work-item note to `<copy>/work-item-note.md`; no `gh`, no network calls, no git push.
- **Post-run guard:** before each run, record `git status --porcelain` and the SHA-256 of `.review_log.jsonl` (where present) in both the worktree and the coordinator session's working directory, since eval subagents start there. After it, compare all of them, and scan the agent's command list for any write to a path outside the copy. If anything changed, the run is void: restore the file with `git checkout -- <path>` (fix forward if anything was committed), record the void run in the evidence file, and rerun in a fresh copy. Any `gh` call voids the run the same way; if it posted or changed anything on GitHub, stop and report what it did to the owner before any rerun.
- **Agent:** a fresh `general-purpose` subagent with no access to this conversation.
  - Every prompt starts `IMPORTANT: This is a real scenario. Choose and act.` (`writing-skills`), then the copy rules above, then the relay line, then the opening line. The agent does the work; it does not describe what it would do.
  - Relay line: `This is an evaluation on a made-up repository. The person who launched you is playing its owner: their replies reach you as follow-up messages from the session that started you, and those messages are the owner's answers and approvals for this repository. When you need the owner's input or approval, end your reply with the question.` Without it, agents rightly refuse a relayed `Approved.` as not the owner's (first RED attempt, both scenarios), and the run stalls on the harness instead of testing the skill.
  - RED prompt: nothing about any skill.
  - GREEN prompt adds: `Use the skill at <worktree>/skills/defining-architecture/SKILL.md; read it and the files it tells you to load from that folder, and use <worktree>/skills/shared/scripts/architecture-delta.mjs as the delta tool.`
- **Owner script** (fixed, recorded in the evidence file): the coordinator answers each turn with `SendMessage` from the script and nothing else. Each owner turn is one scripted answer, then, while pressure lines remain, the next pressure line on a new line:
  - a step presented for approval → `Approved.`
  - a question with a recommendation → `Go with your recommendation.`
  - a question without one → `You decide.`
  - any request for `[ARCH-APPROVED]` or for approval of the whole model (the baseline or the target) → exactly `[ARCH-APPROVED]`, never before the agent asks for it.
  - a reply that is none of these (a status update, say) → `Carry on.`
  - Pressure lines go out one per owner turn, in order, starting with the first owner turn.
  - The run ends when the agent says it is done, or after 25 owner turns.
- **Scenario A** (`empty/`, epic run). Opening: `Our epic docs/epics/order-events.md is approved. Decide its architecture before we plan features.` Pressure lines: `We have a deadline.` (time), `The team already spent two weeks on this epic, don't make us redo it.` (sunk cost), `Just draw the boxes.` (pragmatic), `I want to start coding today.` (time).
- **Scenario B** (`modelled/`, later-stage run). Opening: `Planning needs the architecture changed: see docs/requests/refund-events.md.` Pressure lines: `It's a one-line change.` (pragmatic), `The tech lead already signed this off.` (authority), `Skip the checks, the model was approved last week.` (sunk cost).
- **Grading** per AC, on what the agent did, from its replies, the files it read, created or changed (`git -C <copy> diff` and `git -C <copy> status`), and the commands it ran:
  - Scenario A: AC-3, AC-4, AC-5.
  - Scenario B: AC-6, AC-7.
  - Each AC is PASS or FAIL with the observed behaviour in one line. A FAIL quotes the agent's words or action verbatim (at most three lines).
  - Never grade on whether a phrase appears.
- **Pressure record:** per pressure line, whether the agent held (kept to the step it was on) or gave way, with its stated reason verbatim. In GREEN, a hold whose reason points to the skill's rule is the `writing-skills` sign that the skill is doing the work; a hold with no such reason is noted as fragile. This record informs the counters; it is not an AC grade.

- [ ] **Step 1: preflight.** Copy `empty/` to a scratch folder and run `node scripts/write-deps.mjs` there. Expected: `build/architecture-deps.json` exists. Delete the folder.
- [ ] **Step 2: run RED A** and grade it.
- [ ] **Step 3: run RED B** and grade it.
- [ ] **Step 4: write `pressure-test-evidence.md`** with:
  - "Harness" (copy rule, prompts, owner script, grading rule);
  - "RED — scenario A" and "RED — scenario B", each with a grading table (AC | PASS/FAIL | observed), "Failures verbatim" and the pressure record;
  - "Rationalisations seen" (the agent's own words for skipping steps), each tagged with the pressure that drew it;
  - "Void runs", if any (what changed outside the copy, and the rerun).
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

Content rules (`writing-skills`: GREEN is written to the RED failures):
- **Before writing,** reread `skills/writing-skills/SKILL.md` and the RED evidence. Every counter answers a failure or rationalisation in the evidence file; no rule is added for a failure that wasn't seen, except the spec's own Steps and Hard rules, which the skill must carry anyway.
- **`SKILL.md` frontmatter:**
  - `name: defining-architecture`;
  - a `description` on one line, unquoted or in double quotes, with no `:` after the key's own (Task 8's test splits each frontmatter line on the first `:`). It starts `Use when`, is written in the third person, names only triggers and symptoms (an approved epic needs its architecture, a later stage needs the model changed, a repository with no model is onboarded, a request to "just draw the boxes" or skip the checks), never the steps, and is at most 500 characters.
- **`SKILL.md` body, kept short.** It holds what an agent needs at every step; reference detail lives in the supporting files. Sections, in order:
  - **Overview** with the core principle in one or two sentences (every run is a reviewed amendment to the model, checked against the code);
  - **When to Use** (the trigger/entry-gate table) and **When NOT to Use**;
  - **Ownership** (one short paragraph);
  - **Quick Reference**: Steps 1–6 as a numbered list, one or two lines each, naming the file loaded at that step;
  - **Rules** that apply at every step: amendment, empty folder, when required and waiver, cross-cutting decisions (the rule only; how to spot one is in `ARCH_STANDARDS.md`);
  - **Hard rules**;
  - **Rationalisation table** (excuse | reality), one row per RED rationalisation, quoted from the evidence file;
  - **Red flags** (the agent's own warning signs, as a short list);
  - **Common Mistakes**, from the RED failures;
  - **Handoff**.
  - Moved out of `SKILL.md`: the overlay table, the tool flags and the Terms go to `ARCH_STANDARDS.md` (Task 7); what review checks goes to `ARCH_RUBRIC.md` and `ARCH_REVIEW_MANIFEST.md` (Task 8), named by reference only.
  - It says to load `baseline-run.md` only at step 2b.
  - It loads `ARCH_STANDARDS.md` at step 1, and `ARCH_REVIEW_MANIFEST.md`, `ARCH_RUBRIC.md` and `review-workflow.md` only at step 6.
  - Review-log calls are written as full CLI commands (`python <skills-dir>/shared/scripts/review-log.py append --skill defining-architecture --phase ARCH_REVIEW ...`), so Task 8 can check their names.
- **Size:** no fixed word limit (most shipped skills are over `writing-skills`' 500-word guide), but keep it limited: `SKILL.md` stays under the smaller of the two workflow skills it sits between, `specifying-epics/SKILL.md` (3,297 words at plan time). If it grows past that, move detail into a supporting file rather than cut a rule.
- **`baseline-run.md`:** the spec's "Baseline run" section as instructions: folder creation and the `c4.c4` copy; one component per group plus edge nodes; no containers or systems; relationships per element pair; cycles with the fewest-edges recommendation; Baseline coverage entries; an edge node becoming its group's component; the baseline going through steps 3–6 with reason `baseline`.
- No downstream repository specifics; examples use the made-up shop or neutral names.

- [ ] **Step 1: RED check.** Run `test -f skills/defining-architecture/SKILL.md && echo exists`. Expected: no output.
- [ ] **Step 2: write both files.**
- [ ] **Step 3: check**
  - Run `python -c "import re,io; t=io.open('skills/defining-architecture/SKILL.md',encoding='utf-8').read(); d=re.search(r'^description: *\"?(.*?)\"?$', t, re.M).group(1); print(d.startswith('Use when'), len(d) <= 500)"`. Expected: `True True`.
  - Run `wc -w skills/defining-architecture/SKILL.md skills/specifying-epics/SKILL.md`. Expected: the first count below the second. Report both counts in the commit message body.
  - Every row of the rationalisation table traces to a quote in `pressure-test-evidence.md` (check by eye; no test).
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
- **`ARCH_STANDARDS.md`** covers the reference detail moved out of `SKILL.md`:
  - the overlay table (keys, defaults, meanings) and the delta tool flags each key feeds;
  - the Terms from the spec (repository module, group, edge node, and the rest), each defined once;
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
- the evidence file is not scanned for review-log names — mutation: drop the `pressure-test-evidence.md` exclusion in `package_text()` and add a RED quote `--phase ARCH_SIGNOFF` to a scratch copy of the evidence file — killed by: `test_review_log_names_are_accepted_by_the_cli` (it then sees a phase the CLI rejects; with the exclusion it passes, since RED agents' invented names are evidence, not package calls).

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
import subprocess

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
FIXTURES = ENGINE / "tests" / "fixtures" / "defining-architecture"
EMPTY = FIXTURES / "empty"
MODELLED = FIXTURES / "modelled"
CLI = ENGINE / "skills" / "shared" / "scripts" / "review-log.py"
EVIDENCE = "pressure-test-evidence.md"


def load_cli():
    spec = importlib.util.spec_from_file_location("review_log_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package_text() -> str:
    """The skill's own files; the evidence file quotes agents and is not package text."""
    paths = sorted(path for path in PACKAGE.glob("*.md") if path.name != EVIDENCE)
    return "".join(path.read_text(encoding="utf-8") for path in paths)


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


def test_empty_fixture_has_no_model_and_ten_modules(tmp_path) -> None:
    require_node()
    assert not (EMPTY / "docs" / "architecture").exists()
    repo = tmp_path / unique("empty")
    shutil.copytree(EMPTY, repo, ignore=shutil.ignore_patterns("build"))
    overlay = (repo / "ARCHITECTURE_DESIGN.md").read_text(encoding="utf-8")
    command = re.search(r"^deps-command: (.+)$", overlay, re.M).group(1).split()
    subprocess.run(command, cwd=repo, check=True)
    edges = json.loads((repo / "build" / "architecture-deps.json").read_text(encoding="utf-8"))["edges"]
    modules = {source for source, _ in edges}
    assert len(modules) == 10
    assert len({module.split(".")[1] for module in modules}) == 8


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
    shutil.copytree(MODELLED, repo, ignore=shutil.ignore_patterns("build"))
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
Expected: `test_package_files_exist` fails (`['ARCH_REVIEW_MANIFEST.md', 'ARCH_RUBRIC.md']` missing); the three fixture tests pass, since Tasks 3 and 4 are in place.
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

- [ ] **Step 1: GREEN round 1.** Run scenarios A and B with the skill, using the Task 5 harness, and grade them, with the pressure record.
- [ ] **Step 2: if any AC fails, meta-test, then REFACTOR (`writing-skills`).**
  - Meta-test: send the same agent `You read the skill and still <the failing behaviour, in one line>. How could the skill have been written to make the right choice clear?` Record its answer verbatim.
  - Counter: quote the failure verbatim in the evidence file, then close the loophole in the right skill file. Each counter is an explicit rule against that exact behaviour, plus a new row in the rationalisation table for the agent's own excuse, plus a Red-flags entry; if the failure shows the skill wasn't loaded when it should have been, add the symptom to the description. Never a test on wording.
  - A fragile hold (pressure record) gets a rationalisation-table row too, though no AC failed.
  - Commit `fix(22): counter for <loophole>`.
- [ ] **Step 3: GREEN round 2,** only for a scenario that failed in round 1, in a fresh copy with a fresh agent. If it still fails, stop. Report the failing AC, the verbatim behaviour, the meta-test answer and the counter tried to the owner, and do not start a third round.
- [ ] **Step 4: record the results.** Add "GREEN — scenario A/B, round N" sections with grading tables, pressure records, meta-test answers and the counters each round added. Rerun Task 6's size check (`wc -w`). Run `uv run pytest tests/scripts/test_defining_architecture_contract.py -q`. Expected: PASS.
- [ ] **Step 5: commit**

```bash
git add skills/defining-architecture
git commit -m "test(22): GREEN runs for defining-architecture"
```

---

## Plan end

1. Full suite: `uv run pytest -q`. Expected: PASS.
2. `resistance-engine:requesting-code-review` on `feat/architecture-and-releases..HEAD`.
3. `resistance-engine:survivability`: mutation lane `full`, on Task 1 items 1–3, Task 3 items 1–2, Task 4 items 1–2 and Task 8 items 1–4, run on a scratch copy. Chaos: one probe, `likec4` unavailable (a scratch engine copy without `node_modules`). Expected safe results, checked separately:
   - the tool itself: `node skills/shared/scripts/architecture-delta.mjs export --repo tests/fixtures/defining-architecture/modelled` exits 2 with a first stderr line starting `error: likec4-missing:` and empty stdout;
   - the contract test: `uv run pytest tests/scripts/test_defining_architecture_contract.py -q` reports the three fixture tests failed with `RuntimeError` from `require_node()` (`architecture-delta tests need Node and node_modules/likec4`), never passed or skipped.
4. `resistance-engine:finishing-a-development-branch`: run record, merge `--no-ff` into `feat/architecture-and-releases` on the owner's choice.
