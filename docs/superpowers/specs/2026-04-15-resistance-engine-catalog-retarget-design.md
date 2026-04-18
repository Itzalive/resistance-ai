## Resistance engine coherent local catalog retarget

**Date:** 2026-04-15
**Status:** Drafted for review
**Supersedes:** `docs/superpowers/specs/2026-04-14-superpowers-overlay-lifecycle-design.md`

---

## Problem

The current approved Superpowers rewrite spec is structured around a
controller-plus-overlay architecture. That design improves separation of concerns,
but it does not make the first implementation milestone a single coherent local
skill set.

The desired direction is different:

1. start by importing every upstream Superpowers skill
2. normalize the imported skills into one coherent local catalog under
   `resistance-engine/`
3. keep local additions as first-class peers in that same catalog
4. preserve upstream traceability without making a heavyweight overlay runtime the
   center of the architecture

The rewrite therefore needs a new source-of-truth model and a new shard order.

---

## Goals

- Make `resistance-engine/` the single coherent public skill framework
- Import every upstream skill as the baseline for the local catalog
- Normalize names and paths during import so the local framework is coherent from
  day one
- Preserve machine-readable provenance for every local skill
- Keep local-only skills as first-class peers rather than sidecar extensions
- Keep `vendor/obra-superpowers` as a pristine upstream reference snapshot
- Retain truthful Copilot-first and Claude-compatible behavior without claiming
  fake parity
- Keep repo-specific guidance local without requiring a heavyweight runtime overlay
  architecture
- Replace the current shard order with an import-first roadmap

## Non-goals

- No edits inside `vendor/obra-superpowers`
- No silent loss of upstream provenance after import
- No requirement that runtime behavior be driven by a generic overlay hook engine
- No collapsing all behavior into a small number of mega-skills
- No monolithic rewrite that skips sharding, review, or acceptance criteria

---

## Approach

Retarget the rewrite around two durable artifacts and one local input surface:

1. **Pristine upstream snapshot:** `vendor/obra-superpowers/` remains the pinned
   source input.
2. **Canonical local catalog:** `resistance-engine/` becomes the only coherent
   skill surface that the repo evolves and uses.
3. **Local project inputs:** `AGENTS.md` and companion docs remain local sources of
   repo-specific commands, architecture notes, and workflow rules, but the rewrite
   treats them as documented local inputs rather than a heavyweight overlay runtime.

The main architectural shift is this:

- the previous spec centered the lifecycle controller and overlay contract
- the retargeted spec centers the coherent local skill catalog and provenance ledger

The controller and adapter ideas can still exist, but they become downstream
consumers of the coherent local catalog rather than the first implementation target.

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `.gitmodules` | Keep / modify if needed | Continue tracking the upstream reference repository |
| `vendor/obra-superpowers/` | Keep reference only | Pinned pristine upstream source; never edited directly |
| `resistance-engine/` | Expand | Canonical normalized local skill catalog and related metadata |
| `resistance-engine/provenance/` | Create | Source maps, import manifests, divergence records, refresh metadata |
| `AGENTS.md` | Later modify | Remain project-local guidance consumed by rewritten local skills |
| `docs/superpowers/project/` | Later modify | Companion local guidance docs referenced by local skills |
| `docs/superpowers/specs/` | Modify | Store this retarget spec and later shard specs |
| `docs/superpowers/plans/` | Modify later | Store plans derived from the retargeted shard specs |

---

## Detailed design

### 1. Canonical source-of-truth model

`resistance-engine/` is the only coherent skill tree the repo should present to
the agent. Every skill visible in the local framework must exist there exactly
once.

Each skill entry must record whether it is:

- `superpowers-derived`
- `local-only`

For superpowers-derived skills, the repo must also be able to trace:

- source framework or repository
- source path
- pinned source revision or equivalent import reference
- normalized local path
- whether the local copy has diverged

### 2. Import and normalization pipeline

The first shard must import every upstream skill into the local framework.
Importing is not a literal mirror; it is a controlled normalization step that
produces the coherent local naming and path scheme immediately.

