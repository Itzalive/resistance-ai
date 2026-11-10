# planning-features: field evidence

This file is the skill's behaviour record. The skill was written from what happened on a real multi-item release run without it, not from synthetic scenarios, and it is tuned from real use.

## Baseline

What happened without the skill.

| # | What happened | Source |
|---|---|---|
| B1 | Several work items each restated one rule on separate entry paths. Each was reshared by path, and a consolidation item had to be inserted late, before the items that needed it. | Field report 2026-10-25 §7, lesson 14; change plan "Why" |
| B2 | The number of entry paths an item touched, not its size, drove its cost. This was found only by a costing spike run in the middle of the release. | Field report 2026-10-25 §7, lesson 16; change plan "Why" |
| B7 | Behaviour questions the approved scope had left open surfaced one item at a time. Each was settled in chat and recorded in scattered places, and one invalidated a plan already written for the item before. | Field report 2026-10-25, lessons 26 and 27 |
| B8 | A pass that found 21 open questions for one item, 2 blocking and 19 with safe defaults, was heavy for the owner to decide at once. | Field report 2026-10-25, lesson 27 |
| B9 | A size number given to a plan writer became a target: drafts landed just over a line cap twice, and tasks were packed to stay under a task count. | Field report 2026-10-25, lessons 18 and 23 |
| B10 | A decision's consequence was stated wrongly because it was not checked against the real thresholds: an action said to "wait for approval" would have been silently dropped. | Field report 2026-10-25, lesson 25 |

## Rule map

| Rule in the skill | Answers |
|---|---|
| Step 3, signals: entry paths and implementations per rule, three or more flagged | B1, B2 |
| Step 4, a rough cost per feature fitted from run records | B2 |
| Ordering rule 2 and step 2: direction-changing questions found up front and placed early, high-risk ones split out | B7 |
| Each step puts the owner's decisions first and lists the rest as defaults | B8 |
| Hard rule: a cost is reported, never a target or a cap | B9 |
| A question's risk states what changes at each answer, against the real thresholds | B10 |
| Red flags: order before questions and counts are known; a feature sized to a number | B2, B7, B9 |

**From the approved change plan, with no recorded failure behind them yet:** ordering rules 1 (decisions first), 3 (value to cost), 4 (every feature stands alone) and 5 (not by commonality); the red flags about shared code and a foundation-only first feature; the entry gates; the review steps and `[FEATURES-APPROVED]`; the re-plan run.

## Field log

Empty. Add a dated entry when a real use of this skill goes wrong: what the agent did (in its own words where possible), the rule it broke or the gap it fell through, and the wording changed in response. Describe it generically and name no project. Change the skill only from an entry here or a filed issue.
