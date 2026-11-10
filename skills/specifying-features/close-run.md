# Close run

Load this file only for a close run: the feature's last shard has merged, and the feature design has `[FEATURE-APPROVED]`.

## Steps

1. **Run the delta on the whole model.** Run the overlay's `deps-command`, then `check` with no `--scope` and no `--shards` (the command is in `FEATURE_STANDARDS.md`, "Running the delta"). Quote the output.
2. **Remove stale entries.** Remove from `<model>/known-gap.json` each entry the tool reports stale. Change nothing else in the model folder.
3. **Write the Close record** in the feature design:
   - each gap entry removed;
   - each gap entry the map says this feature closes that the tool still reports, recorded as **not closed**;
   - the actual cost, from the run records of the feature's shards.
4. **Update the map row:** state `shipped`, and the actual cost.
5. **Owner confirms** the Close record. No review runs.
6. **Hand to `planning-features`** for a re-plan run.

## Rules

- "The shards have merged" is not evidence that a gap entry is closed. Only the tool reporting the entry stale is.
- A new breach is never added to the gap here. Write a diff request and hand it to `defining-architecture`; the Close record notes it.
- Exit 2 stops the run with the tool's error.
- For a one-feature epic, see `FEATURE_STANDARDS.md`: there is no map row and no re-plan, and with a waived, empty model no `check` runs.
