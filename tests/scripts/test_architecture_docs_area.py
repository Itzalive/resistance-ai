"""Area and capability documents (spec 2026-11-17-architecture-docs-design.md, "Drawing rules", "Area", "Capability")."""

from __future__ import annotations

import json

from arch_delta_support import DOCS_LIB, lib_url, require_node, run_module

require_node()


def element(id_: str, title: str, **over) -> dict:
    record = {"id": id_, "kind": "container", "tags": [], "code": [], "rules": [], "title": title, "description": None}
    record.update(over)
    return record


# Export-shaped, not a valid model (records skip fields the documents never print). Area `front` frames shop and its
# children; `money` holds pay and its gateway; bank and ledger are in no area.
DATA = {
    "elements": [
        element("bank", "Bank", kind="system"),
        element("ledger", "Ledger", kind="system"),
        element("pay", "Pay", kind="system"),
        element("pay.gateway", "Gateway"),
        element("shop", "Shop", kind="system", description="Sells things.", tags=["edge", "web"], code=["src/shop", "src/lib"],
                rules=["BR-1", "BR-2"]),
        element("shop.api", "API"),
        element("shop.api.orders", "Orders", kind="component"),
        element("shop.web", "Web"),
    ],
    "allowed": [
        {"from": "bank", "to": "pay", "titles": []},
        {"from": "shop.api", "to": "pay", "titles": []},
        {"from": "shop.api.orders", "to": "pay.gateway", "titles": []},
        {"from": "shop.web", "to": "bank", "titles": []},
        {"from": "shop.web", "to": "shop.api", "titles": ["orders"]},
    ],
    "runtime": [
        {"from": "shop", "to": "pay", "kind": "http", "titles": []},
        {"from": "shop.api", "to": "pay.gateway", "kind": "http", "titles": ["charges"]},
        {"from": "shop.web", "to": "bank", "kind": "event", "titles": ["reports"]},
        {"from": "shop.web", "to": "bank", "kind": "http", "titles": ["feeds", "reports"]},
    ],
    "decisions": [],
    "contracts": [],
    "holes": [],
    "changes": [],
    "coverage": None,
    "areas": [
        {"name": "front", "title": "Front", "description": "The shop.", "elements": ["shop", "shop.api", "shop.api.orders", "shop.web"]},
        {"name": "money", "title": "Money", "description": None, "elements": ["pay", "pay.gateway"]},
    ],
    "capabilities": [],
}
GAP = [
    {"from": "bank", "to": "pay", "reason": "between neighbours", "close_by": None},
    {"from": "shop.api", "to": "ledger", "reason": "cycle in current code", "close_by": "2027-01"},
]


def run(code: str, data: dict = DATA, gap: list = GAP) -> object:
    snippet = (
        f"import * as d from {json.dumps(lib_url('area-diagram.mjs', DOCS_LIB))};\n"
        f"import {{ documentBase }} from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\n"
        f"const data = {json.dumps(data)};\nconst gap = {json.dumps(gap)};\nconst base = documentBase(data);\n"
        f"process.stdout.write(JSON.stringify({code}));\n"
    )
    proc = run_module(snippet)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def arrow(from_: str, to: str, style: str, text: str = "") -> dict:
    return {"from": from_, "to": to, "style": style, "dashed": style == "runtime", "red": style == "gap", "text": text}


def test_area_drawing() -> None:  # AC-19; Drawing rules
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, gap, base)")
    assert picture["frame"] == {"text": "Front", "ids": ["shop", "shop.api", "shop.api.orders", "shop.web"]}
    assert picture["nodes"] == [
        {"id": "bank", "text": "Bank (no area)"},
        {"id": "ledger", "text": "Ledger (no area)"},
        {"id": "pay", "text": "Pay (money)"},
        {"id": "pay.gateway", "text": "Gateway (money)"},
        {"id": "shop", "text": "Shop"},
        {"id": "shop.api", "text": "API"},
        {"id": "shop.api.orders", "text": "Orders"},
        {"id": "shop.web", "text": "Web"},
    ]
    assert picture["arrows"] == [
        arrow("shop.api", "ledger", "gap", "known gap"),
        arrow("shop.api", "pay.gateway", "runtime", 'http, "charges"'),
        arrow("shop.api.orders", "pay.gateway", "import"),
        arrow("shop.web", "bank", "import"),
        arrow("shop.web", "bank", "runtime", 'event, http, "feeds", "reports"'),
        arrow("shop.web", "shop.api", "import"),
    ]


