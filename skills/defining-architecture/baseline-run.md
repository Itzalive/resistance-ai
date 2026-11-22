# Baseline run

Load at step 2b, or for a baseline run. A baseline describes what the code **is**, not what it should be. A baseline run (a repository with no model) covers the whole repository and asks no coverage question; a baseline nested in an epic or later-stage run covers what step 2b chose. Groups come from `roots` (`ARCH_STANDARDS.md`).

## What a baseline holds

1. **Folder.** When the model folder is empty, create it and copy the shipped spec `<skills-dir>/shared/architecture/c4.c4` into it unchanged. Never edit `c4.c4`.
2. **Structure.** One `system` for the repository, and a `container` for each part the repository builds or ships separately (a server, an app, a library kept apart), each named in the run's step 2 proposal. One `component` per top-level module group inside the coverage, with `code` set to the group's prefix and no `rules`; where a group's modules are depended on from different directions, `code` values below the group split it into several components.
3. **Outside systems.** An `external` element for each outside system the code calls, and a runtime link (a relationship with a kind other than `uses`) for each call that is not an import.
4. **Relationships.** One import relationship per element pair with at least one code edge between them, edge nodes included. Edges from an edge node into unmodelled code point at no element, and the tool ignores them.
5. **Descriptions.** Each element's description says what the part does today. A description never states a target as fact.
6. **Records.** Decisions recovered from the code and earlier documents, each with `evidence` and `sources`; structure with no reason found as a hole with evidence `search`; contracts with outside systems (`records.md`).
7. **Edge nodes.** One per neighbour group outside the coverage that has a code edge to or from it (`ARCH_STANDARDS.md`, Terms).
8. **Views.** One area view (`view area-<name> of <container>`) scoped to each container, and area views grouping components for reading, so every element is in at least one area.
9. **Unmapped modules.** A module equal to a root gets an element only when the whole repository is baselined; otherwise it is unmapped with `root prefix`. A module under no root is unmapped with `outside roots`.

## Nesting

Every relationship counts for every ancestor of both its ends, so a parent element lifts its children's relationships onto itself and its siblings. A component's parent is a `system` or `container`. Any other element may be a parent only when `cycles` reports no group among that parent's siblings. Groups for reading are area views, never parent elements.

## Cycles

Run `cycles` on the drafted model (`tools.md`) and propose its leave-out set; the owner chooses in step 6. A group reported `too large` is chosen by hand with the owner. After leaving the relationships out, run `check`: each new breach it reports goes into `known-gap.json` with the reason `cycle in current code`, keyed by the elements its modules map to (which may differ from the left-out relationship's ends). A cycle is never left out of both the model and the gap file.

## Coverage

Write `coverage.json` after the change file (`records.md`): the answer, the module and group counts, each baselined group and edge node with this run's change id, and the unmapped modules with reasons.

## An edge node's group gets baselined

When a diff needs an edge node's inside, the run comes back here for that area. The edge node becomes that group's `component`: move its entry from `edge_nodes` to `baselined`. From then on it may have children and `rules`. Extending coverage can turn up breaches an edge node hid; they appear as new `check` breaches and go through step 6.

## Then

The baseline goes through steps 3 to 7 like any diff, with its own change file (`--run baseline`), its own review and its own `[ARCH-APPROVED]`, and review-log entries whose `--reason` starts `baseline`. A nested baseline then hands back to the outer run, which resumes with a fresh `check` against it.

## Decided targets (baseline run only)

After a baseline run's `[ARCH-APPROVED]`, ask the owner once for targets already decided that the code does not meet yet (for example, one part being the only caller of another). A target the owner stated earlier in the run is put forward as the recommended answer. Each answer becomes the first amendment: a later-stage run whose diff request is the owner's answer, quoted, with `asked_by` `owner`, through steps 2 to 7, its breaches gapped with reasons. With no answer, the baseline run ends. A baseline nested in another run does not ask: the outer run's diff is where its targets are decided.
