# Architecture documents generated from the model

Work items: #32 (A4, model pack), #33 (A5, architecture book), #34 (A6, change record and improvement list), parts of #37. Amends `2026-11-17-architecture-model-records-design.md` (capability names), `2026-11-16-architecture-delta-runtime-links-design.md` (`export` format) and `2026-11-09-architecture-delta-tool-design.md` (the model-folder walk).

> Amended by #43: a change record whose change file lists `relationships` draws only what the change did, as a model diagram and a known-gap diagram (Change record, below; AC-31).

## Why

The architecture model is the single source of truth, but only a tool or a patient reader can use it as it stands: a `.c4` folder and JSON records. Architects, the product team, senior engineers and AI agents each need a readable cut of it: the whole system, one area, one process, what a change did, and what to improve. The first run built those cuts by hand with one-off scripts, and they went stale the moment the model changed (`docs/field-reports/2026-11-16-defining-architecture-first-run.md`, F9, F12, R5). This work item makes them a generated, checked part of the model.

## What this work item owns

- What `export` prints about element and relationship titles, area views and capability views (format 4), and the rules that keep those views honest, applied wherever the model is loaded.
- Two records rules: a `capabilities` entry names a capability view; a change file's name, without `.json`, is at most 64 characters.
- A new tool, `architecture-docs.mjs`, beside the delta tool, that writes the documents into one output folder (`build`) and reports when they are stale (`check`).
- What each generated document holds.

It does not own the skill's steps (#31 part A3b), running `check` in CI or verifying a dependency file (#35, A7), or converting an existing model (#36, A8).

## Terms

- **Inside.** Element ids are dotted paths. X is **inside** Y when X's id starts with Y's id followed by `.`. X's **parent** is its id up to the last `.`; a **top-level** element has no `.` in its id; a **child** of Y is an element whose parent is Y.
- **Open question** is a hole record (`holes` in a decisions file).
- **Principle** is a decision with `obligations`, empty `binds` and no `owner`. **Cross-cutting** is a decision with `obligations`.
- **First** means sorted in UTF-16 code-unit order (names, ids, paths).

## Areas and capabilities

An **area** is a LikeC4 element view whose id is `area-<name>`. Its **elements** are:
- for a scoped view (`view area-x of E`): E and every element inside E, whatever the view's include rules draw;
- for an unscoped view: the element nodes the view draws.

Nodes that are not elements (LikeC4 `group` nodes) are ignored. In a scoped view, the neighbours `include *` draws around E are not area elements. An element may be in several areas, or in none. Its **areas** are the area views it is an element of. A record's areas are the areas of the elements it binds: a decision's or open question's `binds`, a contract's `owner` and `bound`. A record with no such element, including one with empty `binds`, has no area.

A **capability** is a LikeC4 dynamic view whose id is `capability-<name>`. Its steps, in order, say how the elements work together for one process. Steps in a LikeC4 `parallel` block are taken in the order LikeC4 lists them, and all steps are numbered from 1 in that order. Each step must follow a relationship already in the model:

- A relationship **matches** a step from A to B when its source is A or inside A, and its target is B or inside B.
- A step is a **call** when some relationship matches it from A to B; it is a **reply** when none does but one matches it from B to A (a response to an earlier call). Any other step is an error.
- The step carries its label (LikeC4 gives an unlabelled step the title of the relationship it follows) and the kinds of the relationships it matched: for a call those from A to B, for a reply those from B to A (a relationship with no kind counts as `uses`).

So a sequence diagram can never show an interaction the model does not have. Timing is expressed only through labels and relationship kinds (an "async" or "every 5 min" label, an `http` or `event` kind); durations and deadlines are mechanism detail and are not modelled.

`<name>` is 1 to 64 characters of lowercase letters, digits and `-`, starting with a letter or digit, and not a name Windows reserves for devices (`con`, `prn`, `aux`, `nul`, `com1` to `com9`, `lpt1` to `lpt9`). It becomes a file name, so it is safe and case cannot collide on any platform.

Other views (the default index view and any other views) are not exported and do not produce documents.

**Where the rules apply.** The view rules below and the records rule are applied when the model and records load, which every command shares: the delta tool's `export` and `check`, and this tool's `build` and `check`. The delta `check` can therefore now exit 2 on them; its output is otherwise unchanged.

## What `export` prints (format 4)

`format` is 4. Everything format 3 printed stays, in the same order, with these additions. "Id" values are cleaned as ids (cut at 200 characters, no line feeds); "text" values as record text (line feeds kept, no cut). Lists are made distinct and sorted on raw values, then cleaned, as today.

| Added | Content |
|---|---|
| each element, after `rules`: `title` (text), `description` (text or `null`) | As written; LikeC4 gives an element with no title its name. The description is its source text, plain or Markdown. |
| each `allowed` entry, after `to`, and each `runtime` entry, after `kind`: `titles` (text list) | The distinct non-empty titles of the relationships the entry stands for, sorted; empty when none has a title. |
| `areas`, after `coverage` | One entry per area view, sorted by `name`: `name` (id), `title` (text), `description` (text or `null`), `elements` (ids, sorted). |
| `capabilities`, after `areas` | One entry per capability view, sorted by `name`: `name` (id), `title` (text), `description` (text or `null`), `steps` in step order, each `{ "from", "to", "label", "reply", "kinds" }`: `from`, `to` and `kinds` ids, `kinds` sorted; `label` text or `null`; `reply` `true` or `false`. |

