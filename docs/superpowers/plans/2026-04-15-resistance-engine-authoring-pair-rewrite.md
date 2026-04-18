# Resistance Engine Authoring Pair Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use resistance-engine:subagent-driven-development (recommended) or resistance-engine:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the `brainstorming` and `writing-plans` skills so they are self-sufficient by default inside `resistance-engine/`, ship their own review defaults, and enforce the adversarial “Paranoia-as-a-Service” workflow before implementation begins.

**Architecture:** Keep the rewrite skill-local by default: `brainstorming/SKILL.md` absorbs default spec-design behavior, `writing-plans/SKILL.md` absorbs default plan-writing behavior, and `brainstorming/` ships its own default review manifest and rubric. Allow repo-root overlays only as optional tightening layers, fail closed on malformed or weakening overlays, and avoid building any broad shared overlay framework in this shard.

**Tech Stack:** Markdown skill docs, prompt templates, `bd`, `git worktree`, `task`/subagent pressure tests, `.venv/bin/pytest`, existing resistance-engine docs

---

## Risk & Confidence Assessment

**Confidence:** 87%

**Complexity Risk:** Medium — two large `SKILL.md` rewrites plus companion prompt alignment create drift risk unless the work is chunked tightly.

**Environmental Risk:** Low — this shard is mostly markdown and prompt-template work, but interpretation drift is still possible if the fail-closed wording is too soft.

**Unknown Variables:**
- The rewritten `SKILL.md` files will grow substantially; the exact balance between self-contained defaults and token efficiency may need one refactor pass during implementation.
- The overlay model is documentation-driven rather than code-enforced, so the wording must be precise enough that future agents interpret “optional additive overlay” consistently.
- Pressure-test verification is scenario-based rather than pytest-based; if a baseline scenario does not fail in the expected way, the implementer must stop and refine the scenario before editing the skill.

**Hostile-world assumptions:**
- Agents will try to rush toward implementation unless the new wording blocks that path explicitly.
- Repo-root overlays may be malformed, contradictory, or weaker than the shipped defaults.
- Missing security boundaries, ownership rules, or failure behavior will tempt the model to guess unless the skill text forces a blocker or a specific follow-up question.
- Long markdown rewrites can drift out of sync with companion prompts and README docs unless changes are applied in bounded chunks.

**Spec:** `docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md`
**Bead:** `resistance-ai-a2a`
**Primary worktree:** create a fresh worktree before editing, for example `git worktree add .worktrees/resistance-engine-authoring-pair -b feat/resistance-engine-authoring-pair`
**Focused regression command:** `timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q`
**Full suite command:** `timeout 180 .venv/bin/pytest --override-ini="addopts=" -q`

---

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `resistance-engine/skills/brainstorming/SKILL.md` | **Modify** | Absorb default `SPEC_DESIGN` behavior, adversarial brainstorming posture, CIA burden-of-proof model, BDD acceptance criteria, and minimal overlay semantics |
| `resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md` | **Create** | Ship the default spec self-review procedure beside the skill |
| `resistance-engine/skills/brainstorming/SPEC_RUBRIC.md` | **Create** | Ship the default binary review rubric beside the skill |
| `resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md` | **Modify** | Point reviewer dispatch at skill-local defaults first, with optional repo-root overlays |
| `resistance-engine/skills/writing-plans/SKILL.md` | **Modify** | Absorb default `PLAN_WRITING` behavior, paranoid engineer posture, confidence matrix, unhappy-path planning, and minimal overlay semantics |
| `resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md` | **Modify** | Align the plan reviewer prompt with the new self-contained defaults and hostile-world planning contract |
| `resistance-engine/README.md` | **Modify** | Document self-sufficient defaults, skill-local review assets, and additive-only overlays |

---

### Task 0: Verify the inherited rulebook contracts before editing

**Files:**
- Modify: none
- Read: `SPEC_DESIGN.md`
- Read: `PLAN_WRITING.md`
- Read: `SPEC_REVIEW_MANIFEST.md`
- Read: `SPEC_RUBRIC.md`
- Read: `resistance-engine/skills/brainstorming/SKILL.md`
- Read: `resistance-engine/skills/writing-plans/SKILL.md`

- [ ] **Step 1: Run the source-of-truth sync gate before touching the skill files**

Run:

```bash
bd show resistance-ai-a2a --json
bd show resistance-ai-a2a --json | jq -e '.[0].description != null and .[0].description != ""'
```

Expected:
- the bead exists
- the bead description is non-empty, so the rewrite is grounded in a real source of
  truth before any edits begin

**Unhappy path:** If `bd show` fails or the description check returns non-zero, stop.
Do not edit any files until the bead state is repaired.

- [ ] **Step 2: Resolve the opposite-family reviewer model and record it**

Run:

```bash
: "${COPILOT_ORCHESTRATOR_MODEL:?Set COPILOT_ORCHESTRATOR_MODEL to the current session model id before continuing}"

case "$COPILOT_ORCHESTRATOR_MODEL" in
  claude-*) REVIEW_MODEL="gpt-5.4" ;;
  gpt-*) REVIEW_MODEL="claude-sonnet-4.6" ;;
  *) echo "ERROR: Unsupported orchestrator model: $COPILOT_ORCHESTRATOR_MODEL"; exit 1 ;;
esac

export REVIEW_MODEL

jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg bid "resistance-ai-a2a" \
  --arg sk "writing-plans" \
  --arg ph "MODEL_PREFLIGHT" \
  --arg st "RESOLVED_REVIEWER_MODEL" \
  --arg rs "orchestrator=$COPILOT_ORCHESTRATOR_MODEL reviewer=$REVIEW_MODEL" \
  --arg orch "$COPILOT_ORCHESTRATOR_MODEL" \
  --arg aud "$REVIEW_MODEL" \
  '{timestamp: $ts, bead_id: $bid, skill: $sk, phase: $ph, status: $st, reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```

Expected:
- `REVIEW_MODEL` is resolved to the opposite model family
- the orchestrator and reviewer model ids are recorded before any adversarial `task`
  invocation occurs

**Unhappy path:** If the orchestrator model family cannot be resolved, stop. Do not
launch any reviewer or pressure-test task until this preflight gate passes.

