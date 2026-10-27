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

- Log the rejection with the append CLI described in
  `../shared/review-log-jsonl.md`: `--phase SPEC_REVIEW --verdict REJECTED
  --independence self`, the round number, and one `--finding` per failed
  criterion.
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

## Independent audit

After the spec passes self-review, an independent reviewer must audit it
before planning begins. What the audit needs is independence: fresh context and
no stake in the draft. A different model family helps but is not required.
Load `SPEC_REVIEW_MANIFEST.md` to create the audit context and ensure the
auditor applies the same standards.

**Invocation Syntax:** You must physically invoke the `requesting-code-review`
skill with a fresh-context reviewer. It must not be you, and it must not be a
sub-agent that helped draft or fix the spec.

- **Required:** fresh context. The reviewer gets only the inputs listed below,
  never this conversation or your drafting notes.
- **Preferred:** a different model family, when the harness offers one. If a
  repo-root overlay names the reviewer model, use that model. This skill names
  none.
- Record the result as `independence: "cross-family"` when the reviewer is from
  another model family, otherwise `independence: "fresh-context"`. A
  fresh-context review from the same family is a compliant audit, not a
  substitute. Do not log an excuse for it.

The reviewer receives only:

- The issue title and description.
- The full spec text.
- The `grep` and `ls` logs generated during `Empirical verification before
  review`.
- The git diff or file paths of any repository changes the spec depends on.
- The shipped `SPEC_RUBRIC.md`.

**Same reviewer across rounds:** round 2 and later go back to the same
reviewer (resume or message it) with the spec diff and your response to each
finding. Start a new reviewer only after a rewrite of the spec.

**Pass condition:** The reviewer returns `[SPEC-APPROVED]`.

- Record the approval with the append CLI described in
  `../shared/review-log-jsonl.md`: `--phase INDEPENDENT_AUDIT --verdict
  APPROVED`, the round number, the reviewer model and its `--independence`.

**On independent-audit rejection:**

- Log the rejection with the append CLI: `--phase INDEPENDENT_AUDIT --verdict
  REJECTED`, the round number, the reviewer model, its `--independence`, and
  one `--finding` per blocking finding.
- **Circuit Breaker:** If you fail independent audit three consecutive times,
  you are strictly forbidden from attempting a fourth fix. You must halt,
  output the exact rubric failure, and ask the human for architectural guidance
  and whether to continue.
- Fix the spec inline.
- Run a post-fix consistency check across every affected section.
- Commit the updated spec before returning to the self-review loop.
  `git commit -m "spec(<work_item_id>): cr<N> fixes..."`
- Re-run the full review loop from the self-review step.
- The spec may not proceed to plan writing until both reviews pass.
