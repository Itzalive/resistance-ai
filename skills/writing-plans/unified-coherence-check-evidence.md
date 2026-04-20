# Unified Coherence Check evidence bundle

Use this reference when preparing the evidence passed into the plan reviewer
sub-agent.

## Required evidence

1. **Work item details**
   - Full work item title
   - Description
   - Notes or comments from the work-item system

2. **Final spec**
   - `docs/superpowers/specs/<spec-file>.md`

3. **Final plan**
   - `docs/superpowers/plans/<plan-file>.md`

4. **Pre-plan verification evidence**
   - Existing implementation/state check (for example whether the target section,
     file, feature, or prior plan already exists)
   - Target directory verification (`ls` / `tree`)
   - Test runner verification (`package.json`, `pyproject.toml`, or equivalent)
   - Method/class/return-shape verification (`grep`)
   - Config template verification when new env/config values appear
   - MCP `inputSchema` argument verification when applicable
   - Naming-collision checks

5. **Tabula Rasa / spec-ingestion proof**
   - Shell history or captured output showing the spec was physically ingested
     before drafting (for example `ls docs/superpowers/specs/` then `cat <file>`)

6. **Plan self-review outcome**
   - Summary of the self-review pass
   - Any inline fixes made before the reviewer was dispatched

7. **`.review_log.jsonl` chain**
   - Relevant entries for plan self-review, rejection/retry loops, and prior
     spec-review outcomes
   - Use the schema in `../review-log-jsonl.md`

8. **Opposite-model proof**
   - Evidence that the reviewer is from the opposite model family to the
     orchestrator
   - Any other explicit model-family proof needed by the hard gates

## Placeholder mapping

- `**Work item / issue:**` → item 1
- `**Spec for reference:**` → item 2
- `**Plan to review:**` → item 3
- `**Verification evidence:**` → item 4
- `**Tabula Rasa / spec-ingestion proof:**` → item 5
- `**Phase 4 audit evidence:**` → relevant parts of items 6 and 7 when needed
- `**.review_log.jsonl chain:**` → item 7
- `**Orchestrator / reviewer family proof:**` → item 8
