# Architecture Docs Tool: Commands and Output Folder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `node skills/shared/scripts/architecture-docs.mjs build|check` loads the model as the delta tool does, enforces the output-folder write rules, and writes (or checks) its first document, `pack/model.json`.

**Architecture:** This repository has no architecture model. The delta tool's shared start (deadline, model and records load, optional input files, run wrapper) moves from `architecture-delta.mjs` into `architecture-delta/load.mjs` so both tools use it. The new tool's modules live in `skills/shared/scripts/architecture-docs/`: `args.mjs` (flags), `out.mjs` (write rules 1 and 2: where the folder may be and what it may hold), `writer.mjs` (write rule 3; the only module that changes files), `build.mjs` (the documents of one build and write rule 4). Later plans add documents to `buildFiles`.

**Tech Stack:** Node ESM, LikeC4 1.60.0, pytest.

**Spec:** `docs/superpowers/specs/2026-11-17-architecture-docs-design.md`, "The tool" (commands, output folder, write rules 1–5, layout), "AI pack" (`pack/model.json` only), AC-8, AC-10, AC-11, AC-13 (JSON marker part), AC-14, AC-15, AC-16, AC-17 — decisions applied: none. Plan 2 of the spec's four is split in three (2a this plan; 2b writers and the overview; 2c the rest of the pack) to keep each plan within the sizing rule. AC-9 is covered here with a stale marked file in place of a removed area document; plan 3 adds the area case. Known-gap cleaning (`readGap`) is read here for error parity and first used, and tested, in plan 2b.

**Open decisions:** none

**Size:** 6 tasks, 2 entry paths (`build`, `check`), 1100 lines (reported, not a target)

**Trust boundary:** changed — see Trust-boundary table. The new tool writes files; the delta tool stays read-only.

### Risk & Confidence Assessment

**Confidence:** 90% — the write rules are fully specified and each has a direct test; the refactor of the delta tool's start is a move under a large existing suite.

**Complexity Risk:** Medium — write rules 1 and 2 are the trust boundary: a wrong containment or marker check lets the tool overwrite a person's file. Tasks 3 to 5 are strong tier.

**Environmental Risk:** Medium — Windows: junctions as links, case-insensitive paths, CRLF checkouts, rename over an existing file. Each has a test.

**Main failure modes:** the refactor changing the delta tool's exit or error behaviour (pinned by its suite, including the stdout-throws fixture); a containment check done on a lexical path through a link (Task 3 walks every existing part with `lstat`); a marker check that reads too much or accepts a near-marker (Task 4 tests).

**Unknown variables:**
- Whether `fs.renameSync` over an existing file can fail on Windows when another program holds the file open. The writer reports any failure as `out-error` naming the path; no retry.

---

## Caller and test sweep

Searched: `skills/`, `tests/` with `rg -n "loadRepoModel|startDeadline|readOptional|SHIPPED_SPEC|ENGINE_ROOT|def call\(|def lib_url\(|lib_url\(|copy_engine" skills/shared/scripts tests/scripts`.

| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |
|---|---|---|---|---|
| `startDeadline`, `loadRepoModel`, `readOptional`, the fail handler move to `architecture-delta/load.mjs` | `skills/shared/scripts/architecture-delta.mjs` | caller | 1 | imports them from `./architecture-delta/load.mjs`; `main` returns `{ output, exitCode }`; the file ends with `runCli(main);` |
| `ENGINE_ROOT`, `SHIPPED_SPEC` now computed from `load.mjs`'s folder | `tests/scripts/arch_delta_support.py` `copy_engine` | helper | — | none: it copies the whole `architecture-delta` folder and the script, so `load.mjs` sits in the same place relative to the copied root |
| `call(module, fn, *args)` gains keyword `lib` | `tests/scripts/arch_delta_support.py` `call`, `lib_url` | helper | 2 | `def lib_url(module: str, lib: Path = LIB) -> str: return (lib / module).as_uri()`; `def call(module: str, fn: str, *args: object, lib: Path = LIB) -> dict:` using `lib_url(module, lib)` |
| same | every existing `call(...)` | caller | — | none: the keyword defaults to the delta folder |
| new constants | `tests/scripts/arch_delta_support.py` | helper | 2 | add `DOCS_SCRIPT = ENGINE / "skills" / "shared" / "scripts" / "architecture-docs.mjs"` and `DOCS_LIB = ENGINE / "skills" / "shared" / "scripts" / "architecture-docs"` after `LIB` |

## Trust-boundary table

| Boundary | Rule | Mechanism | Task | Test |
|---|---|---|---|---|
| Where the tool may write | write rule 1 | `out.mjs` `resolveOut`: every existing part of the path below `--repo` checked with `lstat` (no link, no file); then, on native real paths (short names and case settled), inside `--repo`, not holding the model folder, inside the model folder only as `generated` in any case | 3 | `test_resolve_out_*`, `test_build_refuses_bad_out` |
| What may be overwritten or deleted | write rule 2 | `out.mjs` `listOut`: every file marked by type, or a temporary or operating-system file; every folder a named one; no link; no file over 50 MB; checked before the model loads | 4 | `test_list_out_*`, `test_build_and_check_refuse_an_unmarked_file` |
| How files change | write rule 3 | `writer.mjs` `writeOutput`: write to a temporary name, rename into place, then delete stale marked files, then empty named folders; every failure `out-error` naming the path | 5 | `test_write_output_*` |
| Which code may change files | threat model, least privilege | only `writer.mjs` calls a file-changing function; files are opened only for reading elsewhere | 5 | `test_only_the_writer_changes_files`, `test_files_are_opened_only_for_reading` |
| The delta tool stays read-only | delta spec | `load.mjs` sits in `architecture-delta/` and is covered by `test_tool_source_never_spawns_or_writes` | 1 | existing test |

## Checkpoints

| Checkpoint | After task | Tasks covered | Reviewer looks at |
|---|---|---|---|
| C1 | 3 | 1–3 | Task 1 pinning, Task 2 items 1–2, Task 3 items 1–5; focused tests `uv run pytest -q tests/scripts/test_architecture_docs_out.py tests/scripts/test_architecture_docs_args.py` and `uv run pytest -q tests/scripts -k architecture_delta` |
| C2 | 6 | 4–6 | Task 4 items 1–5, Task 5 items 1–4, Task 6 items 1–5; full suite `uv run pytest -q` |

Checkpoint reviewers on this machine: one scratch copy, one mutation at a time, in the foreground.

---

### Task 1: the delta tool's shared start moves into `load.mjs`

**Tier:** standard — a move of existing code; the delta suite pins it.

**Files:**
- Create: `skills/shared/scripts/architecture-delta/load.mjs`
- Modify: `skills/shared/scripts/architecture-delta.mjs`

**Callers that move with this task:** `architecture-delta.mjs` (sweep row 1).

