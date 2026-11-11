# Architecture review manifest

Used by the self-review and by the independent auditor. Work out the scopes, run the checks below, then grade every item in `ARCH_RUBRIC.md` against its scope.

## Inputs

- The model folder: the `.c4` files, `architecture.md`, `known-gap.json`.
- `export` output (`node <skills-dir>/shared/scripts/architecture-delta.mjs export --repo . --model <model>`).
- `check` output on the written model, from this run.
- The trigger: the epic (its capabilities and business rules), or the diff request.
- The run's diff: the decision-log entry, or `git diff` of the model folder.

## Scopes

- **changed:** the elements the diff adds, changes or removes; every relationship with one of them at either end; and every cross-cutting decision whose bound-elements list includes one of them.
- **whole:** every element, relationship, decision and gap entry in the model.

## Cycle check

Build the reachability graph from `export`'s relationships. Each relationship counts for its endpoints and for all their ancestors: `a.x -> b.y` means `a.x`, `a` and any parent above them reach `b.y`, `b` and any parent above them. Two siblings (elements with the same parent) form a cycle when each reaches the other, directly or through others. A relationship left out and recorded as `cycle in current code` in `known-gap.json` is not in the graph.

## Shared-prefix check

Take the longest prefix, at the separator, shared by every repository module in the dependency file. An element whose `code` equals it fails, unless "Baseline coverage" says the whole repository is baselined.

## Edge-node check

For each edge node listed under "Baseline coverage", confirm in `export` that it:
- is a `component`;
- has `code`;
- has no children and no `rules`;
- is in no decision's bound-elements list.

## What to quote from `check`

The decision-log entry for this run quotes `check`'s full text output: the new breaches, known breaches, not yet reached, unmapped code and the summary line, with the exit code. A summary line alone is not enough. Confirm the quoted output matches a `check` you run now on the same files. If they differ, the entry is stale.

## Grading

Grade against every `ARCH_RUBRIC.md` checkbox, each against its tagged scope. Report:
- each failed item, with the element, relationship, decision or gap entry it names and the exact correction;
- the scopes you worked out (the changed elements and decisions);
- the verdict: `[ARCH-REVIEW-PASSED]` only when every item passes, otherwise `[ARCH-REVIEW-FAILED]`.
