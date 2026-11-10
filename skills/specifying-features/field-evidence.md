# specifying-features: field evidence

This file is the skill's behaviour record. The skill was written from what happened on a real multi-item release run without it, not from synthetic scenarios, and it is tuned from real use.

## Baseline

What happened without the skill.

| # | What happened | Source |
|---|---|---|
| B1 | Several work items each restated one rule on separate entry paths, each with its own reader, validator and write call, so every new rule cost one set of tasks and tests per path. A consolidation item had to be inserted late. | Field report 2026-10-25 §7, lesson 14; change plan "Why" |
| B2 | The number of entry paths an item touched, not its size, drove its cost. This was found only by a costing spike run in the middle of the release. | Field report 2026-10-25 §7, lesson 16; change plan "Why" |
| B3 | Parts of the proposed consolidation did not pay back within the release: moving evals onto seams the next items did not change, and splitting a large file. | Field report 2026-10-25 §7, lesson 15 |
| B4 | A feature opened with an unplanned run of behaviour-free refactors, found only when its first items were designed. | Change plan "Why" |
| B5 | An eval used its own copy of a builder instead of production's, so it measured something production did not run. | Change plan "Why" |
| B6 | Work was split again and again with no re-costing; the splitting came from coupling, which another split did not remove. | Field report 2026-10-25 §7, lesson 17 |
| B7 | Behaviour questions the approved scope had left open surfaced one item at a time. Each was settled in chat and recorded in scattered places, and one invalidated a plan already written for the item before. | Field report 2026-10-25, lessons 26 and 27 |
| B8 | A pass that found 21 open questions for one item, 2 blocking and 19 with safe defaults, was heavy for the owner to decide at once. | Field report 2026-10-25, lesson 27 |
| B9 | A size number given to a plan writer became a target: drafts landed just over a line cap twice, and tasks were packed to stay under a task count. | Field report 2026-10-25, lessons 18 and 23 |

## Rule map

| Rule in the skill | Answers |
|---|---|
| Step 5, entry paths per shard and implementations per rule; a consolidation shard first at three or more | B1, B2 |
| Step 4, a refactor is cut to what this feature's shards change; a tidy-up is left alone | B3 |
| Step 4, every known breach and hot spot is decided as shard 0 or left alone, before any shard spec; hard rule "no shard spec before `[FEATURE-APPROVED]`" | B4 |
| Step 4, eval copies are read for and decided | B5 |
| Reshard: the second request re-runs the costing first | B6 |
| Step 2, the feature's questions are answered with evidence and written in the design, before the shards; an answer that changes another feature goes to a re-plan | B7 |
| Answers presented in tiers: owner decisions first, defaults listed once | B8 |
| Hard rule: a cost is reported, never a target or a cap | B9 |
| Red flags: shard spec first; refactor folded in; a second split answered by splitting; a tidy-up in shard 0; a question settled only in conversation | B3, B4, B6, B7 |

**From the approved change plan, with no recorded failure behind them yet:** feature ACs tracing to epic ACs; the delta run through the tool with a scope and a shards file; the rule that a shard never mixes a refactor with behaviour; the eval plan; the close run; the entry gates; the review steps and `[FEATURE-APPROVED]`; the red flag about skipping the delta.

## Field log

Empty. Add a dated entry when a real use of this skill goes wrong: what the agent did (in its own words where possible), the rule it broke or the gap it fell through, and the wording changed in response. Describe it generically and name no project. Change the skill only from an entry here or a filed issue.
