# Agent Instructions

This project tracks work items in **GitHub Issues**. Use `gh issue` for the canonical work queue.

## Quick Reference

```bash
gh issue list --state open                # Find available work
gh issue view <number>                    # View issue details
gh issue create --title "..." --body "..."  # Create follow-up work
gh issue comment <number> --body "..."    # Post status or blocker updates
gh issue close <number> --comment "..."   # Close completed work
```

## GitHub Issues Workflow

- GitHub Issues are the canonical source of truth for planned, active, and follow-up work.
- Start by identifying the relevant issue number and reading it with `gh issue view <number>`.
- If you discover new work, file or update a GitHub issue instead of leaving ad hoc TODOs in code, chat, or markdown notes.
- When work is blocked or changes scope, leave a comment on the issue so the next person can pick up accurate context.
- Reference the issue number in related branches, pull requests, and commits when it is practical to do so.
- Close the issue once the work is complete, or leave a clear closing comment explaining why it was not finished.

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

## Lifecycle Phase 4: Resilience & Mutation Testing

**CRITICAL:** Before an implementation is complete, it must survive the "Gauntlet."
Use the `survivability` skill to run this gate after implementation/review and before
branch finishing.

### 1. Mutation Testing (Test Efficacy)
Use the `survivability` skill to run a bounded mutation slate:
- 3 representative probes for a small change
- plus 1 per additional meaningful decision point
- capped at 5 total
- pass condition: the focused tests must fail for every injected mutation

### 2. Chaos Injection (Logic Durability)
Use the same `survivability` skill to run:
- 1 chaos probe minimum for local-only changes
- 2 for dependency-touching changes
- capped at 3 total
- pass condition: the system degrades safely and restore completes cleanly

### 3. Log Submission
Record the "Survivability Score" in your Phase 6 Retrospective.
- Log any "survived mutations" as CRITICAL FRICTION in `.review_log.jsonl`.
