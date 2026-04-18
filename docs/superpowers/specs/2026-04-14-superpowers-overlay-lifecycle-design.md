## Superpowers overlay lifecycle rewrite

**Date:** 2026-04-14
**Status:** Approved design, ready for sharded implementation planning

---

## Problem

This repo currently has two overlapping systems for agent behavior:

1. the upstream Superpowers skill/process model
2. a local project process spread across `AGENTS.md`, `SPEC_DESIGN.md`,
   `PLAN_WRITING.md`, `SPEC_REVIEW_MANIFEST.md`, and related files

The result is useful but structurally messy:

- generic lifecycle rules and repo-specific rules are interleaved
- Copilot CLI and Claude Code concerns are not cleanly separated
- some hardening behavior exists as local prose rather than explicit lifecycle gates
- project-only constraints risk leaking into generic skill behavior
- there is no standard hook contract for "every project probably needs a block like this"

This rewrite defines a hardened, Copilot-first Superpowers architecture that preserves
specialized skills, introduces a lifecycle controller, and moves project-specific
content into an explicit overlay layer. The upstream `obra/superpowers` repository is
checked out as a read-only reference submodule at `vendor/obra-superpowers`.

---

## Goals

- Define a **generic core lifecycle** with explicit named states and gate semantics
- Keep existing specialized skills discrete rather than collapsing them into a few
  mega-skills
- Make **Copilot CLI** the reference harness, with a documented **Claude Code**
  compatibility adapter
- Define a **project overlay contract** so project-specific rules remain in
  `AGENTS.md` and companion docs rather than being baked into generic skills
- Introduce **named hook points** that skills can call when a project provides local
  rules
- Require a **human-confirmed classification pass** for each local process block before
  it remains project-local
- Require **BDD-style acceptance criteria** for the rewrite and a **spec adversarial
  audit** before plan writing
- Produce a roadmap that is explicitly **sharded** into independently reviewable
  implementation slices

## Non-goals

- No attempt to upstream this full local rewrite into `obra/superpowers` as-is
- No rewriting of upstream skills directly inside `vendor/obra-superpowers`
- No fake platform parity where Copilot CLI and Claude Code differ in real mechanics
- No folding all workflow behaviors into six numbered phases or a handful of merged
  skills
- No silent retention of project-local rules in `AGENTS.md`
- No new third-party runtime dependencies for the lifecycle framework without a
  separate justification

---

## Approach

Rewrite the process as a **three-layer system**:

1. **Core lifecycle layer**: generic named lifecycle states, gate semantics, and
   shared vocabulary
2. **Platform adapter layer**: Copilot-first behavior plus a Claude compatibility
   adapter with explicit downgrade rules
3. **Project overlay layer**: `AGENTS.md` plus companion docs that provide local
   commands, architecture, security, and workflow rules through named hooks

The rewrite introduces a **lifecycle controller**, not a skill merger. Skills remain
modular. The controller defines which skills own which lifecycle states and when hooks
must be resolved.

Every candidate rule block from local process docs must go through a classification
worksheet:

- `core-generic`
- `platform-adapter`
- `project-overlay`

If a block might be project-specific, the agent must ask the human before leaving it in
`AGENTS.md` or a companion overlay doc.

---

## Files and surfaces expected to change

| File / Surface | Action | Responsibility |
| --- | --- | --- |
| `.gitmodules` | Modify | Track upstream `obra/superpowers` reference submodule |
| `vendor/obra-superpowers/` | Add reference only | Read-only upstream reference; not edited directly by this rewrite |
| `AGENTS.md` | Modify | Reduce to project index, local high-signal guidance, and overlay entrypoints |
| `SPEC_DESIGN.md` | Modify | Align spec workflow rules with the new hook/controller model where appropriate |
| `PLAN_WRITING.md` | Modify | Align planning rules with named lifecycle states and adapter-aware execution |
| `SPEC_REVIEW_MANIFEST.md` | Modify | Align spec self-review expectations with BDD criteria and adversarial spec checks |
| `docs/superpowers/specs/` | Modify | Store umbrella spec plus shard specs |
| `docs/superpowers/plans/` | Modify | Store plans derived from approved shard specs |
| `docs/superpowers/project/` | Create | Companion overlay docs for project-specific rules referenced by `AGENTS.md` |
| `superpowers-local/` | Create | Hold the local forked/reworked skill framework and adapters outside the upstream submodule |

