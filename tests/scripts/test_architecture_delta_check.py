from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_delta_support import (
    copy_engine, error_lines, link_dir, make_repo, make_shim, require_node, run_tool, unique, write_json,
)

require_node()

CLEAN_EDGES = [["shop.orders.api.handler", "shop.checkout.service"], ["shop.checkout.service", "shop.payments.card.charge"]]
BREACH = ["shop.orders.api.x", "shop.payments.card.y"]


def check(repo: Path, edges: list[list[str]], *extra: str, script: Path | None = None):
    deps = write_json(repo / "deps.json", {"edges": edges})
    kwargs = {"script": script} if script else {}
    return run_tool("check", "--repo", repo, "--deps", deps, *extra, **kwargs)


def report(proc) -> dict:
    assert proc.returncode in (0, 1), proc.stderr
    return json.loads(proc.stdout)


def gap(repo: Path, *entries: tuple[str, str]) -> Path:
    return write_json(repo / "architecture" / "known-gap.json",
                      {"entries": [{"from": a, "to": b, "reason": "r"} for a, b in entries]})


def test_clean_repo_exits_zero_from_the_plugin_copy(tmp_path) -> None:
    proc = check(make_repo(tmp_path), CLEAN_EDGES, "--format", "json")
    assert proc.returncode == 0, proc.stderr
    data = report(proc)
    assert data["likec4"] == {"version": "1.60.0", "source": "plugin"}
    assert data["breaches"] == [] and data["not_yet_reached"] == [] and data["unmapped"] == []


def test_repo_copy_wins_with_a_note(tmp_path) -> None:
    repo = make_repo(tmp_path)
    make_shim(repo / "node_modules", version="1.59.0")
    proc = check(repo, [BREACH], "--format", "json")
    assert proc.returncode == 1
    assert report(proc)["likec4"] == {"version": "1.59.0", "source": "repo"}
    assert "note: likec4 1.59.0 from repo; tested with 1.60.0" in proc.stderr.splitlines()


def test_parent_folder_copies_are_not_used(tmp_path) -> None:
    outer_repo = tmp_path / unique("a")
    make_shim(outer_repo / "node_modules")
    repo = make_repo(outer_repo)
    outer_engine = tmp_path / unique("b")
    make_shim(outer_engine / "node_modules")
    script = copy_engine(outer_engine)
    proc = check(repo, CLEAN_EDGES, script=script)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: likec4-missing: ")
    assert "npm" in error_lines(proc)[0]


def test_bad_shape_shim_exits_internal(tmp_path) -> None:
    for element in ("{ kind: 'component', tags: [], getMetadata() { return {}; } }",
                    "{ id: 'a', kind: 'component', tags: [], getMetadata() { return { code: ['a'] }; } }"):
        repo = make_repo(tmp_path)
        source = ("export class LikeC4 { static async fromWorkspace() { return { getErrors() { return []; },"
                  " async computedModel() { return { elements() { return [" + element + "]; },"
                  " relationships() { return []; } }; } }; } }\n")
        make_shim(repo / "node_modules", source=source)
        proc = check(repo, CLEAN_EDGES)
        assert proc.returncode == 2
        assert error_lines(proc)[0].startswith("error: internal: ")


def test_model_errors_end_to_end(tmp_path) -> None:
    repo = make_repo(tmp_path, "model {\n  a = component 'A'\n  a -> missing\n  b = nosuchkind 'B'\n}\n")
    proc = check(repo, [])
    assert proc.returncode == 2
    assert proc.stdout == ""
    lines = error_lines(proc)
    assert len(lines) >= 2
    assert all(line.startswith("error: model-error: model.c4:") for line in lines)
    assert any(":3:" in line for line in lines) and any(":4:" in line for line in lines)


@pytest.mark.parametrize(
    ("setup", "token"),
    [
        pytest.param("deps-unknown-key", "bad-input", id="deps-unknown-key"),
        pytest.param("gap-empty-reason", "bad-input", id="gap-empty-reason"),
        pytest.param("shards-wrong-type", "bad-input", id="shards-wrong-type"),
        pytest.param("missing-deps", "bad-input", id="missing-deps"),
        pytest.param("deps-outside", "outside-repo", id="deps-outside"),
        pytest.param("unknown-scope", "unknown-scope", id="unknown-scope"),
    ],
)
def test_input_errors_end_to_end(tmp_path, setup: str, token: str) -> None:
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": []})
    args = ["check", "--repo", repo, "--deps", deps]
    if setup == "deps-unknown-key":
        write_json(deps, {"edges": [], "x": 1})
    elif setup == "gap-empty-reason":
        write_json(repo / "architecture" / "known-gap.json", {"entries": [{"from": "shop", "to": "shop.orders", "reason": ""}]})
    elif setup == "shards-wrong-type":
        args += ["--shards", write_json(repo / "shards.json", {"shards": []})]
    elif setup == "missing-deps":
        args[4] = repo / "nope.json"
    elif setup == "deps-outside":
        args[4] = write_json(tmp_path / unique("out") / "deps.json", {"edges": []})
    elif setup == "unknown-scope":
        args += ["--scope", "shop.nope"]
    proc = run_tool(*args)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith(f"error: {token}: ")