Normalization rules must be explicit and deterministic. If two upstream skills
would normalize to the same local name or path, the import must fail with a
collision report rather than silently overwriting one.

### 3. Provenance ledger instead of heavyweight overlay runtime

The rewrite still needs traceability, but not necessarily a broad overlay runtime.
The retargeted design replaces the overlay contract as the architectural center
with a thin provenance layer, such as:

- import manifest
- skill source map
- divergence ledger
- refresh report format

This metadata exists to answer maintenance questions:

- what came from another Superpowers-family source
- what was added locally
- what changed locally
- what needs attention when an imported source changes

### 4. Local-only skills as first-class peers

Local-only skills should live beside superpowers-derived skills in the same normalized
catalog. They are not segregated behind an extension namespace. Their distinction
from superpowers-derived skills is carried in metadata, not in a fragmented public
surface.

This keeps the local framework coherent while preserving maintainability.

### 5. Project-rule ingestion

Repo-specific rules still belong in local project docs such as `AGENTS.md` and
companion files. The retargeted design does not require a heavyweight generic
overlay engine for runtime behavior. Instead, rewritten local skills should define
documented points where they consult local project guidance.

That preserves the separation between generic and repo-specific information without
making overlay machinery the main organizing principle of the rewrite.

### 6. Adapter and lifecycle sequencing

Copilot CLI remains the reference harness, and Claude compatibility still requires
truthful downgrade behavior where parity is not real. The difference is sequencing:

- first establish the complete coherent local catalog
- then align that catalog with Copilot behavior
- then document Claude compatibility and downgrade semantics

This avoids designing adapters against an incomplete or fragmented skill surface.

### 7. Retargeted shard roadmap

The new roadmap should be sequential:

1. **Upstream inventory and full import spec**  
   Define the import scope, normalization rules, and collision handling.
2. **Provenance manifest spec**  
   Define source-map, divergence, and refresh metadata for the coherent local
   catalog.
3. **Skill consolidation spec sequence**  
   Break consolidation into bounded sub-specs rather than one document:
   - prerequisite pruning-policy support for intentionally omitted imported files
   - authoring pair rewrite for `brainstorming` + `writing-plans`
   - authoring follow-on for `writing-skills`
   - execution workflow cluster
   - review / finish workflow cluster
   - remaining imported gaps plus local-only additions
4. **Copilot adapter spec**  
   Make the coherent local catalog executable in the reference harness.
5. **Claude compatibility spec**  
   Define truthful downgrade and compatibility behavior.
6. **Project-rule ingestion spec**  
   Define how rewritten local skills read repo-specific inputs from local docs.
7. **Validation and upstream refresh spec**  
   Cover regression checks, refresh safety, and drift reporting.

The current overlay-contract-first shard should be repurposed into provenance
metadata and project-rule-ingestion work rather than remaining the second pillar of
the architecture.

The original shard-3 wording was intentionally coarse. As implementation sequencing
has become concrete, shard 3 is now explicitly decomposed so later clusters and
missing skills remain visible in the roadmap instead of being implied by a single
overloaded consolidation spec.

---

## BDD acceptance criteria

### Canonical local catalog

1. **Given** a pinned upstream Superpowers revision  
   **When** the import process runs  
   **Then** every upstream skill appears in the normalized `resistance-engine/`
   catalog exactly once.

2. **Given** an imported local skill  
   **When** its metadata is inspected  
   **Then** the framework can determine whether the skill is `superpowers-derived` or
   `local-only`.

3. **Given** a superpowers-derived local skill  
   **When** its provenance record is inspected  
   **Then** the record shows the source repository, source path, normalized local
   path, and whether the local copy has diverged.

4. **Given** two upstream skills that would collide under the normalization rules  
   **When** import runs  
   **Then** the process fails explicitly with a collision report rather than
   silently overwriting one skill.

### Local evolution

5. **Given** a local-only skill added after the baseline import  
   **When** the local catalog is enumerated  
   **Then** the skill appears as a first-class peer in the same coherent surface as
   superpowers-derived skills.

6. **Given** a rewritten local skill that needs repo-specific guidance  
   **When** it reads local project inputs  
   **Then** it does so through documented local sources rather than assuming a
   heavyweight overlay runtime exists.

