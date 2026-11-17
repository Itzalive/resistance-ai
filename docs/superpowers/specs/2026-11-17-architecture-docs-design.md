# Architecture documents generated from the model

Work items: #32 (A4, model pack), #33 (A5, architecture book), #34 (A6, change record and improvement list), parts of #37. Amends `2026-11-17-architecture-model-records-design.md` (capability names) and `2026-11-16-architecture-delta-runtime-links-design.md` (`export` format).

## Why

The architecture model is the single source of truth, but only a tool or a patient reader can use it as it stands: a `.c4` folder and JSON records. Architects, the product team, senior engineers and AI agents each need a readable cut of it: the whole system, one area, one process, what a change did, and what to improve. The first run built those cuts by hand with one-off scripts, and they went stale the moment the model changed (`docs/field-reports/2026-11-16-defining-architecture-first-run.md`, F9, F12, R5). This work item makes them a generated, checked part of the model.

## What this work item owns

- What `export` prints about element and relationship titles, area views and capability views (format 4), and the rules that keep those views honest.
- One records rule: a `capabilities` entry names a capability view.
- A new tool, `architecture-docs.mjs`, beside the delta tool, that writes the documents into one output folder (`build`) and reports when they are stale (`check`).
- What each generated document holds.

It does not own the skill's steps (#31 part A3b), running `check` in CI or verifying a dependency file (#35, A7), or converting an existing model (#36, A8).

## Areas and capabilities

An **area** is a LikeC4 element view whose id is `area-<name>`. The elements it shows are the area's elements; an element may be in several areas, or in none. Areas replace any hard-coded grouping: the documents have one area document per area view.

A **capability** is a LikeC4 dynamic view whose id is `capability-<name>`. Its steps, in order, say how the elements work together for one process. Each step must follow a relationship already in the model:

- A relationship **matches** a step from A to B when its source is A or inside A, and its target is B or inside B.
- A step is a **call** when some relationship matches it from A to B; it is a **reply** when none does but one matches it from B to A (a response to an earlier call). Any other step is an error.
- The step carries its label and the kinds of the relationships that match it (a relationship with no kind counts as `uses`).

So a sequence diagram can never show an interaction the model does not have. Timing is expressed only through labels and relationship kinds (an "async" or "every 5 min" label, an `http` or `event` kind); durations and deadlines are mechanism detail and are not modelled.

`<name>` is 1 to 64 characters of lowercase letters, digits and `-`, starting with a letter or digit. It becomes a file name on every platform, so case cannot collide.

Other views (the default index view and any other views) are not exported and do not produce documents.

## What `export` prints (format 4)

`format` is 4. Everything format 3 printed stays, with these additions:

| Added | Content |
|---|---|
| each element: `title`, `description` | As written; LikeC4 gives an element with no title its name. `description` is its source text (plain or Markdown), or `null` when absent. Both are record text (line feeds kept, no cut). |
| each `allowed` and `runtime` entry: `titles` | The distinct non-empty titles of the relationships the entry stands for, sorted; empty when none has a title. A list, because one pair can stand for several relationships. |
| `areas` | One entry per area view, sorted by `name`: `name`, `title`, `description` (or `null`), `elements` (ids, sorted). |
| `capabilities` | One entry per capability view, sorted by `name`: `name`, `title`, `description` (or `null`), `steps` in view order, each `{ "from", "to", "label", "reply", "kinds" }`; `label` is `null` when absent, `reply` is `true` or `false`, `kinds` is sorted. |

A view's `title` is its LikeC4 title, which LikeC4 defaults to the view id when none is written. Steps inside a LikeC4 `parallel` block are listed in the order LikeC4 gives them.

**New `model-error` lines (exit 2)**, reported after LikeC4 loads the model and before the records are read:

- `view <id>: an area view must be an element view` and `view <id>: a capability view must be a dynamic view`;
- `view <id>: <name> is not a valid name` for a name outside the rule above;
- `view <id>: step <n>: <from> -> <to> follows no relationship`, with `<n>` counted from 1.

All problems of this kind are reported in one run, sorted by view id, then step.

**Records amendment.** A decision's or a contract's `capabilities` entries are now capability names, not free text:

- pass 4 (links) reports `<value> is not a capability` at the entry's path for a name that is no capability view's name, and `<value> is listed twice` at the second entry's path for a name repeated in one list;
- `capabilities` joins the keys whose values are cleaned as ids.

