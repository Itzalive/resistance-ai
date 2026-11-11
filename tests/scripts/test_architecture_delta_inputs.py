from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_delta_support import call, lib_url, link_dir, require_node, run_module, unique, write_json

require_node()

MB = 1024 * 1024
IDS = ["shop", "shop.orders", "shop.payments"]


def test_inside_path_resolves(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    write_json(repo / "deps.json", {"edges": []})
    real = call("paths.mjs", "realRepo", str(repo))["value"]
    result = call("paths.mjs", "resolveInside", real, "deps.json", "--deps")
    assert result["value"]["exists"] is True
    assert Path(result["value"]["path"]).name == "deps.json"


def test_missing_inside_path_reports_not_existing(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    result = call("paths.mjs", "resolveInside", str(repo), "nope.json", "--gap")
    assert result["value"]["exists"] is False


def test_lexical_escape_is_refused(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    write_json(tmp_path / "outside.json", {"edges": []})
    assert call("paths.mjs", "resolveInside", str(repo), "../outside.json", "--deps")["token"] == "outside-repo"


def test_path_through_a_link_outside_is_refused(tmp_path) -> None:
    outside = tmp_path / unique("outside")
    write_json(outside / "deps.json", {"edges": []})
    repo = tmp_path / unique("repo")
    link_dir(outside, repo / "linked")
    real = call("paths.mjs", "realRepo", str(repo))["value"]
    assert call("paths.mjs", "resolveInside", real, "linked/deps.json", "--deps")["token"] == "outside-repo"


def test_repo_must_be_a_directory(tmp_path) -> None:
    assert call("paths.mjs", "realRepo", str(tmp_path / "missing"))["token"] == "bad-input"
    file = write_json(tmp_path / unique("f"), {})
    assert call("paths.mjs", "realRepo", str(file))["token"] == "bad-input"


def read_and(fn: str, file: Path, *extra: object) -> dict:
    code = (
        f"import {{ readJson, {fn} }} from {json.dumps(lib_url('inputs.mjs'))};\n"
        "try {\n"
        f"  const out = {fn}(readJson({json.dumps(str(file))}, '--x'), ...{json.dumps(list(extra))});\n"
        "  process.stdout.write(JSON.stringify({ ok: true, value: out }));\n"
        "} catch (err) {\n"
        "  process.stdout.write(JSON.stringify({ ok: false, token: err.token ?? null, details: err.details ?? null }));\n"
        "}\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_deps_are_deduplicated_and_empty_is_valid(tmp_path) -> None:
    file = write_json(tmp_path / unique("d"), {"edges": [["a", "b"], ["a", "b"], ["b", "c"]]})
    assert read_and("parseDeps", file)["value"] == [["a", "b"], ["b", "c"]]
    empty = write_json(tmp_path / unique("d"), {"edges": []})
    assert read_and("parseDeps", empty)["value"] == []


@pytest.mark.parametrize(
    "data",
    [
        pytest.param([], id="not-object"),
        pytest.param({}, id="no-edges"),
        pytest.param({"edges": [], "extra": 1}, id="unknown-key"),
        pytest.param({"edges": {}}, id="edges-not-list"),
        pytest.param({"edges": [["a"]]}, id="one-item"),
        pytest.param({"edges": [["a", "b", "c"]]}, id="three-items"),
        pytest.param({"edges": [["a", ""]]}, id="empty-string"),
        pytest.param({"edges": [["a", 1]]}, id="non-string"),
    ],
)
def test_deps_shape_errors(tmp_path, data: object) -> None:
    assert read_and("parseDeps", write_json(tmp_path / unique("d"), data))["token"] == "bad-input"


def test_invalid_json_is_bad_input(tmp_path) -> None:
    file = tmp_path / unique("d")
    file.write_text("{not json", encoding="utf-8")
    assert read_and("parseDeps", file)["token"] == "bad-input"


@pytest.mark.parametrize(("count", "ok"), [pytest.param(1_000_000, True, id="1000000-ok"), pytest.param(1_000_001, False, id="1000001-refused")])
def test_edge_cap(tmp_path, count: int, ok: bool) -> None:
    file = tmp_path / unique("d")
    file.write_text('{"edges":[' + ",".join(['["a","b"]'] * count) + "]}", encoding="utf-8")
    result = read_and("parseDeps", file)
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "edge-cap"


@pytest.mark.parametrize(("pad", "ok"), [pytest.param(0, True, id="50mb-ok"), pytest.param(1, False, id="over-50mb-refused")])
def test_file_size_limit(tmp_path, pad: int, ok: bool) -> None:
    body = '{"edges":[]}'
    file = tmp_path / unique("d")
    file.write_text(body + " " * (50 * MB - len(body) + pad), encoding="utf-8")
    result = read_and("parseDeps", file)
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "file-size"


def test_gap_entries_parse(tmp_path) -> None:
    data = {"entries": [
        {"from": "shop.orders", "to": "shop.payments", "reason": "r"},
        {"from": "shop", "to": "shop.orders", "reason": "r", "close_by": "feature-2"},
    ]}
    assert read_and("parseGap", write_json(tmp_path / unique("g"), data), IDS)["value"] == [
        {"from": "shop.orders", "to": "shop.payments", "reason": "r", "close_by": None},
        {"from": "shop", "to": "shop.orders", "reason": "r", "close_by": "feature-2"},
    ]


@pytest.mark.parametrize(
    "data",
    [
        pytest.param({}, id="no-entries"),
        pytest.param({"entries": [], "x": 1}, id="unknown-top-key"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders"}]}, id="missing-reason"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": ""}]}, id="empty-reason"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": "r", "why": 1}]}, id="unknown-key"),
        pytest.param({"entries": [{"from": "shop", "to": "nope", "reason": "r"}]}, id="unknown-id"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": "r"}] * 2}, id="duplicate"),
        pytest.param({"entries": [{"from": "shop", "to": "shop.orders", "reason": "r", "close_by": 2}]}, id="close-by-not-string"),
    ],
)
def test_gap_shape_errors(tmp_path, data: object) -> None:
    assert read_and("parseGap", write_json(tmp_path / unique("g"), data), IDS)["token"] == "bad-input"


def test_shards_parse_and_empty_list_is_valid(tmp_path) -> None:
    data = {"shards": {"one": ["shop.orders"], "two": []}}
    assert read_and("parseShards", write_json(tmp_path / unique("s"), data), IDS)["value"] == {
        "one": ["shop.orders"], "two": [],
    }


@pytest.mark.parametrize(
    "data",
    [
        pytest.param({}, id="no-shards"),
        pytest.param({"shards": {}, "x": 1}, id="unknown-key"),
        pytest.param({"shards": {"one": "shop"}}, id="not-list"),
        pytest.param({"shards": {"one": ["nope"]}}, id="unknown-id"),
        pytest.param({"shards": []}, id="shards-not-object"),
    ],
)
def test_shards_shape_errors(tmp_path, data: object) -> None:
    assert read_and("parseShards", write_json(tmp_path / unique("s"), data), IDS)["token"] == "bad-input"


def test_missing_path_outside_is_refused(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    assert call("paths.mjs", "resolveInside", str(repo), "../missing.json", "--gap")["token"] == "outside-repo"


def test_repo_reached_through_a_link_is_resolved(tmp_path) -> None:
    real = tmp_path / unique("real")
    write_json(real / "deps.json", {"edges": []})
    link = tmp_path / unique("link")
    link_dir(real, link)
    root = call("paths.mjs", "realRepo", str(link))["value"]
    assert call("paths.mjs", "resolveInside", root, "deps.json", "--deps")["value"]["exists"] is True


def test_dedupe_keeps_edges_whose_joined_names_collide(tmp_path) -> None:
    file = write_json(tmp_path / unique("d"), {"edges": [["ab", "c"], ["a", "bc"]]})
    assert read_and("parseDeps", file)["value"] == [["ab", "c"], ["a", "bc"]]


def test_shard_value_must_be_a_list(tmp_path) -> None:
    for value in ("", 1):
        file = write_json(tmp_path / unique("s"), {"shards": {"one": value}})
        assert read_and("parseShards", file, IDS)["token"] == "bad-input"


def test_null_gap_entry_is_bad_input(tmp_path) -> None:
    file = write_json(tmp_path / unique("g"), {"entries": [None]})
    assert read_and("parseGap", file, IDS)["token"] == "bad-input"