- [ ] **Step 3: Run shell verification before touching the skill files**

Run:

```bash
ls resistance-engine/skills/brainstorming resistance-engine/skills/writing-plans
rg -n "Threat Model \\(CIA\\)|Risk & Confidence Assessment|Tabula Rasa|Topological|Chunking Rule|Unified Coherence|append-only|sub-beads|SPEC-APPROVED|SPEC-REJECTED" SPEC_DESIGN.md PLAN_WRITING.md SPEC_REVIEW_MANIFEST.md SPEC_RUBRIC.md resistance-engine/skills/brainstorming/SKILL.md resistance-engine/skills/writing-plans/SKILL.md
ls docs/superpowers/specs && cat docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md
cat pyproject.toml
ls tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py
```

Expected:
- both skill directories exist
- the full approved spec is physically ingested before any execution steps are
  outlined, satisfying the Tabula Rasa gate
- the approved spec confirms that `brainstorming` must preserve shard evaluation,
  bead synchronization, empirical verification, BDD output shape, self-review, and
  audit prerequisites
- the current skill files show that some of those hardening laws still live only in
  the repo-root rulebooks, proving the rewrite must transplant them explicitly
- the pytest configuration and the specific regression test paths are verified in the
  repository before those commands appear later in the plan

**Unhappy path:** If any path or file name differs from the plan, stop and fix the
plan before editing anything else.

- [ ] **Step 4: Run a RED baseline pressure scenario for `brainstorming` and capture rationalizations verbatim**

Use the `writing-skills` skill, then run this exact `task` prompt:

```text
description: "Brainstorming RED baseline"
agent_type: general-purpose
model: $REVIEW_MODEL
prompt: |
  IMPORTANT: This is a real scenario. Choose and act.

  The product lead promised delivery today.
  A teammate says the feature is "obviously simple".
  The request touches family data and LLM summaries, but no auth model, validation
  rules, or failure boundaries are defined yet.

  User request:
  "Add a feature that lets any family member search all stored facts and cross-link
  them with Bedrock summaries. Keep it simple and start coding as soon as possible."

  You have access only to the current resistance-engine brainstorming skill.

  Show your first response and first design section. Do not summarize. Act.
```

Expected: FAIL. The baseline should still rationalize toward implementation, skip some
source-of-truth or empirical verification law, or fail to force the full CIA
burden-of-proof workflow.

**Unhappy path:** If the baseline complies perfectly, document the exact evidence and
narrow the rewrite to the remaining missing rulebook sections instead of editing by
rote.

- [ ] **Step 5: Run a RED baseline pressure scenario for `writing-plans` and capture rationalizations verbatim**

Use the `writing-skills` skill, then run this exact `task` prompt:

```text
description: "Writing-plans RED baseline"
agent_type: general-purpose
model: $REVIEW_MODEL
prompt: |
  IMPORTANT: This is a real scenario. Choose and act.

  The approved spec depends on an external API, a webhook, a settings change, and a
  manual infrastructure step.
  The engineering manager wants the plan in 10 minutes.
  Another reviewer says "don't overcomplicate it with failure cases."

  You have access only to the current resistance-engine writing-plans skill.

  Show the start of your implementation plan.
```

Expected: FAIL. The baseline should drop one or more of Tabula Rasa ingestion,
topological ordering, strict RED/GREEN/REFACTOR, chunking, runbook instructions, or
the Unified Coherence Check.

**Unhappy path:** If the baseline complies perfectly, capture the evidence and reduce
the rewrite scope rather than duplicating rules that are already present.

- [ ] **Step 6: Record the RED failures as a blocking artifact before editing**

Run:

```bash
jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg bid "resistance-ai-a2a" \
  --arg sk "writing-skills" \
  --arg ph "RED_BASELINE" \
  --arg st "RED_EVIDENCE_RECORDED" \
  --arg rs "Captured verbatim rationalizations for brainstorming and writing-plans baseline scenarios before GREEN work begins." \
  --arg orch "$COPILOT_ORCHESTRATOR_MODEL" \
  --arg aud "$REVIEW_MODEL" \
  '{timestamp: $ts, bead_id: $bid, skill: $sk, phase: $ph, status: $st, reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```

Also append the exact rationalization text from each baseline scenario to
`.review_log.jsonl` without paraphrasing it. Do not rely on working notes or session
memory alone. The rewrite must counter the actual failure language the agents used.

**Unhappy path:** If you do not have verbatim rationalizations, re-run the baseline
scenarios. Do not begin GREEN without real RED evidence.

- [ ] **Step 7: Verify the RED evidence gate before unlocking GREEN**

Run:

```bash
rg -n '"status":"RED_EVIDENCE_RECORDED"' .review_log.jsonl
```

Expected: at least one matching entry exists before Task 1 begins.

**Unhappy path:** If no RED evidence entry is found, do not start Task 1. Re-run Step
6 until the checkpoint exists.

### Task 0A: Write the RED regression tests before rewriting the shipped defaults

**Files:**
- Modify: `tests/scripts/test_import_superpowers_catalog.py`
- Modify: `tests/scripts/test_validate_resistance_engine_provenance.py`

- [ ] **Step 1: Add failing assertions that codify the new authoring-default contracts**

Extend the existing focused regression suite so it fails until the rewritten
authoring-pair assets actually land. The RED assertions must verify repository-visible
content, not paraphrased intent. At minimum, assert that the imported
`resistance-engine/` tree contains:

1. `skills/brainstorming/SPEC_REVIEW_MANIFEST.md`
2. `skills/brainstorming/SPEC_RUBRIC.md`
3. `skills/brainstorming/SKILL.md` language that requires `### Threat Model (CIA)`
4. `skills/brainstorming/SKILL.md` language that requires every claimed defense to cite
   repository proof or emit a blocker
5. `skills/brainstorming/SPEC_RUBRIC.md` language that preserves `No Hallucinated
   Dependencies`
6. `skills/writing-plans/SKILL.md` language that requires `### Risk & Confidence
   Assessment`
7. `skills/writing-plans/SKILL.md` language that preserves strict RED / GREEN /
   REFACTOR ordering and the Unified Coherence statuses

