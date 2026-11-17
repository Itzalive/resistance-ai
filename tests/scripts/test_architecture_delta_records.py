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


def read(folder: Path, ids: list[str] = SHOP_IDS) -> dict:
    return call("records.mjs", "readRecords", str(folder), ids)


def problems(result: dict) -> list[str]:
    assert result["ok"] is False and result["token"] == "record-error", result
    return result["details"]


def test_absent_folders_are_empty(tmp_path) -> None:  # AC-1
    _, folder = model_folder(tmp_path, {})
    assert read(folder) == {"ok": True, "value": {"groups": [], "decisions": [], "holes": [], "contracts": [],
                                                   "changes": [], "coverage": None}}


def test_valid_records_are_returned_with_their_group(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions/orders.json": dfile(decision("D-1"), holes=(hole("H-1"),)),
                                        "contracts/app.json": cfile(contract("C-1")),
                                        "changes/2026-11-16-baseline.json": change(), "coverage.json": coverage()})
    value = read(folder)["value"]
    assert value["groups"] == [{"kind": "contracts", "group": "app", "title": "Boundaries"},
                               {"kind": "decisions", "group": "orders", "title": "Orders"}]
    assert value["decisions"] == [{**decision("D-1"), "group": "orders"}]
    assert value["holes"] == [{**hole("H-1"), "group": "orders"}]
    assert value["contracts"] == [{**contract("C-1"), "group": "app"}]
    assert value["changes"] == [change()] and value["coverage"] == coverage()


def test_misnamed_file_is_reported_once_and_not_read(tmp_path) -> None:  # AC-10, AC-17
    _, folder = model_folder(tmp_path, {"decisions/Memory.json": "{not json", "decisions/.gitkeep": "",
                                        "contracts/old/x.json": cfile(contract("C-1")),
                                        "changes/2026-11-16.json": change()})
    assert problems(read(folder)) == [
        "changes/2026-11-16.json: -: not a valid file name here",
        "contracts/old: -: folders are not allowed here",
        "decisions/Memory.json: -: not a valid file name here",
    ]


def test_record_folder_that_is_a_file_and_coverage_that_is_a_folder(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions": "x", "coverage.json/x.json": "{}"})
    assert problems(read(folder)) == ["coverage.json: -: must be a file", "decisions: -: must be a folder"]


def test_bad_json_is_reported_once_and_others_still_checked(tmp_path) -> None:  # AC-14
    _, folder = model_folder(tmp_path, {"decisions/a.json": "{oops", "decisions/b.json": dfile(decision("D-1", colour="x")),
                                        "contracts/c.json": "[1]"})
    assert problems(read(folder)) == [
        "contracts/c.json: -: must be a JSON object",
        "decisions/a.json: -: not valid JSON",
        "decisions/b.json: decisions[0].colour: unknown field",
    ]


def test_problems_are_listed_by_path(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions/zeta.json": dfile(decision("D-1", status=5)),
                                        "decisions/alpha.json": dfile(decision("D-2", evidence=[]))})
    assert problems(read(folder)) == ["decisions/alpha.json: decisions[0].evidence: must be a string",
                                      "decisions/zeta.json: decisions[0].status: must be a string"]


def test_binds_naming_no_element(tmp_path) -> None:  # AC-3
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-1", binds=["shop.orders", "shop.nope"]))})
    assert problems(read(folder)) == ["decisions/a.json: decisions[0].binds[1]: shop.nope is not a model element"]


def test_contract_owner_and_bound_problems_in_one_run(tmp_path) -> None:  # AC-4
    _, folder = model_folder(tmp_path, {"contracts/a.json": cfile(contract("C-1", owner="ghost"), contract("C-2", bound=[]))})
    assert problems(read(folder)) == ["contracts/a.json: contracts[1].bound: needs at least one item",
                                      "contracts/a.json: contracts[0].owner: ghost is not a model element"]


def test_duplicate_id_across_files(tmp_path) -> None:  # AC-5
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("X-1")), "contracts/b.json": cfile(contract("X-1"))})
    assert problems(read(folder)) == ["decisions/a.json: decisions[0].id: duplicate id X-1, first in contracts/b.json"]


