# The tools

Load at step 2. Three tools ship with the engine; the repository needs no copy of them. Run each from the repository root with `--repo .`, passing the overlay's values (`ARCH_STANDARDS.md`) as `--model`, `--deps` and `--separator` where a command below shows them (`export` and `architecture-docs` take only `--model`). Every tool reports an error as `error: <token>: <detail>` on stderr with exit 2, and a run stops on it.

## The delta tool: `node <skills-dir>/shared/scripts/architecture-delta.mjs`

- `export --repo . --model <model>`: loads the model and its records and prints them as JSON (format 4): `elements`, `allowed` (import relationships), `runtime` (runtime links), the records (`decisions`, `holes`, `contracts`, `changes`, `coverage`), `areas` and `capabilities`. Exit 0 or 2.
- `check --repo . --model <model> --deps <deps-file> --separator <separator>`: compares the code's edges with the model. Exit 0 when every breach is in the gap file, 1 when a breach is new or a gap entry is stale, 2 on an error. `--format json` gives machine output with the module edges behind each breach. The text sections are `New breaches`, `Stale gap entries`, `Known breaches`, `Not yet reached` (an import relationship the code doesn't have yet) and `Unmapped code`, then the summary line `N new, N stale, N known (likec4 <version> from <source>)`.
- Never pass `--gap`: the gap file is always `<model>/known-gap.json`.
- Only a relationship of kind `uses`, or with no kind, permits imports. Any other kind is a runtime link: `check` ignores it and `export` lists it under `runtime`.
- A record problem is `record-error`, and a bad area or capability view is `model-error`, from both commands, before any other input is read.
- **In tests or CI:** run the overlay's `deps-command`, then `check`. Exit 1 fails the build. The repository decides how the engine and LikeC4 get there (a pinned dependency, a copy or a fetch).

## The records tool: `node <skills-dir>/shared/scripts/architecture-records.mjs`

**`change`** writes the run's change file, `<model>/changes/<date>-<name>.json`:

```bash
node <skills-dir>/shared/scripts/architecture-records.mjs change --repo . --model <model> --before <before-copy> --deps <deps-file> --separator <separator> --name <name> --date <YYYY-MM-DD> --run baseline|epic|later-stage --asked-by "<work item or stage>" --summary "<what the run changed>" [--rejected "<choice not taken>"]...
```

- It derives everything else from the files: the elements, relationships, decisions, holes and contracts added, changed and removed against the before copy (an element counts as changed only when it changed itself, not its relationships), the gap pairs added and removed, and a fresh `check` (`exit`, `summary`, `output`). Leave out `--before` when the model folder was empty.
- `--name` is lowercase letters, digits and `-`; `<date>-<name>` is at most 64 characters. A bad name or date, or an empty text flag, is `bad-input` and nothing is written. A `check` that errors stops it with that error.
- It replaces an existing change file of that id only while its `approved` is `null`; an approved one is `out-error`.
- It prints `wrote changes/<id>.json`.

**`change --compare`** (same flags; the text flags default to the existing file's) builds the same object and writes nothing: `same changes/<id>.json` (exit 0), `differs changes/<id>.json` (exit 1), or `missing changes/<id>.json` (exit 1). Use it before approval only: an approved file always `differs`, since the built object has `approved: null`.

**`cycles`** reads only:

```bash
node <skills-dir>/shared/scripts/architecture-records.mjs cycles --repo . --model <model> --deps <deps-file> --separator <separator> [--format text|json]
```

For each group of siblings whose import relationships form a cycle, it proposes the relationships to leave out: the fewest relationships, then the fewest module edges, then a fixed order, so a tie is never yours to break. Text output is one `group <parent or "top level">: <siblings>` line per group, then `leave out <from> -> <to> (<n> module edges)` lines, or `too large: <n> candidate pairs` for a group over 20 candidate pairs (chosen by hand), then `<r> relationships to leave out in <g> groups, <t> too large`. A model with no cycle prints only `0 relationships to leave out in 0 groups, 0 too large`. Exit 0 or 2.

## The documents tool: `node <skills-dir>/shared/scripts/architecture-docs.mjs`

- `build --repo . --model <model>`: writes every generated document into `<model>/generated`: the overview (`README.md`), one per area (`areas/<name>.md`), one per change file (`changes/<id>.md`), the improvement list (`improvements.md`), the HTML pages beside them and the AI pack (`pack/`). Prints `wrote <n> files, removed <m>`. Exit 0 or 2.
- `check --repo . --model <model>`: reports each document that is `missing`, `changed` or `extra`, then `<m> missing, <c> changed, <e> extra`. Exit 0 when current, 1 when stale, 2 on an error.
- It owns `generated/`: never edit a file there by hand; change the model or a record and build again.