def test_deps_through_a_link_outside_is_refused(tmp_path) -> None:
    outside = tmp_path / unique("outside")
    write_json(outside / "deps.json", {"edges": []})
    repo = make_repo(tmp_path)
    link_dir(outside, repo / "linked")
    proc = run_tool("check", "--repo", repo, "--deps", "linked/deps.json")
    assert error_lines(proc)[0].startswith("error: outside-repo: ")


def test_known_new_and_stale(tmp_path) -> None:
    known = make_repo(tmp_path)
    gap(known, ("shop.orders.api", "shop.payments.card"))
    assert check(known, [BREACH]).returncode == 0
    new = make_repo(tmp_path)
    assert check(new, [BREACH]).returncode == 1
    stale = make_repo(tmp_path)
    gap(stale, ("shop.orders", "shop.payments"))
    proc = check(stale, CLEAN_EDGES, "--format", "json")
    assert proc.returncode == 1
    assert report(proc)["gap"]["stale"] == [{"from": "shop.orders", "to": "shop.payments"}]


def test_scope_end_to_end(tmp_path) -> None:
    repo = make_repo(tmp_path)
    proc = check(repo, [BREACH], "--scope", "shop.checkout", "--format", "json")
    assert proc.returncode == 0
    assert report(proc)["breaches"] == []


def test_gap_file_is_untouched(tmp_path) -> None:
    repo = make_repo(tmp_path)
    file = gap(repo, ("shop.orders.api", "shop.payments.card"))
    before = file.read_bytes()
    check(repo, [BREACH, ["shop.checkout.a", "shop.orders.api.b"]])
    assert file.read_bytes() == before


def test_json_report_shape_and_edge_sample(tmp_path) -> None:
    edges = [[f"shop.orders.api.m{i:02d}", "shop.payments.card.n"] for i in range(25)]
    data = report(check(make_repo(tmp_path), edges, "--format", "json"))
    assert list(data) == ["likec4", "breaches", "not_yet_reached", "unmapped", "hot_spots", "gap"]
    breach = data["breaches"][0]
    assert (breach["from"], breach["to"], breach["gap"]) == ("shop.orders.api", "shop.payments.card", "new")
    assert breach["edges"] == [[f"shop.orders.api.m{i:02d}", "shop.payments.card.n"] for i in range(20)]
    assert breach["more_edges"] == 5
    assert list(data["gap"]) == ["known", "new", "stale"]


def test_hot_spots_end_to_end(tmp_path) -> None:
    repo = make_repo(tmp_path)
    shards = write_json(repo / "shards.json", {"shards": {"b": ["shop.payments"], "a": ["shop.payments.card"]}})
    data = report(check(repo, CLEAN_EDGES, "--shards", shards, "--format", "json"))
    assert data["hot_spots"] == [{"element": "shop.payments.card", "shards": ["a", "b"]}]


def test_printed_strings_are_cleaned(tmp_path) -> None:
    long_name = "q" * 250
    edges = [["zz\x1b[31m.evil\u202e", "shop.orders"], [long_name, "shop.orders"]]
    data = report(check(make_repo(tmp_path), edges, "--format", "json"))
    assert sorted(data["unmapped"]) == sorted(["zz.evil", "q" * 199 + "…"])


def test_text_report_headings_and_summary(tmp_path) -> None:
    repo = make_repo(tmp_path)
    gap(repo, ("shop.checkout", "shop.orders.api"), ("shop.orders", "shop.payments"))
    proc = check(repo, [BREACH, ["shop.checkout.s", "shop.orders.api.t"]])
    assert proc.returncode == 1
    lines = proc.stdout.splitlines()
    headings = [line for line in lines if line in {"New breaches", "Stale gap entries", "Known breaches"}]
    assert headings == ["New breaches", "Stale gap entries", "Known breaches"]
    assert lines[-1].startswith("1 new, 1 stale, 1 known (likec4 ")
    assert lines[-1] == "1 new, 1 stale, 1 known (likec4 1.60.0 from plugin)"
