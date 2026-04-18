## Resistance engine provenance manifest shard

**Date:** 2026-04-15
**Status:** Drafted for review
**Parent spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-catalog-retarget-design.md`
**Prerequisite shard:** `docs/superpowers/specs/2026-04-15-resistance-engine-import-catalog-design.md`

---

## Problem

Shard 1 successfully created a coherent local catalog under `resistance-engine/`:

- `resistance-engine/skills/` contains imported skill directories
- `resistance-engine/agents/` contains imported agent files
- `resistance-engine/catalog/catalog_index.json` records the current imported entries
- `resistance-engine/catalog/non_skill_inventory.json` records deferred non-skill
  surfaces

That shard intentionally stopped at an import snapshot. It does not yet provide a
mandatory provenance record for every skill and agent, and it cannot distinguish
between:

- an entry that is expected and present
- an entry that is expected but missing locally
- an entry whose local copy has drifted from source
- an entry whose source disappeared

The next shard must make provenance first-class and mandatory. Every skill and
agent should always have a provenance record, whether the local files are currently
present or not.

---

## Goals

- Add a central provenance manifest that covers every skill and agent entry
- Keep `catalog_index.json` as the current import snapshot for this shard
- Make the provenance manifest authoritative for lineage and state
- Provide file-level provenance for imported support files, not just entry-level
  metadata
- Detect local drift, missing local copies, missing source entries, and catalog /
  manifest mismatches explicitly
- Keep all scans bounded to the current vendor source set and the local
  `resistance-engine/` tree
- Use stdlib-only implementation primitives

## Non-goals

- No replacement of `catalog_index.json` in this shard
- No provenance model for deferred non-skill inventory surfaces yet
- No per-entry manifest files
- No Copilot or Claude adapter work
- No new third-party dependencies

---

## Approach

Shard 2 adds a central provenance registry alongside the current catalog snapshot.

The importer in `scripts/import_superpowers_catalog.py` continues to emit the shard-1
catalog files, but it is extended to also emit a provenance manifest under
`resistance-engine/provenance/`.

The catalog and manifest have different roles:

1. `catalog_index.json` describes what is currently imported locally
2. `provenance_manifest.json` describes the full expected skill/agent source set and
   the current state of each entry and file

This shard also introduces a standalone validator so provenance can be checked
without depending on a fresh import run.

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `resistance-engine/provenance/provenance_manifest.json` | Create via script | Central mandatory provenance registry for all skill and agent entries |
| `scripts/import_superpowers_catalog.py` | Modify | Extend importer to compute and write provenance data alongside the existing catalog snapshot |
| `scripts/validate_resistance_engine_provenance.py` | Create | Validate manifest structure, catalog consistency, state transitions, and digest-backed drift rules |
| `tests/scripts/test_import_superpowers_catalog.py` | Modify | Extend importer coverage for manifest emission and manifest state transitions |
| `tests/scripts/test_validate_resistance_engine_provenance.py` | Create | Focused validator coverage for happy-path and negative-path provenance checks |
| `resistance-engine/README.md` | Modify | Document the provenance manifest, its relationship to the catalog snapshot, and the validation command |

---

## Detailed design

### 1. Artifact relationship

Shard 2 keeps both the catalog and the manifest, but gives them distinct authority:

- `resistance-engine/catalog/catalog_index.json` remains the current import snapshot
- `resistance-engine/provenance/provenance_manifest.json` becomes the authoritative
  provenance registry

The manifest must contain an entry for every source skill directory and every source
agent file discovered under:

- `vendor/obra-superpowers/skills/`
- `vendor/obra-superpowers/agents/`

That rule holds even if the local copy is absent or stale.

### 2. Entry model

Each manifest entry should record:

- `entry_id`
- `entry_type` (`skill` or `agent`)
- `name`
- `source_repo`
- `source_path`
- `local_path`
- `manifest_state`
- `source_revision`
- `last_imported_at`
- `last_verified_at`
- `files`

`entry_id` should be stable and derived from the entry kind plus normalized name, so
the same logical entry can be tracked across repeated refreshes.

`manifest_state` must support at least:

- `imported`
- `missing-local-copy`
- `source-missing`
- `drift-detected`

### 3. File model

Every manifest entry must have a `files` array that provides file-level provenance.

Each file record should contain:

- `source_file`
- `local_file`
- `file_state`
- `source_digest`
- `local_digest`
- `last_verified_at`

For imported entries, the file array describes each copied file pair. For expected
entries that are not currently imported, the array should still describe the expected
source file set, with missing local data reflected in state rather than omission.

### 4. Digest and state semantics

This shard should use `hashlib.sha256` to compute deterministic content digests for:

- source files under `vendor/obra-superpowers/skills/` and
  `vendor/obra-superpowers/agents/`
- local files under `resistance-engine/skills/` and `resistance-engine/agents/`

State rules:

- matching source/local digests with both sides present -> `imported`
- source file present and local file absent -> `missing-local-copy`
- source entry absent from the current vendor tree -> `source-missing`
- source and local files both present but digest mismatch -> `drift-detected`

The spec should require consistent mapping between file-level states and entry-level
`manifest_state`; an entry cannot report `imported` while any of its files are in a
drift or missing state.

### 5. Importer integration

The current importer already exposes verified helpers and entrypoints:

- `normalize_name()`
- `_safe_output_path()`
- `_inventory_non_skill_surfaces()`
- `import_superpowers_catalog()`
- `main()`

Shard 2 should extend `import_superpowers_catalog()` so that one importer run emits:

- `catalog/catalog_index.json`
- `catalog/non_skill_inventory.json`
- `provenance/provenance_manifest.json`

The importer should keep its bounded source scan and reuse the existing normalized
entry names and local paths so shard 2 does not invent a second naming scheme.

### 6. Standalone validation

A dedicated validator should exist separately from the importer so provenance can be
checked without regenerating the workspace.

Because the importer intentionally resets and rebuilds `resistance-engine/` on each
run, local filesystem drift detection should be validator-owned in this shard. The
importer owns manifest generation and source-set reconciliation, while the validator
owns checks against the current local tree for missing or drifted files.

The validator should fail explicitly when:

- a catalog entry lacks a manifest entry
- an expected skill or agent from the source set lacks a manifest entry
- an entry or file state contradicts observed digests or file presence
- digests are missing or malformed where a state requires them
- `manifest_state` and file states disagree

### 7. Non-skill boundary

`resistance-engine/catalog/non_skill_inventory.json` remains separate in this shard.

The provenance manifest should not yet absorb:

- docs
- commands
- hooks
- plugin metadata
- root manifests and root guidance files

However, the manifest schema should remain extensible enough that a future shard can
add new `entry_type` values without rewriting the current skill/agent model.

---

## Required RED tests

Implementation must begin by extending the existing importer tests and adding new
validator tests before any production changes are written.

Required failing tests:

1. `tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_writes_provenance_manifest`
   - proves one importer run emits `resistance-engine/provenance/provenance_manifest.json`
   - asserts the manifest contains entries for the imported fixture skill and agent
2. `tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_marks_source_missing_entry`
   - simulates a source entry disappearing after an earlier manifest baseline
   - asserts the manifest retains the entry and marks it `source-missing`
3. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_rejects_catalog_entry_without_manifest`
   - proves validator failure when catalog and manifest disagree
4. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_rejects_imported_entry_with_missing_local_file`
   - deletes a local copied file after import
   - proves validator failure when an entry claims `imported` but local files are gone
5. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_rejects_drift_detected_file_digest_mismatch`
   - mutates a local copied support file
   - proves validator failure when digests disagree but the manifest still claims a clean state
6. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_rejects_file_state_entry_state_disagreement`
   - proves validator failure when file-level states contradict `manifest_state`

Refactor safety:

- existing shard-1 importer tests remain, but must be updated so they assert the new
  provenance artifact rather than treating catalog emission as the only output
- live-repo acceptance should continue to validate discovered source coverage, but
  should compare the manifest coverage to the discovered runtime source set rather
  than hardcoding only one static count

---

## BDD acceptance criteria

### Manifest coverage

1. **Given** the current vendor source set  
   **When** the importer runs  
   **Then** `resistance-engine/provenance/provenance_manifest.json` contains one
   entry for every discovered skill directory and agent file.

2. **Given** the current repository baseline  
   **When** the importer scans the live vendor repo  
   **Then** the manifest covers the discovered source set and the catalog continues
   to describe the currently imported local set.

3. **Given** a manifest entry  
   **When** it is inspected  
   **Then** it includes file-level provenance for every imported or expected file in
   that entry.

### State transitions

4. **Given** a local file is deleted after import  
   **When** the importer or validator checks provenance  
   **Then** the affected file and entry move to `missing-local-copy`.

5. **Given** a local file is modified after import  
   **When** the importer or validator checks provenance  
   **Then** the affected file and entry move to `drift-detected`.

6. **Given** a source entry disappears from the vendor source set  
   **When** the importer or validator checks provenance  
   **Then** the manifest retains the entry and marks it `source-missing` rather than
   silently deleting provenance history.

### Catalog / manifest consistency

7. **Given** a local catalog entry exists  
   **When** validation runs  
   **Then** exactly one manifest entry exists for that catalog entry.

8. **Given** a manifest entry claims `imported`  
   **When** validation runs  
   **Then** its local files exist, its digests are present, and its file states agree
   with the entry state.

9. **Given** a catalog/manifest mismatch  
   **When** validation runs  
   **Then** the validator fails explicitly rather than repairing or ignoring the
   mismatch silently.

### Boundaries

10. **Given** deferred non-skill surfaces in `non_skill_inventory.json`  
    **When** shard 2 completes  
    **Then** those surfaces remain outside the provenance manifest and are not given
    fake skill/agent lineage records.

---

## Security & risk analysis

### 1. Confidentiality

The provenance manifest should record lineage and digest metadata, not duplicate large
content bodies or unrelated local instructions.

Rules:

- store paths, states, revisions, and digests rather than raw file content
- avoid logging full manifest payloads during normal validation
- do not copy deferred non-skill file bodies into provenance metadata

### 2. Integrity

The main integrity risk is false provenance: claiming an entry is healthy when the
local files drifted or disappeared.

Rules:

- use deterministic sha256 digests
- derive states from observed files, not hand-maintained flags alone
- require validator failure on catalog/manifest contradiction
- keep entry identity stable across refreshes

### 3. Availability

This shard must remain bounded and should not introduce unbounded repo walks.

Rules:

- limit source scanning to `vendor/obra-superpowers/skills/` and `agents/`
- limit local scanning to the existing `resistance-engine/skills/` and `agents/`
  trees
- use one central manifest file rather than an explosion of per-entry files

### 4. Agentic and architectural vulnerabilities

The main architectural risk is blurring the current shard boundary by dragging in
deferred non-skill surfaces or adapter work.

Rules:

- provenance is mandatory for skills and agents only in this shard
- `catalog_index.json` remains during the transition instead of a flag-day
  replacement
- deferred non-skill inventory remains explicitly separate

### 5. Supply chain

The manifest strengthens rather than weakens source traceability, but only if it
records real source lineage.

Rules:

- every manifest entry must include source repo, source path, and source revision
- local divergence must remain visible instead of being normalized away
- no new third-party libraries are introduced for hashing or validation

---

## Future beads

| Candidate follow-on shard / bead | Priority | Effort | Notes |
| --- | --- | --- | --- |
| Skill consolidation sequencing spec | 1 | M | Builds on manifest-backed lineage when weaving local deltas into imported skills |
| Project-rule ingestion spec | 2 | M | Decides how imported behaviors read local repo guidance |
| Validation and upstream refresh spec | 2 | M | Extends provenance into repeatable refresh workflows and drift reporting UX |
| Non-skill provenance extension spec | 3 | S | Decides if deferred non-skill surfaces should later gain provenance coverage |

---

## Open implementation constraints already decided

- `resistance-engine/` remains the canonical local workspace
- provenance is mandatory for every skill and agent entry
- provenance is stored in one central manifest/index, not per-entry files
- `catalog_index.json` remains in place during this shard
- deferred non-skill surfaces stay outside the provenance manifest for now
- shard 2 uses stdlib hashing and validation only

---

## Summary

Shard 2 turns shard 1’s import snapshot into a traceable lineage system:

- one central provenance manifest for every skill and agent
- file-level provenance for imported support files
- explicit state transitions for missing, stale, and drifted entries
- standalone validation
- bounded scope that preserves the current catalog and non-skill inventory split

That gives later shards a trustworthy base for local edits, refreshes, and future
adapter work without overloading this step with non-skill or platform concerns.
