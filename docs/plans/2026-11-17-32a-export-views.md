# Export Format 4: Titles, Areas and Capabilities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `export` prints format 4 (element and relationship titles, area views, capability views); the view rules and the capability-names records rule apply wherever the model loads; the model walk counts `generated` apart.

**Architecture:** This repository has no architecture model. A new read-only module `views.mjs` beside `model.mjs` reads LikeC4's views and checks them; `model.mjs` adds titles and calls it; `report.mjs` prints the new fields; `records.mjs` checks `capabilities` against the capability names; `walk.mjs` counts `generated` apart.

**Tech Stack:** Node ESM, LikeC4 1.60.0, pytest.

**Spec:** `docs/superpowers/specs/2026-11-17-architecture-docs-design.md` (plan 1 of 4: "Terms", "Areas and capabilities", "What `export` prints (format 4)", AC-1 to AC-7) — decisions applied: none. AC-2's wording was corrected while planning to match the main-body matching rule (a step to an element that holds a relationship's target is a call; a step to an element inside it is not).

**Open decisions:** none

**Size:** 6 tasks, 2 entry paths (`export`, `check`), lines reported in the self-review commit (reported, not a target)

**Trust boundary:** unchanged. New values come from LikeC4's computed model, are shape-checked like the existing ones (`internal` on a wrong shape), and are printed through the existing cleaning. `views.mjs` reads only; the source test (`test_tool_source_never_spawns_or_writes`) covers it because it globs `architecture-delta/*.mjs`.

### Risk & Confidence Assessment

**Confidence:** 93% — every LikeC4 value used was probed on the fixtures below; the work is several small additions with many exact-shape test edits.

**Complexity Risk:** Medium — the step-matching rule (inside, call, reply) is the one piece of logic with direction to get right; Task 3's tests pin all four cases.

**Environmental Risk:** Low — same worktree and suite (416 passing on `main`).

**Main failure modes:** a missed exact-shape assert in an existing test (the sweep lists every one found); a fake LikeC4 shim without `views()` or `title` (sweep rows); Windows path separators in the walk message (Task 5 joins with `/`).

**Unknown variables:**
- Whether LikeC4 ever returns a view whose `$view.edges` entry has a `source` that is not a node id. The probes never did; `views.mjs` treats it as `internal`.

Probe facts used (LikeC4 1.60.0, fixtures of Tasks 2 and 3): `view.$view._type` is `element` or `dynamic`; `$view.title` is `null` for an untitled unscoped or dynamic view, and the scope element's title for an untitled scoped view; `$view.viewOf` is the scope element id or absent; nodes carry `modelRef` (the element id), and a `group` node has none (id `@gr1`); an unscoped view that includes `shop.web` also draws its ancestor `shop`; dynamic edges come in order as `step-01`, `step-02:par.01`, `step-02:par.02`, `step-03`, with `source`, `target` (node ids) and `label` (string or `null`); `element.description` and `view.description` have `isEmpty` and `md` (source text, dedented); `element.title` is the element's name when untitled; `relationship.title` is a string or `null`.

---

## Caller and test sweep

