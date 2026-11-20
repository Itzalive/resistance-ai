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
