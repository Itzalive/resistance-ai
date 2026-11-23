"""The change object (spec 2026-11-21-defining-architecture-records-design.md, "`change`": elements, records, gap,
check, the rest)."""

from __future__ import annotations

from arch_delta_support import RECORDS_LIB, call, require_node

require_node()

EMPTY = {"elements": [], "allowed": [], "runtime": [], "decisions": [], "holes": [], "contracts": []}
FLAGS = {"name": "first", "date": "2026-11-21", "run": "epic", "askedBy": "#1", "summary": "S.", "rejected": ["B.", "A."]}
CHECK = {"output": "Known breaches\n  b -> a (1 edges)\n\n0 new, 0 stale, 1 known (likec4 1.60.0 from plugin)\n",
         "exitCode": 0}


def element(id_: str, title: str = "T") -> dict:
    return {"id": id_, "kind": "component", "tags": [], "code": [id_], "rules": [], "title": title, "description": None}


def link(from_: str, to: str) -> dict:
    return {"from": from_, "to": to, "titles": []}


def build(before: dict, after: dict, before_gap: list = (), after_gap: list = ()) -> dict:
    out = call("change.mjs", "buildChange", {"before": before, "after": after, "beforeGap": list(before_gap),
                                             "afterGap": list(after_gap), "check": CHECK, "flags": FLAGS}, lib=RECORDS_LIB)
    assert out["ok"], out
    return out["value"]


def test_keys_and_fixed_fields() -> None:
    value = build(EMPTY, EMPTY)
    assert list(value) == ["id", "date", "run", "asked_by", "summary", "rejected", "elements", "decisions", "holes",
                           "contracts", "relationships", "gap", "check", "approved"]
    assert value["relationships"] == {"added": [], "changed": [], "removed": []}
    assert (value["id"], value["date"], value["run"], value["asked_by"], value["summary"]) == (
        "2026-11-21-first", "2026-11-21", "epic", "#1", "S.")
    assert value["rejected"] == ["B.", "A."]
    assert value["check"] == {"exit": 0, "summary": "0 new, 0 stale, 1 known (likec4 1.60.0 from plugin)",
                              "output": CHECK["output"]}
    assert value["approved"] is None
    assert list(value["elements"]) == ["added", "changed", "removed"]
    assert list(value["gap"]) == ["added", "removed"]


def runtime(from_: str, to: str, kind: str, titles: tuple = ()) -> dict:
    return {"from": from_, "to": to, "kind": kind, "titles": list(titles)}


def test_relationships_are_listed_and_change_no_element() -> None:  # AC-21
    elements = [element("a"), element("b"), element("c")]
    before = {**EMPTY, "elements": elements, "allowed": [link("a", "b")],
              "runtime": [runtime("a", "c", "http"), runtime("b", "c", "push", ("wake",)), runtime("c", "a", "http")]}
    after = {**EMPTY, "elements": elements, "allowed": [link("a", "b"), link("c", "b")],
             "runtime": [runtime("b", "c", "push", ("sealed",)), runtime("c", "a", "http")]}
    value = build(before, after)
    assert value["elements"] == {"added": [], "changed": [], "removed": []}
    assert value["relationships"] == {
        "added": [{"from": "c", "to": "b", "kind": None, "titles": []}],
        "changed": [{"from": "b", "to": "c", "kind": "push", "titles": ["sealed"]}],
        "removed": [{"from": "a", "to": "c", "kind": "http", "titles": []}],
    }


def test_an_import_and_a_runtime_link_between_the_same_ends_are_two_relationships() -> None:
    before = {**EMPTY, "elements": [element("a"), element("b")]}
    after = {**before, "allowed": [link("a", "b")], "runtime": [runtime("a", "b", "http"), runtime("a", "b", "call")]}
    added = build(before, after)["relationships"]["added"]
    assert [(r["from"], r["to"], r["kind"]) for r in added] == [("a", "b", None), ("a", "b", "call"), ("a", "b", "http")]


def test_relationships_sort_by_from_then_to() -> None:
    after = {**EMPTY, "allowed": [link("b", "a"), link("a", "c"), link("a", "b")]}
    assert [(r["from"], r["to"]) for r in build(EMPTY, after)["relationships"]["added"]] == [("a", "b"), ("a", "c"), ("b", "a")]


def test_a_retitled_element_is_changed() -> None:
    before = {**EMPTY, "elements": [element("a", "Old")]}
    after = {**EMPTY, "elements": [element("a", "New")]}
    assert build(before, after)["elements"]["changed"] == ["a"]


def test_moved_record_is_unchanged() -> None:
    record = {"id": "D-1", "decision": "X.", "reason": None, "group": "a"}
    moved = {"group": "b", "reason": None, "decision": "X.", "id": "D-1"}
    edited = {"id": "D-2", "decision": "Y.", "reason": "New.", "group": "a"}
    before = {**EMPTY, "decisions": [record, {"id": "D-2", "decision": "Y.", "reason": "Old.", "group": "a"}]}
    after = {**EMPTY, "decisions": [moved, edited]}
    assert build(before, after)["decisions"] == {"added": [], "changed": ["D-2"], "removed": []}


def test_empty_before_adds_everything() -> None:  # AC-2
    after = {**EMPTY, "elements": [element("a")], "holes": [{"id": "H-1", "what": "?", "group": "a"}],
             "contracts": [{"id": "C-1", "name": "API", "group": "x"}]}
    value = build(EMPTY, after, after_gap=[{"from": "a", "to": "b", "reason": "r", "close_by": None}])
    assert value["elements"]["added"] == ["a"]
    assert value["holes"]["added"] == ["H-1"]
    assert value["contracts"]["added"] == ["C-1"]
    assert value["gap"] == {"added": [["a", "b"]], "removed": []}


def test_lists_and_gap_pairs_are_sorted() -> None:
    after = {**EMPTY, "elements": [element("b"), element("Z"), element("a")]}
    assert build(EMPTY, after)["elements"]["added"] == ["Z", "a", "b"]
    gap = [{"from": "b", "to": "a", "reason": "r", "close_by": None}, {"from": "a", "to": "c", "reason": "r", "close_by": None},
           {"from": "a", "to": "b", "reason": "r", "close_by": None}]
    assert build(EMPTY, EMPTY, before_gap=gap)["gap"] == {"added": [], "removed": [["a", "b"], ["a", "c"], ["b", "a"]]}


def test_changed_reason_is_not_a_gap_change() -> None:
    before_gap = [{"from": "a", "to": "b", "reason": "old", "close_by": None}]
    after_gap = [{"from": "a", "to": "b", "reason": "new", "close_by": "F-1"}]
    assert build(EMPTY, EMPTY, before_gap, after_gap)["gap"] == {"added": [], "removed": []}
