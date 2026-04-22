# `.review_log.jsonl` reference

Use this support file when a skill requires review outcomes to be appended to
`.review_log.jsonl` at the repository root.

## Rules

- Treat `.review_log.jsonl` as append-only. Never rewrite or delete prior entries.
- Preserve the exact status vocabulary required by the invoking skill.
- Preserve raw reviewer reason text instead of paraphrasing it.
- Use the current work item identifier.
- Include both orchestrator and reviewer model names when the review involves a
  second model.

## Canonical fields

| Field | Meaning |
|---|---|
| `timestamp` | UTC time in ISO-8601 form |
| `item_id` | Current work item identifier |
| `skill` | Skill responsible for this review stage |
| `phase` | Review stage, such as `SPEC_REVIEW`, `CROSS_MODEL_AUDIT`, or `PLAN_REVIEW` |
| `status` | Exact gate outcome required by the skill |
| `reason` | Raw reviewer output or approval note |
| `orchestrator` | Primary model running the workflow |
| `model` | Reviewer or auditing model |

## Generic append template

```bash
jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg wiid "<work_item_id>" \
  --arg sk "<skill_name>" \
  --arg ph "<phase>" \
  --arg st "<status>" \
  --arg rs "<raw_reason_text>" \
  --arg orch "<orchestrator_model_name>" \
  --arg aud "<reviewer_model_name>" \
  '{timestamp: $ts, item_id: $wiid, skill: $sk, phase: $ph, status: $st, reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```

## Named templates

### `SPEC_REVIEW` rejection template

```bash
jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg wiid "<work_item_id>" \
  --arg orch "<orchestrator_model_name>" \
  --arg aud "<reviewer_model_name>" \
  --arg rs "<failed criterion and exact correction>" \
  '{timestamp: $ts, item_id: $wiid, skill: "specifying-work-items", phase: "SPEC_REVIEW", status: "REJECTED", reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```

### `CROSS_MODEL_AUDIT` approval template

```bash
jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg wiid "<work_item_id>" \
  --arg orch "<orchestrator_model_name>" \
  --arg aud "<reviewer_model_name>" \
  --arg rs "<approval note>" \
  '{timestamp: $ts, item_id: $wiid, skill: "specifying-work-items", phase: "CROSS_MODEL_AUDIT", status: "APPROVED - CROSS-MODEL AUDIT", reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```

### `CROSS_MODEL_AUDIT` rejection template

```bash
jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg wiid "<work_item_id>" \
  --arg orch "<orchestrator_model_name>" \
  --arg aud "<reviewer_model_name>" \
  --arg rs "<raw rejection text>" \
  '{timestamp: $ts, item_id: $wiid, skill: "specifying-work-items", phase: "CROSS_MODEL_AUDIT", status: "REJECTED - CROSS-MODEL AUDIT", reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```

### `PLAN_REVIEW` template

```bash
jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg wiid "<work_item_id>" \
  --arg st "<plan review status>" \
  --arg orch "<orchestrator_model_name>" \
  --arg aud "<reviewer_model_name>" \
  --arg rs "<raw reviewer output>" \
  '{timestamp: $ts, item_id: $wiid, skill: "writing-plans", phase: "PLAN_REVIEW", status: $st, reason: $rs, orchestrator: $orch, model: $aud}' \
  >> .review_log.jsonl
```
