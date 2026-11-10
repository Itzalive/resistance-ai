# Planning-Features Review Workflow

Load this file at step 6, once the map is written.

## Self-review

The review is not optional and may not be abbreviated.

1. Load `FEATURES_REVIEW_MANIFEST.md` and `FEATURES_RUBRIC.md`.
2. If repo-root overlays exist, apply them only where they tighten the defaults.
3. Run the manifest's checks and grade every rubric item against its scope.
4. Output `[FEATURES-REVIEW-PASSED]` or `[FEATURES-REVIEW-FAILED]`, with each failed item and the exact correction.

Log every round:

```bash
python <skills-dir>/shared/scripts/review-log.py append --item-id <id> --skill planning-features --phase FEATURES_PLAN_REVIEW --round <n> --verdict APPROVED|REJECTED --orchestrator <model> --reviewer-model <model> --independence self --reason "<reason>" [--finding <severity>:<kind>:<text> ...]
```

The `--reason` starts `planning` or `re-plan`. Use `--log <path>` only when the caller names a different review log.

**On failure:** fix the map and review again from the start. **Circuit breaker:** after 5 consecutive failed self-reviews, stop. Report the failing rubric item to the owner and ask how to continue.

## Independent audit

After self-review passes, a reviewer with fresh context and no stake in the draft audits it. A different model family helps but isn't required.

The reviewer receives only:
- the inputs the manifest lists;
- `FEATURES_REVIEW_MANIFEST.md` and `FEATURES_RUBRIC.md`.

Never give it this conversation or your drafting notes. Round 2 and later go back to the same reviewer, with the diff and your answer to each finding.

Log every round:

```bash
python <skills-dir>/shared/scripts/review-log.py append --item-id <id> --skill planning-features --phase INDEPENDENT_AUDIT --round <n> --verdict APPROVED|REJECTED --orchestrator <model> --reviewer-model <reviewer model> --independence fresh-context --reason "<reason>" [--finding <severity>:<kind>:<text> ...]
```

Use `--independence cross-family` when the reviewer is from another model family.

**Circuit breaker:** after 3 consecutive failed audits, stop and ask the owner how to continue.

## Owner approval

Once the audit passes, present the owner with:
- the features in order, with the reasoning per rule;
- the questions and where each is answered;
- both review verdicts.

Ask for `[FEATURES-APPROVED]`. Only the owner gives it. The run is not finished until they do. If the owner asks for changes, make them and go back through self-review and the audit.

## Work-item note

After `[FEATURES-APPROVED]`, append one note to the epic's work item. The note is append-only; never edit or delete an earlier one. It records:
- the features in order;
- the split-out questions and what each runs before or alongside;
- the next stage (the handoff in `SKILL.md`).

Use the place the caller names when it names one, for example a file instead of the tracker.
