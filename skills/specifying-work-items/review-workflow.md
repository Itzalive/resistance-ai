# Specifying-work-items review workflow

Load this support file only after a written spec exists.

## Review loop discipline

Run the review using the shipped `SPEC_REVIEW_MANIFEST.md` in this directory.
The review is not optional and may not be abbreviated.

**Review procedure:**

1. Ingest `SPEC_REVIEW_MANIFEST.md` and `SPEC_RUBRIC.md` using your workspace
   reading tools.
2. If repo-root overlays exist, apply them only if they tighten the defaults.
3. Run every check in the manifest against the drafted spec.
4. Grade against every rubric item.
5. Output `[SPEC-APPROVED]` or `[SPEC-REJECTED]` with the failed criterion and
   the exact correction needed.

**On rejection:**

- Log the rejection to `.review_log.jsonl` using the `SPEC_REVIEW` rejection
  template in `../review-log-jsonl.md`.
- Fix the spec inline.
- Run a post-fix consistency check across every affected section.
- Commit the updated spec before dispatching the next review round.
  `git commit -m "spec(<work_item_id>): r<N> fixes..."`
- Re-run the full review from the beginning.
- **Circuit Breaker:** If you fail self-review five consecutive times, you are
  strictly forbidden from attempting a sixth fix. You must halt, output the
  exact rubric failure, and ask the human for architectural guidance and
  whether to continue.
- A rejected spec may **not** proceed to plan writing. No exceptions.

## Cross-model audit

After the spec passes self-review, it must be audited by a model from the
opposite family before planning begins. Load `SPEC_REVIEW_MANIFEST.md` to
create the audit context and ensure the auditor applies the same standards.

**Invocation Syntax:** You must physically invoke the `requesting-code-review`
skill. Determine your current model family.

- If you are Claude, explicitly set the skill's `model` parameter to `gpt-5.4`.
- If you are GPT, explicitly set the skill's `model` parameter to
  `claude-sonnet-4.6`.

Both models receive:

- The issue title and description.
- The full spec text.
- The `grep` and `ls` logs generated during `Empirical verification before
  review`.
- The git diff or file paths of any repository changes the spec depends on.
- The shipped `SPEC_RUBRIC.md`.

**Pass condition:** The auditing model returns `[SPEC-APPROVED]`.

- Record the approval in `.review_log.jsonl` using the `CROSS_MODEL_AUDIT`
  approval template in `../review-log-jsonl.md`.

**On cross-model rejection:**

- Log the rejection to `.review_log.jsonl` using the `CROSS_MODEL_AUDIT`
  rejection template in `../review-log-jsonl.md`.
- **Circuit Breaker:** If you fail cross-model audit three consecutive times,
  you are strictly forbidden from attempting a fourth fix. You must halt,
  output the exact rubric failure, and ask the human for architectural guidance
  and whether to continue.
- Fix the spec inline.
- Run a post-fix consistency check across every affected section.
- Commit the updated spec before returning to the self-review loop.
  `git commit -m "spec(<work_item_id>): cr<N> fixes..."`
- Re-run the full review loop from the self-review step.
- The spec may not proceed to plan writing until both reviews pass.
