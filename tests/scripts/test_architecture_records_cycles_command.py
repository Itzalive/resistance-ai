"""The architecture records tool, `cycles` (spec 2026-11-21-defining-architecture-records-design.md, "`cycles`")."""

from __future__ import annotations

import json

from arch_delta_support import RECORDS_SCRIPT, SHOP_MODEL, error_lines, make_repo, require_node, run_tool, write_json

require_node()


def block(name: str, kind: str, code: str, inner: str = "") -> str:
    return f"  {name} = {kind} '{name}' {{\n    metadata {{\n      code '{code}'\n    }}\n{inner}  }}\n"


CYCLE_MODEL = (
    "model {\n"
    + block("a", "component", "a") + block("b", "component", "b") + block("c", "component", "c")
    + block("x", "container", "x", "    d = component 'd' {\n      metadata {\n        code 'x.d'\n      }\n    }\n"
            "    e = component 'e' {\n      metadata {\n        code 'x.e'\n      }\n    }\n    d -> e\n    e -> d\n")
    + "  a -> b\n  b -> c\n  c -> a\n}\n"
)
EDGES = [["a.1", "b.1"], ["a.2", "b.1"], ["a.3", "b.1"], ["b.1", "c.1"], ["c.1", "a.1"], ["x.d.1", "x.e.1"],
         ["x.e.1", "x.d.1"]]


def run(repo, *extra: str):
    return run_tool("cycles", "--repo", repo, "--deps", "deps.json", *extra, script=RECORDS_SCRIPT)


def test_cycles_command_text_and_json(tmp_path) -> None:  # AC-10
    repo = make_repo(tmp_path, CYCLE_MODEL)
    write_json(repo / "deps.json", {"edges": EDGES})
    text = run(repo)
    assert text.returncode == 0, text.stderr
    assert text.stdout == (
        "group top level: a, b, c\n"
        "leave out b -> c (1 module edges)\n"
        "group x: x.d, x.e\n"
        "leave out x.d -> x.e (1 module edges)\n"
        "2 relationships to leave out in 2 groups, 0 too large\n"
    )
    data = json.loads(run(repo, "--format", "json").stdout)
    assert data["summary"] == {"relationships": 2, "groups": 2, "too_large": 0}
    assert data["groups"][1] == {"parent": "x", "siblings": ["x.d", "x.e"],
                                 "leave_out": [{"from": "x.d", "to": "x.e", "module_edges": 1}], "too_large": None}


def test_cycles_command_timeout(tmp_path) -> None:  # AC-13
    repo = make_repo(tmp_path, CYCLE_MODEL)
    write_json(repo / "deps.json", {"edges": EDGES})
    proc = run(repo, "--timeout", "0")
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: timeout: ")


def test_cycles_command_without_a_cycle(tmp_path) -> None:  # AC-14
    repo = make_repo(tmp_path, SHOP_MODEL)
    write_json(repo / "deps.json", {"edges": [["shop.orders.x", "shop.checkout.y"]]})
    text = run(repo)
    assert (text.returncode, text.stdout) == (0, "0 relationships to leave out in 0 groups, 0 too large\n")
    assert json.loads(run(repo, "--format", "json").stdout) == {
        "groups": [], "summary": {"relationships": 0, "groups": 0, "too_large": 0}}


def test_cycles_command_needs_the_dependency_file(tmp_path) -> None:
    repo = make_repo(tmp_path, SHOP_MODEL)
    proc = run(repo)
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: bad-input: --deps file not found"]


def test_cycles_command_leaves_runtime_links_outside_the_cycle_rule(tmp_path) -> None:
    model = ("specification {\n  relationship http\n}\nmodel {\n" + block("a", "component", "a")
             + block("b", "component", "b") + "  a -> b\n  b -[http]-> a\n}\n")
    repo = make_repo(tmp_path, model)
    write_json(repo / "deps.json", {"edges": [["a.1", "b.1"]]})
    proc = run(repo)
    assert (proc.returncode, proc.stdout) == (0, "0 relationships to leave out in 0 groups, 0 too large\n"), proc.stderr


def test_cycles_command_loads_the_known_gap_as_check_does(tmp_path) -> None:  # spec "The helper tool"
    repo = make_repo(tmp_path, CYCLE_MODEL)
    write_json(repo / "deps.json", {"edges": EDGES})
    write_json(repo / "docs" / "architecture" / "known-gap.json", {"entries": [{"from": "nope", "to": "a", "reason": "r"}]})
    proc = run(repo)
    assert proc.returncode == 2
    assert error_lines(proc)[0] == "error: bad-input: --gap entry 0: nope is not a model element"