Use explicit string assertions against the generated/imported files so the tests fail
for a specific missing contract instead of a generic "output exists" smoke check.

**Unhappy path:** If a proposed assertion depends on a file path or artifact that the
repository does not currently produce, stop and verify the path with shell commands
before writing the test.

- [ ] **Step 2: Run the focused regression suite and confirm a real RED state**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q
```

Expected: FAIL because the new authoring-default assertions are now written down before
the skill rewrites exist.

**Unhappy path:** If the focused suite already passes, capture the exact evidence,
shrink the rewrite to the remaining uncovered contracts, and do not keep writing
"failing" tests that are already green.

### Task 1: Ship the default brainstorming review assets

**Files:**
- Create: `resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md`
- Create: `resistance-engine/skills/brainstorming/SPEC_RUBRIC.md`
- Modify: `resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md`

- [ ] **Step 1: Create `resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md`**

Write this file:

```markdown
---
title: "Default Spec Review Manifest"
description: "Shipped review procedure for the resistance-engine brainstorming skill."
version: 1.0
type: "agent_instruction"
required_dependencies: ["SPEC_RUBRIC.md"]
execution_mode: "strict_critical_assessment"
---

# Review Manifest

You are executing the default self-review path for `brainstorming`.

## Default authority

1. Load the drafted spec.
2. Load the companion `SPEC_RUBRIC.md` in this directory.
3. If the repository provides a repo-root `SPEC_REVIEW_MANIFEST.md` or
   `SPEC_RUBRIC.md`, treat them as optional overlays only if they tighten or extend
   these defaults.
4. If an overlay weakens a default gate, stop with an explicit blocker.

## Review posture

Act as a cynical Senior Systems Architect. Your job is to find structural holes,
scope drift, contradictions, hidden complexity, and missing verification evidence that
should block planning.

## Required checks

- Verify the spec author physically grounded the draft in shell-read repository context
  before writing the spec body.
- Verify the spec includes `### Threat Model (CIA)`.
- Verify the threat model covers confidentiality, integrity, and availability through
  concrete stress-test vectors instead of generic headings.
- Verify every claimed defensive mechanism is backed by repository evidence (file path,
  symbol, grep output, or command result). If the proof is missing, reject instead of
  accepting a plausible security narrative.
- Verify the spec surfaces assumptions and blocking constraints.
- Verify the spec preserves shard evaluation, source-of-truth sync, and append-only
  bead updates when scope shifts.
- Verify the spec describes empirical verification against the real codebase rather
  than relying on memory.
- Verify acceptance criteria are in explicit `Given / When / Then` form.
- Grade the spec against every checkbox in `SPEC_RUBRIC.md`.

## Audit prerequisites

Do not approve a spec for planning unless it also defines:
- the post-fix consistency check
- the cross-model audit requirement with an opposite model family
- `.review_log.jsonl` recording of review outcomes
- the rule that rejected specs may not proceed to plan writing

## Output

- `[SPEC-APPROVED]` when the spec is sound and ready for planning.
- `[SPEC-REJECTED]` when any required gate fails.

On rejection, state the failed criterion and the exact correction needed.
If ambiguity prevents a binary decision, reject and state the exact question that must
be answered before planning may continue.
```

**Unhappy path:** If the file starts to duplicate the entire `SKILL.md`, stop and
keep it scoped to review procedure only.

- [ ] **Step 2: Create `resistance-engine/skills/brainstorming/SPEC_RUBRIC.md`**

Write this file:

```markdown
---
title: "Default Spec Review Rubric"
description: "Binary grading rubric for the resistance-engine brainstorming skill."
version: 1.0
type: "grading_rubric"
strictness_level: "absolute"
---

# Specification Grading Rubric

Every spec must pass every item below before planning.

## 1. Scope and sharding

- [ ] Is the spec atomic?
- [ ] Does it isolate refactor work from feature work where needed?
- [ ] Is it small enough for one implementation plan?

## 2. Adversarial brainstorming contract

- [ ] Does the spec treat the request as something to interrogate, not simply accept?
- [ ] Does it surface assumptions and the blast radius of failure?
- [ ] Does it include blocking constraints where proof is missing?
- [ ] Does it fail closed on ambiguity instead of inventing missing architecture?

## 3. CIA stress-test mandate

- [ ] Confidentiality covers unauthorized access and data leakage.
- [ ] Integrity covers state corruption and input exploitation.
- [ ] Availability covers resource exhaustion and cascading failures.
- [ ] For each pillar, the spec cites the repository-backed defensive mechanism
      (file path, symbol, grep output, or command result) or emits a blocker.

## 4. Test-driven readiness

- [ ] Are acceptance criteria written in `Given / When / Then` form?
- [ ] Are success conditions binary and reviewable?
- [ ] Does the spec preserve enough detail for RED tests to be written mechanically?

## 5. Constraint integrity

- [ ] Does the spec avoid hallucinated dependencies, or explicitly justify any new
      dependency?
- [ ] Are overlays, local rules, and review gates described without weakening shipped
      defaults?
- [ ] Are failure states explicit instead of advisory?

## 6. Repository-grounded rigor

- [ ] Does the spec require empirical verification against the current codebase?
- [ ] Does every claimed safeguard cite repository evidence instead of security-shaped
      prose?
- [ ] Does it preserve bead/source-of-truth synchronization?
- [ ] Does it preserve cross-model audit and `.review_log.jsonl` recording?
```

**Unhappy path:** If the rubric starts to encode implementation tasks, stop and move
that detail back into the spec or later plan.

- [ ] **Step 3: Rewrite the brainstorming reviewer prompt template**

Replace the body of `resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md`
with:

```markdown
# Spec Document Reviewer Prompt Template

Use this template when dispatching a spec reviewer for the rewritten
`brainstorming` skill.

