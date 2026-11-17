"""Runtime links: only `uses` (or kindless) relationships permit imports (issue #30)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_delta_support import error_lines, load_model, make_repo, make_shim, require_node, run_tool, write_json

require_node()


def model(*relationships: str, kinds: tuple[str, ...] = ("http",), extra: str = "") -> str:
    """Components a, b, c, d with code app.a .. app.d, the given kinds declared, and the given relationships."""
    spec = "specification {\n" + "".join(f"  relationship {k}\n" for k in kinds) + "}\n" if kinds else ""
    parts = "".join(
        f"  {name} = component '{name.upper()}' {{\n    metadata {{\n      code 'app.{name}'\n    }}\n  }}\n" for name in "abcd"
    )
    return spec + "model {\n" + parts + extra + "".join(f"  {r}\n" for r in relationships) + "}\n"


def check(repo: Path, edges: list[list[str]]) -> tuple[int, dict]:
    deps = write_json(repo / "deps.json", {"edges": edges})
    proc = run_tool("check", "--repo", repo, "--deps", deps, "--format", "json")
    assert proc.returncode in (0, 1), proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def breaches(data: dict) -> list[tuple[str, str, str]]:
    return [(b["from"], b["to"], b["gap"]) for b in data["breaches"]]


def test_import_with_only_a_runtime_link_is_a_new_breach(tmp_path) -> None:  # AC-1
    code, data = check(make_repo(tmp_path, model("a -[http]-> b")), [["app.a.x", "app.b.y"]])
    assert breaches(data) == [("a", "b", "new")]
    assert code == 1


def test_that_breach_is_known_when_the_gap_file_lists_it(tmp_path) -> None:  # AC-2
    repo = make_repo(tmp_path, model("a -[http]-> b"))
    write_json(repo / "docs" / "architecture" / "known-gap.json", {"entries": [{"from": "a", "to": "b", "reason": "r"}]})
    code, data = check(repo, [["app.a.x", "app.b.y"]])
    assert breaches(data) == [("a", "b", "known")]
    assert code == 0


def test_runtime_link_is_never_not_yet_reached(tmp_path) -> None:  # AC-3
    code, data = check(make_repo(tmp_path, model("a -[http]-> b")), [["app.c.x", "os"]])
    assert data["not_yet_reached"] == []
    assert code == 0


def test_kindless_and_uses_relationships_both_permit_imports(tmp_path) -> None:  # AC-4
    text = model("a -> b", "c -[uses]-> d")
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "app.b.y"], ["app.c.x", "app.d.y"]])
    assert data["breaches"] == [] and data["not_yet_reached"] == []
    assert code == 0
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "os"]])
    assert data["not_yet_reached"] == [{"from": "a", "to": "b"}, {"from": "c", "to": "d"}]


def test_import_relationship_beside_a_runtime_link_permits(tmp_path) -> None:  # AC-5
    code, data = check(make_repo(tmp_path, model("a -> b", "a -[http]-> b")), [["app.a.x", "app.b.y"]])
    assert data["breaches"] == []
    assert code == 0


PROTECTED = """  r = component 'R' {
    metadata {
      code 'app.r'
    }
    p = component 'P' {
      #protected
      metadata {
        code 'app.r.p'
      }
    }
  }
