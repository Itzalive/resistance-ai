"""Change records and the improvement list (spec 2026-11-17-architecture-docs-design.md, "Change record",
"Improvement list")."""

from __future__ import annotations

import copy

from arch_delta_support import require_node
from test_architecture_docs_area import GAP, RECORDS, L, built, element, heads, para, section

require_node()

GONE = " (not in the current model)"


def lists(added: list = (), changed: list = (), removed: list = ()) -> dict:
    return {"added": list(added), "changed": list(changed), "removed": list(removed)}


def change(**over) -> dict:
    record = {"id": "2026-11-05-more", "date": "2026-11-05", "run": "later-stage", "asked_by": "#1", "summary": "More.",
              "rejected": [], "elements": lists(), "decisions": lists(), "holes": lists(), "contracts": lists(),
              "gap": {"added": [], "removed": []}, "check": {"exit": 0, "summary": "ok", "output": "ok\n"}, "approved": None}
    record.update(over)
    return record


# AC-22: adds an element, adds one a later change removed, changes an element and a decision, removes a contract.
MORE = change(rejected=["A monolith."], elements=lists(["shop.web", "shop.cart"], ["pay"], ["shop.old"]),
              decisions=lists(changed=["D-2"]), contracts=lists(removed=["C-9"]),
              gap={"added": [["shop.api", "ledger"]], "removed": [["shop.cart", "pay"]]},
              check={"exit": 1, "summary": "1 new breach", "output": "New breaches\n  shop.api -> ledger (1 edges)\n"})


def with_change(record: dict, data: dict = RECORDS) -> dict:
    data = copy.deepcopy(data)
    for decision in data["decisions"]:
        if decision["id"] == "D-2":
            decision["rejected"] = ["Two APIs.", "No API."]
        if decision["id"] == "D-0":
            decision["rejected"] = ["A fat web."]
    data["changes"] = [record]
    return data


def change_doc(record: dict = MORE, data: dict = RECORDS, gap: list = GAP) -> dict:
    return built("change.mjs", "m.buildChange(data, gap, data.changes[0], base)", with_change(record, data), gap)


ELEMENT_HEADER = ["Element", "Title", "Description", "Code", "Rules", "Tags"]


def test_change_record_layout() -> None:  # Change record: summary, asked by, run, date, approval; the sections in order; AC-22
    document = change_doc()
    assert document["title"] == "2026-11-05-more"
    assert document["blocks"][0] == {"type": "list", "items": [
        ["Summary: ", "More."], ["Asked by: ", "#1"], ["Run: ", "later-stage"], ["Date: ", "2026-11-05"],
        ["Approval: ", "Not yet approved"]]}
    assert heads(document, 2) == ["Diagram", "What changed", "Choices not taken", "Known gap", "Check"]


def test_change_record_approval() -> None:  # Change record: approval by and date
    document = change_doc(change(approved={"by": "Owner", "date": "2026-11-06"}))
    assert document["blocks"][0]["items"][-1] == ["Approval: ", "approved by Owner on 2026-11-06"]


def test_change_record_diagram() -> None:  # Change record: added and changed elements still in the model framed and marked; AC-22
    diagram = section(change_doc(), "Diagram")
    assert len(diagram) == 1 and diagram[0]["type"] == "diagram"
    text = diagram[0]["text"]
    assert text.startswith('flowchart LR\n  subgraph frame["2026-11-05-more"]\n')
    frame = text.split("\n  end\n")[0]
    assert '["Web #40;added#41;"]' in frame and '["Pay #40;changed#41;"]' in frame
    assert "shop.cart" not in text and "Old" not in text


def test_change_record_marks_an_id_in_both_lists_added() -> None:  # Change record (amended): added wins
    text = section(change_doc(change(elements=lists(["pay"], ["pay", "shop.web"]))), "Diagram")[0]["text"]
    assert '["Pay #40;added#41;"]' in text and '["Web #40;changed#41;"]' in text and "Pay #40;changed" not in text


def test_change_record_with_nothing_to_draw() -> None:  # Change record: no diagram when no added or changed element is current
    document = change_doc(change(elements=lists(["shop.cart"], [], ["pay"])))
    assert section(document, "Diagram") == [para("No element the change added or changed is in the current model.")]


def test_change_record_over_the_arrow_limit() -> None:  # Shared rules: a flowchart over 80 arrows is replaced by the note
    data = {**RECORDS, "allowed": [{"from": "pay", "to": f"x{i:02}", "titles": []} for i in range(81)], "runtime": [],
            "elements": RECORDS["elements"] + [element(f"x{i:02}", f"X{i}") for i in range(81)]}
    document = change_doc(change(elements=lists(changed=["pay"])), data, [])
    assert section(document, "Diagram") == [para("The diagram has more than 80 arrows and is not drawn; the tables list everything.")]