def test_area_drawing_of_the_other_area() -> None:  # Drawing rules: neighbours and arrows of an unscoped area
    picture = run("d.drawing(data.areas[1].elements, data.areas[1].title, gap, base)")
    assert [node["text"] for node in picture["nodes"]] == ["Bank (no area)", "Pay", "Gateway", "Shop (front)", "API (front)",
                                                            "Orders (front)"]
    assert picture["arrows"] == [
        arrow("bank", "pay", "import"),
        arrow("bank", "pay", "gap", "known gap"),
        arrow("shop.api", "pay.gateway", "runtime", 'http, "charges"'),
        arrow("shop.api.orders", "pay.gateway", "import"),
    ]


def test_known_gap_arrows_are_never_hidden_and_hide_nothing() -> None:  # Drawing rules: known-gap arrows
    gap = [{"from": "shop", "to": "ledger", "reason": "r", "close_by": None},
           {"from": "shop.api", "to": "ledger", "reason": "r", "close_by": None},
           {"from": "shop.api.orders", "to": "pay.gateway", "reason": "r", "close_by": None}]
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, gap, base)", gap=gap)
    drawn = [(a["from"], a["to"], a["style"]) for a in picture["arrows"]]
    assert ("shop", "ledger", "gap") in drawn and ("shop.api", "ledger", "gap") in drawn
    assert ("shop.api", "pay.gateway", "runtime") in drawn and ("shop.api.orders", "pay.gateway", "gap") in drawn


def test_an_import_hides_only_its_own_style() -> None:  # Drawing rules: within the import or the runtime style
    data = {**DATA, "runtime": [{"from": "shop.api", "to": "pay", "kind": "http", "titles": []}]}
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, [], base)", data=data)
    drawn = [(a["from"], a["to"], a["style"]) for a in picture["arrows"]]
    assert ("shop.api", "pay", "runtime") in drawn and ("shop.api", "pay", "import") not in drawn


def test_an_arrow_is_implied_only_by_one_strictly_inside() -> None:  # Drawing rules: X' at or inside X, Y' at or inside Y
    data = {**DATA, "runtime": [], "allowed": [
        {"from": "shop.web", "to": "pay", "titles": []},
        {"from": "shop.api", "to": "pay.gateway", "titles": []},
        {"from": "shop.api", "to": "pay", "titles": []},
        {"from": "shop", "to": "bank", "titles": []},
        {"from": "shop.web", "to": "pay.gateway", "titles": []},
    ]}
    picture = run("d.drawing(data.areas[0].elements, data.areas[0].title, [], base)", data=data, gap=[])
    drawn = [(a["from"], a["to"]) for a in picture["arrows"]]
    assert drawn == [("shop", "bank"), ("shop.api", "pay.gateway"), ("shop.web", "pay.gateway")]


def test_area_drawing_with_no_relationships() -> None:  # Drawing rules: framed elements are drawn with no arrows
    data = {**DATA, "allowed": [], "runtime": []}
    picture = run("d.drawing(data.areas[1].elements, data.areas[1].title, [], base)", data=data, gap=[])
    assert picture == {"nodes": [{"id": "pay", "text": "Pay"}, {"id": "pay.gateway", "text": "Gateway"}], "arrows": [],
                       "frame": {"text": "Money", "ids": ["pay", "pay.gateway"]}}


