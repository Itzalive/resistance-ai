# Steps 2 to 6: the amendment

Load at step 2. The commands are in `tools.md`; the files and the change file's life in `records.md`.

## Step 2: the baseline check

Run the `deps-command` again, then `export` and `check` (both skipped while the model folder is empty). A `check` exit 1 is a 2a finding; exit 2 stops the run with the tool's error. Propose the groups the run touches; the owner approves the list. In a later-stage run, the gate is read from `changes/`: the model is approved when every change file's `approved` is set.

**2a. Is the affected model current?** For every modelled element the run touches, its relationships and its gap entries, look for:
- an invalid model: it doesn't load, `c4.c4` differs from the shipped spec, or `cycles` reports a group;
- a `code` value that matches no module;
- a breach not in the gap file (drift);
- a gap entry that no longer matches (its breach was fixed);
- a relationship reported "not yet reached" that the code now has (note it only).

Read an `Unmapped code` module and a "not yet reached" relationship together: a module renamed under an element is a stale `code` value, not new code. Each finding gets its own recommendation from the allowed outcomes (`SKILL.md`, "Drift is a finding"), and the owner decides each. Change nothing before that; the chosen outcomes are written at step 3, after the before copy, so the change file records them.

**2c. Does the request stand?** (later-stage run) Only after 2a, judge the diff request. Refuse a request that changes a cross-cutting decision in part or for one bound element, or changes a product rule; recommend the whole change, or the epic, instead. A refused request ends the diff, not the run: the run carries on with the 2a outcomes, writes its change file (its `summary` says what was refused and why, `rejected` holds the request), and goes through step 7.

**2b. How much to baseline?** In a baseline run, ask nothing: the coverage is the whole repository; load `baseline-run.md`. In an epic or later-stage run whose touched groups are not modelled: one question with a recommendation and its counts (`ARCH_STANDARDS.md`), then load `baseline-run.md`. The baseline is its own diff through steps 3 to 7; after its `[ARCH-APPROVED]` it asks no decided-targets question and the outer run resumes at step 3, taking its own before copy.

## Step 3: write the draft

The before copy first (`records.md`). Then write the diff into the files:
- the `.c4` changes, every element the diff adds placed in at least one area view (`view area-<name>`);
- decisions and holes in `decisions/<group>.json`; contracts in `contracts/<group>.json`; every improvement seen and not made as a hole or a proposed decision;
- gap entries in `known-gap.json`.

Then run, in order: `change`; the coverage entries; `export`; `check`; `architecture-docs build`. Nothing is presented before this has run, and each later step is presented from what it wrote.

## Steps 4 to 6

Each of these is its own reply, ending in its own approval question; send nothing from the next step with it, and present an empty step ("no cross-cutting decision in scope: approve?") on its own too.

- **Step 4, cross-cutting decisions:** each decision with `obligations` that binds a changed element, and every principle, with options and a recommendation, presented from its record and approved separately.
- **Step 5, the diff:** presented from the change document (`generated/changes/<id>.md`) and the area documents it touches, with the elements' `rules` as the rule map. A diff that needs an edge node's inside goes back to 2b for that area.
- **Step 6, the known gap:** from the written `check`: each breach the diff adds with a proposed reason, closed entries removed, renamed ends re-keyed. The owner accepts or rejects each.

Whatever the owner changes in steps 4 to 6 is edited into the files, and `change` (same `--name` and `--date`), `check` and `build` run again.

## What the owner is shown

The generated documents only: the change document, the area documents of every area the run touches, and the improvement list (`generated/improvements.md`). Never the record files, and never your own summary in their place. From step 4 on, each approval request shows that turn's `build` output and names the documents to read.
