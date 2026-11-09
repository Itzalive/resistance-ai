# Architecture and features: change plan

Status: approved by the owner on 2026-11-09. Covers every change to resistance-engine.

## Why

Today the flow is `specifying-epics` (product, ends at the product boundary) → work items →
`specifying-work-items` (architecture decided per item) → `writing-plans`. Nothing decides the
architecture across a whole epic, and nothing turns an epic into features. In a multi-feature epic
this shows up as late, unplanned refactors:

- A mid-feature costing spike finds that several items each restate the same rule on separate entry
  paths, and a consolidation item has to be inserted before them.
- The next feature opens with a "shard 0" of behaviour-free refactors (splitting a write path so a
  later shard can dry-run it; one context builder shared by production and the eval that copied it).
- Both spikes reach the same conclusion: a feature's cost is set less by what it adds than by where
  two of its parts must change one tangled function.

The layering that would have prevented most of this (a generic library behind one domain module that
every caller uses) was knowable when the epic started. Seams that only one feature needs are found
when that feature is designed. So the flow needs an architecture step at epic level and an
architecture delta at feature level.

The sequencing part of issue #16 (entry-path count, consolidation first, costing spike) is absorbed
into this work; its step-file restructure of `specifying-epics` is not.

## Terms

- **Epic:** the product scope (rules, ACs, MoSCoW, success metrics), from `specifying-epics`.
- **Capability:** one item of the epic's product breakdown. It owns business rules and ACs and says
  what value it brings (which success metric or MVP criterion it moves). It is a unit of meaning, not
  of delivery.
- **Feature:** one stage of staged value. Features are delivered in sequence so that each one ships
  something measurable and the order gets the most value for the least cost early on. A feature is
  chosen for where it sits in that sequence, not for what its parts have in common, so it can take
  ACs from several capabilities, or only some of one capability's ACs. It has its own goal, success
  metric and eval run, and is delivered as one or more shards. `planning-features` forms and orders
  the features.
- **Cross-cutting decision:** a decision several capabilities depend on (a data model or format, a
  contract, a vocabulary). It is decided once, whole, before the features that need it, even when its
  build is spread across several features.
- **Shard:** one work item inside a feature, specified just in time and planned on its own.
- **Release** keeps its ordinary meaning: shipping a version.

## The flow after this change

```
specifying-epics           product: rules, ACs, metrics, capabilities        [EPIC-APPROVED]
  -> defining-architecture   target C4 model (LikeC4), cross-cutting         [ARCH-APPROVED]
                             decisions taken whole, known gap
  -> planning-features       staged value: features formed and ordered by    [FEATURES-APPROVED]
                             decisions first, direction-changing questions
                             early (high-risk ones split out), value to cost
     -> specifying-features    per feature: its questions answered, design,  [FEATURE-APPROVED]
                               architecture delta,
                               shard map, shard 0, evals, costing
        -> specifying-work-items  per shard, just in time                    [SPEC-APPROVED]
           -> writing-plans -> subagent-driven-development -> ...
```

Short paths stay available:

- A single work item with clear scope goes straight to `specifying-work-items`, as today.
- An epic the owner agrees ships as one feature skips `planning-features` and goes to
  `specifying-features`.
- `defining-architecture` is required for any epic with more than one feature, or any epic whose
  items touch the same module from two or more entry paths. Otherwise the owner may waive it, and the
  waiver is logged.

## Format: LikeC4

The architecture model is LikeC4 DSL (`.c4` files, MIT), written as C4.

- **One C4 specification ships with the engine** (`skills/shared/architecture/c4.c4`): element kinds
  `system`, `container`, `component`, `external`; relationship kind `uses`; tags `#protected`,
  `#layer`, `#generic`, `#eval`; metadata keys `code` (module path or glob the element owns) and
  `rules` (the epic business rules it owns). Every repo uses it unchanged, so every model is C4-shaped
  and portable between repos. Repos may add kinds and tags in their own file, never redefine these.
- **The model is the target.** A `uses` relationship means "may depend on". `#protected` means "only
  elements with a `uses` relationship to it may depend on it". An element with `code` metadata maps to
  code; one without is conceptual.
- **Default location** `architecture/` at the repo root, overridable in the repo's overlay
  (`ARCHITECTURE_DESIGN.md`, same overlay rules as `SPEC_DESIGN.md`).

## Shared tool: architecture delta

