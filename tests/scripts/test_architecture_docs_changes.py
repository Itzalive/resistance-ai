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
    assert document["blocks"][0]["items"][-1] == ["Approval: ", "Approved by Owner on 2026-11-06"]


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


def rel(from_: str, to: str, kind: str | None = None, titles: tuple = ()) -> dict:
    return {"from": from_, "to": to, "kind": kind, "titles": list(titles)}


# AC-31: shop.web is changed; it gains an import to shop.api and keeps its unchanged links to bank. The import
# shop.api -> ledger is removed and gapped while a runtime link on the same pair is removed too, another runtime link and
# an import from a gone element are removed, and the gap pair pay -> ledger is closed. Seven arrows: one diagram.
DRAWN = change(elements=lists(changed=["shop.web"]),
               relationships={"added": [rel("shop.web", "shop.api", titles=("orders",))],
                              "changed": [rel("shop.api", "pay.gateway", "http", ("refunds", "charges"))],
                              "removed": [rel("pay.gateway", "shop.api", "event"), rel("shop.api", "ledger"),
                                          rel("shop.api", "ledger", "event"), rel("shop.old", "pay")]},
               gap={"added": [["shop.api", "ledger"]], "removed": [["pay", "ledger"]]})
# The same with eleven more removed imports from gone elements: 18 arrows, drawn as two diagrams.
GONE_IDS = [f"gone.g{i:02}" for i in range(11)]
SPLIT = change(**{**DRAWN, "relationships": {**DRAWN["relationships"],
                                             "removed": DRAWN["relationships"]["removed"] + [rel(g, "pay") for g in GONE_IDS]}})
NONE = {"added": [], "changed": [], "removed": []}


def drawn(blocks: list) -> dict:
    """Each level-3 heading of the Diagram section with the block under it."""
    return {blocks[at]["text"]: blocks[at + 1] for at in range(len(blocks) - 1) if blocks[at]["type"] == "heading"}


def arrows_of(block: dict) -> list:
    return [(a["from"], a["to"], a["dashed"], a["red"], a["text"]) for a in block["figure"]["arrows"]]


MODEL_ARROWS = [
    ("pay.gateway", "shop.api", True, False, "removed, event"),
    ("shop.api", "ledger", True, False, "removed, event"),
    ("shop.api", "pay.gateway", True, False, 'http, "charges", "refunds"'),
    ("shop.old", "pay", True, False, "removed"),
    ("shop.web", "shop.api", False, False, ""),
]


def test_a_small_change_is_one_diagram() -> None:  # AC-31: 15 arrows or fewer
    [block] = section(change_doc(DRAWN), "Diagram")
    assert block["type"] == "diagram"
    assert arrows_of(block) == [
        ("pay", "ledger", True, False, "gap closed"),
        ("pay.gateway", "shop.api", True, False, "removed, event"),
        ("shop.api", "ledger", False, True, "known gap"),
        ("shop.api", "ledger", True, False, "removed, event"),
        ("shop.api", "pay.gateway", True, False, 'http, "charges", "refunds"'),
        ("shop.old", "pay", True, False, "removed"),
        ("shop.web", "shop.api", False, False, ""),
    ]
    assert block["figure"]["frame"] == {"text": "2026-11-05-more", "ids": ["shop.web"]}
    assert "bank" not in block["text"] and "Bank" not in block["text"]


def test_a_large_change_is_split_into_model_and_known_gap_diagrams() -> None:  # AC-31: over 15 arrows
    blocks = section(change_doc(SPLIT), "Diagram")
    parts = drawn(blocks)
    assert list(parts) == ["Model changes", "Known-gap changes"] and len(blocks) == 4
    assert all(block["drawing"] for block in blocks if block["type"] == "heading")
    model = parts["Model changes"]
    assert arrows_of(model) == sorted(MODEL_ARROWS + [(g, "pay", True, False, "removed") for g in GONE_IDS])
    nodes = {node["id"]: node["text"] for node in model["figure"]["nodes"]}
    assert nodes["shop.web"] == "Web (changed)" and nodes["ledger"] == "Ledger (no area)"
    assert nodes["shop.old"] == "shop.old (not in the current model)"
    assert model["figure"]["frame"] == {"text": "2026-11-05-more", "ids": ["shop.web"]}
    gap = parts["Known-gap changes"]
    assert arrows_of(gap) == [("pay", "ledger", True, False, "gap closed"), ("shop.api", "ledger", False, True, "")]
    assert gap["figure"]["frame"] is None
    assert {node["id"] for node in gap["figure"]["nodes"]} == {"pay", "ledger", "shop.api"}
    for block in parts.values():
        assert "bank" not in block["text"] and "Bank" not in block["text"]


