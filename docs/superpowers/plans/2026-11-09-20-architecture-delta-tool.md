# Architecture delta tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `skills/shared/scripts/architecture-delta.mjs` with its `check` and `export` commands, the shipped C4 specification and the `likec4` 1.60.0 pin, as specified.

**Architecture:** A thin CLI (`architecture-delta.mjs`) over small ES modules in `skills/shared/scripts/architecture-delta/`: error and cleaning helpers, argument parsing, `likec4` location and loading, a model-folder walk, model loading with shape checks, input-file parsing, the matching engine and report rendering. Pure modules are unit-tested by running short ES module snippets with Node from pytest; the commands are tested end to end as subprocesses.

**Tech Stack:** Node 24 (plain ESM, standard library), `likec4` 1.60.0, Python 3.12 with pytest under `uv run pytest -q`.

**Spec:** `docs/superpowers/specs/2026-11-09-architecture-delta-tool-design.md` — decisions applied: none (the spec has no decision register; every rule cited below is from its sections)

**Open decisions:** none

**Size:** 12 tasks, 2 entry paths (`check`, `export`), 2,834 lines (reported, not a target). The owner chose one plan over the proposed two-plan split.

**Trust boundary:** changed — see Trust-boundary table

### Risk & Confidence Assessment

**Confidence:** 85% — every `likec4` call the plan uses was run against 1.60.0 in scratch installs; the remaining risk is test runtime and Windows path behaviour.

**Complexity Risk:** Medium — the matching rules (ancestors, `#protected`, scope, gap staleness) interact; Tasks 9 and 10 carry them with full code and threshold tests.

**Environmental Risk:** Medium — tests create junctions or symlinks and multi-megabyte files on Windows, and load a 5,000-element model through `likec4`.

**Main failure modes:** a test that creates a link fails without symlink rights (the helper falls back to a junction); the 5,000-element load is slow; `path.relative` case handling on Windows paths; `npm install` rewriting `package.json` formatting.

**Unknown variables:**
- How long `likec4` takes to load 5,000 and 5,001 elements (Task 6). If one load exceeds 120 s, the executor stops and reports; the cap test may move to a generated model with fewer files but the same element count.
- Whether `npm install --save-exact` keeps `package.json` key order; Task 1 diffs it and restores order by hand if needed.

---

## Caller and test sweep

Searched: `skills/`, `tests/`, `scripts/`, `.claude-plugin/`, `docs/` (no runnable code) with
`rg -n "package.json|node_modules|dependencies|gitignore|gitattributes" skills tests scripts .claude-plugin`
and `rg -n "architecture-delta|c4\.c4" skills tests scripts`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `package.json` gains `dependencies` | `tests/test_pi_package.py::test_package_json_exposes_pi_skills_manifest` reads `pi.skills` and `keywords` | test | 1 | none (keys unchanged) |
| same | `scripts/bump_version.py:22-29` `_json_top` rewrites the first `  "version": "…"` line | caller | 1 | none (the top-level `version` stays the first line at two-space indent) |
| new `package-lock.json` | `scripts/bump_version.py:64-70` `TARGETS` mapping | caller | 1 | none (`npm ci --ignore-scripts --dry-run` accepts a lockfile root `version` that differs from `package.json`, checked in a scratch install) |
| `.gitignore` gains `node_modules/` | none found | — | 1 | — |
| new `skills/shared/…` files | `tests/test_pi_package.py::test_skills_root_has_no_top_level_markdown_helpers` asserts no top-level `skills/*.md` | test | 1 | none (no file added at `skills/` top level) |

Nothing else references `architecture-delta` or `c4.c4` today.

## Trust-boundary table

Untrusted source throughout: the content of the repository under `--repo` (its files, its
`node_modules`, and the dependency file its overlay command writes).

| Producer or reader | Where it is used | Text it receives | Task | Proving test |
|---|---|---|---|---|
| `locateLikeC4()` / `importLikeC4()` | dynamic `import()` of code | `<repo>/node_modules/likec4` and its `package.json` entry | 4 | `tests/scripts/test_architecture_delta_likec4.py::test_parent_folders_are_never_searched`, `::test_entry_outside_the_copy_is_internal`, `::test_repo_copy_that_resolves_outside_the_repo_is_not_used` |
| `walkModelDir()` before `LikeC4.fromWorkspace` | `likec4` loader, which executes config files | model folder file names and links | 5, 8 | `tests/scripts/test_architecture_delta_model.py::test_config_file_at_any_depth_is_refused`, `tests/scripts/test_architecture_delta_export.py::test_export_refuses_config_and_never_runs_it` |
| `resolveInside()` | file paths read | `--model`, `--deps`, `--gap`, `--shards` values | 7, 11 | `tests/scripts/test_architecture_delta_inputs.py::test_path_through_a_link_outside_is_refused`, `tests/scripts/test_architecture_delta_check.py::test_deps_through_a_link_outside_is_refused` |
| `readJson()`, `parseDeps()`, `parseGap()`, `parseShards()` | JSON parser whose output drives the comparison | dependency, gap and shards files | 7 | `tests/scripts/test_architecture_delta_inputs.py::test_deps_shape_errors`, `::test_gap_shape_errors`, `::test_shards_shape_errors` |
| `loadModel()` shape check | values that drive matching | whatever `likec4` (possibly a repository copy) returns | 6, 11 | `tests/scripts/test_architecture_delta_model.py::test_unexpected_api_shapes_are_internal`, `tests/scripts/test_architecture_delta_check.py::test_bad_shape_shim_exits_internal` |
| `clean()` in `errorLines()`, `exportJson()`, `checkJson()`, `checkText()` | stdout and stderr read by agents | ids, module names, tags, metadata, error messages | 2, 8, 11 | `tests/scripts/test_architecture_delta_errors.py::test_clean_removes_ansi_sequences_first`, `tests/scripts/test_architecture_delta_check.py::test_printed_strings_are_cleaned` |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 items 1–2, Task 2 items 1–3, Task 3 items 1–3; focused tests |
| C2 | 6 | 4–6 | Task 4 items 1–4, Task 5 items 1–3, Task 6 items 1–3; trust-boundary rows 1, 2, 5; focused tests |
| C3 | 9 | 7–9 | Task 7 items 1–3, Task 8 items 1–3, Task 9 items 1–4; trust-boundary rows 3, 4; full suite (Task 8 is the first end-to-end task) |
| C4 | 12 | 10–12 | Task 10 items 1–3, Task 11 items 1–4, Task 12 items 1–3; trust-boundary row 6; full suite |

---

### Task 1: Pin `likec4`, ship the C4 specification, add the test support module

**Tier:** fast — every edit and command is written out.

**Files:**
- Modify: `package.json` (add `dependencies`)
- Create: `package-lock.json` (generated by npm)
- Modify: `.gitignore`
- Create: `.gitattributes`
- Create: `skills/shared/architecture/c4.c4`
- Create: `tests/scripts/arch_delta_support.py`
- Test: `tests/scripts/test_architecture_delta_packaging.py`

**Callers that move with this task:** none (sweep rows for `package.json`, `package-lock.json` and `.gitignore` need no edit; `tests/test_pi_package.py` must still pass).

**Reviewer looks at:**
- lockfile pin — mutation: change `"likec4": "1.60.0"` to `"^1.60.0"` in `package.json` — killed by: `tests/scripts/test_architecture_delta_packaging.py::test_lockfile_pins_likec4_exactly`
- shipped spec content — mutation: delete `tag protected` from `c4.c4` — killed by: `tests/scripts/test_architecture_delta_packaging.py::test_shipped_spec_declares_the_c4_kinds_and_tags`

- Satisfies Spec AC: none directly (Scope: exact pin, lockfile version 3, installed version, `.gitignore`, `.gitattributes`, session check that fails rather than skips)
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write the support module and the RED tests.**

`tests/scripts/arch_delta_support.py`:

```python
"""Shared helpers for the architecture-delta tests: paths, Node runners and fixture builders."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]
SCRIPT = ENGINE / "skills" / "shared" / "scripts" / "architecture-delta.mjs"
LIB = ENGINE / "skills" / "shared" / "scripts" / "architecture-delta"
SHIPPED_SPEC = ENGINE / "skills" / "shared" / "architecture" / "c4.c4"
LIKEC4_DIR = ENGINE / "node_modules" / "likec4"
LIKEC4_ENTRY = LIKEC4_DIR / "dist" / "index.mjs"
FIXTURES = ENGINE / "tests" / "fixtures" / "architecture"

SHOP_MODEL = """model {
  shop = system 'Shop' {
    orders = container 'Orders' {
      metadata {
        code 'shop.orders'
      }
      api = component 'Orders API' {
        metadata {
          code 'shop.orders.api'
        }
      }
    }
    checkout = container 'Checkout' {
      metadata {
        code 'shop.checkout'
      }
    }
    payments = container 'Payments' {
      #protected
      metadata {
        code 'shop.payments'
      }
      card = component 'Card' {
        metadata {
          code 'shop.payments.card'
        }
      }
    }
    orders -> checkout
    checkout -> payments
  }
}
"""


def require_node() -> None:
    """Fail (never skip) when Node or the pinned likec4 install is missing."""
    if shutil.which("node") is None or not (LIKEC4_DIR / "package.json").is_file():
        raise RuntimeError(
            "architecture-delta tests need Node and node_modules/likec4: run `npm ci --ignore-scripts`"
        )


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def run_module(code: str) -> subprocess.CompletedProcess[str]:
    """Run an ES module snippet written to a temporary file (no command-line length limit)."""
    with tempfile.TemporaryDirectory() as folder:
        snippet = Path(folder) / "snippet.mjs"
        snippet.write_text(code, encoding="utf-8")
        return subprocess.run(
            ["node", str(snippet)], capture_output=True, text=True, encoding="utf-8", timeout=600
        )


def lib_url(module: str) -> str:
    return (LIB / module).as_uri()


def call(module: str, fn: str, *args: object) -> dict:
    """Call an exported function of a tool module; return {ok, value} or {ok, token, details, message}."""
    code = (
        f"import * as m from {json.dumps(lib_url(module))};\n"
        f"const args = {json.dumps(list(args))};\n"
        "try {\n"
        f"  const out = await m.{fn}(...args);\n"
        "  process.stdout.write(JSON.stringify({ ok: true, value: out === undefined ? null : out }));\n"
        "} catch (err) {\n"
        "  process.stdout.write(JSON.stringify({ ok: false, token: err.token ?? null,"
        " details: err.details ?? null, message: String(err.message) }));\n"
        "}\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def load_model(model_dir: Path, entry: Path = LIKEC4_ENTRY) -> dict:
    """Run model.mjs loadModel with the LikeC4 class from `entry`."""
    code = (
        f"import {{ LikeC4 }} from {json.dumps(entry.as_uri())};\n"
        f"import {{ loadModel }} from {json.dumps(lib_url('model.mjs'))};\n"
        "try {\n"
        f"  const out = await loadModel(LikeC4, {json.dumps(str(model_dir))});\n"
        "  process.stdout.write(JSON.stringify({ ok: true, value: out }));\n"
        "} catch (err) {\n"
        "  process.stdout.write(JSON.stringify({ ok: false, token: err.token ?? null,"
        " details: err.details ?? null, message: String(err.message) }));\n"
        "}\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def run_tool(
    *args: object, preload: Path | None = None, script: Path = SCRIPT, timeout: int = 600
) -> subprocess.CompletedProcess[str]:
    cmd = ["node"]
    if preload is not None:
        cmd += ["--import", preload.as_uri()]
    cmd += [str(script), *[str(a) for a in args]]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)


def error_lines(proc: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in proc.stderr.splitlines() if line.startswith("error: ")]


def make_repo(tmp_path: Path, model: str | None = SHOP_MODEL, *, spec: bool = True) -> Path:
    """A repository folder under tmp_path with architecture/c4.c4 and architecture/model.c4."""
    repo = tmp_path / unique("repo")
    model_dir = repo / "architecture"
    model_dir.mkdir(parents=True)
    if spec:
        shutil.copyfile(SHIPPED_SPEC, model_dir / "c4.c4")
    if model is not None:
        (model_dir / "model.c4").write_text(model, encoding="utf-8")
    return repo


def write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def link_dir(target: Path, link: Path) -> None:
    """A directory symlink, or a junction where symlinks need rights the user lacks."""
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, link, target_is_directory=True)
    except OSError:
        import _winapi  # Windows only: junctions need no special rights

        _winapi.CreateJunction(str(target), str(link))


def copy_engine(dest: Path) -> Path:
    """Copy the tool and the shipped spec into dest/engine with no node_modules; return the script."""
    root = dest / "engine"
    shutil.copytree(LIB, root / "skills" / "shared" / "scripts" / "architecture-delta")
    shutil.copyfile(SCRIPT, root / "skills" / "shared" / "scripts" / "architecture-delta.mjs")
    (root / "skills" / "shared" / "architecture").mkdir(parents=True)
    shutil.copyfile(SHIPPED_SPEC, root / "skills" / "shared" / "architecture" / "c4.c4")
    return root / "skills" / "shared" / "scripts" / "architecture-delta.mjs"


def make_shim(node_modules: Path, version: object = "1.59.0", source: str | None = None,
              package: dict | None = None) -> Path:
    """A fake likec4 package; by default it re-exports the engine's installed copy."""
    pkg = node_modules / "likec4"
    pkg.mkdir(parents=True)
    manifest = package if package is not None else {
        "name": "likec4", "version": version, "exports": {".": {"import": "./index.mjs"}}
    }
    write_json(pkg / "package.json", manifest)
    text = source if source is not None else f"export * from {json.dumps(LIKEC4_ENTRY.as_uri())};\n"
    (pkg / "index.mjs").write_text(text, encoding="utf-8")
    return pkg
```

`tests/scripts/test_architecture_delta_packaging.py`:

