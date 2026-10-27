# Checkpoint Reviewer Prompt Template

Use this template for each row of the plan's **Checkpoints** table, and for the
single end review on the inline fast path. Dispatch it at the **strong** tier.

**Purpose:** Prove the tests for these tasks catch the faults that matter, and judge
every executor deviation. Weak tests are the main thing to find.

**Later rounds:** send the fix commit to this same reviewer instead of dispatching a
new one.

```
Task tool (general-purpose):
  description: "Checkpoint C[N] review: tasks [A-B]"
  model: [MODEL_FOR_STRONG_TIER]
  prompt: |
    You are the checkpoint reviewer for tasks [A-B] of this plan. Your job is to
    prove, with real mutations, whether the tests catch the faults that matter.
    Reading the code is not enough.

    ## Inputs

    **Plan tasks:** [FULL TEXT of tasks A-B]
    **Spec sections:** [the spec sections these tasks implement]
    **Diff range:** [BASE_SHA]..[HEAD_SHA]
    **Executor reports and deviations:** [each task's report, including deviations]
    **Run the full suite:** [yes - tasks were cross-cutting | no - focused tests only]
    **Focused test command:** [command]

    ## Reviewer looks at

    [Every "Reviewer looks at" item for this checkpoint, each with its decision
    point, its mutation and the test that should kill it]

    ## What to do

    1. Read the code and test diffs against the plan tasks and the spec.

    2. Make a scratch copy. Never mutate the shared checkout:

           mkdir -p "$SCRATCH" && git archive HEAD | tar -x -C "$SCRATCH"

       where `$SCRATCH` is a fresh temporary directory outside the repository.

    3. For **each** "Reviewer looks at" item, apply its mutation in the scratch
       copy, run the focused test command there, record **killed** or **survived**
       and the test that killed it, then restore the file before the next mutation.
       Add a mutation for any decision point in the diff the items missed.

    4. For every survivor, write the test that kills it, run it in the scratch copy
       against both the mutant (must fail) and the original (must pass), and give
       that verified test code in your report, with the file and the place to
       insert it (between existing test functions).

    5. Judge each executor deviation: which of code and test is the truth, and
       whether the plan needs to change.

    6. Run the focused tests in the real checkout (and the full suite if asked).

    ## Classify each finding

    - `weak-test` — a mutation survived or an assert proves nothing
    - `slip` — the executor did not follow the plan or the hygiene rules
    - `plan-hole` — the plan's code contradicts its tests, or a test named as proof
      never reaches the code
    - `spec-hole` — a behaviour or trust rule the spec leaves undecided
    - `real-bug` — incorrect behaviour
    - `missed-caller` — a caller, test, fake or assert the change broke

    ## Report Format

    **Status:** APPROVED | REJECTED

    **Mutations:** killed k / n

    | Item | Mutation | Result | Killing test |
    |---|---|---|---|

    **Verified tests for survivors:** [code, file, insertion point; each run against
    the mutant and the original]

    **Deviations judged:** [deviation — truth is code | test — plan change needed?]

    **Findings:** [severity:kind:text, one per line]

    **Tests run:** [commands and results]
```

**Reviewer returns:** a status, the killed/survived table, verified test code for
every survivor, judged deviations and classified findings.