def test_order_problem_is_at_the_first_record_out_of_order(tmp_path) -> None:  # AC-6
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-2"), decision("D-1"), decision("D-3"))})
    assert problems(read(folder)) == ["decisions/a.json: decisions[1].id: not sorted by id: D-1 comes after D-2"]


def test_supersession_rules(tmp_path) -> None:  # AC-7
    files = {"decisions/a.json": dfile(decision("D-1", status="superseded"), decision("D-2", superseded_by="D-1"),
                                       decision("D-3", status="superseded", superseded_by="D-9"), holes=(hole("H-1"),)),
             "contracts/b.json": cfile(contract("C-1", decisions=["H-1"]))}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == [
        "contracts/b.json: contracts[0].decisions[0]: H-1 names no decision",
        "decisions/a.json: decisions[2].superseded_by: D-9 names no decision",
        "decisions/a.json: decisions[0].superseded_by: required when status is superseded",
        "decisions/a.json: decisions[1].superseded_by: only allowed when status is superseded",
    ]


def test_values_outside_their_lists(tmp_path) -> None:  # AC-9, AC-10
    files = {"decisions/a.json": dfile(decision("D-1", status="done", evidence="memory")),
             "changes/2026-02-30-x.json": change("2026-02-30-x", run="nightly", check={"exit": 2, "summary": "s", "output": "o"}),
             "changes/2026-11-16-y.json": change("2026-11-16-y", date="2026-11-15")}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == [
        "changes/2026-02-30-x.json: date: not a real date",
        "changes/2026-02-30-x.json: run: must be one of baseline, epic, later-stage",
        "changes/2026-02-30-x.json: check.exit: must be 0 or 1",
        "changes/2026-11-16-y.json: date: must be the start of the file name",
        "decisions/a.json: decisions[0].status: must be one of current, partly-built, planned, superseded",
        "decisions/a.json: decisions[0].evidence: must be one of checked, code, spec",
    ]


def test_change_history_is_not_looked_up(tmp_path) -> None:  # AC-11
    _, folder = model_folder(tmp_path, {"changes/2026-11-16-baseline.json": change(
        elements={"added": [], "changed": [], "removed": ["gone.element"]}, gap={"added": [["gone.a", "gone.b"]], "removed": []})})
    assert read(folder)["ok"] is True


def test_coverage_links(tmp_path) -> None:  # AC-15
    _, folder = model_folder(tmp_path, {"coverage.json": coverage(edge_nodes=[{"element": "ghost", "run": "2026-11-16-baseline"}])})
    assert problems(read(folder)) == ["coverage.json: baselined[0].run: 2026-11-16-baseline names no change file",
                                      "coverage.json: edge_nodes[0].element: ghost is not a model element",
                                      "coverage.json: edge_nodes[0].run: 2026-11-16-baseline names no change file"]


def test_self_supersession_and_duplicates_but_not_cycles(tmp_path) -> None:  # AC-16
    files = {"decisions/a.json": dfile(decision("D-1", status="superseded", superseded_by="D-1"),
                                       decision("D-2", binds=["shop", "shop"]),
                                       decision("D-3", status="superseded", superseded_by="D-4"),
                                       decision("D-4", status="superseded", superseded_by="D-3"))}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["decisions/a.json: decisions[0].superseded_by: names its own id",
                                      "decisions/a.json: decisions[1].binds[1]: shop is listed twice"]


def test_misnamed_file_does_not_create_a_duplicate(tmp_path) -> None:  # AC-17
    _, folder = model_folder(tmp_path, {"decisions/Memory.json": dfile(decision("M-1")), "decisions/orders.json": dfile(decision("M-1")),
                                        "decisions/.gitkeep": ""})
    assert problems(read(folder)) == ["decisions/Memory.json: -: not a valid file name here"]


def test_references_are_not_ids(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("D-1"), decision("D-2", status="superseded", superseded_by="D-1")),
             "contracts/b.json": cfile(contract("C-1", decisions=["D-1"])),
             "changes/2026-11-16-baseline.json": change(decisions={"added": ["D-1", "D-2"], "changed": [], "removed": []})}
    _, folder = model_folder(tmp_path, files)
    assert read(folder)["ok"] is True


