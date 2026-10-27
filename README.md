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

## Authoring defaults

- `skills/specifying-work-items/SKILL.md` is self-sufficient by default
- `skills/specifying-work-items/SPEC_REVIEW_MANIFEST.md` and `skills/specifying-work-items/SPEC_RUBRIC.md`
  ship the default spec review behavior
- `skills/writing-plans/SKILL.md` is self-sufficient by default
- the self-contained `specifying-work-items` default also carries sharding, source-of-truth
  sync, empirical verification, self-review, and independent audit requirements
- the self-contained `writing-plans` default also carries Tabula Rasa ingestion,
  topological TDD, chunking, pre-plan verification, runbook rules, and Unified
  Coherence review requirements
- repo-root `SPEC_DESIGN.md`, `PLAN_WRITING.md`, `SPEC_REVIEW_MANIFEST.md`, and
  `SPEC_RUBRIC.md` are optional overlays only
- overlays may tighten or extend the shipped defaults, but may not weaken them
- malformed or contradictory overlays are blocking conditions