The local rewritten framework root is `superpowers-local/`. It consumes
`vendor/obra-superpowers` as reference material and must not edit the submodule
in-place.

---

## Detailed design

### 1. Lifecycle states and skill map

The rewrite should use **named lifecycle states**, not hardcoded numbered phases:

- `session-intake`
- `brainstorming`
- `spec-audit`
- `plan-writing`
- `workspace-setup`
- `execution`
- `debugging`
- `review`
- `survivability`
- `retrospective`
- `finish`

These are orchestration states, not skills.

Skills remain separate and are mapped onto states. The initial target mapping is:

| Lifecycle state | Primary skill(s) |
| --- | --- |
| `session-intake` | `using-resistance-engine` |
| `brainstorming` | `brainstorming` |
| `spec-audit` | controller-owned spec-audit routine using manifest/rubric-driven review prompts |
| `plan-writing` | `writing-plans` |
| `workspace-setup` | `using-git-worktrees` |
| `execution` | `executing-plans` or `subagent-driven-development` |
| `execution` discipline | `test-driven-development` |
| `debugging` | `systematic-debugging` |
| `review` | `requesting-code-review`, `receiving-code-review` |
| `survivability` | lifecycle gate owned by controller and project/platform rules |
| `finish` | `verification-before-completion`, `finishing-a-development-branch` |
| skill evolution | `writing-skills` |

The lifecycle controller owns:

- state transitions
- gate requirements
- hook resolution
- downgrade semantics
- failure escalation paths

It does **not** absorb the specialized skill content.

### 2. Core hardening model

The generic lifecycle must include first-class gates, with configurable strictness:

- approval gate
- review gate
- retrospective gate
- finish gate
- survivability gate where applicable

The core framework defines that these gates exist. Platform adapters and project
overlays define how strict they are and how they execute in practice.

Examples:

- Copilot CLI may support stronger subagent orchestration and explicit ask-user flows
- Claude Code may require an adapter-defined downgrade for cross-model audit behavior
- a project overlay may require push-to-remote before work is considered finished

The system must prefer **truthful downgrade behavior** over fake equivalence.

### 3. Spec rigor gate

Before a plan can be written, the approved spec must pass a dedicated **spec adversarial
audit**.

This is analogous to mutation testing, but for design quality rather than source code.
The audit should challenge the spec with counterexamples such as:

- removing a required hook
- weakening a review gate
- silently classifying a local rule as generic
- assuming Copilot and Claude parity where none exists
- omitting the human confirmation step for project-local retention

The question is whether the spec's own acceptance criteria and invariants would reject
the mutated design.

### 4. BDD acceptance criteria

This rewrite spec and its implementation shards must define acceptance criteria in BDD
style:

- **Given** a request, lifecycle state, hook configuration, or platform limitation
- **When** the framework or skill executes
- **Then** the expected gate, handoff, or failure mode is observable

Negative criteria are mandatory for:

- unsupported or degraded platform features
- ambiguous generic-vs-project classification
- missing human confirmation
- unresolved project hooks
- failed audits or review gates

### 5. Platform adapter model

The rewrite is **Copilot CLI first**.

The Copilot adapter becomes the reference implementation for:

- skill invocation timing
- tool and prompt mapping
- ask-user flow
- review and subagent orchestration expectations
- session state / checkpoint behavior
- explicit verification semantics