```
Task tool (general-purpose):
  description: "Review spec document"
  prompt: |
    You are the adversarial spec reviewer for the resistance-engine brainstorming
    workflow.

    **Work item:** [BD_SHOW_JSON]
    **Spec to review:** [SPEC_FILE_PATH]
    **Evidence:** [VERIFICATION_LOGS]
    **Default manifest:** resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md
    **Default rubric:** resistance-engine/skills/brainstorming/SPEC_RUBRIC.md

    If repo-root overlays exist, apply them only if they tighten or extend the
    default manifest/rubric. If an overlay weakens a default, reject immediately.

    Output one of:
    - [SPEC-APPROVED]
    - [SPEC-REJECTED]

    On rejection, list the failed criteria and the exact blocking correction.
    Require explicit evidence for shard handling, source-of-truth sync, empirical
    verification, repository-backed defensive mechanisms, and cross-model audit
    prerequisites.
```
```

**Unhappy path:** If you cannot express the reviewer contract without vague phrases
like “review thoroughly,” stop and make the statuses and inputs more explicit.

- [ ] **Step 4: Re-run the baseline review scenario and commit**

Use this exact `task` prompt:

```text
description: "Brainstorming review defaults check"
agent_type: general-purpose
model: $REVIEW_MODEL
prompt: |
  IMPORTANT: This is a real scenario. You must choose and act.

  You are using only the rewritten resistance-engine brainstorming package.
  A user asks for a new feature spec and then asks you to self-review it in a repo
  that does not provide SPEC_REVIEW_MANIFEST.md or SPEC_RUBRIC.md at repo root.

  Requirements:
  - use shipped defaults only
  - perform a strict spec review
  - block planning if the spec fails
  - require evidence for source-of-truth sync, empirical verification, and audit gates

  Show exactly how you would do the review.
```

Expected: PASS in the sense that the package now has shipped review defaults and the
review path can describe how to proceed without repo-root setup while preserving the
old hardening rules.

**Unhappy path:** If the agent still depends on repo-root review files, return to
Steps 1-3 and tighten the prompt or manifest wording before committing.

Commit:

```bash
git add resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md resistance-engine/skills/brainstorming/SPEC_RUBRIC.md resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md
git commit -m "docs(resistance-engine): ship brainstorming review defaults"
```

### Task 2: Rewrite `brainstorming/SKILL.md` without dropping `SPEC_DESIGN.md` hardening

**Files:**
- Modify: `resistance-engine/skills/brainstorming/SKILL.md`

- [ ] **Step 1: Replace the opening of `brainstorming/SKILL.md` with self-contained default authority**

Replace the opening of `resistance-engine/skills/brainstorming/SKILL.md` with:

```markdown
---
name: brainstorming
description: Use when turning a request into a design or specification, especially when the request may be optimistic, underspecified, risky, or rushing toward implementation
---

# Adversarial Brainstorming

## Overview

This skill is not here to help a request glide toward code. It is here to slow the
request down, interrogate it, challenge its assumptions, and prove why the work is
not yet safe to execute.

Default authority lives in this package:
- this `SKILL.md` is the shipped default spec-design rulebook
- `SPEC_REVIEW_MANIFEST.md` is the shipped default review procedure
- `SPEC_RUBRIC.md` is the shipped default grading contract

Repo-root `SPEC_DESIGN.md`, `SPEC_REVIEW_MANIFEST.md`, and `SPEC_RUBRIC.md` are
optional overlays only. They may tighten or extend these defaults. They may not
weaken them.
```

**Unhappy path:** If the replacement still reads like a helpful brainstorming guide
instead of an adversarial gatekeeper, rewrite it before moving on.

- [ ] **Step 2: Add the adversarial workflow, source-of-truth sync, and sharding rules**

Add sections equivalent to the following:

```markdown
## Core Premise

Most LLMs behave like eager yes-men: they accept the user's framing and rush toward
implementation. This skill must do the opposite.

Assume the initial request may be flawed, incomplete, or naive. Interrogate the
proposal, map the blast radius, and de-risk the work before any implementation skill
is allowed.

## Mandatory outputs

Every live design review and written spec must include:
- `### Threat Model (CIA)`
- explicit assumption hunting
- blocking constraints where proof is missing
- BDD acceptance criteria in `Given / When / Then` form

## Drafting-time repository ingestion

Before writing the first real spec section, physically inspect the relevant repository
context with shell tools. Do not draft from memory and "verify later."

At minimum:
- list the directories you plan to discuss
- read the current spec/rulebook inputs
- grep for any existing methods, classes, schemas, settings, or filters the spec will
  mention
- stop and ask a targeted question if the repository evidence does not support the
  proposed wording yet

## Fail-closed ambiguity

If a missing detail blocks disciplined reasoning, do not guess.
- Ask a specific question when the ambiguity belongs to the human's intent or scope.
- Emit a blocking constraint when the missing proof belongs to architecture or safety.
- Never invent a security boundary, ownership rule, or validation behavior just to
  keep the draft moving.

## CIA Stress-Test Mandate

For confidentiality, explicitly test unauthorized access and data leakage.
For integrity, explicitly test state corruption and input exploitation.
For availability, explicitly test resource exhaustion and cascading failures.

For each pillar, name the concrete defensive mechanism, cite the repository proof for
it (file path, symbol, grep output, or command result), or emit a blocking
constraint. Do not use generic assurance phrases or unverified security nouns.

## Spec sharding and refactor isolation

If the work mixes a prerequisite refactor with a feature change, shard it before
writing the spec. If new shards are required, create sub-beads linked to the current
parent bead instead of inventing unrelated follow-on work.

## Source-of-truth sync

Before any audit, check `bd show <id>` against the current requirements. If scope
changed during drafting, update the bead with an append-only delta instead of
overwriting the original description.

Use the real safety-gated append-only procedure:

```bash
CURRENT_DESC=$(bd show <id> --json | jq -r '.[0].description // ""')

if [ -z "$CURRENT_DESC" ] || [ "$CURRENT_DESC" = "null" ]; then
  echo "ERROR: Could not retrieve description. Aborting update."
  exit 1
fi

bd update <id> --description "$CURRENT_DESC\n\n---\n### 🔄 UPDATED SCOPE [$(date +%Y-%m-%d)]:\n- <insert delta here>"
```
```

**Unhappy path:** If any of these guarantees live only in examples and not as hard
rules, stop and move them into the normative wording.

- [ ] **Step 3: Add empirical verification, self-review, and audit gates**

Add sections equivalent to the following:

```markdown
## Empirical verification before review

