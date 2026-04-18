# Resistance engine submodule extraction

**Date:** 2026-04-17  
**Status:** Drafted for review

---

## Problem

`resistance-engine/` is currently owned inside this repository even though the desired
end state is different:

1. `Itzalive/resistance-ai` should become the canonical repository for the
   resistance-engine content
2. this repository should consume that content only as a pinned git submodule at
   `resistance-engine/`
3. if `vendor/obra-superpowers` is still required by the importer/validator flow, it
   must move with the canonical repo instead of remaining here

The current repository state is in between those models. The worktree contains the
approved local resistance-engine content and its authoring-pair follow-on changes, but
`main` still contains partial plugin scaffolding directly under
`resistance-engine/.claude-plugin/`. Meanwhile, the importer/validator flow still treats
the vendor plugin surfaces and package metadata as deferred inventory rather than
canonical shipped assets.

Without an explicit extraction design, the merge to `main` risks preserving the wrong
source of truth, splitting the import pipeline across two repositories, or keeping
stale local ownership in the parent repo after the submodule cutover.

---

## Current-state evidence

The current repository reads show the exact ownership and dependency surface that this
migration must resolve.

```text
$ cat .gitmodules
[submodule "vendor/obra-superpowers"]
	path = vendor/obra-superpowers
	url = https://github.com/obra/superpowers

$ sed -n '20,65p' scripts/import_superpowers_catalog.py
DEFAULT_SOURCE_ROOT = REPO_ROOT / "vendor" / "obra-superpowers"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "resistance-engine"
SOURCE_REPO = "vendor/obra-superpowers"
...
_LOCAL_AUTHORING_SKILLS_ROOT = REPO_ROOT / "resistance-engine" / "skills"
...
    ".claude-plugin": "defer",
    ".cursor-plugin": "defer",
    "package.json": "defer",
    "LICENSE": "defer",
    "gemini-extension.json": "defer",

$ git show main:resistance-engine/.claude-plugin/plugin.json
{
  "name": "resistance-engine",
  "homepage": "https://github.com/Itzalive/resistance-ai",
  "repository": "https://github.com/Itzalive/resistance-ai",
  ...
}

$ git show main:resistance-engine/.claude-plugin/marketplace.json
{
  "name": "resistance-dev",
  "plugins": [
    {
      "name": "resistance-engine",
      "source": "./",
      ...
    }
  ]
}

$ git diff --name-status main..HEAD
D	resistance-engine/.claude-plugin/marketplace.json
D	resistance-engine/.claude-plugin/plugin.json
D	resistance-engine/LICENSE
M	resistance-engine/README.md
M	resistance-engine/skills/brainstorming/SKILL.md
M	resistance-engine/skills/writing-plans/SKILL.md
...
```

These reads establish four important facts:

- the parent repo still owns `vendor/obra-superpowers` as a submodule today
- the importer still assumes the parent repo owns both `vendor/obra-superpowers` and
  `resistance-engine/`
- `main` already carries an intended standalone-plugin direction for resistance-engine
- the approved feature branch currently diverges from `main` by deleting that plugin
  scaffold, so the extraction must intentionally decide where those files belong

---

## Goals

- Make `Itzalive/resistance-ai` the single canonical repository for resistance-engine
  source content
- Move the current resistance-engine tree, its authoring/import/validation tooling, its
  contract tests, and `vendor/obra-superpowers` into the canonical repo if the importer
  still depends on that vendor source
- Treat Copilot CLI plugin metadata and VS Code metadata-only packaging as canonical
  assets of `resistance-ai`
- Replace the local `resistance-engine/` directory in this repository with a git
  submodule that points at `https://github.com/Itzalive/resistance-ai`
- Remove parent-repo ownership of resistance-engine authoring and import validation
- Preserve the approved authoring-pair content during the extraction and cutover

## Non-goals

- No full installable VS Code extension package in this shard
- No simultaneous redesign of resistance-engine’s content model beyond what is needed
  for canonical extraction
