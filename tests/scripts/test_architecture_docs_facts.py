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


def test_top_level() -> None:
    assert [facts("topLevel", "a"), facts("topLevel", "a.x.y")] == ["a", "a"]