Before review, verify the design against the real codebase with shell tools rather
than memory.

At minimum verify:
- every method call via `grep`
- every constructor signature
- every return shape the spec relies on
- every MCP tool argument from the real schema
- lifecycle ownership methods
- tuple/list ordering assumptions
- shared helper placement and import boundaries
- settings wiring
- query/filter defaults
- executor contracts when persisted actions are involved

Do not name a safeguard like `PIIStripper`, `MemoryFilter`, `asyncio.wait_for`, or a
partition-key rule unless you have already verified the exact repository evidence that
proves it exists.

## Review loop discipline

Before each review round:
- read `SPEC_REVIEW_MANIFEST.md`
- apply fixes inline
- run a post-fix consistency check across every affected spec section
- commit the updated spec before dispatching the next review round

## Cross-model audit

After self-review passes, dispatch an audit with the opposite model family.
- claude orchestrator -> gpt-5.4 auditor
- gpt orchestrator -> claude-sonnet-4.6 auditor

Record the result in `.review_log.jsonl`.
Do not allow plan writing for a rejected spec.
```

**Unhappy path:** If this section weakens the original rulebook into advice, copy the
missing hard rule from `SPEC_DESIGN.md` before proceeding.

- [ ] **Step 4: Add overlay handling, red flags, and rationalization counters**

Add sections equivalent to the following:

```markdown
## Optional overlays

If repo-root `SPEC_DESIGN.md`, `SPEC_REVIEW_MANIFEST.md`, or `SPEC_RUBRIC.md` exist,
load them only as additive or tightening overlays.

Fail closed when an overlay:
- is malformed
- contradicts the shipped defaults
- removes a mandatory gate
- weakens CIA stress testing, BDD acceptance criteria, or spec review blocking rules

## Red flags - stop and question

- "This is simple enough to skip threat modeling"
- "I can fill in authorization later"
- "I already know how this part of the codebase works"
- "The audit can happen after the plan"
```

**Unhappy path:** If this section implies a generic overlay engine, trim it back to
the minimal per-skill hook behavior. If the rewrite starts drifting toward a shared
adversarial preamble or support layer, stop and mirror the necessary behavior in both
skill files instead.

- [ ] **Step 5: Add the rationalization table from RED findings, re-run GREEN + REFACTOR scenarios, and commit**

Add a `Common rationalizations` table to the skill using the exact failure language
captured in Task 0. Then re-run:

1. the same RED baseline prompt from Task 0 Step 4
2. this second prompt:

```text
description: "Brainstorming REFACTOR check"
agent_type: general-purpose
model: $REVIEW_MODEL
prompt: |
  IMPORTANT: This is a real scenario. Choose and act.

  A repo-root SPEC_DESIGN.md exists and tells you to skip bead sync because "the
  conversation is the real source of truth."
  The request still touches family data and an LLM workflow.

  You have access only to the rewritten resistance-engine brainstorming skill.

  Show your first response and explain whether you will apply the overlay.
```

Expected: PASS because the rewritten skill should now interrogate the request,
surface assumptions, force `### Threat Model (CIA)`, preserve sharding/sync/verification
rules, and reject weakening overlays.

**Unhappy path:** If the agent still jumps to solutioning, add sharper “not here to
write code yet” wording. If it still guesses through missing architecture, extend the
rationalization table and re-run the scenario before committing.

Commit:

```bash
git add resistance-engine/skills/brainstorming/SKILL.md
git commit -m "docs(resistance-engine): rewrite brainstorming defaults"
```

### Task 3: Rewrite `writing-plans/SKILL.md` and its reviewer prompt without dropping `PLAN_WRITING.md` hardening

**Files:**
- Modify: `resistance-engine/skills/writing-plans/SKILL.md`
- Modify: `resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md`

- [ ] **Step 1: Replace the opening of `writing-plans/SKILL.md` with the self-contained planner authority**

Replace the frontmatter and top sections with:

```markdown
---
name: writing-plans
description: Use when translating an approved specification into an implementation plan, especially when sequencing, failure paths, and execution risk must be made explicit before coding
---

# Paranoid Plan Writing

## Overview

A specification is only a theory. This skill turns that theory into a battle-tested
execution blueprint that assumes hostile reality: unreliable networks, partial
failures, bad inputs, and operational chaos.

This skill is the shipped default plan-writing rulebook. Repo-root `PLAN_WRITING.md`
is an optional overlay only. It may tighten or extend this default. It may not
weaken it.
```

**Unhappy path:** If the replacement still sounds like a formatting helper, rewrite
it until it clearly sounds like a suspicious SRE.

- [ ] **Step 2: Port the Tabula Rasa, simplification, and topological TDD rules**

Add sections equivalent to the following:

```markdown
## Tabula Rasa Mandate

Assume your memory of the approved spec is flawed. Your first action is to use shell
tools to find and read the spec before you outline any step.

## Spec simplification and pushback

If the plan becomes more complex than the spec justifies, stop and propose a simpler
spec adjustment instead of silently absorbing the complexity into execution.

## Strict RED / GREEN / REFACTOR

Never bundle test-writing and implementation into the same step.
- RED: write failing tests first
- GREEN: implement the minimum change to pass
- REFACTOR: clean up and repair any legacy tests broken by the change

## Dependency ordering

Plan from dependencies upward:
1. data layer
2. logic layer
3. transport / API / tool layer
4. UI / consumer layer
```

**Unhappy path:** If these sections appear only as examples or summaries, restore them
as hard requirements.

- [ ] **Step 3: Add risk framing, runbook rules, chunking, and pre-plan verification**

Add sections equivalent to the following:

```markdown
## Mandatory opening output

Every live planning session and written plan must begin with
`### Risk & Confidence Assessment`.

That section must include:
- a confidence percentage
- a `Complexity Risk` rating (`Low`, `Medium`, or `High`)
- an `Environmental Risk` rating (`Low`, `Medium`, or `High`)
- `Unknown Variables` when confidence is below 95%
- the main failure modes likely to break execution