- No dual-write workflow where both repositories remain valid authoring locations
- No forced removal of `vendor/obra-superpowers` from the canonical repo if that would
  require a larger importer redesign
- No long-lived transitional state where this repository still regenerates or validates
  resistance-engine content locally after the submodule cutover

---

## Approach

Adopt a **full canonical extraction** model.

`Itzalive/resistance-ai` becomes the authored standalone repository and carries the
entire resistance-engine control plane:

- shipped skills and agents
- catalog and provenance artifacts
- consolidation overrides
- importer and validator scripts
- contract tests
- plugin and packaging metadata
- `vendor/obra-superpowers` if still needed by the importer

This repository becomes a consumer only. After cutover, resistance-engine changes are
made in `resistance-ai` and propagated here only by updating the submodule pointer.

The migration should not combine ownership transfer with a deeper importer redesign.
If the canonical repo still needs `vendor/obra-superpowers`, move that dependency with
the extraction. The parent repo should not keep a sibling vendor dependency for a tree
it no longer authors.

---

## Files and surfaces expected to change

### In `Itzalive/resistance-ai`

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `.gitmodules` | Modify | Drop `vendor/obra-superpowers`, add `resistance-engine` submodule |
| `resistance-engine/` | Replace with submodule | Consume canonical repo instead of local source tree |
| `scripts/import_superpowers_catalog.py` | Remove or relocate | Parent repo must stop owning resistance-engine regeneration |
| `scripts/validate_resistance_engine_provenance.py` | Remove or relocate | Parent repo must stop owning canonical provenance validation |
| `tests/scripts/test_import_superpowers_catalog.py` | Remove or relocate | Contract tests move with the canonical repo |
| `tests/scripts/test_validate_resistance_engine_provenance.py` | Remove or relocate | Provenance contract tests move with the canonical repo |
| Docs referencing local resistance-engine authoring | Modify | Point contributors to `resistance-ai` and submodule update workflow |

### In `Itzalive/resistance-ai`

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| repo root content seeded from current `resistance-engine/` tree | Create or import | Canonical shipped skills/agents/catalog/provenance surfaces |
| importer / validator scripts | Add | Own the canonical regeneration and validation workflow |
| contract tests | Add | Prove importer, provenance, and authoring defaults in the canonical repo |
| `vendor/obra-superpowers/` | Add if still required | Keep importer dependency local to the canonical repo |
| `.claude-plugin/` and Copilot-compatible plugin metadata | Add / restore | Canonical plugin surface |
| VS Code metadata-only manifest | Add | Metadata support without shipping a full extension package |
| `README`, install docs, release notes, `LICENSE` | Add / align | Explain canonical ownership and plugin consumption |

---

## Detailed design

### 1. Canonical repo layout

`Itzalive/resistance-ai` should use the current `resistance-engine/` contents as its
repo-root payload, not as a nested subdirectory. The canonical repo root should contain
the shipped runtime surfaces directly:

- `skills/`
- `agents/`
- `catalog/`
- `provenance/`
- `consolidation/`
- importer and validator scripts
- contract tests
- plugin manifests
- `README` and `LICENSE`

If `vendor/obra-superpowers` remains necessary, it should live inside the canonical
repo and be referenced there by the moved importer instead of from this parent repo.

### 2. Plugin and packaging ownership

The existing `main` branch `.claude-plugin` scaffold establishes that resistance-engine
already intends to be consumed as a standalone plugin-style asset. That ownership must
move into `resistance-ai`.

The canonical repo must ship:

- Copilot CLI plugin-facing metadata
- Claude-style plugin metadata already implied by `main`
- VS Code metadata-only packaging artifacts

These plugin/package files should no longer be treated as deferred inventory. They are
part of the canonical release surface and should be versioned, documented, and
verified in the standalone repo.

### 3. Parent-repo cutover

After `resistance-ai` is independently green, this repository should:

