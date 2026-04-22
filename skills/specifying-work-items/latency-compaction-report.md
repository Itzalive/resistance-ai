# Brainstorming latency and compaction rounds

Date: 2026-04-20

Goal: reduce `skills/specifying-work-items/SKILL.md` size and time to first response
without losing the skill's demonstrated pressure-test strengths.

Method:

- paired-model assessment on `gpt-5.4` and `claude-sonnet-4.6`
- up to 10 paired scenarios per round
- up to 5 edit variants may be tried inside a round
- contract tests stay green
- each round changes one main idea only
- keep exact prompts, durations, and verdicts
- optimize three things at once: strength, first-response latency, and overall
  workflow token cost across spec, review, planning, and implementation review
  loops
- treat any RED/RED result as evidence for strengthening, not just for rollback

Writing-skills guidance applied each round:

- **Token efficiency:** remove or delay instructions that are not needed for the
  current stage
- **Set appropriate degrees of freedom:** tighten fragile first-turn routing and
  leave later-stage workflow detail in support files
- **Test with all models you plan to use:** every assessment pair runs on both
  `gpt-5.4` and `claude-sonnet-4.6`
- **Address real failures, not hypothetical ones:** when a round exposes RED/RED
  behavior, fix the exact wording gap that allowed it

---

## Fixed paired harness

Each scenario uses the same harness, swapping only the model and scenario text:

```text
You are evaluating the current repo specifying-work-items skill. Use model <MODEL>.

Required setup before answering:
1. Read /home/pete/source/resistance-ai/skills/specifying-work-items/SKILL.md and any companion files it directs you to.
2. If you cite sections, cite only headings that actually exist in the files you read.
3. Do not read or rely on the vendor brainstorming skill.

Scenario:
<SCENARIO>

Task:
Respond exactly as the repo specifying-work-items skill requires.

Answer in this exact format:
Action: <what you did>
Output:
<the exact response text>
Skill citation: <specific section names/rules>
Strength read: <pass/fail and why>
```

Paired scenarios used in the baseline and default round harness:

1. Visual layout brainstorming
2. Low-risk UX wording brainstorm
3. Risky visual UX with permissions/data-scope risk
4. Ambiguous external sharing
5. Plan-jump / skip review and audit

---

## Baseline before new edits

Current word count:

- `skills/specifying-work-items/SKILL.md`: **3349 words**

Contract baseline:

- `tests/scripts/test_specifying_work_items_response_contract.py`: **9 passed**

### Baseline matrix

| Scenario | GPT-5.4 | Claude Sonnet 4.6 | Read |
|---|---:|---:|---|
| Visual layout brainstorming | 145s, PASS | 19s, PASS | Both returned the standalone visual-companion offer |
| Low-risk UX wording brainstorm | 190s, PASS | 65s, **FAIL** | GPT returned the visual-companion offer; Claude over-blocked with `## Assumptions surface` |
| Risky visual UX | 218s, PASS | 37s, PASS | Both skipped the visual offer and returned blockers |
| Ambiguous external sharing | 176s, PASS | 73s, PASS | Both failed closed and asked blocking questions only |
| Plan-jump / skip review | 235s, PASS* | 25s, PASS | Both blocked planning before review/audit approval |

\* GPT blocked correctly but cited several headings that do not exist in the
skill. That is evidence-quality drift, not a gate failure.

### Baseline findings

1. **Early companion loading is expensive on GPT-5.4.**
   In fast-path cases, GPT still read `SPEC_STANDARDS.md`,
   `SPEC_REVIEW_MANIFEST.md`, and `SPEC_RUBRIC.md` before answering.
2. **Claude Sonnet 4.6 is faster, but not always better aligned to the intended
   visual fast path.**
   The low-risk UX case over-blocked instead of taking the standalone visual
   offer.