def test_record_id_forms_and_change_id(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("_bad"), decision("D-1", binds=[""])),
             "changes/2026-11-16-baseline.json": change(id_="2026-11-16-other", date="2026-11-16")}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["changes/2026-11-16-baseline.json: id: must equal the file name 2026-11-16-baseline",
                                      "decisions/a.json: decisions[0].id: not a valid record id",
                                      "decisions/a.json: decisions[1].binds[0]: must not be empty"]


def test_ids_that_are_object_property_names(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("toString"), decision("valueOf", status="superseded", superseded_by="constructor"))}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["decisions/a.json: decisions[1].superseded_by: constructor names no decision"]


def test_wrong_typed_values_are_not_checked_again(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("D-1", status=5, superseded_by=7, binds=["shop", 3])),
             "changes/2026-11-16-baseline.json": change(date=20261116, check={"exit": "0", "summary": "s", "output": "o"})}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == [
        "changes/2026-11-16-baseline.json: date: must be a string",
        "changes/2026-11-16-baseline.json: check.exit: must be a whole number",
        "decisions/a.json: decisions[0].binds[1]: must be a string",
        "decisions/a.json: decisions[0].status: must be a string",
        "decisions/a.json: decisions[0].superseded_by: must be a string",
    ]


def test_underscored_element_ids_are_accepted(tmp_path) -> None:
    model = "model {\n  my_part = component 'P'\n}\n"
    repo = make_repo(tmp_path, model)
    folder = repo / "docs" / "architecture"
    (folder / "decisions").mkdir()
    (folder / "decisions" / "a.json").write_text(json.dumps(dfile(decision("D-1", binds=["my_part"]))), encoding="utf-8")
    assert read(folder, ["my_part"])["ok"] is True


BAD = {"decisions/a.json": dfile(decision("D-1", binds=["shop.nope"]))}
BAD_LINE = "error: record-error: decisions/a.json: decisions[0].binds[0]: shop.nope is not a model element"


def test_export_and_check_report_record_errors(tmp_path) -> None:  # AC-3
    repo, _ = model_folder(tmp_path, BAD)
    deps = repo / "deps.json"
    deps.write_text(json.dumps({"edges": []}), encoding="utf-8")
    for args in (("export", "--repo", repo), ("check", "--repo", repo, "--deps", deps)):
        proc = run_tool(*args)
        assert proc.returncode == 2 and proc.stdout == ""
        assert error_lines(proc) == [BAD_LINE]


def test_check_exits_2_on_bad_records_even_when_clean(tmp_path) -> None:  # AC-13
    repo, _ = model_folder(tmp_path, BAD)
    deps = repo / "deps.json"
    deps.write_text(json.dumps({"edges": [["shop.orders.x", "shop.checkout.y"]]}), encoding="utf-8")
    assert run_tool("check", "--repo", repo, "--deps", deps).returncode == 2


def test_record_error_lines_are_cleaned(tmp_path) -> None:
    repo, _ = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-1", binds=["\u001b[31mx" + "y" * 300]))})
    line = error_lines(run_tool("export", "--repo", repo))[0]
    assert "\u001b" not in line and line.endswith("…")


def test_export_reports_shape_and_link_problems_in_order(tmp_path) -> None:  # AC-4, AC-8 through export
    files = {"contracts/a.json": cfile(contract("C-1", owner="ghost"), contract("C-2", bound=[])),
             "decisions/b.json": dfile(decision("D-1", colour="x"))}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: contracts/a.json: contracts[1].bound: needs at least one item",
        "error: record-error: contracts/a.json: contracts[0].owner: ghost is not a model element",
        "error: record-error: decisions/b.json: decisions[0].colour: unknown field",
    ]


def test_record_errors_come_before_other_inputs(tmp_path) -> None:  # AC-18
    repo, _ = model_folder(tmp_path, BAD)
    proc = run_tool("check", "--repo", repo, "--deps", repo / "missing.json")
    assert proc.returncode == 2
    assert error_lines(proc) == [BAD_LINE]


def export(repo: Path) -> dict:
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_export_without_records(tmp_path) -> None:  # AC-1
    data = export(model_folder(tmp_path, {})[0])
    assert data["format"] == 3
    assert [data[k] for k in ("groups", "decisions", "holes", "contracts", "changes")] == [[], [], [], [], []]
    assert data["coverage"] is None


