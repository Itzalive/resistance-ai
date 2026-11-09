# Architecture delta tool

Work item: #20 (part of #19). Status: draft for review.

## What it is

`skills/shared/scripts/architecture-delta.mjs` compares a repository's target architecture, written as
a LikeC4 C4 model, with the dependencies its code actually has, and reports where they differ. It
runs when a skill step or a CI job calls it; it never runs on its own, never runs another program and
never writes a file.

It is language-neutral. It never reads source code. The repository supplies a list of module-to-module
dependencies, produced by a command its overlay names; the tool treats module names as plain strings.

This work item owns the tool, the shipped C4 specification and their tests. It does not own the
overlay text (each repository's), any language's dependency command, or the skills that call the tool
(`defining-architecture`, `specifying-features`, plan review and finishing wire it in later).

## Commands

```
node skills/shared/scripts/architecture-delta.mjs check  --repo <dir> --deps <file>
        [--model architecture] [--gap architecture/known-gap.json]
        [--scope <element,…>] [--shards <file>] [--separator .]
        [--format text|json] [--timeout 60]

node skills/shared/scripts/architecture-delta.mjs export --repo <dir> [--model architecture]
        [--timeout 60]
```

Relative paths resolve against `--repo`. The shipped C4 specification is found relative to the script
(`../architecture/c4.c4`). `--timeout` takes 0 to 600 seconds (default 60). An unknown `--scope` id is
an input error (exit 2).

## Inputs

All inputs are read-only. `--model`, `--deps`, `--gap` and `--shards` are resolved to real paths
(following symlinks) and must lie inside `--repo`'s real path; otherwise exit 2.

- **`likec4`:** loaded from the plugin's own install (resolved relative to the script), else from
  `<repo>`'s installed copy (resolved from `<repo>/package.json`). Neither: exit 2 with an install hint.
- **Model:** the directory `--model` (default `<repo>/architecture`), loaded with
  `LikeC4.fromWorkspace`. Any entry from `getErrors()`, or an exception from `likec4`: exit 2, listing
  each error's message, file and line where known.
- **C4 specification copy:** `<model>/c4.c4` must be byte-identical to the shipped
  `skills/shared/architecture/c4.c4`; missing or different: exit 2. Repositories add their own kinds
  or tags in other files.
- **Dependency file** (`--deps`, required for `check`): `{"edges": [["<from>", "<to>"], …]}`. Only the
  `edges` key; each edge exactly two non-empty strings. A repeated edge counts once.
- **Known-gap file** (`--gap`, default `<model>/known-gap.json`): optional; absent means an empty gap.
  Format below.
- **Shards file** (`--shards`): optional, `{"shards": {"<name>": ["<element id>", …]}}`; an id that is
  not a model element: exit 2.

## Matching rules

**Module to element.** An element's `code` metadata holds one or more module prefixes, comma-separated
and trimmed. A module belongs to an element when it equals one of the element's prefixes or starts
with a prefix followed by the separator (`--separator`, default `.`): `shop.orders` matches
`shop.orders.api` but not `shop.ordersx`. When several elements match, the longest matching prefix
wins. Two elements listing the same prefix is a model error (exit 2).

**Edges not checked.**
- Both ends map to the same element, or to an element and one of its ancestors: internal, ignored.
- The target maps to no element: a dependency outside the model (a standard library, a third-party
  package), ignored. To bring an external package under the rules, give it an element with `code`.
- The source maps to no element: the source module is listed under unmapped code; the edge is not
  checked.

**Allowed.** An edge from element A to element B is allowed when the model has a relationship from A
or any ancestor of A to B or any ancestor of B. Any relationship grants the permission, whatever its
kind; relationship kinds only change how diagrams look.

**`#protected`.** When B or an ancestor of B is tagged `#protected`, call the nearest such element P.
If A lies outside P, the edge is then allowed only by a relationship from A or an ancestor of A to P
or to a descendant of P; a relationship to an ancestor of P does not count. Edges between elements
that are both inside P follow the ordinary rule.

**Reported.**
- **Breach:** a checked edge that is not allowed; one breach per element pair (source element, target
  element), carrying its module edges.
- **Not yet reached:** a model relationship whose two ends both have `code`, where no checked code
  edge runs from the source element or a descendant to the target element or a descendant.
- **Unmapped code:** each source module that maps to no element, once.
- **Shared hot spot** (with `--shards`): an element inside the scope of two or more shards, where a
  shard's scope is its listed elements and their descendants; names the shards.

**Scope.** With `--scope`, breaches and not-yet-reached items are listed only when either end is a
scoped element or its descendant. Known-gap matching and stale detection always use the whole repo,
so a scoped run never reports an entry as stale because it lies outside the scope.

## Known gap

```json
{
  "entries": [
    {
      "from": "shop.orders",
      "to": "shop.payments",
      "reason": "orders call payments directly; moves behind checkout",
      "close_by": "feature-2"
    }
  ]
}
```

- An entry matches a breach when `from` and `to` equal the breach's element ids, and covers every
  module edge behind that pair.
- `from`, `to` and `reason` are required non-empty strings; `close_by` is optional free text. An
  unknown key, a missing field, a duplicate entry or an id that is not a model element: exit 2.
- A breach matched by an entry is **known**; a breach with no entry is **new**; an entry that matches
  no breach anywhere in the repo is **stale** ("remove this entry").
- The tool never writes or edits the file.

## Output

**`check`.** `--format json` prints one object:

```json
{
  "breaches": [{ "from": "…", "to": "…", "edges": [["…", "…"]], "more_edges": 0, "gap": "known|new" }],
  "not_yet_reached": [{ "from": "…", "to": "…" }],
  "unmapped": ["…"],
  "hot_spots": [{ "element": "…", "shards": ["…", "…"] }],
  "gap": { "known": [{ "from": "…", "to": "…" }], "new": [{ "from": "…", "to": "…" }], "stale": [{ "from": "…", "to": "…" }] }
}
```

Every list is sorted by its first field, then the next. A breach carries at most 20 module edges
(sorted) and counts the rest in `more_edges`. `--format text` (the default) prints the same content as
short sections, new breaches first, then stale entries, known breaches, not yet reached, unmapped
code and hot spots.

**`export`.** Prints the model for repositories that generate their own checks:

```json
{
  "format": 1,
  "elements": [
    { "id": "shop.payments", "kind": "component", "tags": ["protected"], "code": ["shop.payments"], "rules": ["BR-4"] }
  ],
  "allowed": [{ "from": "shop.checkout", "to": "shop.payments" }]
}
```

`code` and `rules` are split on commas and trimmed (empty lists when absent). `allowed` lists the
model's relationships as declared, one entry per element pair with duplicates merged; a consumer
applies the ancestor and `#protected` rules itself. Elements are sorted by id and `allowed` by `from`
then `to`, so the same model always gives the same bytes. `format` is the schema version; a breaking
change raises it.

**Cleaning.** Every string printed (ids, module names, tags, metadata, `reason`, `close_by`, model
error messages) has control characters and ANSI escape sequences removed and is cut to 200 characters
with a trailing `…`.

**Limits.** At most 1,000,000 edges, 5,000 model elements and 50 MB per input file; over a limit, exit 2
naming it.

**Time limit.** The deadline is checked after loading `likec4`, after loading the model, after
reading each input file and after every 10,000 edges matched; past it, the run stops with exit 2
naming the timeout. With `--timeout 0` the first check fails.

**Exit codes.**

| Code | Meaning |
|---|---|
| 0 | No new breach and no stale gap entry |
| 1 | A new breach or a stale gap entry |
| 2 | Input error: no `likec4`, a model error, a spec copy mismatch, a bad or missing file, a path outside `--repo`, a cap exceeded, a timeout |

Not yet reached, unmapped code and hot spots are reported but never change the exit code.

## The C4 specification

`skills/shared/architecture/c4.c4`:

```
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

`system`, `container` and `component` are the C4 levels and `external` covers people or systems
outside the boundary. `#protected` changes the allowed rule above; `#generic` (a domain-free library),
`#layer` and `#eval` are labels the skills read and the tool does not act on. `uses` is the default
relationship name. Its header comment documents the metadata keys `code` and `rules`, since LikeC4
metadata has no schema.

## Scope

- `skills/shared/scripts/architecture-delta.mjs`: plain ESM using Node's standard library and `likec4`;
  no build step.
- `skills/shared/architecture/c4.c4`.
- `package.json` gains `"dependencies": { "likec4": "1.60.0" }` (exact pin); its Pi manifest fields stay
  unchanged. `package-lock.json` (lockfile version 3) is committed. `.gitignore` gains `node_modules/`.
- `tests/scripts/test_architecture_delta.py` with fixture models and dependency files under
  `tests/fixtures/architecture/`, calling the tool as a subprocess under `uv run pytest -q`.
- Required checks that are not acceptance criteria:
  - a session-level test that fails, never skips, when `node` or `node_modules/likec4` is missing,
    with the message "run `npm ci`";
  - a source test that the tool imports neither `child_process` nor `worker_threads` and calls no
    `fs` write function;
  - a test that `package-lock.json` is lockfile version 3, pins `likec4` at exactly 1.60.0, and
    that the installed `node_modules/likec4` is that version;
  - the no-network test runs the tool as `node --import <preload> architecture-delta.mjs …`, where
    the preload (a fixture) replaces `fetch`, `http.request` and `https.request` with functions that
    throw;
  - the fallback tests copy the script and `c4.c4` into a temporary `skills/shared/…` layout with no
    `node_modules`, then run it with `--repo` set to the engine root (which has `likec4` installed, for
    AC-2's fallback) or to a temporary folder without it (for AC-2's install hint);
  - `npm audit` output recorded when the pin is made; a high or critical finding stops the pin for the
    owner's decision.

**Out of scope:** any language's dependency command; the overlay file; calling the tool from skills;
relationship kinds that withhold permission; mutation tooling (#27).

## Threat Model (CIA)

This is a net-new tool, so each mechanism is a designed defence with a test, not existing code.

**Confidentiality.** The tool reads only the model directory, the dependency, gap and shards files
and the spec copy, and prints only element ids, module names, tags, `code` and `rules` values and the
gap's `reason` and `close_by`. It reads no environment variable beyond Node's own and makes no
network call. Whether `likec4`'s loader ever reaches the network is not proven, so a test replaces
`fetch`, `http.request` and `https.request` with functions that throw and requires `check` and
`export` to succeed (AC-21).

**Integrity.** Every input is repository content and treated as hostile:
- Strict shapes for the dependency, gap and shards files: unknown keys, wrong types and empty strings
  are exit 2 (AC-5).
- Every input path must resolve inside `--repo` (Inputs above) (AC-5).
- The spec copy must match the shipped one, so a repository cannot quietly redefine kinds or tags
  (AC-4).
- Printed strings are cleaned (above) because agents read the report; the skills that consume it must
  treat it as data, never instructions (their work items own that rule) (AC-20).
- The tool writes no file and runs no program (source test in Scope; AC-17 checks the gap file is
  untouched).

**Availability.** The limits and time limit above bound memory and run time; at most 20 module edges
per breach are printed (AC-19, AC-22).

**Least privilege.** Read-only file access inside `--repo`; no secrets, tokens or permissions.

**Supply chain.** `likec4` 1.60.0 is the only new dependency: MIT, published 2026-10-15, no install
script. It is pinned exactly with a committed lockfile carrying integrity hashes; the tests install
with `npm ci --ignore-scripts`, and Claude Code's plugin install runs no lifecycle scripts. Upgrades
are their own reviewed change with the tests re-run. It pulls in `playwright`, which the tool's code
path never imports. `@likec4/language-services` alone was rejected: it fails to load without
`bundle-require`.

## Acceptance criteria

*Loading and inputs*
- **AC-1** Given `likec4` is installed beside the tool and a fixture repository without it, when
  `check` runs on a clean fixture, then it exits 0.
- **AC-2** Given `likec4` is not installed beside the tool, when the repository has it installed, then
  `check` runs with the repository's copy; when neither has it, then it exits 2 and prints an install
  hint.
- **AC-3** Given the model has an unknown reference and an unknown element kind, when `check` runs,
  then it exits 2 and lists both errors with file and line.
- **AC-4** Given the repository's `c4.c4` differs from the shipped one or is missing, when `check` or
  `export` runs, then it exits 2.
- **AC-5** Given a dependency, gap or shards file with an unknown key, a wrong type or an empty string,
  or any of `--model`, `--deps`, `--gap` or `--shards` resolving outside `--repo` (including through a
  symlink), or an unknown `--scope` id, when `check` runs, then it exits 2 and names the problem.

*Matching*
- **AC-6** Given elements `shop` (prefix `shop`), `shop.orders` (prefix `shop.orders`) and `c` (prefix
  `cat`) with no relationships, when the dependency file holds `shop.orders.api -> cat` and
  `shop.ordersx -> cat`, then the breaches are `shop.orders -> c` and `shop -> c`.
- **AC-7** Given two elements list the same prefix, when `check` runs, then it exits 2.
- **AC-8** Given an edge within one element, an edge between an element and its ancestor, an edge to an
  unmapped module and an edge from an unmapped module, when `check` runs, then the first three produce
  no breach and the unmapped source module is listed under `unmapped`.
- **AC-9** Given containers A and B, a relationship A -> B and a component of A depending on a component
  of B, when `check` runs, then there is no breach.
- **AC-10** Given B is tagged `#protected` and the only relationship goes to B's parent, when an element
  depends on B, then that pair is a breach; given a relationship directly to B, then it is not; given two elements both inside B, when one
  depends on the other, then the ordinary rule applies.
- **AC-11** Given a relationship between two elements with `code` and no matching code edge, when
  `check` runs, then the pair is listed under `not_yet_reached` and the exit code is 0.
- **AC-12** Given a shards file in which two shards both cover element E, when `check` runs, then E is
  listed under `hot_spots` naming both shards.
- **AC-13** Given `--scope X` and breaches inside and outside X, when `check` runs, then only the
  breaches touching X or its descendants are listed, and a gap entry for a breach outside X is not
  reported stale.

*Known gap*
- **AC-14** Given the only breach's element pair is in the gap file, when `check` runs, then the breach
  is listed as known and the exit code is 0.
- **AC-15** Given a breach not in the gap file, when `check` runs, then it is listed as new and the
  exit code is 1.
- **AC-16** Given a gap entry that matches no breach, when `check` runs, then it is listed as stale and
  the exit code is 1.
- **AC-17** Given any `check` run, when it finishes, then the gap file's bytes are unchanged.

*Output*
- **AC-18** Given one model, when `export` runs twice, then the outputs are byte-identical and have
  `format`, `elements` and `allowed` in the shape above.
- **AC-19** Given `--format json` and a breach with 25 module edges, when `check` runs, then the report
  has exactly the five keys above, each list sorted, and the breach shows 20 edges with
  `more_edges: 5`.
- **AC-20** Given a model string with an ANSI escape sequence, a control character, or more than 200
  characters, when it is printed, then it appears with the sequence and character removed and cut to
  200 characters ending in `…`.

*Safety and limits*
- **AC-21** Given `fetch`, `http.request` and `https.request` throw, when `check` and `export` run on a
  fixture, then both succeed.
- **AC-22** Given a dependency file over the edge cap, a model over the element cap, an input over 50 MB,
  or `--timeout 0`, when the tool runs, then it exits 2 and names the cap or the timeout.
- **AC-23** Given a model folder holding only the shipped `c4.c4`, when `export` runs, then it exits 0
  with no elements.

## Future work (downstream cost)

| Item | Priority | Effort | Why |
|---|---|---|---|
| Call the tool from `defining-architecture`, `specifying-features`, plan review and finishing | P1 | in #22–#25 | The tool has no effect until the skills run it |
| Check whether Copilot CLI and Pi install plugin npm dependencies | P2 | S | Decides whether those harnesses rely on the repository fallback |
| A `likec4` upgrade routine (re-audit, re-run tests, re-check the loader) | P2 | S | `likec4` releases every few weeks |
| Measure the ~109 MB dependency against plugin install time and Claude Code's 60 s install limit | P3 | S | The plugin install could time out on a slow link |
| Relationship kinds that withhold permission | P3 | M | Only if a real model needs one |
| Mutation tool named by an overlay | — | — | #27 |

## Assumptions surface

| # | Assumption | Status |
|---|---|---|
| A1 | `package.json` has no dependencies; its test checks only `pi.skills` and the `pi-package` keyword; `bump_version.py` rewrites only the version | VERIFIED: `tests/test_pi_package.py`, `scripts/bump_version.py:65` |
| A2 | Engine Python scripts use only the standard library; pytest is dev-only | VERIFIED: `skills/shared/scripts/review-log.py` header, `pyproject.toml` |
| A3 | Tests run with `uv run pytest -q` over `tests/`; there is no CI workflow | VERIFIED: `pyproject.toml`; no `.github/workflows` |
| A4 | `likec4` 1.60.0: MIT, published 2026-10-15, no install script, 54 packages, ~109 MB | VERIFIED: `npm view`; scratch install with `--ignore-scripts` |
| A5 | `fromWorkspace`, `getErrors()` (message, line, range, file), `computedModel()`, `elements()` (`id`, `kind`, `tags`, `getMetadata()`), `relationships()` (`source.id`, `target.id`, `kind`, `title`) behave as used here; a small model loads in under 200 ms | VERIFIED: scratch run |
| A6 | `@likec4/language-services` alone fails to load (`bundle-require` missing) | VERIFIED: scratch run |
| A7 | A script outside a repository can load that repository's `likec4` via `createRequire(<repo>/package.json)`; without it, resolution fails with `MODULE_NOT_FOUND` | VERIFIED: scratch run from a separate folder |
| A8 | Claude Code installs a plugin's npm dependencies when it has `package.json` and a version 2 or 3 `package-lock.json` with exact registry pins, without lifecycle scripts, within 60 s | VERIFIED from Claude Code's plugin documentation; not yet exercised end to end |
| A9 | `node_modules/` is not in `.gitignore` | VERIFIED: `.gitignore` |
| A10 | Copilot CLI and Pi install plugin npm dependencies | UNVERIFIED, not blocking: the repository fallback covers both (future work) |

Shard evaluation: one tool with one responsibility; `export` reads the same model. No split, no
refactor mixed in.

## Evidence

Commands run against the repository and scratch installs while specifying:

- `cat package.json pyproject.toml`, `sed -n 1,40p skills/shared/scripts/review-log.py`,
  `cat tests/test_pi_package.py`, `grep -n package.json scripts/bump_version.py`, `cat .gitignore`,
  `ls .github` (absent).
- `npm view likec4 version time.modified license dependencies scripts exports`;
  `npm view @likec4/language-services version license dependencies`.
- `npm install --ignore-scripts likec4@1.60.0` and `@likec4/language-services@1.60.0` into separate
  scratch folders; a two-component model (`#protected` tag, `code` and `rules` metadata, one
  relationship) loaded through `LikeC4.fromWorkspace`, printing elements and relationships; a broken
  model (unknown reference, unknown kind) printing `getErrors()`; a loader in a third folder resolving
  `likec4` through `createRequire`, with and without it installed.
- File count and size of the scratch `node_modules` (7,256 files, 108.8 MB).