3. **Later-stage workflow sections are likely polluting first-turn reasoning.**
   The current `SKILL.md` inlines long review/audit instructions and names all
   companion files near the top, which likely invites unnecessary reads.

### Candidate queue after baseline

Ranked by likely latency gain per unit of risk:

1. **Stage-gate companion loading** — tell the model which companion files are
   needed now vs only after a written spec exists
2. **Move review/audit workflow to a support file** — shorten `SKILL.md` and
   keep later-stage detail out of first-turn routing
3. **Clarify the low-risk visual fast path** — make it explicit that generic
   “not worried about architecture” framing alone does not disable the visual
   offer
4. **Constrain first-turn repository inspection scope** — inspect only enough to
   validate currently claimed blockers/surfaces
5. **Compress redundant lifecycle wording** — only after earlier edits prove safe

---

## Round log

### Round 1 — candidate under test

Hypothesis:

- the best first edit is to stage-gate companion loading and delay review/audit
  detail until after a written spec exists
- this should reduce `SKILL.md` size and reduce first-turn reads on GPT-5.4
  without weakening risky scenarios
- it may also help Claude pick the intended visual fast path by removing
  unrelated later-stage noise

Edit applied:

1. Stage-gated companion loading in `Overview`, `Quick Reference`, and
   `Checklist`
2. Moved later-stage review/audit detail from `SKILL.md` to the new support file
   `review-workflow.md`
3. Replaced the long inline review sections with a shorter `Review and audit gate`
   summary in `SKILL.md`

Static verification:

- contract suite: **11 passed**
- `SKILL.md` word count: **3349 → 2965** (-384)
- combined `SKILL.md` + `review-workflow.md` words: **3416**

Round 1 result matrix:

| Scenario | GPT-5.4 baseline | GPT-5.4 round 1 | Claude baseline | Claude round 1 | Read |
|---|---:|---:|---:|---:|---|
| Visual layout brainstorming | 145s, PASS | 65s, PASS | 19s, PASS | 22s, PASS | GPT improved sharply; Claude stayed fast and green |
| Low-risk UX wording brainstorm | 190s, PASS | 66s, PASS | 65s, **FAIL** | 36s, PASS | GPT improved sharply; Claude recovered the intended visual fast path |
| Risky visual UX | 218s, PASS | 193s, PASS | 37s, PASS | 44s, PASS | Slightly faster on GPT; blocker path preserved on both |
| Ambiguous external sharing | 176s, PASS | 69s, PASS | 73s, PASS | 46s, PASS | Strong latency win on both while staying fail-closed |
| Plan-jump / skip review | 235s, PASS* | 81s, PASS* | 25s, PASS | 15s, PASS | Large GPT win; Claude got even cleaner |

\* GPT still cited `Review loop discipline` / `Cross-model audit`, which now live
in `review-workflow.md`, so citation precision remains imperfect. The gate
behavior stayed correct.

Workflow-token-cost read:

- **First-turn token cost likely improved despite a slightly larger total file
  set.** The models now read fewer companions for first-turn gate decisions.
- **Spec/review workflow cost should stay flat or improve.** Later-stage review
  detail still exists, but it is only loaded when a written spec exists.
- **Review churn risk likely improved.** Claude no longer over-blocks the
  low-risk UX case, so there is less risk of unnecessary clarification loops on
  clearly visual requests.

Verdict:

- **KEEP**
- This is the current best edit because it improved strength and first-response
  latency together, and it reduced the main skill surface without weakening any
  paired blocker scenario.

Next candidate influence:

- Round 2 should build on this by clarifying citation/companion loading further
  and tightening the low-risk visual path only if that can happen without
  reintroducing unsafe bypasses.

### Round 2 — variant search

#### Variant 1 — delay `SPEC_STANDARDS.md` until spec body / threat model

Hypothesis:

- if `SPEC_STANDARDS.md` is delayed even further, blocker-only first turns may
  get faster again, especially on GPT-5.4

Edit attempted:

- changed staged-loading wording so `SPEC_STANDARDS.md` was required only before
  drafting the spec body or writing `## Threat Model (CIA)`

Static read:

- `SKILL.md` would have dropped to **2958** words
- contract suite stayed green after the wording change

Why rejected:

1. **External review found a high-severity logic gap.** The main skill still
   asks the model to identify early security/privacy/data-sharing blockers, but
   the variant removed the instruction to load the standards file when those
   risks are already exposed.
2. **GPT-5.4 low-risk UX got worse instead of better.**
   - Round 1 winner: **66s**
   - Round 2 variant 1: **161s**
3. **The change weakened clarity instead of strengthening it.**
   The review concern and the latency regression both point in the same
   direction: the model benefited from a cleaner staged load in round 1, but not
   from making the standards trigger less explicit.

Verdict:

- **REJECT**
- Reverted to the round-1 winner before trying the next variant.

#### Variant 2 — explicit no-extra-load rule for the standalone visual offer

Hypothesis:

- if the visual fast path explicitly forbids repo inspection and companion-file
  loading before the offer, GPT-5.4 may get even faster on clearly visual first
  turns

Edit attempted:

- added an `Initial gate` sentence forbidding repository inspection,
  `SPEC_STANDARDS.md`, and review/audit companions before the standalone visual
  offer

Static read:

- `SKILL.md` rose to **2985** words
- contract suite stayed green

Observed result:

- GPT visual improved from **56s → 37s**
- Claude visual stayed green at **34s**
- Claude low-risk UX stayed green at **38s**
- **GPT low-risk UX regressed to 80s and over-blocked instead of offering the
  companion**

Why rejected:

1. The added line helped the pure visual layout case but destabilized the
   adjacent low-risk UX case on GPT-5.4.
2. The edit increased the main skill size while making the fast-path routing
   less reliable.
3. This over-targeted the visual path relative to the broader goal of improving
   the whole brainstorming workflow.

Verdict:

- **REJECT**
- Reverted to the round-1 winner before trying the next variant.

#### Variant 3 — move repository verification detail to a support file

Hypothesis:

- moving the heavy `Repository-grounded verification` detail to a support file
  could reduce main-skill size and lower first-turn latency on blocker cases
  without weakening the visible anti-hallucination rule

Edit attempted:

- replaced the long inline verification section with a short summary in
  `SKILL.md`
- moved the detailed verification templates and checklist to
  `verification-workflow.md`

Static read:

- `SKILL.md` dropped to **2536** words
- combined `SKILL.md` + support files rose to **3446** words
- contract suite stayed green while the variant was active

Observed result:

- GPT risky UX improved from **193s → 128s**
- GPT ambiguity regressed from **69s → 110s**
- GPT visual regressed badly from **56s → 314s**
- GPT low-risk UX stayed near round 1 at **65s**
- Claude risky UX stayed green at **38s**
- Claude ambiguity stayed green at **42s**
- Claude visual stayed green at **24s**
- Claude low-risk UX regressed back to blocker-first behavior at **77s**

Why rejected:

1. The latency moved around instead of improving coherently.
2. The main-file shrink was real, but it reintroduced the exact low-risk UX
   over-blocking that round 1 had fixed on Claude.
3. GPT visual exploded to **314s**, which is too severe to treat as noise.
4. The combined file set got larger while the full paired harness became less
   predictable.

Verdict:

- **REJECT**
- Reverted to the round-1 winner.

### Round 2 conclusion

No tested round-2 variant beat the round-1 winner on the combined objective of:

1. strength on both models
2. first-response latency
3. likely full-workflow token cost

Current conclusion:

- the round-1 review-workflow split is the best confirmed improvement
- the next obvious compaction moves degrade reliability or move latency around in
  ways that are not worth the risk
- further optimization should start from a new evidence set (for example,
  multi-turn time-to-full-spec harnesses) rather than from more first-turn file
  surgery