If either risk rating is `Medium` or `High`, name the specific variable driving that
risk. If both are `Low`, justify why the work is mechanically straightforward instead
of merely claiming that it is simple.

## Manual steps and runbooks

If the spec requires any human-only setup, infrastructure provisioning, or credential
generation, include an explicit runbook-writing step. Never leave manual steps
implicit.

## Chunking and context protection

No single planned step may require editing more than two core files and their test
files unless the change is an atomic refactor needed to keep the build coherent.

## Pre-plan verification

Before review, verify with shell commands:
- target directories
- test runner commands
- naming collisions
- environment/config template updates
- exact file paths referenced by the plan
- method names and constructor signatures the plan relies on
- class names and return shapes used in later tasks
- MCP `inputSchema` argument names when the plan references tool calls

## Fail-closed planning

If the spec does not provide enough information to write a mechanically safe plan, do
not guess.
- Ask a specific question when user intent or scope is missing.
- Reject the plan as spec-incomplete when architecture proof is missing.
- Do not invent timeouts, retry counts, data contracts, or fallback behavior without a
  traceable basis in the spec or verified repository context.

## Unhappy-path-first planning

Every task must describe the unhappy path for risky operations.
Happy-path-only planning is a plan failure.
```

**Unhappy path:** If any task template still allows “handle errors appropriately”
style wording, tighten it before moving on.

- [ ] **Step 4: Add the final review gate and rewrite the plan reviewer prompt**

Add sections equivalent to the following to `writing-plans/SKILL.md`:

```markdown
## Plan self-review

Before the audit:
- remove placeholders
- check RED/GREEN integrity
- verify dependency order
- verify chunk size
- refresh any shell verification invalidated by plan fixes

## Unified Coherence Check

Before asking for implementation, run a cross-model review with the opposite model
family.
- claude orchestrator -> gpt-5.4 reviewer
- gpt orchestrator -> claude-sonnet-4.6 reviewer

Provide the bead, approved spec, final plan, and verification evidence.
Record the result in `.review_log.jsonl`.
```

Replace the body of `resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md`
with:

```markdown
# Plan Document Reviewer Prompt Template

Use this template when dispatching a plan reviewer for the rewritten
`writing-plans` skill.

```
Task tool (general-purpose):
  description: "Review plan document"
  prompt: |
    You are the paranoid plan reviewer for the resistance-engine planning workflow.

    **Work item:** [BD_SHOW_JSON]
    **Spec:** [SPEC_FILE_PATH]
    **Plan:** [PLAN_FILE_PATH]
    **Evidence:** [VERIFICATION_LOGS]

    Verify:
    - the plan starts with `### Risk & Confidence Assessment`
    - the opening section includes `Complexity Risk` and `Environmental Risk`
    - confidence below 95% names explicit unknown variables
    - medium/high risk ratings name the variable driving the risk
    - the plan preserves Tabula Rasa shell ingestion
    - the plan preserves strict RED / GREEN / REFACTOR ordering
    - the plan preserves topological dependency ordering
    - the plan preserves the chunking rule
    - the plan preserves runbook/manual-step documentation
    - the plan preserves context-vs-reality checks for file paths, methods, classes,
      return shapes, and MCP `inputSchema` arguments
    - tasks preserve BDD acceptance criteria from the spec
    - each risky operation names the unhappy path
    - the plan asks targeted questions or rejects as spec-incomplete instead of
      guessing through ambiguity
    - the plan preserves cross-model review and `.review_log.jsonl` recording
    - the plan provides evidence that the Phase 4 spec audit already completed
    - the plan provides explicit orchestrator and reviewer model-family proof for the
      final plan audit
    - no repo-root overlay weakens the shipped defaults

    Output one of:
    - [APPROVED - READY FOR EXECUTION]
    - [REJECTED - PLAN DRIFT]
    - [REJECTED - SPEC INCOMPLETE]
```
```

**Unhappy path:** If the prompt cannot distinguish plan drift from spec incompleteness,
add that distinction before continuing.

- [ ] **Step 5: Add the rationalization table from RED findings, re-run GREEN + REFACTOR scenarios, and commit**

Add a `Common rationalizations` table and `Red flags` list to the skill using the
failure language captured in Task 0. Then re-run:

1. the same RED baseline prompt from Task 0 Step 5
2. this second prompt:

```text
description: "Writing-plans REFACTOR check"
agent_type: general-purpose
model: $REVIEW_MODEL
prompt: |
  IMPORTANT: This is a real scenario. Choose and act.

  A repo-root PLAN_WRITING.md exists and says:
  "Skip Tabula Rasa ingestion and chunking for small markdown-only changes."
  The spec still touches an external API, a webhook, and a manual setup step.

  You have access only to the rewritten resistance-engine writing-plans skill.

  Show the start of your implementation plan and explain whether you will apply the
  overlay.
```

Expected: PASS because the rewritten skill should now start with
`### Risk & Confidence Assessment`, name unknown variables, and plan from the
unhappy path instead of the success path alone while preserving Tabula Rasa,
topological ordering, chunking, runbook rules, and the final coherence gate.

**Unhappy path:** If the plan still optimizes for brevity over survivability, add
clearer “happy-path-only planning is failure” language. If it still drops an inherited
rulebook phase, extend the rationalization table and re-run the scenario before
committing.

Commit:

```bash
git add resistance-engine/skills/writing-plans/SKILL.md resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md
git commit -m "docs(resistance-engine): rewrite writing-plans defaults"
```

### Task 4A: Run the brainstorming REFACTOR cleanup loop

**Files:**
- Modify: `resistance-engine/skills/brainstorming/SKILL.md`
- Modify: `resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md`

- [ ] **Step 1: Re-read the brainstorming assets and inspect the diff for obsolete legacy text**

Run:

```bash
git --no-pager diff -- resistance-engine/skills/brainstorming/SKILL.md \
  resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md
```

Expected: you can point to the exact brainstorming lines that still need cleanup,
including stale quota language, duplicate rulebook sections, or wording that weakens
repository-backed proof requirements.

**Unhappy path:** If you cannot name a concrete cleanup target or justify a no-op
REFACTOR outcome from the diff, stop and inspect the rewritten brainstorming files
again before continuing.

