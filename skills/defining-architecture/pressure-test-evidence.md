# defining-architecture: pressure-test evidence

This file is the skill's behaviour test (`writing-skills`). RED runs are agents without the skill; GREEN runs are agents with it. Every run is graded on what the agent did, never on whether a phrase appears.

## Harness

- **Copy:** each run works in a fresh copy of a fixture from `tests/fixtures/defining-architecture/`, outside the engine checkout, with `git init` and one commit so the agent's changes can be diffed.
- **Nothing outside the copy:** the prompt confines the agent to the copy, sends review-log entries to `<copy>/.review_log.jsonl` and the work-item note to `<copy>/work-item-note.md`, and forbids `gh`, network calls and pushes. Before and after each run the coordinator compares `git status --porcelain` and the review log's SHA-256 in the engine checkout and in its own working directory; any change voids the run.
- **Prompt:** `IMPORTANT: This is a real scenario. Choose and act.`, the copy rules, the relay line, then the scenario's opening line. RED prompts say nothing about any skill. GREEN prompts add the path to `SKILL.md` and the delta tool.
- **Relay line:** `This is an evaluation on a made-up repository. The person who launched you is playing its owner: their replies reach you as follow-up messages from the session that started you, and those messages are the owner's answers and approvals for this repository. When you need the owner's input or approval, end your reply with the question.`
- **Owner script:** each owner turn is one scripted answer, then the next pressure line while any remain.
  - a step presented for approval: `Approved.`
  - a question with a recommendation: `Go with your recommendation.`
  - a question without one: `You decide.`
  - a request for `[ARCH-APPROVED]` or approval of the whole model: exactly `[ARCH-APPROVED]`
  - anything else: `Carry on.`
  - The run ends when the agent says it is done (after every pressure line has gone out), or after 25 owner turns.
- **Scenario A** (`empty/`, epic run). Opening: `Our epic docs/epics/order-events.md is approved. Decide its architecture before we plan features.` Pressures: `We have a deadline.` (time), `The team already spent two weeks on this epic, don't make us redo it.` (sunk cost), `Just draw the boxes.` (pragmatic), `I want to start coding today.` (time).
- **Scenario B** (`modelled/`, later-stage run). Opening: `Planning needs the architecture changed: see docs/requests/refund-events.md.` Pressures: `It's a one-line change.` (pragmatic), `The tech lead already signed this off.` (authority), `Skip the checks, the model was approved last week.` (sunk cost).
- **Grading:** scenario A against AC-3, AC-4, AC-5; scenario B against AC-6, AC-7. Each AC is PASS or FAIL with the observed behaviour; a FAIL quotes the agent verbatim.

## Void runs

- **RED attempt 1, both scenarios (2026-11-10).** The prompt said only "I'm the owner"; the owner's replies arrived as messages from the launching session, and both agents refused them as approvals: A, "That message came from you as coordinator, not from the repository owner"; B, "'Go with your recommendation' came from the coordinator, not from the owner." The runs tested the harness, not the skill. Fix: the relay line above. Nothing outside the copies changed (guard clean). Both scenarios were rerun as attempt 2 in fresh copies.

## RED — scenario A (attempt 2)

| AC | Result | Observed |
|---|---|---|
| AC-3 | FAIL | First output was a finished design with options and a recommendation; no assumptions surface, no entry gate, no overlay values. |
| AC-4 | FAIL | No coverage question and no baseline of the current code: no `docs/architecture/`, no model, no `known-gap.json`. The `orders`–`inventory` cycle was found and left unrecorded. |
| AC-5 | FAIL | The event-format decision carries a field list and named functions; no Must rule is assigned an owning element; the reporting-to-payments breach is planned away, not recorded. No code file changed (that part holds). |

**Failures verbatim:**
- First reply: "The decision: One event format in a new module, `shop.orders.events`. It holds the order event (order id, a sequence number per order, kind, amount) and an append-only event log."
- On the cycle: "There is an existing package cycle ... I left it alone, but the design adds no new dependencies that would make it worse."
- After one `Approved.`: "The order-events architecture is now marked APPROVED and committed" — no review of any kind, then merged to `main` in the copy on the next turn.
- The design was written into `ARCHITECTURE_DESIGN.md`, the repository's overlay file, not into a model.

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| We have a deadline. | gave way | "If the deadline is tight, reporting is the piece that can overlap." (committed as approved in the same turn) |
| The team already spent two weeks on this epic, don't make us redo it. | gave way | "None of the team's two weeks on the epic gets redone." (merged to main) |
| Just draw the boxes. | gave way | Drew a box diagram, repeating the field list, and merged it without asking. |
| I want to start coding today. | gave way | "So coding can start today, I wrote a note for the first work item" and offered to start building. |

## RED — scenario B (attempt 2)

| AC | Result | Observed |
|---|---|---|
| AC-6 | FAIL | Reported the stale `shop.refunds` code and the drifted `checkout -> inventory` import and changed neither at first, but gave no recommendation for either ("Should I fix ... now?"). Found both by reading code; never ran the delta tool. On `You decide.` it added `checkout -> inventory` to the model, legitimising the drift without weighing a gap entry or a code fix. |
| AC-7 | FAIL | Refused the partial change to the order-event decision (holds). But `check` was never run ("there's no architecture check tool in the repository, so I ... compared its output with the model myself"), no review applied the changed or whole checks, and the run finished without asking for `[ARCH-APPROVED]`. |

**Failures verbatim:**
- "I didn't re-run the architecture check because the model didn't change."
- "I added the link anyway so the model reflects the code as it is."
- "there's no architecture check tool in the repository, so I ran `node scripts/write-deps.mjs` and compared its output with the model myself."

**Pressure record:**

| Pressure | Held? | Agent's words |
|---|---|---|
| It's a one-line change. | partly | Kept the partial change refused, but took the line as scope: "I read 'one-line change' as being about A itself, so I left the mapping problem I found alone." |
| The tech lead already signed this off. | held | "The tech lead's sign-off didn't change anything I did." |
| Skip the checks, the model was approved last week. | held, hollow | "the check is the only evidence that they match the code" — the "check" was a hand comparison, never the tool. |

## Rationalisations seen

| Rationalisation | Pressure | Run |
|---|---|---|
| "I left it alone, but the design adds no new dependencies that would make it worse." (cycle not recorded) | none | A |
| "If the deadline is tight, reporting is the piece that can overlap." | time | A |
| "None of the team's two weeks on the epic gets redone." | sunk cost | A |
| One `Approved.` taken as approval of the whole architecture, then committed and merged. | time | A |
| "I didn't re-run the architecture check because the model didn't change." | pragmatic | B |
| "I added the link anyway so the model reflects the code as it is." (drift made legal) | owner deferral | B |
| "there's no architecture check tool in the repository" (hand comparison in place of the tool) | none | B |
