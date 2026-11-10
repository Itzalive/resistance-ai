from __future__ import annotations

import json

from arch_delta_support import lib_url, require_node, run_module

require_node()


def element(id_: str, code: str | None = None, tags: list[str] | None = None) -> dict:
    return {"id": id_, "kind": "component", "tags": tags or [], "code": [code] if code else [], "rules": []}


def compare(elements: list[dict], relationships: list[tuple[str, str]], edges: list[list[str]], **options) -> dict:
    model = {"elements": elements, "relationships": [{"from": a, "to": b} for a, b in relationships]}
    opts = {"separator": ".", **options}
    code = (
        f"import {{ compare }} from {json.dumps(lib_url('match.mjs'))};\n"
        f"const out = compare({json.dumps(model)}, {json.dumps(edges)}, {json.dumps(opts)});\n"
        "process.stdout.write(JSON.stringify(out));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def pairs(items: list[dict]) -> list[tuple[str, str]]:
    return sorted((item["from"], item["to"]) for item in items)


def test_longest_prefix_wins_and_separator_counts() -> None:
    out = compare(
        [element("shop", "shop"), element("shop.orders", "shop.orders"), element("c", "cat")],
        [],
        [["shop.orders.api", "cat"], ["shop.ordersx", "cat"]],
    )
    assert pairs(out["breaches"]) == [("shop", "c"), ("shop.orders", "c")]


def test_other_separator() -> None:
    out = compare([element("a", "src/a"), element("b", "src/b")], [], [["src/a/x", "src/b"]], separator="/")
    assert pairs(out["breaches"]) == [("a", "b")]


def test_ignored_edges_and_unmapped_sources() -> None:
    out = compare(
        [element("a", "a"), element("a.b", "a.b")],
        [],
        [["a.x", "a.y"], ["a.b.x", "a.y"], ["a.x", "ext.lib"], ["zz.q", "a.x"]],
    )
    assert out["breaches"] == []
    assert out["unmapped"] == ["zz.q"]


def test_container_relationship_allows_its_components() -> None:
    elements = [element("A"), element("A.c", "A.c"), element("B"), element("B.d", "B.d")]
    assert compare(elements, [("A", "B")], [["A.c.x", "B.d.y"]])["breaches"] == []
    assert pairs(compare(elements, [], [["A.c.x", "B.d.y"]])["breaches"]) == [("A.c", "B.d")]


PROTECTED = [
    element("o", "o"),
    element("s"),
    element("s.p", "s.p", ["protected"]),
    element("s.p.a", "s.p.a"),
    element("s.p.b", "s.p.b"),
]


def test_protected_needs_a_relationship_into_it() -> None:
    edge = [["o.x", "s.p.a.y"]]
    assert pairs(compare(PROTECTED, [("o", "s")], edge)["breaches"]) == [("o", "s.p.a")]
    assert compare(PROTECTED, [("o", "s.p")], edge)["breaches"] == []
    assert compare(PROTECTED, [("o", "s.p.b")], edge)["breaches"] == []


def test_children_of_a_protected_element_follow_the_ordinary_rule() -> None:
    edge = [["s.p.a.x", "s.p.b.y"]]
    assert pairs(compare(PROTECTED, [], edge)["breaches"]) == [("s.p.a", "s.p.b")]
    assert compare(PROTECTED, [("s.p.a", "s.p.b")], edge)["breaches"] == []
    assert compare(PROTECTED, [("s.p.a", "s")], edge)["breaches"] == []


def test_breach_carries_its_module_edges() -> None:
    out = compare([element("a", "a"), element("b", "b")], [], [["a.one", "b.x"], ["a.two", "b.x"]])
    assert sorted(map(tuple, out["breaches"][0]["edges"])) == [("a.one", "b.x"), ("a.two", "b.x")]


def test_not_yet_reached_and_exit_code() -> None:
    out = compare(PROTECTED, [("o", "s.p"), ("o", "s")], [])
    assert pairs(out["notYetReached"]) == [("o", "s.p")]
    assert out["exitCode"] == 0
    reached = compare(PROTECTED, [("o", "s.p")], [["o.x", "s.p.a.y"]])
    assert reached["notYetReached"] == []


def test_new_breach_sets_exit_code_one() -> None:
    assert compare([element("a", "a"), element("b", "b")], [], [["a", "b"]])["exitCode"] == 1


def test_tick_runs_after_every_10000_edges() -> None:
    model = {"elements": [element("a", "a")], "relationships": []}
    for count, ticks in ((10_000, 0), (10_001, 1), (20_000, 1), (20_001, 2)):
        edges = [[f"a.m{i}", "a"] for i in range(count)]
        code = (
            f"import {{ compare }} from {json.dumps(lib_url('match.mjs'))};\n"
            "let ticks = 0;\n"
            f"compare({json.dumps(model)}, {json.dumps(edges)}, {{ separator: '.', tick: () => {{ ticks += 1; }} }});\n"
            "process.stdout.write(String(ticks));\n"
        )
        proc = run_module(code)
        assert proc.returncode == 0, proc.stderr
        assert int(proc.stdout) == ticks, count


def test_nearest_protected_ancestor_is_the_guard() -> None:
    elements = [
        element("s", "s", ["protected"]),
        element("s.q", "s.q"),
        element("s.p", "s.p", ["protected"]),
        element("s.p.a", "s.p.a"),
    ]
    edge = [["s.q.x", "s.p.a.y"]]
    assert pairs(compare(elements, [("s.q", "s")], edge)["breaches"]) == [("s.q", "s.p.a")]
    assert compare(elements, [("s.q", "s.p")], edge)["breaches"] == []


def test_allowed_is_decided_per_pair_not_per_source() -> None:
    elements = [element("a", "a"), element("b", "b"), element("c", "c")]
    for edges in ([["a.x", "b"], ["a.x", "c"]], [["a.x", "c"], ["a.x", "b"]]):
        assert pairs(compare(elements, [("a", "b")], edges)["breaches"]) == [("a", "c")]


def test_edge_from_an_element_into_its_descendant_is_ignored() -> None:
    out = compare([element("a", "a"), element("a.b", "a.b")], [], [["a.x", "a.b.x"]])
    assert out["breaches"] == []


def test_not_yet_reached_needs_code_at_the_source() -> None:
    assert compare(PROTECTED, [("s", "o")], [])["notYetReached"] == []


def test_not_yet_reached_needs_an_edge_into_the_target() -> None:
    out = compare(PROTECTED, [("o", "s.p.b")], [["o.x", "s.p.a.y"]])
    assert pairs(out["notYetReached"]) == [("o", "s.p.b")]


def test_duplicate_relationships_are_reported_once() -> None:
    out = compare(PROTECTED, [("o", "s.p"), ("o", "s.p")], [])
    assert pairs(out["notYetReached"]) == [("o", "s.p")]


def test_sibling_whose_id_starts_with_another_is_not_inside_it() -> None:
    out = compare([element("a", "a"), element("ab", "ab")], [], [["ab.x", "a.x"], ["a.x", "ab.x"]])
    assert pairs(out["breaches"]) == [("a", "ab"), ("ab", "a")]