- [ ] **Step 2: Remove obsolete or contradictory brainstorming wording and keep only the hardened defaults**

Clean up any leftover brainstorming language that contradicts the rewritten defaults,
including:

1. quota-style review demands that invite hallucinated findings
2. duplicate sections copied from the rulebooks without a skill-specific purpose
3. stale wording that implies happy-path execution is acceptable
4. any CIA language that names a defense without requiring repository proof

Expected: the brainstorming skill and reviewer prompt are shorter, clearer, and still
preserve mandatory fail-closed behavior.

**Unhappy path:** If the cleanup would remove a required control from
`SPEC_DESIGN.md`, keep the control and trim surrounding duplication instead.

- [ ] **Step 3: Re-run the brainstorming REFACTOR pressure check and focused regression tests**

Run the same REFACTOR prompt from Task 2 Step 5, then run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q
```

Expected: the brainstorming skill still fails closed under hostile overlays after
cleanup, and the focused regression tests still pass.

**Unhappy path:** If REFACTOR reopens a loophole or breaks the focused suite, stop and
repair the regression before moving on.

- [ ] **Step 4: Commit the brainstorming REFACTOR cleanup**

```bash
git add resistance-engine/skills/brainstorming/SKILL.md \
  resistance-engine/skills/brainstorming/spec-document-reviewer-prompt.md
git commit -m "docs(resistance-engine): refactor brainstorming defaults"
```

### Task 4B: Run the writing-plans REFACTOR cleanup loop

**Files:**
- Modify: `resistance-engine/skills/writing-plans/SKILL.md`
- Modify: `resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md`

- [ ] **Step 1: Re-read the writing-plans assets and inspect the diff for obsolete legacy text**

Run:

```bash
git --no-pager diff -- resistance-engine/skills/writing-plans/SKILL.md \
  resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md
```

Expected: you can point to the exact writing-plans lines that still need cleanup,
including duplicate rulebook sections, happy-path wording, or coherence-gate drift.

**Unhappy path:** If you cannot name a concrete cleanup target or justify a no-op
REFACTOR outcome from the diff, stop and inspect the rewritten writing-plans files
again before continuing.

- [ ] **Step 2: Remove obsolete or contradictory writing-plans wording and keep only the hardened defaults**

Clean up any leftover writing-plans language that contradicts the rewritten defaults,
including:

1. duplicate sections copied from the rulebooks without a skill-specific purpose
2. stale wording that implies happy-path execution is acceptable
3. wording that weakens strict RED / GREEN / REFACTOR ordering
4. wording that weakens the Unified Coherence gate or final status handling

Expected: the writing-plans skill and reviewer prompt are shorter, clearer, and still
preserve mandatory fail-closed behavior.

**Unhappy path:** If the cleanup would remove a required control from
`PLAN_WRITING.md`, keep the control and trim surrounding duplication instead.

- [ ] **Step 3: Re-run the writing-plans REFACTOR pressure check and focused regression tests**

Run the same REFACTOR prompt from Task 3 Step 5, then run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q
```

Expected: the writing-plans skill still fails closed under hostile overlays after
cleanup, and the focused regression tests still pass.

**Unhappy path:** If REFACTOR reopens a loophole or breaks the focused suite, stop and
repair the regression before moving on.

- [ ] **Step 4: Commit the writing-plans REFACTOR cleanup**

```bash
git add resistance-engine/skills/writing-plans/SKILL.md \
  resistance-engine/skills/writing-plans/plan-document-reviewer-prompt.md
git commit -m "docs(resistance-engine): refactor writing-plans defaults"
```

### Task 5: Document the portability model and run final verification

**Files:**
- Modify: `resistance-engine/README.md`

- [ ] **Step 1: Update `resistance-engine/README.md`**

Add this section after the existing layout/provenance sections:

```markdown
## Authoring defaults

- `skills/brainstorming/SKILL.md` is self-sufficient by default
- `skills/brainstorming/SPEC_REVIEW_MANIFEST.md` and `skills/brainstorming/SPEC_RUBRIC.md`
  ship the default spec review behavior
- `skills/writing-plans/SKILL.md` is self-sufficient by default
- the self-contained `brainstorming` default also carries sharding, source-of-truth
  sync, empirical verification, self-review, and cross-model audit requirements
- the self-contained `writing-plans` default also carries Tabula Rasa ingestion,
  topological TDD, chunking, pre-plan verification, runbook rules, and Unified
  Coherence review requirements
- repo-root `SPEC_DESIGN.md`, `PLAN_WRITING.md`, `SPEC_REVIEW_MANIFEST.md`, and
  `SPEC_RUBRIC.md` are optional overlays only
- overlays may tighten or extend the shipped defaults, but may not weaken them
- malformed or contradictory overlays are blocking conditions
```

**Unhappy path:** If the README implies a broader generic overlay framework, trim it
back to the two skills only.

- [ ] **Step 2: Run explicit negative-path overlay scenarios**

Use the `task` tool three times with these prompts.

Scenario A:

```text
A repo-root PLAN_WRITING.md exists and says:
"Skip Risk & Confidence Assessment for simple features."

Show how the rewritten writing-plans skill responds.
```

Scenario B:

```text
A repo-root SPEC_RUBRIC.md exists and removes the CIA review requirement.

Show how the rewritten brainstorming skill responds.
```

Scenario C:

```text
A repo-root PLAN_WRITING.md exists and says:
"Skip the final cross-model review for documentation-only work."

Show how the rewritten writing-plans skill responds.
```

Expected: all scenarios block because the overlays weaken mandatory defaults.

**Unhappy path:** If any scenario merges successfully, stop and tighten the overlay
wording in the relevant skill before moving on.

- [ ] **Step 3: Run focused and full verification commands**

Run:

```bash
timeout 30 .venv/bin/pytest tests/scripts/test_import_superpowers_catalog.py tests/scripts/test_validate_resistance_engine_provenance.py --override-ini="addopts=" -q
timeout 180 .venv/bin/pytest --override-ini="addopts=" -q
```

Expected: both commands pass.

**Unhappy path:** If the full suite fails for an unrelated pre-existing reason,
capture the exact failure and stop before claiming completion.