def test_area_drawing_text_and_arrow_limit() -> None:  # AC-21 (the diagram part); Shared rules
    text = run("d.drawingText(d.drawing(data.areas[1].elements, data.areas[1].title, gap, base))")
    assert text.split("\n")[:4] == ["flowchart LR", '  subgraph frame["Money"]', '    n2["Pay"]', '    n3["Gateway"]']
    assert text.endswith("  linkStyle 1 stroke:#d00,color:#d00")
    many = {**DATA, "allowed": [{"from": "pay", "to": f"x{i}", "titles": []} for i in range(81)],
            "elements": DATA["elements"] + [element(f"x{i}", f"X{i}") for i in range(81)], "runtime": []}
    assert run("d.drawingText(d.drawing(data.areas[1].elements, data.areas[1].title, [], base))", data=many) is None
    many["allowed"] = many["allowed"][:80]
    assert run("d.drawingText(d.drawing(data.areas[1].elements, data.areas[1].title, [], base))", data=many).count(" --> ") == 80


RECORDS = {
    **DATA,
    "decisions": [
        {"id": "D-0", "decision": "Keep the web thin.", "reason": None, "rejected": [], "binds": ["shop.web"], "capabilities": ["buy"],
         "status": "current", "evidence": "spec", "sources": []},
        {"id": "D-1", "decision": "Log every call.", "reason": "Audit.", "rejected": [], "binds": ["shop.web", "pay"],
         "obligations": ["Log."], "status": "current", "evidence": "spec", "sources": []},
        {"id": "D-2", "decision": "One API.", "reason": "Simple.", "rejected": [], "binds": ["shop.api"], "status": "planned",
         "evidence": "spec", "sources": []},
        {"id": "P-1", "decision": "Data stays in the EU.", "reason": "Law.", "rejected": [], "binds": [], "obligations": ["EU only."],
         "status": "current", "evidence": "spec", "sources": []},
    ],
    "contracts": [{"id": "C-1", "name": "Card API", "owner": "pay", "bound": ["shop.web"], "obligations": ["Ids"],
                   "compatibility": None, "capabilities": ["buy"]}],
    "holes": [{"id": "H-1", "what": "Why one API?", "binds": ["shop.api"], "evidence": "search"}],
    "capabilities": [
        {"name": "audit", "title": "Audit", "description": None, "steps": [
            {"from": "bank", "to": "ledger", "label": None, "reply": False, "kinds": ["uses"]}]},
        {"name": "buy", "title": "Buy", "description": "Buy a thing.", "steps": [
            {"from": "shop.web", "to": "shop.api", "label": "order", "reply": False, "kinds": ["uses"]},
            {"from": "shop.api", "to": "pay.gateway", "label": None, "reply": False, "kinds": ["http", "uses"]},
            {"from": "pay.gateway", "to": "shop.api", "label": "paid", "reply": True, "kinds": ["http"]}]},
    ],
}


def built(module: str, code: str, data: dict = RECORDS, gap: list = GAP) -> dict:
    snippet = (
        f"import * as m from {json.dumps(lib_url(module, DOCS_LIB))};\n"
        f"import {{ documentBase }} from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\n"
        f"const data = {json.dumps(data)};\nconst gap = {json.dumps(gap)};\nconst base = documentBase(data);\n"
        f"process.stdout.write(JSON.stringify({code}));\n"
    )
    proc = run_module(snippet)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def area_doc(index: int = 0, data: dict = RECORDS, gap: list = GAP) -> dict:
    return built("area.mjs", f"m.buildArea(data, gap, data.areas[{index}], base)", data, gap)


def section(document: dict, title: str) -> list:
    """The blocks under the level-2 heading `title`, up to the next level-2 heading."""
    blocks = document["blocks"]
    start = blocks.index({"type": "heading", "level": 2, "text": title}) + 1
    end = next((at for at in range(start, len(blocks)) if blocks[at]["type"] == "heading" and blocks[at]["level"] == 2), len(blocks))
    return blocks[start:end]


def L(text: str, href: str) -> dict:
    return {"type": "link", "text": text, "href": href}


def para(text: str) -> dict:
    return {"type": "paragraph", "parts": [text]}


def heads(document: dict, level: int) -> list:
    return [block["text"] for block in document["blocks"] if block["type"] == "heading" and block["level"] == level]


