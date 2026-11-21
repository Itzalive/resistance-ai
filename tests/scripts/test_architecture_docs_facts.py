"""Facts shared by the generated documents (spec 2026-11-17-architecture-docs-design.md, "Shared rules")."""

from __future__ import annotations

from arch_delta_support import DOCS_LIB, call, require_node

require_node()

DATA = {
    "elements": [{"id": e, "title": e.upper()} for e in ("a", "a.x", "b", "c")],
    "areas": [{"name": "zeta", "title": "Zeta", "elements": ["a", "a.x"]}, {"name": "alpha", "title": "Alpha", "elements": ["a.x", "b"]}],
    "capabilities": [{"name": "pay", "title": "Pay", "steps": []}],
}


def facts(fn: str, *args) -> object:
    result = call("facts.mjs", fn, *args, lib=DOCS_LIB)
    assert result["ok"], result
    return result["value"]


def run(code: str) -> object:
    from arch_delta_support import lib_url, run_module
    import json
    snippet = f"import * as f from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\nconst data = {json.dumps(DATA)};\n{code}"
    proc = run_module(snippet)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_areas_by_element_are_sorted() -> None:
    assert run("process.stdout.write(JSON.stringify([...f.areasByElement(data)]));") == [
        ["a", ["zeta"]], ["a.x", ["alpha", "zeta"]], ["b", ["alpha"]], ["c", []],
    ]


def test_principles_and_cross_cutting() -> None:
    cases = [
        {"binds": [], "obligations": ["o"]},
        {"binds": [], "obligations": ["o"], "owner": "a"},
        {"binds": ["a"], "obligations": ["o"]},
        {"binds": []},
    ]
    assert [facts("isPrinciple", d) for d in cases] == [True, False, False, False]
    assert [facts("isCrossCutting", d) for d in cases] == [True, True, True, False]


def test_record_targets() -> None:
    code = (
        "const by = f.areasByElement(data);\n"
        "process.stdout.write(JSON.stringify([\n"
        "  f.recordTarget('decisions', { binds: ['a.x'] }, by),\n"
        "  f.recordTarget('decisions', { binds: [], obligations: ['o'] }, by),\n"
        "  f.recordTarget('decisions', { binds: ['c'] }, by),\n"
        "  f.recordTarget('contracts', { owner: 'b', bound: ['c'] }, by),\n"
        "  f.recordTarget('holes', { binds: ['a'] }, by),\n"
        "  f.elementTarget('a.x', by), f.elementTarget('c', by),\n"
        "]));\n"
    )
    assert run(code) == ["areas/alpha.md", "README.md", "README.md", "areas/alpha.md", "areas/zeta.md", "areas/alpha.md", "README.md"]


def test_relative_links() -> None:
    assert [facts("relative", "README.md", "areas/a.md"), facts("relative", "areas/a.md", "README.md"),
            facts("relative", "areas/a.md", "areas/b.md"), facts("relative", "README.md", "README.md")] == [
        "areas/a.md", "../README.md", "b.md", "README.md",
    ]


def test_relative_refuses_a_target_outside_the_output_folder() -> None:
    for target in ("../x.md", "/x.md", "areas/../../x.md"):
        result = call("facts.mjs", "relative", "areas/a.md", target, lib=DOCS_LIB)
        assert result["ok"] is False
        assert result["message"] == f"link target {target} leaves the output folder"


def test_top_level() -> None:
    assert [facts("topLevel", "a"), facts("topLevel", "a.x.y")] == ["a", "a"]


