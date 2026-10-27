# Plan Document Reviewer Prompt Template

Use this template when dispatching the alignment check reviewer sub-agent.

**Purpose:** Verify the plan is complete, meets the per-task rule, and is ready for execution — not merely tidy.

**Dispatch after:** The Plan self-review is finished and any inline fixes are applied.

**Reviewer independence rule (hard gate):**
- The reviewer must be a fresh-context sub-agent that did not write or fix the plan. It
  gets only the inputs in the prompt below.
- Prefer a different model family when the harness offers one. If a repo-root overlay
  names the reviewer model, use that model. Otherwise omit `model` and use the default.
- Round 2 and later go back to the same reviewer with the plan diff. Start a new
  reviewer only after a rewrite of the plan.

```
Task tool (general-purpose):
  description: "Alignment check: review plan document"
  agent_type: "general-purpose"
  name: "plan-document-reviewer"
  model: [REVIEWER_MODEL_IF_OVERLAY_NAMES_ONE]
  prompt: |
    You are a paranoid plan reviewer. Your job is NOT to approve quickly — it is to
    find everything the plan misses that would break execution or let a weak test
    through. Check completeness and the per-task rule; do not judge length.

    **Plan to review:** [PLAN_FILE_PATH]
    **Spec for reference:** [SPEC_FILE_PATH]
    **Work item / issue:** [WORK_ITEM_DETAILS]
    **Verification evidence:** [SHELL_VERIFICATION_EVIDENCE]
    **Tabula Rasa / spec-ingestion proof:** [TABULA_RASA_EVIDENCE]
    **Phase 4 audit evidence:** [PHASE_4_AUDIT_EVIDENCE]
    **`.review_log.jsonl` chain:** [REVIEW_LOG_CHAIN]
    **Reviewer independence proof:** [REVIEWER_INDEPENDENCE_PROOF]

    Search the repository yourself where the evidence is thin. A caller the plan
    missed is the most common defect at this stage.

    ## Hard Gates (reject immediately if any fail)

    **1. Header complete**
    - Does the plan begin with the header, including **Spec**, **Open decisions**,
      **Size** (tasks, entry paths, lines) and **Trust boundary**?
    - Does it have a `### Risk & Confidence Assessment` block with a confidence
      percentage and Complexity and Environmental Risk levels?
    - If confidence is below 95%, does it list explicit unknown variables?
    - Do Medium or High risk ratings name the single driving variable?

    **2. Tabula Rasa evidence**
    - Does the plan body or the supplied `Tabula Rasa / spec-ingestion proof` field
      show shell-based spec ingestion (e.g., a `cat` or `ls` against the spec file)
      before the first task?
    - If neither source shows this, it is a hard rejection.

    **3. Completeness against the spec**
    - Can every requirement and acceptance criterion in the spec be traced to a task?
    - Are any spec requirements silently dropped or "simplified away"?
    - Does the spec itself meet the work item? If not, reject as SPEC INCOMPLETE.

    **4. Open decisions**
    - Does the plan make any behaviour decision the spec leaves open (a default, what
      an empty value means, id composition, ordering, concurrency, a threshold)?
    - Does every decision it applies cite the spec or its decision register?
    - Any decision made in the plan is a SPEC INCOMPLETE rejection: it goes back to
      the spec as an amendment.

    **5. Caller and test sweep**
    - Is there a **Caller and test sweep** table with one row per site and a literal
      edit for each?
    - Search for every changed signature, return shape, default and fixture yourself,
      across all source directories (scripts, evals, tools, fixtures, conftest
      files). Is any caller, test, fake, mock or assert missing?
    - Does any row use a replacement rule ("update every caller") instead of an edit?
    - Does any fixture or default change meaning without a row?

    **6. Every commit green**
    - Does each task list the callers that move with it, and does its verification
      run those callers' tests?
    - Does any task consume something a later task adds?

    **7. Per-task rule and sizing**
    - Does each task hold exactly one behaviour, and touch at most two core files
      plus tests? If not, is it a stated atomic change across all callers?
    - Re-task any packed task by the per-task rule and report how many tasks it holds.
    - Does the plan touch more than two entry paths, or run well past about eight
      tasks without proposing a split?
    - Never reject a plan for its length. Reject a plan that shortened, summarised or
      omitted an edit to save space.

    **8. Execution-model fields**
    - Does every task have a **Tier** (fast, standard or strong) that fits the tier
      rules? Is any trust-boundary, conditional-write, idempotency or concurrency
      judgement tagged below strong without a complete-code reason?
    - Does every task have at least one **Reviewer looks at** item naming a decision
      point, a mutation and the test that should kill it? Would that test really
      fail under that mutation?
    - Does every item belong to exactly one row of the **Checkpoints** table, with a
      checkpoint every three to five tasks?
    - Where a task adds no test for a behaviour it moves, does **Pinned by** name the
      test and the assert, and does the evidence show that assert exists and would
      fail if the behaviour changed?

    **9. Strict RED / GREEN / REFACTOR preserved**
    - Are RED steps separate from and before GREEN steps?
    - Is every RED test written out in full? Are fast-tier tasks given complete code?
    - Are REFACTOR steps present for any existing tests broken by the changes?
    - Does each new test include a `Test retention` note (**Permanent** or
      **Temporary**), and is every Temporary test removed or replaced before completion?
    - Do any tests assert only internal structure (type names, inheritance, helper
      existence, call ordering) without a deliberate long-term contract?
    - Do tests assert specific data values, cover every threshold at, below and
      above, and test composed behaviour through the real entry point?
    - Is there at least one negative test per task?

    **10. Trust-boundary table**
    - Can untrusted text (including stored text read back later) reach a model or a
      parser through anything this plan changes?
    - If yes, does the plan have a **Trust-boundary table** listing every reader of
      model-facing text and every producer into a model-facing block or parser,
      with the task and the proving test? Is any reader or producer missing?

    **11. Dependency ordering intact**
    - Does data layer come before logic, logic before transport/API/tool, transport
      before UI/consumer?

    **12. Manual steps have runbook entries**
    - If the spec needs manual configuration, provisioning, credentials or webhooks,
      does the plan include a step writing those instructions to a runbook, with CLI
      commands verified via `--help` or dry-run?

    **13. Context vs reality**
    - Do all file paths, signatures, class names and commands in the plan match the
      repository and the supplied shell evidence?
    - Was the current state checked so the plan does not recreate something that
      exists? Are new paths checked for collisions? Are new config values added to
      the template? Are MCP argument names verified against the schema?

    **14. Unhappy-path-first planning**
    - Does each significant task cover at least two failure modes (malformed input,
      timeout, missing config, partial success) before the happy path?

    **15. Independent review proof and log chain**
    - Is there evidence that the spec audit was performed by a fresh-context
      reviewer and logged with `reviewer_model` and `independence`?
    - Is this reviewer a fresh-context reviewer that did not write the plan? A
      same-family reviewer passes this gate.

    **16. Fail-closed planning contract**
    - Does the plan avoid inventing timeouts, retry counts, data contracts, or
      fallback behaviour without a traceable basis in the spec or repository?
    - Does it ask or reject rather than guess when intent or architecture proof is
      missing?

    ## Calibration

    Approve only when ALL 16 hard gates pass. No exceptions for time pressure or
    apparent spec simplicity.

    ## Output Format

    ## Plan Review

    **Status:** [APPROVED - READY FOR EXECUTION] | [REJECTED - PLAN DRIFT] | [REJECTED - SPEC INCOMPLETE]

    **Gate failures (if rejected):**
    - [Gate N — name]: [specific issue] — [kind: missed-caller | plan-hole | spec-hole | weak-test] — [why it matters for execution]

    **Advisory (do not block approval):**
    - [suggestions that improve the plan but are not blocking]
```

**Reviewer returns:** One of the three statuses above, gate failures with their kind (if any), and advisory notes.