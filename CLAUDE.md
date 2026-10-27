# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this project.

## Issue Tracker

This project tracks work in **GitHub Issues** (see `AGENTS.md` for the full workflow).

### Quick Reference

```bash
gh issue list --state open                # Find available work
gh issue view <number>                    # View issue details
gh issue create --title "..." --body "..."  # Create follow-up work
gh issue comment <number> --body "..."    # Post status or blocker updates
gh issue close <number> --comment "..."   # Close completed work
```

### Rules

- Use GitHub Issues for ALL follow-up work — do NOT leave TODOs in code, chat, or markdown notes
- Reference the issue number in related branches, pull requests, and commits

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create GitHub issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds


## Build & Test

```bash
uv run pytest -q                                   # Run the test suite
```

## Releasing

Bump versions with `scripts/bump_version.py` (see `AGENTS.md`). Never edit version strings by hand.

```bash
uv run python scripts/bump_version.py minor        # or major / patch / X.Y.Z
uv run python scripts/bump_version.py --check      # fails if manifests disagree
```

## Architecture Overview

_Add a brief overview of your project architecture_

## Conventions & Patterns

_Add your project-specific conventions here_