`skills/shared/scripts/architecture-delta.mjs` (Node, the `likec4` package's model API
`LikeC4.fromWorkspace`). Language-neutral: the engine never reads source code and never assumes a
language; it only compares the model with a list of dependencies the repo supplies.

- **Input:** the model directory, and a dependency file of `{"edges": [[from_module, to_module], ...]}`.
  Module names are opaque strings to the engine; the model's `code` metadata uses the same names.
- **Where the dependencies come from:** the repo's overlay (`ARCHITECTURE_DESIGN.md`) names the command
  that writes the dependency file, and how module names map to `code` metadata (for example dotted
  module prefixes). The engine ships no language adapters. A repo with no command configured gets
  exit code 2 and a message saying what the overlay must name. (A Python repo might use `grimp`; a
  Kotlin repo a Konsist or Gradle dump. Those live in the repo, not here.)
- **Where `likec4` comes from:** the engine pins `likec4` as a runtime dependency in its
  `package.json`, with `package-lock.json` committed, so Claude Code installs it with the plugin. The
  tool loads it from the plugin's own install first, then from the consuming repo's pinned copy (for
  harnesses that do not install plugin dependencies), and exits 2 with an install hint if neither
  exists. Cost: about 109 MB per plugin version for every user.
- **Output** (JSON and a short text report), each item naming the model elements and code modules:
  - **breaches:** code dependencies with no `uses` relationship, or into a `#protected` element from
    an element not allowed to use it;
  - **not yet reached:** relationships in the model that the code does not have yet;
  - **unmapped code:** modules no element's `code` covers;
  - **shared hot spots:** with `--shards <file>`, model elements inside two or more shards' scopes.
- **Known gap file** `architecture/known-gap.json`: today's accepted breaches. The check fails on a
  breach not in the file and on an entry that no longer matches anything, so the gap only shrinks.
- **Model export for repo checkers:** `architecture-delta.mjs export` writes the model's elements
  (kind, tags, `code`) and allowed `uses` relationships as plain JSON, so a repo can generate its own
  language-specific checks from it (for example import-linter contracts in a Python repo). The
  generator itself belongs to the repo.
- **Exit codes:** 0 clean, 1 new breach or stale gap entry, 2 input error.
- Tests run under the repo's existing `uv run pytest` (fixture models and edge files, the Node script
  called as a subprocess), plus one contract test that the shipped C4 specification parses.

## New skills

Each new skill follows the existing package shape: `SKILL.md`, `*_STANDARDS.md`,
`*_REVIEW_MANIFEST.md`, `*_RUBRIC.md`, `review-workflow.md`, self-review then independent audit, an
owner approval tag, outcomes logged with the review-log CLI, and append-only sync to the work item.
Each is written RED first per `writing-skills`: a baseline pressure scenario run without the skill,
its failures recorded in the skill's evidence file, then the skill, then the scenario re-run.

### defining-architecture (epic level)

- **When:** after `[EPIC-APPROVED]`, before any feature or work item, for epics meeting the rule above.
  Also when an approved model must change (amendment mode, below).
