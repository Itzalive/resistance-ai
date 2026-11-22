# Architecture review manifest

Used by the self-review and by the independent auditor, with the inputs `review-workflow.md` lists. Work out the scopes, run the checks below, then grade every item in `ARCH_RUBRIC.md` against its scope.

## Scopes

- **changed:** the elements the run's change file lists as added, changed or removed; every relationship with one of them at either end; every decision, hole and contract the change file lists; every decision with `obligations` that binds a changed element; and every principle.
- **whole:** every element, relationship, record and gap entry in the model.

## Checks

- **Rule map:** each element's `rules` metadata in `export`.
- **Coverage and unmapped modules:** `coverage.json`, in `export` `coverage`.
- **Cycles:** `cycles` on the written model reports `0 relationships to leave out in 0 groups, 0 too large`.
- **Roots:** no element's `code` is a root (the overlay's `roots`, or the shared prefix without them), unless the whole repository is baselined.
- **Edge nodes:** each `edge_nodes` element in `coverage.json` is a `component` with `code`, no children and no `rules`, and is in no decision's `binds` or `owner` and no contract's `owner` or `bound`.
- **The change file:** its `check.output` equals the output of a `check` run now on the same files, and `change --compare` with the run's before copy prints `same` (exit 0). A stale or hand-made change file fails both.
- **Documents:** `architecture-docs check` exits 0.
- **Areas:** every element id in `export` `elements` appears in some `areas[].elements`.
- **The dependency file** (audit only): the independent import scan of `review-workflow.md`.

## Grading

Grade every `ARCH_RUBRIC.md` checkbox against its tagged scope. Report:
- each failed item, with the element, relationship, record or gap entry it names and the exact correction;
- the scopes you worked out;
- the verdict: `[ARCH-REVIEW-PASSED]` only when every item passes, otherwise `[ARCH-REVIEW-FAILED]`.
