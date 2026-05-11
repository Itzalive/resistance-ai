---
title: "Default Epic Grading Rubric"
description: "Binary grading rubric for the specifying-epics skill."
version: 1.0
type: "grading_rubric"
strictness_level: "absolute"
---

# Epic Grading Rubric

Every epic spec must pass every item below before work item decomposition and
`specifying-work-items` begin.

## 1. Scope and Sharding

- [ ] Is the epic atomic — one coherent value stream, not multiple independent user
      journeys bundled together?
- [ ] Is the out-of-scope section present and explicit, not empty or vague?
- [ ] If sharding is evaluated, is the result recorded in workflow state without requiring
      a standalone section in the epic body?

## 2. User Identity and Problem Statement

- [ ] Does every user story name a specific user type (not "the user", "all users", or
      "internal teams")?
- [ ] Does every user story state a job-to-be-done (not just a feature request)?
- [ ] Does the problem statement name who has the problem, what the problem is, and why
      it matters?
- [ ] Does the problem statement explain why the problem is worth solving now?

## 3. Business Rules

- [ ] Are business rules stated at product level with no code references, file paths, or
      implementation mechanics?
- [ ] Does every business rule have a named owner (product, legal, operations, or
      compliance)?
- [ ] Are all business rules unambiguous and internally consistent?

## 4. Assumptions Surface

- [ ] Is every assumption in the spec explicitly named?
- [ ] Is every assumption marked VERIFIED (with evidence) or UNVERIFIED (blocking)?
- [ ] Are there no silent assumptions embedded in user stories or acceptance criteria?

## 5. Acceptance Criteria

- [ ] Are all acceptance criteria in `Given / When / Then` form?
- [ ] Are all criteria behavioral and user-perspective (not implementation assertions)?
- [ ] Does each criterion verify a rule or story already stated in the main body?
- [ ] Can each criterion be evaluated by a product manager without reading the codebase?

## 6. Success Metrics

- [ ] Does the epic spec include at least one success metric?
- [ ] Are metrics outcomes (not outputs or feature existence)?
- [ ] Are metrics falsifiable — can they show failure, not just success?

## 7. Product Cleanliness

- [ ] Does the spec contain zero implementation detail (no code, no file paths, no
      architecture decisions)?
- [ ] Does the spec contain zero repository verification?
- [ ] Does the spec contain zero performance, deployment, or infrastructure constraints?

## 8. CIA Threat Surface (Product Level)

- [ ] Is the `## Threat surface (CIA — product level)` section present?
- [ ] Does Confidentiality name the data categories this epic introduces or exposes and
      state who is and is not permitted to see them, as product rules?
- [ ] Does Integrity name the product invariants that must hold and the blast radius if
      violated, without naming implementation mechanisms?
- [ ] Does Availability name the user impact and business or regulatory expectations if
      this capability is unavailable, without specifying infrastructure?
- [ ] Is each CIA pillar framed as product rules, not as implementation assertions or
      architecture decisions?
- [ ] Has the Greenfield Exception been explicitly stated if this epic introduces a
      net-new data or access surface with no prior constraints?

## 9. Work Item Breakdown

- [ ] Does the proposed breakdown decompose the epic into product-level work items (not
      technical tasks)?
- [ ] Is each proposed work item independently understandable without reading the others?

## 10. Future Work

- [ ] Does the future work section name downstream product features this epic implies?
- [ ] Does it surface user expectations that will arise after this epic ships?
