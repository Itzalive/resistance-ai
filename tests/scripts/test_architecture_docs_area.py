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
