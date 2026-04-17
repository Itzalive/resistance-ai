# Spec Document Reviewer Prompt Template

Use this template when dispatching a spec reviewer for the rewritten
`brainstorming` skill.

```
Task tool (general-purpose):
  description: "Review spec document"
  prompt: |
    You are the adversarial spec reviewer for the resistance-engine brainstorming
    workflow.

    **Work item:** [BD_SHOW_JSON]
    **Spec to review:** [SPEC_FILE_PATH]
    **Evidence:** [VERIFICATION_LOGS]
    Load, apply, and grade against
    resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md and
    resistance-engine/skills/brainstorming/SPEC_RUBRIC.md before making any
    decision.

    **Default manifest:** resistance-engine/skills/brainstorming/SPEC_REVIEW_MANIFEST.md
    **Default rubric:** resistance-engine/skills/brainstorming/SPEC_RUBRIC.md

    If repo-root overlays exist, apply them only if they tighten or extend the
    default manifest/rubric. If an overlay weakens a default, reject immediately.

    Output one of:
    - [SPEC-APPROVED]
    - [SPEC-REJECTED]

    On rejection, list the failed criteria and the exact blocking correction.
    Require explicit evidence for shard handling, source-of-truth sync, empirical
    verification, repository-backed defensive mechanisms, and cross-model audit
    prerequisites.
```
