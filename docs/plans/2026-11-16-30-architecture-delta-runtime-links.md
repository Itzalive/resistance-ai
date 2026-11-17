# Architecture Delta Runtime Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The delta tool treats only `uses` (or kindless) relationships as permitting imports, and exports every other kind as a runtime link.

**Architecture:** This repository has no architecture model. The loader (`model.mjs`) classifies each relationship by kind and returns import relationships and runtime links as two lists. The comparison (`match.mjs`) is not changed: it keeps reading `relationships`, which now holds import relationships only. The report (`report.mjs`) adds the `runtime` list to `export` and raises `format` to 2.

**Tech Stack:** Node ESM (standard library and `likec4` 1.60.0), tests in Python with pytest calling the tool as a subprocess.

**Spec:** `docs/superpowers/specs/2026-11-16-architecture-delta-runtime-links-design.md` — decisions applied: none (the spec has no decision register).

**Open decisions:** none

**Size:** 3 tasks, 2 entry paths (`check`, `export`), 446 lines (reported, not a target)

**Trust boundary:** unchanged. The model folder is already read as untrusted input; the one new value read from it, a relationship's kind, is printed through the existing output cleaning and interpreted nowhere.

### Risk & Confidence Assessment

**Confidence:** 95% — the loader is the only place relationships enter, the scratch runs in the spec's assumptions show what LikeC4 returns, and existing tests never assert the loader's whole return value.

**Complexity Risk:** Low — one branch in one loop of the loader and one added list in the export function; no caller changes its call.

**Environmental Risk:** Low — the tests need Node and `node_modules/likec4`, already installed in this worktree by `npm ci --ignore-scripts` (242 delta tests passing before the change).

**Main failure modes:** a runtime link still reaching the permission set (caught by AC-1 and AC-6 tests); the loader rejecting a relationship with no `kind` key, which every existing LikeC4 stand-in returns (caught by the existing model and check tests).

