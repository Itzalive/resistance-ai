# README Installation Instructions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add accurate README instructions for using this repository with GitHub Copilot CLI and VS Code.

**Architecture:** This is a documentation-only change centered in `README.md`. The README will gain a platform-first installation section: Copilot CLI gets concrete plugin marketplace and local-path commands from official GitHub Docs, while VS Code explicitly documents the repo's current metadata-only integration model and the absence of a public Marketplace install path today.

**Tech Stack:** Markdown, GitHub Copilot CLI plugin metadata (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`), VS Code extension metadata (`package.json`)

---

### Task 1: Add the new installation section to README

**Files:**
- Modify: `README.md`
- Reference: `.claude-plugin/plugin.json`
- Reference: `.claude-plugin/marketplace.json`
- Reference: `package.json`

- [ ] **Step 1: Reconfirm the repository metadata that the README must describe**

Run:

```bash
sed -n '1,80p' .claude-plugin/plugin.json
sed -n '1,80p' .claude-plugin/marketplace.json
sed -n '1,80p' package.json
```

Expected:

- `plugin.json` shows plugin name `resistance-engine`
- `marketplace.json` shows marketplace name `resistance-dev`
- `package.json` shows `"private": true`

- [ ] **Step 2: Prepare the exact Markdown content for the new section**

Insert this section after `## Packaging and consumption`:

````md
## Installation

### GitHub Copilot CLI

Install from the repository-hosted marketplace:

```bash
copilot plugin marketplace add Itzalive/resistance-ai
copilot plugin install resistance-engine@resistance-dev
```

Install directly from a local checkout:

```bash
git clone https://github.com/Itzalive/resistance-ai.git
cd resistance-ai
git submodule update --init --recursive vendor/obra-superpowers
copilot plugin install .
```

The marketplace metadata lives in `.claude-plugin/marketplace.json`, and the plugin manifest lives in `.claude-plugin/plugin.json`.

### VS Code

This repository does not currently ship a standalone VS Code extension. Its `package.json` is metadata-only packaging for VS Code discovery and publishing workflows, and it is currently marked `private`.

To use this repository from VS Code today, consume it from a parent repository or extension workspace:

```bash
git submodule add https://github.com/Itzalive/resistance-ai.git resistance-engine
git submodule update --init --recursive resistance-engine/vendor/obra-superpowers
```

There is no public VS Code Marketplace install flow for this repository yet. If that changes later, document the Marketplace install path separately instead of changing the local/submodule flow described above.
````

- [ ] **Step 3: Apply the README edit**

Use `apply_patch` to insert the new installation section immediately after the existing `## Packaging and consumption` bullets so the install guidance sits next to the packaging explanation.

- [ ] **Step 4: Review the updated README for correctness and placement**

Run:

```bash
sed -n '1,120p' README.md
git --no-pager diff -- README.md
```

Expected:

- The new `## Installation` section appears after `## Packaging and consumption`
- Copilot CLI instructions use `copilot plugin marketplace add` and `copilot plugin install`
- VS Code instructions clearly state that the repo is metadata-only and not publicly installable from Marketplace today

- [ ] **Step 5: Commit the README update**

Run:

```bash
git add README.md
git commit -m "docs: add plugin installation instructions" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Expected:

- A new commit records the README change without unrelated files
