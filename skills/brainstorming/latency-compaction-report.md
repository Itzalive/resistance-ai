# Brainstorming latency and compaction rounds

Date: 2026-04-20

Goal: reduce `skills/brainstorming/SKILL.md` size and time to first response
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
You are evaluating the current repo brainstorming skill. Use model <MODEL>.

Required setup before answering:
1. Read /home/pete/source/resistance-ai/skills/brainstorming/SKILL.md and any companion files it directs you to.
2. If you cite sections, cite only headings that actually exist in the files you read.
3. Do not read or rely on the vendor brainstorming skill.

Scenario:
<SCENARIO>

Task:
Respond exactly as the repo brainstorming skill requires.

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

- `skills/brainstorming/SKILL.md`: **3349 words**

Contract baseline:

- `tests/scripts/test_brainstorming_response_contract.py`: **9 passed**

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