Searched: `skills/`, `tests/` with `rg -n "\"format\"\]|== 3|\"allowed\"\] ==|\"runtime\"\] ==|\"elements\"\]\[|list\(data\) ==|computedModel|readRecords|uniquePairs|uniqueLinks|capabilities" skills/shared/scripts tests/scripts`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `format` 3 → 4 | `tests/scripts/test_architecture_delta_export.py:23` | assert | 1 | `assert data["format"] == 4` |
| same | `tests/scripts/test_architecture_delta_export.py:44` | assert | 1 | `"format": 3` → `"format": 4` |
| same | `tests/scripts/test_architecture_delta_export.py:182` | assert | 1 | `== 3` → `== 4` |
| same | `tests/scripts/test_architecture_delta_records.py:363` | assert | 1 | `== 3` → `== 4` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py:156` | assert | 1 | `== 3` → `== 4` |
| element gains `title`, `description` | `tests/scripts/test_architecture_delta_export.py:27-29` | assert | 1 | add `"title": "Payments", "description": None,` after `"rules": [],` |
| same | `tests/scripts/test_architecture_delta_model.py:112-114` | assert | 1 | add `"title": "Payments", "description": None,` after `"rules": [],` |
| `allowed` entries gain `titles` | `tests/scripts/test_architecture_delta_export.py:30-32` | assert | 1 | each entry gains `"titles": []` |
| same | `tests/scripts/test_architecture_delta_export.py:38` | assert | 1 | `[{"from": "a", "to": "b", "titles": ["again"]}]` |
| same | `tests/scripts/test_architecture_delta_export.py:205` | assert | 1 | each entry gains `"titles": []` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py:142` | assert | 1 | `[{"from": "a", "to": "b", "titles": []}]` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py:157` | assert | 1 | each entry gains `"titles": []` |
| `runtime` entries gain `titles` | `tests/scripts/test_architecture_delta_runtime_links.py:158-161` | assert | 1 | `calls` entry `"titles": []`, `http` entry `"titles": ["one", "two"]`, `push` entry `"titles": []` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py:166` | assert | 1 | each entry gains `"titles": []` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py:173` | assert | 1 | entry gains `"titles": []` |
| loader relationships gain `title` | `tests/scripts/test_architecture_delta_runtime_links.py:103` | assert | 1 | `set(r) == {"from", "to", "title"}` |
| loader requires a string element `title` | `tests/scripts/test_architecture_delta_model.py` `GOOD["ELEMENT"]` | fake | 1 | `"{ id: 'a', kind: 'component', title: 'A', tags: [], getMetadata() { return {}; } }"` |
| same | `tests/scripts/test_architecture_delta_model.py` param `no-target` element | fake | 1 | `"{ id: 'a', kind: 'component', title: 'A', tags: [], getMetadata() { return {}; } }"` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py` `KIND_SHIM` `E` | fake | 1 | `const E = (id) => ({ id, kind: 'component', title: id, tags: [], getMetadata() { return {}; } });` |
| same | `tests/scripts/test_architecture_delta_check.py:64-73` shim | fake | — | none: both elements fail an earlier check (no id; array `code`), which runs before the title check |
| loader calls `computed.views()` | `tests/scripts/test_architecture_delta_model.py` `SHIM` | fake | 2 | `return { elements() { return [ELEMENT]; }, relationships() { return [RELATIONSHIP]; }, views() { return []; } };` |
| same | `tests/scripts/test_architecture_delta_runtime_links.py` `KIND_SHIM` | fake | 2 | `return { elements() { return [E('a'), E('b')]; }, relationships() { return [RELATIONSHIP]; }, views() { return []; } };` |
| same | `tests/scripts/test_architecture_delta_model.py` `BAD_ELEMENT` | fake | — | none: every case fails at the element or relationship stage, before views are read |
| top-level keys gain `areas` | `tests/scripts/test_architecture_delta_export.py:22` | assert | 2 | append `"areas"` to the list |
| same | `tests/scripts/test_architecture_delta_export.py:44` | assert | 2 | append `"areas": []` to the dict |
| top-level keys gain `capabilities` | `tests/scripts/test_architecture_delta_export.py:22` | assert | 3 | append `"capabilities"` to the list |
| same | `tests/scripts/test_architecture_delta_export.py:44` | assert | 3 | append `"capabilities": []` to the dict |
| `readRecords(modelDir, elementIds, tick, capabilityNames = [])` | `skills/shared/scripts/architecture-delta.mjs` `loadRepoModel` | caller | 4 | `readRecords(model.path, loaded.elements.map((element) => element.id), deadline.check, loaded.capabilities.map((capability) => capability.name))` |
| same | `tests/scripts/test_architecture_delta_records.py:127`, `:439-441` | caller | — | none: the new argument defaults to `[]`, and these calls pass no `capabilities` |
| `capabilities` entries must name a capability | `tests/scripts/test_architecture_delta_records.py:465-469` `test_decisions_carry_obligations` | test | 4 | `capabilities=["pay"]`, and its `model_folder` files gain `"views.c4": CAPABILITY_VIEW` |
| same | `tests/scripts/test_architecture_delta_records.py:83`, `:485` | test | — | none: shape-only, pass 4 not reached |
| `uniquePairs`, `uniqueLinks`, `byLink` replaced | `report.mjs` only | helper | 1 | deleted; no other caller (`rg` above) |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 items 1–3, Task 2 items 1–4, Task 3 items 1–4; focused tests `uv run pytest -q tests/scripts/test_architecture_delta_views.py tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_model.py tests/scripts/test_architecture_delta_runtime_links.py` |
| C2 | 6 | 4–6 | Task 4 items 1–2, Task 5 items 1–3, Task 6 verification; full suite `uv run pytest -q` |

---

### Task 1: elements and relationships carry titles; format 4

**Tier:** standard — complete code, but fifteen exact-shape test edits across four files.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/model.mjs` (`loadModel`)
- Modify: `skills/shared/scripts/architecture-delta/report.mjs` (`exportJson`; delete `uniquePairs`, `uniqueLinks`, `byLink`)
- Test: `tests/scripts/test_architecture_delta_export.py` (append; sweep edits)
- Modify (sweep): `tests/scripts/test_architecture_delta_model.py`, `tests/scripts/test_architecture_delta_runtime_links.py`, `tests/scripts/test_architecture_delta_records.py`

**Callers that move with this task:** every Task 1 row of the sweep table. This is an atomic change: the format number and the exact shapes change together, so every assert moves in this commit.

**Reviewer looks at:**
- titles merged per pair — mutation: keep only the first relationship's title — killed by: `test_export_carries_titles_and_descriptions` (`["reads", "writes"]`)
- titles are text, not ids — mutation: `clean` instead of `cleanText` on titles — killed by: `test_titles_are_not_cut`
- description is the source text — mutation: read `description.text` instead of `.md` — killed by: `test_export_carries_titles_and_descriptions` (`**Two**`)

- Satisfies Spec AC: AC-1 (titles and descriptions)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append to `tests/scripts/test_architecture_delta_export.py`:

```python
TITLED = """specification {
  relationship http
}
model {
  a = component 'A' {
    description '''
      One
      **Two**
    '''
  }
  b = component
  a -> b 'reads'
  a -> b 'writes'
  a -> b
  a -[http]-> b 'calls'
}
"""