**Pinned by:** behaviour is unchanged; existing tests pin it:
- exit codes and error lines for every command: `tests/scripts/test_architecture_delta_check.py`, `test_architecture_delta_export.py`, `test_architecture_delta_safety.py::test_limits_end_to_end` (`model-size`, `file-size`, `edge-cap`, `timeout` first lines);
- a failure after output starts is `internal`, exit 2, nothing else: `test_architecture_delta_safety.py::test_unexpected_error_is_internal_never_one` asserts `error_lines(proc) == ["error: internal: forced stdout failure"]`;
- the engine and repository LikeC4 copies are found from the moved code's location: `tests/scripts/test_architecture_delta_likec4.py` (uses `copy_engine`);
- the shipped spec copy is found: `test_architecture_delta_export.py::test_export_checks_the_spec_copy`;
- the delta tool still never writes: `test_tool_source_never_spawns_or_writes` globs `architecture-delta/*.mjs`, which now includes `load.mjs`.

- Satisfies Spec AC: none (refactor)
- **Test retention:** n/a

- [ ] **Step 1:** Run `uv run pytest -q tests/scripts -k architecture_delta` and note the pass count (baseline).
- [ ] **Step 2:** Create `load.mjs` with this header and imports, then **move verbatim** from `architecture-delta.mjs` the functions `startDeadline`, `loadRepoModel` and `readOptional`, each now `export`ed:

```js
// Shared start of the architecture tools: the deadline, the model and records load, optional input files, and the run wrapper.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ToolError, errorLines } from './errors.mjs';
import { locateLikeC4, importLikeC4, versionNote } from './likec4.mjs';
import { walkModelDir, checkSpecCopy } from './walk.mjs';
import { loadModel } from './model.mjs';
import { readRecords } from './records.mjs';
import { realRepo, resolveInside } from './paths.mjs';
import { readJson } from './inputs.mjs';

const LIB_DIR = path.dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = path.resolve(LIB_DIR, '..', '..', '..', '..');
const SHIPPED_SPEC = path.resolve(LIB_DIR, '..', '..', 'architecture', 'c4.c4');
```

Then add, replacing the script's `failed`/`fail` block and its three `process.on`/`stdout.on` lines and the final `main(...).catch(fail)` line:

```js
// Spec, Errors: any failure, including one thrown later from a timer or a promise and a failed
// stdout write, is exit 2; the first one is reported and nothing after it can set another code.
// `main` returns { output, exitCode }; the output is written only when nothing has failed.
export function runCli(main) {
  let failed = false;
  const fail = (err) => {
    if (failed) return;
    failed = true;
    const error = err instanceof ToolError ? err : new ToolError('internal', err?.message ?? String(err));
    process.exitCode = 2;
    process.stderr.write(`${errorLines(error).join('\n')}\n`);
  };
  process.on('uncaughtException', fail);
  process.on('unhandledRejection', fail);
  process.stdout.on('error', fail);
  main(process.argv.slice(2))
    .then((result) => {
      if (failed) return;
      process.stdout.write(result.output);
      process.exitCode = result.exitCode;
    })
    .catch(fail);
}
```

- [ ] **Step 3:** In `architecture-delta.mjs`: delete the moved functions, the `SCRIPT_DIR`, `ENGINE_ROOT`, `SHIPPED_SPEC` constants and the fail block; drop imports no longer used (`fs`, `fileURLToPath`, `errorLines`, `locateLikeC4`, `importLikeC4`, `versionNote`, `walkModelDir`, `checkSpecCopy`, `loadModel`, `readRecords`, `realRepo`); add `import { startDeadline, loadRepoModel, readOptional, runCli } from './architecture-delta/load.mjs';`. Keep `runCheck` as it is. Replace `main` with:

```js
async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const loaded = await loadRepoModel(args, deadline);
  const result = args.command === 'export'
    ? { output: `${JSON.stringify(exportJson(loaded.model, loaded.records), null, 2)}\n`, exitCode: 0 }
    : await runCheck(args, deadline, loaded);
  deadline.stop();
  return result;
}

runCli(main);
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts -k architecture_delta`. Expected: PASS with the Step 1 count.
- [ ] **Step 5:** No refactor beyond the move.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-delta.mjs skills/shared/scripts/architecture-delta/load.mjs && git commit -m "refactor(#32): the delta tool's shared start moves into load.mjs"`

### Task 2: the docs tool's command line

**Tier:** fast — complete code.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/args.mjs`
- Modify: `tests/scripts/arch_delta_support.py` (sweep rows 3–5)
- Test: `tests/scripts/test_architecture_docs_args.py` (create)

**Callers that move with this task:** sweep rows 3–5.

**Reviewer looks at:**
- defaults — mutation: default `--model` to `.` — killed by: `test_docs_args_defaults`
- usage problems — mutation: accept a flag given twice — killed by: `test_docs_args_problems[twice]`

- Satisfies Spec AC: none directly ("The tool": commands and flags)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Make the sweep edits to `arch_delta_support.py`. Create `tests/scripts/test_architecture_docs_args.py`:

```python
"""Command line of the architecture docs tool (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

import pytest

from arch_delta_support import DOCS_LIB, call, require_node

require_node()


def parse(*argv: str) -> dict:
    return call("args.mjs", "parseArgs", list(argv), lib=DOCS_LIB)


def test_docs_args_defaults() -> None:
    assert parse("build", "--repo", ".")["value"] == {
        "command": "build", "repo": ".", "model": "docs/architecture", "gap": None, "out": None, "timeout": 60,
    }
    assert parse("check", "--repo", "r", "--model", "m", "--gap", "g", "--out", "o", "--timeout", "5")["value"] == {
        "command": "check", "repo": "r", "model": "m", "gap": "g", "out": "o", "timeout": 5,
    }


@pytest.mark.parametrize(("argv", "detail"), [
    pytest.param((), "unknown subcommand (none); use build or check", id="none"),
    pytest.param(("export", "--repo", "."), "unknown subcommand export; use build or check", id="export"),
    pytest.param(("build",), "--repo is required", id="no-repo"),
    pytest.param(("build", "--repo", ".", "--deps", "x"), "unknown flag for build: --deps", id="deps"),
    pytest.param(("build", "--repo"), "--repo needs a value", id="no-value"),
    pytest.param(("check", "--repo", ".", "--repo", "."), "--repo given twice", id="twice"),
    pytest.param(("build", "--repo", ".", "--out", ""), "--out must not be empty", id="empty-out"),
    pytest.param(("build", "--repo", ".", "--timeout", "601"), "--timeout must be a whole number from 0 to 600", id="timeout"),
])
def test_docs_args_problems(argv: tuple, detail: str) -> None:
    result = parse(*argv)
    assert (result["token"], result["details"]) == ("usage", [detail])
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_args.py`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Create `args.mjs`:

