"""Architecture model records: reading, validation and export (issue #31, A3a)."""

from __future__ import annotations

import json
from pathlib import Path

from arch_delta_support import call, make_repo, require_node, run_tool, error_lines

require_node()

SHOP_IDS = ["shop", "shop.checkout", "shop.orders", "shop.orders.api", "shop.payments", "shop.payments.card"]


def decision(id_: str, **over) -> dict:
    record = {"id": id_, "decision": "Use one store.", "reason": "Simpler.", "rejected": [], "binds": ["shop.orders"],
              "status": "current", "evidence": "spec", "sources": ["docs/x.md"]}
    record.update(over)
    return record


def hole(id_: str, **over) -> dict:
    record = {"id": id_, "what": "No reason recorded.", "binds": [], "evidence": "search"}
    record.update(over)
    return record


def contract(id_: str, **over) -> dict:
    record = {"id": id_, "name": "Orders API", "owner": "shop.orders", "bound": ["shop.checkout"],
              "obligations": ["Every order has an id."], "compatibility": None}
    record.update(over)
    return record


def lists() -> dict:
    return {"added": [], "changed": [], "removed": []}


def change(id_: str = "2026-11-16-baseline", **over) -> dict:
    record = {"id": id_, "date": id_[:10], "run": "baseline", "asked_by": "#1", "summary": "Baseline.", "rejected": [],
              "elements": {"added": ["shop"], "changed": [], "removed": []}, "decisions": lists(), "holes": lists(),
              "contracts": lists(), "gap": {"added": [], "removed": []},
              "check": {"exit": 0, "summary": "0 new, 0 stale, 0 known", "output": "0 new, 0 stale, 0 known\n"},
              "approved": None}
    record.update(over)
    return record


def coverage(**over) -> dict:
    record = {"answer": "Whole repository.", "baselined": [{"prefix": "shop", "run": "2026-11-16-baseline"}],
              "edge_nodes": [], "counts": {"modules": 3, "groups": 2}, "unmapped": []}
    record.update(over)
    return record


def dfile(*decisions: dict, holes: tuple = (), title: str = "Orders") -> dict:
    return {"title": title, "decisions": list(decisions), "holes": list(holes)}


def cfile(*contracts: dict, title: str = "Boundaries") -> dict:
    return {"title": title, "contracts": list(contracts)}


def model_folder(tmp_path: Path, files: dict) -> tuple[Path, Path]:
    """A repo with the shop model and the given record files (dict or raw text), keyed by path in the model folder."""
    repo = make_repo(tmp_path)
    folder = repo / "docs" / "architecture"
    for rel, content in files.items():
        target = folder / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
    return repo, folder


def shape(kind: str, data: object) -> list[str]:
    result = call("records-shape.mjs", "shapeProblems", kind, data)
    assert result["ok"], result
    return [f"{p['field']}: {p['message']}" for p in result["value"]]


def test_valid_files_have_no_shape_problems() -> None:
    assert shape("decisions", dfile(decision("D-1"), decision("D-2", reason=None, note="n"), holes=(hole("H-1"),))) == []
    assert shape("contracts", cfile(contract("C-1", notes=["x"], decisions=["D-1"], capabilities=["Pay"]))) == []
    assert shape("change", change(approved={"by": "owner", "date": "2026-11-16"})) == []
    assert shape("coverage", coverage(edge_nodes=[{"element": "shop", "run": "2026-11-16-baseline"}],
                                      unmapped=[{"module": "shop.x", "reason": "shared prefix"}])) == []


def test_shape_orders_unknown_keys_after_table_fields() -> None:  # AC-8
    data = dfile(decision("D-1", colour="red"), decision("D-2"), holes=(hole("H-1", what=["x"]),))
    del data["decisions"][1]["reason"]
    assert shape("decisions", data) == [
        "decisions[0].colour: unknown field",
        "decisions[1].reason: required",
        "holes[0].what: must be a non-empty string",
    ]


def test_shape_reports_types_minimums_and_nested_paths() -> None:
    assert shape("contracts", cfile(contract("C-1", bound=[], obligations=["ok", ""], compatibility=5))) == [
        "contracts[0].bound: needs at least one item",
        "contracts[0].obligations[1]: must be a non-empty string",
        "contracts[0].compatibility: must be a non-empty string or null",
    ]
    assert shape("change", change(gap={"added": [["a"]], "removed": []}, check={"exit": 1.5, "summary": "s", "output": "o"},
                                  approved=7, extra=1)) == [
        "gap.added[0]: must be a pair of two non-empty strings",
        "check.exit: must be a whole number",
        "approved: must be an object or null",
        "extra: unknown field",
    ]
    assert shape("coverage", coverage(counts={"modules": -1, "groups": 2}, baselined=[{"prefix": "shop"}])) == [
        "baselined[0].run: required",
        "counts.modules: must be a whole number of 0 or more",
    ]


def test_shape_reports_wrong_container_types() -> None:
    assert shape("decisions", {"title": "", "decisions": {}, "holes": [5]}) == [
        "title: must be a non-empty string",
        "decisions: must be a list",
        "holes[0]: must be an object",
    ]
