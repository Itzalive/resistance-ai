## Resistance engine import catalog shard

**Date:** 2026-04-15
**Status:** Drafted for review
**Parent spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-catalog-retarget-design.md`

---

## Problem

The retargeted resistance-engine umbrella spec intentionally decomposes the rewrite
into sequential shard specs. The first shard must produce a real, coherent local
catalog rather than more controller or overlay scaffolding.

The repo is currently at a fresh-start baseline:

- previously completed controller and overlay shards have been reverted
- `resistance-engine/` does not exist yet
- `vendor/obra-superpowers/skills/` currently contains 14 skill directories
- `vendor/obra-superpowers/agents/` currently contains 1 top-level agent file:
  `code-reviewer.md`

That makes shard 1 responsible for the first durable local artifact: importing the
vendor skills and agent files into the new `resistance-engine/` workspace, while
inventorying the rest of the vendor repo for later decisions.

---

## Goals

- Create `resistance-engine/` as the canonical local workspace
- Import every directory under `vendor/obra-superpowers/skills/` with its support
  files preserved
- Import every agent file under `vendor/obra-superpowers/agents/`
- Normalize imported names into a coherent local layout
- Emit a unified minimal catalog index for imported skills and agents
- Inventory and classify vendor surfaces outside `skills/` and `agents/`
- Keep `vendor/obra-superpowers/` pristine and read-only
- Fail explicitly on collisions, malformed inputs, or unsafe path derivations

## Non-goals

- No full provenance or divergence ledger in this shard
- No upstream refresh workflow in this shard
- No Copilot or Claude adapter behavior in this shard
- No reimport of the reverted controller or overlay shards unless this shard proves a
  hard dependency, which it currently does not
- No blanket mirror of the entire vendor repository

---

## Approach

Shard 1 uses a filesystem-first import pipeline with a minimal catalog index.

The import script reads from two direct source surfaces:

1. `vendor/obra-superpowers/skills/`
2. `vendor/obra-superpowers/agents/`

It writes into three local output surfaces:

1. `resistance-engine/skills/`
2. `resistance-engine/agents/`
3. `resistance-engine/catalog/`

The importer copies complete skill directories and top-level agent files into the
local workspace under normalized names, then emits a unified catalog index plus a
separate inventory for non-skill vendor content.

The rest of the vendor repo is not blindly mirrored. Instead, shard 1 inventories it
and labels each surface so later shard specs can make explicit import decisions.

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `resistance-engine/README.md` | Create | Explain the local workspace, import scope, and read-only role of `vendor/obra-superpowers/` |
| `resistance-engine/skills/` | Create | Canonical local directories for imported skills |
| `resistance-engine/agents/` | Create | Canonical local files for imported agents |
| `resistance-engine/catalog/catalog_index.json` | Create | Unified minimal index for imported skills and agents |
| `resistance-engine/catalog/non_skill_inventory.json` | Create | Classification inventory for vendor surfaces outside `skills/` and `agents/` |
| `scripts/import_superpowers_catalog.py` | Create | Deterministic importer for vendor skills, agents, and catalog outputs |
| `tests/scripts/test_import_superpowers_catalog.py` | Create | RED/GREEN coverage for happy-path imports and negative-path failures |

---

## Detailed design

### 1. Source shapes

This shard imports two different source shapes:

- **skill sources:** directories under `vendor/obra-superpowers/skills/`
- **agent sources:** markdown files under `vendor/obra-superpowers/agents/`

The importer must treat each source shape explicitly rather than pretending the
vendor repo uses one uniform structure.

### 2. Normalized local layout

Imported skills land under:

- `resistance-engine/skills/<normalized-name>/`

Imported agents land under:

- `resistance-engine/agents/<normalized-name>.md`

Normalization is conservative:

- if the source name is already valid kebab-case, keep it
- if normalization would change the name, the transformation must be deterministic
- if two sources would normalize to the same local path, the import fails with an
  explicit collision error

The importer must never guess a winner in a collision.

### 3. Unified minimal catalog index

`resistance-engine/catalog/catalog_index.json` stores one entry per imported item.

Each entry must include:

- `entry_type` (`skill` or `agent`)
- `name`
- `source_repo`
- `source_path`
- `local_path`
- `imported_files`
- `source_revision`
- `imported_at`

This is intentionally minimal. Shard 2 will extend the metadata model with
divergence and refresh semantics.

### 4. Non-skill inventory

The importer must inventory vendor surfaces outside `skills/` and `agents/`, such
as docs, commands, hooks, plugin metadata, root manifests, and top-level guidance
files.

`resistance-engine/catalog/non_skill_inventory.json` must record, for each
discovered surface:

- the source path
- a surface kind
- a classification decision

Classification decisions are:

- `required-now`
- `defer`
- `ignore`

Shard 1 should only import non-skill content immediately when the coherent local
catalog would be incomplete without it. Otherwise the surface is inventoried and
deferred.

### 5. Failure and safety rules

The importer must fail explicitly for:

- source path collisions after normalization
- missing required source surfaces
- entries that resolve outside `resistance-engine/`
- malformed or unsupported source shapes that the importer does not know how to
  classify

The importer must not:

- write into `vendor/obra-superpowers/`
- silently skip malformed entries
- recursively mirror the full vendor repository without classification

---

## BDD acceptance criteria

### Canonical import

1. **Given** the current vendor repo layout  
   **When** the shard-1 importer runs  
   **Then** every directory under `vendor/obra-superpowers/skills/` is copied into
   `resistance-engine/skills/` with its support files preserved.

2. **Given** the current vendor repo layout  
   **When** the shard-1 importer runs  
   **Then** every markdown file under `vendor/obra-superpowers/agents/` is copied
   into `resistance-engine/agents/` under a normalized local name.

3. **Given** an imported skill or agent  
   **When** `resistance-engine/catalog/catalog_index.json` is inspected  
   **Then** the entry records its type, source path, local path, imported files, and
   source reference metadata.

### Boundaries and classification

4. **Given** a vendor repo surface outside `skills/` and `agents/`  
   **When** the inventory pass runs  
   **Then** the surface appears in
   `resistance-engine/catalog/non_skill_inventory.json` with an explicit
   classification decision instead of being dropped invisibly.

5. **Given** the vendor repo contains content outside `skills/` and `agents/`  
   **When** shard 1 completes  
   **Then** only surfaces classified as `required-now` are imported, and all other
   surfaces remain untouched in the vendor repo.

### Negative paths

6. **Given** two source entries that normalize to the same local name  
   **When** the importer runs  
   **Then** the importer fails with a collision error rather than overwriting one
   entry.

7. **Given** a malformed source entry or unsupported source shape  
   **When** the importer encounters it  
   **Then** the importer reports the issue explicitly and stops rather than silently
   skipping it.

8. **Given** the importer is asked to write a path outside `resistance-engine/`  
   **When** path resolution runs  
   **Then** the importer fails before writing any output.

### Live-repo acceptance

9. **Given** the current repository baseline  
   **When** the importer inventories the live vendor repo  
   **Then** it discovers the current source set of 14 skill directories and 1 agent
   file, and the generated catalog matches that discovered set.

---

## Security & risk analysis

### 1. Confidentiality

This shard copies vendor-authored files into a local workspace. The main
confidentiality risk is uncontrolled propagation of content into logs or metadata.

Rules:

- catalog metadata must contain paths, types, and source references, not dumped file
  contents
- validation output must avoid echoing large content bodies
- no secrets or unrelated repo content may be copied into metadata by convenience

### 2. Integrity

The main integrity risks are silent collisions, unsafe path traversal, and false
assumptions about source shapes.

Rules:

- normalization collisions must be fatal
- all resolved output paths must be bounded under `resistance-engine/`
- source shapes must be validated before copy
- unsupported shapes must be surfaced explicitly

### 3. Availability

This shard should stay bounded and predictable even if the vendor repo grows.

Rules:

- shard 1 only walks the selected vendor surfaces plus a top-level inventory pass
- inventory output must record decisions rather than triggering recursive import of
  everything
- failures must happen early before partial uncontrolled copy

### 4. Agentic and architectural vulnerabilities

The main architectural risk is accidentally rebuilding the old controller/overlay
sequence by sneaking its artifacts back in.

Rules:

- reverted controller and overlay work stays out of shard 1 unless a hard dependency
  is discovered and explicitly approved
- shard 1 owns import/catalog boundaries only
- richer provenance, refresh, and adapter behaviors remain later shards

### 5. Supply chain

This shard depends on a vendor repository snapshot, so provenance of source origin
must remain visible even in the minimal metadata model.

Rules:

- `vendor/obra-superpowers/` remains read-only
- every imported entry must preserve source path and source reference metadata
- no new third-party dependency is introduced without explicit justification

---

## Future beads

| Candidate follow-on shard / bead | Priority | Effort | Notes |
| --- | --- | --- | --- |
| Provenance manifest spec | 1 | M | Adds divergence, refresh, and richer source lineage semantics |
| Skill consolidation sequencing spec | 1 | M | Begins weaving local changes into imported skills |
| Agent integration sequencing spec | 2 | S | Defines how imported agents participate in the coherent local catalog |
| Project-rule ingestion spec | 2 | M | Decides which local project docs must be consulted by imported local behaviors |
| Validation and refresh spec | 2 | M | Adds repeatable re-import and drift reporting workflow |

---

## Open implementation constraints already decided

- `resistance-engine/` is the canonical new workspace root
- all vendor `skills/` directories are imported in shard 1
- all vendor `agents/` markdown files are imported in shard 1
- non-skill vendor content is inventoried and classified, not blindly mirrored
- shard 1 uses a unified minimal catalog index
- reverted controller and overlay shards remain out of scope unless explicitly needed

---

## Summary

Shard 1 creates the first real deliverable of the retargeted architecture:

- a fresh `resistance-engine/` workspace
- imported vendor skills and agents under coherent local paths
- a unified minimal catalog index
- an explicit inventory of the rest of the vendor repo

That gives the rewrite a usable local surface immediately while keeping provenance,
refresh logic, adapters, and old scaffold revival out of scope for now.
