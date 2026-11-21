# Architecture Records `cycles` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `architecture-records.mjs cycles` proposes, for each strongly connected group of siblings, the set of import relationships to leave out that has the fewest relationships, then the fewest distinct module edges, then the first sorted list of pairs, found by exact search up to 20 candidate pairs.

**Architecture:** This repository has no architecture model. `match.mjs` exports the module-to-element mapper `compare` already uses (and its ancestor helper); a new pure module `architecture-records/cycles.mjs` builds the sibling levels, the strongly connected groups and the exact search; the tool's `args.mjs` and entry script gain the `cycles` command. Reads only.

**Tech Stack:** Node ESM (no new dependency), pytest via `uv run`.

**Spec:** `docs/superpowers/specs/2026-11-21-defining-architecture-records-design.md` ("The helper tool" intro and "Delta modules the helper reuses"; "`cycles`"; the Availability row; AC-10 to AC-14) — decisions applied: none. Plan 2b of the four plans (the spec's plan 2, split into 2a and 2b by the sizing rule).

**Open decisions:** none

**Size:** 3 tasks, 1 entry path (`architecture-records.mjs cycles`), lines reported in the self-review commit (reported, not a target)

**Trust boundary:** unchanged. `cycles` reads the model and the dependency file through the delta loader and `check`'s readers and prints cleaned ids; it writes nothing.

### Risk & Confidence Assessment

**Confidence:** 90% — the rules are fully stated; the exact search is small and bounded.

**Complexity Risk:** Medium — driving variable: the search's order of preference (relationships, then distinct module edges, then the pair list) and the level a relationship belongs to.

**Environmental Risk:** Low — the search is bounded at 2^20 subsets, each checked with bit masks.

**Main failure modes:** module edges summed instead of counted once (`test_distinct_module_edges_decide_a_tie`); a relationship counted at a level other than its nearest common ancestor's (`test_cycle_between_children_is_found_at_their_level`); the 20-pair limit off by one (`test_twenty_pairs_are_searched_and_twenty_one_are_too_large`).

**Unknown variables:**
- The time of a full 2^20 search in Node on the test machine; measured in the dry run (the 20-pair test must stay well under the default 60 s deadline).

---

## Caller and test sweep

Searched: `skills/`, `tests/` with `grep -rn "mapModule\|ancestorsOrSelf\|unknown subcommand" skills/shared/scripts tests/scripts`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `compare`'s `mapModule` closure becomes `moduleMapper(elements, separator)` | `match.mjs` `compare` | caller | 1 | `const mapModule = moduleMapper(model.elements, separator);` |
| `ancestorsOrSelf` exported | `match.mjs` `compare` (two uses) | caller | 1 | none: same name |
| the records tool's subcommand list gains `cycles` | `tests/scripts/test_architecture_records_args.py::test_usage_errors[subcommand]` | assert | 3 | `"unknown subcommand cycles-ish; use change or cycles"` |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | no mutation reviewer (no strong-tier task, owner's rule); the code review and survivability check every item |

---

### Task 1: `match.mjs` exports the module mapper

