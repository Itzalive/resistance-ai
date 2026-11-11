---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

Dispatch resistance-engine:code-reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- At plan end in subagent-driven development (checkpoint reviews cover tasks during execution)
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**1b. Run the architecture check (before the whole-branch review at plan end, and before
any review that precedes a merge; not before per-task or batch reviews):**

Only where the repository has an architecture model: its model folder (`docs/architecture`
unless the overlay `ARCHITECTURE_DESIGN.md` names another) holds a `.c4` file other than
`c4.c4`. With no model, skip this step.

Run the overlay's `deps-command`, then:

```bash
node <skills-dir>/shared/scripts/architecture-delta.mjs check --repo . --model <model> --deps <deps-file> --separator <separator>
```

Give the reviewer the whole output as `{ARCH_CHECK_OUTPUT}`.
- **A breach not in the known gap is a Critical issue.** Fix it in code, or hold the merge
  and hand a diff request to `defining-architecture`. Never resolve it by adding a
  known-gap entry in the branch.
- **Exit 2** stops the request with the tool's error.
- **A stale entry** is not an issue. Note it for `finishing-a-development-branch`, which
  removes it.

**2. Dispatch code-reviewer subagent:**

Use Task tool with resistance-engine:code-reviewer type, fill template at `code-reviewer.md`

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary
- `{ARCH_CHECK_OUTPUT}` - The architecture check's output from step 1b, or "no architecture model"

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch resistance-engine:code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: requesting-code-review/code-reviewer.md