def test_area_document_layout() -> None:  # Area: title, description, then the sections in order
    document = area_doc()
    assert document["title"] == "Front"
    assert document["blocks"][0] == para("The shop.")
    assert heads(document, 2) == ["Diagram", "Elements", "Dependencies", "Decisions", "Contracts", "Open questions", "Known gap",
                                  "Capabilities"]
    diagram = section(document, "Diagram")
    assert len(diagram) == 1 and diagram[0]["type"] == "diagram"
    assert diagram[0]["text"].startswith('flowchart LR\n  subgraph frame["Front"]\n')
    assert '  n6 -->|"known gap"| n2' in diagram[0]["text"]


def test_area_document_elements() -> None:  # Area: Elements (id, title, description, code, rules, tags)
    rows = section(area_doc(), "Elements")[0]
    assert rows["header"] == ["Element", "Title", "Description", "Code", "Rules", "Tags"]
    assert rows["rows"] == [
        [["shop"], ["Shop"], ["Sells things."], ["src/shop, src/lib"], ["BR-1, BR-2"], ["#edge #web"]],
        [["shop.api"], ["API"], [""], [""], [""], [""]],
        [["shop.api.orders"], ["Orders"], [""], [""], [""], [""]],
        [["shop.web"], ["Web"], [""], [""], [""], [""]],
    ]


def test_area_document_links_an_element_held_by_another_area() -> None:  # Shared rules: an id links to its first area
    data = {**RECORDS, "areas": [{"name": "core", "title": "Core", "description": None, "elements": ["shop.api"]}, *RECORDS["areas"]]}
    rows = section(area_doc(1, data), "Elements")[0]["rows"]
    assert [row[0] for row in rows] == [["shop"], [L("shop.api", "core.md")], ["shop.api.orders"], ["shop.web"]]


def test_area_document_dependencies() -> None:  # Area: Dependencies, each with the other end's areas
    table = section(area_doc(), "Dependencies")[0]
    assert table["header"] == ["Element", "Relation", "Other end", "Kind and titles", "Its areas"]
    money = [L("money", "money.md"), " (Money)"]
    assert table["rows"] == [
        [["shop"], ["runtime to"], [L("pay", "money.md"), " (Pay)"], ["http"], money],
        [["shop.api"], ["uses"], [L("pay", "money.md"), " (Pay)"], [""], money],
        [["shop.api"], ["used by"], [L("shop.web", "front.md"), " (Web)"], [""], [L("front", "front.md"), " (Front)"]],
        [["shop.api"], ["runtime to"], [L("pay.gateway", "money.md"), " (Gateway)"], ['http, "charges"'], money],
        [["shop.api.orders"], ["uses"], [L("pay.gateway", "money.md"), " (Gateway)"], [""], money],
        [["shop.web"], ["uses"], [L("bank", "../README.md"), " (Bank)"], [""], ["Not in any area"]],
        [["shop.web"], ["uses"], [L("shop.api", "front.md"), " (API)"], [""], [L("front", "front.md"), " (Front)"]],
        [["shop.web"], ["runtime to"], [L("bank", "../README.md"), " (Bank)"], ['event, "reports"'], ["Not in any area"]],
        [["shop.web"], ["runtime to"], [L("bank", "../README.md"), " (Bank)"], ['http, "feeds", "reports"'], ["Not in any area"]],
    ]


def test_area_document_runtime_from() -> None:  # Area: an incoming runtime link names its source
    rows = section(area_doc(1), "Dependencies")[0]["rows"]
    assert [row[1][0] for row in rows] == ["used by", "used by", "runtime from", "used by", "runtime from"]
    assert rows[2] == [["pay"], ["runtime from"], [L("shop", "front.md"), " (Shop)"], ["http"], [L("front", "front.md"), " (Front)"]]


