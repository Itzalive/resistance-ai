---
title: "Default Spec Review Rubric"
description: "Binary grading rubric for the resistance-engine specifying-work-items skill."
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
- [ ] If sharding is evaluated, is the result preserved without requiring a
      standalone `## Shard Evaluation` section unless implementation detail
      makes it necessary?

## 2. Specifying-work-items contract

- [ ] Does the spec treat the request as something to interrogate, not simply accept?
- [ ] Does it surface assumptions and the blast radius of failure?
- [ ] Does it surface blocking constraints where proof is missing, in the most
      relevant section instead of defaulting to a standalone heading?
- [ ] Does it fail closed on ambiguity instead of inventing missing architecture?

## 3. CIA stress-test mandate

- [ ] Confidentiality covers unauthorized access and data leakage.
- [ ] Integrity covers state corruption and input exploitation.
- [ ] Availability covers resource exhaustion and cascading failures.
- [ ] For each pillar, the spec cites the repository-backed defensive mechanism
      (file path, symbol, grep output, or command result) or emits a blocker.

## 4. Human-readable contract and test-driven readiness

- [ ] Does the main body let a human recover the problem, scope, governing
      business rules, key mechanics, and primary risks without reading dense
      supporting detail first, and does it stay concise and non-repetitive?
- [ ] Are acceptance criteria written in `Given / When / Then` form, binary and
      reviewable, and limited to verifying rules already stated in the main body?
- [ ] Does the spec preserve enough detail for RED tests to be written mechanically?
- [ ] Are abstract terms unpacked immediately with concrete meaning instead of
      standing in for missing mechanics?

## 5. Constraint integrity

- [ ] No Hallucinated Dependencies: does the spec avoid hallucinated dependencies, or explicitly justify any new
      dependency?
- [ ] Are overlays, local rules, and review gates enforced without weakening
      shipped defaults or forcing workflow-only metadata into the spec body by
      default?
- [ ] If a section can be deleted without changing what an implementer builds,
      tests, or verifies, is it kept out of the work item body?
- [ ] Are failure states explicit instead of advisory?

## 6. Repository-grounded rigor

- [ ] Does the spec require empirical verification against the current codebase?
- [ ] Does every claimed safeguard cite repository evidence instead of security-shaped
      prose?
- [ ] If the request is synchronization, projection, event-driven, or
      state-driven work, does the main body explicitly name the source, target,
      trigger, mapping rules, state rules, and replay/retry/failure behavior?
- [ ] Does the workflow preserve issue/source-of-truth synchronization without
      requiring a dedicated spec-body section for it?
- [ ] Does the workflow preserve cross-model audit and `.review_log.jsonl`
      recording without requiring dedicated review-metadata sections in the spec
      body?