A view's `title` is LikeC4's title for it when that is not `null`, otherwise the view id. (LikeC4 gives a scoped view with no title its scope element's title.)

**New `model-error` lines (exit 2)**, reported after LikeC4 loads the model and before the records are read, all in one run, sorted by view id, then step. A view of the wrong type gets only its type line; the name is checked only on views of the right type, and the steps only on capability views of the right type with a valid name.

- `view <id>: an area view must be an element view` and `view <id>: a capability view must be a dynamic view`;
- `view <id>: <name> is not a valid name`;
- `view <id>: step <n>: <from> -> <to> follows no relationship`.

**Records amendment.** A decision's or a contract's `capabilities` entries are now capability names, not free text:

- pass 4 (links) reports `<value> is not a capability` at the entry's path for a name that is no capability's name, and `<value> is listed twice` at the second entry's path for a name repeated in one list;
- `capabilities` joins the keys whose values are cleaned as ids.

A change file's name, without `.json`, is at most 64 characters, the same as an area or capability name; a longer one breaks layout rule 2 and is reported in pass 1 as `not a valid file name here`, like any misnamed file. A change id is then never cut by `export` (which cuts ids at 200 characters), so it always names one change document.

**Model-folder walk amendment.** The folder `generated` at the root of the model folder is walked as before for links and config files, and a LikeC4 source file (`.c4`, `.likec4`, `.like-c4`) in it is a `model-error`. The folder's name is matched in any case, and walk errors name paths with `/` on every platform. Its files count toward their own limits (2,000 files, 50 MB), not the model folder's, so generated documents can never push the model over its limits; going over them is `model-size`, as for the model folder.

## The tool

`node <skills-dir>/shared/scripts/architecture-docs.mjs <command> --repo <path> [--model <dir>] [--gap <file>] [--out <dir>] [--timeout <s>]`

| Command | Does | Exit |
|---|---|---|
| `build` | Checks `--out` (write rules 1 and 2), then loads the model, the records and the known-gap file exactly as the delta `check` does (same rules and errors, same `--model`, `--gap` and `--timeout` defaults), builds every document, and writes them. Prints `wrote <n> files, removed <m>`. | 0; 2 on any error |
| `check` | The same checks and loading; builds every document in memory and writes nothing. Prints one line per file that is missing, differs, or is no longer produced (`missing <path>`, `changed <path>`, `extra <path>`, paths relative to `--out` with `/`, sorted by path), then `<m> missing, <c> changed, <e> extra`. A missing `--out` folder makes every file `missing`. | 0 current; 1 stale; 2 on any error |

One build writes the whole set, so the links between documents always agree. Errors use the delta tool's format (`error: <token>: <detail>`), with one new token, `out-error`. Because `--out` is checked before the model loads, a problem in the output folder is always `out-error`, never a model-walk token.

Known-gap entries are cleaned like `export` output before any document uses them: `from` and `to` as ids, `reason` and `close_by` as text.

**The output folder.** `--out` defaults to `<model>/generated`.

**Write rules.**

1. `--out` must resolve, through real paths, inside `--repo`. It must not contain the model folder, and when it lies inside the model folder it must be exactly `<model>/generated` (the only folder the model walk counts apart); no existing part of the path below `--repo` may be a link. Otherwise `out-error`.
2. **The tool owns the folder.** Every Markdown and HTML file it writes starts with the line `<!-- Generated by architecture-docs from the architecture model. Do not edit. -->`, and its JSON file is an object whose first key is `"generated": "architecture-docs"`. `build` and `check` list the folder first: a link, a folder the layout below does not name, a file over 50 MB, or an unmarked file gives `out-error`, and `build` writes nothing. The folder may hold at most 2,000 files and 50 MB in all, or `out-error`; only regular files and named folders. A `.md` or `.html` file is marked when its first line (read up to 4 KB, after removing a byte-order mark and a trailing CR) is the marker line; a `.json` file is marked when it parses as an object whose first key is `generated` with the value `architecture-docs`; any other file is unmarked. Exempt from the marker: the temporary files of rule 3, and the operating-system files `.DS_Store`, `Thumbs.db` and `desktop.ini`, which are left alone. So the tool never overwrites or deletes a file a person wrote.
3. `build` writes every file to a temporary name (`.architecture-docs-<number>-<number>`) in its folder and renames it into place, then deletes the marked files it no longer produces (a file whose name differs from a produced one only in letter case counts as produced), then removes named folders left empty; it creates `--out`, its named folders and any missing parent inside `--repo` as needed. A failed write, rename or delete stops with `out-error` naming the path. A build that stops part-way leaves whole files only, possibly a mix of old and new, which `check` reports. A file is a left-over temporary file only when its name has exactly that form; a later `build` removes any it finds, and `check` ignores them.
4. **Limits.** A build whose output would exceed 2,000 files or 50 MB stops with `out-error` before writing. Every change file adds two output files, so a model holds at most about 1,000 change files, fewer by its other documents; past that `build` stops with `out-error`, as for any output over the limit.
5. **The output is deterministic**: no timestamps or run-dependent values, a fixed order everywhere, LF line endings, UTF-8 with no byte-order mark. `check` compares after turning CRLF into LF, so a checkout that converts line endings is not reported stale.

**Layout of the output folder.**

```
generated/
  README.md, index.html                      overview
  areas/<name>.md, areas/<name>.html          one per area
  capabilities/<name>.md, <name>.html         one per capability
  changes/<id>.md, changes/<id>.html          one per change file
  improvements.md, improvements.html
  pack/README.md                              AI pack index and facts outside any area
  pack/areas/<name>.md
  pack/capabilities/<name>.md
  pack/model.json
```

**Writers.** Each document is first built as a tree of headings, paragraphs, lists, tables, code blocks, links and diagrams. A Markdown writer and an HTML writer turn the tree into text. There is no Markdown parser. Links go to documents, not to anchors inside them.

- **Markdown** (all documents except the pack): model text outside code blocks is escaped. The ASCII punctuation `\ ` `` ` `` `* _ { } [ ] ( ) # + - . ! | = ~ $` is backslash-escaped and `< > &` are written as entities, so record text cannot open a link, an HTML tag, a code span, a heading or a table break. A block's leading spaces and tabs are written as `&#32;` and `&#9;`, so an indented block cannot become a code block. In a table cell, line feeds become spaces. A code block's content is not escaped; its fence is longer than any run of backticks in it. Bare URLs in text may still be turned into links by renderers that do that; only `http`, `https` and `mailto` are, which is accepted. Diagrams are fenced `mermaid` blocks.
- **Pack text:** the pack is read raw by agents, so ids and text are written as `export` gives them, unescaped. The fields of each kind are listed under "Pack fields". The line separators U+2028 and U+2029 count as line feeds. Line feeds become spaces in one-line fields; in a multi-line field every line is kept, and a line starting with `#`, `---`, three backticks or `~~~` gets a leading `\`, so record text cannot start a heading, a separator or a code fence. A line in a multi-line field can still read like a field line (`status: current` inside a reason); the pack does not guard that, and `pack/model.json` is the exact source.
- **HTML:** every value is HTML-escaped. Each page carries `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">` and no script, so a page reads the same in a viewer that runs no scripts. Diagrams are SVG drawn at build time (below), inline in a `<div class="diagram">` that scrolls sideways when the diagram is wider than the page; each table likewise sits in a `<div class="table">` that scrolls sideways, keeping the table's semantics. The page declares `color-scheme: light dark` and sets its text, background, borders and diagram colours for each `prefers-color-scheme`, so one page reads in a light and a dark viewer; known-gap arrows are red in both. Links between pages are relative.
- **Diagrams (Mermaid, in Markdown):** node and participant ids are generated (`n1`, `n2`, … in element id order), never element ids. In every label, line feeds become spaces and every character other than ASCII letters, ASCII digits, space and `.'/_-` is written as a Mermaid entity `#<decimal code>;`, which Mermaid decodes before parsing. So no label can close its quotes, end a sequence message (`;`, `:`), or hold `%%`. Flowchart labels are quoted (`n1["…"]`); sequence diagrams use `participant n1 as …` and `n1->>n2: …` (calls) or `n2-->>n1: …` (replies), unquoted.
- **Diagrams (SVG, in HTML):** flowcharts are laid out by Graphviz `dot`, left to right, through `@hpcc-js/wasm-graphviz` (Graphviz compiled to WebAssembly, run in Node): the frame is a cluster, import arrows solid, runtime arrows dashed, known-gap arrows red. Every label goes to Graphviz as an HTML-like label with its text XML-escaped. Graphviz expands escape sequences such as `\N` (the node name) even there, so a word joiner (U+2060) follows every backslash, and the SVG drops every word joiner; Graphviz XML-escapes the text it writes. Sequence diagrams are drawn by the tool: participant boxes in columns in the order given, a lifeline under each, one row per step in step order, calls solid and replies dashed, each with its label above it; a step from a participant to itself is a loop. The SVG keeps only drawing: no XML prolog, doctype, comment, title, link or script, and no background fill; lines and text use the page's text colour. The same model gives the same SVG. Text widths are estimated (Graphviz's built-in font metrics; 7 pixels a character in sequence diagrams), so a viewer font that is much wider, or wide CJK or emoji text, can run past a box. A lone surrogate or a non-character in a label is drawn as U+FFFD.

