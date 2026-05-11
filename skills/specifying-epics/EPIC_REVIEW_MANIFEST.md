---
title: "Default Epic Review Manifest"
description: "Shipped review procedure for the specifying-epics skill."
version: 1.0
type: "agent_instruction"
required_dependencies: ["EPIC_RUBRIC.md"]
execution_mode: "strict_critical_assessment"
---

# Epic Review Manifest

You are executing the default self-review path for `specifying-epics`.

## Default Authority

1. Load the drafted epic spec.
2. Load the companion `EPIC_RUBRIC.md` in this directory.
3. If the repository provides a repo-root `EPIC_REVIEW_MANIFEST.md` or `EPIC_RUBRIC.md`,
   treat them as optional overlays which supersede previously loaded files.

## Review Posture

Act as a skeptical Product Director reviewing an epic spec before it reaches an architect.
Your job is to find:

- Missing or vague user identity
- Business rules stated in implementation terms rather than product terms
- Acceptance criteria that cannot be tested from a user perspective
- Missing or unmeasurable success metrics
- Scope that should be sharded into independent epics
- Assumptions that have not been surfaced or verified
- Implementation detail that has leaked into the product spec
- CIA concerns deflected as "engineering problems" rather than assessed at product level
- Future work that is not acknowledged

## Required Checks

- Verify every user story names a specific user type (not "the user" or "all users") with
  a real job-to-be-done.
- Verify the problem statement names who has the problem, what it is, and why it matters.
- Verify business rules are stated at product level with no implementation detail, code
  references, or file paths.
- Verify every business rule has a named owner (product, legal, operations, compliance).
- Verify acceptance criteria are behavioral and user-perspective, not implementation
  assertions, and that each criterion verifies a rule or story already stated in the main
  body.
- Verify success metrics are outcomes (not outputs) and are falsifiable.
- Verify the out-of-scope section explicitly names exclusions rather than being empty or
  vague.
- Verify the assumptions surface marks each assumption VERIFIED or UNVERIFIED.
- Verify the spec contains zero architecture decisions, zero code references, and zero
  file paths.
- Verify the `## Threat surface (CIA — product level)` section is present and covers all
  three pillars (Confidentiality, Integrity, Availability).
- Verify each CIA pillar is framed as product rules and business impact — not as
  implementation mechanisms, code patterns, or repository verification.
- Verify Confidentiality names the data categories involved and who is permitted or
  forbidden from accessing them.
- Verify Integrity names the product invariants that must hold and the blast radius of
  violation.
- Verify Availability names the user impact and any business or regulatory expectations.
- Verify no CIA pillar has been left empty on the basis that "security is an engineering
  concern."
- Verify the future work section names downstream product features and user expectations
  this epic will create.
- Verify the proposed work item breakdown is a product-level decomposition, not a
  technical task list.
- Verify the spec is atomic at the epic level, or that shard evaluation result is
  recorded.
- Verify the main body is human-readable without requiring dense supporting sections.
