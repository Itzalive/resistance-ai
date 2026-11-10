# Review log: skills, phases and run-record field for architecture and features

Work item: #21. Part of #19.

## What changes and why

Three new skills — `defining-architecture`, `planning-features` and `specifying-features` — log
their reviews and run records with the review-log CLI (`skills/shared/scripts/review-log.py`). Today
the CLI rejects their names and has no phase for their self-reviews, and a run record cannot say
which feature its plan belongs to. This work item makes the CLI and its schema doc
(`skills/shared/review-log-jsonl.md`) accept them. It owns only the CLI, the schema doc and the
CLI's tests; the skills that log these values are their own work items.

**Trigger.** A skill runs `review-log.py append` or `review-log.py run-record`. Nothing else
changes: the output format, the log paths, the exit codes and every existing check stay as they
are.

## Rules

**Skills.** `defining-architecture`, `planning-features` and `specifying-features` join the allowed
`skill` values. Any other name is still exit 2 with nothing written.

**Phases.** Three self-review phases join the allowed `phase` values. Each accepts only
`--independence self`, as the existing self-review phases do; any other independence is exit 2
with nothing written.

| Phase | Used for |
|---|---|
| `ARCH_REVIEW` | Architecture self-review (`defining-architecture`) |
| `FEATURES_PLAN_REVIEW` | Feature plan self-review (`planning-features`) |
| `FEATURE_REVIEW` | Feature spec self-review (`specifying-features`) |

The fresh-context or cross-family audit of each of these documents logs as `INDEPENDENT_AUDIT`,
whose "Used for" text becomes "Epic, architecture, feature plan, feature or spec independent
audit". Phase names are exact: a near miss such as `FEATURES_REVIEW` is an unknown phase. The CLI
still does not check which skill logs which phase.

**Run records.** `feature` is the one optional run-record field: the id of the feature that the
plan's work item belongs to, written to the record unchanged. When present it must be a string
with at least one non-blank character; `null`, `""`, a blank string or a non-string is exit 2 with
a message naming `feature`, and nothing is written. When absent, the record is valid and carries
no `feature` key, so existing callers and records are unaffected. Every other field stays
required, unknown fields are still rejected, and the finding layers are unchanged: run records
count findings from plan execution, and architecture and feature reviews happen before a plan.

**Schema doc.** `skills/shared/review-log-jsonl.md` lists the three skills, adds the three phase
rows with `self` independence, widens the `INDEPENDENT_AUDIT` row as above, adds a `feature` row
(string, optional) to the run-record table, and changes "All fields are required" to "All fields
except `feature` are required".

## Scope

- `skills/shared/scripts/review-log.py`: the skill list, the self-review phase list, and the
  optional `feature` check in run-record validation.
- `skills/shared/review-log-jsonl.md`: the edits above.
- `tests/scripts/test_review_log_cli.py`: tests for each criterion, using its existing `run` and
  log-reading helpers and its `RUN_RECORD` fixture; plus a test that the doc's skill list, phase
  table and run-record table name exactly the CLI's `SKILLS`, `PHASES` and run-record fields
  (with `feature`), so the two cannot drift.
- `docs/superpowers/specs/2026-11-09-architecture-and-releases-plan.md`: `FEATURES_REVIEW`
  renamed to `FEATURES_PLAN_REVIEW` (owner decision, 2026-11-10).

**Out of scope:** the skills that log these phases (#22, #23, #24); a skill-to-phase check.

## Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | The allowed skills and phases are the tuples `SKILLS`, `SELF_PHASES` and `REVIEWER_PHASES` in `review-log.py`, and `build_entry` requires `self` for every `SELF_PHASES` member | VERIFIED: `review-log.py` lines 25–37, `build_entry` |
| A2 | Run-record validation requires every `RUN_RECORD_FIELDS` member and rejects any other key | VERIFIED: `validate_run_record` (`missing`, `unknown`) |
| A3 | `non_empty` rejects non-strings and strings that strip to empty | VERIFIED: `non_empty` |
| A4 | No other file holds a copy of the skill or phase lists | VERIFIED: `grep -rln "EPIC_REVIEW\|PLAN_SELF_REVIEW"` finds only the schema doc, the CLI and skill prose that names single phases |
| A5 | The CLI uses only the standard library | VERIFIED: imports `argparse`, `json`, `sys`, `datetime`, `pathlib` |

## Threat Model (CIA)

- **Confidentiality.** No new input source or output sink: the CLI still reads only its flags
  and the record file or stdin it is given, and writes only the two local log files
  (`append_line`).
- **Integrity.** New values pass the existing allow-list check (`one_of`) and the existing
  non-blank check (`non_empty`); lines are still serialised by `json.dumps` in `append_line`, so
  text cannot break the JSONL format. AC-3, AC-4 and AC-6 prove a rejected entry writes nothing.
- **Availability.** No loops, network calls or extra file reads are added.
- **Least privilege and supply chain.** Standard library only (A5); no new dependency.

## Acceptance criteria

- **AC-1** Given each of `defining-architecture`, `planning-features` and `specifying-features`,
  when `append` runs with `--phase SPEC_REVIEW --independence self`, then it exits 0 and the
  written entry's `skill` is that name.
- **AC-2** Given each of `ARCH_REVIEW`, `FEATURES_PLAN_REVIEW` and `FEATURE_REVIEW` with
  `--independence self`, when `append` runs, then it exits 0 and the written entry's `phase` is
  that name.
- **AC-3** Given each of those three phases with `--independence fresh-context`, when `append`
  runs, then it exits 2, stderr says independence must be `self` for that phase, and no log file
  is written.
- **AC-4** Given `--phase FEATURES_REVIEW`, when `append` runs, then it exits 2 and no log file is
  written.
- **AC-5** Given a valid run record with `"feature": "F-7"`, when `run-record` runs, then it exits
  0 and the written record's `feature` is `"F-7"`; given the same record without `feature`, then
  it exits 0 and the written record has no `feature` key.
- **AC-6** Given a valid run record whose `feature` is `null`, `""`, `"  "` or `7`, when
  `run-record` runs, then each exits 2, stderr names `feature`, and no log file is written.

## Future work (downstream cost)

| Item | Priority | Effort | Why |
|---|---|---|---|
| Skills #22–#24 log these phases and the `feature` field | P1 | in those items | This item only makes the CLI accept them |
| A skill-to-phase check in the CLI | P3 | S | Would catch a skill logging another skill's phase |