```js
// Command-line parsing for the architecture docs tool. Every problem is a `usage` error.
import { ToolError } from '../architecture-delta/errors.mjs';

const COMMANDS = ['build', 'check'];
const FLAGS = ['--repo', '--model', '--gap', '--out', '--timeout'];
const MAX_TIMEOUT = 600;
const usage = (detail) => new ToolError('usage', detail);

export function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (!COMMANDS.includes(command ?? '')) throw usage(`unknown subcommand ${command ?? '(none)'}; use build or check`);
  const opts = {};
  for (let i = 0; i < rest.length; i += 2) {
    const flag = rest[i];
    const value = rest[i + 1];
    if (!FLAGS.includes(flag)) throw usage(`unknown flag for ${command}: ${flag}`);
    if (value === undefined || value.startsWith('--')) throw usage(`${flag} needs a value`);
    if (Object.hasOwn(opts, flag)) throw usage(`${flag} given twice`);
    opts[flag] = value;
  }
  if (!opts['--repo']) throw usage('--repo is required');
  for (const flag of ['--model', '--gap', '--out']) if (opts[flag] === '') throw usage(`${flag} must not be empty`);
  const timeoutText = opts['--timeout'] ?? '60';
  if (!/^\d+$/.test(timeoutText) || Number(timeoutText) > MAX_TIMEOUT) {
    throw usage(`--timeout must be a whole number from 0 to ${MAX_TIMEOUT}`);
  }
  return {
    command,
    repo: opts['--repo'],
    model: opts['--model'] ?? 'docs/architecture',
    gap: opts['--gap'] ?? null,
    out: opts['--out'] ?? null,
    timeout: Number(timeoutText),
  };
}
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_args.py tests/scripts -k "architecture_delta or architecture_docs"`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/args.mjs tests/scripts/arch_delta_support.py tests/scripts/test_architecture_docs_args.py && git commit -m "feat(#32): the docs tool's command line"`

### Task 3: where the output folder may be (write rule 1)

**Tier:** strong — trust boundary: this check decides where the tool may write.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/out.mjs` (`resolveOut`)
- Test: `tests/scripts/test_architecture_docs_out.py` (create)

**Callers that move with this task:** none.

**Reviewer looks at:**
- outside the repository — mutation: drop the `isInside(target, repo)` check — killed by: `test_resolve_out_refuses[outside]`
- links along the path — mutation: stop the part walk at the first part — killed by: `test_resolve_out_refuses_a_link_on_the_way` (the link is the second part)
- holding the model folder — mutation: `isInside(target, modelDir)` instead of `isInside(modelDir, target)` — killed by: `test_resolve_out_refuses[repo-root]`, `[docs]`
- inside the model folder only as `generated` — mutation: compare without `toLowerCase()` — killed by: `test_resolve_out_accepts_generated_in_any_case`; mutation: drop the rule — killed by: `[decisions]`, `[docs-out]`
- a nested path under `generated` — mutation: test `startsWith('generated')` — killed by: `test_resolve_out_refuses[generated-child]`
- real paths, not lexical — mutation: run the three checks on `lexical`, `repo` and `modelDir` — killed by: `test_resolve_out_refuses_another_spelling_of_the_model_folder` (Windows short name; skipped where the volume has no short names and the file system is case-sensitive)