def test_the_split_is_at_15_arrows() -> None:  # AC-31
    sixteen = change(relationships={**NONE, "removed": [rel(f"gone.h{i:02}", "pay") for i in range(16)]})
    fifteen = change(relationships={**NONE, "removed": [rel(f"gone.h{i:02}", "pay") for i in range(15)]})
    assert list(drawn(section(change_doc(sixteen), "Diagram"))) == ["Model changes"]
    [block] = section(change_doc(fifteen), "Diagram")
    assert block["type"] == "diagram"


def test_the_split_counts_drawn_arrows() -> None:  # AC-31: a gapped import is drawn once; a closed gap pair counts
    gapped = change(relationships={**NONE, "removed": [rel(f"gone.h{i:02}", "pay") for i in range(14)] + [rel("shop.api", "ledger")]},
                    gap={"added": [["shop.api", "ledger"]], "removed": []})
    [block] = section(change_doc(gapped), "Diagram")
    assert block["type"] == "diagram"
    closed = change(relationships={**NONE, "removed": [rel(f"gone.h{i:02}", "pay") for i in range(15)]},
                    gap={"added": [], "removed": [["pay", "ledger"]]})
    assert list(drawn(section(change_doc(closed), "Diagram"))) == ["Model changes", "Known-gap changes"]


def test_a_split_leaves_out_an_empty_model_diagram() -> None:  # AC-31
    record = change(relationships=NONE, gap={"added": [[f"gone.h{i:02}", "pay"] for i in range(16)], "removed": []})
    assert list(drawn(section(change_doc(record), "Diagram"))) == ["Known-gap changes"]


def test_each_split_diagram_has_its_own_arrow_limit() -> None:  # AC-31, Shared rules
    record = change(relationships={**NONE, "removed": [rel(f"gone.h{i:02}", "pay") for i in range(81)]},
                    gap={"added": [["shop.api", "ledger"]], "removed": []})
    parts = drawn(section(change_doc(record), "Diagram"))
    assert parts["Model changes"]["text"] is None and parts["Model changes"]["note"].startswith("The Markdown diagram has more than 80")
    assert parts["Known-gap changes"]["text"].startswith("flowchart LR")


def test_change_record_with_nothing_drawn_says_so() -> None:  # AC-31
    [block] = section(change_doc(change(relationships=NONE)), "Diagram")
    assert block["type"] == "paragraph"


def test_change_record_lists_its_relationships() -> None:  # AC-31, What changed
    blocks = section(change_doc(DRAWN), "What changed")
    flat = lambda block: ["".join(part if isinstance(part, str) else part["text"] for part in item) for item in block["items"]]
    at = blocks.index({"type": "heading", "level": 3, "text": "Relationships added"})
    assert flat(blocks[at + 1]) == ["shop.web (Web) -> shop.api (API): import"]
    at = blocks.index({"type": "heading", "level": 3, "text": "Relationships changed"})
    assert flat(blocks[at + 1]) == ["shop.api (API) -> pay.gateway (Gateway): http"]
    at = blocks.index({"type": "heading", "level": 3, "text": "Relationships removed"})
    assert flat(blocks[at + 1]) == ["pay.gateway (Gateway) -> shop.api (API): event", "shop.api (API) -> ledger (Ledger): import",
                                    "shop.api (API) -> ledger (Ledger): event", "shop.old (not in the current model) -> pay (Pay): import"]


def test_change_record_with_only_relationships_draws_without_a_frame() -> None:  # AC-31: no framed element
    record = change(relationships={"added": [rel("shop.web", "bank")], "changed": [], "removed": []})
    [block] = section(change_doc(record), "Diagram")
    assert block["figure"]["frame"] is None
    assert [(a["from"], a["to"]) for a in block["figure"]["arrows"]] == [("shop.web", "bank")]


def test_change_record_frames_no_changed_element_gone_from_the_model() -> None:  # Change record: only current ids framed
    document = change_doc(change(elements=lists(["shop.web"], ["shop.gone"])))
    text = section(document, "Diagram")[0]["text"]
    assert '["Web #40;added#41;"]' in text and "changed" not in text
    assert section(document, "What changed")[-1] == {"type": "list", "items": [["shop.gone (not in the current model)"]]}


def test_change_record_with_nothing_to_draw() -> None:  # Change record: no diagram when no added or changed element is current
    document = change_doc(change(elements=lists(["shop.cart"], [], ["pay"])))
    assert section(document, "Diagram") == [para("No element the change added or changed is in the current model.")]