"""


def test_runtime_link_into_a_protected_element_does_not_open_it(tmp_path) -> None:  # AC-6
    text = model("a -> r", "a -[http]-> r.p", extra=PROTECTED)
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "app.r.p.y"]])
    assert breaches(data) == [("a", "r.p", "new")]
    assert code == 1


def test_kind_name_is_compared_exactly(tmp_path) -> None:  # AC-12
    text = model("a -[Uses]-> b", kinds=("Uses",))
    code, data = check(make_repo(tmp_path, text), [["app.a.x", "app.b.y"]])
    assert breaches(data) == [("a", "b", "new")]


def test_loader_returns_import_relationships_and_runtime_links_apart(tmp_path) -> None:
    repo = make_repo(tmp_path, model("a -> b", "c -[uses]-> d", "a -[http]-> c", "d -[push]-> a", kinds=("http", "push")))
    value = load_model(repo / "docs" / "architecture")["value"]
    assert sorted((r["from"], r["to"]) for r in value["relationships"]) == [("a", "b"), ("c", "d")]
    assert sorted((r["from"], r["to"], r["kind"]) for r in value["runtime"]) == [("a", "c", "http"), ("d", "a", "push")]
    assert all(set(r) == {"from", "to"} for r in value["relationships"])


KIND_SHIM = """const E = (id) => ({ id, kind: 'component', tags: [], getMetadata() { return {}; } });
export class LikeC4 {
  static async fromWorkspace() {
    return {
      getErrors() { return []; },
      async computedModel() {
        return { elements() { return [E('a'), E('b')]; }, relationships() { return [RELATIONSHIP]; } };
      },
    };
  }
}
"""


def export_with(tmp_path: Path, relationship: str):
    repo = make_repo(tmp_path, None)
    make_shim(repo / "node_modules", source=KIND_SHIM.replace("RELATIONSHIP", relationship))
    return run_tool("export", "--repo", repo)


@pytest.mark.parametrize("kind", ["5", "''", "{}", "['uses']"])
def test_bad_kind_from_likec4_is_internal(tmp_path, kind: str) -> None:  # AC-11, first half
    proc = export_with(tmp_path, f"{{ source: {{ id: 'a' }}, target: {{ id: 'b' }}, kind: {kind} }}")
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: internal: ")
    assert proc.stdout == ""


@pytest.mark.parametrize("relationship", [
    "{ source: { id: 'a' }, target: { id: 'b' } }",
    "{ source: { id: 'a' }, target: { id: 'b' }, kind: null }",
    "{ source: { id: 'a' }, target: { id: 'b' }, kind: undefined }",
])
def test_missing_or_null_kind_is_an_import_relationship(tmp_path, relationship: str) -> None:  # AC-11, second half
    proc = export_with(tmp_path, relationship)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["allowed"] == [{"from": "a", "to": "b"}]
def export(repo: Path) -> dict:
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_export_lists_runtime_links_once_per_pair_and_kind(tmp_path) -> None:  # AC-7
    text = model(
        "a -> b", "c -[uses]-> d", "c -[push]-> a", "a -[http]-> b 'one'", "a -[http]-> b 'two'", "a -[calls]-> b",
        kinds=("http", "push", "calls"),
    )
    data = export(make_repo(tmp_path, text))
    assert list(data) == ["format", "elements", "allowed", "runtime"]
    assert data["format"] == 2
    assert data["allowed"] == [{"from": "a", "to": "b"}, {"from": "c", "to": "d"}]
    assert data["runtime"] == [
        {"from": "a", "to": "b", "kind": "calls"}, {"from": "a", "to": "b", "kind": "http"},
        {"from": "c", "to": "a", "kind": "push"},
    ]


def test_runtime_links_in_both_directions_are_exported_and_not_allowed(tmp_path) -> None:  # AC-8
    data = export(make_repo(tmp_path, model("a -[http]-> b", "b -[http]-> a")))
    assert data["runtime"] == [{"from": "a", "to": "b", "kind": "http"}, {"from": "b", "to": "a", "kind": "http"}]
    assert data["allowed"] == []


def test_long_kind_name_is_cleaned(tmp_path) -> None:  # AC-9
    kind = "k" * 201
    data = export(make_repo(tmp_path, model(f"a -[{kind}]-> b", kinds=(kind,))))
    assert data["runtime"] == [{"from": "a", "to": "b", "kind": "k" * 199 + "…"}]


def test_export_without_runtime_links_has_an_empty_list(tmp_path) -> None:  # AC-10
    assert export(make_repo(tmp_path, model("a -> b", kinds=())))["runtime"] == []