The Claude Code adapter must define:

- equivalent behavior where possible
- downgraded behavior where necessary
- which guarantees remain intact
- which guarantees are reduced and how the user is told

The adapter contract must never imply that Claude can perform a gate identically if it
cannot.

### 6. Project overlay contract

Project-specific content remains local and is provided through an overlay pack:

- `AGENTS.md`
- companion docs under `docs/superpowers/project/`

The rewrite defines **generic block names** that projects may supply:

- `project-overview`
- `commands-and-testing`
- `architecture`
- `security-guardrails`
- `codebase-conventions`
- `issue-tracking`
- `environment-limitations`
- `branch-finish-rules`
- `retrospective-rules`

It also defines **phase hooks**:

- `brainstorming.preflight`
- `spec-audit.preflight`
- `plan-writing.preflight`
- `execution.preflight`
- `review.preflight`
- `finish.preflight`

And **decision hooks**:

- `resolve-test-command`
- `resolve-build-command`
- `resolve-sensitive-data-rules`
- `resolve-human-approval-rules`
- `resolve-issue-tracker-rules`

Skills and lifecycle states may call these hooks, but must not assume they always exist.
If a hook is absent, the controller or adapter must resolve that absence explicitly.

### 7. Human-confirmed classification workflow

Every existing rule block in:

- `AGENTS.md`
- `SPEC_DESIGN.md`
- `PLAN_WRITING.md`
- `SPEC_REVIEW_MANIFEST.md`
- directly related companion docs

must be inventoried and classified using a worksheet with these fields:

| Field | Purpose |
| --- | --- |
| Source section | Where the rule came from |
| Proposed class | `core-generic`, `platform-adapter`, or `project-overlay` |
| Why it might be generic | Reuse case across projects/harnesses |
| Why it might be project-specific | Repo/domain/tool-specific constraint |
| Human decision | Explicit keep/move ruling from the human |
| Destination | Final file / hook / adapter location |

Rule:

- if the answer is uncertain, the agent must ask the human
- no section remains in `AGENTS.md` by silent default
- human decisions must be visible in the migration artifact history

### 8. Sharded implementation roadmap

This umbrella spec intentionally stops short of a monolithic implementation plan.
Implementation must be split into sequential shards:

1. **Core lifecycle/controller shard**
2. **Overlay contract and classification shard**
3. **Copilot CLI adapter shard**
4. **Claude Code adapter shard**
5. **Skill rewrite shard(s)**
6. **Local project migration shard**
7. **Validation and regression shard**

Each shard must have its own spec and plan unless the resulting scope is small enough to
remain atomic after review.

---

## BDD acceptance criteria

### Core lifecycle

1. **Given** a request that matches a known workflow state  
   **When** the lifecycle controller determines the next action  
   **Then** it invokes the appropriate specialized skill rather than collapsing behavior
   into a merged mega-skill.

2. **Given** a lifecycle state with a required gate  
   **When** the controller reaches that state  
   **Then** the gate is evaluated explicitly and the outcome is visible rather than
   implied.

### Project overlay handling

3. **Given** a skill that needs project-local commands or security rules  
   **When** it resolves its hook dependencies  
   **Then** it reads them from the project overlay contract rather than embedding local
   content in generic skill text.

4. **Given** an existing rule block from `AGENTS.md` or a companion local doc  
   **When** the migration process classifies it  
   **Then** the block is not retained as project-local until the human has explicitly
   confirmed that decision.

5. **Given** a standard project block is absent  
   **When** a skill or adapter attempts to resolve it  
   **Then** the framework reports the absence explicitly and follows the documented
   fallback or stop rule.

### Platform adapters

6. **Given** a workflow that Copilot CLI can perform but Claude Code cannot match
   exactly  
   **When** the adapter contract is evaluated  
   **Then** the spec documents an explicit Claude downgrade path rather than claiming
   parity.

