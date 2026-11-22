# Defining-Architecture Review Workflow

Load at step 7, once step 3 has written the run's files and steps 4 to 6 are approved.

## Inputs

The self-review and the audit work from:
- the model folder: the `.c4` files, `known-gap.json`, the records;
- `export`, this run's `check`, `cycles`, `change --compare` with the run's before copy, and `architecture-docs check` (`tools.md`);
- the run's change file;
- the trigger (the epic, or the diff request);
- read-only access to the repository source, the dependency file and the `deps-command`;
- the run's before copy, or a note that it has none.

## Self-review

The review is not optional and may not be abbreviated.

1. Load `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md`.
2. If repo-root overlays exist, apply them only where they tighten the defaults.
3. Run the tools above on the written model, and work out the "changed" and "whole" scopes as the manifest says.
4. Grade every rubric item against its scope.
5. Output `[ARCH-REVIEW-PASSED]` or `[ARCH-REVIEW-FAILED]`, with each failed item and the exact correction.

Log every round:

```bash
python <skills-dir>/shared/scripts/review-log.py append --item-id <id> --skill defining-architecture --phase ARCH_REVIEW --round <n> --verdict APPROVED|REJECTED --orchestrator <model> --reviewer-model <model> --independence self --reason "<reason>" [--finding <severity>:<kind>:<text> ...]
```

The `--reason` starts `epic`, `later-stage: <stage>` or `baseline`. Severities: `critical`, `important`, `minor`. Kinds: the shared ones (`missed-caller`, `weak-test`, `plan-hole`, `spec-hole`, `real-bug`, `slip`, `wording`) and `model-drift` (the model states something the code does not do, or a description states a target as fact), `deps-defect` (the dependency file is wrong or incomplete), `unsourced` (a reason or evidence claim has no source, or its source does not say it). Use `--log <path>` only when the caller names a different review log. A `REJECTED` verdict needs at least one `--finding`.

**On failure:** fix the files, run `change`, `check` and `build` again (`records.md`), and review again from the start. **Circuit breaker:** after 5 consecutive failed self-reviews, stop and report the failing item to the owner.

## Independent audit

After self-review passes, a reviewer with fresh context and no stake in the draft audits it. It receives only the inputs above, `tools.md` (to rerun `check`, `cycles`, `change --compare` and `architecture-docs check`), the overlay, `ARCH_REVIEW_MANIFEST.md` and `ARCH_RUBRIC.md`; never this conversation or your notes. Round 2 and later go back to the same reviewer with the diff and your answer to each finding.

**The auditor checks the dependency file by a second method.** It scans the source for imports by its own search over import statements, independent of the `deps-command`, and compares the module edges it finds inside the coverage with the dependency file. An edge it finds that the file lacks is a `deps-defect` finding and fails the audit. Its report names the search it used and how many module edges it compared.

**A `deps-defect` stops the run.** Report the missing edges to the owner with a recommended fix to the `deps-command`; the owner, or a work item, makes it, since this skill changes no file outside the model folder. Then resume at step 2, keeping the before copy.

Log every round with `--phase INDEPENDENT_AUDIT --independence fresh-context` (or `cross-family` for a reviewer of another model family), otherwise as above. **Circuit breaker:** after 3 consecutive failed audits, stop and ask the owner.

## Owner approval

Once the audit passes, show the owner the documents `amendment.md` lists, with both review verdicts, and ask for `[ARCH-APPROVED]`. Only the owner gives it; the run is not finished until they do. If the owner asks for changes, make them and go back through self-review and the audit. After approval, finish the change file as `records.md` says.

## Work-item note

After `[ARCH-APPROVED]`, append one note to the triggering work item (the epic, or the stage's work item), or to the place the caller names. It is append-only. It records what the run changed, the change id, the `check` summary line, and the next stage (`SKILL.md`, Handoff). A baseline run's note comes before its decided-targets question (`baseline-run.md`).