def test_change_record_over_the_arrow_limit() -> None:  # Shared rules: a flowchart over 80 arrows is replaced by the note
    data = {**RECORDS, "allowed": [{"from": "pay", "to": f"x{i:02}", "titles": []} for i in range(81)], "runtime": [],
            "elements": RECORDS["elements"] + [element(f"x{i:02}", f"X{i}") for i in range(81)]}
    document = change_doc(change(elements=lists(changed=["pay"])), data, [])
    block = section(document, "Diagram")[0]
    assert block["type"] == "diagram" and block["text"] is None and block["note"] == "The Markdown diagram has more than 80 arrows and is not drawn; the HTML page draws it."


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
    record = change(contracts=lists(["C-7", "C-1"]), holes=lists(changed=["H-9", "H-1", "H-8"]), decisions=lists(["D-8"], [], ["D-1"]))
    blocks = section(change_doc(record), "What changed")
    assert blocks[0:2] == [{"type": "heading", "level": 3, "text": "Decisions added"}, {"type": "list", "items": [["D-8" + GONE]]}]
    assert blocks[2:4] == [{"type": "heading", "level": 3, "text": "Decisions removed"}, {"type": "list", "items": [["D-1"]]}]
    assert blocks[4:6] == [{"type": "heading", "level": 3, "text": "Contracts added"}, {"type": "heading", "level": 4, "text": "C-1: Card API"}]
    assert blocks[7] == {"type": "list", "items": [["C-7" + GONE]]}
    assert blocks[8:11] == [{"type": "heading", "level": 3, "text": "Open questions changed"},
                            {"type": "heading", "level": 4, "text": "H-1"}, para("Why one API?")]
    assert blocks[12] == {"type": "list", "items": [["H-9" + GONE], ["H-8" + GONE]]}
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


def test_change_record_prints_elements_in_full_in_file_order() -> None:  # Change record: in full, each list as the file gives it
    table = section(change_doc(change(elements=lists(["shop.web", "shop"]))), "What changed")[1]
    assert table["rows"] == [
        [[L("shop.web", "../areas/front.md")], ["Web"], [""], [""], [""], [""]],
        [[L("shop", "../areas/front.md")], ["Shop"], ["Sells things."], ["src/shop, src/lib"], ["BR-1, BR-2"], ["#edge #web"]],
    ]


def test_change_record_at_the_arrow_limit() -> None:  # Shared rules: a flowchart with 80 arrows is still drawn
    data = {**RECORDS, "allowed": [{"from": "pay", "to": f"x{i:02}", "titles": []} for i in range(80)], "runtime": [],
            "elements": RECORDS["elements"] + [element(f"x{i:02}", f"X{i}") for i in range(80)]}
    diagram = section(change_doc(change(elements=lists(changed=["pay"])), data, []), "Diagram")
    assert diagram[0]["type"] == "diagram" and diagram[0]["text"].count(" --> ") == 80


def improvements(data: dict = RECORDS, gap: list = GAP) -> dict:
    return built("improvements.mjs", "m.buildImprovements(data, gap, base)", data, gap)


def items(document: dict, heading: str) -> list:
    blocks = section(document, heading)
    assert len(blocks) == 1
    return blocks[0]["items"] if blocks[0]["type"] == "list" else blocks


FRONT = ["Areas: ", L("front", "areas/front.md"), " (Front)"]
MONEY = ["Areas: ", L("money", "areas/money.md"), " (Money)"]
NOWHERE = ["Not in any area"]
COVERAGE = {"answer": "Most code is mapped.", "baselined": [], "edge_nodes": [{"element": "bank", "run": "baseline"}],
            "counts": {"modules": 9, "groups": 2},
            "unmapped": [{"module": "src/z", "reason": "new code"}, {"module": "src/a", "reason": "generated"}]}


def test_improvement_list_groups_in_order_with_counts() -> None:  # Improvement list (amended): `<group name> (<count>)`; AC-23
    document = improvements()
    assert document["title"] == "Improvement list"
    assert document["blocks"][0] == para("Facts from the architecture model and the known-gap file; nothing here is judged or ranked.")
    assert heads(document, 2) == [
        "Cycles in current code (1)", "Other known breaches (1)", "Open questions (1)", "Decisions not yet fully built (1)",
        "Decisions with no known reason (1)", "Unmapped code (0)", "Elements in no area (2)", "Elements that own nothing (5)"]