## What each document holds

**Shared rules.** Every fact comes from `export` or the known-gap file. Ids are shown as written, titles beside them. Each id links to the document that holds it: an element to its first area's document (or the overview, for an element in no area), a decision, contract or open question to its first area's document (or the overview, when it has none), a principle to the overview, a capability and a change to their own documents. A flowchart (overview, area, change record) with more than 80 arrows (after the drawing rules) is drawn only in its HTML page, and the Markdown document shows a note saying so; with more than 400 arrows it is drawn in neither and both show a note. A capability's sequence diagram when the capability has more than 200 steps is replaced by a note in both; the arrow limit does not apply to sequence diagrams, and the tables still list everything.

**Drawing rules** (area and change-record diagrams). The diagram has **framed** elements (an area's elements) and **neighbours**: each element outside the frame at the other end of an import or runtime relationship, or of a known-gap entry, with a framed element, drawn as itself and labelled `<title> (<first area's name>)`, or `<title> (no area)`. A diagram holds no `click` lines: the links to a neighbour's area are in an area document's Dependencies section (a change record has none, so there the label alone names the area), and the Markdown diagram and the HTML page's SVG are drawn from the same nodes and arrows. The framed elements are drawn flat, as nodes in one frame; an element inside another framed element is a separate node, not a nested frame. Only arrows with at least one framed end are drawn; arrows between two neighbours are not. Arrows come in three styles: import (solid), runtime (dashed, labelled with its sorted kinds, then its sorted titles in double quotes, joined by `, `) and known gap (red, labelled `known gap`, for a known-gap entry whose two ends are both drawn). Within the import or the runtime style, an arrow from X to Y is not drawn when the same style has a drawn arrow (one with at least one framed end) from X' to Y' where X' is X or inside X, Y' is Y or inside Y, and at least one of X', Y' is strictly inside (it is implied by the more specific one). Known-gap arrows are never hidden and never hide others. Several relationships of one style between the same two elements are one arrow. A neighbour is drawn only when at least one of its arrows is drawn; a neighbour whose arrows are all hidden is left out (the Dependencies section still lists it).

**Overview** (`README.md`).
- The heading "Architecture", and a diagram of the top-level elements, with each relationship lifted to the top-level elements that hold its ends; a relationship within one top-level element is not drawn. One arrow per pair: solid when any lifted relationship is an import; otherwise dashed, labelled with the sorted kinds.
- Areas: title, description, element count, link. Capabilities: title, description, the areas they pass through, link.
- Principles, in full.
- Contracts: name, owner, bound elements, compatibility, link.
- Changes, newest date first, then by id in ascending order, with summary and approval.
- Model health: the number of known-gap entries and of open questions; the coverage answer (or "No coverage file"); the number of unmapped modules; each linking to the improvement list.
- **Not in any area:** the elements in no area, with title and description; then, in full, every decision (other than a principle), contract and open question that has no area.

**Area** (`areas/<name>.md`).
- Title and description.
- **Diagram** by the drawing rules, the area's elements framed.
- **Elements:** id, title, description, code, rules, tags.
- **Dependencies:** for each area element, what it may use and what may use it, and its runtime links, each with the other end's areas (or "Not in any area").
- **Decisions** binding any area element, cross-cutting first, by id within each, each in full: decision, reason (or "Reason not known"), rejected, obligations, owner, compatibility, capabilities, status and superseded_by, evidence, sources, note, and "Also binds: <areas>". Principles have no area and appear only in the overview.
- **Contracts** whose owner or bound elements are in the area, in full; **open questions** binding area elements; **known-gap entries** with an end in the area, with reason and `close_by`; **capabilities** with a step whose end is an area element.

**Capability** (`capabilities/<name>.md`).
- Title and description.
- A sequence diagram: participants in order of first appearance, labelled with their titles; calls solid, replies dashed, each with its label.
- **Steps:** number, from, to, label, call or reply, kinds; each end linking to its area.
- The decisions and contracts that name this capability, in full; the areas involved (the areas of every step's ends, and "Not in any area" for an end in none).

**Change record** (`changes/<id>.md`).
- Summary, asked by, run, date, and approval (by and date, or "Not yet approved").
- A diagram by the drawing rules, the elements the change added or changed that are still in the model framed, in a frame labelled with the change id. Each framed node is labelled `<title> (added)` or `<title> (changed)`; an id listed as both added and changed is marked `added`. No diagram when there are none.
  When the change file lists `relationships`, the section instead shows only what the change did, in two diagrams, each under its own level-3 heading and each left out when it would be empty. No unchanged relationship is drawn in either; the area documents show the context.
  - **Model changes:** the frame holds the same elements, with the same labels. The arrows are each added or changed relationship in its style (import solid, runtime dashed and labelled as the drawing rules say) and each removed relationship dashed and labelled `removed` (a runtime one `removed, <kind>`), except a removed import relationship whose pair is an added gap pair, which is drawn only in the known-gap diagram. Left out when there is neither a framed element nor an arrow.
  - **Known-gap changes:** no frame; each added gap pair red, unlabelled, and each removed gap pair dashed and labelled `gap closed`. Left out when the change added and removed no gap pair.

  In both, no arrow is hidden as implied, and arrows between two unframed elements are drawn. The other nodes are the ends of the arrows, labelled as neighbours, and an end no longer in the model is labelled `<id> (not in the current model)`. An import relationship whose titles alone changed is drawn like an added one; What changed tells them apart. When both are left out, the section says so in one paragraph. The 80- and 400-arrow limits apply to each diagram as for any flowchart.
- **What changed:** elements, relationships (when the change file lists them, each as `<from> -> <to>: <kind>`, the kind `import` for an import relationship, each end shown as a known-gap end is), decisions, contracts and open questions, each as added, changed, removed, each list as the change file gives it (an id in two lists is shown in both). Added and changed records still in the model are printed in full as they stand now; the change file holds only ids. Removed ids are plain text; an added or changed id no longer in the model is plain text with "(not in the current model)".
- **Choices not taken:** the change's `rejected` list, then the `rejected` options of each decision it added or changed that is still in the model.
- **Known gap:** the pairs it added and removed, each as `<from> -> <to>`, with no reason (the change file holds only pairs). Each end links to its document when it is a model element, and is otherwise plain text with "(not in the current model)".
- **Check:** exit, summary, and the output in a code block.

**Improvement list** (`improvements.md`). Facts only; nothing judged or ranked. Groups in this order, each with its count, items sorted by id or by pair:
1. Cycles in current code: known-gap entries whose reason is `cycle in current code`.
2. Other known breaches: the other known-gap entries, with reason and `close_by`.
3. Open questions, with the elements they bind.
4. Decisions not yet fully built: `status` is `partly-built` or `planned`.
5. Decisions with no known reason: `reason` is `null`.
6. Unmapped code: the coverage file's `unmapped` entries with their reasons (the build reads no dependency file); none when there is no coverage file.
7. Elements in no area.
8. Elements that own nothing: no `code`, no child, kind not `external`, and not a coverage edge node (none is, when there is no coverage file).

Each group is a heading `<group name> (<count>)`, followed by "None." when it has no items; unmapped-code items are sorted by module. Each item names its id (or pair, or module) with its title, then its details (a known-gap entry's reason and `close_by`, an open question's bound elements, a decision's status, an unmapped entry's reason), then `Areas: <links>`, or "Not in any area" when it has none. Each item links to its areas (for a known-gap entry, both ends'). Unmapped-code items are modules, not elements, so they have no areas part. A judgement on how the architecture should improve is not generated: a `defining-architecture` run records it as an open question or a proposed decision, and it then appears here (A3b).

**AI pack** (`pack/`). The same facts in a compact form, for an agent to load only the slice it needs.
- `pack/README.md`: how the pack is laid out; an index from every element, decision, contract, open question and capability id to the pack files that hold it; then the facts outside any area: the principles, the elements in no area, and the decisions, contracts and open questions with no area, in full.
- `pack/areas/<name>.md`: one block per area element, then the area's decisions, contracts, open questions and known-gap entries (as in the area document), in full, then the capabilities with a step whose end is an area element; no diagrams.
- `pack/capabilities/<name>.md`: the steps, one block per element they touch, then the decisions and contracts that name the capability, in full.
- Every id not held in the slice is followed by its **pack file** in brackets: the first area's pack file, or `README.md` for a fact outside any area; a capability's pack file is its own slice. The bracket follows the id and any note in brackets that belongs to it (`D-3 (cross-cutting) [areas/x.md]`, `-> pay (http, "charges card") [areas/payments.md]`).
- `pack/model.json`: `{ "generated": "architecture-docs", "export": <the format 4 export> }`.

**Pack layout.** Each pack file starts with the marker line, then `# ` and its title: `Architecture pack` for the index, `<name>: <title>` for a slice. Then, in this order, the sections that have content (an empty section is left out):
- `pack/README.md`: a paragraph saying how the pack is laid out; `## Index`; `## Principles`; `## Elements in no area`; `## Decisions in no area`; `## Contracts in no area`; `## Open questions in no area`.
- `pack/areas/<name>.md`: the area description; `## Elements`; `## Decisions` (cross-cutting first, by id within each); `## Contracts`; `## Open questions`; `## Known gap`; `## Capabilities`.
- `pack/capabilities/<name>.md`: the capability description; `## Steps`; `## Elements`; `## Decisions`; `## Contracts`.