- Satisfies Spec AC: AC-14 (with Task 6's end-to-end test)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_docs_out.py`:

```python
"""The docs tool's output folder: write rules 1 and 2 (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from arch_delta_support import DOCS_LIB, call, link_dir, require_node, unique

require_node()


def layout(tmp_path: Path) -> tuple[Path, Path]:
    repo = Path(os.path.realpath(tmp_path)) / unique("r")
    model = repo / "docs" / "architecture"
    (model / "decisions").mkdir(parents=True)
    return repo, model


def resolve(repo: Path, model: Path, value: str | None) -> dict:
    return call("out.mjs", "resolveOut", str(repo), str(model), value, lib=DOCS_LIB)


def test_resolve_out_defaults_to_the_generated_folder(tmp_path) -> None:
    repo, model = layout(tmp_path)
    assert resolve(repo, model, None)["value"] == str(model / "generated")


def test_resolve_out_accepts_a_folder_elsewhere_in_the_repo(tmp_path) -> None:
    repo, model = layout(tmp_path)
    assert resolve(repo, model, "site/docs")["value"] == str(repo / "site" / "docs")


def test_resolve_out_accepts_generated_in_any_case(tmp_path) -> None:
    repo, model = layout(tmp_path)
    assert resolve(repo, model, "docs/architecture/Generated")["value"] == str(model / "Generated")


@pytest.mark.parametrize(("value", "detail"), [
    pytest.param("../elsewhere", "--out lies outside --repo", id="outside"),
    pytest.param(".", "--out must not hold the model folder", id="repo-root"),
    pytest.param("docs", "--out must not hold the model folder", id="docs"),
    pytest.param("docs/architecture", "--out must not hold the model folder", id="model"),
    pytest.param("docs/architecture/decisions", "--out inside the model folder must be its generated folder", id="decisions"),
    pytest.param("docs/architecture/docs-out", "--out inside the model folder must be its generated folder", id="docs-out"),
    pytest.param("docs/architecture/generated/x", "--out inside the model folder must be its generated folder", id="generated-child"),
])
def test_resolve_out_refuses(tmp_path, value: str, detail: str) -> None:
    repo, model = layout(tmp_path)
    result = resolve(repo, model, value)
    assert (result["token"], result["details"]) == ("out-error", [detail])


def test_resolve_out_refuses_a_link_on_the_way(tmp_path) -> None:
    repo, model = layout(tmp_path)
    (repo / "site").mkdir()
    target = tmp_path / unique("t")
    target.mkdir()
    link_dir(target, repo / "site" / "via")
    result = resolve(repo, model, "site/via/out")
    assert (result["token"], result["details"]) == ("out-error", ["--out passes through a link: site/via"])


def other_spelling(target: Path) -> str | None:
    """Another spelling of an existing folder that names the same folder: its Windows short name, or its upper case."""
    if sys.platform == "win32":
        import ctypes
        buffer = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(str(target), buffer, 1024) and buffer.value.lower() != str(target).lower():
            return buffer.value
        return None
    upper = str(target).upper()
    return upper if os.path.exists(upper) and os.path.samefile(upper, target) else None


def test_resolve_out_refuses_another_spelling_of_the_model_folder(tmp_path) -> None:
    repo, model = layout(tmp_path)
    alternate = other_spelling(model)
    if alternate is None:
        pytest.skip("no other spelling of the model folder on this file system")
    result = resolve(repo, model, str(Path(alternate) / "notes"))
    assert (result["token"], result["details"]) == ("out-error", ["--out inside the model folder must be its generated folder"])


def test_resolve_out_refuses_a_file_on_the_way_or_as_the_folder(tmp_path) -> None:
    repo, model = layout(tmp_path)
    (repo / "f").write_text("x", encoding="utf-8")
    on_the_way = resolve(repo, model, "f/out")
    as_folder = resolve(repo, model, "f")
    assert (on_the_way["token"], on_the_way["details"]) == ("out-error", ["--out passes through a file: f"])
    assert (as_folder["token"], as_folder["details"]) == ("out-error", ["--out is not a folder"])
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_out.py`. Expected: FAIL (module not found).
- [ ] **Step 3: GREEN.** Create `out.mjs`:

```js
// The docs tool's output folder: where it may be (write rule 1) and what it may hold (write rule 2).
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from '../architecture-delta/errors.mjs';
import { isInside } from '../architecture-delta/paths.mjs';

export const GENERATED = 'generated';
const outError = (detail) => new ToolError('out-error', detail);
const shown = (root, target) => path.relative(root, target).split(path.sep).join('/');

function lstatOrNull(target) {
  try {
    return fs.lstatSync(target);
  } catch (err) {
    if (err?.code === 'ENOENT') return null;
    throw err;
  }
}

// Spec, write rule 1, through real paths: every existing part of the path below `--repo` is checked with `lstat`, then
// the checks run on the native real path (which settles Windows short names and letter case), and that path is returned.
export function resolveOut(repo, modelDir, value) {
  const lexical = value === null ? path.join(modelDir, GENERATED) : path.resolve(repo, value);
  if (!isInside(lexical, repo)) throw outError('--out lies outside --repo');
  let current = repo;
  let deepest = repo;
  const rest = [];
  for (const part of path.relative(repo, lexical).split(path.sep).filter((item) => item !== '')) {
    if (rest.length > 0) {
      rest.push(part);
      continue;
    }
    current = path.join(current, part);
    const stat = lstatOrNull(current);
    if (stat === null) {
      rest.push(part);
      continue;
    }
    if (stat.isSymbolicLink()) throw outError(`--out passes through a link: ${shown(repo, current)}`);
    if (!stat.isDirectory()) {
      if (current === lexical) throw outError('--out is not a folder');
      throw outError(`--out passes through a file: ${shown(repo, current)}`);
    }
    deepest = current;
  }
  const real = path.join(fs.realpathSync.native(deepest), ...rest);
  const repoReal = fs.realpathSync.native(repo);
  const modelReal = fs.existsSync(modelDir) ? fs.realpathSync.native(modelDir) : modelDir;
  if (!isInside(real, repoReal)) throw outError('--out lies outside --repo');
  if (isInside(modelReal, real)) throw outError('--out must not hold the model folder');
  // Spec: inside the model folder only its `generated` folder, matched in any case as the model walk matches it.
  if (isInside(real, modelReal) && path.relative(modelReal, real).toLowerCase() !== GENERATED) {
    throw outError(`--out inside the model folder must be its ${GENERATED} folder`);
  }
  return real;
}
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_out.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/out.mjs tests/scripts/test_architecture_docs_out.py && git commit -m "feat(#32): the docs output folder must be inside the repository, outside the model's own files"`

### Task 4: what the output folder may hold (write rule 2)

**Tier:** strong — trust boundary: this check decides what the tool may overwrite or delete.

**Files:**
- Modify: `skills/shared/scripts/architecture-docs/out.mjs` (add `MARKER`, `TEMP_PREFIX`, `FOLDERS`, `FILE_LIMIT`, `isMarked`, `listOut`)
- Test: `tests/scripts/test_architecture_docs_out.py` (append)

**Callers that move with this task:** none.

**Reviewer looks at:**
- the Markdown and HTML marker — mutation: `startsWith(MARKER)` instead of equality — killed by: `test_list_out_refuses[near-marker]`
- the byte-order mark and CR — mutation: drop the BOM strip — killed by: `test_list_out_accepts_a_marker_after_a_bom_and_before_cr`
- the JSON marker is the first key — mutation: accept `generated` anywhere — killed by: `test_list_out_refuses[json-second-key]`
- named folders only — mutation: accept any folder — killed by: `test_list_out_refuses[unknown-folder]`, `[unknown-nested]`
- links and size — mutation: drop the link check, or the size check, or check size only for marked files — killed by: `test_list_out_refuses_a_link`, `test_list_out_refuses_a_file_over_50_mb[big.md]`, `[.architecture-docs-1]`

- Satisfies Spec AC: AC-11 (with Task 6), AC-13 (JSON marker)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Append to `tests/scripts/test_architecture_docs_out.py`:

```python
MARKER = "<!-- Generated by architecture-docs from the architecture model. Do not edit. -->"
BOM = bytes([0xEF, 0xBB, 0xBF])
MB = 1024 * 1024


def listing(folder: Path) -> dict:
    return call("out.mjs", "listOut", str(folder), lib=DOCS_LIB)


def put(folder: Path, rel: str, content: str | bytes) -> None:
    target = folder / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        target.write_bytes(content)
    else:
        target.write_text(content, encoding="utf-8", newline="")


def test_list_out_of_a_missing_folder_is_empty(tmp_path) -> None:
    assert listing(tmp_path / "nope")["value"] == {"files": [], "temps": []}


def test_list_out_lists_marked_and_temporary_files(tmp_path) -> None:
    folder = tmp_path / "out"
    put(folder, "index.html", MARKER + "\n<p>x</p>\n")
    put(folder, "areas/a.md", MARKER + "\n# A\n")
    put(folder, "pack/model.json", '{"generated": "architecture-docs", "export": {}}')
    put(folder, ".architecture-docs-7", "partial")
    put(folder, ".DS_Store", "os")
    assert listing(folder)["value"] == {"files": ["areas/a.md", "index.html", "pack/model.json"], "temps": [".architecture-docs-7"]}


def test_list_out_accepts_a_marker_after_a_bom_and_before_cr(tmp_path) -> None:
    folder = tmp_path / "out"
    put(folder, "README.md", BOM + MARKER.encode("utf-8") + b"\r\n# x\r\n")
    assert listing(folder)["value"] == {"files": ["README.md"], "temps": []}


@pytest.mark.parametrize(("rel", "content", "detail"), [
    pytest.param("notes.md", "hello\n", "notes.md was not written by architecture-docs", id="unmarked"),
    pytest.param("notes.md", MARKER + " extra\n", "notes.md was not written by architecture-docs", id="near-marker"),
    pytest.param("x.json", '{"a": 1, "generated": "architecture-docs"}', "x.json was not written by architecture-docs", id="json-second-key"),
    pytest.param("x.json", "{not json", "x.json was not written by architecture-docs", id="json-invalid"),
    pytest.param("a.txt", MARKER + "\n", "a.txt was not written by architecture-docs", id="other-type"),
    pytest.param("extra/a.md", MARKER + "\n", "extra is not a folder the tool makes", id="unknown-folder"),
    pytest.param("pack/x/a.md", MARKER + "\n", "pack/x is not a folder the tool makes", id="unknown-nested"),
])
def test_list_out_refuses(tmp_path, rel: str, content: str, detail: str) -> None:
    folder = tmp_path / "out"
    put(folder, rel, content)
    result = listing(folder)
    assert (result["token"], result["details"]) == ("out-error", [detail])


def test_list_out_refuses_a_link(tmp_path) -> None:
    folder = tmp_path / "out"
    folder.mkdir()
    target = tmp_path / unique("t")
    target.mkdir()
    link_dir(target, folder / "areas")
    result = listing(folder)
    assert (result["token"], result["details"]) == ("out-error", ["areas is a link"])


@pytest.mark.parametrize("name", ["big.md", ".architecture-docs-1"])
def test_list_out_refuses_a_file_over_50_mb(tmp_path, name: str) -> None:
    folder = tmp_path / "out"
    put(folder, name, MARKER.encode("utf-8") + b"\n" + b"x" * (50 * MB))
    result = listing(folder)
    assert (result["token"], result["details"]) == ("out-error", [f"{name} is over 50 MB"])
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_out.py -k list_out`. Expected: FAIL (`listOut` is not a function).
- [ ] **Step 3: GREEN.** Append to `out.mjs` (add `import { cmp } from '../architecture-delta/report.mjs';` to the imports):

```js
export const MARKER = '<!-- Generated by architecture-docs from the architecture model. Do not edit. -->';
export const TEMP_PREFIX = '.architecture-docs-';
export const FOLDERS = ['areas', 'capabilities', 'changes', 'pack', 'pack/areas', 'pack/capabilities'];
export const FILE_LIMIT = 50 * 1024 * 1024;
const OS_FILES = new Set(['.DS_Store', 'Thumbs.db', 'desktop.ini']);
const HEAD_BYTES = 4096;
const BOM = 0xfeff;

// The first line of a file, read from at most its first 4 KB, without a byte-order mark or a trailing CR.
function firstLine(file) {
  const fd = fs.openSync(file, 'r');
  try {
    const buffer = Buffer.alloc(HEAD_BYTES);
    const read = fs.readSync(fd, buffer, 0, HEAD_BYTES, 0);
    let text = buffer.subarray(0, read).toString('utf8');
    if (text.charCodeAt(0) === BOM) text = text.slice(1);
    return text.split('\n')[0].replace(/\r$/, '');
  } finally {
    fs.closeSync(fd);
  }
}

// Spec, write rule 2: a Markdown or HTML file is marked by its first line; a JSON file by its first key.
export function isMarked(file, name) {
  if (name.endsWith('.md') || name.endsWith('.html')) return firstLine(file) === MARKER;
  if (name.endsWith('.json')) {
    let data;
    try {
      data = JSON.parse(fs.readFileSync(file, 'utf8'));
    } catch {
      return false;
    }
    return data !== null && typeof data === 'object' && !Array.isArray(data)
      && Object.keys(data)[0] === 'generated' && data.generated === 'architecture-docs';
  }
  return false;
}

// Spec, write rule 2: the marked files and the temporary files in the folder (paths with `/`), or `out-error`.
export function listOut(outDir) {
  const result = { files: [], temps: [] };
  if (!fs.existsSync(outDir)) return result;
  const pending = [''];
  while (pending.length > 0) {
    const rel = pending.pop();
    for (const entry of fs.readdirSync(path.join(outDir, rel), { withFileTypes: true })) {
      const child = rel === '' ? entry.name : `${rel}/${entry.name}`;
      const full = path.join(outDir, child);
      if (entry.isSymbolicLink()) throw outError(`${child} is a link`);
      if (entry.isDirectory()) {
        if (!FOLDERS.includes(child)) throw outError(`${child} is not a folder the tool makes`);
        pending.push(child);
        continue;
      }
      if (fs.statSync(full).size > FILE_LIMIT) throw outError(`${child} is over 50 MB`);
      if (entry.name.startsWith(TEMP_PREFIX)) {
        result.temps.push(child);
        continue;
      }
      if (OS_FILES.has(entry.name)) continue;
      if (!isMarked(full, entry.name)) throw outError(`${child} was not written by architecture-docs`);
      result.files.push(child);
    }
  }
  result.files.sort(cmp);
  result.temps.sort(cmp);
  return result;
}
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_out.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/out.mjs tests/scripts/test_architecture_docs_out.py && git commit -m "feat(#32): the docs output folder holds only files the tool marked"`

### Task 5: the writer (write rule 3) and the source rule

**Tier:** strong — the only code that changes files.

**Files:**
- Create: `skills/shared/scripts/architecture-docs/writer.mjs`
- Test: `tests/scripts/test_architecture_docs_writer.py` (create), `tests/scripts/test_architecture_docs_safety.py` (create)

**Callers that move with this task:** none.

**Reviewer looks at:**
- stale files deleted, only listed ones — mutation: delete every listed file — killed by: `test_write_output_writes_replaces_and_deletes` (the produced file survives); mutation: skip deleting — killed by the same test
- temporary files removed — mutation: skip the temp loop — killed by: `test_write_output_writes_replaces_and_deletes`
- empty named folders removed, deepest first — mutation: sort shallowest first — killed by: `test_write_output_removes_empty_folders` (`pack` stays when `pack/areas` empties after it)
- failures named — mutation: let the raw error through — killed by: `test_write_output_names_a_failed_replace`
- only the writer changes files — mutation: add `fs.writeFileSync` to `out.mjs` on a scratch copy — killed by: `test_only_the_writer_changes_files`

- Satisfies Spec AC: AC-17 (with Task 6)
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_docs_writer.py`:

```python
"""The docs tool's writer: write rule 3 (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

from pathlib import Path

from arch_delta_support import DOCS_LIB, call, require_node

require_node()


def write(folder: Path, files: dict, listed: dict) -> dict:
    return call("writer.mjs", "writeOutput", str(folder), files, listed, lib=DOCS_LIB)


def test_write_output_writes_replaces_and_deletes(tmp_path) -> None:
    folder = tmp_path / "out"
    (folder / "areas").mkdir(parents=True)
    (folder / "areas" / "old.md").write_text("old", encoding="utf-8")
    (folder / "README.md").write_text("before", encoding="utf-8")
    (folder / ".architecture-docs-9").write_text("partial", encoding="utf-8")
    result = write(folder, {"README.md": "after\n", "pack/model.json": "{}\n"},
                   {"files": ["README.md", "areas/old.md"], "temps": [".architecture-docs-9"]})
    assert result["value"] == {"wrote": 2, "removed": 1}
    assert (folder / "README.md").read_bytes() == b"after\n"
    assert (folder / "pack" / "model.json").read_bytes() == b"{}\n"
    assert sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")) == ["README.md", "pack", "pack/model.json"]


def test_write_output_creates_the_folder_and_its_parents(tmp_path) -> None:
    folder = tmp_path / "a" / "b" / "out"
    assert write(folder, {"README.md": "x\n"}, {"files": [], "temps": []})["value"] == {"wrote": 1, "removed": 0}
    assert (folder / "README.md").is_file()


def test_write_output_removes_empty_folders(tmp_path) -> None:
    folder = tmp_path / "out"
    (folder / "pack" / "areas").mkdir(parents=True)
    (folder / "pack" / "areas" / "x.md").write_text("x", encoding="utf-8")
    write(folder, {"README.md": "x\n"}, {"files": ["pack/areas/x.md"], "temps": []})
    assert sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")) == ["README.md"]


def test_write_output_names_a_failed_replace(tmp_path) -> None:
    folder = tmp_path / "out"
    (folder / "README.md").mkdir(parents=True)
    (folder / "README.md" / "inner").write_text("x", encoding="utf-8")
    result = write(folder, {"README.md": "x\n"}, {"files": [], "temps": []})
    assert result["token"] == "out-error"
    assert result["details"][0].startswith("could not replace README.md: ")
```

Create `tests/scripts/test_architecture_docs_safety.py`:

```python
"""Least privilege of the architecture docs tool (spec 2026-11-17-architecture-docs-design.md, Threat Model)."""

from __future__ import annotations

import re

from arch_delta_support import DOCS_LIB, DOCS_SCRIPT

CHANGES_FILES = re.compile(
    r"(?<!stdout\.)(?<!stderr\.)\bwrite(Sync)?\s*\("
    r"|\b(writeFile|appendFile|mkdir|rmdir|rm|unlink|rename|copyFile|cp|createWriteStream|symlink|link|truncate"
    r"|chmod|chown|utimes)(Sync)?\s*\("
)


def sources() -> list:
    # The script exists from Task 6 on; until then only the modules are checked.
    return [p for p in [DOCS_SCRIPT, *sorted(DOCS_LIB.glob("*.mjs"))] if p.exists()]


def test_only_the_writer_changes_files() -> None:
    for source in sources():
        if source.name == "writer.mjs":
            continue
        assert not CHANGES_FILES.search(source.read_text(encoding="utf-8")), source


def test_docs_tool_never_spawns_or_uses_the_network() -> None:
    forbidden = re.compile(r"child_process|worker_threads|fs/promises|node:(http|https|net|tls|dgram)\b")
    for source in sources():
        assert not forbidden.search(source.read_text(encoding="utf-8")), source


def test_files_are_opened_only_for_reading() -> None:
    for source in sources():
        for match in re.finditer(r"openSync\(([^)]*)\)", source.read_text(encoding="utf-8")):
            assert match.group(1).rstrip().endswith("'r'"), source
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_writer.py tests/scripts/test_architecture_docs_safety.py`. Expected: the writer tests FAIL (module not found); the safety tests pass (no writer yet, nothing forbidden).
- [ ] **Step 3: GREEN.** Create `writer.mjs`:

```js
// The only module of the docs tool that changes files: it writes, replaces and deletes inside the output folder (write rule 3).
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from '../architecture-delta/errors.mjs';
import { FOLDERS, TEMP_PREFIX } from './out.mjs';

function attempt(what, rel, action) {
  try {
    return action();
  } catch (err) {
    throw new ToolError('out-error', `could not ${what} ${rel}: ${err?.code ?? err?.message ?? String(err)}`);
  }
}

// Spec, write rule 3: every file of `files` ({ path with '/': text }) is written to a temporary name and renamed into
// place (left-over temporary files are deleted first); then the listed marked files no longer produced are deleted; then named
// folders left empty are removed, deepest first. `listed` is `listOut`'s result. Returns the counts.
export function writeOutput(outDir, files, listed) {
  attempt('create', '.', () => fs.mkdirSync(outDir, { recursive: true }));
  // Left-over temporary files go first, so a new temporary name can never meet an old one.
  for (const rel of listed.temps) attempt('delete', rel, () => fs.unlinkSync(path.join(outDir, rel)));
  const names = Object.keys(files).sort();
  names.forEach((rel, index) => {
    const final = path.join(outDir, rel);
    const temp = path.join(path.dirname(final), `${TEMP_PREFIX}${process.pid}-${index}`);
    attempt('create', path.posix.dirname(rel), () => fs.mkdirSync(path.dirname(final), { recursive: true }));
    attempt('write', rel, () => fs.writeFileSync(temp, files[rel], 'utf8'));
    attempt('replace', rel, () => fs.renameSync(temp, final));
  });
  const produced = new Set(names);
  const stale = listed.files.filter((rel) => !produced.has(rel));
  for (const rel of stale) attempt('delete', rel, () => fs.unlinkSync(path.join(outDir, rel)));
  for (const folder of [...FOLDERS].sort((x, y) => y.split('/').length - x.split('/').length)) {
    const full = path.join(outDir, folder);
    if (fs.existsSync(full) && fs.readdirSync(full).length === 0) attempt('remove', folder, () => fs.rmdirSync(full));
  }
  return { wrote: names.length, removed: stale.length };
}
```

(In `test_write_output_names_a_failed_replace`, `rename` onto a non-empty folder fails on every platform; the temporary file is then left behind, and a later build removes it, as write rule 3 says.)

- [ ] **Step 4:** `uv run pytest -q tests/scripts/test_architecture_docs_writer.py tests/scripts/test_architecture_docs_safety.py tests/scripts/test_architecture_docs_out.py`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs/writer.mjs tests/scripts/test_architecture_docs_writer.py tests/scripts/test_architecture_docs_safety.py && git commit -m "feat(#32): the docs writer; only it changes files"`

### Task 6: `build` and `check`, with `pack/model.json`

**Tier:** standard — integration of the modules above; complete code.

**Files:**
- Create: `skills/shared/scripts/architecture-docs.mjs`, `skills/shared/scripts/architecture-docs/build.mjs`
- Modify: `skills/defining-architecture/ARCH_STANDARDS.md` (one line: the tool's commands)
- Test: `tests/scripts/test_architecture_docs_tool.py` (create)

**Callers that move with this task:** none.

**Reviewer looks at:**
- `--out` checked before the model loads — mutation: call `resolveOut`/`listOut` after `loadRepoModel` — killed by: `test_build_and_check_refuse_an_unmarked_file` on a model that also has a link in `generated` (expects `out-error`, not `model-symlink`)
- `check` compares after CRLF → LF — mutation: compare raw — killed by: `test_check_accepts_crlf_line_endings`
- `extra` only for marked files no longer produced — mutation: report every listed file as extra — killed by: `test_check_reports_missing_changed_and_extra` (the produced file is `changed`, not `extra`)
- limits — mutation: `>=` instead of `>` on the file limit — killed by: `test_output_limits` (exactly 2,000 files pass)
- nothing written over the limits — mutation: write before `checkLimits` — killed by: `test_build_over_the_limits_writes_nothing`

- Satisfies Spec AC: AC-8, AC-9 (stale marked file), AC-10, AC-11, AC-13 (JSON marker), AC-14, AC-15, AC-16, AC-17
- **Test retention:** **Permanent**

- [ ] **Step 1: RED.** Create `tests/scripts/test_architecture_docs_tool.py`:

```python
"""The architecture docs tool: build and check (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

import json
from pathlib import Path

from arch_delta_support import (
    DOCS_LIB, DOCS_SCRIPT, error_lines, link_dir, lib_url, make_repo, require_node, run_module, run_tool, unique,
)

require_node()

MARKER = "<!-- Generated by architecture-docs from the architecture model. Do not edit. -->"


def docs(*args: object):
    return run_tool(*args, script=DOCS_SCRIPT)


def out_of(repo: Path) -> Path:
    return repo / "docs" / "architecture" / "generated"


def snapshot(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_build_is_deterministic_and_check_agrees(tmp_path) -> None:  # AC-8, AC-13 (JSON marker)
    repo = make_repo(tmp_path)
    first = docs("build", "--repo", repo)
    assert (first.returncode, first.stdout) == (0, "wrote 1 files, removed 0\n"), first.stderr
    before = snapshot(out_of(repo))
    assert docs("build", "--repo", repo).returncode == 0
    assert snapshot(out_of(repo)) == before
    check = docs("check", "--repo", repo)
    assert (check.returncode, check.stdout) == (0, "0 missing, 0 changed, 0 extra\n")
    data = json.loads(before["pack/model.json"])
    assert list(data) == ["generated", "export"]
    assert data["generated"] == "architecture-docs"
    assert data["export"] == json.loads(run_tool("export", "--repo", repo).stdout)


def test_check_reports_missing_changed_and_extra(tmp_path) -> None:  # AC-9 (stale marked file)
    repo = make_repo(tmp_path)
    missing = docs("check", "--repo", repo)
    assert (missing.returncode, missing.stdout) == (1, "missing pack/model.json\n1 missing, 0 changed, 0 extra\n")
    docs("build", "--repo", repo)
    (out_of(repo) / "areas").mkdir()
    (out_of(repo) / "areas" / "old.md").write_text(MARKER + "\n# Old\n", encoding="utf-8")
    model = repo / "docs" / "architecture" / "model.c4"
    model.write_text(model.read_text(encoding="utf-8").replace("'Card'", "'Card reader'"), encoding="utf-8")
    stale = docs("check", "--repo", repo)
    assert (stale.returncode, stale.stdout) == (1, "extra areas/old.md\nchanged pack/model.json\n0 missing, 1 changed, 1 extra\n")
    rebuilt = docs("build", "--repo", repo)
    assert rebuilt.stdout == "wrote 1 files, removed 1\n"
    assert sorted(snapshot(out_of(repo))) == ["pack/model.json"]
    assert not (out_of(repo) / "areas").exists()


def test_check_accepts_crlf_line_endings(tmp_path) -> None:  # AC-10
    repo = make_repo(tmp_path)
    docs("build", "--repo", repo)
    target = out_of(repo) / "pack" / "model.json"
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    assert docs("check", "--repo", repo).returncode == 0


def test_build_and_check_refuse_an_unmarked_file(tmp_path) -> None:  # AC-11
    repo = make_repo(tmp_path)
    docs("build", "--repo", repo)
    (out_of(repo) / "notes.md").write_text("mine\n", encoding="utf-8")
    target = tmp_path / unique("t")
    target.mkdir()
    link_dir(target, out_of(repo) / "pack" / "areas")
    before = snapshot(out_of(repo))
    for command in ("build", "check"):
        proc = docs(command, "--repo", repo)
        assert proc.returncode == 2
        assert error_lines(proc)[0].startswith("error: out-error: ")
    assert snapshot(out_of(repo)) == before


def test_build_leaves_operating_system_files(tmp_path) -> None:  # AC-11
    repo = make_repo(tmp_path)
    out_of(repo).mkdir()
    (out_of(repo) / ".DS_Store").write_text("os", encoding="utf-8")
    assert docs("build", "--repo", repo).returncode == 0
    assert (out_of(repo) / ".DS_Store").read_text(encoding="utf-8") == "os"


def test_build_refuses_bad_out(tmp_path) -> None:  # AC-14
    repo = make_repo(tmp_path)
    target = tmp_path / unique("t")
    target.mkdir()
    link_dir(target, repo / "via")
    for value in ("../away", "docs/architecture", "docs/architecture/decisions", "docs/architecture/docs-out", "via/out"):
        proc = docs("build", "--repo", repo, "--out", value)
        assert proc.returncode == 2, value
        assert error_lines(proc)[0].startswith("error: out-error: "), value
    assert not out_of(repo).exists()
    assert list(target.iterdir()) == []


def test_build_writes_nothing_on_invalid_records(tmp_path) -> None:  # AC-15
    repo = make_repo(tmp_path)
    decisions = repo / "docs" / "architecture" / "decisions"
    decisions.mkdir()
    (decisions / "a.json").write_text('{"title": "A", "decisions": [{"id": "D-1"}], "holes": []}', encoding="utf-8")
    built = docs("build", "--repo", repo)
    assert built.returncode == 2
    assert error_lines(built)[0].startswith("error: record-error: ")
    assert error_lines(built) == error_lines(run_tool("export", "--repo", repo))
    assert not out_of(repo).exists()


def test_build_reads_the_gap_file_as_check_does(tmp_path) -> None:
    repo = make_repo(tmp_path)
    (repo / "docs" / "architecture" / "known-gap.json").write_text('{"entries": [{"from": "ghost"}]}', encoding="utf-8")
    proc = docs("build", "--repo", repo)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: bad-input: --gap entry 0")


def test_build_leaves_no_temporary_file(tmp_path) -> None:  # AC-17
    repo = make_repo(tmp_path)
    docs("build", "--repo", repo)
    (out_of(repo) / ".architecture-docs-1").write_text("partial", encoding="utf-8")
    check = docs("check", "--repo", repo)
    assert (check.returncode, check.stdout) == (0, "0 missing, 0 changed, 0 extra\n")
    docs("build", "--repo", repo)
    assert sorted(snapshot(out_of(repo))) == ["pack/model.json"]


def test_build_usage_and_timeout(tmp_path) -> None:
    repo = make_repo(tmp_path)
    assert error_lines(docs("build")) == ["error: usage: --repo is required"]
    timed = docs("build", "--repo", repo, "--timeout", "0")
    assert (timed.returncode, timed.stdout) == (2, "")
    assert error_lines(timed)[0].startswith("error: timeout: ")
    assert not out_of(repo).exists()


BIG_OUTPUT = (
    "const byteLength = Buffer.byteLength;\n"
    "Buffer.byteLength = (...args) => (new Error().stack.includes('build.mjs') ? 60 * 1024 * 1024 : byteLength(...args));\n"
)


def test_build_over_the_limits_writes_nothing(tmp_path) -> None:  # AC-16
    preload = tmp_path / "big-output.mjs"
    preload.write_text(BIG_OUTPUT, encoding="utf-8")
    repo = make_repo(tmp_path)
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT, preload=preload)
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: out-error: the output would be more than 50 MB"]
    assert not out_of(repo).exists()


def test_output_limits() -> None:  # AC-16
    code = (
        f"import {{ checkLimits }} from {json.dumps(lib_url('build.mjs', DOCS_LIB))};\n"
        "const results = [];\n"
        "const files = (n, size) => Object.fromEntries(Array.from({ length: n }, (_, i) => [`f${i}.md`, 'x'.repeat(size)]));\n"
        "for (const [n, size] of [[2000, 1], [2001, 1], [1, 50 * 1024 * 1024], [1, 50 * 1024 * 1024 + 1]]) {\n"
        "  try { checkLimits(files(n, size)); results.push('ok'); } catch (err) { results.push(`${err.token}: ${err.details[0]}`); }\n"
        "}\n"
        "process.stdout.write(JSON.stringify(results));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == [
        "ok", "out-error: the output would be more than 2000 files", "ok", "out-error: the output would be more than 50 MB",
    ]
```

- [ ] **Step 2:** `uv run pytest -q tests/scripts/test_architecture_docs_tool.py`. Expected: FAIL (script not found).
- [ ] **Step 3: GREEN.** Create `architecture-docs/build.mjs`:

```js
// The documents of one build, as { path with '/': text }, and the output limits (write rule 4).
import { ToolError } from '../architecture-delta/errors.mjs';
import { exportJson } from '../architecture-delta/report.mjs';

export const OUT_FILE_LIMIT = 2000;
export const OUT_BYTES_LIMIT = 50 * 1024 * 1024;

// Spec, AI pack: `pack/model.json` holds the format 4 export under `export`, marked by its first key.
// Later plans add the other documents here; `gap` (cleaned known-gap entries) is for them.
export function buildFiles(model, records, gap, tick = () => {}) {
  const files = {};
  files['pack/model.json'] = `${JSON.stringify({ generated: 'architecture-docs', export: exportJson(model, records) }, null, 2)}\n`;
  tick();
  return files;
}

// Spec, write rule 4: a build over 2,000 files or 50 MB stops before writing.
export function checkLimits(files) {
  const names = Object.keys(files);
  if (names.length > OUT_FILE_LIMIT) throw new ToolError('out-error', `the output would be more than ${OUT_FILE_LIMIT} files`);
  const bytes = names.reduce((sum, rel) => sum + Buffer.byteLength(files[rel], 'utf8'), 0);
  if (bytes > OUT_BYTES_LIMIT) throw new ToolError('out-error', 'the output would be more than 50 MB');
}
```

Create `architecture-docs.mjs`:

```js
#!/usr/bin/env node
// Architecture docs: builds documents from the architecture model into one output folder, or reports which are stale.
// Changes files only inside its output folder (architecture-docs/writer.mjs); never runs another program or uses the network.
import fs from 'node:fs';
import path from 'node:path';
import { clean, cleanText } from './architecture-delta/errors.mjs';
import { realRepo, resolveInside } from './architecture-delta/paths.mjs';
import { parseGap } from './architecture-delta/inputs.mjs';
import { cmp } from './architecture-delta/report.mjs';
import { startDeadline, loadRepoModel, readOptional, runCli } from './architecture-delta/load.mjs';
import { parseArgs } from './architecture-docs/args.mjs';
import { resolveOut, listOut } from './architecture-docs/out.mjs';
import { writeOutput } from './architecture-docs/writer.mjs';
import { buildFiles, checkLimits } from './architecture-docs/build.mjs';

// Spec, The tool: known-gap entries are cleaned like `export` output before any document uses them.
function readGap(loaded, value) {
  const ids = loaded.model.elements.map((element) => element.id);
  const entries = readOptional(loaded.repo, value, path.join(loaded.modelDir, 'known-gap.json'), '--gap',
    (data) => parseGap(data, ids)) ?? [];
  return entries.map((entry) => ({
    from: clean(entry.from),
    to: clean(entry.to),
    reason: cleanText(entry.reason),
    close_by: entry.close_by === null ? null : cleanText(entry.close_by),
  }));
}

function runBuild(outDir, files, listed) {
  const { wrote, removed } = writeOutput(outDir, files, listed);
  return { output: `wrote ${wrote} files, removed ${removed}\n`, exitCode: 0 };
}

// Spec, `check`: compare after CRLF to LF; a marked file no longer produced is `extra`.
function runCheck(outDir, files, listed) {
  const produced = Object.keys(files);
  const lines = [];
  for (const rel of produced) {
    const full = path.join(outDir, rel);
    if (!fs.existsSync(full)) lines.push(['missing', rel]);
    else if (fs.readFileSync(full, 'utf8').replace(/\r\n/g, '\n') !== files[rel]) lines.push(['changed', rel]);
  }
  const keep = new Set(produced);
  for (const rel of listed.files) if (!keep.has(rel)) lines.push(['extra', rel]);
  lines.sort((x, y) => cmp(x[1], y[1]));
  const count = (word) => lines.filter((line) => line[0] === word).length;
  const output = lines.map(([word, rel]) => `${word} ${clean(rel)}\n`).join('')
    + `${count('missing')} missing, ${count('changed')} changed, ${count('extra')} extra\n`;
  return { output, exitCode: lines.length > 0 ? 1 : 0 };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  // Spec: the output folder is checked (write rules 1 and 2) before the model loads.
  const repo = realRepo(args.repo);
  const outDir = resolveOut(repo, resolveInside(repo, args.model, '--model').path, args.out);
  const listed = listOut(outDir);
  deadline.check();
  const loaded = await loadRepoModel(args, deadline);
  const gap = readGap(loaded, args.gap);
  deadline.check();
  const files = buildFiles(loaded.model, loaded.records, gap, deadline.check);
  checkLimits(files);
  const result = args.command === 'build' ? runBuild(outDir, files, listed) : runCheck(outDir, files, listed);
  deadline.stop();
  return result;
}

runCli(main);
```

In `skills/defining-architecture/ARCH_STANDARDS.md`, after the line starting "- An area is an element view", add:

```markdown
- `node <skills-dir>/shared/scripts/architecture-docs.mjs build|check --repo . [--model <model>] [--gap <gap-file>] [--out <folder>]` builds the generated documents into `<model>/generated` (or `--out`), or reports which are missing, changed or extra. `build` exits 0 or 2; `check` exits 0 when current, 1 when stale, 2 on an error. It overwrites or deletes only files it marked, and `out-error` names any problem with the output folder.
```

- [ ] **Step 4:** `uv run pytest -q tests/scripts -k "architecture_delta or architecture_docs or defining_architecture"`. Expected: PASS.
- [ ] **Step 5:** No refactor.
- [ ] **Step 6:** `git add skills/shared/scripts/architecture-docs.mjs skills/shared/scripts/architecture-docs/build.mjs tests/scripts/test_architecture_docs_tool.py skills/defining-architecture/ARCH_STANDARDS.md && git commit -m "feat(#32): architecture-docs build and check, with pack/model.json"`