def blocks(js: str, doc: str = "README.md", area: str = "null") -> object:
    import json
    from arch_delta_support import lib_url, run_module
    code = (
        f"import * as f from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\n"
        f"import * as r from {json.dumps(lib_url('records-doc.mjs', DOCS_LIB))};\n"
        f"const data = {json.dumps(DATA)};\n"
        "const byElement = f.areasByElement(data);\n"
        "const decisions = new Map([['D-0', { id: 'D-0', binds: ['b'] }]]);\n"
        f"const ctx = {{ doc: {json.dumps(doc)}, byElement, titles: f.titlesOf(data), decisions, area: {area} }};\n"
        f"process.stdout.write(JSON.stringify({js}));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def L(text: str, href: str) -> dict:
    return {"type": "link", "text": text, "href": href}


DECISION = ("{ id: 'D-1', decision: 'Use one store.', reason: null, rejected: ['Two stores', 'None'], binds: ['a', 'b'], "
            "status: 'superseded', superseded_by: 'D-0', evidence: 'spec', sources: ['docs/x.md'], owner: 'a', "
            "obligations: ['Keep ids'], compatibility: 'Additive only.', capabilities: ['pay'], note: 'N' }")


def test_decision_in_full() -> None:
    assert blocks(f"r.decisionBlocks({DECISION}, ctx)") == [
        {"type": "heading", "level": 3, "text": "D-1"},
        {"type": "paragraph", "parts": ["Use one store."]},
        {"type": "list", "items": [
            ["Reason: ", "Reason not known"],
            ["Rejected: ", "Two stores; None"],
            ["Obligations: ", "Keep ids"],
            ["Owner: ", L("a", "areas/zeta.md"), " (A)"],
            ["Compatibility: ", "Additive only."],
            ["Capabilities: ", L("pay", "capabilities/pay.md"), " (Pay)"],
            ["Status: superseded by ", L("D-0", "areas/alpha.md")],
            ["Evidence: ", "spec"],
            ["Sources: ", "docs/x.md"],
            ["Note: ", "N"],
            ["Binds: ", L("a", "areas/zeta.md"), " (A)", ", ", L("b", "areas/alpha.md"), " (B)"],
            ["Areas: ", L("alpha", "areas/alpha.md"), " (Alpha)", ", ", L("zeta", "areas/zeta.md"), " (Zeta)"],
        ]},
    ]


def test_decision_in_an_area_document() -> None:
    items = blocks(f"r.decisionBlocks({DECISION}, ctx)", doc="areas/zeta.md", area="'zeta'")[2]["items"]
    assert items[-1] == ["Also binds: ", L("alpha", "alpha.md"), " (Alpha)"]
    assert items[3] == ["Owner: ", L("a", "zeta.md"), " (A)"]


def test_contract_and_open_question_in_full() -> None:
    contract = "{ id: 'C-1', name: 'Orders API', owner: 'b', bound: ['c'], obligations: ['Ids', 'Order'], compatibility: null, decisions: ['D-0'] }"
    assert blocks(f"r.contractBlocks({contract}, ctx)") == [
        {"type": "heading", "level": 3, "text": "C-1: Orders API"},
        {"type": "list", "items": [
            ["Owner: ", L("b", "areas/alpha.md"), " (B)"],
            ["Bound: ", L("c", "README.md"), " (C)"],
            ["Obligations: ", "Ids; Order"],
            ["Compatibility: ", "No rule stated"],
            ["Decisions: ", L("D-0", "areas/alpha.md")],
            ["Areas: ", L("alpha", "areas/alpha.md"), " (Alpha)"],
        ]},
    ]
    hole = "{ id: 'H-1', what: 'Why two caches?', binds: ['c'], evidence: 'search' }"
    assert blocks(f"r.holeBlocks({hole}, ctx)") == [
        {"type": "heading", "level": 3, "text": "H-1"},
        {"type": "paragraph", "parts": ["Why two caches?"]},
        {"type": "list", "items": [["Binds: ", L("c", "README.md"), " (C)"], ["Evidence: ", "search"]]},
    ]


RECORDS = {
    "elements": [{"id": e, "title": e} for e in ("bank", "pay", "shop", "shop.api", "shop.web")],
    "areas": [{"name": "front", "title": "Front", "elements": ["shop", "shop.api", "shop.web"]},
              {"name": "money", "title": "Money", "elements": ["pay"]}],
    "capabilities": [{"name": "buy", "title": "Buy", "steps": [
        {"from": "shop.web", "to": "shop.api"}, {"from": "shop.api", "to": "pay"}, {"from": "pay", "to": "shop.api"}]}],
    "decisions": [
        {"id": "D-1", "binds": ["shop.api"], "capabilities": ["buy"]},
        {"id": "D-2", "binds": ["shop.api", "pay"], "obligations": ["o"]},
        {"id": "D-3", "binds": ["bank"]},
        {"id": "D-4", "binds": ["shop.web"], "obligations": ["o"]},
        {"id": "P-1", "binds": [], "obligations": ["o"]},
    ],
    "contracts": [{"id": "C-1", "owner": "pay", "bound": ["shop.web"], "capabilities": ["buy"]},
                  {"id": "C-2", "owner": "bank", "bound": ["bank"]},
                  {"id": "C-3", "owner": "pay", "bound": ["bank"]}],
    "holes": [{"id": "H-1", "binds": ["shop.web"]}, {"id": "H-2", "binds": ["bank"]}],
}
GAP = [
    {"from": "shop.web", "to": "bank", "reason": "r", "close_by": None},
    {"from": "shop.api", "to": "bank", "reason": "r", "close_by": None},
    {"from": "bank", "to": "pay", "reason": "r", "close_by": None},
]


def ids(records: list) -> list:
    return [record["id"] for record in records]


def test_area_records() -> None:  # Area: decisions (cross-cutting first), contracts, open questions, known-gap entries
    front = facts("areaRecords", RECORDS, GAP, RECORDS["areas"][0])
    assert ids(front["decisions"]) == ["D-2", "D-4", "D-1"]
    assert ids(front["contracts"]) == ["C-1"]
    assert ids(front["holes"]) == ["H-1"]
    assert [(e["from"], e["to"]) for e in front["gap"]] == [("shop.api", "bank"), ("shop.web", "bank")]
    money = facts("areaRecords", RECORDS, GAP, RECORDS["areas"][1])
    assert (ids(money["decisions"]), ids(money["contracts"]), ids(money["holes"])) == (["D-2"], ["C-1", "C-3"], [])
    assert [(e["from"], e["to"]) for e in money["gap"]] == [("bank", "pay")]


def test_area_records_of_an_area_with_none() -> None:  # Area: an area may have no records
    empty = facts("areaRecords", RECORDS, GAP, {"name": "x", "title": "X", "elements": []})
    assert empty == {"decisions": [], "contracts": [], "holes": [], "gap": []}


def test_capability_records() -> None:  # Capability and AI pack: the elements the steps touch, the records naming it
    buy = facts("capabilityRecords", RECORDS, RECORDS["capabilities"][0])
    assert buy["elements"] == ["pay", "shop.api", "shop.web"]
    assert (ids(buy["decisions"]), ids(buy["contracts"])) == (["D-1"], ["C-1"])


def test_capability_records_with_no_steps_or_names() -> None:  # a record without `capabilities` names none
    empty = facts("capabilityRecords", RECORDS, {"name": "refund", "title": "Refund", "steps": []})
    assert empty == {"elements": [], "decisions": [], "contracts": []}


def run_on(data: dict, code: str) -> object:
    from arch_delta_support import lib_url, run_module
    import json
    snippet = f"import * as f from {json.dumps(lib_url('facts.mjs', DOCS_LIB))};\nconst data = {json.dumps(data)};\n{code}"
    proc = run_module(snippet)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_outside_areas() -> None:  # Overview and AI pack: the facts outside any area
    out = run_on(RECORDS, "process.stdout.write(JSON.stringify(f.outsideAreas(data, f.areasByElement(data))));")
    assert [element["id"] for element in out["elements"]] == ["bank"]
    assert (ids(out["principles"]), ids(out["decisions"]), ids(out["contracts"]), ids(out["holes"])) == (
        ["P-1"], ["D-3"], ["C-2"], ["H-2"])


LINKS = {
    "elements": [{"id": e} for e in ("a", "b", "c")],
    "allowed": [{"from": "a", "to": "b", "titles": []}, {"from": "c", "to": "a", "titles": []}],
    "runtime": [{"from": "b", "to": "a", "kind": "http", "titles": ["t"]}, {"from": "ghost", "to": "c", "kind": "event", "titles": []}],
    "decisions": [{"id": "D-1", "binds": ["a", "a", "c"]}, {"id": "D-2", "binds": ["a"]}],
}


def test_link_index() -> None:  # Area and AI pack: each element's entries, grouped once
    code = ("const i = f.linkIndex(data);\n"
            "process.stdout.write(JSON.stringify(Object.fromEntries([...i].map(([id, e]) => [id, {"
            " from: e.from.map((x) => x.to), to: e.to.map((x) => x.from), out: e.out.map((x) => x.to), in: e.in.map((x) => x.from),"
            " boundBy: e.boundBy.map((d) => d.id) }]))));")
    assert run_on(LINKS, code) == {
        "a": {"from": ["b"], "to": ["c"], "out": [], "in": ["b"], "boundBy": ["D-1", "D-2"]},
        "b": {"from": [], "to": ["a"], "out": ["a"], "in": [], "boundBy": []},
        "c": {"from": ["a"], "to": [], "out": [], "in": ["ghost"], "boundBy": ["D-1"]},
    }


def test_area_capabilities() -> None:  # Area and AI pack: the capabilities with a step whose end is an area element
    data = {"capabilities": [
        {"name": "buy", "steps": [{"from": "shop.web", "to": "shop.api"}]},
        {"name": "pay", "steps": [{"from": "bank", "to": "pay"}]},
        {"name": "refund", "steps": [{"from": "bank", "to": "shop.api"}]},
        {"name": "idle", "steps": []},
    ]}
    names = lambda area: [c["name"] for c in facts("areaCapabilities", data, {"elements": area})]  # noqa: E731
    assert names(["shop.api"]) == ["buy", "refund"]
    assert names(["shop.web"]) == ["buy"]
    assert names(["pay"]) == ["pay"]
    assert names([]) == []