def test_change_record_what_changed() -> None:  # Change record: What changed; AC-22
    blocks = section(change_doc(), "What changed")
    assert [block["text"] for block in blocks if block["type"] == "heading" and block["level"] == 3] == [
        "Elements added", "Elements changed", "Elements removed", "Decisions changed", "Contracts removed"]
    assert blocks[1] == {"type": "table", "header": ELEMENT_HEADER,
                         "rows": [[[L("shop.web", "../areas/front.md")], ["Web"], [""], [""], [""], [""]]]}
    assert blocks[2] == {"type": "list", "items": [["shop.cart" + GONE]]}
    assert blocks[4]["rows"] == [[[L("pay", "../areas/money.md")], ["Pay"], [""], [""], [""], [""]]]
    assert blocks[6] == {"type": "list", "items": [["shop.old"]]}
    assert blocks[8] == {"type": "heading", "level": 4, "text": "D-2"}
    assert blocks[9] == para("One API.")
    assert ["Rejected: ", "Two APIs.; No API."] in blocks[10]["items"]
    assert blocks[10]["items"][-1] == ["Areas: ", L("front", "../areas/front.md"), " (Front)"]
    assert blocks[11:] == [{"type": "heading", "level": 3, "text": "Contracts removed"}, {"type": "list", "items": [["C-9"]]}]


def test_change_record_prints_current_records_in_full_and_gone_ones_as_text() -> None:  # Change record: What changed
    record = change(contracts=lists(["C-1", "C-7"]), holes=lists(changed=["H-1", "H-9"]), decisions=lists(["D-8"], [], ["D-1"]))
    blocks = section(change_doc(record), "What changed")
    assert blocks[0:2] == [{"type": "heading", "level": 3, "text": "Decisions added"}, para("D-8" + GONE)]
    assert blocks[2:4] == [{"type": "heading", "level": 3, "text": "Decisions removed"}, {"type": "list", "items": [["D-1"]]}]
    assert blocks[4:6] == [{"type": "heading", "level": 3, "text": "Contracts added"}, {"type": "heading", "level": 4, "text": "C-1: Card API"}]
    assert blocks[7] == para("C-7" + GONE)
    assert blocks[8:11] == [{"type": "heading", "level": 3, "text": "Open questions changed"},
                            {"type": "heading", "level": 4, "text": "H-1"}, para("Why one API?")]
    assert blocks[12] == para("H-9" + GONE)
    assert len(blocks) == 13


def test_change_record_shows_an_id_in_two_lists_in_both() -> None:  # Change record (amended): each list as the file gives it
    blocks = section(change_doc(change(elements=lists(["pay"], ["pay"]))), "What changed")
    assert [block["rows"][0][1] for block in blocks if block["type"] == "table"] == [["Pay"], ["Pay"]]


def test_change_record_with_no_ids() -> None:  # Change record: empty sections say so
    document = change_doc(change())
    assert section(document, "What changed") == [para("The change file lists no elements or records.")]
    assert section(document, "Choices not taken") == [para("No choices are recorded as not taken.")]
    assert section(document, "Known gap") == [para("The change added or removed no known-gap entries.")]


def test_change_record_choices_not_taken() -> None:  # Change record: the change's rejected list, then its decisions'; AC-22
    record = change(rejected=["A monolith."], decisions=lists(["D-2", "D-8"], ["D-0", "D-2"], ["D-1"]))
    assert section(change_doc(record), "Choices not taken") == [{"type": "list", "items": [
        ["A monolith."], [L("D-2", "../areas/front.md"), ": ", "Two APIs."], [L("D-2", "../areas/front.md"), ": ", "No API."],
        [L("D-0", "../areas/front.md"), ": ", "A fat web."]]}]


def test_change_record_known_gap() -> None:  # Change record (amended): pairs, ends linked or marked gone, no reason
    assert section(change_doc(), "Known gap") == [{"type": "list", "items": [
        ["Added: ", L("shop.api", "../areas/front.md"), " (API)", " -> ", L("ledger", "../README.md"), " (Ledger)"],
        ["Removed: ", "shop.cart" + GONE, " -> ", L("pay", "../areas/money.md"), " (Pay)"]]}]


def test_change_record_check() -> None:  # Change record: exit, summary, and the output in a code block
    assert section(change_doc(), "Check") == [
        {"type": "list", "items": [["Exit: ", "1"], ["Summary: ", "1 new breach"]]},
        {"type": "code", "text": "New breaches\n  shop.api -> ledger (1 edges)\n"}]
