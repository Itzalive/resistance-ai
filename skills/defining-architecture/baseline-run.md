# Baseline run

Load this file only at step 2b, once the owner has answered the coverage question. A baseline describes what the code **is**, not what it should be, for the coverage step 2b chose. The terms (repository module, top-level module group, edge node) are defined in `ARCH_STANDARDS.md`.

## Build the baseline

1. **Folder.** When the model folder is empty, create it and copy the shipped spec `<skills-dir>/shared/architecture/c4.c4` into it unchanged. Never edit `c4.c4`.
2. **Components.** One `component` per top-level module group inside the coverage, with `code` set to the group's prefix and no `rules`. A baseline adds no containers and no systems; only an epic's diff adds those.
3. **Edge nodes.** One edge node per neighbour group outside the coverage that has a code edge to or from it: a `component` with `code` set to that group's prefix, no children, no `rules`, and no part in any cross-cutting decision.
4. **Relationships.** One relationship per element pair with at least one code edge between them, edge nodes included. Edges from an edge node into unmodelled code point at no element, and the tool ignores them.
5. **Cycles.** Where the groups' code edges form a cycle of any length, leave one relationship of each cycle out of the model and record it in `known-gap.json` with the reason `cycle in current code`. Recommend the relationship with the fewest module edges; the owner chooses in step 5. A cycle is never left out of both the model and the gap file.
6. **Coverage record.** In `architecture.md` under "Baseline coverage", list the baselined groups, the edge nodes, the run that added each, and the coverage answer with the counts behind it (repository modules and top-level groups).
7. **Unmapped modules.** A repository module equal to the shared prefix gets an element only when the whole repository is baselined; otherwise list it under "Unmapped modules" with the reason `shared prefix`.

## An edge node's group gets baselined

When a run's diff needs an edge node's inside, it comes back here (step 2b) for that area; that baseline is approved on its own, then the run returns to step 3. When a run baselines a group that is an edge node, the edge node becomes that group's `component`: move its entry from the edge-node list to the baselined groups. From then on it may have children and `rules`. Extending coverage can turn up breaches an edge node hid; they appear as new `check` breaches and go through step 5.

## Then

The baseline goes through steps 3 to 6 like any diff: `check` against it (expect only the cycle entries as known breaches), its own review, its own `[ARCH-APPROVED]`, and review-log entries whose `--reason` starts `baseline`. Only after that approval does the outer run resume at step 3, with `check` re-run against the approved baseline. An epic's diff then amends the baseline into the target, so its diff and its new gap entries show what the epic forbids that the code does today.
