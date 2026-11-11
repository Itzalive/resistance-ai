# resistance-ai

Canonical repository for the resistance-engine skills and agents. They began as a
fork of [obra/superpowers](https://github.com/obra/superpowers) and are now maintained
independently.

## Layout

- `skills/` - skill directories with their support files
- `agents/` - top-level agent markdown files

## Packaging and consumption

- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` are the canonical
  Copilot CLI plugin metadata for this repository
- `package.json` remains the metadata surface for VS Code discovery/publishing workflows
  and now also declares the Pi package manifest for skill discovery
- parent repositories should consume this project via a `resistance-engine/` git
  submodule and update the gitlink when adopting canonical changes

## Installation

### GitHub Copilot CLI

Install from the repository-hosted marketplace:

```bash
copilot plugin marketplace add Itzalive/resistance-ai
copilot plugin install resistance-engine@resistance-dev
```

Install directly from a local checkout:

```bash
git clone https://github.com/Itzalive/resistance-ai.git
cd resistance-ai
copilot plugin install .
```

The marketplace metadata lives in `.claude-plugin/marketplace.json`, and the
plugin manifest lives in `.claude-plugin/plugin.json`.

### Pi

Install from GitHub:

```bash
pi install git:github.com/Itzalive/resistance-ai
```

Install from a local checkout:

```bash
git clone https://github.com/Itzalive/resistance-ai.git
cd resistance-ai
pi install .
```

Pi discovers this repository as a package via `package.json` and loads the shared
`skills/` tree. The Claude/Copilot plugin metadata remains unchanged.

### VS Code

This repository does not currently ship a standalone VS Code extension. Its
`package.json` still provides VS Code discovery and publishing metadata, is
currently marked `private`, and also carries the Pi package manifest.

To use this repository from VS Code today, consume it from a parent repository
or extension workspace:

```bash
git submodule add https://github.com/Itzalive/resistance-ai.git resistance-engine
```

There is no public VS Code Marketplace install flow for this repository yet. If
that changes later, document the Marketplace install path separately instead of
changing the local/submodule flow described above.

## Workflow

```
specifying-epics -> defining-architecture -> planning-features -> specifying-features
  -> specifying-work-items (per shard) -> writing-plans -> execution -> code review -> finishing
```

| Stage | What it decides | Approval tag |
|---|---|---|
| `specifying-epics` | Product scope: users, rules, ACs, metrics, capabilities | `[EPIC-APPROVED]` |
| `defining-architecture` | The target architecture model across the epic, cross-cutting decisions, the known gap | `[ARCH-APPROVED]` |
| `planning-features` | The features and their order: decisions first, risky questions early, then value to cost | `[FEATURES-APPROVED]` |
| `specifying-features` | One feature: questions answered, feature ACs, architecture delta, shard map, eval plan, costing | `[FEATURE-APPROVED]` |
| `specifying-work-items` | One work item (a shard of a feature), specified just in time | `[SPEC-APPROVED]` |
| `writing-plans` and execution | The plan, its tasks, reviews and survivability | plan alignment check |

Short paths: one clear work item goes straight to `specifying-work-items`; an epic that
ships as one feature skips `planning-features`.

The architecture model is LikeC4 (`.c4` files). The delta tool that compares it with the
code, `skills/shared/scripts/architecture-delta.mjs`, needs Node. Every architecture step
is skipped in a repository that has no model.

## Authoring defaults

- `skills/specifying-work-items/SKILL.md` is self-sufficient by default
- `skills/specifying-work-items/SPEC_REVIEW_MANIFEST.md` and `skills/specifying-work-items/SPEC_RUBRIC.md`
  ship the default spec review behavior
- `skills/writing-plans/SKILL.md` is self-sufficient by default
- the self-contained `specifying-work-items` default also carries sharding, source-of-truth
  sync, empirical verification, self-review, and independent audit requirements
- the self-contained `writing-plans` default also carries Tabula Rasa ingestion,
  topological TDD, rule-based sizing, the caller and test sweep, tier tags and
  checkpoints, pre-plan verification, runbook rules, and alignment check requirements
- repo-root `SPEC_DESIGN.md`, `PLAN_WRITING.md`, `SPEC_REVIEW_MANIFEST.md`, and
  `SPEC_RUBRIC.md` are optional overlays only
- overlays may tighten or extend the shipped defaults, but may not weaken them
- malformed or contradictory overlays are blocking conditions
