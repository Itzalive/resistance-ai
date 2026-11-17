# First run of defining-architecture: a whole-repository baseline (November 2026)

Source: one downstream repository, on version 0.3.0 of the skill. The run was a baseline on a repository with no model: a Python server, an owned Python library kept as a submodule, eval and script packages, and an Android app. This was the first time the skill was used outside its own tests.

## 1. Data

| Measure | Value |
|---|---|
| Repository modules | 351 (232 Python, 119 Kotlin), tests left out |
| Roots | 6 Python roots and one Kotlin package tree; no shared prefix |
| Model written | 91 elements: 1 system, 5 containers, 73 components, 12 outside systems |
| Relationships | 367 from imports, 33 runtime links |
| Known gaps | 14, all cycles in current code |
| Shared contracts recorded | 25 |
| Decisions recovered with reasons | 112, plus 27 holes |
| Research | 8 subagent passes over code and about 190 earlier specs |
| Review | self-review passed; independent audit failed round 1, passed round 2 |
| Source check of the recovered decisions | 4 of 139 rows wrong, 17 weakly sourced |

## 2. What worked

- **The delta tool.** `export` and `check` behaved as specified on a model of this size, and the exit codes were enough to drive the run.
- **The independent audit.** It found the one serious defect of the run (F1), which the self-review and the tool both passed.
- **Cycles as the baseline's gap.** Each of the 14 entries came down to one or two imports in an odd direction, which made them a usable work list.
- **`code` prefixes at module level.** Mapping below the package let a package be modelled as several components where its modules are depended on from different directions.

## 3. Findings

### F1. Nothing verifies the dependency file, and the check is only as good as it

The skill stops without a `deps-command`, ships none, and its rubric says no code file may change. The run had to write one. Its first version lost every import into a package directory with no `__init__.py`: seven element relationships and several cycles were missing, and `check` passed. The audit caught it only because it was asked to look. A second, independent scan of imports is what proved the fixed file complete.

### F2. A baseline as specified cannot hold reasons

A baseline is components and import relationships. It has no containers, no outside systems, no element descriptions and nowhere to record why a part is shaped as it is. The decision log records the alternatives of a run, not standing decisions. A cross-cutting decision may hold a name, an owner, bound elements, obligations and a compatibility rule "and nothing else". The owner's stated need was the opposite: enough reasoning in the model to judge what should change. The run added a decision register, a metadata key linking each element to it, and descriptions.

### F3. The tool treats every relationship as an import

Links that are not imports (HTTP calls between a client app and a server, a push path, calls to outside systems) can only be modelled as ordinary relationships. Between two elements that have code, the tool then reports them as "not yet reached" on every run. The delta tool's spec lists relationship kinds that the check treats differently as future work "only if a real model needs one". This model does.

### F4. Grouping assumes one package tree

Top-level groups are defined from one shared prefix and one `group-depth`. With several roots and two languages there is no shared prefix, and the useful depth differs per root. The coverage rule (small-repository thresholds) gave no usable answer either.

### F5. Nesting and cycles

The review manifest counts a relationship for every ancestor of both ends. A parent element that is not a layer therefore makes its siblings cyclic. The skill does not say so, and grouping components under readable "areas" produced 72 false sibling cycles. Areas had to become views. "Leave out the relationship with the fewest module edges" is also not defined when cycles overlap; the run needed a minimum set computed across each strongly connected group.

### F6. A cycle gap entry cannot say what causes it

The reason must be exactly `cycle in current code`. The imports behind each entry, which are what a reader needs, had to go in a table in the decision log.

### F7. A baseline makes every non-cyclic import legal

Targets the owner had already decided (for example, one component being the only caller of a library) are not expressed by a baseline, and the skill has no step that asks for them. They need an immediate amendment run, or they are forgotten.

### F8. Step order

Steps 3 to 5 (decisions, diff, gap) cannot be presented without writing the model and running `check`, which the skill places in step 6.

### F9. Cross-cutting decisions in a baseline

They are defined by an epic's capabilities. A baseline has none. The run used "two or more elements depend on it" instead, and needed a note field for bindings that exist without an import.

### F10. Review-log finding kinds

The allowed kinds describe code and plan review. None fits "the dependency file was wrong" or "a description states a target as fact".

### F11. Small mismatches

The manifest says `export` lists "relationships"; the tool's key is `allowed`. The baseline rule "one component per group" is too coarse where a package is depended on from several directions.

### F12. Nothing to review with

The owner-approval step hands over `.c4` files, a check output and a Markdown log. At this size that is not reviewable. A one-off page was built: one section per area, each with its diagram, its parts, the decisions and reasons binding those parts, its contracts, holes and gaps. A first version with all diagrams followed by one flat decision table was hard to use; grouping by area fixed it. Diagrams needed implied import arrows hidden, neighbours drawn as context, and runtime links and known gaps drawn differently.

## 4. What the owner asked for next

Documents generated from one model of truth, repeatable, in formats other tools can render, for these purposes:

1. the overall architecture, to be assessed by an AI;
2. the overall architecture, to be assessed by a human architect;
3. documentation for a product team and senior engineers;
4. the architecture of one module, for an AI or a person;
5. an architecture change record: what changed, new decisions, choices not taken, and the model updated with it;
6. ways to improve the architecture;
7. automated checking of architecture breaks.

One document may serve several purposes. The model of truth should be optimised for an AI reader.

## 5. Recommendations

| # | Change | Findings |
|---|---|---|
| R1 | Correct the skill where no new tooling is needed: step order; nesting and cycle guidance with a defined way to choose what to leave out; a step for targets already decided; grouping across several roots; containers, outside systems and module-level mapping in a baseline; verifying the dependency file during audit; review-log finding kinds; the manifest wording. | F1, F2, F4, F5, F7, F8, F10, F11 |
| R2 | Tool: relationship kinds the check ignores, and evidence on gap entries. | F3, F6 |
| R3 | A structured model of truth: decisions, holes, contracts and change records as data files, validated by the tool. Replace the current layout outright and convert. | F2, F9 |
| R4 | Generate a model pack for AI readers: the whole model, or one area with its neighbours. | purposes 1, 4 |
| R5 | Generate an architecture book for human readers, organised by area, as Markdown with Mermaid diagrams; a renderer shipped with the skill turns it into HTML. | F12; purposes 2, 3, 4 |
| R6 | Generate the change record of each run and an improvement list from holes, gaps and decisions not yet fully built. | purposes 5, 6 |
| R7 | A check command for tests and CI, a way to verify a dependency file, and dependency extractors as plug-in strategies, starting with one for Python. | F1; purpose 7 |
| R8 | Release, then convert the downstream baseline to the new layout. | |

Owner decisions on these (2026-11-16): the new layout may replace the old one, since no approved model uses it elsewhere; the skill may be rewritten and split into companion files to keep its main file tight; scripts should be as automated as possible; Markdown with Mermaid is the main document format; the engine ships dependency-file verification, with extractors as optional plug-ins.

Suggested order: R1 and R2 in either order, then R3, then R4 to R6, then R7, then R8.

## 6. Measures to watch

- Audit rounds per run, and whether a failed round was a dependency-file defect.
- New breaches found by a second, independent import scan that `check` missed (target: none).
- Share of recovered decisions a source check finds wrong (this run: 4 of 139).
- Whether an owner can approve from the generated documents alone.
