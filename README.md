# resistance-ai

Canonical repository for Superpowers-derived skills and agents imported from
`vendor/obra-superpowers/`.

## Bootstrap

Clone the repo, then initialize the nested vendor submodule before running importer
or validation tooling:

```bash
git submodule update --init --recursive vendor/obra-superpowers
```

## Layout

- `skills/` - imported skill directories with support files preserved
- `agents/` - imported top-level agent markdown files
- `consolidation/consolidation_overrides.json` - local pruning policy overrides for
  intentionally omitted imported files
- `catalog/catalog_index.json` - minimal unified index for imported skills and agents
- `catalog/non_skill_inventory.json` - classification output for vendor repo surfaces
  outside `skills/` and `agents/`

## Packaging and consumption

- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` are the canonical
  Copilot CLI plugin metadata for this repository
- `package.json` is metadata-only packaging for VS Code discovery/publishing workflows
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
git submodule update --init --recursive vendor/obra-superpowers
copilot plugin install .
```

The marketplace metadata lives in `.claude-plugin/marketplace.json`, and the
plugin manifest lives in `.claude-plugin/plugin.json`.

### VS Code

This repository does not currently ship a standalone VS Code extension. Its
`package.json` is metadata-only packaging for VS Code discovery and publishing
workflows, and it is currently marked `private`.

To use this repository from VS Code today, consume it from a parent repository
or extension workspace:

```bash
git submodule add https://github.com/Itzalive/resistance-ai.git resistance-engine
git submodule update --init --recursive resistance-engine/vendor/obra-superpowers
```

There is no public VS Code Marketplace install flow for this repository yet. If
that changes later, document the Marketplace install path separately instead of
changing the local/submodule flow described above.

## Refresh

Run: `python3 scripts/import_superpowers_catalog.py`

## Provenance

- `provenance/provenance_manifest.json` - authoritative lineage and state for every
  skill and agent
- every manifest file record includes `local_sync_policy`, which defaults to
  `required` and may be set to `pruned` via the override file

Validate the current local tree against the manifest:

Run: `python3 scripts/validate_resistance_engine_provenance.py .`

## Authoring defaults

- `skills/specifying-work-items/SKILL.md` is self-sufficient by default
- `skills/specifying-work-items/SPEC_REVIEW_MANIFEST.md` and `skills/specifying-work-items/SPEC_RUBRIC.md`
  ship the default spec review behavior
- `skills/writing-plans/SKILL.md` is self-sufficient by default
- the self-contained `specifying-work-items` default also carries sharding, source-of-truth
  sync, empirical verification, self-review, and cross-model audit requirements
- the self-contained `writing-plans` default also carries Tabula Rasa ingestion,
  topological TDD, chunking, pre-plan verification, runbook rules, and Unified
  Coherence review requirements
- repo-root `SPEC_DESIGN.md`, `PLAN_WRITING.md`, `SPEC_REVIEW_MANIFEST.md`, and
  `SPEC_RUBRIC.md` are optional overlays only
- overlays may tighten or extend the shipped defaults, but may not weaken them
- malformed or contradictory overlays are blocking conditions

## Consolidation overrides

- keep `consolidation/consolidation_overrides.json` in git, even when it is `[]`
- `required` means the imported file must remain present locally
- `pruned` means the imported file should be absent locally while remaining in
  provenance tracking

## Guardrails

- `vendor/obra-superpowers/` remains read-only
- shard 1 owns import and inventory only; divergence tracking belongs to shard 2
- non-skill vendor content is inventoried and classified before any future import