def test_export_carries_titles_and_descriptions(tmp_path) -> None:  # AC-1 (titles)
    data = export(make_repo(tmp_path, TITLED))
    assert data["format"] == 4
    assert data["elements"] == [
        {"id": "a", "kind": "component", "tags": [], "code": [], "rules": [], "title": "A", "description": "One\n**Two**"},
        {"id": "b", "kind": "component", "tags": [], "code": [], "rules": [], "title": "b", "description": None},
    ]
    assert data["allowed"] == [{"from": "a", "to": "b", "titles": ["reads", "writes"]}]
    assert data["runtime"] == [{"from": "a", "to": "b", "kind": "http", "titles": ["calls"]}]


def test_titles_are_not_cut(tmp_path) -> None:
    title = "t" * 250
    model = "model {\n  a = component '" + title + "'\n  b = component 'B'\n  a -> b '" + title + "'\n}\n"
    data = export(make_repo(tmp_path, model))
    assert data["elements"][0]["title"] == title
    assert data["allowed"][0]["titles"] == [title]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_delta_export.py -k "titles"`. Expected: FAIL (`format` is 3; no `title`).
- [ ] **Step 3: GREEN.** In `model.mjs` `loadModel`, inside the element loop after the `for (const key of ['code', 'rules'])` check, add:

```js
    if (typeof element.title !== 'string') throw shapeError(`element ${element.id} without a string title`);
```

and push the element as:

```js
    elements.push({
      id: element.id,
      kind: element.kind,
      tags: [...element.tags],
      code: splitList(meta.code),
      rules: splitList(meta.rules).filter((rule) => rule !== ''),
      title: element.title,
      description: richText(element.description),
    });
```

Add above `loadModel`:

```js
// LikeC4 rich text (a description): its source text, or null when it is empty or absent.
export function richText(value) {
  return value && value.isEmpty === false && typeof value.md === 'string' ? value.md : null;
}
```

In the relationship loop, after the kind check, add:

```js
    const title = relationship.title ?? null;
    if (title !== null && typeof title !== 'string') throw shapeError('a relationship whose title is not a string');
    const pair = { from: relationship.source.id, to: relationship.target.id, title };
```

(replacing the existing `const pair = ...` line; the two `push` lines stay as they are).

In `report.mjs`, delete `uniquePairs`, `byLink` and `uniqueLinks`, and add:

```js
// One entry per key, with the distinct non-empty titles of the relationships it stands for, sorted raw.
function mergeTitles(list, keyOf) {
  const byKey = new Map();
  for (const item of list) {
    const key = keyOf(item);
    if (!byKey.has(key)) byKey.set(key, { item, titles: new Set() });
    if (typeof item.title === 'string' && item.title !== '') byKey.get(key).titles.add(item.title);
  }
  return [...byKey.values()].map(({ item, titles }) => ({ ...item, titles: [...titles].sort(cmp) }));
}

const pairKey = (pair) => `${pair.from}\u0000${pair.to}`;
const linkKey = (link) => `${pairKey(link)}\u0000${link.kind}`;
const byLink = (x, y) => byPair(x, y) || cmp(x.kind, y.kind);
```

In `exportJson`, set `format: 4`, add `title: cleanText(element.title), description: element.description === null ? null : cleanText(element.description),` after `rules` in the element map, and replace the `allowed` and `runtime` lines with:

```js
    allowed: mergeTitles(model.relationships, pairKey).sort(byPair)
      .map((entry) => ({ ...cleanPair(entry), titles: entry.titles.map(cleanText) })),
    runtime: mergeTitles(model.runtime, linkKey).sort(byLink)
      .map((link) => ({ ...cleanPair(link), kind: clean(link.kind), titles: link.titles.map(cleanText) })),
```

Then make every Task 1 sweep edit.
- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_model.py tests/scripts/test_architecture_delta_runtime_links.py tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_delta_check.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/model.mjs skills/shared/scripts/architecture-delta/report.mjs tests/scripts && git commit -m "feat(#32): export format 4 carries element and relationship titles"`

### Task 2: area views and the view type and name rules

