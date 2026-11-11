# planning-features and specifying-features: implementation plan

Spec: `docs/superpowers/specs/2026-11-10-feature-skills-design.md`. Work items #23 and #24.

**Architecture:** two new skill packages of markdown under `skills/`, one sentence added to `skills/defining-architecture/SKILL.md`, and one structure-only contract test. No code path changes.

**Execution:** three tasks, run inline by the coordinator in order, with one code review at the end. There is no trust-boundary change and no behaviour code, so there are no checkpoint reviews and no survivability run.

## Task 1: `planning-features` package (#23)

Files, all new, in `skills/planning-features/`: `SKILL.md`, `replan-run.md`, `FEATURES_STANDARDS.md`, `FEATURES_REVIEW_MANIFEST.md`, `FEATURES_RUBRIC.md`, `review-workflow.md`, `field-evidence.md`.

- `SKILL.md` holds the gates, ordering rules, steps, hard rules and handoff from the spec's `planning-features` section, in at most 1,000 words.
- `FEATURES_STANDARDS.md` holds the map's format, the split-out test, the signals, cost fitting, work items and `close_by`.
- `FEATURES_RUBRIC.md` holds each review check of the spec as a binary item.
- `field-evidence.md` holds baseline rows B1, B2, B7, B8, B9 and B10, the rule map, and an empty field log.

Done when: the package matches the spec section, and `wc -w SKILL.md` is at most 1,000. Commit before task 2 starts.

## Task 2: `specifying-features` package (#24)

Files, all new, in `skills/specifying-features/`: `SKILL.md`, `close-run.md`, `FEATURE_STANDARDS.md`, `FEATURE_REVIEW_MANIFEST.md`, `FEATURE_RUBRIC.md`, `review-workflow.md`, `field-evidence.md`.

- `SKILL.md` holds the gates, the one-feature epic path, steps, reshard, hard rules and handoff.
- `FEATURE_STANDARDS.md` holds the design's format, the feature's elements, the delta command and its dispositions, shard-map rules and cost fitting.
- `field-evidence.md` holds baseline rows B1 to B10 as assigned in the spec, the rule map, and an empty field log.
- `skills/defining-architecture/SKILL.md`, Ownership: add the sentence giving stale-entry removal at a feature's close to `specifying-features`.

Done when: the package matches the spec section, `wc -w SKILL.md` is at most 1,000, and the existing `defining-architecture` contract test still passes.

## Task 3: contract test

New file `tests/scripts/test_feature_skills_contract.py`, parametrised over both packages:

- the seven package files exist;
- the frontmatter `name` equals the folder name, and the description starts "Use when" and is at most 500 characters;
- every `--skill` and `--phase` value the package text names is accepted by the review-log CLI, and the package names its own skill, its own self-review phase and `INDEPENDENT_AUDIT`;
- `SKILL.md` has at most 1,000 words.

No test asserts a phrase, sentence or heading of the skill text.

Done when: `uv run pytest` passes in full.

## After the tasks

Code review of the whole diff against the spec (AC-2 and AC-3 are checked here by reading), then a run record, then merge back to `feat/architecture-and-releases` with `--no-ff`.
