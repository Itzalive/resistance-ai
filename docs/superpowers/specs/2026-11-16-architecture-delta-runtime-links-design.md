# Architecture delta: runtime links

Work item: #30 (A2 of #37). Amends `2026-11-09-architecture-delta-tool-design.md`.

> `export` is now format 3: `2026-11-17-architecture-model-records-design.md` (#31) adds the record lists after `runtime`.

## Why

A model author sometimes needs a relationship that is not an import: a client app calling a server over HTTP, a push path, a component calling an outside system. Today the delta tool has one sort of relationship. Any relationship permits imports between its two ends, and one whose ends both have code but no import between them is reported as "not yet reached" on every run. The first real model had 33 runtime links, and each one between two elements with code was reported as not yet reached on every run (`docs/field-reports/2026-11-16-defining-architecture-first-run.md`, F3).

## What this work item owns

How the delta tool reads, checks and exports relationships by kind. It does not own how skills use the result, the model folder's layout, or document generation (#31 onward).

## Rules

1. **Two sorts of relationship.** A relationship of kind `uses`, or with no kind, is an **import relationship**. A relationship of any other kind is a **runtime link**. The kind name is compared exactly, so `Uses` is a runtime link. The loader accepts a relationship's `kind` as a non-empty string, `null` or absent; `null` and absent mean no kind. Any other value fails the existing check on what LikeC4 returns: exit 2, `error: internal:`.
2. **Only import relationships permit imports.** A code edge from element A to element B is allowed only when the model has an import relationship from A or an ancestor of A to B or an ancestor of B. A runtime link permits nothing. The `#protected` rule is unchanged and considers import relationships only.
3. **An import with only a runtime link is a breach.** It is reported like any other breach: known when the gap file lists the pair, otherwise new.
4. **Runtime links are never "not yet reached".** That report lists import relationships only.
5. **Runtime links are outside the cycle rule.** `export` lists the two sorts separately, and the review's cycle check reads the import list only. A model may hold runtime links in both directions between two elements.
6. **Both sorts may join the same pair.** Each is judged by its own rule.
7. **Any declared kind name is accepted.** The model declares its kinds as LikeC4 requires; an undeclared kind is a model error as today.

Nothing else changes: the module-to-element mapping, the gap file's format and matching, scopes, shared hot spots, unmapped code, exit codes, the limits, and the tool being read-only with no network access.

## Output

**`export`**

```json
{
  "format": 2,
  "elements": [{ "id": "…", "kind": "…", "tags": ["…"], "code": ["…"], "rules": ["…"] }],
  "allowed": [{ "from": "…", "to": "…" }],
  "runtime": [{ "from": "…", "to": "…", "kind": "…" }]
}
```

- `allowed` keeps its meaning and shape and now holds import relationships only, one entry per element pair.
- `runtime` holds each runtime link once per element pair and kind, sorted by `from`, then `to`, then `kind`, by the same raw-string order as the other lists. Entries are unique before cleaning, so two kinds that differ only past the cleaning cut print alike. It is present and empty when the model has none.
- `format` is 2.
- A relationship's title is not exported.
- `kind` is cleaned for output by the rule already applied to ids.

**`check`**

No key is added or removed, and the text form keeps its headings and summary line. `not_yet_reached` lists import relationships only.

## Compatibility

A model that relied on a kind other than `uses` to permit an import starts reporting breaches (A7). A reader of `export` that checks `format` sees 2; a reader that only reads `allowed` keeps working.

## Risk

A misspelt kind that the model also declares (`use` beside `uses`) turns an import relationship into a runtime link. Where code already imports across the pair, those imports appear as new breaches, exit 1. Where no code edge crosses the pair yet, the relationship only leaves `not_yet_reached`, and `export`'s `runtime` list is the one place the mistake shows.

## Documents that change

- `2026-11-09-architecture-delta-tool-design.md`: a note at the top pointing here for the "Allowed", "`#protected`" and "Reported" rules, the API-shape rule for what LikeC4 returns (a relationship's `kind`), and the `export` shape; and the out-of-scope item for relationship kinds struck.
- `ARCH_STANDARDS.md`, delta tool flags: one line saying only `uses` relationships permit imports and other kinds are runtime links the check ignores; and "not yet reached" reworded as an import relationship the code doesn't have yet.
- `ARCH_REVIEW_MANIFEST.md`, cycle check: name `export`'s `allowed` list as its input. The skill's step 2a wording ("the relationships have a cycle") is left to #31; the manifest's cycle check is what decides it.

These are wording changes that describe the tool. They change no step of the skill, so they need no new pressure run.

## Scope

- The delta tool's model loading, comparison and report modules.
- Tests beside the existing delta tool tests, building their models in the test as the existing tests do.
- The three documents above.
- Required check that is not an acceptance criterion: the delta tool's existing tests, whose fixtures use only `uses` or no kind, all pass, and the only edits to them are in the `export` tests: the expected `format` value and the new `runtime` key in the expected key list and the expected empty export.

**Out of scope:** stating the rule inside the shipped `c4.c4` (model folders hold a copy that must match; #31 refreshes them); skill steps and rubric text on the two sorts (#31); drawing runtime links (#32, #33); other meanings for kinds.

## Threat Model (CIA)

| Pillar | Vector | Defence and proof |
|---|---|---|
| Confidentiality | `kind` is a new string the tool prints; a model file can put a very long name in it (LikeC4's grammar already rejects anything but plain identifier characters). | The output cleaning used for every id and tag is applied to `kind` (`skills/shared/scripts/architecture-delta/report.mjs`, `clean` from `errors.mjs`). AC-9. |
| Integrity | A runtime link wrongly permitting an import would hide a breach. | Rule 2 is tested directly (AC-1, AC-6). The comparison builds its permission set from relationships (`match.mjs`, `relationshipKeys`); the change filters that set to import relationships. |
| Integrity | A misspelt kind reclassifies a relationship. | An undeclared kind fails to load: existing model-error path, exit 2 (`model.mjs`, `getErrors`). A declared misspelling is the risk stated under Risk. |
| Integrity | LikeC4 returns a `kind` that is not a string. | The loader's existing shape check on what LikeC4 returns is extended to `kind` (`model.mjs`, `shapeError`): exit 2, `internal`. AC-11. |
| Availability | More relationships to walk. | The permission set is filtered once per run; no new loop over modules. The model-folder limits (2,000 files, 50 MB: `walk.mjs`), the element limit (5,000: `model.mjs`) and `--timeout` are unchanged and bound the input. |
| Least privilege | None added. | The source test (no `child_process`, no `worker_threads`, no `fs` write) and the no-network test must pass unchanged (`tests/scripts/test_architecture_delta_safety.py`). |
| Supply chain | None added. | No new dependency; the `likec4` pin does not move (`package.json`, `package-lock.json`). |

## Acceptance criteria

- **AC-1** Given a model where A and B are joined only by a runtime link, and the code imports from A to B, when `check` runs, then it reports a breach from A to B marked new and exits 1.
- **AC-2** Given the model and code of AC-1 with that pair in the gap file, when `check` runs, then the breach is known and the exit code is 0.
- **AC-3** Given a model where A and B both have code and are joined only by a runtime link, and no code edge runs between them, when `check` runs, then `not_yet_reached` is empty.
- **AC-4** Given one relationship with no kind and one of kind `uses`, between different pairs of elements that have code, when `check` runs with code edges across both pairs, then no breach is reported; and when it runs with no code edges, then both are listed in `not_yet_reached`.
- **AC-5** Given a pair joined by both an import relationship and a runtime link, when the code imports across it, then no breach is reported.
- **AC-6** Given a `#protected` element P inside a parent R, and an element Q outside P with an import relationship from Q to R and a runtime link from Q to P, when the code imports from Q into P, then a breach is reported.
- **AC-7** Given a model with import relationships and runtime links, when `export` runs, then `format` is 2, `allowed` holds only the import pairs, and `runtime` holds each runtime link once per pair and kind, with its kind, in the stated order.
- **AC-8** Given a runtime link from A to B and another from B to A, when `export` runs, then both are in `runtime` and neither is in `allowed`.
- **AC-9** Given a declared kind of 201 ASCII letters on a runtime link, when `export` runs, then the printed `kind` is its first 199 letters followed by `…`.
- **AC-10** Given a model with no runtime link, when `export` runs, then `runtime` is present and empty.
- **AC-11** Given a LikeC4 copy that returns a relationship whose `kind` is the number 5, when `export` runs, then it exits 2 with a line starting `error: internal:`; and given one that returns a relationship with no `kind` key, when `export` runs, then that relationship is in `allowed`.
- **AC-12** Given a model that declares a relationship kind `Uses` and joins A to B only by a relationship of that kind, and the code imports from A to B, when `check` runs, then a new breach from A to B is reported.

## Future work (downstream cost)

| Item | Priority | Effort | Note |
|---|---|---|---|
| Skill steps and rubric name the two sorts of relationship | P1 | S | #31 |
| Generators draw runtime links differently and list them per boundary | P1 | M | #32, #33 |
| The downstream baseline redraws its push path in its real direction | P2 | S | #36 |
| State the rule inside the shipped `c4.c4` | P3 | S | With #31, when model folders are refreshed |
| Kinds with other meanings, such as "must not exist" | P3 | M | Only if a real model needs one |

## Assumptions surface

| # | Assumption | Status |
|---|---|---|
| A1 | Any relationship permits imports today, whatever its kind. | VERIFIED: delta tool spec, "Allowed"; `match.mjs` builds `relationshipKeys` from every relationship. |
| A2 | "Not yet reached" lists any relationship whose two ends have code and no checked code edge. | VERIFIED: delta tool spec, "Reported"; `match.mjs`, `notYetReached`. |
| A3 | LikeC4 returns each relationship's kind, and none for a relationship written without one. | VERIFIED: scratch run on likec4 1.60.0 against a model with `uses`, `http`, `push`, `calls` (kinds returned as written) and a two-element model with `a -> b` (kind `null`) and `a -[uses]-> b` (kind `uses`). A kind name with a non-ASCII letter fails to parse; a kind of more than 200 ASCII letters loads. |
| A4 | The loader does not read the kind today, and the existing tests' LikeC4 stand-ins return relationships with no `kind` key. | VERIFIED: `model.mjs` keeps `source.id` and `target.id` only; `tests/scripts/test_architecture_delta_model.py` and `test_architecture_delta_check.py` stand-ins. This is why an absent `kind` must mean no kind. |
| A5 | The shipped `c4.c4` declares one relationship kind, `uses`, and a model folder's copy must match it. | VERIFIED: `skills/shared/architecture/c4.c4`; `walk.mjs`, `checkSpecCopy`. |
| A6 | `export` lists relationships under `allowed` with `format` 1. | VERIFIED: `report.mjs`, `exportJson`. |
| A7 | No approved model relies on a non-`uses` kind to permit an import. | VERIFIED by the owner (2026-11-16): one model exists, and it uses `uses` for every import relationship. |
| A8 | There is no separate limit on the number of relationships. | VERIFIED: `model.mjs` has an element limit only; the model-folder limits bound the input. |
| A9 | Existing tests pin the `export` shape and will need editing. | VERIFIED (`grep -n format tests/scripts/*.py`): `tests/scripts/test_architecture_delta_export.py` pins `format` 1 in three places, the key list `format, elements, allowed`, and the empty export object. No `check` test pins `format`. |