**Tier:** fast — a closure lifted out, complete code.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/match.mjs`
- Test: `tests/scripts/test_architecture_delta_match.py` (append)

**Callers that move with this task:** `match.mjs` `compare` (sweep row 1).

**Reviewer looks at:**
- the longest prefix wins, at the separator only — mutation: return the first prefix found from the left — killed by: `test_module_mapper_longest_prefix_at_the_separator`

**Pinned by:** `tests/scripts/test_architecture_delta_match.py::test_longest_prefix_wins_and_separator_counts` and `::test_other_separator` (compare's mapping through the moved closure).

- Satisfies Spec AC: none directly ("Delta modules the helper reuses")
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append to `tests/scripts/test_architecture_delta_match.py`:

```python
def test_module_mapper_longest_prefix_at_the_separator() -> None:
    code = (
        f"import {{ moduleMapper, ancestorsOrSelf }} from {json.dumps(lib_url('match.mjs'))};\n"
        "const map = moduleMapper([{ id: 'o', code: ['shop.orders'] }, { id: 'o.api', code: ['shop.orders.api'] }], '.');\n"
        "process.stdout.write(JSON.stringify([map('shop.orders.api.v1'), map('shop.orders.x'), map('shop.ordersx'),"
        " map('shop.orders'), map('other'), ancestorsOrSelf('a.b.c')]));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == ["o.api", "o", None, "o", None, ["a", "a.b", "a.b.c"]]
```

Add `json`, `lib_url` and `run_module` to that file's imports if they are not there.

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_match.py -k module_mapper`
Expected: 1 failed (Node: "does not provide an export named 'moduleMapper'").

- [ ] **Step 3: GREEN.** In `skills/shared/scripts/architecture-delta/match.mjs`, replace

```js
function ancestorsOrSelf(id) {
```

with

```js
export function ancestorsOrSelf(id) {
```

and replace

```js
  const byPrefix = new Map();
  for (const element of model.elements) {
    for (const prefix of element.code) byPrefix.set(prefix, element.id); // loadModel refuses duplicate prefixes
  }
  // Longest matching prefix: the module itself, then each cut just before a separator, right to left.
  const mapModule = (module) => {
    let hit = byPrefix.get(module);
    let end = module.length;
    while (hit === undefined && end > 0) {
      end = module.lastIndexOf(separator, end - 1);
      if (end < 0) break;
      hit = byPrefix.get(module.slice(0, end));
    }
    return hit ?? null;
  };
```

with

```js
  const mapModule = moduleMapper(model.elements, separator);
```

then insert above `export function compare(`:

```js
// A function from a module name to the id of the element whose `code` is the longest prefix of it at the separator,
// or null when none is.
export function moduleMapper(elements, separator) {
  const byPrefix = new Map();
  for (const element of elements) {
    for (const prefix of element.code) byPrefix.set(prefix, element.id); // loadModel refuses duplicate prefixes
  }
  // Longest matching prefix: the module itself, then each cut just before a separator, right to left.
  return (module) => {
    let hit = byPrefix.get(module);
    let end = module.length;
    while (hit === undefined && end > 0) {
      end = module.lastIndexOf(separator, end - 1);
      if (end < 0) break;
      hit = byPrefix.get(module.slice(0, end));
    }
    return hit ?? null;
  };
}

```

- [ ] **Step 4: run GREEN and the delta tests.**

Run: `uv run pytest -q tests/scripts/ -k architecture_delta`
Expected: all pass.

- [ ] **Step 5: commit.**

```bash
git add skills/shared/scripts/architecture-delta/match.mjs tests/scripts/test_architecture_delta_match.py
git commit -m "refactor(#31): match.mjs exports its module mapper and ancestor helper"
```

---

### Task 2: the cycle search

**Tier:** standard — an exact search with an order of preference; complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-records/cycles.mjs`
- Test: `tests/scripts/test_architecture_records_cycles.py`

**Callers that move with this task:** none.

**Reviewer looks at:**
- fewest relationships first — mutation: compare distinct module edges before relationships — killed by: `test_fewest_relationships_come_first`
- module edges counted once — mutation: sum `c.edges.size` over the chosen pairs instead of the union — killed by: `test_distinct_module_edges_decide_a_tie`
- the pair list breaks the last tie — mutation: prefer the later list — killed by: `test_tie_on_module_edges_goes_to_the_first_pair_list` (AC-10)
- a relationship counts at its nearest common ancestor's level only — mutation: give every relationship a pair at the top level too — killed by: `test_cycle_between_children_is_found_at_their_level`
- the limit is 20 candidate pairs — mutation: `> SEARCH_LIMIT` to `>= SEARCH_LIMIT` — killed by: `test_twenty_pairs_are_searched_and_twenty_one_are_too_large`
- group order — mutation: drop the sort of `groups` — killed by: `test_groups_in_level_order_then_by_siblings`

- Satisfies Spec AC: AC-10, AC-11, AC-12
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_records_cycles.py`:

```python
"""The cycle search (spec 2026-11-21-defining-architecture-records-design.md, "`cycles`")."""

from __future__ import annotations

from arch_delta_support import RECORDS_LIB, call, require_node

require_node()


def model(ids: list, rels: list) -> dict:
    return {"elements": [{"id": id_, "code": [id_]} for id_ in ids], "relationships": [{"from": f, "to": t} for f, t in rels]}


def cycles(ids: list, rels: list, edges: list) -> dict:
    out = call("cycles.mjs", "findCycles", model(ids, rels), edges, ".", lib=RECORDS_LIB)
    assert out["ok"], out
    return out["value"]


def leave(from_: str, to: str, edges: int) -> dict:
    return {"from": from_, "to": to, "module_edges": edges}


def test_tie_on_module_edges_goes_to_the_first_pair_list() -> None:  # AC-10
    value = cycles(
        ["a", "b", "c", "x", "x.d", "x.e"],
        [("a", "b"), ("b", "c"), ("c", "a"), ("x.d", "x.e"), ("x.e", "x.d")],
        [["a.1", "b.1"], ["a.2", "b.1"], ["a.3", "b.1"], ["b.1", "c.1"], ["c.1", "a.1"],
         ["x.d.1", "x.e.1"], ["x.e.1", "x.d.1"]],
    )
    assert value == {
        "groups": [
            {"parent": None, "siblings": ["a", "b", "c"], "leave_out": [leave("b", "c", 1)], "too_large": None},
            {"parent": "x", "siblings": ["x.d", "x.e"], "leave_out": [leave("x.d", "x.e", 1)], "too_large": None},
        ],
        "summary": {"relationships": 2, "groups": 2, "too_large": 0},
    }


def test_cycle_between_children_is_found_at_their_level() -> None:  # AC-11
    value = cycles(
        ["A", "A.k", "B", "P", "P.q", "P.r", "S"],
        [("A.k", "B"), ("B", "A"), ("P.q", "P.r"), ("P.r", "P.q")],
        [["A.k.1", "B.1"], ["A.k.2", "B.1"], ["B.1", "A.1"], ["P.q.1", "P.r.1"], ["P.r.1", "P.q.1"]],
    )
    assert [(g["parent"], g["siblings"]) for g in value["groups"]] == [(None, ["A", "B"]), ("P", ["P.q", "P.r"])]
    assert value["groups"][0]["leave_out"] == [leave("B", "A", 1)]


def test_fewest_relationships_come_first() -> None:
    value = cycles(
        ["a", "a.x", "a.y", "b"],
        [("a.x", "b"), ("a.y", "b"), ("b", "a")],
        [["a.x.1", "b.1"], ["a.y.1", "b.1"], *[["b.1", f"a.{n}"] for n in range(5)]],
    )
    assert value["groups"][0]["leave_out"] == [leave("b", "a", 5)]


def test_distinct_module_edges_decide_a_tie() -> None:
    # Leaving out o -> i (two relationships that share one module edge) or i -> o with i -> z (two relationships, two
    # module edges) both leave out two relationships; counted once, o -> i has fewer module edges.
    value = cycles(
        ["o", "o.x", "i", "z"],
        [("o", "i"), ("o.x", "i"), ("i", "o"), ("i", "z"), ("z", "o")],
        [["o.x.1", "i.1"], ["i.1", "o.1"], ["i.1", "z.1"], ["z.1", "o.1"]],
    )
    assert value["groups"][0]["leave_out"] == [leave("o", "i", 1), leave("o.x", "i", 1)]


def test_groups_in_level_order_then_by_siblings() -> None:
    value = cycles(
        ["c", "d", "a", "b", "p", "p.m", "p.n"],
        [("c", "d"), ("d", "c"), ("a", "b"), ("b", "a"), ("p.m", "p.n"), ("p.n", "p.m")],
        [],
    )
    assert [g["siblings"] for g in value["groups"]] == [["a", "b"], ["c", "d"], ["p.m", "p.n"]]
    assert value["summary"] == {"relationships": 3, "groups": 3, "too_large": 0}


def complete(n: int) -> list:
    nodes = [f"n{i}" for i in range(1, n + 1)]
    return [(f, t) for f in nodes for t in nodes if f != t]


def test_twenty_pairs_are_searched_and_twenty_one_are_too_large() -> None:  # AC-12
    nodes = [f"n{i}" for i in range(1, 7)]
    twenty = cycles(nodes[:5], complete(5), [])
    [group] = twenty["groups"]
    assert group["too_large"] is None
    assert group["leave_out"] == [leave(f, t, 0) for f, t in complete(5) if f < t]
    twenty_one = [pair for pair in complete(5) if pair != ("n2", "n1")] + [("n5", "n6"), ("n6", "n1")]
    value = cycles(nodes, twenty_one, [])
    assert value == {"groups": [{"parent": None, "siblings": nodes, "leave_out": [], "too_large": 21}],
                     "summary": {"relationships": 0, "groups": 1, "too_large": 1}}


def test_no_cycle_gives_no_group() -> None:  # AC-14
    assert cycles(["a", "b"], [("a", "b")], [["a.1", "b.1"]]) == {
        "groups": [], "summary": {"relationships": 0, "groups": 0, "too_large": 0}}


def test_relationship_into_its_own_child_gives_no_pair() -> None:
    assert cycles(["a", "a.x"], [("a", "a.x"), ("a.x", "a")], [])["groups"] == []
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_cycles.py`
Expected: 8 failed (the module does not exist).

- [ ] **Step 3: GREEN.** Create `skills/shared/scripts/architecture-records/cycles.mjs`:

```js
// Proposes the relationships a baseline leaves out of each cycle (spec 2026-11-21, "`cycles`"). Pure: reads and writes
// nothing.
import { clean } from '../architecture-delta/errors.mjs';
import { cmp } from '../architecture-delta/report.mjs';
import { ancestorsOrSelf, moduleMapper } from '../architecture-delta/match.mjs';

export const SEARCH_LIMIT = 20;

const key = (from, to) => `${from}\u0000${to}`;
const byPair = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to);

// Lists compared item by item; a list that is a prefix of another comes first.
function cmpLists(x, y, cmpItem) {
  for (let i = 0; i < Math.min(x.length, y.length); i += 1) {
    const c = cmpItem(x[i], y[i]);
    if (c !== 0) return c;
  }
  return x.length - y.length;
}

// The sibling pair a relationship gives: the children of the nearest common ancestor of its ends (the top level when
// they have none) that hold the ends. Null when one end is inside the other.
function siblingPair(from, to) {
  const a = ancestorsOrSelf(from);
  const b = ancestorsOrSelf(to);
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i += 1;
  if (i === a.length || i === b.length) return null;
  return { parent: i === 0 ? null : a[i - 1], from: a[i], to: b[i] };
}

// Strongly connected groups of two or more siblings (Tarjan), each sorted.
function strongGroups(arcs) {
  const out = new Map();
  for (const arc of arcs) {
    if (!out.has(arc.from)) out.set(arc.from, []);
    if (!out.has(arc.to)) out.set(arc.to, []);
    out.get(arc.from).push(arc.to);
  }
  const index = new Map();
  const low = new Map();
  const stack = [];
  const onStack = new Set();
  const groups = [];
  let next = 0;
  const visit = (v) => {
    index.set(v, next);
    low.set(v, next);
    next += 1;
    stack.push(v);
    onStack.add(v);
    for (const w of out.get(v)) {
      if (!index.has(w)) {
        visit(w);
        low.set(v, Math.min(low.get(v), low.get(w)));
      } else if (onStack.has(w)) {
        low.set(v, Math.min(low.get(v), index.get(w)));
      }
    }
    if (low.get(v) === index.get(v)) {
      const group = [];
      let w;
      do {
        w = stack.pop();
        onStack.delete(w);
        group.push(w);
      } while (w !== v);
      if (group.length > 1) groups.push(group.sort(cmp));
    }
  };
  for (const v of [...out.keys()].sort(cmp)) if (!index.has(v)) visit(v);
  return groups;
}

// Whether the arcs not in `mask` leave the n nodes with no cycle (nodes and arcs as small integers, n <= 20).
function acyclicWithout(n, arcs, mask) {
  const into = new Array(n).fill(0);
  for (let i = 0; i < arcs.length; i += 1) if ((mask & (1 << i)) === 0) into[arcs[i][1]] |= 1 << arcs[i][0];
  let remaining = (1 << n) - 1;
  let progress = true;
  while (remaining !== 0 && progress) {
    progress = false;
    for (let v = 0; v < n; v += 1) {
      if ((remaining & (1 << v)) !== 0 && (into[v] & remaining) === 0) {
        remaining &= ~(1 << v);
        progress = true;
      }
    }
  }
  return remaining === 0;
}

// The best set of candidate pairs to leave out: fewest relationships, then fewest distinct module edges, then the
// first sorted list of pairs. `candidates` are sorted by pair; each has `rels` (relationships) and `edges` (a Set).
function bestLeaveOut(siblings, candidates, tick) {
  const position = new Map(siblings.map((id, i) => [id, i]));
  const arcs = candidates.map((c) => [position.get(c.from), position.get(c.to)]);
  let best = null;
  for (let mask = 0; mask < 2 ** candidates.length; mask += 1) {
    if ((mask & 4095) === 0) tick();
    let rels = 0;
    for (let i = 0; i < candidates.length; i += 1) if ((mask & (1 << i)) !== 0) rels += candidates[i].rels.length;
    if (best !== null && rels > best.rels) continue;
    if (!acyclicWithout(siblings.length, arcs, mask)) continue;
    const chosen = candidates.filter((_, i) => (mask & (1 << i)) !== 0);
    const edges = new Set();
    for (const c of chosen) for (const e of c.edges) edges.add(e);
    const found = { rels, edges: edges.size, chosen };
    const order = best === null ? -1
      : (found.rels - best.rels) || (found.edges - best.edges) || cmpLists(found.chosen, best.chosen, byPair);
    if (order < 0) best = found;
  }
  return best.chosen;
}

// `model` holds `elements` (id, code) and import `relationships` (from, to); `edges` are dependency-file edges.
export function findCycles(model, edges, separator, tick = () => {}) {
  const rels = new Map();
  for (const r of model.relationships) {
    if (!rels.has(key(r.from, r.to))) rels.set(key(r.from, r.to), { from: r.from, to: r.to, edges: new Set() });
  }
  // A dependency edge counts for every relationship whose source holds its source's element and whose target holds
  // its target's.
  const mapModule = moduleMapper(model.elements, separator);
  edges.forEach(([from, to], index) => {
    if (index > 0 && index % 10000 === 0) tick();
    const source = mapModule(from);
    const target = mapModule(to);
    if (source === null || target === null) return;
    for (const a of ancestorsOrSelf(source)) for (const b of ancestorsOrSelf(target)) rels.get(key(a, b))?.edges.add(index);
  });
  // The candidate pairs of each level: parent -> sibling pair -> the relationships that give it.
  const levels = new Map();
  for (const rel of rels.values()) {
    const pair = siblingPair(rel.from, rel.to);
    if (pair === null) continue;
    const level = JSON.stringify(pair.parent);
    if (!levels.has(level)) levels.set(level, { parent: pair.parent, arcs: new Map() });
    const arcs = levels.get(level).arcs;
    if (!arcs.has(key(pair.from, pair.to))) arcs.set(key(pair.from, pair.to), { from: pair.from, to: pair.to, rels: [], edges: new Set() });
    const arc = arcs.get(key(pair.from, pair.to));
    arc.rels.push(rel);
    for (const e of rel.edges) arc.edges.add(e);
  }
  const groups = [];
  for (const { parent, arcs } of levels.values()) {
    for (const siblings of strongGroups([...arcs.values()])) {
      tick();
      const inside = new Set(siblings);
      const candidates = [...arcs.values()].filter((a) => inside.has(a.from) && inside.has(a.to)).sort(byPair);
      const tooLarge = candidates.length > SEARCH_LIMIT;
      const chosen = tooLarge ? [] : bestLeaveOut(siblings, candidates, tick);
      const leaveOut = chosen.flatMap((c) => c.rels).sort(byPair)
        .map((r) => ({ from: clean(r.from), to: clean(r.to), module_edges: r.edges.size }));
      groups.push({ parent, siblings, leave_out: leaveOut, too_large: tooLarge ? candidates.length : null });
    }
  }
  const depth = (parent) => (parent === null ? 0 : parent.split('.').length);
  groups.sort((x, y) => depth(x.parent) - depth(y.parent) || cmp(x.parent ?? '', y.parent ?? '')
    || cmpLists(x.siblings, y.siblings, cmp));
  return {
    groups: groups.map((g) => ({ ...g, parent: g.parent === null ? null : clean(g.parent), siblings: g.siblings.map(clean) })),
    summary: {
      relationships: groups.reduce((n, g) => n + g.leave_out.length, 0),
      groups: groups.length,
      too_large: groups.filter((g) => g.too_large !== null).length,
    },
  };
}

export function cyclesText(result) {
  const lines = [];
  for (const group of result.groups) {
    lines.push(`group ${group.parent ?? 'top level'}: ${group.siblings.join(', ')}`);
    if (group.too_large !== null) lines.push(`too large: ${group.too_large} candidate pairs`);
    for (const r of group.leave_out) lines.push(`leave out ${r.from} -> ${r.to} (${r.module_edges} module edges)`);
  }
  const s = result.summary;
  lines.push(`${s.relationships} relationships to leave out in ${s.groups} groups, ${s.too_large} too large`);
  return `${lines.join('\n')}\n`;
}
```

- [ ] **Step 4: run GREEN.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_cycles.py --durations=3`
Expected: 8 passed; the 20-pair test well under 60 s (record its time in the dry run).

- [ ] **Step 5: commit.**

```bash
git add skills/shared/scripts/architecture-records/cycles.mjs tests/scripts/test_architecture_records_cycles.py
git commit -m "feat(#31): the cycle search - fewest relationships, then distinct module edges, then the first pair list"
```

---

### Task 3: the `cycles` command

**Tier:** standard — wiring and flags; complete code given.

**Files:**
- Modify: `skills/shared/scripts/architecture-records/args.mjs`
- Modify: `skills/shared/scripts/architecture-records.mjs`
- Test: `tests/scripts/test_architecture_records_cycles_command.py`; `tests/scripts/test_architecture_records_args.py` (one row)

**Callers that move with this task:** `test_usage_errors[subcommand]` (sweep row 3).

**Reviewer looks at:**
- `--format json` prints the result object — mutation: always print text — killed by: `test_cycles_command_text_and_json`
- `--format` is checked — mutation: drop the format check — killed by: `test_cycles_usage_errors[format]`

- Satisfies Spec AC: AC-10 (the output form), AC-13, AC-14
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** In `tests/scripts/test_architecture_records_args.py`, replace

```python
    (["cycles-ish"], "unknown subcommand cycles-ish; use change"),
```

with

```python
    (["cycles-ish"], "unknown subcommand cycles-ish; use change or cycles"),
```

and append:

```python
def test_cycles_defaults() -> None:
    out = parse("cycles", "--repo", ".", "--deps", "d.json")
    assert out == {"ok": True, "value": {"command": "cycles", "repo": ".", "model": "docs/architecture", "deps": "d.json",
                                         "separator": ".", "format": "text", "timeout": 60}}


@pytest.mark.parametrize(("argv", "detail"), [
    (["cycles", "--repo", ".", "--deps", "d.json", "--format", "xml"], "--format must be text or json"),
    (["cycles", "--repo", "."], "--deps is required"),
    (["cycles", "--repo", ".", "--deps", "d.json", "--compare"], "unknown flag for cycles: --compare"),
], ids=["format", "deps", "switch"])
def test_cycles_usage_errors(argv: list, detail: str) -> None:
    out = parse(*argv)
    assert (out["ok"], out["token"], out["details"]) == (False, "usage", [detail])
```

Create `tests/scripts/test_architecture_records_cycles_command.py`:

```python
"""The architecture records tool, `cycles` (spec 2026-11-21-defining-architecture-records-design.md, "`cycles`")."""

from __future__ import annotations

import json

from arch_delta_support import RECORDS_SCRIPT, SHOP_MODEL, error_lines, make_repo, require_node, run_tool, write_json

require_node()


def block(name: str, kind: str, code: str, inner: str = "") -> str:
    return f"  {name} = {kind} '{name}' {{\n    metadata {{\n      code '{code}'\n    }}\n{inner}  }}\n"


CYCLE_MODEL = (
    "model {\n"
    + block("a", "component", "a") + block("b", "component", "b") + block("c", "component", "c")
    + block("x", "container", "x", "    d = component 'd' {\n      metadata {\n        code 'x.d'\n      }\n    }\n"
            "    e = component 'e' {\n      metadata {\n        code 'x.e'\n      }\n    }\n    d -> e\n    e -> d\n")
    + "  a -> b\n  b -> c\n  c -> a\n}\n"
)
EDGES = [["a.1", "b.1"], ["a.2", "b.1"], ["a.3", "b.1"], ["b.1", "c.1"], ["c.1", "a.1"], ["x.d.1", "x.e.1"],
         ["x.e.1", "x.d.1"]]


def run(repo, *extra: str):
    return run_tool("cycles", "--repo", repo, "--deps", "deps.json", *extra, script=RECORDS_SCRIPT)


def test_cycles_command_text_and_json(tmp_path) -> None:  # AC-10
    repo = make_repo(tmp_path, CYCLE_MODEL)
    write_json(repo / "deps.json", {"edges": EDGES})
    text = run(repo)
    assert text.returncode == 0, text.stderr
    assert text.stdout == (
        "group top level: a, b, c\n"
        "leave out b -> c (1 module edges)\n"
        "group x: x.d, x.e\n"
        "leave out x.d -> x.e (1 module edges)\n"
        "2 relationships to leave out in 2 groups, 0 too large\n"
    )
    data = json.loads(run(repo, "--format", "json").stdout)
    assert data["summary"] == {"relationships": 2, "groups": 2, "too_large": 0}
    assert data["groups"][1] == {"parent": "x", "siblings": ["x.d", "x.e"],
                                 "leave_out": [{"from": "x.d", "to": "x.e", "module_edges": 1}], "too_large": None}


def test_cycles_command_timeout(tmp_path) -> None:  # AC-13
    repo = make_repo(tmp_path, CYCLE_MODEL)
    write_json(repo / "deps.json", {"edges": EDGES})
    proc = run(repo, "--timeout", "0")
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: timeout: ")


def test_cycles_command_without_a_cycle(tmp_path) -> None:  # AC-14
    repo = make_repo(tmp_path, SHOP_MODEL)
    write_json(repo / "deps.json", {"edges": [["shop.orders.x", "shop.checkout.y"]]})
    text = run(repo)
    assert (text.returncode, text.stdout) == (0, "0 relationships to leave out in 0 groups, 0 too large\n")
    assert json.loads(run(repo, "--format", "json").stdout) == {
        "groups": [], "summary": {"relationships": 0, "groups": 0, "too_large": 0}}


def test_cycles_command_needs_the_dependency_file(tmp_path) -> None:
    repo = make_repo(tmp_path, SHOP_MODEL)
    proc = run(repo)
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: bad-input: --deps file not found"]
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest -q tests/scripts/test_architecture_records_args.py tests/scripts/test_architecture_records_cycles_command.py`
Expected: 9 failed (the subcommand row, `test_cycles_defaults`, the three `test_cycles_usage_errors` cases and the four command tests), the rest pass.

- [ ] **Step 3: GREEN.** In `skills/shared/scripts/architecture-records/args.mjs`, replace

```js
    '--summary', '--rejected', '--timeout'],
};
const SWITCHES = { change: ['--compare'] };
const REQUIRED = { change: ['--repo', '--deps', '--name', '--date', '--run'] };
```

with

```js
    '--summary', '--rejected', '--timeout'],
  cycles: ['--repo', '--model', '--deps', '--separator', '--format', '--timeout'],
};
const SWITCHES = { change: ['--compare'], cycles: [] };
const REQUIRED = { change: ['--repo', '--deps', '--name', '--date', '--run'], cycles: ['--repo', '--deps'] };
```

replace

```js
    if (!compare && opts[flag] === undefined) throw usage(`${flag} is required without --compare`);