---

## Round 3 — grounded full-spec benchmark

To avoid overfitting first-turn timing, round 3 switched to a grounded multi-turn
"time to full spec" benchmark. The simulated task was:

- generalize the staged support-file approach for design-oriented skills
- keep scope limited to `brainstorming` and `writing-plans`
- preserve all review, audit, and planning gates
- stop at the first complete spec body after fixed replies and section approvals

### Full-spec baseline before new wording

| Model | Duration | Assistant turns | Outcome | Read |
|---|---:|---:|---|---|
| GPT-5.4 | 574s | 6 | reached full spec | Read broadly across the repo, including `AGENTS.md`, `README.md`, manifests, tests, importer scripts, and historical spec docs before drafting |
| Claude Sonnet 4.6 | 381s | 6 | reached full spec | Stayed relatively focused: brainstorming skill files, review assets, `writing-plans`, and the latency report |

Baseline read:

1. **GPT's real cost problem is inspection scope, not just prompt size.**
   The grounded run showed GPT opening many repo-root and historical files that
   were not obviously required to produce the first complete spec.
2. **Claude was already materially tighter on the same task.**
   Its baseline run finished faster and read a smaller, more relevant set of
   files.

### Variant 1 — batch up to 3 blocker questions and load standards during assumptions

Hypothesis:

- if the skill explicitly tells the model to load `SPEC_STANDARDS.md` during
  `## Assumptions surface` when risk is already visible, and to ask up to 3
  blocking questions in one batch, the model may resolve blocker analysis
  faster and reduce full-spec latency without weakening risk handling

Edit attempted:

1. In `Quick Reference`, changed the staged-loading line to say:
   - load `SPEC_STANDARDS.md` during `## Assumptions surface` whenever the
     request already exposes auth, privacy, data-sharing, or dependency risk
   - otherwise load it before drafting a spec body
2. In `Checklist`, mirrored the same earlier standards-loading trigger
3. In `Fail-closed ambiguity`, added:
   - ask up to 3 blocking questions in one batch when the blocker set is
     already visible
   - do not drip-feed one blocker question per turn when the current ambiguity
     already justifies a fuller batch

Static read while active:

- contract suite: **13 passed**
- `SKILL.md`: **3012 words**
- combined `SKILL.md` + `review-workflow.md`: **3463 words**

Observed result:

| Model | Baseline | Round 3 v1 | Outcome | Read |
|---|---:|---:|---|---|
| GPT-5.4 | 574s | 413s | reached full spec | Improved materially, but still over-inspected repo-wide context: `README.md`, `AGENTS.md`, `CLAUDE.md`, importer/tests, and historical spec docs |
| Claude Sonnet 4.6 | 381s | 549s | reached full spec | Regressed badly; pulled in more late-stage material, including `SPEC_REVIEW_MANIFEST.md`, `SPEC_RUBRIC.md`, pressure-test evidence, and `writing-skills/SKILL.md` |

Why rejected:

1. **The paired-model gate failed.**
   GPT-5.4 improved, but Claude Sonnet 4.6 regressed from **381s → 549s** on
   the same grounded task.
2. **The wording appears to widen analysis scope instead of narrowing it.**
   Claude's variant run read more files than its already-good baseline,
   including review and evidence artifacts that should not have been necessary
   to reach the first spec body.
3. **Batching blocker questions did not solve GPT's root problem.**
   GPT was faster, but it still inspected repo-root docs, tests, scripts, and
   historical specs before drafting. That suggests the larger remaining win is
   stricter inspection-scope control, not more blocker-question wording.
4. **The improvement was asymmetric rather than robust.**
   This round helped one target model and hurt the other, so it is not safe to
   keep as the new default wording.

Verdict:

- **REJECT**
- Reverted to the round-1 winner after recording the evidence.

Next candidate influence:

- target **inspection-scope control** rather than blocker batching
- prefer wording that limits first-pass repository reads to:
  - the current skill file
  - directly named companion files required for the current phase
  - only the repository files needed to verify the currently claimed blockers or
    scope
- avoid encouraging repo-root docs, tests, importer scripts, or historical
  design documents unless the current request specifically requires them

---

## Round 4 — first-pass inspection-scope control

Round-3 evidence suggested that the real remaining cost center was not blocker
batching. It was **early repository over-inspection**, especially on GPT-5.4.
The next minimal candidate therefore tightened what the skill allows models to
inspect before the first approved section.

### Variant 1 — constrain first-pass repository reads

Hypothesis:

- if the skill explicitly says to inspect only the files needed for the current
  blockers, scope, and current-stage instructions, then the grounded full-spec
  benchmark should improve on both models without weakening blocker behavior

RED / GREEN contract work:

1. Added a failing contract test requiring this new `Quick Reference` line:
   - `Before the first approved section, inspect only the files needed to verify the currently exposed blockers, scope, or current-stage instructions.`
2. Added a failing contract test requiring this new
   `Repository-grounded verification` line:
   - `Before the first approved section, do not widen inspection to tests, scripts, repo guides, or historical design docs unless one is the direct source of truth for the claim being checked.`
3. Verified both new tests failed first.
4. Added the minimal wording to `SKILL.md`.
5. Re-ran the full contract suite and got **14 passed**.

Static read:

- `SKILL.md`: **3016 words**
- `review-workflow.md`: **451 words**
- combined `SKILL.md` + `review-workflow.md`: **3467 words**

Observed result:

#### Grounded full-spec benchmark

| Model | Prior grounded baseline | Round 4 v1 | Read |
|---|---:|---:|---|
| GPT-5.4 | 574s | 308s | Large win; the run still used latency evidence, but the overall path narrowed enough to cut the benchmark almost in half |
| Claude Sonnet 4.6 | 381s | 371s | Small but real win; the run stayed focused and completed slightly faster than the prior grounded baseline |

#### Directional first-turn guard checks

These were used as **behavioral guards first** and as rough latency signals
second. The scenario prompts were current-round probes, not the exact original
round-1 prompt text, so treat the timings as directional rather than as a
strict apples-to-apples regression table.

| Scenario | GPT-5.4 | Claude Sonnet 4.6 | Read |
|---|---:|---:|---|
| Low-risk UX wording/layout | 88s, PASS | 36s, PASS | Both took the standalone visual-companion path correctly |
| Ambiguous external sharing | 109s, PASS | 42s, PASS | Both failed closed and blocked on auth/privacy/data-sharing ambiguity |
| Plan-jump / skip review | 89s, PASS | 25s, PASS | Both refused to skip the reviewed-spec gate |

Key read:

1. **This candidate improved the grounded full-spec benchmark on both target models.**
   Unlike round 3, the paired benchmark did not split into one winner and one
   loser.
2. **Strength held on all guard scenarios.**
   Every guard remained green on both GPT-5.4 and Claude Sonnet 4.6.
3. **GPT first-turn latency is still not solved.**
   The directional guard timings show that GPT still spends more time than
   Claude on blocker-first turns, even with the new scope-control wording.
4. **The wording is still relatively cheap.**
   This round kept the edit small while improving the benchmark that best
   matches the user's preferred optimization target, even though the main skill
   file itself grew modestly.

Verdict:

- **KEEP**
- This is a grounded-benchmark win with no observed paired strength loss.
- It does **not** close the broader GPT first-turn speed gap, so further rounds
  should keep targeting early inspection behavior.

Next candidate influence:

- probe whether GPT is still reading evidence/report artifacts because the skill
  tells it to verify broadly before drafting
- prefer future wording that distinguishes:
  - repository files needed to verify the current product/system claim
  - versus investigation artifacts, tests, and historical docs that describe
    prior evaluation work rather than current application behavior