7. **Given** a platform-specific behavior belongs in an adapter rather than project
   overlay  
   **When** the classification pass reviews that behavior  
   **Then** it is moved into the platform adapter layer rather than left in
   `AGENTS.md`.

### Spec rigor

8. **Given** a spec mutation that removes a required hook, hides a downgrade, or skips
   human confirmation  
   **When** the spec adversarial audit runs  
   **Then** the mutation is rejected by the spec's own criteria.

9. **Given** acceptance criteria for a shard spec  
   **When** they are written  
   **Then** they use BDD structure and include at least one negative path relevant to
   platform limits, hook absence, or classification failure.

### Local migration

10. **Given** the current local process rules  
    **When** the migration shard executes  
    **Then** the resulting local overlay pack places project-specific rules in
    `AGENTS.md` plus companion docs, while generic and platform rules move out to the
    proper layer.

---

## Security & risk analysis

### 1. Confidentiality

Project overlays may contain commands, environment details, workflow constraints, or
security guardrails that should not be sprayed across generic skill content or logs.

Rules:

- overlay content must be consumed through bounded hooks
- security-sensitive project rules must remain local
- migration artifacts must avoid introducing secrets or copying sensitive material into
  generic framework files

### 2. Integrity

The highest integrity risk is **misclassification**:

- treating project-local rules as generic
- treating platform limitations as project rules
- pretending two harnesses are equivalent when they are not

Rules:

- require human confirmation for uncertain project-local retention
- require adapter-specific downgrade documentation
- require explicit gate semantics and BDD criteria

### 3. Availability

A lifecycle framework can become too heavy if every state performs unbounded checks or
multi-agent work.

Rules:

- keep gates explicit but configurable
- require adapters to document where expensive gates are mandatory vs optional
- shard implementation so the rewrite does not become an unreviewable monolith

### 4. Agentic and architectural vulnerabilities

Risks:

- hook explosion without stable naming
- merged mega-skills that hide responsibility boundaries
- local overlays that bypass lifecycle gates through prose only

Rules:

- use a fixed hook taxonomy
- keep skills discrete and state-owned
- require all local rules to enter through the overlay contract

### 5. Supply chain

The rewrite depends on an upstream reference repository but must not couple local
implementation to in-place edits of the submodule.

Rules:

- `vendor/obra-superpowers` is reference-only
- local rewritten framework lives outside the submodule
- no new dependency is introduced without explicit justification in shard specs

---

## Future beads

| Candidate shard / bead | Priority | Effort | Notes |
| --- | --- | --- | --- |
| Core lifecycle/controller spec | 1 | M | Defines named states, gates, and controller boundaries |
| Overlay contract + classification spec | 1 | M | Defines hook schema and human-confirmed migration worksheet |
| Copilot CLI adapter spec | 1 | M | Establishes reference harness behavior |
| Claude Code adapter spec | 2 | M | Documents compatibility and downgrade rules |
| Skill rewrite sequencing spec | 2 | L | Orders changes across existing skills without merging them |
| Local project migration spec | 1 | M | Moves current repo rules into overlay pack structure |
| Validation/regression spec | 2 | M | Covers BDD fixture set, adversarial spec checks, and hook validation |

---

## Open implementation constraints already decided

- Copilot CLI is the preferred reference harness
- Claude Code compatibility is required, but fake parity is forbidden
- Specialized skills must remain separate
- Numbered phases are descriptive only; named states are normative
- Project-local rules stay local only after explicit human confirmation
- Cross-model review may require platform-aware degradation

---

## Summary

This rewrite turns the current process from a powerful but interleaved instruction set
into a structured framework:

- lifecycle controller for orchestration
- specialized skills for behavior
- platform adapters for harness truthfulness
- project overlays for local reality

That gives this repo a hardened agentic lifecycle without contaminating generic
Superpowers behavior with repo-specific constraints.
