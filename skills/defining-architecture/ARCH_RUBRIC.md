# Architecture rubric

Grade every item. Each item is binary. The tag in brackets gives its scope, worked out as `ARCH_REVIEW_MANIFEST.md` describes. An item that fails names the element, relationship, record or gap entry and the correction.

## What review checks

- [ ] Every Must rule has exactly one owning element in the elements' `rules`. Not graded for a baseline run, which assigns no rules. [whole]
- [ ] Every cross-cutting decision in scope (a decision with `obligations` binding a changed element, and every principle) is found, taken whole for every part it binds, and holds only product-level content. [changed]
- [ ] No cycles: `cycles` reports 0 groups. [whole]
- [ ] Every `code` value equals a repository module or a prefix of one at the separator. [changed]
- [ ] The run's change file quotes a `check` run: its `check.output` equals a `check` run now, and every breach that output reports is in `known-gap.json` with a reason. [whole]
- [ ] `change --compare` with the run's before copy exits 0. [changed]
- [ ] Inside the coverage, every unmapped module is mapped or listed in `coverage.json` `unmapped` with a reason. [whole]
- [ ] No element's `code` is a root, unless the whole repository is baselined. [whole]
- [ ] Every edge node in `coverage.json` is a `component` with `code`, no children and no `rules`, and is in no decision's `binds` or `owner` and no contract's `owner` or `bound`. [whole]
- [ ] Every improvement the run noted is a hole or a proposed decision. [changed]
- [ ] `architecture-docs check` exits 0. [whole]
- [ ] Every element is in at least one area in `export` `areas`. [whole]
- [ ] No element description states a target as fact. [changed]
- [ ] No mechanism detail (functions, schemas, field lists, algorithms) and no new product rules. [changed]
- [ ] The model loads with no errors (`export` exits 0). [whole]

## Hard rules

- [ ] No product rule appears that the epic doesn't have. [changed]
- [ ] Every breach `check` reports is in `known-gap.json`; none was resolved by changing code. [whole]
- [ ] `c4.c4` in the model folder is byte-identical to the shipped spec. [whole]
- [ ] No code file changed in this run. [whole]
- [ ] No drift breach was made legal by adding a relationship without the owner choosing a target change over a gap entry. [changed]
- [ ] Every gap reason is one sentence saying why the breach exists today and what closes it, or exactly `cycle in current code`. [changed]
- [ ] The audit's independent import scan found no edge the dependency file lacks. [whole; audit only, not graded in self-review]
