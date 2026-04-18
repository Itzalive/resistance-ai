## Resistance engine pruning-policy prerequisite shard

**Date:** 2026-04-15
**Status:** Drafted for review
**Parent spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-catalog-retarget-design.md`
**Prerequisite shard:** `docs/superpowers/specs/2026-04-15-resistance-engine-provenance-manifest-design.md`
**Follow-on shard:** authoring pair rewrite for `brainstorming` + `writing-plans`

---

## Problem

Shard 2 established a provenance model for imported skills and agents under
`resistance-engine/`, but the current model still assumes every imported upstream
file is either:

- present and healthy locally
- unexpectedly missing locally
- drifted locally
- missing from source entirely

That is correct for pure import refreshes, but it is too strict for consolidation.
The first authoring rewrite needs to be able to remove imported support files on
purpose without making the validator report corruption.

The current implementation has no way to express that intent:

- `scripts/import_superpowers_catalog.py` always records every copied file in
  `provenance_manifest.json`
- `scripts/validate_resistance_engine_provenance.py` treats absent files as
  `missing-local-copy`
- manifest coverage checks assume the current catalog file set is the complete local
  expectation for each imported entry

If consolidation proceeds without a prerequisite change, the first rewrite spec
would need to mix skill design with provenance semantics. That would make the skill
spec harder to reason about and would obscure the remaining shard-3 clusters in the
umbrella roadmap.

---

## Goals

- Add a dedicated local declaration surface for intentional pruning of imported files
- Extend provenance so file records distinguish:
  - what the local tree is supposed to do
  - what the validator actually observed
- Preserve upstream lineage for pruned files rather than deleting their provenance
- Keep the validator strict for contradictions and malformed override data
- Amend the umbrella roadmap so shard 3 is explicitly a sequence of bounded
  consolidation sub-specs
- Keep the authoring pair spec (`brainstorming` + `writing-plans`) focused on skill
  rewrites rather than provenance primitives

## Non-goals

- No rewrite of `brainstorming` or `writing-plans` content in this shard
- No local-only skill creation in this shard
- No Copilot or Claude adapter changes
- No replacement of `catalog_index.json` or `provenance_manifest.json`
- No new third-party dependencies

---

## Approach

This shard inserts a narrow prerequisite before the first authoring consolidation
spec.

It introduces a dedicated local override file that declares when a file imported
from upstream is intentionally omitted from the local tree. The importer merges that
declaration into file-level provenance, and the validator enforces it against the
actual local tree.

That keeps the model explicit:

1. upstream source set remains authoritative for lineage
2. the local override file is authoritative for intentional pruning intent
3. the provenance manifest remains the merged registry used by validation

The follow-on authoring spec can then prune files inside `brainstorming` and
`writing-plans` without redefining provenance semantics at the same time.

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `docs/superpowers/specs/2026-04-15-resistance-engine-catalog-retarget-design.md` | Modify | Make shard 3 explicitly sequential and list the bounded follow-on clusters |
| `resistance-engine/consolidation/consolidation_overrides.json` | Create | Local declaration file for intentional pruning decisions |
| `scripts/import_superpowers_catalog.py` | Modify | Merge override declarations into file-level provenance output |
| `scripts/validate_resistance_engine_provenance.py` | Modify | Validate override-informed file expectations against the local tree |
| `tests/scripts/test_import_superpowers_catalog.py` | Modify | Cover default and override-driven pruning policy emission |
| `tests/scripts/test_validate_resistance_engine_provenance.py` | Modify | Cover valid pruning, contradiction cases, malformed override entries, and policy preservation |
| `resistance-engine/README.md` | Modify | Document the override file and its relationship to provenance validation |

---

## Detailed design

### 1. Override file

Create a dedicated local file:

- `resistance-engine/consolidation/consolidation_overrides.json`

This file is the only local source of truth for intentional pruning in this shard.
It should not try to describe full skill rewrites yet.

The file should be a JSON list of entry overrides. Each override should contain:

- `entry_id`
- `file_overrides`

Each file override should contain:

- `source_file`
- `local_sync_policy`

`local_sync_policy` must support:

- `required`
- `pruned`

`source_file` must refer to the upstream-relative file path already used in
provenance records, for example `skills/brainstorming/visual-companion.md`.

### 2. Provenance extension

Each provenance file record should gain a new field:

- `local_sync_policy`

This field expresses what the local tree is expected to do, independent of the
observed health state already carried by `file_state`.

The split is intentional:

- `local_sync_policy` = expectation (`required` or `pruned`)
- `file_state` = observation (`imported`, `missing-local-copy`, `drift-detected`,
  `source-missing`)

This shard should keep entry-level `manifest_state` behavior unchanged unless file
policy evaluation proves a new entry-level state is required. The goal is to extend
file semantics surgically, not redesign the whole manifest.

### 3. Importer integration

`scripts/import_superpowers_catalog.py` should:

1. load `resistance-engine/consolidation/consolidation_overrides.json` if present
2. preserve that override file across import refreshes instead of deleting it during
   output-root reset
3. validate that every override references:
   - a real imported entry
   - a real upstream file for that entry
4. emit `local_sync_policy: "required"` by default for every imported file
5. override selected file records to `local_sync_policy: "pruned"` where declared
6. preserve those policies when carrying forward `source-missing` entries from an
   earlier manifest baseline

The importer must fail explicitly if the override file contains:

- duplicate `entry_id` values
- duplicate `source_file` overrides within an entry
- unknown `entry_id`
- unknown `source_file`
- malformed JSON or wrong top-level shapes

### 4. Validator semantics

`scripts/validate_resistance_engine_provenance.py` should enforce the following
rules:

- `required` + file absent -> `missing-local-copy`
- `required` + file present with unexpected digest -> `drift-detected`
- `pruned` + file absent -> valid
- `pruned` + file present -> explicit contradiction
- `source-missing` entries keep their prior `local_sync_policy` values and still
  fail on malformed lineage data

The validator must also check that the override-informed manifest remains complete:

- every imported source file still has a provenance record
- pruning changes policy, not coverage
- lineage fields remain present for pruned files even though the local file is
  intentionally absent

### 5. Catalog and manifest consistency

This shard should keep the current division of authority:

- `catalog_index.json` = current imported snapshot
- `provenance_manifest.json` = authoritative lineage and state registry

The new override file is local configuration, not a replacement catalog. The
validator should compare the manifest to the catalog and the override file together:

- catalog proves what was imported from source
- override file proves which imported files are intentionally omitted locally
- manifest proves the merged expected state plus observed health

### 6. README and operator model

`resistance-engine/README.md` should document:

- the purpose of `consolidation/consolidation_overrides.json`
- that pruning intent must be declared there rather than inferred from missing files
- the existing import command
- the existing provenance validation command
- that this shard only establishes pruning semantics; actual skill rewrites land in
  later consolidation specs

---

## Required RED tests

Implementation must begin with failing tests before any production changes.

Required failing tests:

1. `tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_defaults_local_sync_policy_to_required`
   - proves imported file records emit `local_sync_policy: "required"` when no
     override file exists
2. `tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_applies_pruned_file_override`
   - proves the importer merges an override file into the emitted manifest
3. `tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_preserves_consolidation_override_file`
   - proves import refreshes do not delete the local override file
4. `tests/scripts/test_import_superpowers_catalog.py::test_import_superpowers_catalog_rejects_unknown_override_target`
   - proves malformed override references fail explicitly
5. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_accepts_pruned_file_absence`
   - proves a `pruned` file may be absent without being treated as
     `missing-local-copy`
6. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_rejects_present_pruned_file`
   - proves a `pruned` file still present locally is treated as a contradiction
7. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_preserves_pruning_policy_for_source_missing_entry`
   - proves a carried-forward `source-missing` entry keeps its prior pruning intent
8. `tests/scripts/test_validate_resistance_engine_provenance.py::test_validate_provenance_rejects_malformed_override_file`
   - proves malformed override structures fail explicitly and do not get silently
     repaired

Refactor safety:

- existing provenance tests for drift, missing-local-copy, malformed digests, and
  completeness must remain green
- live importer acceptance should continue to verify source-set coverage, with the
  override system changing policy rather than deleting file lineage records

---

## BDD acceptance criteria

### Override declaration

1. **Given** no local override file  
   **When** the importer emits provenance  
   **Then** every imported file record defaults to `local_sync_policy = required`.

2. **Given** a valid override entry targeting one imported file  
   **When** the importer runs  
   **Then** that file keeps its lineage metadata but is marked `local_sync_policy =
   pruned`.

3. **Given** an override references an unknown entry or file  
   **When** import or validation runs  
   **Then** the command fails explicitly instead of ignoring the bad override.

4. **Given** `consolidation/consolidation_overrides.json` already exists  
   **When** the importer refreshes `resistance-engine/`  
   **Then** that local override file survives unchanged.