**Tier:** standard — complete code for a new module; the area-element rule needs care.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/views.mjs`
- Modify: `skills/shared/scripts/architecture-delta/model.mjs` (`loadModel` return)
- Modify: `skills/shared/scripts/architecture-delta/report.mjs` (`exportJson`)
- Test: `tests/scripts/test_architecture_delta_views.py` (create)

**Callers that move with this task:** the Task 2 rows of the sweep table (`SHIM`, `KIND_SHIM`, export key list and empty export).

**Reviewer looks at:**
- a scoped area is its whole subtree — mutation: use the view's nodes for a scoped view too — killed by: `test_area_views_are_exported` (`shop.api.db` in, `pay` out)
- group nodes ignored — mutation: keep nodes without `modelRef` — killed by: `test_area_views_are_exported`
- untitled view falls back to its id — mutation: drop `?? view.id` — killed by: `test_area_views_are_exported` (`area-plain`)
- name rule — mutation: drop the reserved-name test, or the 64-character cap — killed by: `test_bad_view_types_and_names_are_model_errors` (`area-con`, the 65-character name)

- Satisfies Spec AC: AC-1 (areas), AC-3 (types and names), AC-6
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_delta_views.py`:

```python
"""Area and capability views in export (spec 2026-11-17-architecture-docs-design.md, plan 1)."""

from __future__ import annotations

import json
from pathlib import Path

from arch_delta_support import error_lines, make_repo, require_node, run_tool, write_json

require_node()

BASE = """specification {
  relationship http
}
model {
  shop = system 'Shop' {
    web = container 'Web'
    api = container 'API' {
      db = component 'DB'
    }
  }
  pay = system 'Pay'
  shop.web -> shop.api 'places order'
  shop.api -[http]-> pay 'charges'
  pay -[http]-> shop.api.db 'settles'
}
"""


def repo_with(tmp_path: Path, views: str) -> Path:
    return make_repo(tmp_path, BASE + "views {\n" + views + "}\n")


def export(repo: Path) -> dict:
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def both_commands(repo: Path) -> list[list[str]]:
    deps = write_json(repo / "deps.json", {"edges": []})
    return [error_lines(run_tool("export", "--repo", repo)), error_lines(run_tool("check", "--repo", repo, "--deps", deps))]


AREAS = """  view area-shop of shop {
    include *
  }
  view area-two {
    title 'Two'
    description 'Front and back'
    include shop.web, pay
    group 'G' {
      include shop.api
    }
  }
  view area-plain {
    include pay
  }
  view other {
    include *
  }
"""


def test_area_views_are_exported(tmp_path) -> None:  # AC-1 (areas), AC-6
    data = export(repo_with(tmp_path, AREAS))
    assert data["areas"] == [
        {"name": "plain", "title": "area-plain", "description": None, "elements": ["pay"]},
        {"name": "shop", "title": "Shop", "description": None, "elements": ["shop", "shop.api", "shop.api.db", "shop.web"]},
        {"name": "two", "title": "Two", "description": "Front and back", "elements": ["pay", "shop", "shop.api", "shop.web"]},
    ]


LONG = "a" * 65

BAD_VIEWS = f"""  dynamic view area-flow {{
    shop.web -> shop.api
  }}
  view capability-box {{
    include *
  }}
  view area-Shop {{
    include *
  }}
  view area-con {{
    include *
  }}
  view area-{LONG} {{
    include *
  }}
"""


def test_bad_view_types_and_names_are_model_errors(tmp_path) -> None:  # AC-3 (types and names)
    expected = [
        "error: model-error: view area-Shop: Shop is not a valid name",
        f"error: model-error: view area-{LONG}: {LONG} is not a valid name",
        "error: model-error: view area-con: con is not a valid name",
        "error: model-error: view area-flow: an area view must be an element view",
        "error: model-error: view capability-box: a capability view must be a dynamic view",
    ]
    assert both_commands(repo_with(tmp_path, BAD_VIEWS)) == [expected, expected]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_delta_views.py`. Expected: FAIL (no `areas` key; exit 0 for the bad views).
- [ ] **Step 3: GREEN.** Create `views.mjs`:

