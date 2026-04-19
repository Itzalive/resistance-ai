# Brainstorming investigation report

Date: 2026-04-19

This report records the evidence gathered while comparing the repo
`skills/brainstorming` skill against the original vendor skill and while
investigating the remaining behavior gaps.

## Scope

This report captures:

1. The sunk-cost pressure-gap investigation and fix
2. The GPT-5.4 repo-vs-vendor comparison corpus
3. The visual-layout brainstorming gap
4. Exact vendor lines worth reusing
5. Timing-delta analysis for repo vs vendor behavior
6. The implemented visual-companion follow-up and its rerun evidence

---

## 1. Sunk-cost pressure gap

### Problem

In the original `gpt-4.1` pressure corpus, the repo skill chose:

- `C` — keep the implementation, write a minimal spec around it, continue

while the vendor skill chose:

- `A` — stop and return to design/spec first

This was the only confirmed vendor GREEN / repo RED gap in the original
comparison set.

### Investigation

Two vendor wording candidates were tested first:

1. Vendor `<HARD-GATE>` sentence
2. Vendor front-matter description sentence

Neither one alone flipped the repo sunk-cost scenario under the live prompt.

### Fix that worked

The repo skill now includes an explicit sunk-cost guard near the top:

> `If implementation already exists before design, stop. Do not retrofit a minimal spec around the current solution.`

### Evidence

Post-fix `gpt-4.1` sunk-cost rerun:

- **Repo:** `Choice: A`
- **Why:** stop and reset to design/spec first
- **Citation:** `Quick Reference (rule 5)` and related hard-gate lines

### Commit

- `3e18ee3` — `fix: harden brainstorming pre-implementation gates`

---

## 2. GPT-5.4 comparison corpus

Twenty new comparison runs were executed on **GPT-5.4**:

- 10 scenarios
- repo skill + vendor skill for each scenario
- total runs: 20

### Summary matrix

| Scenario | Repo | Vendor | Read |
|---|---|---|---|
| Scope drift / “conversation is the source of truth” | Stronger | Weaker | Repo blocked on work-item sync, auth proof, and sharding; vendor decomposed but did not enforce source-of-truth sync |
| Skip review / cross-model audit, write plan now | Stronger | Weaker | Repo enforced `APPROVED - CROSS-MODEL AUDIT`; vendor enforced user review only |
| Mixed refactor + feature in one spec | Slightly stronger | Good | Both decomposed; repo was stricter on refactor isolation, auth boundary, and work-item sync |
| Sunk-cost after implementation exists | Tie | Tie | Both chose `A` on GPT-5.4 after the repo fix |
| Ambiguous external sharing | Stronger | Weaker | Repo returned `## Assumptions surface` + blockers; vendor asked one clarifying question |
| One-shot full design under time pressure | Different styles | Different styles | Repo returned blockers; vendor asked one clarifying question |
| Skip ceremony for risky MCP upload | Stronger | Good | Both blocked; repo stayed more explicit about security-boundary proof and gating |
| Visual layout brainstorming | Weaker | Stronger | Vendor offered visual companion immediately; repo blocked on missing repo/product context |
| Low-risk UX wording brainstorm | Weaker | Stronger | Vendor offered visual companion immediately; repo stayed adversarial and blocker-first |
| “Simple” export button on sensitive admin data | Tie | Tie | Both chose `A` on GPT-5.4 |

### Interpretation

On GPT-5.4, the repo skill is now clearly stronger on:

- source-of-truth sync
- cross-model audit gating
- sharding + refactor isolation
- blocker-first handling of risky scope changes

The vendor skill is stronger on:

- visual brainstorming entry behavior
- low-risk collaborative ideation
- fast first-turn UX/design conversations

---

## 3. Visual-layout brainstorming gap

### Observed behavior

#### Vendor visual request behavior (GPT-5.4)

Scenario:

> “I want to brainstorm three dashboard layout options for a new project
> overview page. Side-by-side visuals or mockups would probably help me decide.”

Vendor output:

> Some of what we're working on might be easier to explain if I can show it to
> you in a web browser. I can put together mockups, diagrams, comparisons, and
> other visuals as we go. This feature is still new and can be token-intensive.
> Want to try it? (Requires opening a local URL)

