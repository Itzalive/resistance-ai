# Architecture rubric

Grade every item. Each item is binary. The tag in brackets gives its scope, worked out as `ARCH_REVIEW_MANIFEST.md` describes. An item that fails names the element, relationship, decision or gap entry and the correction.

## What review checks

- [ ] Every Must rule has exactly one owning element in the rule map and in the elements' `rules` metadata. [whole]
- [ ] Every cross-cutting decision in scope is found, taken whole for every capability that depends on it, and holds only product-level content: name, owning element, bound elements and capabilities, obligations, compatibility rule. [changed]
- [ ] No cycles: no two sibling elements reach each other, directly or through others. [whole]
- [ ] Every `code` value equals a repository module or a prefix of one at the separator. [changed]
- [ ] This run's decision-log entry quotes a `check` run's output, and every breach that output reports is in `known-gap.json` with a reason. [whole]
- [ ] Inside the baselined coverage, every unmapped module is mapped or listed under "Unmapped modules" with a reason. [whole]
- [ ] No element's `code` is the shared prefix, unless the whole repository is baselined. [whole]
- [ ] Every edge node listed under "Baseline coverage" is a `component` with `code`, no children and no `rules`, and is in no decision's bound-elements list. [whole]
- [ ] No mechanism detail (functions, schemas, field lists, algorithms) and no new product rules. [changed]
- [ ] The model loads with no errors (`export` exits 0). [whole]

## Hard rules

- [ ] No product rule appears that the epic doesn't have. [changed]
- [ ] Every breach `check` reports is in `known-gap.json`; none was resolved by changing code. [whole]
- [ ] `c4.c4` in the model folder is byte-identical to the shipped spec. [whole]
- [ ] No code file changed in this run. [whole]
- [ ] No drift breach was made legal by adding a relationship without the owner choosing a target change over a gap entry. [changed]
- [ ] Every gap reason is one sentence saying why the breach exists today and what closes it, or exactly `cycle in current code`. [changed]
- [ ] The decision log only grew: no earlier entry was edited or removed. [whole]