```js
// Area and capability views: read from LikeC4's computed model and checked against the model's elements.
import { ToolError } from './errors.mjs';
import { cmp } from './report.mjs';

export const AREA = 'area-';
export const CAPABILITY = 'capability-';
const NAME = /^[a-z0-9][a-z0-9-]{0,63}$/;
const RESERVED = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/;

// Spec, Terms: X is inside Y when X's id starts with Y's id and a dot; here an id also counts as inside itself.
export const within = (id, outer) => id === outer || id.startsWith(`${outer}.`);

function shapeError(detail) {
  return new ToolError('internal', `likec4 returned ${detail}`);
}

function richText(value) {
  return value && value.isEmpty === false && typeof value.md === 'string' ? value.md : null;
}

function readView(view) {
  if (typeof view?.id !== 'string' || view.$view === null || typeof view.$view !== 'object') {
    throw shapeError('a view without a string id');
  }
  const data = view.$view;
  if (typeof data._type !== 'string' || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
    throw shapeError(`view ${view.id} without a type, nodes and edges`);
  }
  const title = data.title ?? null;
  if (title !== null && typeof title !== 'string') throw shapeError(`view ${view.id} with a non-string title`);
  return {
    id: view.id,
    type: data._type,
    title: title ?? view.id,
    description: richText(view.description),
    viewOf: typeof data.viewOf === 'string' ? data.viewOf : null,
    nodes: data.nodes,
    edges: data.edges,
  };
}

// Spec, Areas: a scoped view's elements are its scope and everything inside it; an unscoped view's are the element nodes it draws.
function areaElements(view, elementIds) {
  if (view.viewOf !== null) return elementIds.filter((id) => within(id, view.viewOf));
  const known = new Set(elementIds);
  return [...new Set(view.nodes.map((node) => node?.modelRef).filter((ref) => typeof ref === 'string' && known.has(ref)))];
}

function typeProblem(view, prefix) {
  const wanted = prefix === AREA ? 'element' : 'dynamic';
  if (view.type === wanted) return null;
  return prefix === AREA ? 'an area view must be an element view' : 'a capability view must be a dynamic view';
}

// The area and capability views, or one `model-error` naming every problem, sorted by view id, then step.
export function readViews(computed, elementIds) {
  if (typeof computed.views !== 'function') throw shapeError('a model without views()');
  const problems = [];
  const areas = [];
  for (const raw of computed.views()) {
    const view = readView(raw);
    const prefix = view.id.startsWith(AREA) ? AREA : view.id.startsWith(CAPABILITY) ? CAPABILITY : null;
    if (prefix === null) continue;
    const add = (message, step = 0) => problems.push({ view: view.id, step, line: `view ${view.id}: ${message}` });
    const wrongType = typeProblem(view, prefix);
    if (wrongType !== null) {
      add(wrongType);
      continue;
    }
    const name = view.id.slice(prefix.length);
    if (!NAME.test(name) || RESERVED.test(name)) {
      add(`${name} is not a valid name`);
      continue;
    }
    const entry = { name, title: view.title, description: view.description };
    if (prefix === AREA) areas.push({ ...entry, elements: areaElements(view, elementIds).sort(cmp) });
  }
  if (problems.length > 0) {
    problems.sort((x, y) => cmp(x.view, y.view) || x.step - y.step);
    throw new ToolError('model-error', problems.map((item) => item.line));
  }
  return { areas: areas.sort((x, y) => cmp(x.name, y.name)) };
}
```

In `model.mjs`, import `readViews` from `./views.mjs`, use `views.mjs`'s copy of rich text by deleting `richText` from `model.mjs` and importing it instead (export it from `views.mjs`: change `function richText` to `export function richText`), and replace `return { elements, relationships, runtime };` with:

```js
  const views = readViews(computed, elements.map((element) => element.id));
  return { elements, relationships, runtime, ...views };
```

In `report.mjs` `exportJson`, after `coverage`, add:

```js
    areas: model.areas.map((area) => ({
      name: clean(area.name),
      title: cleanText(area.title),
      description: area.description === null ? null : cleanText(area.description),
      elements: area.elements.map(clean),
    })),
```

Make the Task 2 sweep edits.
- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_delta_views.py tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_model.py tests/scripts/test_architecture_delta_runtime_links.py tests/scripts/test_architecture_delta_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta tests/scripts && git commit -m "feat(#32): export lists area views; view type and name rules"`

### Task 3: capability views and the step rule

**Tier:** standard — complete code; the matching direction is pinned by four step cases.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/views.mjs` (`readViews`; add `readSteps`)
- Modify: `skills/shared/scripts/architecture-delta/model.mjs` (pass relationships to `readViews`)
- Modify: `skills/shared/scripts/architecture-delta/report.mjs` (`exportJson`)
- Test: `tests/scripts/test_architecture_delta_views.py` (append)

**Callers that move with this task:** the Task 3 rows of the sweep table (export key list and empty export).

**Reviewer looks at:**
- a step matches a deeper relationship — mutation: require exact ends (`===` instead of `within`) — killed by: `test_capability_steps_are_calls_and_replies` (step 4)
- direction of `within` — mutation: `within(step end, relationship end)` instead of `within(relationship end, step end)` — killed by: `test_capability_steps_are_calls_and_replies` (step 4) and `test_a_step_with_no_relationship_is_a_model_error` (step 3)
- reply only when no call matches — mutation: compute `reply` from the back match alone — killed by: `test_capability_steps_are_calls_and_replies` (step 1 stays a call)
- problems sorted by view then step — mutation: drop the sort — killed by: `test_a_step_with_no_relationship_is_a_model_error`

- Satisfies Spec AC: AC-1 (capabilities), AC-2, AC-3 (steps)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
CAPS = """  dynamic view capability-order {
    title 'Place an order'
    shop.web -> shop.api 'sends order'
    parallel {
      shop.api -> pay 'charges card'
      shop.api -> shop.web 'confirms'
    }
    pay -> shop.api
  }
  dynamic view capability-quiet {
    shop.web -> shop.api
  }
"""