`check`'s output does not change.

## The tool

`node <skills-dir>/shared/scripts/architecture-docs.mjs <command> --repo <path> [--model <dir>] [--gap <file>] [--out <dir>] [--timeout <s>]`

| Command | Does | Exit |
|---|---|---|
| `build` | Loads the model, the records and the known-gap file exactly as `check` loads them (same rules, same errors, same `--model`, `--gap` and `--timeout` defaults), builds every document, and writes them. | 0; 2 on any error |
| `check` | Builds every document in memory and writes nothing. Prints one line per file that is missing, differs, or is no longer produced (`missing <path>`, `changed <path>`, `extra <path>`, paths relative to `--out` with `/`, sorted by path), then `<m> missing, <c> changed, <e> extra`. A missing `--out` folder makes every file `missing`. | 0 current; 1 stale; 2 on any error |

There is no command per document: one build writes the whole set, so the links between documents always agree. Errors use the delta tool's format (`error: <token>: <detail>`), with one new token, `out-error`.

**The output folder.** `--out` defaults to `<model>/generated`. The record reader reads only its named folders, so it ignores this folder; its files count toward the model folder's limits (2,000 files, 50 MB), and a model with 50 areas uses about 200 files.

**Write rules.**

1. `--out` must resolve, through real paths, inside `--repo`. It must not be the model folder, contain the model folder, or be or lie inside the model folder's `decisions`, `contracts` or `changes` folders; no part of the path below `--repo` may be a link. Otherwise `out-error`, before anything is built.
2. **The tool owns the folder.** Every Markdown and HTML file it writes starts with the line `<!-- Generated by architecture-docs from the architecture model. Do not edit. -->`, and its JSON file is an object whose first key is `"generated": "architecture-docs"`. Before building, `build` and `check` both list the folder: a file without the marker (other than a temporary file of rule 3), a link, or a folder the layout below does not name gives `out-error`, and `build` writes nothing. So the tool never overwrites or deletes a file a person wrote. A marked file the build no longer produces is deleted; a named folder is created when it gets a file and removed when it is left empty. `build` creates `--out`, and any missing parent inside `--repo`, when they do not exist.
3. Each file is written to a temporary name in its own folder and renamed into place; a failed build leaves no partly written file. Temporary names start with `.architecture-docs-`; a later `build` removes any it finds, and `check` ignores them.
4. **The output is deterministic**: no timestamps or run-dependent values, a fixed order everywhere, LF line endings, UTF-8. `check` compares after turning CRLF into LF, so a checkout that converts line endings is not reported stale.

**Layout of the output folder.**

```
generated/
  README.md, index.html                      overview
  areas/<name>.md, areas/<name>.html          one per area
  capabilities/<name>.md, <name>.html         one per capability
  changes/<id>.md, changes/<id>.html          one per change file
  improvements.md, improvements.html
  pack/README.md                              AI pack index
  pack/areas/<name>.md
  pack/capabilities/<name>.md
  pack/model.json
```

**Writers.** Each document is first built as a tree of headings, paragraphs, lists, tables, code blocks, links and diagrams. A Markdown writer and an HTML writer turn the tree into text. There is no Markdown parser and no new dependency.

