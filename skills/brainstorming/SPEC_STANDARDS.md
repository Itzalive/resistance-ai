---
title: "Spec Standards"
description: "Architechtural philosophy to be applied when writing specs"
version: 1.0
type: "agent_instruction"
execution_mode: "strict_critical_assessment"
---

# Specification Architectural Standards

This document defines the philosophical and architectural standards that must be applied during the Brainstorming and Spec Design phase.

## 1. The CIA+ Threat Model
A perfectly functional feature is a failure if it introduces an unmitigated attack vector. You must evaluate every design against:

* **Confidentiality (Data Exposure):** Does this feature process or expose sensitive data (PII, API keys)? Never assume downstream systems will scrub secrets. The design must explicitly define sanitization boundaries.
* **Integrity (State Corruption & Hostile Input):** If this feature reads external files, network requests, or uses an MCP server, treat that data as hostile. Define strict type validation to prevent prompt/context injection.
* **Availability (Resource Exhaustion):** No unbounded operations are allowed. Every list/retrieval operation must paginate. Every external network call or database transaction must define a timeout and retry limit.
* **Agentic Vulnerabilities (Least Privilege):** Does the spec grant the implementation excessive permission scopes? Request the absolute minimum directory access and token limits.
* **Supply Chain (Hallucination):** Every new third-party library introduces supply chain injection risk. You must justify its necessity and physically verify its real-world existence.

## 2. Future Work (Downstream Cost)
Architecture is about measuring future debt. When designing a spec, consider the follow-on work items it creates:
- **Anticipate follow-on work**: Identify tasks, bugs, and enhancements likely to be created as a result. List them in the spec so they can influence architecture decisions.
- **Design for work item cost**: A design that produces many high-priority or high-effort future work may be more expensive than it appears. Prefer designs that keep follow-on work decomposable, low-risk, and independently deliverable.
- **Value vs. future debt**: Weigh the immediate value of a design choice against the downstream work items burden it creates. A simpler design with fewer work items often has a better cost/value ratio than a "complete" design that defers complexity into a long tail of work items.
- **Surface hidden dependencies**: If a design requires future work items before the feature is end-to-end usable, make that explicit so the full scope is visible upfront.

## 3. Sharding & Refactor Isolation
Do not default to monolithic specs. Complex specs have a drastically higher likelihood of causing cascading failures during execution.
* **Mitigate Complexity:** If a spec cannot be fully executed and tested within a standard context window, it must be sharded.
* **Isolate Refactoring:** If a feature requires modifying existing architecture, do not bundle the refactor with the new feature. Separate the prerequisite refactoring into its own distinct, purely structural spec to reduce risk.
* **Sub-Work Items:** If you shard a spec, you must create in the work item system a new item linked to the parent item to secure the remaining work.

## 4. Post-Fix Consistency Check
When resolving a review failure, a fix applied to the prose description must also be manually reflected in:
* Pseudocode and flow comments.
* Acceptance criteria and Given/When/Then tables.
* Fields Changed / Files Changed definitions.
Circular review rounds are almost always caused by fixing a flaw in one section but leaving stale, contradictory text in another.
