# Records and the change file

Load at step 3. What each file in the model folder holds, the fields a run fills, and the life of a run's change file. `export` and `check` validate every record (`tools.md`); a record problem stops the run.

## Which file holds what

| File | Holds |
|---|---|
| `*.c4` | The elements (with `code`, `rules`, tags and descriptions), relationships and views |
| `decisions/<group>.json` | `title`, `decisions` and `holes` for one subject; each list sorted by `id` |
| `contracts/<group>.json` | `title` and `contracts` for one interface with another system |
| `known-gap.json` | `entries`: each `from`, `to`, `reason` (and `close_by`, filled by `planning-features`) |
| `changes/<date>-<name>.json` | One change file per diff, written by `architecture-records change` |
| `coverage.json` | What baselines covered and which modules are unmapped |
| `generated/` | The documents, written by `architecture-docs build`; never edited by hand |

A `<group>` is lowercase letters and digits in `-`-separated parts. Record ids (decisions, holes, contracts) are unique across the folder, match `^[A-Za-z0-9][A-Za-z0-9.-]*$`, and never move when a record moves between files.

## The fields a run fills

**Decision:** `id`, `decision`, `reason` (or `null` when none is known), `rejected` (alternatives not taken), `binds` (element ids; empty for a principle), `status` (`current`, `partly-built`, `planned`, `superseded`, with `superseded_by` exactly when superseded), `evidence` (`checked` against the code, `code` comment, or `spec` document), `sources` (paths or references). A cross-cutting decision adds `obligations` (at least one, product-level) and usually `owner` and `compatibility`; an `owner` needs `obligations`. A decision decided but not yet built, and a proposed decision, are both `planned`.

**Hole:** `id`, `what`, `binds`, `evidence` (`checked`, `code`, `spec`, or `search` when a source was looked for and not found).

**Contract:** `id`, `name`, `owner`, `bound` (at least one), `obligations` (at least one), `compatibility` (or `null`).

No run writes a `capabilities` field or a capability view. An area is an element view `view area-<name>`, `<name>` 1 to 64 lowercase letters, digits and `-`, starting with a letter or digit, and not a device name (`con`, `nul`, `com1` and the like). A view `of <element>` holds that element and everything inside it; an unscoped view holds the elements it draws. A runtime link's kind is declared in a `specification` block in a file other than `c4.c4`.

## The change file's life

1. **Before copy.** Just before the first edit of a diff, copy the whole model folder to `architecture-before/<date>-<name>/` in the folder that holds the dependency file (`build/` by default), replacing any earlier copy of that name. Make it once per diff; going back to step 2 within the same diff keeps it. It is never committed. With an empty model folder there is no copy.
2. **Draft.** After the files are written (step 3), run `change` with `--before` (none for an empty folder), the diff's `--name` and `--date`, `--run`, `--asked-by`, `--summary` and a `--rejected` per choice not taken. Then add this run's coverage entries, each naming this change id as its `run`.
3. **Every edit after that** reruns `change` with the same `--name` and `--date` (`amendment.md`, Steps 4 to 6; the review's corrections likewise), so the coverage entries' `run` stays valid.
4. **Approval.** After `[ARCH-APPROVED]`, edit only the change file's `approved`, from `null` to `{ "by": "owner", "date": "<today>" }`, then run `architecture-docs build` once more.
5. **Never again.** A change file is never edited after its run is approved, and `change` refuses to replace one. A later correction is a new diff with its own change file; never rewrite a record an approved run wrote except through a new diff.

**A nested baseline** (step 2b, or an edge node's inside from step 5) is its own diff: its own change file (`--run baseline`, its own `--name`), its own before copy (none when the folder was empty), its own `[ARCH-APPROVED]`. After that, the outer diff takes its own copy before its first edit.

## Coverage

`coverage.json`: `answer` (the coverage answer in words; `whole repository` for a baseline run), `counts` (`modules` and `groups`), `baselined` (each `prefix` with the `run` that added it), `edge_nodes` (each `element` with its `run`), `unmapped` (each `module` with its `reason`). It is written after the change file of the run that adds to it. Only a run that baselines changes it: it adds its own entries and updates `answer` and `counts`, and never edits another run's entry, except moving an edge node it baselines from `edge_nodes` to `baselined` with its own change id as `run`.