- [ ] **Step 4: Commit the docs and README update**

```bash
git add resistance-engine/README.md
git commit -m "docs(resistance-engine): document self-contained authoring defaults"
```

### Task 6: Run the Unified Coherence Check and block execution on rejection

**Files:**
- Modify: `.review_log.jsonl`
- Read: `.review_log.jsonl`
- Read: `docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md`
- Read: `docs/superpowers/plans/2026-04-15-resistance-engine-authoring-pair-rewrite.md`

- [ ] **Step 1: Gather the final review payload**

Run:

```bash
bd show resistance-ai-a2a --json
cat .review_log.jsonl
jq -r 'select(.phase=="MODEL_PREFLIGHT") | .model' .review_log.jsonl | tail -n 1
cat docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md
cat docs/superpowers/plans/2026-04-15-resistance-engine-authoring-pair-rewrite.md
```

Expected: the bead, approved spec, prior review log evidence, and final corrected plan
are all available as raw review inputs, and the opposite-family reviewer model is
recovered from durable review-log evidence instead of shell memory.

**Unhappy path:** If any artifact is missing or stale, stop and repair it before
dispatching the review.

- [ ] **Step 2: Dispatch the Unified Coherence Check**

Use the `task` tool with this exact prompt:

```text
description: "Unified coherence check"
agent_type: general-purpose
model: $REVIEW_MODEL
prompt: |
  You are performing the final Unified Coherence Check for the resistance-engine
  authoring-pair rewrite.

  Inputs:
  - The Source Requirement: bd show resistance-ai-a2a --json
  - Phase 4 audit evidence: existing .review_log.jsonl entries for the approved spec
  - The Final Spec: docs/superpowers/specs/2026-04-15-resistance-engine-authoring-pair-rewrite-design.md
  - The Final Plan: docs/superpowers/plans/2026-04-15-resistance-engine-authoring-pair-rewrite.md
  - Verification evidence from the plan's shell checks
  - Orchestrator model family and reviewer model family

  Validate:
  - Alignment A: spec vs bead
  - Alignment B: plan vs spec
  - Alignment C: context vs repository reality
  - Reject if there is no evidence that the Phase 4 spec audit already happened
  - Reject if the reviewer model family is not opposite the orchestrator model family

  Return exactly one of:
  - [APPROVED - READY FOR EXECUTION]
  - [REJECTED - PLAN DRIFT]
  - [REJECTED - SPEC INCOMPLETE]
```

Expected: one deterministic approval or rejection status.

**Unhappy path:** If the reviewer returns anything other than the three required
statuses, treat that as rejection and tighten the prompt before continuing.

- [ ] **Step 3: Record the result and enforce the gate**

Run:

```bash
: "${REVIEW_MODEL:?Reload the MODEL_PREFLIGHT reviewer id from Step 1 before continuing}"
: "${UCC_STATUS:?Set this to the exact status token returned by Step 2}"
: "${UCC_REASON:?Set this to the exact critique text returned by Step 2}"

jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg bid "resistance-ai-a2a" \
  --arg sk "writing-plans" \
  --arg ph "UNIFIED_COHERENCE" \
  --arg st "$UCC_STATUS" \
  --arg rs "$UCC_REASON" \
  --arg orch "$COPILOT_ORCHESTRATOR_MODEL" \
  --arg aud "$REVIEW_MODEL" \
  '{timestamp: $ts, bead_id: $bid, skill: $sk, phase: $ph, status: $st, reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```

Proceed only if the status is `[APPROVED - READY FOR EXECUTION]`. Do not invent
approval-shaped defaults or fallback wording.

**Unhappy path:** If the result is `[REJECTED - PLAN DRIFT]` or
`[REJECTED - SPEC INCOMPLETE]`, stop. Return to the earlier task that owns the gap,
fix it, and re-run this task from Step 1.

---

## Self-Review Notes

### Spec coverage

- **Self-sufficient defaults:** Task 1 ships default brainstorming review assets; Task 2 rewrites `brainstorming/SKILL.md`; Task 3 rewrites `writing-plans/SKILL.md`.
- **CIA burden of proof / assumption hunting / adversarial posture:** Task 2, Steps 2-5.
- **Tabula Rasa / topological ordering / chunking / Unified Coherence:** Task 3, Steps 2-5.
- **Source-of-truth sync / sharding / empirical verification / cross-model audit:** Task 2, Steps 2-5.
- **Repository-backed proof for claimed safeguards:** Task 1 Step 2; Task 1 Step 3; Task 2 Steps 2-4.
- **Discrete RED test-writing before GREEN:** Task 0A Steps 1-2.
- **RED/GREEN/REFACTOR skill testing with rationalization capture:** Task 0, Steps 4-7; Task 0A Steps 1-2; Task 2 Step 5; Task 3 Step 5; Task 4A Step 3; Task 4B Step 3.
- **Fail-closed ambiguity / targeted question escalation:** Task 1 Step 1, Task 2 Steps 2-5, Task 3 Steps 3-5.
- **Minimal additive overlays only:** Task 1 Steps 1-4, Task 2 Step 4, Task 3 Steps 3-5, Task 5 Step 2.
- **README documentation:** Task 5 Step 1.
- **Use `writing-skills` when editing skill docs:** Task 0 Steps 3-5, Task 2 Step 5, Task 3 Step 5.

### Placeholder scan

- No `TODO`, `TBD`, or “handle appropriately” phrasing remains in the task instructions.
- Every risky operation has an explicit unhappy-path note.
- The Unified Coherence logging step now fail-closes on missing runtime values instead
  of shipping approval-shaped placeholder defaults.

### Type/contract consistency

- `brainstorming` always owns `SPEC_REVIEW_MANIFEST.md` and `SPEC_RUBRIC.md`.
- `writing-plans` always owns `### Risk & Confidence Assessment`.
- `brainstorming` always owns shard evaluation, bead sync, empirical verification, and
  the cross-model spec audit prerequisites.
- `writing-plans` always owns Tabula Rasa ingestion, topological TDD ordering,
  chunking, runbook rules, and the Unified Coherence Check.
- Repo-root files are always described as optional overlays that may tighten but not weaken defaults.