```python
from __future__ import annotations

import json
import shutil

from arch_delta_support import ENGINE, LIKEC4_DIR, LIKEC4_ENTRY, SHIPPED_SPEC, require_node, run_module, unique

require_node()


def test_lockfile_pins_likec4_exactly() -> None:
    package = json.loads((ENGINE / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ENGINE / "package-lock.json").read_text(encoding="utf-8"))

    assert package["dependencies"] == {"likec4": "1.60.0"}
    assert lock["lockfileVersion"] == 3
    assert lock["packages"][""]["dependencies"] == {"likec4": "1.60.0"}
    assert lock["packages"]["node_modules/likec4"]["version"] == "1.60.0"


def test_installed_likec4_matches_the_pin() -> None:
    installed = json.loads((LIKEC4_DIR / "package.json").read_text(encoding="utf-8"))

    assert installed["version"] == "1.60.0"


def test_shipped_spec_declares_the_c4_kinds_and_tags() -> None:
    text = SHIPPED_SPEC.read_text(encoding="utf-8")

    for line in (
        "element system", "element container", "element component", "element external",
        "tag protected", "tag generic", "tag layer", "tag eval", "relationship uses",
    ):
        assert f"  {line}\n" in text
    assert "code" in text.split("specification")[0]
    assert "rules" in text.split("specification")[0]


def test_shipped_spec_loads_without_errors(tmp_path) -> None:
    model = tmp_path / unique("model")
    model.mkdir()
    shutil.copyfile(SHIPPED_SPEC, model / "c4.c4")
    code = (
        f"import {{ LikeC4 }} from {json.dumps(LIKEC4_ENTRY.as_uri())};\n"
        f"const lc = await LikeC4.fromWorkspace({json.dumps(str(model))}, {{ logger: false }});\n"
        "process.stdout.write(JSON.stringify(lc.getErrors()));\n"
    )

    proc = run_module(code)

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == []


def test_line_endings_and_ignores() -> None:
    assert "*.c4 text eol=lf" in (ENGINE / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "node_modules/" in (ENGINE / ".gitignore").read_text(encoding="utf-8").splitlines()
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest tests/scripts/test_architecture_delta_packaging.py -q`
Expected: collection error `RuntimeError: architecture-delta tests need Node and node_modules/likec4: run `npm ci --ignore-scripts``

- [ ] **Step 3: GREEN — pin, generate the lockfile, add the spec and the git attributes.**

Run: `npm install --ignore-scripts --save-exact --no-audit --no-fund likec4@1.60.0`
Then: `git diff package.json` — the only change must be a new `"dependencies": { "likec4": "1.60.0" }` block; if npm reordered or reformatted other keys, restore them by hand so only that block is added.

`skills/shared/architecture/c4.c4`:

```
// Shipped C4 specification for resistance-engine architecture models.
// Copy this file unchanged into a repository's model folder; add kinds or tags in other files.
// Element metadata keys read by the architecture delta tool:
//   code  - module prefixes the element owns, comma-separated (for example 'shop.orders, shop.billing')
//   rules - epic business rules the element owns, comma-separated (for example 'BR-1, BR-4')
specification {
  element system
  element container
  element component
  element external
  tag protected
  tag generic
  tag layer
  tag eval
  relationship uses
}
```

Append to `.gitignore` (new last line): `node_modules/`

`.gitattributes`:

```
*.c4 text eol=lf
```

- [ ] **Step 4: run the task's tests and the moved callers' tests.**

Run: `uv run pytest tests/scripts/test_architecture_delta_packaging.py tests/test_pi_package.py -q`
Expected: PASS (5 + 3 tests)

Run: `npm audit --omit=dev --json | python -c "import json,sys;print(json.load(sys.stdin)['metadata']['vulnerabilities'])"`
Expected: the counts print. If `high` or `critical` is above 0, STOP: do not commit; report the advisories to the coordinator for the owner's decision.

- [ ] **Step 5: refactor — none; confirm `git status` shows only the listed files plus `node_modules/` ignored.**

- [ ] **Step 6: commit.** Put the vulnerability counts from Step 4 in the commit body.

```bash
git add package.json package-lock.json .gitignore .gitattributes skills/shared/architecture/c4.c4 tests/scripts/arch_delta_support.py tests/scripts/test_architecture_delta_packaging.py
git commit -m "feat(20): pin likec4 1.60.0 and ship the C4 specification

npm audit (prod): <paste counts>"
```

---

### Task 2: Error type, output cleaning and error lines

**Tier:** fast — complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/errors.mjs`
- Test: `tests/scripts/test_architecture_delta_errors.py`

**Callers that move with this task:** none

**Reviewer looks at:**
- removal order — mutation: remove controls before ANSI sequences (so `ESC` goes first and `[31m` stays) — killed by: `test_clean_removes_ansi_sequences_first`
- the 200 code-point boundary — mutation: `>` to `>=` in the length check — killed by: `test_clean_keeps_exactly_200_code_points`
- code points, not UTF-16 units — mutation: `text.length` instead of `Array.from(text).length` — killed by: `test_clean_counts_code_points`

- Satisfies Spec AC: AC-20 (cleaning rule; end-to-end in Task 11)
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests.**

```python
from __future__ import annotations

import json

from arch_delta_support import call, lib_url, require_node, run_module

require_node()


def clean(text: str) -> str:
    result = call("errors.mjs", "clean", text)
    assert result["ok"], result
    return result["value"]


def test_clean_removes_ansi_sequences_first() -> None:
    assert clean("a\x1b[31mred\x1b[0m b\x1b]0;title\x07c") == "ared bc"


def test_clean_removes_c0_del_c1_and_bidi_controls() -> None:
    assert clean("x\x00y\x7fz\x85w‮q⁦r\n") == "xyzwqr"


def test_clean_keeps_exactly_200_code_points() -> None:
    assert clean("a" * 200) == "a" * 200


def test_clean_cuts_201_code_points_to_199_plus_ellipsis() -> None:
    out = clean("b" * 201)
    assert out == "b" * 199 + "…"
    assert len(out) == 200


def test_clean_counts_code_points() -> None:
    out = clean("\U0001f600" * 201)
    assert out == "\U0001f600" * 199 + "…"


def test_error_lines_clean_each_detail() -> None:
    code = (
        f"import {{ ToolError, errorLines }} from {json.dumps(lib_url('errors.mjs'))};\n"
        "const err = new ToolError('usage', ['bad \\u001b[1mflag', 'second\\nline']);\n"
        "process.stdout.write(JSON.stringify({ token: err.token, lines: errorLines(err) }));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "token": "usage",
        "lines": ["error: usage: bad flag", "error: usage: secondline"],
    }


def test_single_detail_becomes_one_line() -> None:
    code = (
        f"import {{ ToolError, errorLines }} from {json.dumps(lib_url('errors.mjs'))};\n"
        "process.stdout.write(JSON.stringify(errorLines(new ToolError('timeout', 'run exceeded'))));\n"
    )
    proc = run_module(code)
    assert json.loads(proc.stdout) == ["error: timeout: run exceeded"]
```

- [ ] **Step 2: run RED.**

Run: `uv run pytest tests/scripts/test_architecture_delta_errors.py -q`
Expected: FAIL (`Cannot find module …/errors.mjs` in stderr; `assert proc.returncode == 0`)

- [ ] **Step 3: GREEN.** `skills/shared/scripts/architecture-delta/errors.mjs`:

```js
// Error type, output cleaning and error lines for the architecture delta tool.

export class ToolError extends Error {
  constructor(token, details) {
    const list = [].concat(details).map(String);
    super(`${token}: ${list.join('; ')}`);
    this.token = token;
    this.details = list;
  }
}

const ANSI = /\u001b\[[0-?]*[ -\/]*[@-~]|\u001b\][^\u0007\u001b]*(?:\u0007|\u001b\\)?/g;
const CONTROLS = /[\u0000-\u001f\u007f-\u009f‪-‮⁦-⁩]/g;
export const MAX_POINTS = 200;

export function clean(value) {
  const text = String(value).replace(ANSI, '').replace(CONTROLS, '');
  const points = Array.from(text);
  return points.length > MAX_POINTS ? `${points.slice(0, MAX_POINTS - 1).join('')}…` : text;
}

export function errorLines(error) {
  return error.details.map((detail) => `error: ${error.token}: ${clean(detail)}`);
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_errors.py -q` — Expected: PASS (7)
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/errors.mjs tests/scripts/test_architecture_delta_errors.py
git commit -m "feat(20): error type, output cleaning and error lines"
```

---

### Task 3: Argument parsing and usage errors

**Tier:** fast — complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/args.mjs`
- Test: `tests/scripts/test_architecture_delta_args.py`

**Callers that move with this task:** none

**Reviewer looks at:**
- `--timeout` upper bound — mutation: `> 600` to `> 601` — killed by: `test_usage_errors[timeout-601]`
- whole-number check — mutation: regex `^\d+$` to `^[\d.]+$` — killed by: `test_usage_errors[timeout-1.5]`
- flag sets per command — mutation: allow `--deps` for `export` — killed by: `test_usage_errors[deps-on-export]`

- Satisfies Spec AC: AC-25 (parse level; end-to-end in Task 8)
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests.**

```python
from __future__ import annotations

import pytest

from arch_delta_support import call, require_node

require_node()

DEFAULTS = {
    "deps": None, "model": "architecture", "gap": None, "scope": None, "shards": None,
    "separator": ".", "format": "text", "timeout": 60,
}


def parse(argv: list[str]) -> dict:
    return call("args.mjs", "parseArgs", argv)


def test_check_defaults() -> None:
    result = parse(["check", "--repo", "r", "--deps", "d.json"])
    assert result == {"ok": True, "value": {**DEFAULTS, "command": "check", "repo": "r", "deps": "d.json"}}


def test_export_defaults() -> None:
    result = parse(["export", "--repo", "r"])
    assert result == {"ok": True, "value": {**DEFAULTS, "command": "export", "repo": "r"}}


def test_every_check_flag() -> None:
    result = parse([
        "check", "--repo", "r", "--deps", "d", "--model", "m", "--gap", "g", "--scope", "a, b",
        "--shards", "s", "--separator", "/", "--format", "json", "--timeout", "600",
    ])
    assert result["value"] == {
        "command": "check", "repo": "r", "deps": "d", "model": "m", "gap": "g", "scope": ["a", "b"],
        "shards": "s", "separator": "/", "format": "json", "timeout": 600,
    }


def test_timeout_zero_is_valid() -> None:
    assert parse(["export", "--repo", "r", "--timeout", "0"])["value"]["timeout"] == 0


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param([], id="no-command"),
        pytest.param(["nope"], id="unknown-command"),
        pytest.param(["export"], id="missing-repo"),
        pytest.param(["check", "--repo", "r"], id="missing-deps"),
        pytest.param(["export", "--repo", "r", "--deps", "d"], id="deps-on-export"),
        pytest.param(["export", "--repo", "r", "--bogus", "x"], id="unknown-flag"),
        pytest.param(["export", "--repo"], id="flag-without-value"),
        pytest.param(["export", "--repo", "a", "--repo", "b"], id="repeated-flag"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--format", "xml"], id="format-xml"),
        pytest.param(["export", "--repo", "r", "--timeout", "601"], id="timeout-601"),
        pytest.param(["export", "--repo", "r", "--timeout", "-1"], id="timeout-negative"),
        pytest.param(["export", "--repo", "r", "--timeout", "1.5"], id="timeout-1.5"),
        pytest.param(["export", "--repo", "r", "--timeout", "x"], id="timeout-text"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--separator", ""], id="empty-separator"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--scope", "a,,b"], id="empty-scope-item"),
    ],
)
def test_usage_errors(argv: list[str]) -> None:
    result = parse(argv)
    assert result["ok"] is False
    assert result["token"] == "usage"
```

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_args.py -q` — Expected: FAIL (module not found)

- [ ] **Step 3: GREEN.** `skills/shared/scripts/architecture-delta/args.mjs`:

```js
// Command-line parsing for the architecture delta tool. Every problem is a `usage` error.
import { ToolError } from './errors.mjs';

const FLAGS = {
  check: ['--repo', '--deps', '--model', '--gap', '--scope', '--shards', '--separator', '--format', '--timeout'],
  export: ['--repo', '--model', '--timeout'],
};
const MAX_TIMEOUT = 600;

function usage(detail) {
  return new ToolError('usage', detail);
}

export function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!Object.hasOwn(FLAGS, command ?? '')) {
    throw usage(`unknown subcommand ${command ?? '(none)'}; use check or export`);
  }
  const opts = {};
  for (let i = 0; i < rest.length; i += 2) {
    const flag = rest[i];
    const value = rest[i + 1];
    if (!FLAGS[command].includes(flag)) throw usage(`unknown flag for ${command}: ${flag}`);
    if (value === undefined) throw usage(`${flag} needs a value`);
    if (Object.hasOwn(opts, flag)) throw usage(`${flag} given twice`);
    opts[flag] = value;
  }
  if (!opts['--repo']) throw usage('--repo is required');
  if (command === 'check' && !opts['--deps']) throw usage('--deps is required for check');
  const format = opts['--format'] ?? 'text';
  if (format !== 'text' && format !== 'json') throw usage('--format must be text or json');
  const timeoutText = opts['--timeout'] ?? '60';
  if (!/^\d+$/.test(timeoutText) || Number(timeoutText) > MAX_TIMEOUT) {
    throw usage(`--timeout must be a whole number from 0 to ${MAX_TIMEOUT}`);
  }
  const separator = opts['--separator'] ?? '.';
  if (separator === '') throw usage('--separator must not be empty');
  let scope = null;
  if (opts['--scope'] !== undefined) {
    scope = opts['--scope'].split(',').map((s) => s.trim());
    if (scope.some((s) => s === '')) throw usage('--scope has an empty element id');
  }
  return {
    command,
    repo: opts['--repo'],
    deps: opts['--deps'] ?? null,
    model: opts['--model'] ?? 'architecture',
    gap: opts['--gap'] ?? null,
    scope,
    shards: opts['--shards'] ?? null,
    separator,
    format,
    timeout: Number(timeoutText),
  };
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_args.py -q` — Expected: PASS (19)
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/args.mjs tests/scripts/test_architecture_delta_args.py
git commit -m "feat(20): argument parsing and usage errors"
```

---

### Task 4: Locate and load `likec4` (repository copy first, exact folders)

**Tier:** standard — trust boundary (dynamic import of repository code), complete code given (strong → standard).

**Files:**
- Create: `skills/shared/scripts/architecture-delta/paths.mjs`
- Create: `skills/shared/scripts/architecture-delta/likec4.mjs`
- Test: `tests/scripts/test_architecture_delta_likec4.py`

**Callers that move with this task:** none

**Reviewer looks at:**
- repository copy wins — mutation: swap the order to plugin first — killed by: `test_repo_copy_wins_at_any_version`
- no parent search — mutation: resolve with `createRequire(...).resolve('likec4')` — killed by: `test_parent_folders_are_never_searched`
- entry stays inside its copy — mutation: drop the `isInside(realEntry, dir)` check — killed by: `test_entry_outside_the_copy_is_internal`
- entry field order — mutation: try `main` before `exports` — killed by: `test_entry_field_order`

- Satisfies Spec AC: AC-1, AC-2 (loader level; end to end in Task 11)
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests.**

```python
from __future__ import annotations

