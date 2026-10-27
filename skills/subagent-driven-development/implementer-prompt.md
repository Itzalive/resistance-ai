# Implementer Subagent Prompt Template

Use this template when dispatching an executor for one task. Dispatch it at the
task's **Tier** from the plan (or one tier up after an escalation).

```
Task tool (general-purpose):
  description: "Implement Task N: [task name]"
  model: [MODEL_FOR_TASK_TIER]
  prompt: |
    You are implementing Task N: [task name]

    ## Task Description

    [FULL TEXT of task from plan - paste it here, don't make subagent read file]

    ## Callers that move with this task

    [The task's "Callers that move with this task" rows from the caller and test
    sweep table, each with its literal edit]

    ## Context

    [Scene-setting: where this fits, which earlier tasks it builds on, the spec
    decisions it applies]

    ## Before You Begin

    If anything about the requirements, the approach or the dependencies is unclear,
    **ask now**. Don't guess.

    ## Your Job

    1. Write the RED tests exactly as the plan gives them, and run them. Confirm they
       fail for the reason the plan expects.
    2. Implement the GREEN step.
    3. Make every caller edit listed above.
    4. Run the task's tests and the tests of every caller that moved, and the plan's
       verification commands. All must pass.
    5. Commit, with the commit message the plan gives.
    6. Run any tests that check repository state (clean tree, committed files).
    7. Report back.

    Work from: [directory]

    ## Hygiene rules

    Each of these came from a real slip. Follow them at every tier.

    - **Never `git stash`.** Worktrees share one stash, so a stash in one checkout
      can be popped in another. To set work aside, commit it or ask.
    - **Never write or edit code through shell heredocs** (`cat <<EOF > file`, `sed`
      rewrites of code). They mangle backslash escapes, especially on Windows shells.
      Use the edit and write tools.
    - **RED before GREEN.** Write the failing tests and run them before writing any
      implementation. Never write both together.
    - **Insert new tests between existing test functions**, never inside one. Check
      the surrounding lines before inserting.
    - **Run repository-state tests only after committing.** Tests that check the
      tree is clean or files are committed fail before the commit by design.
    - **Stay in your task.** Don't edit files the task and its callers don't list.

    ## Deviations and plan holes

    If the plan's code and its test disagree, or the code no longer matches what
    the plan says is there, decide which one is the truth only when it is obvious
    and mechanical; report it as a deviation either way.

    If the task needs a decision the plan and spec don't make, or the plan
    contradicts itself, the spec or the code in a way you can't resolve
    mechanically, **stop** and report PLAN_HOLE. Don't guess.

    ## When You're in Over Your Head

    It is always OK to stop. Bad work is worse than no work, and escalating is not
    penalised. Report BLOCKED or NEEDS_CONTEXT when:
    - a test won't go green after a real attempt and you can't see why;
    - you need code beyond what was provided and can't find clarity;
    - you've been reading file after file without progress.

    Say specifically what you're stuck on, what you tried, and what would help.

    ## Before Reporting Back

    Check:
    - every RED test was run and failed before GREEN;
    - every listed caller edit is made and its tests pass;
    - nothing outside the task changed;
    - tests assert specific values, not just "not null".

    ## Report Format

    - **Status:** DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED | PLAN_HOLE
    - **Commit:** SHA (when DONE)
    - **RED run:** the command and the failure it showed
    - **GREEN run:** the commands and results, including caller tests
    - **Attempts:** how many attempts the hardest step took
    - **Deviations from the plan:** each one, and which of code or test you took as
      the truth
    - **Concerns or the blocker**
```
