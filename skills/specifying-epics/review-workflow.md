# Specifying-Epics Review Workflow

Load this file only after a written epic spec exists.

## Review Loop Discipline

Run the review using the shipped `EPIC_REVIEW_MANIFEST.md` in this directory.
The review is not optional and may not be abbreviated.

**Review procedure:**

1. Ingest `EPIC_REVIEW_MANIFEST.md` and `EPIC_RUBRIC.md` using your workspace reading
   tools.
2. If repo-root overlays exist, apply them only if they tighten the defaults.
3. Run every check in the manifest against the drafted epic spec.
4. Grade against every rubric item.
5. Output `[EPIC-APPROVED]` or `[EPIC-REJECTED]` with the failed criterion and the exact
   correction needed.

**On rejection:**

- Log the rejection to `.review_log.jsonl` using the `SPEC_REVIEW` rejection template
  in `../shared/review-log-jsonl.md`, substituting `skill: "specifying-epics"` and
  `phase: "EPIC_REVIEW"`.
- Fix the spec inline.
- Run a post-fix consistency check across every affected section.
- Commit the updated spec before dispatching the next review round.
  `git commit -m "epic(<epic_id>): r<N> fixes..."`
- Re-run the full review from the beginning.
- **Circuit Breaker:** If you fail self-review five consecutive times, you are strictly
  forbidden from attempting a sixth fix. Halt, output the exact rubric failure, and ask
  the human for product guidance and whether to continue.
- A rejected epic spec may **not** proceed to work item decomposition or
  `specifying-work-items`. No exceptions.

## Cross-Model Audit

After the epic spec passes self-review, it must be audited by a model from the opposite
family before work item decomposition begins. Load `EPIC_REVIEW_MANIFEST.md` to create
the audit context and ensure the auditor applies the same standards.

**Invocation Syntax:** Physically invoke the `requesting-code-review` skill. Determine
your current model family.

- If you are Claude, explicitly set the skill's `model` parameter to `gpt-5.4`.
- If you are GPT, explicitly set the skill's `model` parameter to `claude-sonnet-4.6`.

Both models receive:

- The epic title and description.
- The full epic spec text.
- The shipped `EPIC_RUBRIC.md`.

**Pass condition:** The auditing model returns `[EPIC-APPROVED]`.

- Record the approval in `.review_log.jsonl` using the `CROSS_MODEL_AUDIT` approval
  template in `../shared/review-log-jsonl.md`, substituting
  `skill: "specifying-epics"`.

**On cross-model rejection:**

- Log the rejection to `.review_log.jsonl` using the `CROSS_MODEL_AUDIT` rejection
  template in `../shared/review-log-jsonl.md`, substituting
  `skill: "specifying-epics"`.
- **Circuit Breaker:** If you fail cross-model audit three consecutive times, halt and
  ask the human for product guidance and whether to continue.
- Fix the spec inline.
- Run a post-fix consistency check across every affected section.
- Commit the updated spec before returning to the self-review loop.
  `git commit -m "epic(<epic_id>): cr<N> fixes..."`
- Re-run the full review loop from the self-review step.
- The epic spec may not proceed to work item decomposition until both reviews pass.