def test_capability_steps_are_calls_and_replies(tmp_path) -> None:  # AC-1 (capabilities), AC-2
    data = export(repo_with(tmp_path, CAPS))
    assert data["capabilities"] == [
        {"name": "order", "title": "Place an order", "description": None, "steps": [
            {"from": "shop.web", "to": "shop.api", "label": "sends order", "reply": False, "kinds": ["uses"]},
            {"from": "shop.api", "to": "pay", "label": "charges card", "reply": False, "kinds": ["http"]},
            {"from": "shop.api", "to": "shop.web", "label": "confirms", "reply": True, "kinds": ["uses"]},
            {"from": "pay", "to": "shop.api", "label": None, "reply": False, "kinds": ["http"]},
        ]},
        {"name": "quiet", "title": "capability-quiet", "description": None, "steps": [
            {"from": "shop.web", "to": "shop.api", "label": None, "reply": False, "kinds": ["uses"]},
        ]},
    ]


def test_a_step_with_no_relationship_is_a_model_error(tmp_path) -> None:  # AC-3 (steps)
    views = CAPS + """  dynamic view capability-bad {
    shop.web -> shop.api
    shop.web -> pay
    shop.api.db -> shop.web
  }
  dynamic view area-x {
    shop.web -> shop.api
  }
"""
    expected = [
        "error: model-error: view area-x: an area view must be an element view",
        "error: model-error: view capability-bad: step 2: shop.web -> pay follows no relationship",
        "error: model-error: view capability-bad: step 3: shop.api.db -> shop.web follows no relationship",
    ]
    assert both_commands(repo_with(tmp_path, views)) == [expected, expected]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_delta_views.py -k "steps or no_relationship"`. Expected: FAIL (no `capabilities` key; exit 0).
- [ ] **Step 3: GREEN.** In `views.mjs` add:

```js
// Spec, Capabilities: a relationship matches a step from A to B when its source is A or inside A and its target is B or inside B.
function readSteps(view, relationships, add) {
  const refs = new Map(view.nodes.map((node) => [node?.id, node?.modelRef]));
  return view.edges.map((edge, index) => {
    const from = refs.get(edge?.source);
    const to = refs.get(edge?.target);
    if (typeof from !== 'string' || typeof to !== 'string') throw shapeError(`view ${view.id} with a step between non-elements`);
    const forward = relationships.filter((r) => within(r.from, from) && within(r.to, to));
    const back = forward.length > 0 ? [] : relationships.filter((r) => within(r.from, to) && within(r.to, from));
    if (forward.length === 0 && back.length === 0) add(`step ${index + 1}: ${from} -> ${to} follows no relationship`, index + 1);
    const kinds = [...new Set((forward.length > 0 ? forward : back).map((r) => r.kind ?? 'uses'))].sort(cmp);
    const label = typeof edge.label === 'string' && edge.label !== '' ? edge.label : null;
    return { from, to, label, reply: forward.length === 0, kinds };
  });
}
```

Change `readViews(computed, elementIds)` to `readViews(computed, elementIds, relationships, runtime)`; at its top add `const all = [...relationships.map((r) => ({ ...r, kind: null })), ...runtime];` and `const capabilities = [];`; after the area push add:

```js
    else capabilities.push({ ...entry, steps: readSteps(view, all, add) });
```

(the `if (prefix === AREA) areas.push(...)` line becomes `if ... else ...`), and return `{ areas: ..., capabilities: capabilities.sort((x, y) => cmp(x.name, y.name)) }`.

In `model.mjs`: `readViews(computed, elements.map((element) => element.id), relationships, runtime)`.

In `report.mjs` `exportJson`, after `areas`, add:

```js
    capabilities: model.capabilities.map((capability) => ({
      name: clean(capability.name),
      title: cleanText(capability.title),
      description: capability.description === null ? null : cleanText(capability.description),
      steps: capability.steps.map((step) => ({
        from: clean(step.from),
        to: clean(step.to),
        label: step.label === null ? null : cleanText(step.label),
        reply: step.reply,
        kinds: step.kinds.map(clean),
      })),
    })),
```

Make the Task 3 sweep edits.
- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_delta_views.py tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_model.py tests/scripts/test_architecture_delta_runtime_links.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta tests/scripts && git commit -m "feat(#32): export lists capability views; every step follows a relationship"`

### Task 4: capabilities in records name capability views

**Tier:** fast — complete edits.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/records.mjs` (`linkPass`, `laterPasses`, `readRecords`)
- Modify: `skills/shared/scripts/architecture-delta/report.mjs` (`ID_KEYS`)
- Modify: `skills/shared/scripts/architecture-delta.mjs` (`loadRepoModel`)
- Test: `tests/scripts/test_architecture_delta_records.py` (append; sweep edit)

**Callers that move with this task:** `architecture-delta.mjs` `loadRepoModel`; `test_decisions_carry_obligations`.

**Reviewer looks at:**
- the names come from the model — mutation: pass `[]` instead of the capability names in `loadRepoModel` — killed by: `test_decisions_carry_obligations` and `test_capabilities_name_capability_views`
- line order within a record — mutation: check `capabilities` before `owner` — killed by: `test_capability_line_follows_the_owner_line`

**Pinned by:** `capabilities` in `ID_KEYS` has no observable effect (a valid name is at most 64 ASCII characters, cleaned the same either way); it is kept for the spec's cleaning rule and needs no test.

- Satisfies Spec AC: AC-4
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append:

```python
CAPABILITY_VIEW = "views {\n  dynamic view capability-pay {\n    shop.checkout -> shop.payments\n  }\n}\n"


