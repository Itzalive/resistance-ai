"""The cycle search (spec 2026-11-21-defining-architecture-records-design.md, "`cycles`")."""

from __future__ import annotations

from arch_delta_support import RECORDS_LIB, call, require_node

require_node()


def model(ids: list, rels: list) -> dict:
    return {"elements": [{"id": id_, "code": [id_]} for id_ in ids], "relationships": [{"from": f, "to": t} for f, t in rels]}


def cycles(ids: list, rels: list, edges: list) -> dict:
    out = call("cycles.mjs", "findCycles", model(ids, rels), edges, ".", lib=RECORDS_LIB)
    assert out["ok"], out
    return out["value"]


def leave(from_: str, to: str, edges: int) -> dict:
    return {"from": from_, "to": to, "module_edges": edges}


def test_tie_on_module_edges_goes_to_the_first_pair_list() -> None:  # AC-10
    value = cycles(
        ["a", "b", "c", "x", "x.d", "x.e"],
        [("a", "b"), ("b", "c"), ("c", "a"), ("x.d", "x.e"), ("x.e", "x.d")],
        [["a.1", "b.1"], ["a.2", "b.1"], ["a.3", "b.1"], ["b.1", "c.1"], ["c.1", "a.1"],
         ["x.d.1", "x.e.1"], ["x.e.1", "x.d.1"]],
    )
    assert value == {
        "groups": [
            {"parent": None, "siblings": ["a", "b", "c"], "leave_out": [leave("b", "c", 1)], "too_large": None},
            {"parent": "x", "siblings": ["x.d", "x.e"], "leave_out": [leave("x.d", "x.e", 1)], "too_large": None},
        ],
        "summary": {"relationships": 2, "groups": 2, "too_large": 0},
    }


def test_cycle_between_children_is_found_at_their_level() -> None:  # AC-11
    value = cycles(
        ["A", "A.k", "B", "P", "P.q", "P.r", "S"],
        [("A.k", "B"), ("B", "A"), ("P.q", "P.r"), ("P.r", "P.q")],
        [["A.k.1", "B.1"], ["A.k.2", "B.1"], ["B.1", "A.1"], ["P.q.1", "P.r.1"], ["P.r.1", "P.q.1"]],
    )
    assert [(g["parent"], g["siblings"]) for g in value["groups"]] == [(None, ["A", "B"]), ("P", ["P.q", "P.r"])]
    assert value["groups"][0]["leave_out"] == [leave("B", "A", 1)]


def test_fewest_relationships_come_first() -> None:
    value = cycles(
        ["a", "a.x", "a.y", "b"],
        [("a.x", "b"), ("a.y", "b"), ("b", "a")],
        [["a.x.1", "b.1"], ["a.y.1", "b.1"], *[["b.1", f"a.{n}"] for n in range(5)]],
    )
    assert value["groups"][0]["leave_out"] == [leave("b", "a", 5)]


def test_distinct_module_edges_decide_a_tie() -> None:
    # Leaving out o -> i (two relationships that share one module edge) or i -> o with i -> z (two relationships, two
    # module edges) both leave out two relationships; counted once, o -> i has fewer module edges.
    value = cycles(
        ["o", "o.x", "i", "z"],
        [("o", "i"), ("o.x", "i"), ("i", "o"), ("i", "z"), ("z", "o")],
        [["o.x.1", "i.1"], ["i.1", "o.1"], ["i.1", "z.1"], ["z.1", "o.1"]],
    )
    assert value["groups"][0]["leave_out"] == [leave("o", "i", 1), leave("o.x", "i", 1)]


def test_groups_in_level_order_then_by_siblings() -> None:
    value = cycles(
        ["c", "d", "a", "b", "p", "p.m", "p.n"],
        [("c", "d"), ("d", "c"), ("a", "b"), ("b", "a"), ("p.m", "p.n"), ("p.n", "p.m")],
        [],
    )
    assert [g["siblings"] for g in value["groups"]] == [["a", "b"], ["c", "d"], ["p.m", "p.n"]]
    assert value["summary"] == {"relationships": 3, "groups": 3, "too_large": 0}


def complete(n: int) -> list:
    nodes = [f"n{i}" for i in range(1, n + 1)]
    return [(f, t) for f in nodes for t in nodes if f != t]


def test_twenty_pairs_are_searched_and_twenty_one_are_too_large() -> None:  # AC-12
    nodes = [f"n{i}" for i in range(1, 7)]
    twenty = cycles(nodes[:5], complete(5), [])
    [group] = twenty["groups"]
    assert group["too_large"] is None
    assert group["leave_out"] == [leave(f, t, 0) for f, t in complete(5) if f < t]
    twenty_one = [pair for pair in complete(5) if pair != ("n2", "n1")] + [("n5", "n6"), ("n6", "n1")]
    value = cycles(nodes, twenty_one, [])
    assert value == {"groups": [{"parent": None, "siblings": nodes, "leave_out": [], "too_large": 21}],
                     "summary": {"relationships": 0, "groups": 1, "too_large": 1}}


def test_no_cycle_gives_no_group() -> None:  # AC-14
    assert cycles(["a", "b"], [("a", "b")], [["a.1", "b.1"]]) == {
        "groups": [], "summary": {"relationships": 0, "groups": 0, "too_large": 0}}


def test_relationship_into_its_own_child_gives_no_pair() -> None:
    assert cycles(["a", "a.x"], [("a", "a.x"), ("a.x", "a")], [])["groups"] == []
