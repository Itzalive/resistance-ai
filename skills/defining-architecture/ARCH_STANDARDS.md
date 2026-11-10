# Architecture standards

Load at step 1. This file holds the reference detail `SKILL.md` points to.

## Overlay

Repo-root `ARCHITECTURE_DESIGN.md` is optional. Under a heading `## Architecture`, one `key: value` line per key. The overlay holds settings only; the architecture itself lives in the model folder.

| Key | Default | Meaning |
|---|---|---|
| `model` | `docs/architecture` | The model folder, relative to the repository root |
| `deps-command` | none | The command that writes the dependency file (`{"edges": [[from, to], ...]}`) |
| `deps-file` | `build/architecture-deps.json` | Where that command writes; inside the repository, not committed |
| `separator` | `.` | The module-name separator |
| `group-depth` | `1` | Segments below the shared prefix that make one top-level module group |
| `small-repo-modules` | `200` | Coverage question: at or under this many modules counts as small |
| `small-repo-groups` | `10` | Coverage question: at or under this many top-level groups counts as small |

The overlay may tighten this skill's rules, never weaken them. With no `deps-command`, the run stops at step 1 and asks for one; it never guesses.

## Delta tool flags

The tool is `node <skills-dir>/shared/scripts/architecture-delta.mjs`, run from the repository root with `--repo .`.

- `export --repo . --model <model>`: loads the model and prints its elements and relationships as JSON. Exit 0, or exit 2 with `error: <kind>: ...` on stderr.
- `check --repo . --model <model> --deps <deps-file> --separator <separator>`: compares the code's edges with the model. Exit 0 when every breach is in the gap file, 1 when a breach is new or a gap entry is stale, 2 on an error. Add `--format json` for machine output.
- Never pass `--gap`: the gap file is always `<model>/known-gap.json`.
- The `check` sections: new breaches, known breaches, not yet reached (a relationship the code doesn't have yet), unmapped code, and the summary line `N new, N stale, N known`. Quote the whole output in the decision log.

## Terms

- **Repository module:** a module that is the first item of at least one edge in the dependency file. A module that appears only as a target is outside the repository (a standard library or third-party package) and is never grouped, counted or modelled.
- **Top-level module group:** take the longest prefix, at the separator, shared by every repository module; a group is that prefix plus the next `group-depth` segments. A repository module equal to the shared prefix gets an element only when the whole repository is baselined; otherwise it is listed under "Unmapped modules" with the reason `shared prefix`, and it is never an edge node.
- **Not yet built:** an element with no `code` metadata. An element with `code` is built: each `code` value must equal a repository module or a prefix of one at the separator.
- **Must rule:** every business rule owned by a Must Have capability of the epic. For an epic written before capabilities existed, every business rule tied to a Must Have item of its MoSCoW scope.
- **Edge node:** a `component` covering a neighbour group outside the baselined area, with `code` set to that group's prefix, no children, no `rules`, and no part in any cross-cutting decision.

## Coverage question (step 2b)

Recommend, from the run's impact and the codebase's size:
- the whole repository, when there are at most `small-repo-modules` repository modules or at most `small-repo-groups` top-level groups;
- the whole affected container, when the model already has containers and the run touches more than half of one container's groups, or a cross-cutting decision binds that container;
- otherwise the touched groups plus edge nodes.

State the counts behind the recommendation.

## Spotting a cross-cutting decision

A decision is cross-cutting when **two or more capabilities** depend on it. Four kinds come up:
- a data or storage format;
- a shared contract or API;
- an id or naming scheme;
- a vocabulary of kinds or types.

Search the epic's capabilities and rules for anything two of them produce, consume or name in common. Each one found gets its own section in `architecture.md`.

## Mechanism detail stays out

The architecture states what each element owns and what it may depend on, and each decision's product-level obligations. Mechanism detail belongs to the feature and its work items. Made-up examples of what stays out:
- **a function:** "`orders.service.record_refund(order, amount)` writes the refund";
- **a schema:** "a `refunds` table with columns `id`, `order_id`, `amount`";
- **a field list:** "an event carries `order_id`, `seq`, `kind`, `amount`";
- **an algorithm:** "consumers keep the highest sequence number per order and skip anything at or below it".

The product-level form of the last two is an obligation: "every event identifies its order and its place in that order's history, and a consumer can tell an event it has already seen".

## Gap reason format

One sentence: why the breach exists today, and what closes it. For a cycle left out of a baseline, exactly `cycle in current code`.

## `architecture.md` layout

Kept in the model folder, with five sections:
1. **Decision log:** one dated entry per run, with the diff summary, the stage that asked, the alternatives rejected, and the quoted `check` output. The log only grows.
2. **Rule map:** rule → owning element.
3. **Cross-cutting decisions:** one section each, with the name, the owning element, the bound elements and capabilities, the product-level obligations, and the compatibility or versioning rule.
4. **Baseline coverage:** the baselined groups, the edge nodes, and the run that added each, with the coverage answer and its counts.
5. **Unmapped modules:** module → reason.

Sections 2 to 5 are edited in place to stay current.