- **Reads:** the approved epic, the repository, the delta tool's output for today's code.
- **Writes:**
  - the target model in `architecture/`: systems, containers and components with `code` and `rules`
    metadata, allowed `uses` relationships, `#protected` and `#layer` tags, and invariants as
    relationship rules (for example "only the orders module uses the payments library"; "evals use
    production builders, never copies");
  - a short architecture document beside it: the decisions and the alternatives rejected (the
    epic's decision log format), and every epic business rule mapped to the element that owns it;
  - **cross-cutting decisions, each taken whole:** every decision two or more capabilities depend on
    (a data model or storage format, a shared contract or API, an id or naming scheme, a vocabulary
    such as kinds or types) is found here and decided once, for every capability that needs it,
    including those built in later features. Each is written up as its own design (one model spec
    covering all its users, not a piece per feature), and the model records which elements it binds.
    A feature may build part of it; no feature may redesign part of it except through amendment mode;
  - `architecture/known-gap.json` from the first delta run, each entry with the feature expected to
    close it (filled in by `planning-features`).
- **Hard rules:** no new product rules (a rule gap goes back to the epic); every Must business rule
  has an owning element; every breach in the gap is listed, none silently allowed; mechanism detail
  stays out (that is the feature's and the work item's job).
- **Review:** manifest checks include rule coverage, every cross-cutting decision found and taken
  whole, no cycles, every `code` path exists, delta run attached. Tag `[ARCH-APPROVED]`.
- **Amendment mode:** a later stage that needs the target changed proposes a model diff; the scoped
  audit covers only the changed elements and their relationships; owner sign-off; logged.

### planning-features (staged value)

- **When:** after `[ARCH-APPROVED]`.
- **Reads** the epic's capabilities (rules, ACs, value, MoSCoW, product dependencies), its success
  metrics and MVP criteria, and the approved model with its cross-cutting decisions and known gap.
- **Forms and orders the features** by these rules, in this priority:
  1. **Decisions first.** Cross-cutting decisions are already taken whole in `defining-architecture`;
     the first feature that builds on one builds its foundation, so later features add to it rather
     than reshape it.
  2. **Answer direction-changing questions early, split by risk.** A question whose answer could change
     the plan (an unproven technique, a cost or quality unknown, a dependency on another party) is
     placed in the feature that needs its answer, as early as that feature allows, and is answered
     when that feature is specified. The risk decides whether it is split out:
     - **Risk great enough to split:** a wrong answer would waste or redo work in other features, or
       change the epic's direction (its capabilities, value order or a cross-cutting decision). Then
       the question becomes its own item (a spike, a measurement or a prototype), answered before
       any feature it could invalidate. Where it is independent of the current value feature (no
       shared files, no result one needs from the other), it runs in parallel with it rather than
       holding it up.
     - **Otherwise:** it stays with its feature and is answered in `specifying-features`, before that
       feature's shard specs.
  3. **Value to cost.** Among what is left, order so that cumulative value per unit of cost is as high
     as possible early: the MVP criteria first, then Musts by value per cost, Shoulds and Coulds last.
  4. **Every feature stands alone:** it ships, it is measured by its own eval run, and it leaves the
     product better even if the next feature never comes.
  5. **Not by commonality.** Capabilities that touch the same code do not share a feature for that
     reason; a feature is a stage of value. Shared code is handled by cross-cutting decisions and by
     each feature's architecture delta.
- **Writes** a feature map and one work item per feature: the epic ACs it delivers (every epic AC in
  exactly one feature, or marked cross-cutting and checked in every feature), its goal and the success
  metric or MVP criterion it moves, the questions it answers, the decisions it builds on, a rough cost
  (from the project's run records where they exist), the eval run that proves it, and the known-gap
  entries it closes. Each open question is listed against the feature that answers it, with its risk
  (what would change if the answer went the other way). A question split out for risk appears as its
  own item, beside the feature it runs alongside, with the decision its answer feeds and the
  features it could change. Per feature, a first count of entry
  paths and of places each rule is implemented today (the #16 signals), so heavy consolidation is
  visible before any feature is designed.
- **Re-planning:** after each feature ships, and whenever a split-out question is answered, the result and
  actual cost are recorded on the map, and the order of the remaining features is re-checked against
  the same rules.
- **Hard rules:** the order is the owner's call; the skill proposes with its reasoning per rule, the
  owner decides. A change to the epic's capabilities or ACs is an epic amendment (scoped audit, owner
  sign-off), never a silent change. Tag `[FEATURES-APPROVED]`.

### specifying-features (one feature)

- **When:** at the start of each feature, before any shard spec.
- **Writes** the feature design:
  - answers to the open questions the feature map gives this feature, each with its evidence (a
    measurement, a reading of the code, a short spike inside this feature). An answer that would
    change another feature or the epic goes back to `planning-features` for re-planning before the
    design continues;
  - behaviour by section, and feature ACs (`AC-F…`), each tracing to the epic ACs it serves;
  - **architecture delta** (mandatory): the delta tool scoped to the feature's elements, giving the
    breaches in scope, shared hot spots across the proposed shards, and copies an eval reads instead
    of production. Each item becomes a shard 0 refactor decided here, or is recorded as left alone
    with the reason. Any change to the target goes through `defining-architecture`'s amendment mode;
  - shard map: shards, which feature ACs each owns, order and why; refactor shards behaviour-free,
    behaviour shards never carrying a refactor;
  - eval plan: the probes each feature AC needs and the one approved eval run;
  - costing (from #16): entry paths per shard and implementations per rule; consolidation first
    when three or more implementations would each be changed; a cost estimate fitted from the
    project's run records (`.run_records.jsonl`); a second reshard request during the feature
    triggers a costing re-check.
- **Hard rules:** no shard spec before `[FEATURE-APPROVED]`; the delta section may not be empty
  without the tool's output showing it clean.
- **After the feature's last shard:** re-run the delta, update `known-gap.json`, and record what the
  feature closed.

## Changes to existing skills

- **specifying-epics:** the epic breaks down into capabilities, not work items, and states the value
  each brings so that `planning-features` can stage them.
  - Deliverable item 13 "Proposed work item breakdown" becomes **"Capabilities"**. Each capability has
    a name, the business rules and ACs it owns (every AC in exactly one capability), the value it
    brings (the success metric or MVP criterion it moves), its MoSCoW, its known product risks, and
    its product dependencies on other capabilities. No technical tasks, and no sizing to "one
    specifying-work-items session": features are formed in `planning-features` and shards in
    `specifying-features`.
  - The epic may state a product value order; `planning-features` treats it as the value input, not
    as the feature order.
  - "When to Use", "Deliverable Artifact" (the must-not list), "Handoff", "Process Flow", the epic
    sharding trigger about the breakdown, the review manifest and rubric checks on the breakdown, and
    the red flags and rationalizations that mention it all change to match. Architecture now belongs to
    `defining-architecture` (epic-wide) or `specifying-work-items` (per item), and the handoff goes to
    `defining-architecture` → `planning-features` instead of straight to work items.
  - The epic stays product-only. Decomposition into features stays a product decision.
  - The step-file restructure from #16 is not part of this work.
- **specifying-work-items:** a shard of a feature reads the feature design and the model; it does not
  re-decide architecture, and a model change goes back through amendment mode. New red flag: "add a
  dependency the model doesn't allow". The refactor-isolation rule is unchanged.
- **writing-plans:** the plan header's Architecture line names the model elements the plan touches;
  plan review runs the delta tool on the plan's caller sweep and rejects a new breach.
- **requesting-code-review / finishing-a-development-branch:** where the repo has a model, the delta
  check runs before merge; a new breach or a stale gap entry blocks finishing.
- **using-resistance-engine** and **README:** the skill list and the flow.
- **Review log:** `defining-architecture`, `planning-features` and `specifying-features` added to the
  CLI's skill enum and the schema doc, with phases `ARCH_REVIEW`, `FEATURES_REVIEW`,
  `FEATURE_REVIEW`; run record gains an optional `feature` field.

## Delivery shards (resistance-engine)

Each shard branches off `feat/architecture-and-releases`, merges back `--no-ff`, and goes to `main`
by one PR at the end.

| # | Shard | Depends on |
|---|---|---|
| 1 | Delta tool: C4 specification, `architecture-delta.mjs` (`check` and `export`), overlay-named dependency command, known-gap handling, tests | — |
| 2 | Review-log enum, phases and run-record field, with tests | — |
| 3 | `defining-architecture` skill (RED baseline first) | 1, 2 |
| 4 | `planning-features` skill (RED baseline first) | 3 |
| 5 | `specifying-features` skill (RED baseline first), absorbing #16's sequencing | 1, 4 |
| 6 | Edits to specifying-epics, specifying-work-items, writing-plans, code review, finishing, index, README | 3–5 |
| 7 | Version bump (minor) and release | 6 |

Shards 1 and 2 are independent and can run in parallel.

## Decisions (owner, 2026-11-09)

1. **#16's step-file restructure of `specifying-epics`** stays on #16 for later. This work only edits
   the sections named above.
2. **The delta tool runs on Node**, using LikeC4's documented model API. Consuming repos need Node.
3. **`defining-architecture` is required** for an epic with more than one feature, or whose items
   touch the same module from two or more entry paths; otherwise the owner may waive it, logged.
4. **Tracking:** one umbrella issue for this plan and one issue per delivery shard. #16's sequencing
   scope (entry-path count, consolidation first, costing spike) moves to the `specifying-features`
   shard; #16 stays open for the step-file restructure.

5. **Language-neutral engine:** the engine ships no language adapters. The repo's overlay names the
   command that writes the dependency file.
6. **`likec4` ships with the plugin** (pinned in the engine's lockfile), with the consuming repo's
   pinned copy as the fallback.

## Checked

- `likec4` 1.60.0 (MIT, 54 packages, no install script; installed with `--ignore-scripts`): from the
  package root, `LikeC4.fromWorkspace(dir, { logger: false })`, `getErrors()` (message, line, range,
  file for unknown references and unknown kinds), `computedModel()`, `elements()` with `id`, `kind`,
  `tags`, `getMetadata()`, and `relationships()` with `source.id`, `target.id`, `kind`, `title` all
  work as described. A small model loads in under 200 ms.
- `@likec4/language-services` alone does not load (a missing `bundle-require` dependency), so the
  full `likec4` package is the one to pin.