---

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/`, `docs/` with `grep -rn "exportJson\|loadModel\|load_model(\|\.relationships\b"` and `grep -rn "format\|allowed" tests/scripts/*.py skills --include=*.md`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `loadModel` returns `{elements, relationships}` → `{elements, relationships, runtime}`; `relationships` holds import relationships only | `skills/shared/scripts/architecture-delta.mjs:50` | caller | 1 | none: passes the object through as `model` |
| same | `skills/shared/scripts/architecture-delta/match.mjs:34` reads `model.relationships` | caller | 1 | none: now receives import relationships only, which is the behaviour change |
| same | `tests/scripts/arch_delta_support.py:100` `load_model` | test helper | 1 | none: returns the object as JSON |
| same | `tests/scripts/test_architecture_delta_model.py:108-119` reads `["relationships"]` only | assert | 1 | none |
| same | `tests/scripts/test_architecture_delta_match.py` `compare(...)` builds `{elements, relationships}` by hand | test helper | 1 | none: `match.mjs` does not read `runtime` |
| `exportJson` output gains `runtime`, `format` 1 → 2 | `tests/scripts/test_architecture_delta_export.py:22` | assert | 2 | `assert list(data) == ["format", "elements", "allowed", "runtime"]` |
| same | `tests/scripts/test_architecture_delta_export.py:23` | assert | 2 | `assert data["format"] == 2` |
| same | `tests/scripts/test_architecture_delta_export.py:44` | assert | 2 | `assert json.loads(proc.stdout) == {"format": 2, "elements": [], "allowed": [], "runtime": []}` |
| same | `tests/scripts/test_architecture_delta_export.py:182` | assert | 2 | `assert json.loads(proc.stdout)["format"] == 2` |
| same | `skills/defining-architecture/ARCH_REVIEW_MANIFEST.md:20` "from `export`'s relationships" | doc | 3 | see Task 3 |
| same | `skills/writing-plans/SKILL.md:196` reads elements' `code` from `export` | doc | — | none: `elements` is unchanged |
| "not yet reached" covers import relationships only | `skills/defining-architecture/ARCH_STANDARDS.md:28` | doc | 3 | see Task 3 |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 items 1–3, Task 2 items 1–2, Task 3 item 1; full suite `uv run pytest -q tests/scripts` (Task 1 changes what every `check` run permits) |

---

### Task 1: the loader classifies relationships by kind

**Tier:** standard — complete code is given, but the change decides what every `check` run permits.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/model.mjs` (the relationships loop at the end of `loadModel`)
- Create: `tests/scripts/test_architecture_delta_runtime_links.py`

**Callers that move with this task:** none need an edit (sweep rows 1–5).

**Reviewer looks at:**
- which kinds count as import relationships — mutation: treat every kind as an import relationship (push to `relationships` unconditionally) — killed by: `test_import_with_only_a_runtime_link_is_a_new_breach`
- exact comparison of the kind name — mutation: compare `kind.toLowerCase()` with `uses` — killed by: `test_kind_name_is_compared_exactly`
- accepted shapes of `kind` — mutation: drop the shape check — killed by: `test_bad_kind_from_likec4_is_internal`

- Satisfies Spec AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-11, AC-12
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: write the RED tests.** Create `tests/scripts/test_architecture_delta_runtime_links.py`:

```python
"""Runtime links: only `uses` (or kindless) relationships permit imports (issue #30)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_delta_support import error_lines, load_model, make_repo, make_shim, require_node, run_tool, write_json

require_node()


def model(*relationships: str, kinds: tuple[str, ...] = ("http",), extra: str = "") -> str:
    """Components a, b, c, d with code app.a .. app.d, the given kinds declared, and the given relationships."""
    spec = "specification {\n" + "".join(f"  relationship {k}\n" for k in kinds) + "}\n" if kinds else ""
    parts = "".join(
        f"  {name} = component '{name.upper()}' {{\n    metadata {{\n      code 'app.{name}'\n    }}\n  }}\n" for name in "abcd"
    )
    return spec + "model {\n" + parts + extra + "".join(f"  {r}\n" for r in relationships) + "}\n"


def check(repo: Path, edges: list[list[str]]) -> tuple[int, dict]:
    deps = write_json(repo / "deps.json", {"edges": edges})
    proc = run_tool("check", "--repo", repo, "--deps", deps, "--format", "json")
    assert proc.returncode in (0, 1), proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def breaches(data: dict) -> list[tuple[str, str, str]]:
    return [(b["from"], b["to"], b["gap"]) for b in data["breaches"]]


def test_import_with_only_a_runtime_link_is_a_new_breach(tmp_path) -> None:  # AC-1
    code, data = check(make_repo(tmp_path, model("a -[http]-> b")), [["app.a.x", "app.b.y"]])
    assert breaches(data) == [("a", "b", "new")]
    assert code == 1


def test_that_breach_is_known_when_the_gap_file_lists_it(tmp_path) -> None:  # AC-2
    repo = make_repo(tmp_path, model("a -[http]-> b"))
    write_json(repo / "docs" / "architecture" / "known-gap.json", {"entries": [{"from": "a", "to": "b", "reason": "r"}]})
    code, data = check(repo, [["app.a.x", "app.b.y"]])
    assert breaches(data) == [("a", "b", "known")]
    assert code == 0


def test_runtime_link_is_never_not_yet_reached(tmp_path) -> None:  # AC-3
    code, data = check(make_repo(tmp_path, model("a -[http]-> b")), [["app.c.x", "os"]])
    assert data["not_yet_reached"] == []
    assert code == 0


def test_kindless_and_uses_relationships_both_permit_imports(tmp_path) -> None:  # AC-4
    text = model("a -> b", "c -[uses]-> d")
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "app.b.y"], ["app.c.x", "app.d.y"]])
    assert data["breaches"] == [] and data["not_yet_reached"] == []
    assert code == 0
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "os"]])
    assert data["not_yet_reached"] == [{"from": "a", "to": "b"}, {"from": "c", "to": "d"}]


def test_import_relationship_beside_a_runtime_link_permits(tmp_path) -> None:  # AC-5
    code, data = check(make_repo(tmp_path, model("a -> b", "a -[http]-> b")), [["app.a.x", "app.b.y"]])
    assert data["breaches"] == []
    assert code == 0


PROTECTED = """  r = component 'R' {
    metadata {
      code 'app.r'
    }
    p = component 'P' {
      #protected
      metadata {
        code 'app.r.p'
      }
    }
  }
"""


def test_runtime_link_into_a_protected_element_does_not_open_it(tmp_path) -> None:  # AC-6
    text = model("a -> r", "a -[http]-> r.p", extra=PROTECTED)
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "app.r.p.y"]])
    assert breaches(data) == [("a", "r.p", "new")]
    assert code == 1


def test_kind_name_is_compared_exactly(tmp_path) -> None:  # AC-12
    text = model("a -[Uses]-> b", kinds=("Uses",))
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "app.b.y"]])
    assert breaches(data) == [("a", "b", "new")]


def test_loader_returns_import_relationships_and_runtime_links_apart(tmp_path) -> None:
    repo = make_repo(tmp_path, model("a -> b", "c -[uses]-> d", "a -[http]-> c", "d -[push]-> a", kinds=("http", "push")))
    value = load_model(repo / "docs" / "architecture")["value"]
    assert sorted((r["from"], r["to"]) for r in value["relationships"]) == [("a", "b"), ("c", "d")]
    assert sorted((r["from"], r["to"], r["kind"]) for r in value["runtime"]) == [("a", "c", "http"), ("d", "a", "push")]
    assert all(set(r) == {"from", "to"} for r in value["relationships"])


KIND_SHIM = """const E = (id) => ({ id, kind: 'component', tags: [], getMetadata() { return {}; } });
export class LikeC4 {
  static async fromWorkspace() {
    return {
      getErrors() { return []; },
      async computedModel() {
        return { elements() { return [E('a'), E('b')]; }, relationships() { return [RELATIONSHIP]; } };
      },
    };
  }
}
"""


def export_with(tmp_path: Path, relationship: str):
    repo = make_repo(tmp_path, None)
    make_shim(repo / "node_modules", source=KIND_SHIM.replace("RELATIONSHIP", relationship))
    return run_tool("export", "--repo", repo)


@pytest.mark.parametrize("kind", ["5", "''", "{}", "['uses']"])
def test_bad_kind_from_likec4_is_internal(tmp_path, kind: str) -> None:  # AC-11, first half
    proc = export_with(tmp_path, f"{{ source: {{ id: 'a' }}, target: {{ id: 'b' }}, kind: {kind} }}")
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: internal: ")
    assert proc.stdout == ""


@pytest.mark.parametrize("relationship", [
    "{ source: { id: 'a' }, target: { id: 'b' } }",
    "{ source: { id: 'a' }, target: { id: 'b' }, kind: null }",
    "{ source: { id: 'a' }, target: { id: 'b' }, kind: undefined }",
])
def test_missing_or_null_kind_is_an_import_relationship(tmp_path, relationship: str) -> None:  # AC-11, second half
    proc = export_with(tmp_path, relationship)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["allowed"] == [{"from": "a", "to": "b"}]
```

- [ ] **Step 2: run the RED tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_runtime_links.py`
Expected: FAIL. `test_import_with_only_a_runtime_link_is_a_new_breach`, `test_that_breach_is_known_when_the_gap_file_lists_it` (gap entry stale, exit 1), `test_runtime_link_is_never_not_yet_reached`, `test_runtime_link_into_a_protected_element_does_not_open_it`, `test_kind_name_is_compared_exactly`, `test_loader_returns_import_relationships_and_runtime_links_apart` (`KeyError: 'runtime'`) and the four `test_bad_kind_from_likec4_is_internal` cases fail. `test_kindless_and_uses_relationships_both_permit_imports`, `test_import_relationship_beside_a_runtime_link_permits` and the three `test_missing_or_null_kind_is_an_import_relationship` cases already pass: they pin behaviour that must not change.

- [ ] **Step 3: write the implementation.** In `skills/shared/scripts/architecture-delta/model.mjs`, add below `export const ELEMENT_LIMIT = 5000;`:

```js
// A relationship of this kind, or with no kind, permits imports. Any other kind is a runtime link.
export const IMPORT_KIND = 'uses';
```

and replace the relationships loop and the return at the end of `loadModel` (from `const relationships = [];` to `return { elements, relationships };`) with:

```js
  const relationships = [];
  const runtime = [];
  for (const relationship of computed.relationships()) {
    if (typeof relationship?.source?.id !== 'string' || typeof relationship?.target?.id !== 'string') {
      throw shapeError('a relationship without string source and target ids');
    }
    const kind = relationship.kind ?? null;
    if (kind !== null && (typeof kind !== 'string' || kind === '')) {
      throw shapeError('a relationship whose kind is not a non-empty string');
    }
    const pair = { from: relationship.source.id, to: relationship.target.id };
    if (kind === null || kind === IMPORT_KIND) relationships.push(pair);
    else runtime.push({ ...pair, kind });
  }
  validatePrefixes(elements);
  return { elements, relationships, runtime };
```

Also change the file's first comment line to: `// Loads a model folder with likec4, checks the shape of what likec4 returns, validates code prefixes, and splits relationships into import relationships and runtime links.`

- [ ] **Step 4: run the task's tests and every test that reaches the loader.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_runtime_links.py tests/scripts/test_architecture_delta_model.py tests/scripts/test_architecture_delta_check.py tests/scripts/test_architecture_delta_match.py tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_safety.py`
Expected: PASS (every test in the new file; no existing test changed).

- [ ] **Step 5: refactor.** Nothing to restructure: the change is one branch. Confirm the loader's first comment line was updated as step 3 says, and rerun the command of step 4. Expected: PASS.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/model.mjs tests/scripts/test_architecture_delta_runtime_links.py
git commit -m "feat(#30): only uses relationships permit imports; other kinds are runtime links"
```

### Task 2: `export` lists runtime links

**Tier:** fast — complete code and literal edits are given.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/report.mjs` (`exportJson`)
- Modify: `tests/scripts/test_architecture_delta_export.py:22,23,44,182`
- Test: `tests/scripts/test_architecture_delta_runtime_links.py` (append)

**Callers that move with this task:** `tests/scripts/test_architecture_delta_export.py:22`, `:23`, `:44`, `:182` (sweep rows 6–9).

**Reviewer looks at:**
- one entry per pair and kind — mutation: dedupe `runtime` by pair only — killed by: `test_export_lists_runtime_links_once_per_pair_and_kind`
- `runtime` is kept out of `allowed` — mutation: build `allowed` from `[...model.relationships, ...model.runtime]` — killed by: `test_runtime_links_in_both_directions_are_exported_and_not_allowed`

- Satisfies Spec AC: AC-7, AC-8, AC-9, AC-10
- Decisions applied: none
- **Test retention:** **Permanent**

- [ ] **Step 1: write the RED tests.** Append to `tests/scripts/test_architecture_delta_runtime_links.py`:

```python
def export(repo: Path) -> dict:
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_export_lists_runtime_links_once_per_pair_and_kind(tmp_path) -> None:  # AC-7
    text = model(
        "a -> b", "c -[uses]-> d", "c -[push]-> a", "a -[http]-> b 'one'", "a -[http]-> b 'two'", "a -[calls]-> b",
        kinds=("http", "push", "calls"),
    )
    data = export(make_repo(tmp_path, text))
    assert list(data) == ["format", "elements", "allowed", "runtime"]
    assert data["format"] == 2
    assert data["allowed"] == [{"from": "a", "to": "b"}, {"from": "c", "to": "d"}]
    assert data["runtime"] == [
        {"from": "a", "to": "b", "kind": "calls"}, {"from": "a", "to": "b", "kind": "http"},
        {"from": "c", "to": "a", "kind": "push"},
    ]


def test_runtime_links_in_both_directions_are_exported_and_not_allowed(tmp_path) -> None:  # AC-8
    data = export(make_repo(tmp_path, model("a -[http]-> b", "b -[http]-> a")))
    assert data["runtime"] == [{"from": "a", "to": "b", "kind": "http"}, {"from": "b", "to": "a", "kind": "http"}]
    assert data["allowed"] == []


def test_long_kind_name_is_cleaned(tmp_path) -> None:  # AC-9
    kind = "k" * 201
    data = export(make_repo(tmp_path, model(f"a -[{kind}]-> b", kinds=(kind,))))
    assert data["runtime"] == [{"from": "a", "to": "b", "kind": "k" * 199 + "…"}]


def test_export_without_runtime_links_has_an_empty_list(tmp_path) -> None:  # AC-10
    assert export(make_repo(tmp_path, model("a -> b", kinds=())))["runtime"] == []
```

- [ ] **Step 2: run the RED tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_runtime_links.py -k "export_lists or both_directions or long_kind or without_runtime"`
Expected: FAIL, 4 failed: `test_export_lists_runtime_links_once_per_pair_and_kind` on the key list, the other three with `KeyError: 'runtime'`.

- [ ] **Step 3: write the implementation.** In `skills/shared/scripts/architecture-delta/report.mjs`, add below `uniquePairs`:

```js
const byLink = (x, y) => byPair(x, y) || cmp(x.kind, y.kind);

// One entry per pair and kind. Links are compared raw, before cleaning.
function uniqueLinks(list) {
  const seen = new Set();
  return list.filter((link) => {
    const key = `${link.from}\u0000${link.to}\u0000${link.kind}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
```

and in `exportJson` change `format: 1,` to `format: 2,` and add after the `allowed:` line:

```js
    runtime: uniqueLinks(model.runtime).sort(byLink).map((link) => ({ ...cleanPair(link), kind: clean(link.kind) })),
```

- [ ] **Step 4: make the four literal edits in `tests/scripts/test_architecture_delta_export.py`** (sweep rows 6–9):

```python
    assert list(data) == ["format", "elements", "allowed", "runtime"]      # line 22
    assert data["format"] == 2                                              # line 23
    assert json.loads(proc.stdout) == {"format": 2, "elements": [], "allowed": [], "runtime": []}   # line 44
    assert json.loads(proc.stdout)["format"] == 2                           # line 182
```

- [ ] **Step 5: run the task's tests and the moved callers' tests.**

Run: `uv run pytest -q tests/scripts/test_architecture_delta_runtime_links.py tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_safety.py`
Expected: PASS.

- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/report.mjs tests/scripts/test_architecture_delta_export.py tests/scripts/test_architecture_delta_runtime_links.py
git commit -m "feat(#30): export lists runtime links; format 2"
```

### Task 3: documents describe the two sorts of relationship

**Tier:** fast — docs only; every edit is literal.

**Files:**
- Modify: `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md` (after line 3; line 283)
- Modify: `skills/defining-architecture/ARCH_STANDARDS.md` (delta tool flags)
- Modify: `skills/defining-architecture/ARCH_REVIEW_MANIFEST.md:20`

**Callers that move with this task:** sweep rows 10 and 12.

**Reviewer looks at:**
- the manifest's cycle check names the right list — mutation: none (docs); checked by reading — killed by: the grep in step 3

**Pinned by:** `tests/scripts/test_defining_architecture_contract.py` reads `ARCH_STANDARDS.md` and `ARCH_REVIEW_MANIFEST.md`; step 3 runs it to show the wording edits break no pinned text.

- Satisfies Spec AC: none (the spec's "Documents that change")
- Decisions applied: none
- **Test retention:** no new test (docs-only branch)

- [ ] **Step 1: RED — show the old wording is there.**

Run: `grep -n "relationship kinds that withhold permission" docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md; grep -n "a relationship the code doesn't have yet" skills/defining-architecture/ARCH_STANDARDS.md; grep -n "from \`export\`'s relationships" skills/defining-architecture/ARCH_REVIEW_MANIFEST.md; grep -c "runtime link" skills/defining-architecture/ARCH_STANDARDS.md`
Expected: one match for each of the first three (line 283 for the first; the future-work row at line 437 starts with a capital R and does not match), and `0` for the last.

- [ ] **Step 2: GREEN — make the edits.**

In `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md`, insert after line 3 (`Work item: #20 …`):

```markdown

> Amended by `2026-11-16-architecture-delta-runtime-links-design.md` (#30): that spec replaces the "Allowed", "`#protected`" and "Reported" rules below where they say "any relationship", the API-shape rule for what LikeC4 returns (a relationship's `kind`), and the `export` shape. Only relationships of kind `uses`, or with no kind, permit imports; other kinds are runtime links.
```

and in its "Out of scope" paragraph replace `relationship kinds that withhold permission; mutation tooling (#27).` with `mutation tooling (#27).`

In `skills/defining-architecture/ARCH_STANDARDS.md`, replace

```markdown
- The `check` sections: new breaches, known breaches, not yet reached (a relationship the code doesn't have yet), unmapped code, and the summary line `N new, N stale, N known`. Quote the whole output in the decision log.
```

with

```markdown
- Only a relationship of kind `uses`, or with no kind, permits imports. A relationship of any other kind is a runtime link: `check` ignores it, and `export` lists it under `runtime`.
- The `check` sections: new breaches, known breaches, not yet reached (an import relationship the code doesn't have yet), unmapped code, and the summary line `N new, N stale, N known`. Quote the whole output in the decision log.
```

In `skills/defining-architecture/ARCH_REVIEW_MANIFEST.md` line 20, replace `Build the reachability graph from `export`'s relationships.` with `Build the reachability graph from `export`'s `allowed` list (import relationships; runtime links are not part of it).`

- [ ] **Step 3: rerun the checks and the contract tests.**

Run: `grep -c "relationship kinds that withhold permission" docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md; grep -c "runtime link" skills/defining-architecture/ARCH_STANDARDS.md; grep -c "allowed. list" skills/defining-architecture/ARCH_REVIEW_MANIFEST.md; uv run pytest -q tests/scripts/test_defining_architecture_contract.py tests/test_repo_layout.py`
Expected: `0` (the future-work table row at line 437 stays, as history of the earlier spec, and does not match the lower-case pattern), `1`, `1`, then PASS.

- [ ] **Step 4: commit.**

```bash
git add docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md skills/defining-architecture/ARCH_STANDARDS.md skills/defining-architecture/ARCH_REVIEW_MANIFEST.md
git commit -m "docs(#30): standards, manifest and delta tool spec name import relationships and runtime links"
```

- [ ] **Step 5: full suite.**

Run: `uv run pytest -q`
Expected: PASS.