- **Markdown** (all documents except the pack): every piece of model text is escaped: ASCII punctuation that Markdown or HTML gives a meaning to (`\ ` `` ` `` `* _ { } [ ] ( ) # + - . ! | < > &` and `~`) is backslash-escaped or written as an entity, so record text cannot open a link, an HTML tag or a code span. In a table cell, line feeds become spaces. A code block's fence is longer than any run of backticks in its content. Diagrams are fenced `mermaid` blocks.
- **Pack text:** the pack is read raw by agents, so ids and text are written as `export` gives them, unescaped. Line feeds become spaces in one-line fields (titles, labels, list items); in a multi-line field (description, decision, reason, note) every line is kept, and a line starting with `#` or `---` gets a leading `\`, so record text cannot start a heading or a separator.
- **HTML:** every value is HTML-escaped. Each page carries `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js 'sha256-<hash of the start-up script>'; style-src 'unsafe-inline'; img-src data:">`: scripts only from the pinned Mermaid file and the one inline start-up script, inline styles (which Mermaid needs), and no other fetch. Diagrams are `<pre class="mermaid">` holding the escaped diagram text, drawn by Mermaid 12.2.0 (`https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js`, integrity `sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp`) with `securityLevel: 'strict'`. Without the script the page shows the diagram text. Links between pages are relative.
- **Diagrams:** node ids are generated (`n1`, `n2`, … in element id order), never element ids. Every label is quoted; line feeds become spaces, and every character other than letters, digits, space and `.,:;!?'/_-` is written as a Mermaid entity `#<decimal code>;`. So no label can close its quotes, and no diagram holds `%%`.

## What each document holds

**Shared rules.** Every fact comes from `export` or the known-gap file. Ids are shown as written, titles beside them for readers. "First" means sorted by name or id in UTF-16 code-unit order. An element's **areas** are the area views that show it. A record's areas are the areas of the elements it binds (a decision's or open question's `binds`, a contract's `owner` and `bound`). Each id links to the document that holds it: an element to its first area (or the overview's "Not in any area" section), a decision, contract or open question to its first area (or, when it has none, the overview), a principle to the overview, a capability and a change to their own documents. A diagram with more than 80 arrows (after the drawing rules below), or a capability with more than 200 steps, is replaced by a note saying so; the tables still list everything.

**Overview** (`README.md`).
- The system title, and a diagram of the top-level elements (no parent), with each relationship lifted to the top-level elements that hold its ends; a relationship within one top-level element is not drawn. One arrow per pair and style: solid when any lifted relationship is an import; otherwise dashed, labelled with the sorted kinds.
- Areas: title, description, element count, link. Capabilities: title, description, the areas they pass through, link.
- Principles (decisions with `obligations`, empty `binds` and no `owner`), in full.
- Contracts: name, owner, bound elements, compatibility, link.
- Changes, newest first (by date, then id), with summary and approval.
- Model health: known-gap entries, open questions, the coverage answer and unmapped modules, as counts linking to the improvement list.
- **Not in any area:** the elements in no area view, with title and description; then, in full, every decision (other than a principle), contract and open question that has no area.

**Area** (`areas/<name>.md`).
- Title and description.
- **Diagram.** The area's elements inside a frame; each element outside the area with an import or runtime relationship to or from an area element is drawn outside the frame and links to its area. Imports solid; runtime links dashed and labelled with kind and titles; known-gap entries between drawn elements red and labelled `known gap`. A relationship from X to Y is not drawn when another drawn relationship runs from X or an element inside X to Y or an element inside Y (it is implied by the more specific one). Several relationships of the same style between the same two elements are one arrow.
- **Elements:** id, title, description, code, rules, tags.
- **Dependencies:** for each area element, what it may use and what may use it, and its runtime links, each with the other end's area.
- **Decisions** binding any area element, cross-cutting first (by id within each), each in full: decision, reason (or "Reason not known"), rejected, obligations, owner, compatibility, capabilities, status and superseded_by, evidence, sources, note, and "Also binds: <areas>".
- **Contracts** whose owner or bound elements are in the area, in full; **open questions** binding area elements; **known-gap entries** with an end in the area, with reason and `close_by`; **capabilities** with a step touching an area element.

**Capability** (`capabilities/<name>.md`).
- Title and description.
- A sequence diagram: participants in order of first appearance, labelled with their titles; calls solid, replies dashed, each with its label.
- **Steps:** number, from, to, label, call or reply, kinds; each end linking to its area.
- The decisions and contracts that name this capability, in full; the areas involved (the areas of every step's ends, and "Not in any area" for an end in none).

**Change record** (`changes/<id>.md`).
- Summary, asked by, run, date, and approval (by and date, or "Not yet approved").
- A diagram of the elements the change added or changed that are still in the model, marked `added` or `changed`, with their neighbours as plain context, drawn by the area rules; no diagram when there are none.
- **What changed:** elements, decisions, contracts and open questions, each as added, changed, removed. Added and changed records still in the model are printed in full as they stand now; the change file holds only ids. Removed ids are plain text; an added or changed id no longer in the model is plain text with "(not in the current model)".
- **Choices not taken:** the change's `rejected` list, then the `rejected` options of each decision it added or changed that is still in the model.
- **Known gap:** the entries it added and removed.
- **Check:** exit, summary, and the output in a code block.

**Improvement list** (`improvements.md`). Facts only; nothing judged or ranked. Groups in this order, each with its count, items sorted by id or by pair:
1. Cycles in current code: known-gap entries whose reason is `cycle in current code`.
2. Other known breaches: the other known-gap entries, with reason and `close_by`.
3. Open questions, with the elements they bind.
4. Decisions with no known reason (`reason` is `null`).
5. Unmapped code: the coverage file's `unmapped` entries with their reasons (the build reads no dependency file).
6. Elements in no area.
7. Elements that own nothing: no `code`, no child element, kind not `external`, and not a coverage edge node.

Each item links to its areas (for a known-gap entry, both ends'). A judgement on how the architecture should improve is not generated: a `defining-architecture` run records it as an open question or a proposed decision, and it then appears here (A3b).

**AI pack** (`pack/`). The same facts in a compact form, for an agent to load only the slice it needs.
- `pack/README.md`: how the pack is laid out, and an index from every element, decision, contract and capability id to the pack files that hold it.
- `pack/areas/<name>.md`, `pack/capabilities/<name>.md`: one block per element in the slice, then the slice's decisions, contracts, open questions and known-gap entries in full; no diagrams. A capability slice holds its steps and the elements they touch. Every id outside the slice is followed by its pack file in brackets.
- `pack/model.json`: `{ "generated": "architecture-docs", "export": <the format 4 export> }`.

Element block:

```
### shop.orders: Orders
kind container · tags #layer · code shop.orders · rules BR-1, BR-4
Takes and tracks orders.
uses: shop.billing, shop.catalog [areas/catalog.md]
used by: shop.web
runtime: -> payments.gateway (http, "charges card") [areas/payments.md]
bound by: D-3 (cross-cutting), D-7
```

## Compatibility

A model with no area or capability views exports as before apart from `format` 4 and the new fields and empty lists; its documents are the overview, the improvement list, the change records and the pack index, with every element under "Not in any area". A record using `capabilities` as free text now fails pass 4; no model uses that field yet. Readers of `export` that check `format` must accept 4.

## Scope

- The delta tool: element and relationship titles, area and capability views, the view rules, `format` 4; the records capability rule. Tests beside the existing delta tests. Existing tests change only where they assert `format` or the exact element and relationship objects, and in the records spec's AC-19 test, whose free-text capability `Pay` becomes the name of a capability view it adds to its model.
- The new tool and its modules in `skills/shared/scripts/`, with tests in `tests/scripts/`.
- `ARCH_STANDARDS.md`: one line each for `format` 4, the area and capability view naming, and the new tool's two commands. The rest of the skill text is A3b.
- Amendment notes in the records spec and the runtime-links spec.

**Out of scope:** CI wiring and dependency-file verification (A7); the skill's steps (A3b); converting a model (A8); serving, watching, PDF; any judgement-based content.

**Shard evaluation.** One spec, because the documents share one tree, one set of writers and one link scheme, and their link rules must be reviewed together. It is too large for one plan, so it is planned and built as four plans in order, each on its own branch and each within the two-entry-path rule, as the records spec was (A3a, A3c). The work items already exist (#32 to #34); each plan names its issue: (1) `export` format 4 and the records rule (#32); (2) the tool, write rules, `check`, writers, overview and pack (#32); (3) area and capability documents (#33); (4) change records and the improvement list (#34).

## Threat Model (CIA)

| Pillar | Vector | Defence and proof |
|---|---|---|
| Confidentiality | The tool reads outside the repository. | It reads only what `check` reads, through the same path rules (`paths.mjs` `resolveInside`, `walk.mjs` `walkModelDir` refuses links). |
| Integrity | The tool overwrites or deletes a person's file, or writes outside its folder. | Write rules 1 and 2: `--out` resolved by real path inside `--repo`, outside the model's own files, no links; a file without the marker stops the build before any write. A test lists every write call in the tool's source, and they are all in one writer module. |
| Integrity | Model or record text injects Markdown links, HTML, Mermaid directives or terminal sequences into a document. | Text is cleaned by `export` (`errors.mjs` `cleanText` removes escape and control characters); the Markdown writer escapes punctuation; the HTML writer escapes every value under a CSP; diagram labels are quoted with entities and node ids are generated. Tests feed hostile text through each writer. |
| Integrity | A sequence diagram shows an interaction the model does not have. | The step rule: every step matches a relationship, or `model-error`. |
| Integrity | A tampered Mermaid script runs in a reader's browser. | Exact version, subresource integrity hash, CSP allowing only that file. |
| Availability | A huge model produces huge documents or slow builds. | The model folder limits (2,000 files, 50 MB) and the 5,000-element cap bound the input; diagrams over 80 arrows and capabilities over 200 steps are replaced by notes; the `--timeout` deadline is checked after loading and after each document. |
| Least privilege | The tool needs file writes the delta tool does not have. | Writes only inside `--out`; no `child_process`, no `worker_threads`, no network module (source test, as `tests/scripts/test_architecture_delta_safety.py` does for the delta tool, which keeps its no-write test unchanged). |
| Supply chain | Mermaid in the browser. | Not a package dependency. Mermaid 12.2.0 verified on npm (released 2026-10-13) and on the CDN (`dist/mermaid.min.js`, 5,494,801 bytes, hash above). No new npm dependency (`package.json` keeps only `likec4`). |

## Acceptance criteria

`export`:
- **AC-1** Given a model with element and relationship titles and descriptions, one area view and one capability view, when `export` runs, then `format` is 4, each element has its `title` and `description`, each `allowed` and `runtime` entry its sorted `titles`, and `areas` and `capabilities` hold the views as written.
- **AC-2** Given a capability with a step along a relationship, a step against one, and a step whose target is inside a relationship's target, when `export` runs, then the steps are a call, a reply and a call, in view order, each with its kinds.
- **AC-3** Given a capability step that follows no relationship either way, an `area-` dynamic view, a `capability-` element view and an `area-Shop` view, when `export` runs, then it exits 2 with four `model-error` lines sorted by view id, and the step line names the step number.
- **AC-4** Given a decision whose `capabilities` names a capability view and a contract whose `capabilities` names none and repeats a name, when `export` runs, then the lines are `… is not a capability` and the duplicate line at the contract's paths, and nothing for the decision.
- **AC-5** Given a model with no area or capability views, when `export` runs, then `areas` and `capabilities` are empty lists and the format 3 fields are unchanged.

The tool:
- **AC-6** Given a valid model, when `build` runs twice, then both runs exit 0 and every file is byte-identical, and `check` then exits 0.
- **AC-7** Given a built folder, when an area view is removed and `check` runs, then it exits 1 listing the area's two files and its pack file as `extra`, and the overview as `changed`; when `build` then runs, those files are gone.
- **AC-8** Given a built folder whose files have CRLF line endings, when `check` runs, then it exits 0.
- **AC-9** Given an output folder holding a file without the marker, or an unknown subfolder, when `build` runs, then it exits 2 with `out-error` and no file in the folder changes; when `check` runs, it also exits 2 with `out-error`.
- **AC-10** Given `--out` outside the repository, equal to the model folder, inside `decisions`, or reached through a link, when `build` runs, then each exits 2 with `out-error` and nothing is written.
- **AC-11** Given invalid records, when `build` runs, then it exits 2 with the same `record-error` lines `export` gives, and nothing is written.
- **AC-12** Given element, decision and step text holding `[x](javascript:alert(1))`, `<script>`, `|`, a backtick run, a line feed, `%%{init}%%` and an escape sequence, when `build` runs, then no Markdown file holds an unescaped link, tag or table break, no HTML file holds an unescaped value, no diagram holds `%%`, and no file holds an escape character.
- **AC-13** Given a valid model, when `build` runs, then every HTML page carries the Content-Security-Policy as stated, with the hash of its start-up script, has exactly two `<script>` elements (the pinned Mermaid URL with its integrity hash, and the start-up script), and every Markdown and HTML file starts with the marker line.

Documents:
- **AC-14** Given two areas sharing an element and a capability through both, when `build` runs, then the overview links both areas and the capability, each area lists the shared element, and the capability's steps link each end to its first area by name.
- **AC-15** Given an area with a known-gap entry, a runtime link and a relationship implied by a more specific one, when `build` runs, then the area diagram draws the gap red and labelled, the runtime link dashed with its kind, and not the implied relationship.
- **AC-16** Given a cross-cutting decision binding elements in two areas and a principle, when `build` runs, then both areas print the decision in full with "Also binds" naming the other, and the principle is printed in full only in the overview.
- **AC-17** Given an area with more than 80 arrows, when `build` runs, then its diagram is replaced by the note and its tables are complete.
- **AC-18** Given a change file that adds an element, changes a decision, removes a contract and adds an element a later change removed, with `approved` null, when `build` runs, then the change record shows "Not yet approved", the added element in its diagram, the decision in full, the removed contract as plain text, the gone element marked "(not in the current model)", and the decision's rejected options under "Choices not taken".
- **AC-19** Given one item of each improvement kind, when `build` runs, then `improvements.md` lists the seven groups in order, each with its count and its item.
- **AC-20** Given a decision binding only an element in no area, and a contract with no area, when `build` runs, then both are printed in full in the overview's "Not in any area" section, and links to them point there.
- **AC-21** Given a left-over `.architecture-docs-` temporary file and a built folder whose only capability is then removed, when `check` runs, then it does not mention the temporary file; when `build` runs, then the temporary file and the empty `capabilities` and `pack/capabilities` folders are gone.
- **AC-22** Given decision text holding a line `# Heading` and an element title holding a line feed, when `build` runs, then the pack holds the line as `\# Heading` and the title on one line, and the pack shows ids unescaped.
- **AC-23** Given a valid model, when `build` runs, then in the pack every element, decision, contract and capability id is in the pack index, every id outside a slice is followed by its pack file, and `pack/model.json` holds the export under `export`.

## Future work (downstream cost)

| Item | Priority | Effort | Where |
|---|---|---|---|
| The skill builds documents after each run and its review reads them; judgement goes into records | P1 | M | #31 A3b |
| `check` in CI; dependency-file verification | P1 | S | #35 A7 |
| Convert the downstream model: area and capability views, `capabilities` names | P1 | M | #36 A8 |
| Mermaid upgrades: new version and hash, by hand | P3 | S | As needed |
| A pack slice per element or per decision, if agents need finer cuts | P3 | S | Only on evidence |

## Assumptions surface

| # | Assumption | Status |
|---|---|---|
| A1 | LikeC4 1.60.0 gives element titles and descriptions, relationship titles, and views with id, type, title, nodes and, for dynamic views, steps in order with their source, target and label. | VERIFIED: scratch model probed through `computedModel()`: elements, relationships, views `area-shop` (element) and `capability-order` (dynamic) with steps `step-01`, `step-02`. |
| A2 | LikeC4 links a reply step to no relationship, so the step rule must allow replies itself. | VERIFIED: same probe, step `api -> web` had an empty relations list. |
| A3 | `export` today prints format 3 with no titles, descriptions or views. | VERIFIED: `report.mjs` `exportJson`. |
| A4 | The records reader reads only its named folders, so a `generated` folder in the model folder is ignored by it. | VERIFIED: `records.mjs` `FOLDERS`, `listFolder`. |
| A5 | The model-folder walk counts every file toward its limits and refuses links. | VERIFIED: `walk.mjs` `walkModelDir`. |
| A6 | The gap file is read by `parseGap`, with `from`, `to`, `reason` and optional `close_by`, from `<model>/known-gap.json` by default. | VERIFIED: `inputs.mjs` `parseGap`; `architecture-delta.mjs` line 75. |
| A7 | Mermaid 12.2.0 is released (2026-10-13) and its single browser file is on the CDN. | VERIFIED: `npm view mermaid time`; HTTP 200 and sha384 hash of `dist/mermaid.min.js`. |
| A8 | The Mermaid npm package is too large to depend on (123 MB unpacked). | VERIFIED: `npm view mermaid dist.unpackedSize`. |
| A9 | No model uses `capabilities` in its records yet. | VERIFIED: the one downstream model still uses `architecture.md` (owner, 2026-11-16); in the engine tests it appears in the records spec's AC-19 export test (changed, see Scope) and in two shape-only tests that pass 4 does not reach (`tests/scripts/test_architecture_delta_records.py` lines 83, 466, 485). |
| A10 | The owner chose: Mermaid from a CDN; titles and views through `export`; committed output in `<model>/generated`; areas and capabilities as named views; capability names checked; labels only for timing; an overview document; the four approved design sections. | VERIFIED: owner answers and approvals, 2026-11-17. |
