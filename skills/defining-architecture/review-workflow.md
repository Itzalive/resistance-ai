# Defining-Architecture Review Workflow

Load this file at step 6, once the run's files are written in the model folder.

## Self-review

The review is not optional and may not be abbreviated.

1. Load `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md`.
2. If repo-root overlays exist, apply them only where they tighten the defaults.
3. Run `export` and `check` on the written model, and work out the "changed" and "whole" scopes as the manifest says.
4. Grade every rubric item against its scope.
5. Output `[ARCH-REVIEW-PASSED]` or `[ARCH-REVIEW-FAILED]`, with each failed item and the exact correction.

Log every round:

```bash
python <skills-dir>/shared/scripts/review-log.py append --item-id <id> --skill defining-architecture --phase ARCH_REVIEW --round <n> --verdict APPROVED|REJECTED --orchestrator <model> --reviewer-model <model> --independence self --reason "<reason>" [--finding <severity>:<kind>:<text> ...]
```

The `--reason` starts `epic`, `later-stage: <stage>` (the stage that asked) or `baseline`. Use `--log <path>` only when the caller names a different review log.

**On failure:** fix the model files, re-run `check`, and review again from the start. **Circuit breaker:** after 5 consecutive failed self-reviews, stop. Report the failing rubric item to the owner and ask how to continue.

## Independent audit

After self-review passes, a reviewer with fresh context and no stake in the draft audits it. A different model family helps but isn't required.

The reviewer receives only:
- the trigger (the epic, or the diff request);
- the model folder's files and the run's `check` output;
- `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md`.

Never give it this conversation or your drafting notes. Round 2 and later go back to the same reviewer, with the diff and your answer to each finding.

Log every round:

```bash
python <skills-dir>/shared/scripts/review-log.py append --item-id <id> --skill defining-architecture --phase INDEPENDENT_AUDIT --round <n> --verdict APPROVED|REJECTED --orchestrator <model> --reviewer-model <reviewer model> --independence fresh-context --reason "<reason>" [--finding <severity>:<kind>:<text> ...]
```

Use `--independence cross-family` when the reviewer is from another model family.

**Circuit breaker:** after 3 consecutive failed audits, stop and ask the owner how to continue.

## Owner approval

Once the audit passes, present the owner with:
- the diff;
- the `check` output;
- the decision-log entry;
- both review verdicts.

Ask for `[ARCH-APPROVED]`. Only the owner gives it. The run is not finished until they do. If the owner asks for changes, make them and go back through self-review and the audit.

## Work-item note

After `[ARCH-APPROVED]`, append one note to the triggering work item (the epic, or the stage's work item). The note is append-only; never edit or delete an earlier one. It records:
- what the run changed;
- the decision-log entry's date;
- the `check` summary line;
- the next stage (the handoff in `SKILL.md`).

Use the place the caller names when it names one, for example a file instead of the tracker.