import json
import os
from pathlib import Path

from arch_delta_support import (
    ENGINE, LIKEC4_DIR, call, lib_url, link_dir, make_shim, require_node, run_module, unique, write_json,
)

require_node()


def locate(repo: Path, engine: Path) -> dict:
    return call("likec4.mjs", "locateLikeC4", str(repo), str(engine))


def same(a: str, b: Path) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def test_plugin_copy_when_the_repo_has_none(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    result = locate(repo, ENGINE)
    assert result["ok"], result
    assert result["value"]["source"] == "plugin"
    assert result["value"]["version"] == "1.60.0"
    assert same(result["value"]["dir"], LIKEC4_DIR)
    assert result["value"]["entry"].replace("\\", "/").endswith("likec4/dist/index.mjs")


def test_repo_copy_wins_at_any_version(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    make_shim(repo / "node_modules", version="1.59.0")
    result = locate(repo, ENGINE)
    assert result["value"]["source"] == "repo"
    assert result["value"]["version"] == "1.59.0"


def test_parent_folders_are_never_searched(tmp_path) -> None:
    outer_repo = tmp_path / unique("a")
    make_shim(outer_repo / "node_modules")
    repo = outer_repo / "repo"
    repo.mkdir()
    outer_engine = tmp_path / unique("b")
    make_shim(outer_engine / "node_modules")
    engine = outer_engine / "engine"
    engine.mkdir()
    result = locate(repo, engine)
    assert result["ok"] is False
    assert result["token"] == "likec4-missing"


def test_missing_everywhere_gives_an_install_hint(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    engine = tmp_path / unique("engine")
    engine.mkdir()
    result = locate(repo, engine)
    assert result["token"] == "likec4-missing"
    assert "npm" in result["details"][0]


def test_repo_copy_that_resolves_outside_the_repo_is_not_used(tmp_path) -> None:
    outside = tmp_path / unique("outside")
    shim = make_shim(outside / "node_modules", version="9.9.9")
    repo = tmp_path / unique("repo")
    link_dir(shim, repo / "node_modules" / "likec4")
    result = locate(repo, ENGINE)
    assert result["value"]["source"] == "plugin"


def test_missing_or_non_string_version_is_unknown(tmp_path) -> None:
    for version_field in ({}, {"version": 3}):
        repo = tmp_path / unique("repo")
        make_shim(repo / "node_modules", package={"name": "likec4", "main": "./index.mjs", **version_field})
        assert locate(repo, ENGINE)["value"]["version"] == "unknown"


def test_entry_field_order(tmp_path) -> None:
    cases = [
        ({"exports": {".": {"import": "./a.mjs", "default": {"import": "./b.mjs"}}}, "main": "./c.mjs"}, "a.mjs"),
        ({"exports": {".": {"default": {"import": "./b.mjs"}}}, "module": "./d.mjs", "main": "./c.mjs"}, "b.mjs"),
        ({"exports": {".": {"default": "./e.mjs"}}, "main": "./c.mjs"}, "e.mjs"),
        ({"module": "./d.mjs", "main": "./c.mjs"}, "d.mjs"),
        ({"main": "./c.mjs"}, "c.mjs"),
    ]
    for fields, expected in cases:
        repo = tmp_path / unique("repo")
        pkg = make_shim(repo / "node_modules", package={"name": "likec4", "version": "1.0.0", **fields})
        for name in ("a.mjs", "b.mjs", "c.mjs", "d.mjs", "e.mjs"):
            (pkg / name).write_text("export const x = 1;\n", encoding="utf-8")
        assert locate(repo, ENGINE)["value"]["entry"].endswith(expected), fields


def test_no_entry_is_internal(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    make_shim(repo / "node_modules", package={"name": "likec4", "version": "1.0.0"})
    result = locate(repo, ENGINE)
    assert result["token"] == "internal"


def test_entry_outside_the_copy_is_internal(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    (repo / "node_modules").mkdir(parents=True)
    (repo / "node_modules" / "x.mjs").write_text("export const x = 1;\n", encoding="utf-8")
    make_shim(repo / "node_modules", package={"name": "likec4", "version": "1.0.0", "main": "../x.mjs"})
    result = locate(repo, ENGINE)
    assert result["token"] == "internal"


def test_import_requires_fromworkspace(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    make_shim(repo / "node_modules", source="export const nothing = 1;\n")
    code = (
        f"import {{ locateLikeC4, importLikeC4 }} from {json.dumps(lib_url('likec4.mjs'))};\n"
        f"const located = locateLikeC4({json.dumps(str(repo))}, {json.dumps(str(ENGINE))});\n"
        "try { await importLikeC4(located); process.stdout.write('loaded'); }\n"
        "catch (err) { process.stdout.write(err.token); }\n"
    )
    assert run_module(code).stdout == "internal"


def test_import_loads_the_real_class() -> None:
    code = (
        f"import {{ locateLikeC4, importLikeC4 }} from {json.dumps(lib_url('likec4.mjs'))};\n"
        f"const located = locateLikeC4({json.dumps(str(ENGINE / 'tests'))}, {json.dumps(str(ENGINE))});\n"
        "const LikeC4 = await importLikeC4(located);\n"
        "process.stdout.write(typeof LikeC4.fromWorkspace);\n"
    )
    assert run_module(code).stdout == "function"


def test_version_note() -> None:
    assert call("likec4.mjs", "versionNote", {"version": "1.59.0", "source": "repo"})["value"] == (
        "note: likec4 1.59.0 from repo; tested with 1.60.0"
    )
    assert call("likec4.mjs", "versionNote", {"version": "1.60.0", "source": "plugin"})["value"] is None
```

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_likec4.py -q` — Expected: FAIL (module not found)

- [ ] **Step 3: GREEN.**

`skills/shared/scripts/architecture-delta/paths.mjs`:

```js
// Path containment for the architecture delta tool.
import path from 'node:path';

export function isInside(child, parent) {
  const rel = path.relative(parent, child);
  return rel === '' || (rel.split(path.sep)[0] !== '..' && !path.isAbsolute(rel));
}
```

`skills/shared/scripts/architecture-delta/likec4.mjs`:

```js
// Finds and loads likec4: the repository's own copy first, then the plugin's, each from one exact folder.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { ToolError } from './errors.mjs';
import { isInside } from './paths.mjs';

export const TESTED_VERSION = '1.60.0';
const INSTALL_HINT =
  'likec4 not found in <repo>/node_modules or the plugin; run `npm install --save-dev --ignore-scripts likec4@1.60.0` '
  + 'in the repository, or `npm ci --ignore-scripts` in the plugin';

function copyIn(root) {
  const dir = path.join(root, 'node_modules', 'likec4');
  if (!fs.existsSync(path.join(dir, 'package.json'))) return null;
  const realRoot = fs.realpathSync(root);
  const realDir = fs.realpathSync(dir);
  return isInside(realDir, realRoot) ? realDir : null;
}

export function entryOf(pkg) {
  const dot = pkg.exports && typeof pkg.exports === 'object' ? pkg.exports['.'] : undefined;
  const options = [
    dot?.import,
    dot?.default?.import,
    typeof dot?.default === 'string' ? dot.default : undefined,
    pkg.module,
    pkg.main,
  ];
  return options.find((value) => typeof value === 'string' && value !== '');
}

export function locateLikeC4(repoRoot, engineRoot) {
  for (const [root, source] of [[repoRoot, 'repo'], [engineRoot, 'plugin']]) {
    const dir = copyIn(root);
    if (dir === null) continue;
    let pkg;
    try {
      pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
    } catch (err) {
      throw new ToolError('internal', `${source} likec4 package.json is unreadable: ${err.message}`);
    }
    const version = typeof pkg.version === 'string' ? pkg.version : 'unknown';
    const entry = entryOf(pkg);
    if (entry === undefined) throw new ToolError('internal', `${source} likec4 package.json names no entry`);
    let realEntry;
    try {
      realEntry = fs.realpathSync(path.resolve(dir, entry));
    } catch {
      throw new ToolError('internal', `${source} likec4 entry ${entry} does not exist`);
    }
    if (!isInside(realEntry, dir)) throw new ToolError('internal', `${source} likec4 entry lies outside its folder`);
    return { dir, version, source, entry: realEntry };
  }
  throw new ToolError('likec4-missing', INSTALL_HINT);
}

export async function importLikeC4(located) {
  const mod = await import(pathToFileURL(located.entry).href);
  if (typeof mod.LikeC4?.fromWorkspace !== 'function') {
    throw new ToolError('internal', `likec4 ${located.version} from ${located.source} has no LikeC4.fromWorkspace`);
  }
  return mod.LikeC4;
}

export function versionNote(located) {
  return located.version === TESTED_VERSION
    ? null
    : `note: likec4 ${located.version} from ${located.source}; tested with ${TESTED_VERSION}`;
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_likec4.py -q` — Expected: PASS (12)
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/paths.mjs skills/shared/scripts/architecture-delta/likec4.mjs tests/scripts/test_architecture_delta_likec4.py
git commit -m "feat(20): locate and load likec4, repository copy first, exact folders"
```

---

### Task 5: Model-folder walk and C4 spec copy check

**Tier:** standard — trust boundary (keeps `likec4` from running repository code); complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/walk.mjs`
- Test: `tests/scripts/test_architecture_delta_model.py` (walk part)

**Callers that move with this task:** none

**Reviewer looks at:**
- config name match — mutation: make the regex case-sensitive — killed by: `test_config_file_at_any_depth_is_refused`
- file-count boundary — mutation: `>` to `>=` on the file limit — killed by: `test_folder_limits[2000-files-ok]`
- CRLF normalisation — mutation: compare raw text — killed by: `test_spec_copy_with_crlf_is_accepted`

- Satisfies Spec AC: AC-4, AC-24, AC-22 (`model-size`) at module level
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests** (new file `tests/scripts/test_architecture_delta_model.py`).

```python
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from arch_delta_support import SHIPPED_SPEC, call, link_dir, require_node, unique

require_node()

MB = 1024 * 1024


def model_dir(tmp_path: Path) -> Path:
    folder = tmp_path / unique("model")
    folder.mkdir()
    shutil.copyfile(SHIPPED_SPEC, folder / "c4.c4")
    return folder


def walk(folder: Path) -> dict:
    return call("walk.mjs", "walkModelDir", str(folder))


def test_clean_folder_passes(tmp_path) -> None:
    folder = model_dir(tmp_path)
    (folder / "sub").mkdir()
    (folder / "sub" / "more.c4").write_text("model {\n}\n", encoding="utf-8")
    (folder / "known-gap.json").write_text('{"entries": []}', encoding="utf-8")
    assert walk(folder) == {"ok": True, "value": None}


@pytest.mark.parametrize("name", ["likec4.config.mjs", "LikeC4.Config.json", ".likec4rc", "likec4.config.ts"])
def test_config_file_at_any_depth_is_refused(tmp_path, name: str) -> None:
    folder = model_dir(tmp_path)
    (folder / "deep" / "er").mkdir(parents=True)
    (folder / "deep" / "er" / name).write_text("export default {}\n", encoding="utf-8")
    result = walk(folder)
    assert result["ok"] is False
    assert result["token"] == "model-config"


def test_link_inside_the_model_folder_is_refused(tmp_path) -> None:
    folder = model_dir(tmp_path)
    target = tmp_path / unique("elsewhere")
    target.mkdir()
    link_dir(target, folder / "linked")
    assert walk(folder)["token"] == "model-symlink"


@pytest.mark.parametrize(
    ("files", "sizes", "ok"),
    [
        pytest.param(1999, [], True, id="2000-files-ok"),
        pytest.param(2000, [], False, id="2001-files-refused"),
        pytest.param(0, [25 * MB, 25 * MB - 2000], True, id="50mb-total-ok"),
        pytest.param(0, [25 * MB, 25 * MB], False, id="over-50mb-refused"),
    ],
)
def test_folder_limits(tmp_path, files: int, sizes: list[int], ok: bool) -> None:
    folder = model_dir(tmp_path)  # c4.c4 is one file of under 2,000 bytes
    for i in range(files):
        (folder / f"f{i}.txt").write_text("x", encoding="utf-8")
    for i, size in enumerate(sizes):
        (folder / f"big{i}.bin").write_bytes(b"\0" * size)
    result = walk(folder)
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "model-size"


def spec_copy(folder: Path) -> dict:
    return call("walk.mjs", "checkSpecCopy", str(folder), str(SHIPPED_SPEC))


def test_spec_copy_identical_is_accepted(tmp_path) -> None:
    assert spec_copy(model_dir(tmp_path))["ok"] is True


def test_spec_copy_with_crlf_is_accepted(tmp_path) -> None:
    folder = model_dir(tmp_path)
    text = SHIPPED_SPEC.read_text(encoding="utf-8").replace("\n", "\r\n")
    (folder / "c4.c4").write_bytes(text.encode("utf-8"))
    assert spec_copy(folder)["ok"] is True


def test_spec_copy_missing_or_changed_is_refused(tmp_path) -> None:
    missing = tmp_path / unique("model")
    missing.mkdir()
    assert spec_copy(missing)["token"] == "spec-copy"
    changed = model_dir(tmp_path)
    (changed / "c4.c4").write_text(SHIPPED_SPEC.read_text(encoding="utf-8") + "// extra\n", encoding="utf-8")
    assert spec_copy(changed)["token"] == "spec-copy"
```

The `50mb-total-ok` case keeps the folder at 50 MB minus the size of `c4.c4` minus margin; the shipped `c4.c4` is under 2,000 bytes (check with `wc -c skills/shared/architecture/c4.c4`; if it is larger, raise the `- 2000` margin to its size).

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_model.py -q` — Expected: FAIL (module not found)

- [ ] **Step 3: GREEN.** `skills/shared/scripts/architecture-delta/walk.mjs`:

```js
// Checks a model folder before likec4 loads it, and checks the C4 specification copy.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from './errors.mjs';

export const MODEL_FILE_LIMIT = 2000;
export const MODEL_BYTES_LIMIT = 50 * 1024 * 1024;
const CONFIG_NAME = /likec4\.config|likec4rc/i;

export function walkModelDir(dir) {
  let files = 0;
  let bytes = 0;
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
      files += 1;
      if (files > MODEL_FILE_LIMIT) throw new ToolError('model-size', `more than ${MODEL_FILE_LIMIT} files`);
      bytes += fs.statSync(full).size;
      if (bytes > MODEL_BYTES_LIMIT) throw new ToolError('model-size', 'more than 50 MB in total');
    }
  }
}

export function checkSpecCopy(modelDir, shippedPath) {
  const copy = path.join(modelDir, 'c4.c4');
  if (!fs.existsSync(copy)) throw new ToolError('spec-copy', 'c4.c4 is missing from the model folder');
  const lf = (text) => text.replace(/\r\n/g, '\n');
  if (lf(fs.readFileSync(copy, 'utf8')) !== lf(fs.readFileSync(shippedPath, 'utf8'))) {
    throw new ToolError('spec-copy', 'c4.c4 differs from the shipped specification');
  }
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_model.py -q` — Expected: PASS (13)
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/walk.mjs tests/scripts/test_architecture_delta_model.py
git commit -m "feat(20): model-folder walk and C4 spec copy check"
```

---

### Task 6: Load the model, check the API shape, validate prefixes

**Tier:** standard — complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/model.mjs`
- Test: `tests/scripts/test_architecture_delta_model.py` (append)

**Callers that move with this task:** none

**Reviewer looks at:**
- metadata value shape — mutation: skip the `typeof meta[key] !== 'string'` check — killed by: `test_unexpected_api_shapes_are_internal[code-array]`
- duplicate prefix — mutation: drop the `seen.has(prefix)` check — killed by: `test_prefix_errors[duplicate]`
- element cap boundary — mutation: `>` to `>=` — killed by: `test_element_cap[5000-ok]`

- Satisfies Spec AC: AC-2b, AC-3, AC-7, AC-22 (`element-cap`, through the real `likec4` load; no separate end-to-end run, since the CLI calls the same `loadModel`)
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests** (append to `tests/scripts/test_architecture_delta_model.py`).

```python
from arch_delta_support import ENGINE, SHOP_MODEL, load_model, make_shim  # noqa: E402


def write_model(tmp_path: Path, text: str) -> Path:
    folder = model_dir(tmp_path)
    (folder / "model.c4").write_text(text, encoding="utf-8")
    return folder


def test_shop_model_loads_elements_and_relationships(tmp_path) -> None:
    result = load_model(write_model(tmp_path, SHOP_MODEL))
    assert result["ok"], result
    elements = {e["id"]: e for e in result["value"]["elements"]}
    assert set(elements) == {"shop", "shop.orders", "shop.orders.api", "shop.checkout", "shop.payments", "shop.payments.card"}
    assert elements["shop.payments"] == {
        "id": "shop.payments", "kind": "container", "tags": ["protected"], "code": ["shop.payments"], "rules": [],
    }
    assert elements["shop"]["code"] == []
    assert sorted((r["from"], r["to"]) for r in result["value"]["relationships"]) == [
        ("shop.checkout", "shop.payments"), ("shop.orders", "shop.checkout"),
    ]


def test_code_and_rules_are_split_and_trimmed(tmp_path) -> None:
    text = "model {\n  a = component 'A' {\n    metadata {\n      code 'a.one , a.two'\n      rules 'BR-1,  BR-2'\n    }\n  }\n}\n"
    element = load_model(write_model(tmp_path, text))["value"]["elements"][0]
    assert element["code"] == ["a.one", "a.two"]
    assert element["rules"] == ["BR-1", "BR-2"]


def test_model_errors_name_file_and_line(tmp_path) -> None:
    text = "model {\n  a = component 'A'\n  a -> missing\n  b = nosuchkind 'B'\n}\n"
    result = load_model(write_model(tmp_path, text))
    assert result["token"] == "model-error"
    assert len(result["details"]) == 2
    assert any(d.startswith("model.c4:3:") for d in result["details"])
    assert any(d.startswith("model.c4:4:") for d in result["details"])


@pytest.mark.parametrize(
    ("codes", "label"),
    [
        pytest.param(["shared", "shared"], "duplicate", id="duplicate"),
        pytest.param(["a,,b", "c"], "empty", id="empty-item"),
        pytest.param(["", "c"], "empty", id="blank"),
    ],
)
def test_prefix_errors(tmp_path, codes: list[str], label: str) -> None:
    text = "model {\n" + "".join(
        f"  e{i} = component 'E{i}' {{\n    metadata {{\n      code '{code}'\n    }}\n  }}\n" for i, code in enumerate(codes)
    ) + "}\n"
    result = load_model(write_model(tmp_path, text))
    assert result["token"] == "model-error"
    assert label in result["details"][0]


BAD_ELEMENT = """export class LikeC4 {
  static async fromWorkspace() {
    return {
      getErrors() { return []; },
      async computedModel() {
        return { elements() { return [ELEMENT]; }, relationships() { return [RELATIONSHIP]; } };
      },
    };
  }
}
"""


@pytest.mark.parametrize(
    ("element", "relationship"),
    [
        pytest.param("{ kind: 'component', tags: [], getMetadata() { return {}; } }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="no-id"),
        pytest.param("{ id: 'a', kind: 'component', tags: 'x', getMetadata() { return {}; } }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="tags-not-array"),
        pytest.param("{ id: 'a', kind: 'component', tags: [], getMetadata() { return { code: ['a'] }; } }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="code-array"),
        pytest.param("{ id: 'a', kind: 'component', tags: [], metadata: {} }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="no-getmetadata"),
        pytest.param("{ id: 'a', kind: 'component', tags: [], getMetadata() { return {}; } }", "{ source: { id: 'a' } }", id="no-target"),
    ],
)
def test_unexpected_api_shapes_are_internal(tmp_path, element: str, relationship: str) -> None:
    shim = make_shim(tmp_path / unique("nm"), source=BAD_ELEMENT.replace("ELEMENT", element).replace("RELATIONSHIP", relationship))
    result = load_model(model_dir(tmp_path), entry=shim / "index.mjs")
    assert result["ok"] is False
    assert result["token"] == "internal"


@pytest.mark.parametrize(("count", "ok"), [pytest.param(5000, True, id="5000-ok"), pytest.param(5001, False, id="5001-refused")])
def test_element_cap(tmp_path, count: int, ok: bool) -> None:
    text = "model {\n" + "".join(f"  e{i} = component 'E{i}'\n" for i in range(count)) + "}\n"
    result = load_model(write_model(tmp_path, text))
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "element-cap"
```

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_model.py -q` — Expected: the new tests FAIL (`model.mjs` not found); the Task 5 tests still PASS.

- [ ] **Step 3: GREEN.** `skills/shared/scripts/architecture-delta/model.mjs`:

```js
// Loads a model folder with likec4, checks the shape of what likec4 returns, validates code prefixes.
import path from 'node:path';
import { ToolError } from './errors.mjs';

export const ELEMENT_LIMIT = 5000;

function shapeError(detail) {
  return new ToolError('internal', `likec4 returned ${detail}`);
}

function where(err, modelDir) {
  const file = typeof err?.sourceFsPath === 'string' ? path.relative(modelDir, err.sourceFsPath) : '?';
  const line = typeof err?.line === 'number' ? err.line + 1 : '?';
  return `${file}:${line}: ${err?.message ?? 'unknown error'}`;
}

function splitList(value) {
  return value === undefined ? [] : value.split(',').map((item) => item.trim());
}

function validatePrefixes(elements) {
  const seen = new Map();
  for (const element of elements) {
    for (const prefix of element.code) {
      if (prefix === '') throw new ToolError('model-error', `${element.id}: empty code prefix`);
      if (seen.has(prefix)) {
        throw new ToolError('model-error', `${element.id}: duplicate code prefix ${prefix}, also listed by ${seen.get(prefix)}`);
      }
      seen.set(prefix, element.id);
    }
  }
}

export async function loadModel(LikeC4, modelDir) {
  let workspace;
  let computed;
  try {
    workspace = await LikeC4.fromWorkspace(modelDir, { logger: false });
  } catch (err) {
    throw new ToolError('model-error', err?.message ?? String(err));
  }
  const errors = workspace.getErrors();
  if (!Array.isArray(errors)) throw shapeError('getErrors() that is not a list');
  if (errors.length > 0) throw new ToolError('model-error', errors.map((err) => where(err, modelDir)));
  try {
    computed = await workspace.computedModel();
  } catch (err) {
    throw new ToolError('model-error', err?.message ?? String(err));
  }
  const elements = [];
  for (const element of computed.elements()) {
    if (typeof element?.id !== 'string' || typeof element.kind !== 'string') throw shapeError('an element without a string id and kind');
    if (!Array.isArray(element.tags) || !element.tags.every((tag) => typeof tag === 'string')) throw shapeError(`element ${element.id} without a tags list`);
    if (typeof element.getMetadata !== 'function') throw shapeError(`element ${element.id} without getMetadata`);
    const meta = element.getMetadata() ?? {};
    for (const key of ['code', 'rules']) {
      if (meta[key] !== undefined && typeof meta[key] !== 'string') throw shapeError(`element ${element.id} with a non-string ${key}`);
    }
    elements.push({
      id: element.id,
      kind: element.kind,
      tags: [...element.tags],
      code: splitList(meta.code),
      rules: splitList(meta.rules).filter((rule) => rule !== ''),
    });
    if (elements.length > ELEMENT_LIMIT) throw new ToolError('element-cap', `more than ${ELEMENT_LIMIT} elements`);
  }
  const relationships = [];
  for (const relationship of computed.relationships()) {
    if (typeof relationship?.source?.id !== 'string' || typeof relationship?.target?.id !== 'string') {
      throw shapeError('a relationship without string source and target ids');
    }
    relationships.push({ from: relationship.source.id, to: relationship.target.id });
  }
  validatePrefixes(elements);
  return { elements, relationships };
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_model.py -q` — Expected: PASS (26). If a `test_element_cap` case takes over 120 s, STOP and report (see Unknown variables).
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/model.mjs tests/scripts/test_architecture_delta_model.py
git commit -m "feat(20): load the model, check likec4's API shape, validate code prefixes"
```

---

### Task 7: Input paths and input files

**Tier:** standard — trust boundary (file paths and parsed input); complete code given.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/paths.mjs` (add `realRepo`, `resolveInside`)
- Create: `skills/shared/scripts/architecture-delta/inputs.mjs`
- Test: `tests/scripts/test_architecture_delta_inputs.py`

**Callers that move with this task:** none (`paths.mjs` gains functions; `isInside` is unchanged, so `likec4.mjs` and its tests are untouched)

**Reviewer looks at:**
- real-path containment — mutation: check the lexical path only — killed by: `test_path_through_a_link_outside_is_refused`
- edge cap boundary — mutation: `>` to `>=` — killed by: `test_edge_cap[1000000-ok]`
- gap ids — mutation: skip the unknown-id check — killed by: `test_gap_shape_errors[unknown-id]`

- Satisfies Spec AC: AC-5, AC-22 (`edge-cap`, `file-size`) at module level
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests.**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_delta_support import call, lib_url, link_dir, require_node, run_module, unique, write_json

require_node()

MB = 1024 * 1024
IDS = ["shop", "shop.orders", "shop.payments"]


def test_inside_path_resolves(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    write_json(repo / "deps.json", {"edges": []})
    real = call("paths.mjs", "realRepo", str(repo))["value"]
    result = call("paths.mjs", "resolveInside", real, "deps.json", "--deps")
    assert result["value"]["exists"] is True
    assert Path(result["value"]["path"]).name == "deps.json"


def test_missing_inside_path_reports_not_existing(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    result = call("paths.mjs", "resolveInside", str(repo), "nope.json", "--gap")
    assert result["value"]["exists"] is False


def test_lexical_escape_is_refused(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    write_json(tmp_path / "outside.json", {"edges": []})
    assert call("paths.mjs", "resolveInside", str(repo), "../outside.json", "--deps")["token"] == "outside-repo"


def test_path_through_a_link_outside_is_refused(tmp_path) -> None:
    outside = tmp_path / unique("outside")
    write_json(outside / "deps.json", {"edges": []})
    repo = tmp_path / unique("repo")
    link_dir(outside, repo / "linked")
    real = call("paths.mjs", "realRepo", str(repo))["value"]
    assert call("paths.mjs", "resolveInside", real, "linked/deps.json", "--deps")["token"] == "outside-repo"


def test_repo_must_be_a_directory(tmp_path) -> None:
    assert call("paths.mjs", "realRepo", str(tmp_path / "missing"))["token"] == "bad-input"
    file = write_json(tmp_path / unique("f"), {})
    assert call("paths.mjs", "realRepo", str(file))["token"] == "bad-input"


def read_and(fn: str, file: Path, *extra: object) -> dict:
    code = (
        f"import {{ readJson, {fn} }} from {json.dumps(lib_url('inputs.mjs'))};\n"
        "try {\n"
        f"  const out = {fn}(readJson({json.dumps(str(file))}, '--x'), ...{json.dumps(list(extra))});\n"
        "  process.stdout.write(JSON.stringify({ ok: true, value: out }));\n"
        "} catch (err) {\n"
        "  process.stdout.write(JSON.stringify({ ok: false, token: err.token ?? null, details: err.details ?? null }));\n"
        "}\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_deps_are_deduplicated_and_empty_is_valid(tmp_path) -> None:
    file = write_json(tmp_path / unique("d"), {"edges": [["a", "b"], ["a", "b"], ["b", "c"]]})
    assert read_and("parseDeps", file)["value"] == [["a", "b"], ["b", "c"]]
    empty = write_json(tmp_path / unique("d"), {"edges": []})
    assert read_and("parseDeps", empty)["value"] == []


@pytest.mark.parametrize(
    "data",
    [
        pytest.param([], id="not-object"),
        pytest.param({}, id="no-edges"),
        pytest.param({"edges": [], "extra": 1}, id="unknown-key"),
        pytest.param({"edges": {}}, id="edges-not-list"),
        pytest.param({"edges": [["a"]]}, id="one-item"),
        pytest.param({"edges": [["a", "b", "c"]]}, id="three-items"),
        pytest.param({"edges": [["a", ""]]}, id="empty-string"),
        pytest.param({"edges": [["a", 1]]}, id="non-string"),
    ],
)
def test_deps_shape_errors(tmp_path, data: object) -> None:
    assert read_and("parseDeps", write_json(tmp_path / unique("d"), data))["token"] == "bad-input"


def test_invalid_json_is_bad_input(tmp_path) -> None:
    file = tmp_path / unique("d")
    file.write_text("{not json", encoding="utf-8")
    assert read_and("parseDeps", file)["token"] == "bad-input"


@pytest.mark.parametrize(("count", "ok"), [pytest.param(1_000_000, True, id="1000000-ok"), pytest.param(1_000_001, False, id="1000001-refused")])
def test_edge_cap(tmp_path, count: int, ok: bool) -> None:
    file = tmp_path / unique("d")
    file.write_text('{"edges":[' + ",".join(['["a","b"]'] * count) + "]}", encoding="utf-8")
    result = read_and("parseDeps", file)
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "edge-cap"


@pytest.mark.parametrize(("pad", "ok"), [pytest.param(0, True, id="50mb-ok"), pytest.param(1, False, id="over-50mb-refused")])
def test_file_size_limit(tmp_path, pad: int, ok: bool) -> None:
    body = '{"edges":[]}'
    file = tmp_path / unique("d")
    file.write_text(body + " " * (50 * MB - len(body) + pad), encoding="utf-8")
    result = read_and("parseDeps", file)
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "file-size"


def test_gap_entries_parse(tmp_path) -> None:
    data = {"entries": [
        {"from": "shop.orders", "to": "shop.payments", "reason": "r"},
        {"from": "shop", "to": "shop.orders", "reason": "r", "close_by": "feature-2"},
    ]}
    assert read_and("parseGap", write_json(tmp_path / unique("g"), data), IDS)["value"] == [
        {"from": "shop.orders", "to": "shop.payments", "reason": "r", "close_by": None},
        {"from": "shop", "to": "shop.orders", "reason": "r", "close_by": "feature-2"},
    ]


@pytest.mark.parametrize(
    "data",
    [
        pytest.param({}, id="no-entries"),
        pytest.param({"entries": [], "x": 1}, id="unknown-top-key"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders"}]}, id="missing-reason"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": ""}]}, id="empty-reason"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": "r", "why": 1}]}, id="unknown-key"),
        pytest.param({"entries": [{"from": "shop", "to": "nope", "reason": "r"}]}, id="unknown-id"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": "r"}] * 2}, id="duplicate"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": "r", "close_by": 2}]}, id="close-by-not-string"),
    ],
)
def test_gap_shape_errors(tmp_path, data: object) -> None:
    assert read_and("parseGap", write_json(tmp_path / unique("g"), data), IDS)["token"] == "bad-input"


def test_shards_parse_and_empty_list_is_valid(tmp_path) -> None:
    data = {"shards": {"one": ["shop.orders"], "two": []}}
    assert read_and("parseShards", write_json(tmp_path / unique("s"), data), IDS)["value"] == {
        "one": ["shop.orders"], "two": [],
    }


@pytest.mark.parametrize(
    "data",
    [
        pytest.param({}, id="no-shards"),
        pytest.param({"shards": {}, "x": 1}, id="unknown-key"),
        pytest.param({"shards": {"one": "shop"}}, id="not-list"),
        pytest.param({"shards": {"one": ["nope"]}}, id="unknown-id"),
        pytest.param({"shards": []}, id="shards-not-object"),
    ],
)
def test_shards_shape_errors(tmp_path, data: object) -> None:
    assert read_and("parseShards", write_json(tmp_path / unique("s"), data), IDS)["token"] == "bad-input"
```

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_inputs.py -q` — Expected: FAIL (`realRepo` is not exported; `inputs.mjs` not found)

- [ ] **Step 3: GREEN.**

Append to `skills/shared/scripts/architecture-delta/paths.mjs` (and add the imports at its top):

```js
import fs from 'node:fs';
import { ToolError } from './errors.mjs';

export function realRepo(repo) {
  let stat;
  try {
    stat = fs.statSync(repo);
  } catch {
    throw new ToolError('bad-input', `--repo not found: ${repo}`);
  }
  if (!stat.isDirectory()) throw new ToolError('bad-input', `--repo is not a directory: ${repo}`);
  return fs.realpathSync(repo);
}

export function resolveInside(root, value, flag) {
  const lexical = path.resolve(root, value);
  if (!fs.existsSync(lexical)) {
    if (!isInside(lexical, root)) throw new ToolError('outside-repo', `${flag} lies outside --repo`);
    return { path: lexical, exists: false };
  }
  const real = fs.realpathSync(lexical);
  if (!isInside(real, root)) throw new ToolError('outside-repo', `${flag} resolves outside --repo`);
  return { path: real, exists: true };
}
```

`skills/shared/scripts/architecture-delta/inputs.mjs`:

```js
// Reads and validates the dependency, known-gap and shards files.
import fs from 'node:fs';
import { ToolError } from './errors.mjs';

export const FILE_LIMIT = 50 * 1024 * 1024;
export const EDGE_LIMIT = 1_000_000;

function bad(detail) {
  return new ToolError('bad-input', detail);
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function onlyKeys(value, allowed, where) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw bad(`${where}: unknown key ${key}`);
}

function text(value) {
  return typeof value === 'string' && value !== '';
}

export function readJson(file, flag) {
  if (fs.statSync(file).size > FILE_LIMIT) throw new ToolError('file-size', `${flag} is over 50 MB`);
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (err) {
    throw bad(`${flag} is not valid JSON: ${err.message}`);
  }
}

export function parseDeps(data) {
  if (!isObject(data) || !Object.hasOwn(data, 'edges')) throw bad('--deps must be an object with an edges list');
  onlyKeys(data, ['edges'], '--deps');
  if (!Array.isArray(data.edges)) throw bad('--deps edges must be a list');
  if (data.edges.length > EDGE_LIMIT) throw new ToolError('edge-cap', `more than ${EDGE_LIMIT} edges`);
  const seen = new Set();
  const edges = [];
  data.edges.forEach((edge, index) => {
    if (!Array.isArray(edge) || edge.length !== 2 || !edge.every(text)) {
      throw bad(`--deps edge ${index} must be two non-empty strings`);
    }
    const key = `${edge[0]}\u0000${edge[1]}`;
    if (!seen.has(key)) {
      seen.add(key);
      edges.push([edge[0], edge[1]]);
    }
  });
  return edges;
}

export function parseGap(data, elementIds) {
  const ids = new Set(elementIds);
  if (!isObject(data) || !Array.isArray(data.entries)) throw bad('--gap must be an object with an entries list');
  onlyKeys(data, ['entries'], '--gap');
  const seen = new Set();
  return data.entries.map((entry, index) => {
    const where = `--gap entry ${index}`;
    if (!isObject(entry)) throw bad(`${where} must be an object`);
    onlyKeys(entry, ['from', 'to', 'reason', 'close_by'], where);
    for (const key of ['from', 'to', 'reason']) if (!text(entry[key])) throw bad(`${where}: ${key} must be a non-empty string`);
    if (entry.close_by !== undefined && typeof entry.close_by !== 'string') throw bad(`${where}: close_by must be a string`);
    for (const key of ['from', 'to']) if (!ids.has(entry[key])) throw bad(`${where}: ${entry[key]} is not a model element`);
    const pair = `${entry.from}\u0000${entry.to}`;
    if (seen.has(pair)) throw bad(`${where} duplicates ${entry.from} -> ${entry.to}`);
    seen.add(pair);
    return { from: entry.from, to: entry.to, reason: entry.reason, close_by: entry.close_by ?? null };
  });
}

export function parseShards(data, elementIds) {
  const ids = new Set(elementIds);
  if (!isObject(data) || !isObject(data.shards)) throw bad('--shards must be an object with a shards object');
  onlyKeys(data, ['shards'], '--shards');
  const shards = {};
  for (const [name, list] of Object.entries(data.shards)) {
    if (!Array.isArray(list)) throw bad(`--shards ${name} must be a list of element ids`);
    for (const id of list) if (typeof id !== 'string' || !ids.has(id)) throw bad(`--shards ${name}: ${id} is not a model element`);
    shards[name] = [...list];
  }
  return shards;
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_inputs.py tests/scripts/test_architecture_delta_likec4.py -q` — Expected: PASS
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/paths.mjs skills/shared/scripts/architecture-delta/inputs.mjs tests/scripts/test_architecture_delta_inputs.py
git commit -m "feat(20): input paths inside the repo and validated input files"
```

---

### Task 8: The CLI with the `export` command

**Tier:** standard — first end-to-end task; complete code given.

**Files:**
- Create: `skills/shared/scripts/architecture-delta.mjs`
- Create: `skills/shared/scripts/architecture-delta/report.mjs` (`exportJson`)
- Test: `tests/scripts/test_architecture_delta_export.py`

**Callers that move with this task:** none

**Reviewer looks at:**
- stdout empty on exit 2 — mutation: write output before the last check — killed by: `test_usage_errors_end_to_end`
- export sorting — mutation: drop the `sort` on elements — killed by: `test_export_is_stable_and_sorted`
- config refused before load — mutation: call `loadModel` before `walkModelDir` — killed by: `test_export_refuses_config_and_never_runs_it`

- Satisfies Spec AC: AC-18, AC-23, AC-24, AC-25; AC-4 and AC-7 through `export`; the `timeout` part of AC-22 through `export`
- Decisions applied: none
- **Test retention:** Permanent

`check` is wired in Task 11. Until then the CLI answers `check` with `error: internal: check is not available in this build` (exit 2); Task 11 removes that branch.

- [ ] **Step 1: write RED tests.**

```python
from __future__ import annotations

import json
import shutil

import pytest

from arch_delta_support import (
    SHIPPED_SPEC, SHOP_MODEL, copy_engine, error_lines, link_dir, make_repo, make_shim, require_node, run_tool, unique,
)

require_node()


def test_export_is_stable_and_sorted(tmp_path) -> None:
    repo = make_repo(tmp_path)
    first = run_tool("export", "--repo", repo)
    second = run_tool("export", "--repo", repo)
    assert first.returncode == 0, first.stderr
    assert first.stdout == second.stdout
    data = json.loads(first.stdout)
    assert list(data) == ["format", "elements", "allowed"]
    assert data["format"] == 1
    assert [e["id"] for e in data["elements"]] == [
        "shop", "shop.checkout", "shop.orders", "shop.orders.api", "shop.payments", "shop.payments.card",
    ]
    assert data["elements"][4] == {
        "id": "shop.payments", "kind": "container", "tags": ["protected"], "code": ["shop.payments"], "rules": [],
    }
    assert data["allowed"] == [
        {"from": "shop.checkout", "to": "shop.payments"}, {"from": "shop.orders", "to": "shop.checkout"},
    ]


def test_export_merges_duplicate_relationships(tmp_path) -> None:
    model = "model {\n  a = component 'A'\n  b = component 'B'\n  a -> b\n  a -[uses]-> b 'again'\n}\n"
    data = json.loads(run_tool("export", "--repo", make_repo(tmp_path, model)).stdout)
    assert data["allowed"] == [{"from": "a", "to": "b"}]


def test_export_of_a_spec_only_folder_is_empty(tmp_path) -> None:
    proc = run_tool("export", "--repo", make_repo(tmp_path, None))
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"format": 1, "elements": [], "allowed": []}


def test_export_refuses_config_and_never_runs_it(tmp_path) -> None:
    repo = make_repo(tmp_path)
    marker = repo / "ran.txt"
    nested = repo / "architecture" / "nested"
    nested.mkdir()
    (nested / "likec4.config.mjs").write_text(
        "import fs from 'node:fs';\n"
        f"fs.writeFileSync({json.dumps(str(marker))}, 'yes');\n"
        "export default { name: 'x' };\n",
        encoding="utf-8",
    )
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith("error: model-config: ")
    assert not marker.exists()


def test_export_refuses_a_link_in_the_model(tmp_path) -> None:
    repo = make_repo(tmp_path)
    target = tmp_path / unique("t")
    target.mkdir()
    link_dir(target, repo / "architecture" / "link")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: model-symlink: ")


def test_export_checks_the_spec_copy(tmp_path) -> None:
    missing = make_repo(tmp_path, spec=False)
    assert error_lines(run_tool("export", "--repo", missing))[0].startswith("error: spec-copy: ")
    crlf = make_repo(tmp_path)
    (crlf / "architecture" / "c4.c4").write_bytes(SHIPPED_SPEC.read_text(encoding="utf-8").replace("\n", "\r\n").encode())
    assert run_tool("export", "--repo", crlf).returncode == 0


def test_export_refuses_duplicate_prefixes(tmp_path) -> None:
    model = "model {\n  a = component 'A' {\n    metadata {\n      code 'x'\n    }\n  }\n  b = component 'B' {\n    metadata {\n      code 'x'\n    }\n  }\n}\n"
    proc = run_tool("export", "--repo", make_repo(tmp_path, model))
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: model-error: ")


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(["frobnicate"], id="unknown-subcommand"),
        pytest.param(["export", "--repo", ".", "--bogus", "1"], id="unknown-flag"),
        pytest.param(["check", "--repo", ".", "--deps", "d.json", "--format", "xml"], id="format-xml"),
        pytest.param(["export", "--repo", ".", "--timeout", "601"], id="timeout-601"),
    ],
)
def test_usage_errors_end_to_end(args: list[str]) -> None:
    proc = run_tool(*args)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith("error: usage: ")


def test_timeout_zero(tmp_path) -> None:
    proc = run_tool("export", "--repo", make_repo(tmp_path), "--timeout", "0")
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc) == [line for line in error_lines(proc) if line.startswith("error: timeout: ")]
    assert error_lines(proc)


def test_repo_and_model_paths(tmp_path) -> None:
    assert error_lines(run_tool("export", "--repo", tmp_path / "missing"))[0].startswith("error: bad-input: ")
    repo = make_repo(tmp_path)
    assert error_lines(run_tool("export", "--repo", repo, "--model", "nope"))[0].startswith("error: bad-input: ")
    assert error_lines(run_tool("export", "--repo", repo, "--model", ".."))[0].startswith("error: outside-repo: ")


def test_repo_version_note(tmp_path) -> None:
    repo = make_repo(tmp_path)
    make_shim(repo / "node_modules", version="1.59.0")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    assert "note: likec4 1.59.0 from repo; tested with 1.60.0" in proc.stderr.splitlines()


def test_missing_likec4_from_a_copied_engine(tmp_path) -> None:
    script = copy_engine(tmp_path / unique("copy"))
    proc = run_tool("export", "--repo", make_repo(tmp_path), script=script)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: likec4-missing: ")


def test_check_is_not_available_yet(tmp_path) -> None:
    proc = run_tool("check", "--repo", make_repo(tmp_path), "--deps", "d.json")
    assert proc.returncode == 2
    assert error_lines(proc)[0] == "error: internal: check is not available in this build"
```

`test_check_is_not_available_yet` is **Temporary**: Task 11 deletes it.

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_export.py -q` — Expected: FAIL (script not found)

- [ ] **Step 3: GREEN.**

`skills/shared/scripts/architecture-delta/report.mjs`:

```js
// Renders the tool's JSON and text output. Strings are sorted raw, then cleaned.
import { clean } from './errors.mjs';

export const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
export const byPair = (x, y) => cmp(x.from, y.from) || cmp(x.to, y.to);

export function uniquePairs(list) {
  const seen = new Set();
  return list.filter((pair) => {
    const key = `${pair.from}\u0000${pair.to}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

const cleanPair = (pair) => ({ from: clean(pair.from), to: clean(pair.to) });

export function exportJson(model) {
  return {
    format: 1,
    elements: [...model.elements].sort((a, b) => cmp(a.id, b.id)).map((element) => ({
      id: clean(element.id),
      kind: clean(element.kind),
      tags: [...element.tags].sort(cmp).map(clean),
      code: element.code.map(clean),
      rules: element.rules.map(clean),
    })),
    allowed: uniquePairs(model.relationships).sort(byPair).map(cleanPair),
  };
}
```

`skills/shared/scripts/architecture-delta.mjs`:

```js
#!/usr/bin/env node
// Architecture delta: compares a LikeC4 C4 model with a repository's code dependencies.
// Reads files only; never writes a file or runs another program.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ToolError, errorLines } from './architecture-delta/errors.mjs';
import { parseArgs } from './architecture-delta/args.mjs';
import { locateLikeC4, importLikeC4, versionNote } from './architecture-delta/likec4.mjs';
import { walkModelDir, checkSpecCopy } from './architecture-delta/walk.mjs';
import { loadModel } from './architecture-delta/model.mjs';
import { realRepo, resolveInside } from './architecture-delta/paths.mjs';
import { exportJson } from './architecture-delta/report.mjs';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = path.resolve(SCRIPT_DIR, '..', '..', '..');
const SHIPPED_SPEC = path.resolve(SCRIPT_DIR, '..', 'architecture', 'c4.c4');

function startDeadline(seconds) {
  const end = Date.now() + seconds * 1000;
  const message = `run exceeded --timeout ${seconds}s`;
  const timer = setTimeout(() => {
    process.stderr.write(`error: timeout: ${message}\n`);
    process.exit(2);
  }, seconds * 1000);
  timer.unref();
  return {
    check() {
      if (Date.now() >= end) throw new ToolError('timeout', message);
    },
    stop() {
      clearTimeout(timer);
    },
  };
}

async function loadRepoModel(args, deadline) {
  const repo = realRepo(args.repo);
  const model = resolveInside(repo, args.model, '--model');
  if (!model.exists || !fs.statSync(model.path).isDirectory()) throw new ToolError('bad-input', '--model directory not found');
  const located = locateLikeC4(repo, ENGINE_ROOT);
  const note = versionNote(located);
  if (note !== null) process.stderr.write(`${note}\n`);
  const LikeC4 = await importLikeC4(located);
  deadline.check();
  walkModelDir(model.path);
  checkSpecCopy(model.path, SHIPPED_SPEC);
  const loaded = await loadModel(LikeC4, model.path);
  deadline.check();
  return { repo, modelDir: model.path, located, model: loaded };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const { model } = await loadRepoModel(args, deadline);
  let output;
  let exitCode = 0;
  if (args.command === 'export') {
    output = `${JSON.stringify(exportJson(model), null, 2)}\n`;
  } else {
    throw new ToolError('internal', 'check is not available in this build');
  }
  deadline.stop();
  process.stdout.write(output);
  process.exitCode = exitCode;
}

main(process.argv.slice(2)).catch((err) => {
  const error = err instanceof ToolError ? err : new ToolError('internal', err?.message ?? String(err));
  process.stderr.write(`${errorLines(error).join('\n')}\n`);
  process.exitCode = 2;
});
```

- [ ] **Step 4: run GREEN and the suite so far.** `uv run pytest tests/scripts -q` — Expected: PASS
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta.mjs skills/shared/scripts/architecture-delta/report.mjs tests/scripts/test_architecture_delta_export.py
git commit -m "feat(20): CLI with the export command"
```

---

### Task 9: Matching — mapping, ignored edges, allowed edges, `#protected`, not yet reached, unmapped

**Tier:** standard — correctness-critical rules, complete code given (strong → standard).

**Files:**
- Create: `skills/shared/scripts/architecture-delta/match.mjs`
- Test: `tests/scripts/test_architecture_delta_match.py`

**Callers that move with this task:** none

**Reviewer looks at:**
- longest prefix — mutation: sort prefixes shortest first — killed by: `test_longest_prefix_wins_and_separator_counts`
- separator boundary — mutation: `m.startsWith(p)` without the separator — killed by: `test_longest_prefix_wins_and_separator_counts`
- `#protected` from outside — mutation: let a relationship to P's ancestor count — killed by: `test_protected_needs_a_relationship_into_it`
- inside a protected element — mutation: apply the protected rule when A is inside P — killed by: `test_children_of_a_protected_element_follow_the_ordinary_rule`

- Satisfies Spec AC: AC-6, AC-8, AC-9, AC-10, AC-11
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests.**

```python
from __future__ import annotations

import json

from arch_delta_support import lib_url, require_node, run_module

require_node()


def element(id_: str, code: str | None = None, tags: list[str] | None = None) -> dict:
    return {"id": id_, "kind": "component", "tags": tags or [], "code": [code] if code else [], "rules": []}


def compare(elements: list[dict], relationships: list[tuple[str, str]], edges: list[list[str]], **options) -> dict:
    model = {"elements": elements, "relationships": [{"from": a, "to": b} for a, b in relationships]}
    opts = {"separator": ".", **options}
    code = (
        f"import {{ compare }} from {json.dumps(lib_url('match.mjs'))};\n"
        f"const out = compare({json.dumps(model)}, {json.dumps(edges)}, {json.dumps(opts)});\n"
        "process.stdout.write(JSON.stringify(out));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def pairs(items: list[dict]) -> list[tuple[str, str]]:
    return sorted((item["from"], item["to"]) for item in items)


def test_longest_prefix_wins_and_separator_counts() -> None:
    out = compare(
        [element("shop", "shop"), element("shop.orders", "shop.orders"), element("c", "cat")],
        [],
        [["shop.orders.api", "cat"], ["shop.ordersx", "cat"]],
    )
    assert pairs(out["breaches"]) == [("shop", "c"), ("shop.orders", "c")]


def test_other_separator() -> None:
    out = compare([element("a", "src/a"), element("b", "src/b")], [], [["src/a/x", "src/b"]], separator="/")
    assert pairs(out["breaches"]) == [("a", "b")]


def test_ignored_edges_and_unmapped_sources() -> None:
    out = compare(
        [element("a", "a"), element("a.b", "a.b")],
        [],
        [["a.x", "a.y"], ["a.b.x", "a.y"], ["a.x", "ext.lib"], ["zz.q", "a.x"]],
    )
    assert out["breaches"] == []
    assert out["unmapped"] == ["zz.q"]


def test_container_relationship_allows_its_components() -> None:
    elements = [element("A"), element("A.c", "A.c"), element("B"), element("B.d", "B.d")]
    assert compare(elements, [("A", "B")], [["A.c.x", "B.d.y"]])["breaches"] == []
    assert pairs(compare(elements, [], [["A.c.x", "B.d.y"]])["breaches"]) == [("A.c", "B.d")]


PROTECTED = [
    element("o", "o"),
    element("s"),
    element("s.p", "s.p", ["protected"]),
    element("s.p.a", "s.p.a"),
    element("s.p.b", "s.p.b"),
]


def test_protected_needs_a_relationship_into_it() -> None:
    edge = [["o.x", "s.p.a.y"]]
    assert pairs(compare(PROTECTED, [("o", "s")], edge)["breaches"]) == [("o", "s.p.a")]
    assert compare(PROTECTED, [("o", "s.p")], edge)["breaches"] == []
    assert compare(PROTECTED, [("o", "s.p.b")], edge)["breaches"] == []


def test_children_of_a_protected_element_follow_the_ordinary_rule() -> None:
    edge = [["s.p.a.x", "s.p.b.y"]]
    assert pairs(compare(PROTECTED, [], edge)["breaches"]) == [("s.p.a", "s.p.b")]
    assert compare(PROTECTED, [("s.p.a", "s.p.b")], edge)["breaches"] == []


def test_breach_carries_its_module_edges() -> None:
    out = compare([element("a", "a"), element("b", "b")], [], [["a.one", "b.x"], ["a.two", "b.x"]])
    assert sorted(map(tuple, out["breaches"][0]["edges"])) == [("a.one", "b.x"), ("a.two", "b.x")]


def test_not_yet_reached_and_exit_code() -> None:
    out = compare(PROTECTED, [("o", "s.p"), ("o", "s")], [])
    assert pairs(out["notYetReached"]) == [("o", "s.p")]
    assert out["exitCode"] == 0
    reached = compare(PROTECTED, [("o", "s.p")], [["o.x", "s.p.a.y"]])
    assert reached["notYetReached"] == []


def test_new_breach_sets_exit_code_one() -> None:
    assert compare([element("a", "a"), element("b", "b")], [], [["a", "b"]])["exitCode"] == 1
```

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_match.py -q` — Expected: FAIL (module not found)

- [ ] **Step 3: GREEN.** `skills/shared/scripts/architecture-delta/match.mjs`:

```js
// Compares a validated model with code dependencies, following the spec's matching rules.

const key = (a, b) => `${a}\u0000${b}`;

export function within(id, root) {
  return id === root || id.startsWith(`${root}.`);
}

function ancestorsOrSelf(id) {
  const parts = id.split('.');
  return parts.map((_, i) => parts.slice(0, i + 1).join('.'));
}

export function compare(model, edges, options) {
  const { separator, tick = () => {} } = options;
  const elements = new Map(model.elements.map((element) => [element.id, element]));
  const prefixes = model.elements
    .flatMap((element) => element.code.map((prefix) => [prefix, element.id]))
    .sort((a, b) => b[0].length - a[0].length);
  const mapped = new Map();
  const mapModule = (module) => {
    if (!mapped.has(module)) {
      const hit = prefixes.find(([prefix]) => module === prefix || module.startsWith(prefix + separator));
      mapped.set(module, hit ? hit[1] : null);
    }
    return mapped.get(module);
  };
  const relationships = [];
  const relationshipKeys = new Set();
  for (const r of model.relationships) {
    if (!relationshipKeys.has(key(r.from, r.to))) {
      relationshipKeys.add(key(r.from, r.to));
      relationships.push({ from: r.from, to: r.to });
    }
  }
  const nearestProtected = (id) =>
    ancestorsOrSelf(id).reverse().find((x) => elements.get(x)?.tags.includes('protected')) ?? null;
  const allowed = (a, b) => {
    const sources = ancestorsOrSelf(a);
    const guard = nearestProtected(b);
    if (guard !== null && !within(a, guard)) {
      return relationships.some((r) => sources.includes(r.from) && within(r.to, guard));
    }
    const targets = ancestorsOrSelf(b);
    return relationships.some((r) => sources.includes(r.from) && targets.includes(r.to));
  };

  const unmapped = new Set();
  const breachByPair = new Map();
  const allowedByPair = new Map();
  const checkedPairs = [];
  edges.forEach(([from, to], index) => {
    if (index > 0 && index % 10000 === 0) tick();
    const source = mapModule(from);
    if (source === null) {
      unmapped.add(from);
      return;
    }
    const target = mapModule(to);
    if (target === null || within(source, target) || within(target, source)) return;
    const pair = key(source, target);
    if (!allowedByPair.has(pair)) {
      allowedByPair.set(pair, allowed(source, target));
      checkedPairs.push([source, target]);
    }
    if (allowedByPair.get(pair)) return;
    if (!breachByPair.has(pair)) breachByPair.set(pair, { from: source, to: target, edges: [] });
    breachByPair.get(pair).edges.push([from, to]);
  });

  const hasCode = (id) => (elements.get(id)?.code.length ?? 0) > 0;
  const notYetReached = relationships.filter(
    (r) => hasCode(r.from) && hasCode(r.to) && !checkedPairs.some(([s, t]) => within(s, r.from) && within(t, r.to)),
  );
  const breaches = [...breachByPair.values()].map((breach) => ({ ...breach, gap: 'new' }));
  const fresh = breaches.map(({ from, to }) => ({ from, to }));
  return {
    breaches,
    notYetReached,
    unmapped: [...unmapped],
    hotSpots: [],
    gap: { known: [], new: fresh, stale: [] },
    exitCode: fresh.length > 0 ? 1 : 0,
  };
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_match.py -q` — Expected: PASS (9)
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/match.mjs tests/scripts/test_architecture_delta_match.py
git commit -m "feat(20): matching rules - mapping, allowed edges, protected, not yet reached"
```

---

### Task 10: Matching — known gap, scope, hot spots and the exit code

**Tier:** standard — complete code given.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta/match.mjs` (`compare`'s options and result section)
- Test: `tests/scripts/test_architecture_delta_match.py` (append)

**Callers that move with this task:** none (`compare` keeps its signature; the new options default to "none")

**Reviewer looks at:**
- staleness against the whole repo — mutation: compute stale entries after scope filtering — killed by: `test_scope_decides_listing_and_exit_code`
- scope filters the exit code — mutation: compute `exitCode` from unscoped `new` — killed by: `test_scope_decides_listing_and_exit_code`
- hot spot descendants — mutation: compare ids with `===` instead of `within` — killed by: `test_hot_spots`

- Satisfies Spec AC: AC-12, AC-13, AC-14, AC-15, AC-16
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests** (append).

```python
GAP_MODEL = [element("a", "a"), element("b", "b"), element("c", "c"), element("x"), element("x.y", "x.y")]


def entry(a: str, b: str) -> dict:
    return {"from": a, "to": b, "reason": "r", "close_by": None}


def test_known_breach_exits_zero() -> None:
    out = compare(GAP_MODEL, [], [["a", "b"]], gap=[entry("a", "b")])
    assert out["breaches"][0]["gap"] == "known"
    assert pairs(out["gap"]["known"]) == [("a", "b")]
    assert out["exitCode"] == 0


def test_new_breach_exits_one() -> None:
    out = compare(GAP_MODEL, [], [["a", "b"], ["a", "c"]], gap=[entry("a", "b")])
    assert pairs(out["gap"]["new"]) == [("a", "c")]
    assert out["exitCode"] == 1


def test_stale_entry_exits_one() -> None:
    out = compare(GAP_MODEL, [], [], gap=[entry("a", "b")])
    assert pairs(out["gap"]["stale"]) == [("a", "b")]
    assert out["exitCode"] == 1


def test_scope_decides_listing_and_exit_code() -> None:
    outside_only = compare(GAP_MODEL, [], [["a", "b"]], scope=["x"])
    assert outside_only["breaches"] == [] and outside_only["gap"]["new"] == []
    assert outside_only["exitCode"] == 0
    live = compare(GAP_MODEL, [], [["a", "x.y.z"]], scope=["x"], gap=[entry("a", "x.y")])
    assert pairs(live["gap"]["known"]) == [("a", "x.y")]
    assert live["gap"]["stale"] == []
    assert live["exitCode"] == 0
    stale_in = compare(GAP_MODEL, [], [], scope=["x"], gap=[entry("a", "x.y")])
    assert pairs(stale_in["gap"]["stale"]) == [("a", "x.y")]
    assert stale_in["exitCode"] == 1
    stale_out = compare(GAP_MODEL, [], [], scope=["x"], gap=[entry("a", "b")])
    assert stale_out["gap"]["stale"] == []
    assert stale_out["exitCode"] == 0


def test_hot_spots() -> None:
    out = compare(PROTECTED, [], [], shards={"one": ["s.p"], "two": ["s.p.a"], "three": []})
    assert [(h["element"], sorted(h["shards"])) for h in out["hotSpots"]] == [("s.p.a", ["one", "two"])]
    assert compare(PROTECTED, [], [])["hotSpots"] == []
```

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_match.py -q` — Expected: the new tests FAIL (gap, scope and shards are ignored)

- [ ] **Step 3: GREEN.** In `match.mjs`, change the options line to:

```js
  const { separator, gap = [], scope = null, shards = null, tick = () => {} } = options;
```

and replace everything from `const breaches = [...breachByPair.values()]` to the end of `compare` with:

```js
  const entryKeys = new Set(gap.map((entry) => key(entry.from, entry.to)));
  const allBreaches = [...breachByPair.values()].map((breach) => ({
    ...breach,
    gap: entryKeys.has(key(breach.from, breach.to)) ? 'known' : 'new',
  }));
  const staleEverywhere = gap
    .filter((entry) => !breachByPair.has(key(entry.from, entry.to)))
    .map(({ from, to }) => ({ from, to }));
  const inScope = (id) => scope === null || scope.some((root) => within(id, root));
  const keep = (pair) => inScope(pair.from) || inScope(pair.to);
  const breaches = allBreaches.filter(keep);
  const known = breaches.filter((b) => b.gap === 'known').map(({ from, to }) => ({ from, to }));
  const fresh = breaches.filter((b) => b.gap === 'new').map(({ from, to }) => ({ from, to }));
  const stale = staleEverywhere.filter(keep);
  const hotSpots = [];
  if (shards !== null) {
    for (const id of elements.keys()) {
      const names = Object.keys(shards).filter((name) => shards[name].some((root) => within(id, root)));
      if (names.length >= 2) hotSpots.push({ element: id, shards: names });
    }
  }
  return {
    breaches,
    notYetReached: notYetReached.filter(keep),
    unmapped: [...unmapped],
    hotSpots,
    gap: { known, new: fresh, stale },
    exitCode: fresh.length > 0 || stale.length > 0 ? 1 : 0,
  };
}
```

- [ ] **Step 4: run GREEN.** `uv run pytest tests/scripts/test_architecture_delta_match.py -q` — Expected: PASS (14)
- [ ] **Step 5: refactor — none.**
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta/match.mjs tests/scripts/test_architecture_delta_match.py
git commit -m "feat(20): known gap, scope, hot spots and the exit code"
```

---

### Task 11: The `check` command and its reports

**Tier:** standard — wires the comparison end to end; complete code given.

**Files:**
- Modify: `skills/shared/scripts/architecture-delta.mjs` (replace the `check` branch)
- Modify: `skills/shared/scripts/architecture-delta/report.mjs` (add `checkJson`, `checkText`)
- Test: `tests/scripts/test_architecture_delta_check.py`
- Modify: `tests/scripts/test_architecture_delta_export.py` (delete `test_check_is_not_available_yet`)

**Callers that move with this task:** `tests/scripts/test_architecture_delta_export.py::test_check_is_not_available_yet` (Temporary test; delete the whole function)

**Reviewer looks at:**
- 20-edge sample — mutation: `slice(0, 21)` — killed by: `test_json_report_shape_and_edge_sample`
- default gap path — mutation: ignore a missing default gap as an error — killed by: `test_clean_repo_exits_zero_from_the_plugin_copy`
- text summary — mutation: count known breaches as new — killed by: `test_text_report_headings_and_summary`
- unknown scope id — mutation: skip the scope id check — killed by: `test_input_errors_end_to_end[unknown-scope]`

- Satisfies Spec AC: AC-1, AC-2, AC-2b, AC-3, AC-5, AC-13 (one end-to-end case), AC-14, AC-15, AC-16, AC-17, AC-19, AC-20, AC-27
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write RED tests.**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_delta_support import (
    copy_engine, error_lines, link_dir, make_repo, make_shim, require_node, run_tool, unique, write_json,
)

require_node()

CLEAN_EDGES = [["shop.orders.api.handler", "shop.checkout.service"], ["shop.checkout.service", "shop.payments.card.charge"]]
BREACH = ["shop.orders.api.x", "shop.payments.card.y"]


def check(repo: Path, edges: list[list[str]], *extra: str, script: Path | None = None):
    deps = write_json(repo / "deps.json", {"edges": edges})
    kwargs = {"script": script} if script else {}
    return run_tool("check", "--repo", repo, "--deps", deps, *extra, **kwargs)


def report(proc) -> dict:
    assert proc.returncode in (0, 1), proc.stderr
    return json.loads(proc.stdout)


def gap(repo: Path, *entries: tuple[str, str]) -> Path:
    return write_json(repo / "architecture" / "known-gap.json",
                      {"entries": [{"from": a, "to": b, "reason": "r"} for a, b in entries]})


def test_clean_repo_exits_zero_from_the_plugin_copy(tmp_path) -> None:
    proc = check(make_repo(tmp_path), CLEAN_EDGES, "--format", "json")
    assert proc.returncode == 0, proc.stderr
    data = report(proc)
    assert data["likec4"] == {"version": "1.60.0", "source": "plugin"}
    assert data["breaches"] == [] and data["not_yet_reached"] == [] and data["unmapped"] == []


def test_repo_copy_wins_with_a_note(tmp_path) -> None:
    repo = make_repo(tmp_path)
    make_shim(repo / "node_modules", version="1.59.0")
    proc = check(repo, [BREACH], "--format", "json")
    assert proc.returncode == 1
    assert report(proc)["likec4"] == {"version": "1.59.0", "source": "repo"}
    assert "note: likec4 1.59.0 from repo; tested with 1.60.0" in proc.stderr.splitlines()


def test_parent_folder_copies_are_not_used(tmp_path) -> None:
    outer_repo = tmp_path / unique("a")
    make_shim(outer_repo / "node_modules")
    repo = make_repo(outer_repo)
    outer_engine = tmp_path / unique("b")
    make_shim(outer_engine / "node_modules")
    script = copy_engine(outer_engine)
    proc = check(repo, CLEAN_EDGES, script=script)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: likec4-missing: ")
    assert "npm" in error_lines(proc)[0]


def test_bad_shape_shim_exits_internal(tmp_path) -> None:
    for element in ("{ kind: 'component', tags: [], getMetadata() { return {}; } }",
                    "{ id: 'a', kind: 'component', tags: [], getMetadata() { return { code: ['a'] }; } }"):
        repo = make_repo(tmp_path)
        source = ("export class LikeC4 { static async fromWorkspace() { return { getErrors() { return []; },"
                  " async computedModel() { return { elements() { return [" + element + "]; },"
                  " relationships() { return []; } }; } }; } }\n")
        make_shim(repo / "node_modules", source=source)
        proc = check(repo, CLEAN_EDGES)
        assert proc.returncode == 2
        assert error_lines(proc)[0].startswith("error: internal: ")


def test_model_errors_end_to_end(tmp_path) -> None:
    repo = make_repo(tmp_path, "model {\n  a = component 'A'\n  a -> missing\n  b = nosuchkind 'B'\n}\n")
    proc = check(repo, [])
    assert proc.returncode == 2
    assert proc.stdout == ""
    lines = error_lines(proc)
    assert len(lines) == 2
    assert all(line.startswith("error: model-error: model.c4:") for line in lines)
    assert any(":3:" in line for line in lines) and any(":4:" in line for line in lines)


@pytest.mark.parametrize(
    ("setup", "token"),
    [
        pytest.param("deps-unknown-key", "bad-input", id="deps-unknown-key"),
        pytest.param("gap-empty-reason", "bad-input", id="gap-empty-reason"),
        pytest.param("shards-wrong-type", "bad-input", id="shards-wrong-type"),
        pytest.param("missing-deps", "bad-input", id="missing-deps"),
        pytest.param("deps-outside", "outside-repo", id="deps-outside"),
        pytest.param("unknown-scope", "unknown-scope", id="unknown-scope"),
    ],
)
def test_input_errors_end_to_end(tmp_path, setup: str, token: str) -> None:
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": []})
    args = ["check", "--repo", repo, "--deps", deps]
    if setup == "deps-unknown-key":
        write_json(deps, {"edges": [], "x": 1})
    elif setup == "gap-empty-reason":
        write_json(repo / "architecture" / "known-gap.json", {"entries": [{"from": "shop", "to": "shop.orders", "reason": ""}]})
    elif setup == "shards-wrong-type":
        args += ["--shards", write_json(repo / "shards.json", {"shards": []})]
    elif setup == "missing-deps":
        args[4] = repo / "nope.json"
    elif setup == "deps-outside":
        args[4] = write_json(tmp_path / unique("out") / "deps.json", {"edges": []})
    elif setup == "unknown-scope":
        args += ["--scope", "shop.nope"]
    proc = run_tool(*args)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith(f"error: {token}: ")


def test_deps_through_a_link_outside_is_refused(tmp_path) -> None:
    outside = tmp_path / unique("outside")
    write_json(outside / "deps.json", {"edges": []})
    repo = make_repo(tmp_path)
    link_dir(outside, repo / "linked")
    proc = run_tool("check", "--repo", repo, "--deps", "linked/deps.json")
    assert error_lines(proc)[0].startswith("error: outside-repo: ")


def test_known_new_and_stale(tmp_path) -> None:
    known = make_repo(tmp_path)
    gap(known, ("shop.orders.api", "shop.payments.card"))
    assert check(known, [BREACH]).returncode == 0
    new = make_repo(tmp_path)
    assert check(new, [BREACH]).returncode == 1
    stale = make_repo(tmp_path)
    gap(stale, ("shop.orders", "shop.payments"))
    proc = check(stale, CLEAN_EDGES, "--format", "json")
    assert proc.returncode == 1
    assert report(proc)["gap"]["stale"] == [{"from": "shop.orders", "to": "shop.payments"}]


def test_scope_end_to_end(tmp_path) -> None:
    repo = make_repo(tmp_path)
    proc = check(repo, [BREACH], "--scope", "shop.checkout", "--format", "json")
    assert proc.returncode == 0
    assert report(proc)["breaches"] == []


def test_gap_file_is_untouched(tmp_path) -> None:
    repo = make_repo(tmp_path)
    file = gap(repo, ("shop.orders.api", "shop.payments.card"))
    before = file.read_bytes()
    check(repo, [BREACH, ["shop.checkout.a", "shop.orders.api.b"]])
    assert file.read_bytes() == before


def test_json_report_shape_and_edge_sample(tmp_path) -> None:
    edges = [[f"shop.orders.api.m{i:02d}", "shop.payments.card.n"] for i in range(25)]
    data = report(check(make_repo(tmp_path), edges, "--format", "json"))
    assert list(data) == ["likec4", "breaches", "not_yet_reached", "unmapped", "hot_spots", "gap"]
    breach = data["breaches"][0]
    assert (breach["from"], breach["to"], breach["gap"]) == ("shop.orders.api", "shop.payments.card", "new")
    assert breach["edges"] == [[f"shop.orders.api.m{i:02d}", "shop.payments.card.n"] for i in range(20)]
    assert breach["more_edges"] == 5
    assert list(data["gap"]) == ["known", "new", "stale"]


def test_hot_spots_end_to_end(tmp_path) -> None:
    repo = make_repo(tmp_path)
    shards = write_json(repo / "shards.json", {"shards": {"b": ["shop.payments"], "a": ["shop.payments.card"]}})
    data = report(check(repo, CLEAN_EDGES, "--shards", shards, "--format", "json"))
    assert data["hot_spots"] == [{"element": "shop.payments.card", "shards": ["a", "b"]}]


def test_printed_strings_are_cleaned(tmp_path) -> None:
    long_name = "q" * 250
    edges = [["zz\x1b[31m.evil‮", "shop.orders"], [long_name, "shop.orders"]]
    data = report(check(make_repo(tmp_path), edges, "--format", "json"))
    assert sorted(data["unmapped"]) == sorted(["zz.evil", "q" * 199 + "…"])


def test_text_report_headings_and_summary(tmp_path) -> None:
    repo = make_repo(tmp_path)
    gap(repo, ("shop.checkout", "shop.orders.api"), ("shop.orders", "shop.payments"))
    proc = check(repo, [BREACH, ["shop.checkout.s", "shop.orders.api.t"]])
    assert proc.returncode == 1
    lines = proc.stdout.splitlines()
    headings = [line for line in lines if line in {"New breaches", "Stale gap entries", "Known breaches"}]
    assert headings == ["New breaches", "Stale gap entries", "Known breaches"]
    assert lines[-1].startswith("1 new, 1 stale, 1 known (likec4 ")
    assert lines[-1] == "1 new, 1 stale, 1 known (likec4 1.60.0 from plugin)"
```

- [ ] **Step 2: run RED.** `uv run pytest tests/scripts/test_architecture_delta_check.py -q` — Expected: FAIL (`error: internal: check is not available in this build`)

- [ ] **Step 3: GREEN.**

Append to `skills/shared/scripts/architecture-delta/report.mjs`:

```js
export const EDGE_SAMPLE = 20;

export function checkJson(result, located) {
  const cleanPairs = (list) => [...list].sort(byPair).map(cleanPair);
  return {
    likec4: { version: clean(located.version), source: located.source },
    breaches: [...result.breaches].sort(byPair).map((breach) => {
      const edges = [...breach.edges].sort((x, y) => cmp(x[0], y[0]) || cmp(x[1], y[1]));
      return {
        from: clean(breach.from),
        to: clean(breach.to),
        edges: edges.slice(0, EDGE_SAMPLE).map((edge) => edge.map(clean)),
        more_edges: Math.max(0, edges.length - EDGE_SAMPLE),
        gap: breach.gap,
      };
    }),
    not_yet_reached: cleanPairs(result.notYetReached),
    unmapped: [...result.unmapped].sort(cmp).map(clean),
    hot_spots: [...result.hotSpots].sort((a, b) => cmp(a.element, b.element)).map((spot) => ({
      element: clean(spot.element),
      shards: [...spot.shards].sort(cmp).map(clean),
    })),
    gap: {
      known: cleanPairs(result.gap.known),
      new: cleanPairs(result.gap.new),
      stale: cleanPairs(result.gap.stale),
    },
  };
}

export function checkText(report) {
  const count = (breach) => breach.edges.length + breach.more_edges;
  const sections = [
    ['New breaches', report.breaches.filter((b) => b.gap === 'new').map((b) => `  ${b.from} -> ${b.to} (${count(b)} edges)`)],
    ['Stale gap entries', report.gap.stale.map((p) => `  ${p.from} -> ${p.to} (remove this entry)`)],
    ['Known breaches', report.breaches.filter((b) => b.gap === 'known').map((b) => `  ${b.from} -> ${b.to} (${count(b)} edges)`)],
    ['Not yet reached', report.not_yet_reached.map((p) => `  ${p.from} -> ${p.to}`)],
    ['Unmapped code', report.unmapped.map((module) => `  ${module}`)],
    ['Shared hot spots', report.hot_spots.map((spot) => `  ${spot.element}: ${spot.shards.join(', ')}`)],
  ];
  const lines = [];
  for (const [heading, items] of sections) {
    if (items.length === 0) continue;
    lines.push(heading, ...items, '');
  }
  lines.push(
    `${report.gap.new.length} new, ${report.gap.stale.length} stale, ${report.gap.known.length} known `
      + `(likec4 ${report.likec4.version} from ${report.likec4.source})`,
  );
  return `${lines.join('\n')}\n`;
}
```

In `skills/shared/scripts/architecture-delta.mjs`, add to the imports:

```js
import { readJson, parseDeps, parseGap, parseShards } from './architecture-delta/inputs.mjs';
import { compare } from './architecture-delta/match.mjs';
import { exportJson, checkJson, checkText } from './architecture-delta/report.mjs';
```

(remove the old `import { exportJson } from './architecture-delta/report.mjs';` line), and replace `main` with:

```js
function readOptional(repo, value, fallback, flag, parse) {
  const target = resolveInside(repo, value ?? fallback, flag);
  if (!target.exists) {
    if (value !== null) throw new ToolError('bad-input', `${flag} file not found`);
    return null;
  }
  return parse(readJson(target.path, flag));
}

async function runCheck(args, deadline, loaded) {
  const { repo, modelDir, located, model } = loaded;
  const ids = model.elements.map((element) => element.id);
  const deps = resolveInside(repo, args.deps, '--deps');
  if (!deps.exists) throw new ToolError('bad-input', '--deps file not found');
  const edges = parseDeps(readJson(deps.path, '--deps'));
  deadline.check();
  const gap = readOptional(repo, args.gap, path.join(modelDir, 'known-gap.json'), '--gap', (data) => parseGap(data, ids)) ?? [];
  deadline.check();
  const shards = args.shards === null ? null : readOptional(repo, args.shards, null, '--shards', (data) => parseShards(data, ids));
  deadline.check();
  if (args.scope !== null) {
    const known = new Set(ids);
    const unknown = args.scope.filter((id) => !known.has(id));
    if (unknown.length > 0) throw new ToolError('unknown-scope', unknown.map((id) => `${id} is not a model element`));
  }
  const result = compare(model, edges, { separator: args.separator, gap, scope: args.scope, shards, tick: deadline.check });
  const report = checkJson(result, located);
  const output = args.format === 'json' ? `${JSON.stringify(report, null, 2)}\n` : checkText(report);
  return { output, exitCode: result.exitCode };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const loaded = await loadRepoModel(args, deadline);
  let output;
  let exitCode = 0;
  if (args.command === 'export') {
    output = `${JSON.stringify(exportJson(loaded.model), null, 2)}\n`;
  } else {
    ({ output, exitCode } = await runCheck(args, deadline, loaded));
  }
  deadline.stop();
  process.stdout.write(output);
  process.exitCode = exitCode;
}
```

Delete `test_check_is_not_available_yet` from `tests/scripts/test_architecture_delta_export.py`.

- [ ] **Step 4: run GREEN and the whole suite.** `uv run pytest -q` — Expected: PASS
- [ ] **Step 5: refactor — confirm no `check is not available` text remains:** `rg -n "not available in this build" skills tests` — Expected: no output.
- [ ] **Step 6: commit.**

```bash
git add skills/shared/scripts/architecture-delta.mjs skills/shared/scripts/architecture-delta/report.mjs tests/scripts/test_architecture_delta_check.py tests/scripts/test_architecture_delta_export.py
git commit -m "feat(20): check command with JSON and text reports"
```

---

### Task 12: Safety — no network, limits end to end, internal errors, no writes or subprocesses

**Tier:** standard — tests and fixtures only, unless a test exposes a gap.

**Files:**
- Create: `tests/fixtures/architecture/no-network.mjs`
- Create: `tests/fixtures/architecture/stdout-throws.mjs`
- Test: `tests/scripts/test_architecture_delta_safety.py`

**Callers that move with this task:** none

**Reviewer looks at:**
- internal error exit code — mutation: set `process.exitCode = 1` in the top-level handler — killed by: `test_unexpected_error_is_internal_never_one`
- no subprocess import — mutation: add `import { spawn } from 'node:child_process'` to `match.mjs` — killed by: `test_tool_source_never_spawns_or_writes`
- timeout on `check` — mutation: drop `deadline.check()` after reading `--deps` and the timer — killed by: `test_limits_end_to_end[timeout]`

- Satisfies Spec AC: AC-21, AC-22 (`edge-cap`, `file-size`, `model-size`, `timeout` end to end; `element-cap` is covered in Task 6 through the same `loadModel`), AC-26; Scope's source test
- Decisions applied: none
- **Test retention:** Permanent

- [ ] **Step 1: write the fixtures and RED tests.**

`tests/fixtures/architecture/no-network.mjs`:

```js
// Test preload: any network call throws.
import http from 'node:http';
import https from 'node:https';

const deny = () => {
  throw new Error('network access attempted');
};
globalThis.fetch = deny;
http.request = deny;
http.get = deny;
https.request = deny;
https.get = deny;
```

`tests/fixtures/architecture/stdout-throws.mjs`:

```js
// Test preload: the first stdout write that carries a report throws.
const original = process.stdout.write.bind(process.stdout);
let armed = true;
process.stdout.write = (chunk, ...rest) => {
  if (armed && String(chunk).includes('"breaches"')) {
    armed = false;
    throw new Error('forced stdout failure');
  }
  return original(chunk, ...rest);
};
```

`tests/scripts/test_architecture_delta_safety.py`:

```python
from __future__ import annotations

import re

import pytest

from arch_delta_support import FIXTURES, LIB, SCRIPT, error_lines, make_repo, require_node, run_tool, write_json

require_node()

MB = 1024 * 1024
CLEAN_EDGES = [["shop.orders.api.handler", "shop.checkout.service"]]


def test_no_network_check_and_export(tmp_path) -> None:
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": CLEAN_EDGES})
    assert run_tool("check", "--repo", repo, "--deps", deps, preload=FIXTURES / "no-network.mjs").returncode == 0
    assert run_tool("export", "--repo", repo, preload=FIXTURES / "no-network.mjs").returncode == 0


@pytest.mark.parametrize("case", ["edge-cap", "file-size", "model-size", "timeout"])
def test_limits_end_to_end(tmp_path, case: str) -> None:
    repo = make_repo(tmp_path)
    deps = repo / "deps.json"
    write_json(deps, {"edges": CLEAN_EDGES})
    extra: list[str] = []
    if case == "edge-cap":
        deps.write_text('{"edges":[' + ",".join(['["a","b"]'] * 1_000_001) + "]}", encoding="utf-8")
    elif case == "file-size":
        deps.write_text('{"edges":[]}' + " " * (50 * MB), encoding="utf-8")
    elif case == "model-size":
        for i in range(2001):
            (repo / "architecture" / f"f{i}.txt").write_text("x", encoding="utf-8")
    elif case == "timeout":
        extra = ["--timeout", "0"]
    proc = run_tool("check", "--repo", repo, "--deps", deps, *extra)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith(f"error: {case}: ")


def test_unexpected_error_is_internal_never_one(tmp_path) -> None:
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": [["shop.orders.api.x", "shop.payments.card.y"]]})
    proc = run_tool("check", "--repo", repo, "--deps", deps, "--format", "json", preload=FIXTURES / "stdout-throws.mjs")
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: internal: forced stdout failure"]


def test_tool_source_never_spawns_or_writes() -> None:
    sources = [SCRIPT, *sorted(LIB.glob("*.mjs"))]
    forbidden = re.compile(
        r"child_process|worker_threads|\b(writeFile|appendFile|mkdir|rm|unlink|rename|copyFile|cp"
        r"|createWriteStream|symlink|link|truncate|chmod|chown|utimes)(Sync)?\s*\("
    )
    for source in sources:
        assert not forbidden.search(source.read_text(encoding="utf-8")), source
```

- [ ] **Step 2: run RED → GREEN.** Run: `uv run pytest tests/scripts/test_architecture_delta_safety.py -q`. These tests pin behaviour built in Tasks 2–11, so they are expected to PASS on first run. Then prove each one can fail: temporarily set `process.exitCode = 1` in the top-level handler of `architecture-delta.mjs` and run `uv run pytest tests/scripts/test_architecture_delta_safety.py::test_unexpected_error_is_internal_never_one -q` (Expected: FAIL), then restore it with `git checkout skills/shared/scripts/architecture-delta.mjs`. If any test fails on the unmodified code, stop and report: that is a gap in Tasks 2–11, not something to patch silently here.

- [ ] **Step 3: run the whole suite.** `uv run pytest -q` — Expected: PASS
- [ ] **Step 4: refactor — none.**
- [ ] **Step 5: commit.**

```bash
git add tests/fixtures/architecture/no-network.mjs tests/fixtures/architecture/stdout-throws.mjs tests/scripts/test_architecture_delta_safety.py
git commit -m "test(20): no network, limits end to end, internal errors, no writes or subprocesses"
```

---

## Spec coverage

| Spec item | Task(s) |
|---|---|
| AC-1, AC-2 | 4, 11 (8 for the version note and missing case through `export`) |
| AC-2b | 6, 11 |
| AC-3 | 6, 11 |
| AC-4 | 5, 8 |
| AC-5 | 7, 11 |
| AC-6, AC-8, AC-9, AC-10, AC-11 | 9 |
| AC-7 | 6, 8 |
| AC-12 | 10, 11 |
| AC-13 | 10, 11 |
| AC-14, AC-15, AC-16 | 10, 11 |
| AC-17 | 11 |
| AC-18, AC-23 | 8 |
| AC-19, AC-20, AC-27 | 11 (2 for the cleaning rule) |
| AC-21, AC-26 | 12 |
| AC-22 | 5, 6, 7, 8, 12 |
| AC-24 | 5, 8 |
| AC-25 | 3, 8 |
| Scope: pin, lockfile, installed version, `.gitignore`, `.gitattributes`, failing session check | 1 |
| Scope: source test, no-network preload, loading-test layout | 12, 4, 11 |
| Scope: `npm audit` recorded at pin time | 1 |

Deviation from the spec's Scope wording: tests are split across `tests/scripts/test_architecture_delta_*.py` files by area, with shared helpers in `tests/scripts/arch_delta_support.py`, rather than one `test_architecture_delta.py`. The behaviour covered is unchanged.