### Validation behavior

5. **Given** a file is marked `pruned`  
   **When** it is absent locally  
   **Then** validation succeeds for that file.

6. **Given** a file is marked `pruned`  
   **When** it still exists locally  
   **Then** validation fails explicitly because the local tree contradicts declared
   pruning intent.

7. **Given** a file is marked `required`  
   **When** it is absent locally  
   **Then** validation still reports `missing-local-copy`.

8. **Given** a source entry later disappears upstream  
   **When** the importer carries it forward as `source-missing`  
   **Then** the prior file-level pruning policy remains visible in provenance.

### Roadmap integrity

9. **Given** the retarget roadmap is read after this shard is approved  
   **When** shard 3 is inspected  
   **Then** it explicitly lists multiple bounded consolidation sub-specs instead of
   implying one catch-all skill-consolidation document.

---

## Security & Risk Analysis

### 1. Confidentiality

This shard processes local JSON configuration plus existing catalog and provenance
artifacts. It does not introduce new secrets or PII flows. The implementation should
continue the current practice of failing with structural error messages that mention
artifact paths and entry identifiers only, not file contents.

### 2. Integrity

The override file must be treated as hostile local input. The importer and validator
must validate:

- top-level JSON shape
- required fields
- duplicate declarations
- allowed `local_sync_policy` values
- that referenced entries and files actually exist in the imported source set

No path from the override file may be used to construct unbounded filesystem writes.
All local paths must continue to flow through the existing bounded path helpers and
catalog/provenance derivation logic.

### 3. Availability

All scans remain bounded to:

- the current source set under `vendor/obra-superpowers/`
- the local `resistance-engine/` tree
- the override file entries explicitly listed by the operator

No unbounded network calls or new background processes are introduced.

### 4. Agentic & architectural vulnerabilities

The override file gives the operator power to declare pruning intent, so explicit
validation is mandatory. Silent ignore behavior would let malformed declarations
poison future consolidation work. Fail-closed validation is therefore required.

If the override file is malformed, missing required fields, or references unknown
targets, the importer or validator must fail explicitly and leave broken structural
artifacts un-rewritten.

### 5. Supply chain

This shard uses only the current Python stdlib plus the already-present importer and
validator modules. No new package or external service is required.

---

## Future beads

- **P1 / Medium** — Authoring pair rewrite spec for `brainstorming` +
  `writing-plans`
- **P1 / Small** — `writing-skills` follow-on consolidation spec
- **P1 / Medium** — Execution workflow consolidation spec
- **P1 / Medium** — Review / finish workflow consolidation spec
- **P2 / Medium** — Remaining imported gaps plus local-only additions spec
- **P2 / Small** — Project-rule ingestion spec for rewritten local authoring skills

---

## Open questions intentionally resolved by this spec

- Pruning support is **not** bundled into the authoring pair rewrite
- Pruning intent is declared in a **dedicated local override file**
- Pruning changes file policy, **not** lineage coverage
- Shard 3 is now explicitly a **sequence of bounded sub-specs**