### Source refresh and drift visibility

7. **Given** a newer source revision  
   **When** the refresh comparison runs  
   **Then** added, changed, removed, and locally diverged skills are reported
   explicitly.

8. **Given** missing or malformed provenance metadata for a local skill  
   **When** validation runs  
   **Then** the process fails explicitly rather than allowing silent drift.

### Adapter sequencing

9. **Given** the coherent local catalog is incomplete  
   **When** adapter work is proposed  
   **Then** the roadmap rejects adapter completion as premature.

10. **Given** a behavior Copilot CLI can support but Claude cannot match exactly  
    **When** the compatibility layer is specified  
    **Then** the spec documents an explicit downgrade path rather than claiming
    parity.

---

## Security & risk analysis

### 1. Confidentiality

Importing upstream skills and weaving in local behavior must not copy secrets or
sensitive repo data into generic metadata. Provenance records should track origins,
paths, and divergence state, not confidential project content.

Rules:

- provenance files must avoid secret-bearing payloads
- local project guidance remains in local docs
- validation and logging must not dump sensitive local instructions indiscriminately

### 2. Integrity

The primary integrity risk is silent drift:

- missing upstream skills after import
- name/path collisions hidden by normalization
- local edits that cannot be traced back to source
- project-specific behavior creeping into generic skill text without visibility

Rules:

- require explicit collision failures
- require complete provenance metadata for superpowers-derived skills
- require visible distinction between superpowers-derived and local-only skills
- require documented local input points for repo-specific behavior

### 3. Availability

A full import and refresh workflow can become expensive if it scans without bounds
or lacks deterministic comparison rules.

Rules:

- use a pinned upstream revision for each import or refresh event
- define deterministic normalization and comparison behavior
- fail fast on malformed metadata or naming conflicts
- keep the rewrite sharded so validation remains reviewable

### 4. Agentic and architectural vulnerabilities

Risks:

- building a single local skill surface but losing accountability for origin
- over-engineering a runtime overlay system that obscures the real source of truth
- claiming platform parity before the coherent local catalog exists

Rules:

- keep `resistance-engine/` as the canonical surface
- keep provenance explicit and machine-readable
- defer adapter guarantees until after the catalog baseline exists

### 5. Supply chain

The rewrite depends on upstream content, so provenance and refresh behavior must be
honest about that dependency.

Rules:

- `vendor/obra-superpowers` remains reference-only
- imported skills must retain traceable origin metadata
- no new third-party dependency is introduced without explicit justification in
  shard specs

---

## Future beads

| Candidate shard / bead | Priority | Effort | Notes |
| --- | --- | --- | --- |
| Upstream inventory and import spec | 1 | M | Defines full-skill import scope, normalization, and collision rules |
| Provenance manifest spec | 1 | M | Defines source maps, divergence records, and refresh metadata |
| Skill consolidation sequencing spec | 1 | M | Orders local behavior weaving across the normalized local catalog |
| Copilot CLI adapter spec | 1 | M | Aligns the coherent local catalog with the reference harness |
| Claude compatibility spec | 2 | M | Documents truthful downgrade paths |
| Project-rule ingestion spec | 2 | M | Defines how local skills consult repo-specific guidance |
| Validation and upstream refresh spec | 2 | M | Covers catalog validation, drift reporting, and refresh safety |

---

## Open implementation constraints already decided

- `vendor/obra-superpowers` remains pristine and read-only
- `resistance-engine/` is the canonical coherent skill surface
- local-only skills are first-class peers in the same catalog
- provenance metadata is required
- Copilot CLI remains the reference harness
- Claude compatibility is required, but fake parity is forbidden

---

## Summary

This retarget turns the rewrite from an overlay-first architecture into a
catalog-first architecture:

- full upstream import first
- normalized coherent local skill tree first
- provenance instead of heavyweight overlay machinery as the maintenance backbone
- local-only skills as peers
- adapters and project-rule ingestion sequenced after the canonical local surface

That better matches the desired end state: one coherent set of skills, with enough
traceability to evolve safely over time.