```

with

```js
    if (command === 'change' && !compare && opts[flag] === undefined) throw usage(`${flag} is required without --compare`);
```

and replace

```js
  return {
    command,
    repo: opts['--repo'],
    model: opts['--model'] ?? 'docs/architecture',
    before: opts['--before'] ?? null,
```

with

```js
  if (command === 'cycles') {
    const format = opts['--format'] ?? 'text';
    if (format !== 'text' && format !== 'json') throw usage('--format must be text or json');
    return { command, repo: opts['--repo'], model: opts['--model'] ?? 'docs/architecture', deps: opts['--deps'],
      separator: opts['--separator'] ?? '.', format, timeout: Number(timeoutText) };
  }
  return {
    command,
    repo: opts['--repo'],
    model: opts['--model'] ?? 'docs/architecture',
    before: opts['--before'] ?? null,
```

In `skills/shared/scripts/architecture-records.mjs`, replace

```js
// Architecture records: drafts the change file of a defining-architecture run.
```

with

```js
// Architecture records: drafts the change file of a defining-architecture run, or proposes the relationships a
// baseline leaves out of each cycle.
```

replace

```js
import { readJson, parseGap } from './architecture-delta/inputs.mjs';
```

with

```js
import { readJson, parseDeps, parseGap } from './architecture-delta/inputs.mjs';
import { findCycles, cyclesText } from './architecture-records/cycles.mjs';
```

insert above `async function main(argv) {`:

```js
async function runCycles(args, deadline) {
  const loaded = await loadRepoModel(args, deadline);
  const deps = resolveInside(loaded.repo, args.deps, '--deps');
  if (!deps.exists) throw new ToolError('bad-input', '--deps file not found');
  const edges = parseDeps(readJson(deps.path, '--deps'));
  deadline.check();
  const result = findCycles(loaded.model, edges, args.separator, deadline.check);
  return { output: args.format === 'json' ? `${JSON.stringify(result, null, 2)}\n` : cyclesText(result), exitCode: 0 };
}

```

and replace

```js
  const result = await runChange(args, deadline);
```

with

```js
  const result = args.command === 'change' ? await runChange(args, deadline) : await runCycles(args, deadline);
```

- [ ] **Step 4: run GREEN and every records test.**

Run: `uv run pytest -q tests/scripts/ -k architecture_records`
Expected: all pass (the safety test now also scans `cycles.mjs`).

- [ ] **Step 5: run the full suite.**

Run: `uv run pytest -q` (about 3 minutes)
Expected: all pass.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-records/args.mjs skills/shared/scripts/architecture-records.mjs tests/scripts/test_architecture_records_args.py tests/scripts/test_architecture_records_cycles_command.py
git commit -m "feat(#31): architecture-records cycles - text and JSON output"
```
