## Resistance engine authoring-pair rewrite shard

**Date:** 2026-04-15
**Status:** Drafted for review
**Parent spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-catalog-retarget-design.md`
**Prerequisite shard:** `docs/superpowers/specs/2026-04-15-resistance-engine-pruning-policy-design.md`
**Follow-on shards:** authoring follow-on rewrite for `writing-skills`; project-rule-ingestion / generalized overlay architecture

---

## Problem

The next consolidation target is still the authoring pair:

- `resistance-engine/skills/brainstorming/`
- `resistance-engine/skills/writing-plans/`

But the original draft for this shard assumed the rewritten skills would continue to
depend on repo-root rulebooks such as `SPEC_DESIGN.md`, `PLAN_WRITING.md`,
`SPEC_REVIEW_MANIFEST.md`, and `SPEC_RUBRIC.md`.

That is now the wrong architecture.

The desired direction is different:

1. the skills must be self-sufficient by default from inside `resistance-engine/`
2. the default `SPEC_DESIGN` behavior should live in `brainstorming/SKILL.md`
3. the default `PLAN_WRITING` behavior should live in `writing-plans/SKILL.md`
4. default spec-review assets should live beside `brainstorming`
5. repo-root files should be optional overlays only, never required setup

### Current-state evidence

This shard is grounded in repository reads instead of memory alone. The current
workspace already exposes the concrete mechanisms and review gates that the
rewritten authoring pair must preserve as shipped defaults:

```text
$ rg -n "^### Threat Model \\(CIA\\)|SPEC_REVIEW_MANIFEST|SPEC_RUBRIC|\\.review_log\\.jsonl|\\[SPEC-APPROVED\\]" resistance-engine/skills/brainstorming/*.md
resistance-engine/skills/brainstorming/SKILL.md:16:- `SPEC_REVIEW_MANIFEST.md` is the shipped default review procedure
resistance-engine/skills/brainstorming/SKILL.md:17:- `SPEC_RUBRIC.md` is the shipped default grading contract
resistance-engine/skills/brainstorming/SKILL.md:250:- Log the rejection to `.review_log.jsonl`
resistance-engine/skills/brainstorming/SKILL.md:285:**Pass condition:** The auditing model returns `[SPEC-APPROVED]`.
resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md:51:- the cross-model audit requirement with an opposite model family
resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md:52:- `.review_log.jsonl` recording of review outcomes

$ rg -n "^### Risk & Confidence Assessment|Tabula Rasa Mandate|Unified Coherence Check|\\.review_log\\.jsonl" resistance-engine/skills/writing-plans/*.md
resistance-engine/skills/writing-plans/SKILL.md:25:## Tabula Rasa Mandate
resistance-engine/skills/writing-plans/SKILL.md:54:### Risk & Confidence Assessment
resistance-engine/skills/writing-plans/SKILL.md:209:## Unified Coherence Check
resistance-engine/skills/writing-plans/SKILL.md:250:Record the result and raw reasons in `.review_log.jsonl` at the repo root.
```

These reads are the source-of-truth baseline for this shard: the rewritten
skills must keep CIA burden-of-proof review, opposite-family audit logging, and
fail-closed plan review self-contained inside `resistance-engine/`, while still
forcing the user-facing design to cite or block on real application safeguards
such as `PIIStripper`, `MemoryFilter`, webhook signature verification, timeout
boundaries, token-budget ceilings, and TTL-backed storage policies.

Without this pivot, the resistance engine still requires project-specific setup
outside its own catalog, which makes the authoring skills harder to reuse, harder to
import coherently, and still too dependent on local repository scaffolding.

It also leaves the wording too close to the default LLM failure mode this shard is
trying to reverse: eager agreement, optimistic interpretation, and premature motion
toward code. The rewritten pair must do the opposite. These skills exist to prove
why the work is not yet safe to execute, challenge the human's premise, map the
blast radius, and de-risk the objective before implementation begins.

---

## Goals

- Rewrite `brainstorming` and `writing-plans` as self-sufficient default skills
  inside `resistance-engine/`
- Absorb the default `SPEC_DESIGN` behavior into
  `resistance-engine/skills/brainstorming/SKILL.md`
- Absorb the default `PLAN_WRITING` behavior into
  `resistance-engine/skills/writing-plans/SKILL.md`
- Ship default spec-review assets beside `brainstorming` so the skill works without
  repo-root manifests or rubrics
- Keep the "Paranoia-as-a-Service" behavior shift as the core posture of the pair
- Make the pair explicitly hostile to eager "Yes-Men" behavior that accepts the
  user's premise too quickly and rushes toward code
- Preserve BDD-style `Given / When / Then` acceptance criteria in specs and preserve
  those contracts during plan translation
- Allow minimal optional repo-root overlays for `brainstorming` and `writing-plans`
  that can extend or tighten local behavior
- Fail closed if an overlay is malformed, contradictory, or attempts to weaken a
  mandatory default

## Non-goals

- No rewrite of `writing-skills` content in this shard
- No generalized overlay engine or generic project-rule-ingestion framework in this
  shard
- No requirement that repo-root `SPEC_DESIGN.md`, `PLAN_WRITING.md`,
  `SPEC_REVIEW_MANIFEST.md`, or `SPEC_RUBRIC.md` exist
- No broad new shared `authoring/` framework unless one tiny shared artifact proves
  unavoidable
- No Copilot adapter, Claude compatibility, or broader skill-catalog policy work
- No implementation outside the resistance-engine skill workspace and its directly
  related docs/tests

---

## Approach

This shard rewrites the authoring pair around a portable-by-default model.

The core premise is not "help the user write code faster." It is
"Paranoia-as-a-Service": force the model to challenge assumptions, interrogate the
request, identify structural holes, and prove survival before implementation is
allowed to move forward.

### 1. Default authority lives with the skills

- `brainstorming/SKILL.md` becomes the default spec-design rulebook
- `writing-plans/SKILL.md` becomes the default plan-writing rulebook
- `brainstorming/SPEC_REVIEW_MANIFEST.md` becomes the default spec-review procedure
- `brainstorming/SPEC_RUBRIC.md` becomes the default spec-review grading contract

Those defaults should be strong enough that, even with no overlays, the pair already
behaves like an adversarial partner instead of a helpful accelerator.

### 2. Repo-root files become optional overlays only

If the local repository provides:

- `SPEC_DESIGN.md`
- `PLAN_WRITING.md`
- `SPEC_REVIEW_MANIFEST.md`
- `SPEC_RUBRIC.md`

the rewritten skills may load them as local overlays. But those files are no longer
required for the default workflow to function.

### 3. Overlay scope is intentionally minimal

This shard should define only the minimum overlay behavior needed by the authoring
pair:

- load default skill-local behavior first
- detect whether a matching repo-root overlay exists
- merge only additive or tightening rules
- stop with an explicit blocker if an overlay is malformed or weakens a default

The shard must not design a generic overlay engine for the rest of the catalog.
Generalized rule ingestion is explicitly deferred.

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `resistance-engine/skills/brainstorming/SKILL.md` | Modify | Absorb default `SPEC_DESIGN` behavior, repo-native adversarial brainstorming flow, and optional overlay hook semantics |
| `resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md` | Create | Default spec self-review procedure shipped with the skill |
| `resistance-engine/skills/brainstorming/SPEC_RUBRIC.md` | Create | Default binary grading rubric shipped with the skill |
| `resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md` | Modify | Make reviewer dispatch use skill-local defaults first, with optional repo-root overlays |
| `resistance-engine/skills/writing-plans/SKILL.md` | Modify | Absorb default `PLAN_WRITING` behavior, paranoid planner posture, and optional overlay hook semantics |
| `resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md` | Modify | Make reviewer dispatch use the self-contained plan workflow and verified repo inputs |
| `resistance-engine/README.md` | Modify | Document self-sufficient defaults, companion review assets, and minimal optional overlay behavior |
| `docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md` | Modify | Capture this architecture pivot and acceptance contract |

If implementation discovers one tiny shared artifact is unavoidable, it must be
limited to cross-skill review outcome vocabulary or `.review_log.jsonl` contract
language. Any broader shared framework belongs to a later shard.

---

## Detailed design

### 1. `brainstorming` owns its default rulebook

The rewritten `brainstorming` skill should absorb the default `SPEC_DESIGN` behavior
directly into `resistance-engine/skills/brainstorming/SKILL.md`.

That means the default skill text, without any repo-root overlay, must already cover:

- assume the human's initial request may be flawed, incomplete, or naive
- interrogate the request rather than accepting its framing
- map blast radius before design confidence increases
- adversarial brainstorming posture
- shard evaluation and bead/work-item synchronization
- empirical verification before review
- BDD acceptance criteria as a required output shape
- spec self-review sequencing
- spec audit prerequisites before planning

The skill should no longer require a repo-root `SPEC_DESIGN.md` just to perform its
default workflow.

### 2. `brainstorming` ships default review assets beside itself

The rewritten skill should also own the default spec-review assets that were
previously treated as root-level requirements:

- `resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md`
- `resistance-engine/skills/brainstorming/SPEC_RUBRIC.md`

These files should be the shipped defaults used when no repo-root overlays exist.

Their role split remains explicit:

- **manifest:** review procedure, persona, gate sequencing
- **rubric:** binary pass/fail grading contract

This preserves clarity while removing required setup outside the skill folder.

### 3. `writing-plans` owns its default rulebook

The rewritten `writing-plans` skill should absorb the default `PLAN_WRITING`
behavior directly into `resistance-engine/skills/writing-plans/SKILL.md`.

Without any repo-root overlay, it must already cover:

- spec ingestion before planning
- topological sequencing and TDD structure
- risk/confidence assessment
- unhappy-path-first planning
- repo verification before plan completion
- plan self-review and audit prerequisites

The skill should no longer require a repo-root `PLAN_WRITING.md` just to perform its
default workflow.

### 4. Paranoia-as-a-Service remains the behavioral center

This architecture pivot does not relax the behavior shift. The rewritten pair should
still make skepticism the default reasoning mode.

#### 4.1 `brainstorming`

Its default posture remains an adversarial systems architect.

The live interaction and written spec must include `### Threat Model (CIA)`.

This section should operate as a **CIA Stress-Test Mandate (Burden of Proof)**, not a
quota-driven bug hunt. The skill must not use quota-style hole-counting language,
because that rewards hallucinated flaws instead of disciplined scrutiny.

The default `brainstorming` behavior must explicitly evaluate the proposal against
the following vectors:

- **Confidentiality (Data Exposure & Access)**
  - **Unauthorized Access:** how could a user bypass authorization, for example by an
    IDOR-style mistake, to access another family member's data?
  - **Data Leakage:** will this feature expose PII in logs, error messages, or
    downstream dependencies such as the LLM context window?
- **Integrity (State & Logic Tampering)**
  - **State Corruption:** if two conflicting requests hit the feature simultaneously,
    what prevents corruption, such as race conditions or missing transaction
    boundaries?
  - **Input Exploitation:** how does the system handle maliciously crafted inputs,
    edge-case data types, prompt injection, or payload tampering intended to bypass
    business logic?
- **Availability (Resilience & Resource Management)**
  - **Resource Exhaustion:** how could the feature be abused to drain system
    resources, hit Cosmos DB rate limits, or max out the daily LLM token quota?
  - **Cascading Failures:** if an external dependency such as AWS Bedrock or a
    webhook hangs or fails, does the failure isolate cleanly or bring down the wider
    app workflow?

For each CIA pillar, the skill must do exactly one of the following:

1. name the concrete architectural mechanism that defeats the threat
2. emit a blocking constraint because the mechanism is missing

It is not allowed to say only "it is secure" or "looks fine." It must identify the
actual mechanism, for example `MemoryFilter`, Cosmos DB partition keys, or
`asyncio.wait_for`, or else block the design.

The rewritten skill should also force **assumption hunting**:

- surface the human's implicit assumptions
- challenge those assumptions against the CIA vectors above
- write the constraints that would break unsafe assumptions before execution begins

More broadly, the default wording should make clear that `brainstorming` is not there
to validate the requester's optimism. It is there to interrogate the request, attack
its weak points, and prove the design deserves to proceed at all.

#### 4.2 `writing-plans`

Its default posture remains a suspicious SRE.

The live interaction and written plan must begin with
`### Risk & Confidence Assessment`, including:

- a confidence percentage
- unknown variables when confidence is below 95%
- explicit unhappy-path planning expectations

The default wording should also explicitly state that a specification is only a
theory. The planner's job is to turn that theory into a battle-tested blueprint that
assumes hostile reality: unreliable networks, partial failures, unexpected inputs,
and operational chaos.

Every plan step should therefore be written from the standpoint that the happy path
is not enough. The step must state how the work behaves when the operation fails, not
just when it succeeds.

### 5. BDD acceptance criteria remain mandatory

The rewritten `brainstorming` default must require written specs to express
acceptance criteria in explicit BDD form:

- `Given`
- `When`
- `Then`

The rewritten `writing-plans` default must treat those BDD acceptance criteria as
authoritative behavior contracts when deriving RED tests and execution tasks.

### 6. Minimal overlay behavior

This shard should define a narrow overlay resolution rule for the authoring pair
only.

#### 6.1 Load order

For `brainstorming`:

1. load `resistance-engine/skills/brainstorming/SKILL.md`
2. load skill-local default review assets
3. if present, load repo-root overlays such as `SPEC_DESIGN.md`,
   `SPEC_REVIEW_MANIFEST.md`, and `SPEC_RUBRIC.md`

For `writing-plans`:

1. load `resistance-engine/skills/writing-plans/SKILL.md`
2. if present, load repo-root overlay `PLAN_WRITING.md`

#### 6.2 Allowed overlay behavior

An overlay may:

- append local commands or repo-specific examples
- tighten checks
- add extra required review inputs
- add local architecture or workflow rules

An overlay may not:

- weaken mandatory default gates
- remove required BDD acceptance criteria
- remove required CIA threat modeling
- remove required risk/confidence assessment
- convert a fail-closed gate into advisory guidance

#### 6.3 Failure behavior

If an overlay is:

- malformed
- contradictory
- missing a required companion while claiming to override it
- clearly weaker than the shipped default

the workflow must stop with an explicit blocker rather than attempting a best-effort
merge.

### 7. Audit gate prerequisites

The rewritten `brainstorming` default must absorb the audit gate that is still
spelled out in repo-root `SPEC_DESIGN.md`, rather than relying on that overlay
to supply it:

1. **Post-fix consistency check:** the spec self-review loop must be complete and
   every affected section re-checked before the cross-model audit is dispatched.
2. **Opposite-family cross-model audit:** the auditing model must come from the
   opposite model family to the author that drafted the spec.
3. **`.review_log.jsonl` recording:** every review outcome must append the exact
   status and raw reason text to `.review_log.jsonl` at the repository root.
4. **`[SPEC-REJECTED]` blocks plan writing:** a rejected spec must return to the
   relevant earlier phase, apply fixes, and re-enter the self-review loop before
   any implementation plan is written.

Repository evidence for this gate already exists today:

- `SPEC_DESIGN.md:183-188` defines `[SPEC-APPROVED]`, `[SPEC-REJECTED]`, and the
  `.review_log.jsonl` execution directive.
- `resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md:49-55`
  requires the post-fix consistency check, opposite-family audit,
  `.review_log.jsonl` recording, and the rule that rejected specs may not
  proceed to planning.
- `resistance-engine/skills/brainstorming/SKILL.md:250-289` logs rejections,
  requires cross-model audit, and blocks plan writing until `[SPEC-APPROVED]`.

If the rewritten defaults cannot enforce any of these gates without a repo-root
overlay, the shard must emit an explicit blocker instead of pretending the audit
contract is still intact.

### 8. Prompt templates align with self-contained defaults

The reviewer prompt templates must be rewritten around this new authority model.

#### 8.1 `brainstorming/spec-document-reviewer-prompt.md`

The template should reflect:

- work-item/bead context
- spec path
- verification evidence
- use of the skill-local manifest and rubric by default
- optional repo-root overlays if present
- deterministic review outcomes that are compatible with the skill's fail-closed
  behavior

#### 8.2 `writing-plans/plan-document-reviewer-prompt.md`

The template should reflect:

- work-item/bead context
- final approved spec
- final plan
- verification evidence for repo paths and commands
- deterministic review outcomes for plan completeness and drift

### 9. README documents the new portability model

`resistance-engine/README.md` should explain:

- that `brainstorming` and `writing-plans` are self-sufficient by default
- that `brainstorming` ships its own default review assets
- that repo-root files are optional overlays only
- that overlays are additive/tightening only and fail closed when invalid
- that generalized overlay/project-rule-ingestion behavior is intentionally deferred

---

## Required RED tests

Implementation must begin with failing verification of the new default-authority
model before rewriting the skill text.

Required failing scenarios:

1. `brainstorming` still requires repo-root `SPEC_DESIGN.md` to perform its default
   workflow
2. `writing-plans` still requires repo-root `PLAN_WRITING.md` to perform its default
   workflow
3. `brainstorming` lacks shipped default review assets under its own skill directory
4. `brainstorming` default flow produces no `### Threat Model (CIA)` without a
   repo-root overlay
5. `writing-plans` default flow produces no `### Risk & Confidence Assessment`
   without a repo-root overlay
6. `brainstorming` uses quota-style threat-hunting language instead of the
   evidence-based CIA burden-of-proof model
7. `brainstorming` does not evaluate unauthorized access, data leakage, state
   corruption, input exploitation, resource exhaustion, and cascading failure as
   explicit threat vectors
8. `brainstorming` allows a `### Threat Model (CIA)` section to pass without naming
   a concrete defensive mechanism or a blocking constraint for a pillar
9. `brainstorming` produces non-BDD acceptance bullets instead of explicit
   `Given / When / Then` criteria
10. `writing-plans` weakens approved BDD acceptance criteria into generic success
   language
11. a repo-root overlay can weaken a mandatory default instead of causing a blocking
   failure
12. malformed overlay content is silently ignored or loosely merged instead of causing
   an explicit blocker
13. implementation drifts into a generalized overlay framework rather than the
    minimal per-skill hook model
14. `brainstorming` wording still behaves like an eager assistant that accepts the
    human's framing instead of interrogating it
15. `writing-plans` wording still behaves like a formatting helper instead of a
    paranoid engineer stress-testing the plan against hostile reality

Refactor safety:

- use the `writing-skills` skill when editing `SKILL.md` files
- keep companion review assets beside `brainstorming`
- do not create a broad shared authoring framework as a shortcut

---

## BDD acceptance criteria

### Self-sufficient defaults

1. **Given** a user loads `resistance-engine/skills/brainstorming/` in a repository
   with no repo-root `SPEC_DESIGN.md`  
   **When** the skill runs its default brainstorming flow  
   **Then** it still performs the full default spec-design workflow from
   `brainstorming/SKILL.md` alone.

2. **Given** a user loads `resistance-engine/skills/writing-plans/` in a repository
   with no repo-root `PLAN_WRITING.md`  
   **When** the skill runs its default planning flow  
   **Then** it still performs the full default plan-writing workflow from
   `writing-plans/SKILL.md` alone.

3. **Given** a user loads `resistance-engine/skills/brainstorming/` in a repository
   with no repo-root review files  
   **When** the skill reaches spec self-review  
   **Then** it uses `brainstorming/SPEC_REVIEW_MANIFEST.md` and
   `brainstorming/SPEC_RUBRIC.md` as shipped defaults.

### Brainstorming behavior

4. **Given** the rewritten `brainstorming` skill runs without overlays  
   **When** it presents a design or writes a spec  
   **Then** the live interaction and written spec include `### Threat Model (CIA)`.

5. **Given** a CIA pillar is evaluated in the default brainstorming flow  
    **When** the proposal survives that threat  
    **Then** the output names the concrete architectural mechanism that defeats it.

6. **Given** a CIA pillar is evaluated in the default brainstorming flow  
    **When** the necessary defensive mechanism is missing  
    **Then** the skill emits a blocking constraint instead of papering over the gap.

7. **Given** the rewritten `brainstorming` skill evaluates a proposal  
   **When** it produces `### Threat Model (CIA)`  
   **Then** it explicitly covers unauthorized access, data leakage, state corruption,
   input exploitation, resource exhaustion, and cascading failure rather than using
   generic CIA headings with no concrete stress-test vectors.

8. **Given** the rewritten `brainstorming` skill writes acceptance criteria  
   **When** those criteria are inspected  
   **Then** they are expressed in explicit `Given / When / Then` form.

9. **Given** the rewritten `brainstorming` skill receives an optimistic or incomplete
   request  
   **When** it begins the default workflow  
   **Then** it interrogates the request, surfaces assumptions, and maps blast radius
   instead of treating the user's framing as already trustworthy.

### Writing-plans behavior

10. **Given** the rewritten `writing-plans` skill runs without overlays  
   **When** planning begins  
   **Then** the live interaction and written plan begin with
   `### Risk & Confidence Assessment`.

11. **Given** the default plan workflow states confidence below 95%  
    **When** the planner explains the risk posture  
    **Then** it names the unknown variables reducing confidence before task
    decomposition begins.

12. **Given** the approved spec contains BDD acceptance criteria  
    **When** the planner derives RED tests and execution steps  
    **Then** it preserves those `Given / When / Then` contracts instead of replacing
    them with looser success language.

13. **Given** a planned task touches risky state or external systems  
    **When** the task is written  
    **Then** the unhappy path is explicit rather than implied by hand-wavy language.

14. **Given** the rewritten `writing-plans` skill translates an approved spec into a
    plan  
    **When** it writes tasks  
    **Then** it treats the spec as a theory under hostile conditions and makes the
    unhappy path explicit for each risky operation rather than documenting only the
    success path.

### Overlay behavior

15. **Given** no repo-root overlay files exist  
    **When** the authoring pair runs  
    **Then** the default skill-local behavior remains authoritative.

16. **Given** a repo-root overlay exists for `brainstorming` or `writing-plans`  
    **When** the overlay adds stricter local requirements  
    **Then** the overlay extends or tightens the workflow without replacing the
    shipped defaults.

17. **Given** a repo-root overlay attempts to weaken a mandatory default gate  
    **When** the skill evaluates the overlay  
    **Then** the workflow stops with an explicit blocker instead of applying the
    weaker rule.

18. **Given** a repo-root overlay is malformed or contradictory  
     **When** the skill evaluates it  
     **Then** the workflow fails closed rather than performing a best-effort merge.

19. **Given** the rewritten `brainstorming` skill evaluates a CIA pillar  
    **When** it reasons about threats  
    **Then** it names the concrete mechanism or emits a blocking constraint
    instead of using quota-style hole-counting or accepting "looks secure" as a
    finding.

### Audit gate behavior

20. **Given** the rewritten `brainstorming` default finishes spec self-review  
    **When** it prepares the cross-model audit  
    **Then** it has completed the post-fix consistency check and re-validated
    every affected section before dispatching the auditor.

21. **Given** the cross-model audit returns `[SPEC-REJECTED]`  
    **When** the skill receives that result  
    **Then** it records the exact status and raw reason in `.review_log.jsonl`
    and is strictly forbidden from writing an implementation plan until the spec
    is fixed and re-approved.

### Shard boundary

22. **Given** implementation pressure encourages a broader overlay framework  
    **When** the shard is executed  
    **Then** the implementation keeps only minimal per-skill overlay hooks and defers
    generalized project-rule ingestion to a later shard.

---

## Security & Risk Analysis

### Threat Model (CIA)

#### Confidentiality

The self-sufficient defaults will reason over local work-item descriptions, spec
text, plan text, and verification evidence. Those artifacts can contain sensitive
operational context.

Mitigations required by this spec:

- the rewritten CIA output must cite concrete confidentiality controls that
  already exist in the application, including `PIIStripper`
  (`assistant/classification/pii.py`), `MemoryFilter`
  (`assistant/memory/filter.py`), the logging scrubber in
  `assistant/logging.py`, and WhatsApp signature verification in
  `assistant/whatsapp/webhook.py`
- default review assets should require minimal, named review inputs rather than
  broad repository dumps
- overlays may add stricter local confidentiality rules, but may not weaken the
  shipped defaults
- **Blocker:** if a confidentiality threat cannot be tied to a concrete existing
  mechanism, the rewritten `brainstorming` skill must emit
  `[BLOCKER: confidentiality mechanism missing]` instead of claiming the pillar
  is satisfied

#### Integrity

The main integrity risk is contradictory authority: shipped defaults, overlays, and
prompt templates drifting apart or allowing weaker local rules to override stronger
defaults.

Mitigations required by this spec:

- the default authority must be explicit: skill-local first, overlays second
- overlays are additive/tightening only, and malformed or weakening overlays
  must fail closed
- the rewritten CIA output must cite concrete integrity mechanisms such as the
  hierarchical partition keys in `assistant/storage/memory_store.py` and the
  rule that blocking I/O is wrapped with `asyncio.to_thread()` rather than
  guessed at from memory
- `writing-plans` must treat approved BDD acceptance criteria as authoritative
- **Blocker:** if an integrity threat cannot be tied to a concrete existing
  mechanism or an explicit fail-closed rule, the rewritten `brainstorming`
  skill must emit `[BLOCKER: integrity mechanism missing]`

#### Availability

A bad overlay model could create fragile workflows that only work in specially
prepared repositories.

Mitigations required by this spec:

- the default path must succeed without repo-root setup
- generalized overlay architecture is deferred to avoid unbounded complexity
- the rewritten CIA output must cite concrete availability mechanisms such as
  `asyncio.wait_for()` timeout boundaries in `assistant/mcp/bridge.py`,
  emergency token-budget handling in `assistant/llm_router.py`, and `_ttl`
  expiry behavior in `assistant/storage/memory_store.py`
- unhappy-path planning remains mandatory in the default `writing-plans`
  behavior
- **Blocker:** if an availability threat cannot be tied to a concrete existing
  mechanism or explicit resource-control rule, the rewritten `brainstorming`
  skill must emit `[BLOCKER: availability mechanism missing]`

#### Agentic and architectural vulnerabilities

The largest architectural risk is drifting back into a split-brain model where the
real rules live at repo root and the skill package becomes a thin wrapper again.

Mitigations required by this spec:

- absorb the default `SPEC_DESIGN` and `PLAN_WRITING` behaviors into the `SKILL.md`
  files
- ship default review assets beside `brainstorming`
- document repo-root files as optional overlays only
- keep this shard narrowly focused on the authoring pair
- preserve the audit contract that requires opposite-family review,
  `.review_log.jsonl` recording, and `[SPEC-APPROVED]` before plan writing
- **Blocker:** if the rewrite cannot preserve those audit gates without a
  repo-root overlay, stop and reject the shard rather than silently weakening
  the authoring workflow

#### Supply chain

This shard should not add third-party dependencies. It is a markdown/process rewrite
only.

---

## Future beads

| Bead | Priority | Effort | Why it follows from this shard |
| --- | --- | --- | --- |
| Authoring follow-on rewrite for `writing-skills` | 1 | M | Align skill-authoring defaults with the same self-sufficient, adversarial packaging model |
| Project-rule ingestion / generalized overlay architecture | 1 | M | Extend the minimal per-skill overlay hooks into a broader catalog-wide model after this shard proves the portable-default approach |
| Shared review vocabulary normalization across later workflow skills | 2 | S | Only worth extracting if multiple later shards duplicate the same gate language |
| Optional migration/compatibility wrappers for legacy repo-root rulebooks | 3 | S | Convenience follow-on once the self-sufficient defaults are stable |

---

## Open implementation constraints already decided

- `brainstorming/SKILL.md` absorbs the default `SPEC_DESIGN` behavior
- `writing-plans/SKILL.md` absorbs the default `PLAN_WRITING` behavior
- `brainstorming/SPEC_REVIEW_MANIFEST.md` and `brainstorming/SPEC_RUBRIC.md` ship as
  default companion assets
- repo-root files are optional overlays only
- overlays may extend or tighten defaults, but may not weaken them
- generalized overlay architecture is intentionally out of scope for this shard

---

## Summary

This shard is no longer about making the authoring pair depend on better local
rulebooks. It is about making the authoring pair portable and self-sufficient by
default, while still allowing repositories like this one to add stricter local rules
through minimal fail-closed overlays.
