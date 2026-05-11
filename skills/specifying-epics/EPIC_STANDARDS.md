---
title: "Epic Standards"
description: "Philosophical and quality standards for epic-level product specs"
version: 1.0
type: "agent_instruction"
execution_mode: "strict_critical_assessment"
---

# Epic Specification Standards

This document defines the standards applied when writing epic specs in the
`specifying-epics` skill.

## 1. User-Centricity

Every epic spec must be grounded in a real user with a real job-to-be-done:

- **Named user type**: Not "the user" or "users" — a named role with a specific context
  (e.g. "a billing admin reconciling monthly invoices", not "an admin user").
- **Real job**: Not "they want X" — the underlying motivation that makes X valuable.
  What are they trying to accomplish? What slows them down today?
- **Verifiable value**: The user story's benefit must be something we can confirm was
  delivered. If it cannot be measured or observed, it is not a benefit — it is a hope.
- **Customer vs. user (B2B)**: In B2B products the *customer* (buyer, decision-maker,
  budget holder) and the *user* (operator, end-user) are often different people with
  different pain points. An epic may need to serve both. Collapsing them into a single
  persona hides whose value you are actually optimising for and whose problem you are
  actually solving.

Abstract user descriptions ("all users", "the platform", "internal teams") hide missing
audience analysis. Surface them as unverified assumptions and block until resolved.

## 2. Scope Discipline (Product YAGNI)
Product epics suffer from the same over-engineering risk as code:

- **Minimum verifiable value**: Define the smallest scope that delivers real user value
  and can be independently shipped and measured.
- **Exclusion is explicit**: Out-of-scope items must be named. Unnamed exclusions become
  implicit scope that implementation will eventually fill — always at the wrong time.
- **One epic, one coherent value stream**: An epic covering independent user groups with
  different success metrics must be sharded.

## 3. Measurable Outcomes

Features without success metrics are activities, not products:

- **Outcome, not output**: "Users complete onboarding without dropping off" is an outcome.
  "Users see the onboarding screen" is an output. Only outcomes confirm value was
  delivered.
- **Measurable now**: If the metric requires instrumentation that does not exist, surface
  that as future work, not as an implicit assumption.
- **Falsifiable**: A success metric must be able to show that the epic did NOT succeed,
  not just that it was shipped. "Users are happy" is not falsifiable. "Support tickets
  related to X decrease by Y%" is.

## 4. Assumption Transparency

Product assumptions are the most dangerous kind because they are invisible to the people
who hold them:

- **Explicit**: Every assumption is named in the spec, not held in the author's head.
- **Verified or blocking**: An assumption is either supported by evidence (user research,
  existing data, prior behavior) or it is a blocker that must be resolved before drafting.
- **No silent defaults**: "Presumably they already have an account" is an unverified
  assumption. State it. Mark it. Resolve it.

## 5. Business Rules Are Product Rules

Business rules belong to the product spec, not to the architecture spec:

- A business rule describes what the system must do or must not do from a user or business
  perspective. It does not describe how.
- If a rule cannot be stated without referencing implementation detail, the rule is
  incompletely understood. Surface the gap as a blocking question.
- Every business rule must have an owner: product, legal, operations, or compliance.
  Ownerless rules are unenforceable and may change without notice.

## 6. Future Work (Downstream Product Cost)

Product decisions create product debt just as code creates technical debt:

- **Anticipate follow-on**: What product features will this epic make necessary or
  expected by users?
- **Surface user expectations**: What will users expect next after this ships? Are those
  expectations in scope for this epic, or explicitly deferred?
- **Design for decomposability**: Prefer product designs where follow-on epics are
  independently shippable, not sequentially coupled.

## 7. CIA at the Right Abstraction

A security concern does not become a product concern only at the point of implementation.
Every epic spec must assess Confidentiality, Integrity, and Availability at the product
level:

- **Confidentiality** concerns at epic level are about data categories, who is permitted
  to see what, and regulatory constraints — not about which auth library enforces it.
- **Integrity** concerns at epic level are about product invariants and the blast radius
  of bad data — not about which validation function catches it.
- **Availability** concerns at epic level are about user impact and business criticality
  — not about infrastructure topology or retry budgets.

The mechanism that addresses a CIA concern is an architecture decision that belongs in
`specifying-work-items`. The concern itself, and its product-level rules, belong here.

Leaving the CIA section empty because "that's an engineering concern" is a failure mode.
Product decisions about data sensitivity, permitted access, and acceptable degradation
must be made before architecture begins — or architecture will make them silently.

### Confidentiality — what to address

- What data categories does this epic introduce, expose, or aggregate? (e.g. PII,
  financial records, health data, behavioural data, internal business data)
- Who should be allowed to see it? Who must not?
- Could this epic surface data about one user to another, or to an operator who should
  not see it?
- Are there regulatory or contractual constraints on visibility (GDPR, HIPAA, contractual
  data isolation)?

*State as product rules, e.g. "A user must only see their own payment history. A support
agent may see a user's account summary but not their raw payment instrument details."*

### Integrity — what to address

- What inputs does this epic accept from users or external sources?
- What is the blast radius if those inputs are wrong, malicious, or corrupted?
- Could this epic introduce state that, if corrupted, would cause incorrect product
  behaviour for other users or downstream systems?
- Are there business rules that must hold across multiple operations (e.g. a balance
  cannot go negative, an approval cannot be granted twice)?

*State as product invariants, e.g. "A transfer cannot be processed more than once. An
invoice total must equal the sum of its line items."*

### Availability — what to address

- What does it mean for this epic's capability to be unavailable?
- Who is affected and how severely? (e.g. blocking a core user journey vs. degrading a
  secondary feature)
- Are there external dependencies this epic introduces that could become single points
  of failure?
- Are there regulatory, SLA, or contractual availability expectations this epic must meet?

*State as product requirements, e.g. "A user must always be able to view their invoice
history, even if payment processing is degraded." Do not specify uptime percentages,
infrastructure topology, or retry policies — those are architecture decisions.*

### Greenfield exception

If this epic introduces a net-new capability with no prior data or access constraints,
state that explicitly. The absence of prior constraints is itself a product decision that
architecture must be designed around. Never leave the CIA section empty.