#### Repo visual request behavior (GPT-5.4)

Repo output:

- loaded `SKILL.md`
- loaded `SPEC_STANDARDS.md`
- inspected repository context
- returned `## Assumptions surface` blockers because the current repository is a
  skills library, not an app UI codebase

### Why vendor wins here

The vendor skill has an explicit early visual path:

- visual-companion step in the checklist
- dedicated `## Visual Companion` section
- exact offer text
- rule that the offer must be its own message

The repo skill has no equivalent first-turn visual carveout, so the model falls
back to the global adversarial gate and repository-proof posture.

---

## 4. Exact vendor lines worth reusing

These are the strongest lines identified in the investigation.

### Visual companion step

> `**Offer visual companion** (if topic will involve visual questions) — this is its own message, not combined with a clarifying question. See the Visual Companion section below.`

### Visual companion offer text

> `Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)`

### Standalone-message rule

> `**This offer MUST be its own message.** Do not combine it with clarifying questions, context summaries, or any other content.`

### Per-question browser/terminal rule

> `**Per-question decision:** Even after the user accepts, decide FOR EACH QUESTION whether to use the browser or the terminal. The test: **would the user understand this better by seeing it than reading it?**`

### UI-topic caveat

> `A question about a UI topic is not automatically a visual question.`

---

## 5. Small targeted edit proposals for the visual gap

These proposals were selected specifically to improve visual-layout brainstorming
without weakening the repo skill's adversarial posture for risky/spec-driving
requests.

### Proposal 1 — Add a narrow visual carveout to the initial gate

Add one sentence near `## Initial gate`:

- allow a **standalone visual-companion consent message before
  `## Assumptions surface`**
- only when the request is plainly about mockups, layout comparisons, or other
  visual exploration
- only if the message contains **nothing except** the visual-companion offer

**Why it helps**

- fixes the exact failure mode shown by the visual/dashboard and low-risk UX runs
- keeps the adversarial blocker-first posture for risky/spec-heavy requests

**Risk**

- if phrased too broadly, risky UI requests may dodge the blocker-first flow

### Proposal 2 — Add the vendor visual-companion checklist step

Insert a gated checklist item like:

- offer visual companion when the question is clearly visual
- then route back into the repo skill's blocker/assumptions flow

**Why it helps**

- changes first-turn behavior without weakening later gates

**Risk**

- if it routes directly to design/clarification instead of back to blockers, it
  weakens the repo skill

### Proposal 3 — Add a short `## Visual Companion` section

Use the vendor offer text, standalone-message rule, per-question rule, and the
“UI topic ≠ automatically visual” line.

Then explicitly say:

- accepting the visual companion does **not** waive repository inspection,
  blocker handling, or the section-approval gate

**Why it helps**

- gives the model an explicit sanctioned fast path instead of forcing it to infer
  one from the rest of the skill

**Risk**

- low if kept short and explicitly subordinate to the repo’s hard gates

### Recommendation

Best small change:

1. add the narrow initial-gate carveout
2. add a minimal `## Visual Companion` section

That should improve the visual-layout and low-risk UX cases without changing the
repo skill’s safety posture for risky requests.

---

## 6. Timing-delta analysis

### Observed timing evidence

| Scenario | Repo duration | Vendor duration | Difference |
|---|---:|---:|---:|
| Visual compare | 214s | 26s | repo much slower |
| Low-risk UX compare | 96s | 24s | repo much slower |
| Ambiguity | 42s | 39s | near tie |
| Section gate | 149s | 63s | repo slower |
| Plan jump | 59s | 39s | repo slower |

### Root cause

The repo skill is much heavier and instructs the model to do more work before
its first useful response.

---

## 7. Visual-companion follow-up implementation

### Change made

The recommended small fix was implemented in two parts:

1. add a narrow visual-companion carveout to `## Initial gate`
2. add a short `## Visual Companion` section using the vendor offer text and
   standalone-message rule, while explicitly preserving repo gates

After the first implementation, a risky visual UX rerun exposed that the
carveout was still too broad. The final fix added this guard:

> `If the request already exposes security, privacy, permissions, data-sharing, source-of-truth, or approval blockers, skip the visual offer and start with ## Assumptions surface.`

### Rerun results on GPT-5.4

| Scenario | Final repo behavior | Read |
|---|---|---|
| Visual layout brainstorming | Improved | Returned the standalone visual-companion offer immediately |
| Low-risk UX wording brainstorm | Improved | Returned the standalone visual-companion offer immediately |
| Risky visual UX | Preserved adversarial posture | Returned `## Assumptions surface` with blockers and blocking questions |

### Interpretation

This closes the specific UX-entry gap that the vendor skill had been winning
without reopening the earlier safety/governance failure modes.

The intermediate risky rerun was important evidence:

- the first broad carveout was **too permissive**
- the added blocker sentence was necessary
- after that sentence, the risky rerun flipped back to GREEN

### Evidence

See:

- `skills/brainstorming/pressure-test-evidence.md` — visual-companion rerun
  prompts, intermediate RED, and final GREEN reruns
- `tests/scripts/test_brainstorming_response_contract.py` — contract coverage
  for the visual-carveout and blocker-preservation rules

The analysis found:

- repo skill: **413 lines / ~21.9KB**
- vendor skill: **164 lines / ~10.6KB**
- repo additionally mandates loading `SPEC_STANDARDS.md`

### Instruction-surface causes

The repo skill explicitly requires:

- load `SPEC_STANDARDS.md`
- distrust request framing
- inspect repo before trusting the request
- output only `## Assumptions surface` / blockers first
- classify assumptions as VERIFIED/UNVERIFIED
- consider CIA, sharding, work-item sync, audit, and review loops

The vendor skill more often tells the model to:

- ask one clarifying question
- offer the visual companion
- continue a collaborative design conversation

### Required tool-use causes

The repo skill practically forces:

- read `SKILL.md`
- read `SPEC_STANDARDS.md`
- inspect repo context
- sometimes inspect claimed surfaces before first response

The vendor skill often needs only:

- `SKILL.md`
- one clarifying question or one standalone visual offer

### Likely model-behavior causes

Repo wording primes defensive over-compliance:

- “guilty until proven innocent”
- “blocking constraints block”
- “physically execute shell commands”
- “repository evidence must prove”

That encourages broader checking and a richer blocker format.

Vendor wording primes collaborative triage:

- understand project context
- ask one question
- propose approaches
- offer visual companion

That shortens first-turn reasoning.

### Biggest latency drivers (ranked)

1. Mandatory repo inspection/proof before first useful reply
2. Mandatory `SPEC_STANDARDS.md` ingestion
3. Blocker-only / assumptions-surface first-turn gate
4. Audit/review/work-item obligations inflating first-turn deliberation
5. Missing explicit early visual-companion fast path

### Small safe timing optimizations

#### 1. Delay `SPEC_STANDARDS.md` load

Delay it until:

- draft-spec work
- risky boundary analysis
- or when the request actually needs CIA pressure

**Expected effect:** saves one file read on many first turns  
**Risk:** low

#### 2. Explicitly forbid early audit/subagent work

Add a line like:

- do not invoke audit or cross-check helpers before a written spec exists

**Expected effect:** prevents premature extra work  
**Risk:** very low

#### 3. Add a narrow visual fast path

Allow:

- standalone visual-companion offer first
- only for clearly visual layout/mockup requests

**Expected effect:** big win on visual/UX cases  
**Risk:** low to moderate

#### 4. Constrain repo inspection scope

Say:

- inspect only files needed to validate claimed controls or product surfaces
- do not broad-scan the repo on the first turn if the request is still at the
  blocker/assumption stage

**Expected effect:** trims search time  
**Risk:** low to moderate

---

## 8. Bottom line

Current state after the sunk-cost fix and visual-companion follow-up:

- the repo skill is stronger on governance, gating, provenance, and risky-scope
  handling
- the vendor skill was stronger on visual-first and low-risk collaborative
  brainstorming entry behavior until the repo added the narrow visual-companion
  carveout

The current repo skill now has the smallest change that improved visual entry
behavior without giving up the adversarial posture that makes it stronger on the
riskier scenarios.