def test_area_document_decisions() -> None:  # Area: cross-cutting first, by id; "Also binds"; AC-20
    blocks = section(area_doc(), "Decisions")
    assert [block["text"] for block in blocks if block["type"] == "heading"] == ["D-1", "D-0", "D-2"]
    d1 = blocks[2]["items"]
    assert d1[-1] == ["Also binds: ", L("money", "money.md"), " (Money)"]
    assert ["Reason: ", "Reason not known"] in blocks[5]["items"]
    assert not any(item[0] == "Also binds: " for item in blocks[5]["items"])
    money = section(area_doc(1), "Decisions")
    assert [block["text"] for block in money if block["type"] == "heading"] == ["D-1"]
    assert money[2]["items"][-1] == ["Also binds: ", L("front", "front.md"), " (Front)"]
    assert "P-1" not in json.dumps(area_doc()) and "P-1" not in json.dumps(area_doc(1))


def test_area_document_contracts_open_questions_gap_and_capabilities() -> None:  # Area: the rest, in full
    document = area_doc()
    contracts = section(document, "Contracts")
    assert contracts[0] == {"type": "heading", "level": 3, "text": "C-1: Card API"}
    assert contracts[1]["items"][-1] == ["Also in: ", L("money", "money.md"), " (Money)"]
    holes = section(document, "Open questions")
    assert [holes[0]["text"], holes[1]] == ["H-1", para("Why one API?")]
    gap = section(document, "Known gap")[0]
    assert gap["header"] == ["From", "To", "Reason", "Close by"]
    assert gap["rows"] == [[[L("shop.api", "front.md"), " (API)"], [L("ledger", "../README.md"), " (Ledger)"],
                            ["cycle in current code"], ["2027-01"]]]
    capabilities = section(document, "Capabilities")[0]
    assert capabilities["header"] == ["Capability", "Description"]
    assert capabilities["rows"] == [[[L("buy", "../capabilities/buy.md"), " (Buy)"], ["Buy a thing."]]]


def test_area_document_known_gap_with_no_close_by() -> None:  # Area: `close_by` is optional
    rows = section(area_doc(1), "Known gap")[0]["rows"]
    assert rows == [[[L("bank", "../README.md"), " (Bank)"], [L("pay", "money.md"), " (Pay)"], ["between neighbours"], [""]]]


def test_area_document_with_nothing() -> None:  # Area: an empty section says so; no description, no paragraph
    data = {**RECORDS, "areas": [{"name": "side", "title": "Side", "description": None, "elements": []}]}
    document = area_doc(0, data)
    assert document["blocks"][0] == {"type": "heading", "level": 2, "text": "Diagram"}
    assert section(document, "Elements") == [para("The area has no elements.")]
    assert section(document, "Dependencies") == [para("No dependencies.")]
    assert section(document, "Decisions") == [para("No decisions bind an element of this area.")]
    assert section(document, "Contracts") == [para("No contracts.")]
    assert section(document, "Open questions") == [para("No open questions.")]
    assert section(document, "Known gap") == [para("No known-gap entries.")]
    assert section(document, "Capabilities") == [para("No capabilities pass through this area.")]


def test_area_document_over_the_arrow_limit() -> None:  # AC-21: the note, and the tables complete
    data = {**RECORDS, "allowed": [{"from": "pay", "to": f"x{i:02}", "titles": []} for i in range(81)], "runtime": [],
            "elements": RECORDS["elements"] + [element(f"x{i:02}", f"X{i}") for i in range(81)]}
    document = area_doc(1, data, [])
    assert section(document, "Diagram") == [para("The diagram has more than 80 arrows and is not drawn; the tables list everything.")]
    assert len(section(document, "Dependencies")[0]["rows"]) == 81


def capability_doc(index: int = 1, data: dict = RECORDS) -> dict:
    return built("capability.mjs", f"m.buildCapability(data, data.capabilities[{index}], base)", data, [])