1. remove the local `resistance-engine/` source tree
2. remove the local `vendor/obra-superpowers` submodule if that dependency moved
3. add a new `resistance-engine` submodule pointing at
   `https://github.com/Itzalive/resistance-ai`
4. update contributor docs so local edits to resistance-engine are no longer made here
5. remove parent-repo scripts/tests that exist only to author or validate the canonical
   resistance-engine content

The parent repo should retain only consumer-facing proof:

- the submodule initializes correctly
- checked-out resistance-engine content is readable by any remaining consumers here
- setup docs instruct users to initialize the submodule

### 4. Merge strategy

The cutover should happen in two verified stages:

#### Stage A — standalone repo bootstrap

- seed `resistance-ai` from the approved current resistance-engine tree
- include the current importer/validator scripts, tests, and vendor dependency if
  required
- restore or add plugin/package metadata in the canonical repo
- verify the standalone repo passes its own regeneration and contract tests

#### Stage B — parent repo consumes canonical repo

- replace the local directory with the submodule
- update `.gitmodules`
- update or remove docs/tests/scripts that assume local ownership
- verify the parent repo no longer performs canonical authoring work

This sequencing prevents a half-migrated state where the parent repo points at a
canonical repo that is not yet self-sufficient.

### 5. Rollback and failure handling

If `resistance-ai` cannot be made independently green, do not merge the parent-repo
submodule cutover. The rollback point is before Stage B.

Once the cutover lands, ongoing updates should be ordinary submodule bumps instead of
structural moves. Any later redesign of the importer to remove `vendor/obra-superpowers`
entirely belongs in a follow-on change inside `resistance-ai`, not in the extraction
itself.

---

## Assumptions and blockers

### Assumptions

- `Itzalive/resistance-ai` is available as the intended canonical remote and can accept
  the extracted content
- the current approved resistance-engine tree on this branch is the correct seed for
  the canonical repo
- metadata-only VS Code support is sufficient for this shard

### Blocking constraints

- Do not merge the parent-repo submodule change before the standalone repo has passing
  verification on its own
- Do not leave `vendor/obra-superpowers` in this repo if the canonical repo still
  depends on it for importer correctness
- Do not preserve dual authoring paths after cutover

---

## BDD acceptance criteria

### Canonical repo ownership

1. **Given** `resistance-ai` is the target canonical repository  
   **When** the extraction is complete  
   **Then** the resistance-engine content, importer/validator tooling, contract tests,
   and any still-required `vendor/obra-superpowers` dependency live in `resistance-ai`
   rather than in this parent repo.

2. **Given** plugin metadata is part of the standalone release surface  
   **When** `resistance-ai` is bootstrapped  
   **Then** it ships Copilot CLI plugin metadata and VS Code metadata-only packaging as
   canonical tracked assets.

### Parent-repo cutover

3. **Given** this repository no longer authors resistance-engine directly  
   **When** the cutover lands on `main`  
   **Then** `resistance-engine/` is a git submodule pointing at
   `https://github.com/Itzalive/resistance-ai` and not a writable local source tree.

4. **Given** the importer dependency moved with the canonical repo  
   **When** the parent-repo cutover is complete  
   **Then** `.gitmodules` no longer owns `vendor/obra-superpowers` in this repository.

5. **Given** this repository is only a consumer after cutover  
   **When** engineers need to modify resistance-engine behavior  
   **Then** the docs direct them to make the change in `resistance-ai` and update the
   submodule pointer here instead of editing local files.

### Verification and safety rails

6. **Given** the standalone repo must be self-sufficient before the parent-repo cutover  
   **When** the migration is executed  
   **Then** Stage A verification passes in `resistance-ai` before Stage B replaces the
   local directory with the submodule.

7. **Given** the migration may fail partway through  
   **When** the standalone repo cannot pass its own verification  
   **Then** the parent-repo submodule cutover does not merge and the repository remains
   on the pre-cutover ownership model.