def test_capabilities_name_capability_views(tmp_path) -> None:  # AC-4
    files = {"views.c4": CAPABILITY_VIEW,
             "decisions/a.json": dfile(decision("D-1", capabilities=["pay"])),
             "contracts/b.json": cfile(contract("C-1", capabilities=["ship", "pay", "pay"]))}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: contracts/b.json: contracts[0].capabilities[0]: ship is not a capability",
        "error: record-error: contracts/b.json: contracts[0].capabilities[2]: pay is listed twice",
    ]


def test_capability_line_follows_the_owner_line(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("D-1", owner="ghost", obligations=["o"], capabilities=["x"]))}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: decisions/a.json: decisions[0].owner: ghost is not a model element",
        "error: record-error: decisions/a.json: decisions[0].capabilities[0]: x is not a capability",
    ]
```

Make the sweep edit to `test_decisions_carry_obligations`: `capabilities=["pay"]`, and `model_folder(tmp_path, {"views.c4": CAPABILITY_VIEW, "decisions/a.json": dfile(cross, principle)})` (move `CAPABILITY_VIEW` above that test).
- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_delta_records.py -k "capabilit or carry_obligations"`. Expected: the two new tests FAIL (exit 0); `test_decisions_carry_obligations` passes.
- [ ] **Step 3: GREEN.** In `records.mjs`:
  - `linkPass(file, add, elements, decisions, changes)` becomes `linkPass(file, add, elements, decisions, changes, capabilities)`, and gains, after `run`:

```js
  const capabilityList = (values, at) => {
    const seen = new Set();
    list(values).forEach((value, index) => {
      if (!isString(value) || value === '') return;
      if (!capabilities.has(value)) add(`${at}[${index}]`, `${value} is not a capability`);
      if (seen.has(value)) add(`${at}[${index}]`, `${value} is listed twice`);
      seen.add(value);
    });
  };
```

  - in the contracts branch, before `return;`: `capabilityList(record.capabilities, `${at}.capabilities`);`
  - after `if (name === 'decisions') element(record.owner, `${at}.owner`);`: `if (name === 'decisions') capabilityList(record.capabilities, `${at}.capabilities`);`
  - `laterPasses(files, elements, changes)` becomes `laterPasses(files, elements, changes, capabilities)` and passes `capabilities` to `linkPass`;
  - `readRecords(modelDir, elementIds, tick = () => {})` becomes `readRecords(modelDir, elementIds, tick = () => {}, capabilityNames = [])`, and its `laterPasses(...)` call gains `new Set(capabilityNames)` as the last argument.

In `report.mjs` `ID_KEYS`, add `'capabilities'`. In `architecture-delta.mjs` `loadRepoModel`, replace the `readRecords(...)` line with:

```js
  const records = readRecords(model.path, loaded.elements.map((element) => element.id), deadline.check,
    loaded.capabilities.map((capability) => capability.name));
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_delta_records.py tests/scripts/test_architecture_delta_views.py tests/scripts/test_architecture_delta_export.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts tests/scripts/test_architecture_delta_records.py && git commit -m "feat(#32): record capabilities name capability views"`

### Task 5: the model walk counts `generated` apart

**Tier:** fast — complete code.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/walk.mjs` (`walkModelDir`)
- Test: `tests/scripts/test_architecture_delta_views.py` (append)

**Callers that move with this task:** none (`walkModelDir`'s signature is unchanged; `test_folder_limits`, `test_limits_end_to_end` and `test_folder_at_exactly_50_mb_is_accepted` keep their messages).

**Reviewer looks at:**
- files counted apart — mutation: count `generated` files in the model's count too — killed by: `test_generated_folder_counts_apart`
- bytes counted apart — mutation: count `generated` bytes in the model's total — killed by: `test_generated_bytes_count_apart`
- source files refused only in `generated` — mutation: drop the `.c4` check — killed by: `test_likec4_source_in_generated_is_refused`

- Satisfies Spec AC: AC-7
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append (add `call` to the `arch_delta_support` import):

```python
MB = 1024 * 1024


def test_generated_folder_counts_apart(tmp_path) -> None:  # AC-7
    repo = make_repo(tmp_path)
    folder = repo / "docs" / "architecture"
    for i in range(600):
        (folder / f"f{i}.txt").write_text("x", encoding="utf-8")
    generated = folder / "generated"
    generated.mkdir()
    for i in range(1500):
        (generated / f"g{i}.md").write_text("x", encoding="utf-8")
    assert run_tool("export", "--repo", repo).returncode == 0
    for i in range(1500, 2001):
        (generated / f"g{i}.md").write_text("x", encoding="utf-8")
    assert error_lines(run_tool("export", "--repo", repo)) == ["error: model-size: generated: more than 2000 files"]


