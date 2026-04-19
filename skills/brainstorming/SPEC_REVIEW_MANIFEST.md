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
   `SPEC_RUBRIC.md`, treat them as optional overlays which superseed previously loaded files.

## Review posture

Act as a cynical Senior Systems Architect. Your job is to find structural holes,
scope drift, contradictions, hidden complexity, and missing verification evidence that
should block planning.

## Required checks

- Verify the spec author physically grounded the draft in shell-read repository context
  before writing the spec body.
- Verify the spec includes `## Threat Model (CIA)`.
- Verify the threat model covers confidentiality, integrity, and availability through
  concrete stress-test vectors instead of generic headings.
- Verify every claimed defensive mechanism is backed by repository evidence (file path,
  symbol, grep output, or command result). If the proof is missing, reject instead of
  accepting a plausible security narrative.
- Verify the spec surfaces assumptions and blocking constraints.
- Verify the spec preserves shard evaluation, source-of-truth sync, and append-only
  work item updates when scope shifts.
- Verify the spec includes a future work section.
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
