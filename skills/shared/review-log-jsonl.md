# `.review_log.jsonl` reference

Use this support file when a skill requires review outcomes to be appended to
`.review_log.jsonl` at the repository root, or a run record to be appended to
`.run_records.jsonl`.

## Rules

- Write entries only with the append CLI, `scripts/review-log.py` in this
  directory. Never write JSON by hand, with `jq`, or with `echo`. The CLI
  validates every field and escapes the text, and writes nothing when an entry
  is invalid (exit code 2).
- Run it from the repository root, using its path relative to where this
  skill is installed, for example:
  `python <skills-dir>/shared/scripts/review-log.py append ...`
- Treat both logs as append-only. Never rewrite or delete prior entries.
- Use the current work item identifier.
- Use only the values listed below. If a review does not fit a phase, use the
  closest phase and say so in `--reason`; do not invent phase names.
- Do not put full stdout/stderr, full diffs, or secret-bearing output in any
  field.

## Review entry schema

| Field | Required | Meaning |
|---|---|---|
| `ts` | set by CLI | UTC time in ISO-8601 form |
| `item_id` | yes | Current work item identifier |
| `skill` | yes | Skill responsible for this review stage (enum below) |
| `phase` | yes | Review stage (enum below) |
| `round` | yes | Review round for this phase and item, starting at 1 |
| `verdict` | yes | `APPROVED`, `REJECTED`, `PASS` or `FAIL` |
| `orchestrator` | yes | Model running the workflow |
| `reviewer_model` | yes | Model that performed the review (the orchestrator for self-review) |
| `independence` | yes | `self`, `fresh-context` or `cross-family` |
| `findings` | yes | List of `{severity, kind, text}`; may be empty only on `APPROVED` or `PASS` |
| `tokens` | no | Tokens spent on this review round |
| `reason` | no | Short raw note from the reviewer, such as the approval note |

**`skill`:** `specifying-epics`, `specifying-work-items`, `writing-plans`,
`subagent-driven-development`, `executing-plans`, `requesting-code-review`,
`survivability`, `finishing-a-development-branch`.

**`phase`:**

| Phase | Used for | `independence` |
|---|---|---|
| `EPIC_REVIEW` | Epic self-review | `self` |
| `SPEC_REVIEW` | Spec self-review | `self` |
| `PLAN_SELF_REVIEW` | Plan self-review | `self` |
| `INDEPENDENT_AUDIT` | Epic or spec independent audit | `fresh-context` or `cross-family` |
| `PLAN_REVIEW` | Plan alignment check | `fresh-context` or `cross-family` |
| `CHECKPOINT_REVIEW` | Review during execution (per task or checkpoint) | `fresh-context` or `cross-family` |
| `CODE_REVIEW` | Final code review | `fresh-context` or `cross-family` |
| `SURVIVABILITY` | Survivability gate | any |

**`independence`:** `self` is the orchestrator reviewing its own work.
`fresh-context` is a reviewer with no drafting context from the same model
family. `cross-family` is a fresh-context reviewer from a different model
family.

**`findings[].severity`:** `critical`, `important`, `minor`.

**`findings[].kind`:**

| Kind | Meaning |
|---|---|
| `missed-caller` | A caller, test, fake, mock or assert the change breaks and the artifact missed |
| `weak-test` | A test that would not catch the fault it claims to cover |
| `plan-hole` | The plan omits or contradicts something the spec requires |
| `spec-hole` | The spec leaves a behaviour undecided or fails the work item |
| `real-bug` | Incorrect behaviour in code |
| `slip` | An executor or orchestrator did not follow the plan or skill |
| `wording` | Clarity or consistency only; no behaviour change |

**Gate strings:** a skill gate such as `APPROVED - INDEPENDENT AUDIT` means the
latest entry for that item with that phase has verdict `APPROVED`. Reviewer
output such as `[REJECTED - PLAN DRIFT]` goes in `--reason`; the verdict is
`REJECTED` and the findings carry the kinds.

## Appending a review entry

```bash
python <skills-dir>/shared/scripts/review-log.py append \
  --item-id "<work_item_id>" \
  --skill specifying-work-items \
  --phase INDEPENDENT_AUDIT \
  --round 2 \
  --verdict REJECTED \
  --orchestrator "<orchestrator_model>" \
  --reviewer-model "<reviewer_model>" \
  --independence fresh-context \
  --finding "critical:spec-hole:Empty-list behaviour for search results is undecided" \
  --finding "minor:wording:AC3 says 'should' where it means 'must'" \
  --tokens 85000
```

Each `--finding` is `SEVERITY:KIND:TEXT`. The text may contain colons, quotes
and backslashes. Add one `--finding` per finding.

For self-review, pass `--independence self` and your own model as
`--reviewer-model`. For survivability, use `--phase SURVIVABILITY`, put the
score (`mutation_killed=k/n chaos_passed=k/n`) in `--reason`, and log each
surviving mutant as a finding. Survivability entries also need
`--mutation-lane full|uncovered-only|skipped` and, unless the lane was skipped,
`--first-slate K/N` (the first mutation run, before hardening). They are stored as
`mutation_lane` and `first_slate: {killed, total}`. Round 1 with survivors must be
`FAIL`; the hardened rerun is round 2.

## Run record (one per plan)

`finishing-a-development-branch` writes one run record per executed plan to
`.run_records.jsonl`, so later retrospectives can compare plans without
normalising free text. Write the record as a JSON file (or pipe it), then:

```bash
python <skills-dir>/shared/scripts/review-log.py run-record --from run-record.json
```

All fields are required; use `0`, `{}` or `[]` when there is nothing to report.

| Field | Shape | Meaning |
|---|---|---|
| `item_id` | string | Work item the plan implements |
| `plan` | string | Path to the plan file |
| `tasks` | integer | Number of tasks executed |
| `tiers` | `{tier: count}` | Tasks per executor tier or model, e.g. `{"haiku": 3, "sonnet": 2}` |
| `escalations` | list of `{task, from, to, reason}` | Every executor escalation |
| `attempts` | `{task: count}` | Attempts per task |
| `tokens` | `{phase: count}` | Tokens per phase, e.g. `planning`, `execution`, `code-review` |
| `findings` | `{layer: {kind: count}}` | Findings per layer and kind; layers are `self-review`, `spec-audit`, `plan-review`, `checkpoint`, `code-review`, `survivability`; kinds as above |
| `plan_changes` | list of strings | Changes made to the plan during execution |
| `slips` | list of strings | Executor or orchestrator slips |

## Reading older entries

Entries written before 2026-10-27 do not follow this schema. When reading them:

- `timestamp` / `date` → `ts`; `bead_id` / `work_item` / `bead` → `item_id`;
  `stage` → `skill`.
- `status` / `result` → `verdict`, ignoring brackets and any suffix after
  ` - ` (`[APPROVED - CROSS-MODEL AUDIT]` → `APPROVED`).
- `CROSS_MODEL_AUDIT` → `INDEPENDENT_AUDIT`; `model` → `reviewer_model`.
- `brainstorming` → `specifying-work-items`.

Never rewrite them.