def test_generated_bytes_count_apart(tmp_path) -> None:
    folder = tmp_path / "m"
    (folder / "generated").mkdir(parents=True)
    (folder / "big.bin").write_bytes(b"\0" * (30 * MB))
    (folder / "generated" / "big.bin").write_bytes(b"\0" * (30 * MB))
    assert call("walk.mjs", "walkModelDir", str(folder))["ok"] is True


def test_likec4_source_in_generated_is_refused(tmp_path) -> None:  # AC-7
    repo = make_repo(tmp_path)
    areas = repo / "docs" / "architecture" / "generated" / "areas"
    areas.mkdir(parents=True)
    (areas / "x.c4").write_text("model {\n}\n", encoding="utf-8")
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: model-error: generated/areas/x.c4 is a LikeC4 source file in the generated folder",
    ]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_delta_views.py -k generated`. Expected: FAIL (`model-size` on the first export; no refusal of `x.c4`).
- [ ] **Step 3: GREEN.** Replace `walkModelDir` with:

```js
const GENERATED = 'generated';
const SOURCE = /\.(c4|likec4)$/i;

// Spec (docs): the `generated` folder at the model folder's root counts toward its own limits, and holds no LikeC4 source.
export function walkModelDir(dir) {
  const zones = { model: { files: 0, bytes: 0, label: '' }, generated: { files: 0, bytes: 0, label: `${GENERATED}: ` } };
  const pending = [dir];
  while (pending.length > 0) {
    const current = pending.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const full = path.join(current, entry.name);
      const rel = path.relative(dir, full);
      if (entry.isSymbolicLink()) throw new ToolError('model-symlink', `${rel} is a link`);
      if (CONFIG_NAME.test(entry.name)) throw new ToolError('model-config', `${rel} is a likec4 config file`);
      if (entry.isDirectory()) {
        pending.push(full);
        continue;
      }
      const parts = rel.split(path.sep);
      const zone = parts.length > 1 && parts[0] === GENERATED ? zones.generated : zones.model;
      if (zone === zones.generated && SOURCE.test(entry.name)) {
        throw new ToolError('model-error', `${parts.join('/')} is a LikeC4 source file in the generated folder`);
      }
      zone.files += 1;
      if (zone.files > MODEL_FILE_LIMIT) throw new ToolError('model-size', `${zone.label}more than ${MODEL_FILE_LIMIT} files`);
      zone.bytes += fs.statSync(full).size;
      if (zone.bytes > MODEL_BYTES_LIMIT) throw new ToolError('model-size', `${zone.label}more than 50 MB in total`);
    }
  }
}
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_delta_views.py tests/scripts/test_architecture_delta_model.py tests/scripts/test_architecture_delta_safety.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta/walk.mjs tests/scripts/test_architecture_delta_views.py && git commit -m "feat(#32): the model walk counts the generated folder apart"`

### Task 6: standards line and amendment notes

**Tier:** fast — docs only.

**Files:**
- Modify: `skills/defining-architecture/ARCH_STANDARDS.md` (delta tool flags list)
- Modify: `docs/superpowers/specs/2026-11-17-architecture-model-records-design.md`, `docs/superpowers/specs/2026-11-16-architecture-delta-runtime-links-design.md`, `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md` (one note each, after the first paragraph)

**Callers that move with this task:** none.

- Satisfies Spec AC: none (Scope items)
- **Test retention:** n/a

- [ ] **Step 1:** In `ARCH_STANDARDS.md`, after the line starting "- `export` also prints the model's records", add:

```markdown
- `export` prints format 4: element and relationship titles, the area views (`view area-<name>`, an element view) and the capability views (`dynamic view capability-<name>`, each step following a relationship). A bad area or capability view is `model-error`, and a record's `capabilities` must name capability views.
```

- [ ] **Step 2:** Add the notes:
  - records spec: `> Amended by \`2026-11-17-architecture-docs-design.md\`: \`capabilities\` entries name capability views, checked in pass 4.`
  - runtime-links spec: `> Amended by \`2026-11-17-architecture-docs-design.md\`: \`export\` is format 4, with titles on \`allowed\` and \`runtime\` entries.`
  - delta tool spec: `> Amended by \`2026-11-17-architecture-docs-design.md\`: the \`generated\` folder counts toward its own limits and may hold no LikeC4 source file.`
- [ ] **Step 3: Verify.** `rg -n "format 4" skills/defining-architecture/ARCH_STANDARDS.md` and `rg -n "Amended by .2026-11-17-architecture-docs-design" docs/superpowers/specs`. Expected: one line, then three lines. Then `uv run pytest -q`. Expected: PASS.
- [ ] **Step 4:** `git add skills/defining-architecture/ARCH_STANDARDS.md docs/superpowers/specs && git commit -m "docs(#32): format 4 in the standards; amendment notes"`