def test_improvement_list_items() -> None:  # Improvement list (amended): each item, its details and its areas; AC-23
    document = improvements()
    assert items(document, "Cycles in current code (1)") == [
        [L("shop.api", "areas/front.md"), " (API)", " -> ", L("ledger", "README.md"), " (Ledger)", ": ", "cycle in current code", "; ", "close by 2027-01", ". ", *FRONT]]
    assert items(document, "Other known breaches (1)") == [
        [L("bank", "README.md"), " (Bank)", " -> ", L("pay", "areas/money.md"), " (Pay)", ": ", "between neighbours", ". ", *MONEY]]
    assert items(document, "Open questions (1)") == [
        [L("H-1", "areas/front.md"), ": ", "binds ", L("shop.api", "areas/front.md"), " (API)", ". ", *FRONT]]
    assert items(document, "Decisions not yet fully built (1)") == [[L("D-2", "areas/front.md"), ": ", "status ", "planned", ". ", *FRONT]]
    assert items(document, "Decisions with no known reason (1)") == [[L("D-0", "areas/front.md"), ". ", *FRONT]]
    assert items(document, "Unmapped code (0)") == [para("None.")]
    assert items(document, "Elements in no area (2)") == [
        [L("bank", "README.md"), " (Bank)", ". ", *NOWHERE], [L("ledger", "README.md"), " (Ledger)", ". ", *NOWHERE]]
    assert [item[0]["text"] for item in items(document, "Elements that own nothing (5)")] == [
        "bank", "ledger", "pay.gateway", "shop.api.orders", "shop.web"]
    assert items(document, "Elements that own nothing (5)")[2] == [L("pay.gateway", "areas/money.md"), " (Gateway)", ". ", *MONEY]


def test_improvement_list_with_a_coverage_file() -> None:  # Improvement list: unmapped entries by module; edge nodes own something
    document = improvements({**RECORDS, "coverage": COVERAGE})
    assert items(document, "Unmapped code (2)") == [["src/a", ": ", "generated"], ["src/z", ": ", "new code"]]
    assert [item[0]["text"] for item in items(document, "Elements that own nothing (4)")] == [
        "ledger", "pay.gateway", "shop.api.orders", "shop.web"]


def test_elements_that_own_nothing() -> None:  # Improvement list: no code, no child, kind not external, not an edge node
    data = copy.deepcopy(RECORDS)
    data["elements"] = [element("a", "A", kind="external"), element("b", "B", code=["src/b"]), element("c", "C"), element("c.d", "D"),
                        element("e", "E", kind="system")]
    data["areas"] = []
    document = improvements(data, [])
    assert [item[0]["text"] for item in items(document, "Elements that own nothing (2)")] == ["c.d", "e"]


def test_improvement_list_sorts_items() -> None:  # Improvement list: items sorted by id, by pair or by module
    data = copy.deepcopy(RECORDS)
    data["decisions"] = [dict(data["decisions"][2], id=id_) for id_ in ("D-9", "D-10", "D-3")]
    data["holes"] = [dict(data["holes"][0], id=id_) for id_ in ("H-3", "H-10")]
    gap = [{"from": "shop.web", "to": "bank", "reason": "r", "close_by": None}, {"from": "bank", "to": "shop.web", "reason": "r", "close_by": None},
           {"from": "bank", "to": "pay", "reason": "r", "close_by": None}]
    data["coverage"] = {**COVERAGE, "unmapped": [{"module": "b", "reason": "r"}, {"module": "B", "reason": "r"}, {"module": "a", "reason": "r"}]}
    document = improvements(data, gap)
    assert [item[0]["text"] for item in items(document, "Decisions not yet fully built (3)")] == ["D-10", "D-3", "D-9"]
    assert [item[0]["text"] for item in items(document, "Open questions (2)")] == ["H-10", "H-3"]
    assert [(item[0]["text"], item[3]["text"]) for item in items(document, "Other known breaches (3)")] == [
        ("bank", "pay"), ("bank", "shop.web"), ("shop.web", "bank")]
    assert [item[0] for item in items(document, "Unmapped code (3)")] == ["B", "a", "b"]


def test_improvement_list_statuses_and_records_with_no_area() -> None:  # Improvement list: partly-built and planned; no area
    data = copy.deepcopy(RECORDS)
    data["decisions"] = [dict(data["decisions"][0], id="D-5", status="partly-built", binds=[], reason="R."),
                         dict(data["decisions"][0], id="D-6", status="superseded", superseded_by="D-5", reason="R."),
                         dict(data["decisions"][3], reason=None)]
    data["holes"] = [dict(data["holes"][0], binds=[])]
    document = improvements(data, [])
    assert items(document, "Decisions not yet fully built (1)") == [[L("D-5", "README.md"), ": ", "status ", "partly-built", ". ", *NOWHERE]]
    assert items(document, "Decisions with no known reason (1)") == [[L("P-1", "README.md"), ". ", *NOWHERE]]
    assert items(document, "Open questions (1)") == [[L("H-1", "README.md"), ". ", *NOWHERE]]
    assert items(document, "Cycles in current code (0)") == [para("None.")]
    assert items(document, "Other known breaches (0)") == [para("None.")]
