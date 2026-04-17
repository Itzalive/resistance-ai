# README installation documentation design

## Problem

The repository documents packaging metadata for GitHub Copilot CLI and VS Code, but it does not yet explain how to install this plugin in either environment. The README should show both local/development and published/marketplace install paths without confusing the two platforms.

## Goals

- Add clear installation instructions for GitHub Copilot CLI.
- Add clear installation instructions for VS Code.
- Cover both local/development setup and published distribution paths.
- Keep the guidance aligned with this repository's current packaging layout.

## Non-goals

- Changing how the plugin is packaged or published.
- Adding new release automation.
- Documenting unrelated editor or agent integrations.

## Current repository facts

- Copilot CLI plugin metadata lives in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
- `package.json` is metadata-only packaging for VS Code discovery and publishing workflows.
- `package.json` is currently marked `"private": true`, so the README should not imply that a public VS Code Marketplace install is already available.
- `.claude-plugin/marketplace.json` describes a development marketplace rooted at this repository, so the README should treat Copilot CLI local/development installation as the supported path today unless a real published marketplace target is confirmed.
- The current README already has a `Packaging and consumption` section describing those files at a high level.

## Recommended approach

Add a new `## Installation` section to `README.md` after `Packaging and consumption`.

The section should be organized by platform first:

1. `### GitHub Copilot CLI`
2. `### VS Code`

Each platform subsection should then cover:

- **Local/development install**: how to use a local checkout of this repository.
- **Published install**: how to install from the relevant published channel when that channel exists, otherwise a short note that the repository currently documents local/development installation only.

This structure is preferred because most readers start from the platform they want to use, not from the distribution channel.

## Content design

### GitHub Copilot CLI

Document that the plugin metadata is sourced from `.claude-plugin/`.

For the local/development path, instruct readers to:

- clone the repository
- initialize the vendor submodule if needed
- point Copilot CLI at the local plugin or marketplace metadata in `.claude-plugin/`

For the published path, document the install command only if the plugin is actually published. If it is not yet published, say explicitly that the repository currently documents the local/development flow only and direct readers there instead of implying a working marketplace command.

### VS Code

Document that `package.json` is the VS Code packaging surface.

For the local/development path, instruct readers to install from a local checkout or packaged extension artifact, depending on what is already supported by the repo.

For the published path, document the Marketplace install flow only if the extension is published. Because the current package metadata is marked private, the README should state that VS Code installation currently depends on the local/development flow unless publication changes later.

## Error handling and clarity rules

- Do not present guessed commands as if they are supported.
- Distinguish clearly between "available now" and "intended once published".
- Keep each install flow short and task-oriented.
- Prefer explicit notes over ambiguous wording when a distribution channel is not active yet.

## Testing and verification

- Re-read the updated README to confirm the new section matches the repository metadata and does not contradict the existing packaging notes.
- Ensure the instructions are readable as plain Markdown and do not require additional repository changes.

## Implementation notes

- This is a documentation-only change in `README.md`.
- No code or packaging metadata changes are expected unless the repository lacks enough information to support truthful installation guidance.
