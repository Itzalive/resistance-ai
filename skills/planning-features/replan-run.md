# Re-plan run

Load this file only for a re-plan run: a feature shipped, a split-out question was answered, or `specifying-features` sent back an answer that changes another feature. The map must have `[FEATURES-APPROVED]`.

## Steps

1. **Record.** On the map, write the result: the shipped feature's state and actual cost, or the question's answer.
2. **Re-check the order.** Test the features not yet shipped against the same ordering rules, with the new result. Say, per rule, whether anything moves.
3. **Log.** Add a dated entry to the re-plan log: what triggered the run, what was recorded, and what changed or "no change".
4. **If the order or any feature's content changes:** present the change to the owner, update `close_by` on any known-gap entry whose closing feature changed, and go through step 6 of `SKILL.md` with review scoped to the changed features.
5. **If nothing changes:** the owner confirms the log entry. No review runs.

## Rules

- Shipped features are never reordered or rewritten.
- An answer that changes the epic's capabilities or ACs is an epic amendment. An answer that changes the model goes to `defining-architecture` with a written diff request. Record the answer, stop, and hand over; resume the re-plan when the amendment is approved.
- The re-plan log only grows.
