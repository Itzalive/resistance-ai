# Architecture standards

Load at step 1. The overlay, the terms and the writing rules every step uses. The tools are in `tools.md`, the records in `records.md`.

## Overlay

Repo-root `ARCHITECTURE_DESIGN.md` is optional. Under a heading `## Architecture`, one `key: value` line per key. The overlay holds settings only; the architecture itself lives in the model folder.

| Key | Default | Meaning |
|---|---|---|
| `model` | `docs/architecture` | The model folder, relative to the repository root (the tools' `--model`) |
| `deps-command` | none | The command that writes the dependency file (`{"edges": [[from, to], ...]}`) |
| `deps-file` | `build/architecture-deps.json` | Where that command writes (the tools' `--deps`); inside the repository, not committed |
| `separator` | `.` | The module-name separator (the tools' `--separator`) |
| `roots` | none | Comma-separated `<prefix>` or `<prefix>:<depth>` items: where module groups start (below) |
| `group-depth` | `1` | Segments below a root that make one top-level module group |
| `small-repo-modules` | `200` | Coverage question: at or under this many modules counts as small |
| `small-repo-groups` | `10` | Coverage question: at or under this many top-level groups counts as small |

The overlay may tighten this skill's rules, never weaken them. With no `deps-command`, the run stops at step 1 and asks for one; it never guesses.

**`roots`.** Each item is a module name at the separator, optionally with its own depth.
- A module belongs to the longest root it equals or starts with followed by the separator. Its top-level group is that root plus the next `<depth>` segments (`group-depth` when the item gives none). A module with no more segments than its root plus `<depth>` is its own group.
- An empty root matches every module; a module's group under it is its first `<depth>` segments.
- A module under no root is unmapped, reason `outside roots`.
- A module equal to a root gets an element only when the whole repository is baselined; otherwise it is unmapped, reason `root prefix`.
- Without `roots`, the one root is the longest prefix, at the separator, shared by every repository module (it may be empty).
- These stop the run at step 1 as an overlay error: an empty `roots` value, a root listed twice, a depth that is not a whole number of 1 or more, a root that matches no repository module, a `separator` of `:`.

## Terms

- **Repository module:** a module that is the first item of at least one edge in the dependency file. A module that appears only as a target is outside the repository (a standard library or third-party package) and is never grouped, counted or modelled.
- **Root, top-level module group:** as `roots` above.
- **Not yet built:** an element with no `code` metadata. An element with `code` is built: each `code` value must equal a repository module or a prefix of one at the separator.
- **Must rule:** every business rule owned by a Must Have capability of the epic. For an epic written before capabilities existed, every business rule tied to a Must Have item of its MoSCoW scope.
- **Edge node:** a `component` covering a neighbour group outside the baselined area, with `code` set to that group's prefix, no children, no `rules`, and in no decision's `binds` or `owner` and no contract's `owner` or `bound`.
- **Contract:** the interface between this system and another (a server and its app, a public API, an event sent to an outside system), in `contracts/<group>.json`.
- **Decision:** why something is the way it is, in `decisions/<group>.json`. A **cross-cutting decision** has `obligations` and is changed whole, for every part it binds; one that settles something several parts must agree on usually also has an `owner` and a `compatibility` rule. A **principle** is a cross-cutting decision with empty `binds` and no `owner`. A **proposed decision** has `status: planned`.
- **Hole:** an open question, unexplained structure or contradiction, in the same decisions files.

## Spotting a cross-cutting decision

Anything two or more elements, or two or more capabilities, produce, consume or name in common is a decision with `obligations`. Four kinds come up:
- a data or storage format;
- a shared contract or API;
- an id or naming scheme;
- a vocabulary of kinds or types.

Search the epic's capabilities and rules, and in a baseline the code and its documents, for anything two parts share. Each one found is one decision record.

## Coverage question (step 2b)

Asked only in an epic or later-stage run whose touched groups are not modelled; a baseline run covers the whole repository and asks nothing. Recommend, from the run's impact and the repository's size:
- the whole repository, when there are at most `small-repo-modules` repository modules or at most `small-repo-groups` top-level groups;
- the whole affected container, when the model already has containers and the run touches more than half of one container's groups, or a cross-cutting decision binds that container;
- otherwise the touched groups plus edge nodes.

The counts are across all roots: the module count is every repository module, `outside roots` ones included; the group count is the groups under the roots. State them with the recommendation.

## Mechanism detail stays out

The architecture states what each element owns and what it may depend on, and each decision's product-level obligations. Mechanism detail belongs to the feature and its work items. Made-up examples of what stays out:
- **a function:** "`orders.service.record_refund(order, amount)` writes the refund";
- **a schema:** "a `refunds` table with columns `id`, `order_id`, `amount`";
- **a field list:** "an event carries `order_id`, `seq`, `kind`, `amount`";
- **an algorithm:** "consumers keep the highest sequence number per order and skip anything at or below it".

The product-level form of the last two is an obligation: "every event identifies its order and its place in that order's history, and a consumer can tell an event it has already seen".

## Gap reason format

One sentence: why the breach exists today, and what closes it. For a cycle left out of a baseline, exactly `cycle in current code`.