def test_capability_document() -> None:  # Capability: title, description, sequence, steps, records, areas; AC-18
    document = capability_doc()
    assert document["title"] == "Buy"
    assert document["blocks"][0] == para("Buy a thing.")
    assert heads(document, 2) == ["Sequence", "Steps", "Decisions", "Contracts", "Areas involved"]
    assert section(document, "Sequence") == [{"type": "diagram", "text": (
        "sequenceDiagram\n  participant n3 as Web\n  participant n2 as API\n  participant n1 as Gateway\n"
        "  n3->>n2: order\n  n2->>n1: \n  n1-->>n2: paid")}]
    table = section(document, "Steps")[0]
    assert table["header"] == ["Step", "From", "To", "Label", "Call or reply", "Kinds"]
    web, api, gateway = ([L(id_, f"../areas/{area}.md"), f" ({title})"] for id_, area, title in
                         (("shop.web", "front", "Web"), ("shop.api", "front", "API"), ("pay.gateway", "money", "Gateway")))
    assert table["rows"] == [
        [["1"], web, api, ["order"], ["call"], ["uses"]],
        [["2"], api, gateway, [""], ["call"], ["http, uses"]],
        [["3"], gateway, api, ["paid"], ["reply"], ["http"]],
    ]


def test_capability_document_records_and_areas() -> None:  # Capability: the records naming it; the areas involved
    document = capability_doc()
    decisions = section(document, "Decisions")
    assert [block["text"] for block in decisions if block["type"] == "heading"] == ["D-0"]
    assert decisions[2]["items"][-1] == ["Areas: ", L("front", "../areas/front.md"), " (Front)"]
    contracts = section(document, "Contracts")
    assert contracts[0]["text"] == "C-1: Card API"
    assert section(document, "Areas involved") == [{"type": "list", "items": [
        [L("front", "../areas/front.md"), " (Front)"], [L("money", "../areas/money.md"), " (Money)"]]}]


def test_capability_document_outside_any_area() -> None:  # Capability: "Not in any area"; empty sections say so
    document = capability_doc(0)
    assert document["blocks"][0] == {"type": "heading", "level": 2, "text": "Sequence"}
    assert section(document, "Decisions") == [para("No decisions name this capability.")]
    assert section(document, "Contracts") == [para("No contracts name this capability.")]
    assert section(document, "Areas involved") == [{"type": "list", "items": [["Not in any area"]]}]
    assert section(document, "Steps")[0]["rows"][0][1] == [L("bank", "../README.md"), " (Bank)"]


def test_capability_document_with_an_end_in_no_area_and_one_in_an_area() -> None:  # Capability: both kinds of end
    data = {**RECORDS, "capabilities": [{"name": "feed", "title": "Feed", "description": None, "steps": [
        {"from": "bank", "to": "pay", "label": "settle", "reply": False, "kinds": ["uses"]}]}]}
    assert section(capability_doc(0, data), "Areas involved") == [{"type": "list", "items": [
        [L("money", "../areas/money.md"), " (Money)"], ["Not in any area"]]}]


def test_capability_document_with_no_steps() -> None:  # Capability: a capability with no steps
    data = {**RECORDS, "capabilities": [{"name": "idle", "title": "Idle", "description": None, "steps": []}]}
    document = capability_doc(0, data)
    assert section(document, "Sequence") == [para("The capability has no steps.")]
    assert section(document, "Steps") == [para("No steps.")]
    assert section(document, "Areas involved") == [para("No areas.")]


def test_capability_document_step_limit() -> None:  # AC-21 (capability part): 200 steps drawn, 201 replaced by the note
    step = {"from": "shop.web", "to": "shop.api", "label": "x", "reply": False, "kinds": ["uses"]}
    for count, drawn in ((200, True), (201, False)):
        data = {**RECORDS, "capabilities": [{"name": "loop", "title": "Loop", "description": None, "steps": [step] * count}]}
        document = capability_doc(0, data)
        sequence = section(document, "Sequence")
        if drawn:
            assert sequence[0]["type"] == "diagram" and sequence[0]["text"].count("->>") == 200
        else:
            assert sequence == [para("The capability has more than 200 steps, so its sequence diagram is not drawn; "
                                     "the steps table lists every step.")]
        assert len(section(document, "Steps")[0]["rows"]) == count