def test_export_prints_records_sorted_with_group_last(tmp_path) -> None:  # AC-2
    files = {"decisions/orders.json": dfile(decision("D-1", note="n"), holes=(hole("H-1"),)),
             "decisions/app.json": dfile(decision("D-3"), holes=(hole("H-2"),), title="App"),
             "contracts/app.json": cfile(contract("C-2")), "contracts/zeta.json": cfile(contract("C-1"), title="Zeta"),
             "contracts/app-and-server.json": cfile(contract("C-3"), title="App and server"),
             "changes/2026-11-16-baseline.json": change(), "coverage.json": coverage()}
    data = export(model_folder(tmp_path, files)[0])
    assert data["groups"] == [{"kind": "contracts", "group": "app", "title": "Boundaries"},
                              {"kind": "contracts", "group": "app-and-server", "title": "App and server"},
                              {"kind": "contracts", "group": "zeta", "title": "Zeta"},
                              {"kind": "decisions", "group": "app", "title": "App"},
                              {"kind": "decisions", "group": "orders", "title": "Orders"}]
    assert [(d["id"], d["group"]) for d in data["decisions"]] == [("D-1", "orders"), ("D-3", "app")]
    assert list(data["decisions"][0]) == [*decision("D-1", note="n"), "group"]
    assert "note" not in data["decisions"][1]
    assert [(h["id"], h["group"]) for h in data["holes"]] == [("H-1", "orders"), ("H-2", "app")]
    assert [(c["id"], c["group"]) for c in data["contracts"]] == [("C-1", "zeta"), ("C-2", "app"), ("C-3", "app-and-server")]
    assert data["contracts"][0] == {**contract("C-1"), "group": "zeta"}
    assert data["changes"] == [change()] and data["coverage"] == coverage()


def test_record_ids_are_cut_like_other_ids(tmp_path) -> None:
    long_id = "D-" + "1" * 250
    data = export(model_folder(tmp_path, {"decisions/a.json": dfile(decision(long_id))})[0])
    assert data["decisions"][0]["id"] == long_id[:199] + "…"


def test_record_text_is_cleaned_without_a_cut(tmp_path) -> None:  # AC-12
    reason = "r" * 250 + "\u001b[31m" + "\n" + "s" * 250
    data = export(model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-1", reason=reason))})[0])
    assert data["decisions"][0]["reason"] == "r" * 250 + "\n" + "s" * 250


def test_malformed_references_get_only_the_form_line(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("D-1", status="superseded", superseded_by="_bad")),
             "contracts/b.json": cfile(contract("C-1", decisions=["_bad"]))}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["contracts/b.json: contracts[0].decisions[0]: not a valid record id",
                                      "decisions/a.json: decisions[0].superseded_by: not a valid record id"]


def test_bad_id_record_skips_links_but_not_values(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("_bad", binds=["ghost"], status="nope"))})
    assert problems(read(folder)) == [
        "decisions/a.json: decisions[0].id: not a valid record id",
        "decisions/a.json: decisions[0].status: must be one of current, partly-built, planned, superseded",
    ]


def test_change_lists_are_checked_for_form(tmp_path) -> None:
    files = {"changes/2026-11-16-baseline.json": change(elements={"added": [], "changed": [], "removed": [""]},
                                                        decisions={"added": ["_bad"], "changed": [], "removed": []})}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["changes/2026-11-16-baseline.json: elements.removed[0]: must not be empty",
                                      "changes/2026-11-16-baseline.json: decisions.added[0]: not a valid record id"]


def test_approval_date_and_double_date_problems(tmp_path) -> None:
    files = {"changes/2026-11-16-a.json": change("2026-11-16-a", date="2026-02-30"),
             "changes/2026-11-16-b.json": change("2026-11-16-b", approved={"by": "owner", "date": "2026-13-01"})}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["changes/2026-11-16-a.json: date: not a real date",
                                      "changes/2026-11-16-a.json: date: must be the start of the file name",
                                      "changes/2026-11-16-b.json: approved.date: not a real date"]