Within a section, elements and records are in id order (an area's decisions excepted, as above).

**Pack fields.** One-line fields: titles, contract names, step labels, relationship titles, list items, `evidence`, `compatibility`, and a known-gap entry's `reason` and `close_by`. Multi-line fields: descriptions, a decision's `decision`, `reason` and `note`, and an open question's `what` and `note`.

**Index.** Under `## Index`, one `### ` heading per kind that has ids (a kind with none is left out, like an empty section), in the order Elements, Decisions, Contracts, Open questions, Capabilities, each followed by one line per id, sorted: `<id>: <file>, <file>`, naming every pack file that holds the id in full, sorted by path. An element is held by each of its areas' slices, each capability slice with a step that touches it, and `README.md` when it is in no area. A decision, contract or open question is held by each of its areas' slices, each capability slice that names it (decisions and contracts), and `README.md` when it has no area (every principle). A capability is held by its own slice.

Element block (the example below shows every line; a line or a `·` part with nothing to show is left out):

```
### shop.orders: Orders
kind container · tags #layer · code shop.orders · rules BR-1, BR-4
Takes and tracks orders.
uses: shop.billing, shop.catalog [areas/catalog.md]
used by: shop.web
runtime: -> payments.gateway (http, "charges card") [areas/payments.md]
runtime: <- shop.jobs (event)
bound by: D-3 (cross-cutting), D-7
```

- Each tag is written with a leading `#`, tags separated by spaces; `code` and `rules` entries are separated by `, `.
- `uses` lists the `to` of each `allowed` entry from the element, `used by` the `from` of each entry to it, sorted.
- One `runtime` line per runtime link the element is an end of: `->` for a link from it, `<-` for one to it, then the other end, the kind and the link's titles in quotes. Outgoing lines come first, then incoming, each sorted by the other end, then kind.
- `bound by` lists the decisions whose `binds` hold the element, by id, a cross-cutting one marked `(cross-cutting)`.

Record blocks use the same form: `### <id>` (`### <id>: <name>` for a contract), the record's main text on the next line (a decision's `decision`, an open question's `what`), then one `<key>: <value>` line per field the record has, leaving out a list field whose list is empty, in this order (decision: reason, rejected, obligations, owner, compatibility, capabilities, status and superseded_by, evidence, sources, note, binds; contract: owner, bound, obligations, compatibility, notes, decisions, capabilities; open question: binds, evidence, note). Text lists are joined with `; `, id lists with `, `. A decision with no reason shows `reason: not known`; a contract with no compatibility rule shows `compatibility: no rule stated`.

Known-gap lines, under `## Known gap`, sorted by pair: `- <from> -> <to>: <reason>`, then ` (close by <close_by>)` when it has one.

Capability lines, under an area slice's `## Capabilities`, sorted by name: `- <name>: <title> [capabilities/<name>.md]`.

Step lines, under `## Steps`: `<n>. <from> -> <to>: <label> (<kinds>)` for a call, and `<n>. <from> -> <to> (reply): <label> (<kinds>)` for a reply. `: <label>` is left out when the step has no label.

## Compatibility

A model with no area or capability views exports as before apart from `format` 4 and the new fields and empty lists. Its documents are the overview, the improvement list, the change records, the pack index and `pack/model.json`, each Markdown document with its HTML page, and every element is under "Not in any area". A record using `capabilities` as free text now fails pass 4; no model uses that field yet. A model whose folder already has a `generated` folder holding `.c4` files now fails to load; no known model has one. Readers of `export` that check `format` must accept 4.

## Scope

- The delta tool: element and relationship titles, area and capability views, the view rules, `format` 4, the walk amendment; the records capability rule and the change-file name limit. Tests beside the existing delta tests. Existing tests change only where they assert `format` or the exact element and relationship objects, and in the records spec's AC-19 test, whose capability `Pay` becomes `pay`, the name of a capability view it adds to its model.
- The new tool: `skills/shared/scripts/architecture-docs.mjs` and its modules in `skills/shared/scripts/architecture-docs/` (not in `architecture-delta/`, whose source test forbids writes), reusing the delta modules; tests in `tests/scripts/`.
- `ARCH_STANDARDS.md`: one line each for `format` 4, the area and capability view naming, and the new tool's two commands. The rest of the skill text is A3b.
- Amendment notes in the records spec, the runtime-links spec and the delta tool spec.

**Out of scope:** CI wiring and dependency-file verification (A7); the skill's steps (A3b); converting a model (A8); serving, watching, PDF; any judgement-based content.

**Shard evaluation.** One spec, because the documents share one tree, one set of writers and one link scheme, and their rules must be reviewed together. It is too large for one plan, so it is planned and built as four plans in order, each on its own branch and each within the two-entry-path rule, as the records spec was (A3a, A3c). The work items already exist; each plan names its issue: (1) `export` format 4, the view and records rules and the walk amendment (#32); (2) the tool, write rules, `check`, writers, overview and pack (#32); (3) area and capability documents (#33); (4) change records and the improvement list (#34).

## Threat Model (CIA)

| Pillar | Vector | Defence and proof |
|---|---|---|
| Confidentiality | The tool reads outside the repository. | It reads what the delta `check` reads, through the same path rules (`paths.mjs` `resolveInside`; `walk.mjs` `walkModelDir` refuses links), plus the files in `--out`, which write rule 1 keeps inside `--repo`; a Markdown or HTML file is read only up to 4 KB to find its marker, a JSON file in full to find its first key, and in `check` a marked file in full to compare it; no file over 50 MB is read (rule 2). |
| Integrity | The tool overwrites or deletes a person's file, or writes outside its folder. | Write rules 1 and 2: `--out` resolved by real path inside `--repo`, outside the model's own files, no links; an unmarked file stops the build before any write. A source test finds every file-write call of the tool in one writer module. |
| Integrity | Model, record or known-gap text injects Markdown links, HTML, Mermaid directives, Graphviz escapes or terminal sequences into a document. | Model and record text is cleaned by `export` (`errors.mjs` `clean`, `cleanText` remove escape and control characters); known-gap entries are cleaned the same way before use; the Markdown writer escapes punctuation; the HTML writer escapes every value under a CSP; diagram labels are entity-encoded and node ids generated. AC-12 feeds hostile text through each writer. |
| Integrity | A sequence diagram shows an interaction the model does not have. | The step rule: every step matches a relationship, or `model-error`. AC-2, AC-3. |
| Integrity | A script runs in a reader's browser, from a page or from a diagram. | Pages carry no script and the Content-Security-Policy allows none; SVG is written by Graphviz from entity-encoded labels, or by the tool from escaped text, and keeps only drawing elements. AC-13, AC-28. |
| Availability | A huge model produces huge documents or slow builds, or generated files make the model unloadable. | The model folder limits (2,000 files, 50 MB) and the 5,000-element cap bound the input; the output has its own limits (write rule 4) and the walk counts `generated` separately; change records count toward the output limits, so the number of change files a model can hold is bounded (write rule 4); flowcharts over 400 arrows (over 80 in Markdown) and capabilities over 200 steps are replaced by notes; the `--timeout` deadline is checked after loading and after each document. |
| Least privilege | The tool needs file writes the delta tool does not have. | Writes only inside `--out`; no `child_process`, no `worker_threads`, no network module (source test, as `tests/scripts/test_architecture_delta_safety.py` does for the delta tool, which keeps its no-write test unchanged). |
| Supply chain | Graphviz at build time. | `@hpcc-js/wasm-graphviz` 1.29.2, pinned in `package.json`: the version LikeC4 1.60.0 already installs, so no new download. One JavaScript file with the WebAssembly inside; it uses no `child_process`, worker or network module (a source test scans the installed file). The tool finds it as it finds LikeC4: the repository's copy, then the plugin's, each by real path inside its root, and only at 1.29.2, because the SVG bytes `check` compares depend on the version; with neither, `build` and `check` stop with `graphviz-missing` and an install hint. Graphviz 16.1.0. No page loads Mermaid; Markdown keeps Mermaid fences for renderers that draw them. |

## Acceptance criteria

`export` and loading:
- **AC-1** Given a model with element and relationship titles and descriptions, a scoped area view with no title, an unscoped area view with a title, and a capability view with no title, when `export` runs, then `format` is 4, each element has its `title` and `description` after `rules`, each `allowed` and `runtime` entry its sorted `titles`, and `areas` and `capabilities` follow `coverage`, with titles: the scope element's title, the written title, and the view id.
- **AC-2** Given a capability with a step along a relationship, a step against one, and a step to an element that holds a relationship's target (the relationship runs to an element inside the step's target), when `export` runs, then the steps are a call, a reply and a call, in view order, each with its kinds.
- **AC-3** Given a capability step that follows no relationship either way, an `area-` dynamic view, a `capability-` element view, an `area-Shop` view and an `area-con` view, when `export` runs, and again when the delta `check` runs, then each exits 2 with five `model-error` lines sorted by view id, and the step line names the step number.
- **AC-4** Given a decision whose `capabilities` names a capability view and a contract whose `capabilities` names none and repeats a name, when `export` runs, then the lines are `… is not a capability` and `… is listed twice` at the contract's paths, and nothing for the decision.
- **AC-5** Given a model with no area or capability views, when `export` runs, then `areas` and `capabilities` are empty lists and the format 3 fields are unchanged.
- **AC-6** Given a scoped area view `of shop` with `include *`, where `shop` has a grandchild the view does not draw and a relationship to an element outside `shop`, and a view using a `group`, when `export` runs, then the area's `elements` are `shop` and every element inside it, without the outside element or the group node.
- **AC-7** Given a model folder with 600 files of its own and a `generated` folder holding 1,500 files, when `export` runs, then it exits 0; given 2,001 files in `generated`, then it exits 2 with `model-size`; given a `.c4` file in `generated`, then it exits 2 with `model-error`.

The tool:
- **AC-8** Given a valid model, when `build` runs twice, then both runs exit 0 and every file is byte-identical, and `check` then exits 0.
- **AC-9** Given a built folder, when an area view is removed and `check` runs, then it exits 1 listing the area's two files and its pack file as `extra`, and the overview as `changed`; when `build` then runs, those files are gone.
- **AC-10** Given a built folder whose files have CRLF line endings, when `check` runs, then it exits 0.
- **AC-11** Given an output folder holding a file without the marker, an unknown subfolder, or a link, when `build` runs, then it exits 2 with `out-error` and no file in the folder changes; when `check` runs, then it also exits 2 with `out-error`; given only a `.DS_Store`, `build` exits 0 and leaves it.
- **AC-12** Given element, decision, step and known-gap text holding `[x](javascript:alert(1))`, `<script>`, `|`, `;`, a backtick run, a line feed, `%%{init}%%` and an escape sequence, when `build` runs, then no Markdown file holds an unescaped link, tag or table break, no HTML file holds an unescaped value, no Mermaid diagram label holds `;`, `"` or `%%`, and no file holds an escape character.
- **AC-13** Given a valid model, when `build` runs, then every HTML page carries the Content-Security-Policy as stated, holds no `<script`, and draws each diagram as an inline `<svg>`; and every Markdown and HTML file starts with the marker line.
- **AC-14** Given `--out` outside the repository, equal to the model folder, inside `decisions`, equal to `<model>/docs-out`, or reached through a link, when `build` runs, then each exits 2 with `out-error` and nothing is written.
- **AC-15** Given invalid records, when `build` runs, then it exits 2 with the same `record-error` lines `export` gives, and nothing is written.
- **AC-16** Given a model whose output would exceed 2,000 files, when `build` runs, then it exits 2 with `out-error` and nothing is written.
- **AC-17** Given a left-over `.architecture-docs-` temporary file and a built folder whose only capability is then removed, when `check` runs, then it does not mention the temporary file; when `build` runs, then the temporary file and the empty `capabilities` and `pack/capabilities` folders are gone.

Documents:
- **AC-18** Given two areas sharing an element and a capability through both, when `build` runs, then the overview links both areas and the capability, each area lists the shared element, and the capability's steps link each end to its first area.
- **AC-19** Given an area with a known-gap entry, a runtime link, an import and a runtime link between the same two elements, an import implied by a more specific one, and a relationship between two neighbours, when `build` runs, where the gap runs to an element with no relationship to the area, then the area diagram draws that element as a neighbour labelled with its title and first area, and the gap red and labelled, both arrows of the shared pair, the runtime link dashed with its kind, and neither the implied import nor the neighbours' arrow.
- **AC-20** Given a cross-cutting decision binding elements in two areas and a principle, when `build` runs, then both areas print the decision in full with "Also binds" naming the other, and the principle is printed in full only in the overview.
- **AC-21** Given an area with more than 80 arrows, a capability with 81 steps and a capability with 201 steps, when `build` runs, then the area's Markdown diagram is replaced by the note, its HTML page draws the diagram, and its tables are complete, the 81-step capability keeps its sequence diagram, and the 201-step capability's diagram is replaced by the note with all 201 steps in its table.
- **AC-22** Given a change file that adds an element, changes a decision, removes a contract and adds an element a later change removed, with `approved` null, when `build` runs, then the change record shows "Not yet approved", the added element framed in its diagram, the decision in full, the removed contract as plain text, the gone element marked "(not in the current model)", and the decision's rejected options under "Choices not taken".
- **AC-23** Given one item of each improvement kind, when `build` runs, then `improvements.md` lists the eight groups in order, each with its count and its item; given no coverage file, groups 6 and 8 treat it as described.
- **AC-24** Given a decision with empty `binds` and no obligations, and a contract with no area, when `build` runs, then both are printed in full in the overview's "Not in any area" section and in `pack/README.md`, and links to them point there.
- **AC-25** Given decision text holding a line `# Heading`, a line opening a code fence and a U+2028 line separator, and an element title holding a line feed and a U+2029, when `build` runs, then the pack holds the line as `\# Heading`, the fence line with a leading `\`, the separator as a line break, and the title on one line, and the pack shows ids unescaped.
- **AC-26** Given a valid model with a principle and an element in no area, when `build` runs, then every element, decision, contract, open question and capability id is in the pack index; every id not held in a slice is followed by its first area's pack file, or `README.md`; a capability slice holds the decisions naming it; an area slice lists each capability with a step in the area, with its pack file; and `pack/model.json` holds the export under `export`.
- **AC-27** Given a change file whose name, without `.json`, is 65 characters, and one whose name is 64 characters, when `export` runs, then it exits 2 with one `record-error` line, `changes/<the 65-character name>.json: -: not a valid file name here`, and nothing for the 64-character one.
- **AC-28** Given element, frame, arrow and step text holding `<script>`, `"`, `&`, `\N` and `\l`, when `build` runs, then each SVG shows that text literally, and no SVG holds `<script`, `<foreignObject`, `href`, an `on…=` attribute, a comment, a title or a background fill.
- **AC-29** Given any page, then its style declares `color-scheme: light dark` and a `prefers-color-scheme: dark` rule that sets the text and background colours.
- **AC-30** Given a capability with a call, a reply and a step from a participant to itself, when `build` runs, then its page draws one box per participant in the order given, the call as a solid arrow, the reply dashed, the self step as a loop, each with its label, and a second build gives the same SVG.
- **AC-31** (#43) Given a change file whose `relationships` add an import from a framed element to X, remove an import from Y to Z whose pair it adds as a gap entry, remove a runtime link, and whose gap removes a pair, where the framed element also has an unchanged relationship to W, when `build` runs, then the change record's Model changes diagram draws the added import solid and the runtime link dashed as `removed, <kind>`, and not Y to Z; its Known-gap changes diagram draws Y to Z in red and the removed gap pair dashed as `gap closed`, with no frame; neither has a node or arrow for W; a change with no gap pair has no Known-gap changes diagram; its What changed section lists the three relationships; and a change file with no `relationships` gets the diagram it got before.

## Future work (downstream cost)

| Item | Priority | Effort | Where |
|---|---|---|---|
| The skill builds documents after each run and its review reads them; judgement goes into records | P1 | M | #31 A3b |
| `check` in CI; dependency-file verification | P1 | S | #35 A7 |
| Convert the downstream model: area and capability views, `capabilities` names | P1 | M | #36 A8 |
| An optional link from the overview to a `likec4 build` site, for interactive diagrams | P3 | S | On request |
| Evaluate `likec4 mcp` as a live alternative to the AI pack; it knows only the `.c4` files, not the records | P3 | S | On evidence |
| Graphviz upgrades: kept at the version LikeC4 installs, by hand | P3 | S | With each LikeC4 upgrade |
| A pack slice per element or per decision, if agents need finer cuts | P3 | S | Only on evidence |
| Archiving old change files, for a model nearing the output limit's bound on change files (write rule 4) | P3 | S | When a model nears it |

## Assumptions surface

| # | Assumption | Status |
|---|---|---|
| A1 | LikeC4 1.60.0 gives element titles and descriptions, relationship titles, and views with id, type, title, nodes and, for dynamic views, steps in order with their source, target and label. | VERIFIED: scratch model probed through `computedModel()`: elements, relationships, views `area-shop` (element) and `capability-order` (dynamic) with steps `step-01`, `step-02`. |
| A2 | LikeC4 links a reply step to no relationship, so the step rule must allow replies itself. | VERIFIED: same probe, step `api -> web` had an empty relations list. |
| A3 | A scoped `include *` view draws its scope's neighbours as nodes, a `group` gives a non-element node, and an untitled view's title is `null` (a scoped one takes its scope's title). | VERIFIED: independent audit probe of LikeC4 1.60.0. |
| A4 | `export` today prints format 3 with no titles, descriptions or views; element ids are dotted paths. | VERIFIED: `report.mjs` `exportJson`; probe ids `shop.web`, `shop.api`. |
| A5 | The records reader reads only its named folders; the model-folder walk counts every file and refuses links. | VERIFIED: `records.mjs` `FOLDERS`, `listFolder`; `walk.mjs` `walkModelDir`. |
| A6 | The gap file is read by `parseGap`, with `from`, `to`, `reason` and optional `close_by`, uncleaned, from `<model>/known-gap.json` by default. | VERIFIED: `inputs.mjs` `parseGap`; `architecture-delta.mjs` line 75. |
| A7 | Decision status values are `current`, `partly-built`, `planned`, `superseded`. | VERIFIED: `records.mjs` `STATUS`. |
| A8 | Mermaid 12.2.0 is released (2026-10-13), its single browser file is on the CDN, and it decodes `#<code>;` entities before parsing. | VERIFIED: `npm view mermaid time`; HTTP 200 and sha384 hash of `dist/mermaid.min.js`; its entity-encoding step found in that file. Superseded for HTML pages by A15: no page loads Mermaid. |
| A9 | The Mermaid npm package is too large to depend on (123 MB unpacked). | VERIFIED: `npm view mermaid dist.unpackedSize`. |
| A10 | LikeC4's own outputs do not cover these documents: `export markdown` writes one README of view diagrams into the model folder with no records; `gen mermaid` draws views as written, dynamic views as flowcharts; `build` is an interactive site; custom generators need a config file, which the walk refuses. | VERIFIED: `likec4 export markdown` and `likec4 gen mermaid` run on the probe model; `likec4 --help`. |
| A11 | No model uses `capabilities` in its records yet. | VERIFIED: the one downstream model still uses `architecture.md` (owner, 2026-11-16); in the engine tests it appears in the records spec's AC-19 export test (changed, see Scope) and in two shape-only tests that pass 4 does not reach (`tests/scripts/test_architecture_delta_records.py` lines 83, 466, 485). |
| A12 | The owner chose: Mermaid from a CDN (superseded 2026-11-23 by A15: SVG drawn at build time); titles and views through `export`; committed output in `<model>/generated`; areas and capabilities as named views; capability names checked; labels only for timing; an overview document; the four approved design sections. | VERIFIED: owner answers and approvals, 2026-11-17. |
| A13 | Mermaid 12.2.0 with `securityLevel: 'strict'` ignores `click` callback lines but keeps `click … href` links (URL sanitised). The documents use neither, so one diagram text serves both writers. | VERIFIED: `dist/mermaid.min.js` of the npm package, the same 5,494,801-byte file with the spec's sha384 hash: `setClickFun` returns unless the level is `loose`; `setLink` formats the URL at every level. Historical: HTML pages no longer carry diagram text (A15). |
| A14 | `@hpcc-js/wasm-graphviz` 1.29.2 (Graphviz 16.1.0) lays out in Node with no browser and XML-escapes label text in its SVG. It expands `\N`, `\G` and the like after decoding entities, in plain and in HTML-like labels; a word joiner after the backslash stops it. | VERIFIED: probes through `Graphviz.load()` and `dot(…, 'svg')`, 2026-11-23. |
| A15 | The Claude Code app on a phone shows HTML pages without running their scripts, and in its dark theme the old pages were unreadable. | VERIFIED: owner, 2026-11-23. |