def test_deadline_is_checked_after_each_record_file(tmp_path) -> None:
    from arch_delta_support import lib_url, run_module
    files = {"decisions/a.json": dfile(decision("D-1")), "decisions/b.json": dfile(decision("D-2")),
             "changes/2026-11-16-baseline.json": change()}
    _, folder = model_folder(tmp_path, files)
    code = (f"import {{ readRecords }} from {json.dumps(lib_url('records.mjs'))};\n"
            "let ticks = 0;\n"
            f"readRecords({json.dumps(str(folder))}, {json.dumps(SHOP_IDS)}, () => {{ ticks += 1; }});\n"
            "process.stdout.write(String(ticks));\n")
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "3"


def test_only_the_first_out_of_order_record_is_reported(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-2"), decision("D-1"), decision("D-4"), decision("D-3"))})
    assert problems(read(folder)) == ["decisions/a.json: decisions[1].id: not sorted by id: D-1 comes after D-2"]


def test_coverage_run_naming_an_unreadable_change_file_is_not_a_link_problem(tmp_path) -> None:
    _, folder = model_folder(tmp_path, {"changes/2026-11-16-baseline.json": "{oops", "coverage.json": coverage()})
    assert problems(read(folder)) == ["changes/2026-11-16-baseline.json: -: not valid JSON"]


def test_gap_pairs_are_cut_like_other_ids(tmp_path) -> None:
    files = {"changes/2026-11-16-baseline.json": change(gap={"added": [["g" * 250, "x"]], "removed": []})}
    data = export(model_folder(tmp_path, files)[0])
    assert data["changes"][0]["gap"]["added"][0] == ["g" * 199 + "…", "x"]


def test_decisions_carry_obligations(tmp_path) -> None:  # AC-19
    cross = decision("D-1", owner="shop.orders", obligations=["Every order has an id."], compatibility="Additive only.",
                     capabilities=["Pay"])
    principle = decision("P-1", binds=[], obligations=["Data stays in the EU."])
    data = export(model_folder(tmp_path, {"decisions/a.json": dfile(cross, principle)})[0])
    assert data["decisions"] == [{**cross, "group": "a"}, {**principle, "group": "a"}]


def test_decision_owner_problems(tmp_path) -> None:  # AC-21
    files = {"decisions/a.json": dfile(decision("D-1", owner="ghost", obligations=["x"]),
                                       decision("D-2", owner="", obligations=["x"]),
                                       decision("D-3", owner="shop", obligations=[]))}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: decisions/a.json: decisions[2].obligations: needs at least one item",
        "error: record-error: decisions/a.json: decisions[1].owner: must not be empty",
        "error: record-error: decisions/a.json: decisions[0].owner: ghost is not a model element",
    ]


def test_decision_compatibility_and_capabilities_are_text() -> None:
    assert shape("decisions", dfile(decision("D-1", compatibility=None, capabilities=[""]))) == [
        "decisions[0].compatibility: must be a non-empty string",
        "decisions[0].capabilities[0]: must be a non-empty string",
    ]


def test_decision_owner_comes_after_superseded_by_in_pass_3(tmp_path) -> None:
    files = {"decisions/a.json": dfile(decision("D-1", status="superseded", superseded_by="_x", owner="", obligations=["o"]))}
    _, folder = model_folder(tmp_path, files)
    assert problems(read(folder)) == ["decisions/a.json: decisions[0].superseded_by: not a valid record id",
                                      "decisions/a.json: decisions[0].owner: must not be empty"]


def test_owner_needs_obligations_after_evidence(tmp_path) -> None:  # AC-20
    repo, _ = model_folder(tmp_path, {"decisions/a.json": dfile(decision("D-1", evidence="memory", owner="shop.orders"))})
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: decisions/a.json: decisions[0].evidence: must be one of checked, code, spec",
        "error: record-error: decisions/a.json: decisions[0].obligations: required when owner is set",
    ]


def test_obligations_rule_and_wrong_types(tmp_path) -> None:  # AC-22
    files = {"decisions/a.json": dfile(decision("D-1", owner=5), decision("D-2", owner="shop", obligations="x"),
                                       decision("D-3", compatibility="Additive only."))}
    repo, _ = model_folder(tmp_path, files)
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: record-error: decisions/a.json: decisions[0].owner: must be a string",
        "error: record-error: decisions/a.json: decisions[1].obligations: must be a list",
    ]
