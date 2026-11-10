from __future__ import annotations

import json
import shutil

import pytest

from arch_delta_support import (
    SHIPPED_SPEC, SHOP_MODEL, copy_engine, error_lines, link_dir, make_repo, make_shim, require_node, run_tool, unique,
)

require_node()


def test_export_is_stable_and_sorted(tmp_path) -> None:
    repo = make_repo(tmp_path)
    first = run_tool("export", "--repo", repo)
    second = run_tool("export", "--repo", repo)
    assert first.returncode == 0, first.stderr
    assert first.stdout == second.stdout
    data = json.loads(first.stdout)
    assert list(data) == ["format", "elements", "allowed"]
    assert data["format"] == 1
    assert [e["id"] for e in data["elements"]] == [
        "shop", "shop.checkout", "shop.orders", "shop.orders.api", "shop.payments", "shop.payments.card",
    ]
    assert data["elements"][4] == {
        "id": "shop.payments", "kind": "container", "tags": ["protected"], "code": ["shop.payments"], "rules": [],
    }
    assert data["allowed"] == [
        {"from": "shop.checkout", "to": "shop.payments"}, {"from": "shop.orders", "to": "shop.checkout"},
    ]


def test_export_merges_duplicate_relationships(tmp_path) -> None:
    model = "model {\n  a = component 'A'\n  b = component 'B'\n  a -> b\n  a -[uses]-> b 'again'\n}\n"
    data = json.loads(run_tool("export", "--repo", make_repo(tmp_path, model)).stdout)
    assert data["allowed"] == [{"from": "a", "to": "b"}]


def test_export_of_a_spec_only_folder_is_empty(tmp_path) -> None:
    proc = run_tool("export", "--repo", make_repo(tmp_path, None))
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"format": 1, "elements": [], "allowed": []}


def test_export_refuses_config_and_never_runs_it(tmp_path) -> None:
    repo = make_repo(tmp_path)
    marker = repo / "ran.txt"
    nested = repo / "architecture" / "nested"
    nested.mkdir()
    (nested / "likec4.config.mjs").write_text(
        "import fs from 'node:fs';\n"
        f"fs.writeFileSync({json.dumps(str(marker))}, 'yes');\n"
        "export default { name: 'x' };\n",
        encoding="utf-8",
    )
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith("error: model-config: ")
    assert not marker.exists()


def test_export_refuses_a_link_in_the_model(tmp_path) -> None:
    repo = make_repo(tmp_path)
    target = tmp_path / unique("t")
    target.mkdir()
    link_dir(target, repo / "architecture" / "link")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: model-symlink: ")


def test_export_checks_the_spec_copy(tmp_path) -> None:
    missing = make_repo(tmp_path, spec=False)
    assert error_lines(run_tool("export", "--repo", missing))[0].startswith("error: spec-copy: ")
    crlf = make_repo(tmp_path)
    (crlf / "architecture" / "c4.c4").write_bytes(SHIPPED_SPEC.read_text(encoding="utf-8").replace("\n", "\r\n").encode())
    assert run_tool("export", "--repo", crlf).returncode == 0


def test_export_refuses_duplicate_prefixes(tmp_path) -> None:
    model = "model {\n  a = component 'A' {\n    metadata {\n      code 'x'\n    }\n  }\n  b = component 'B' {\n    metadata {\n      code 'x'\n    }\n  }\n}\n"
    proc = run_tool("export", "--repo", make_repo(tmp_path, model))
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: model-error: ")


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(["frobnicate"], id="unknown-subcommand"),
        pytest.param(["export", "--repo", ".", "--bogus", "1"], id="unknown-flag"),
        pytest.param(["check", "--repo", ".", "--deps", "d.json", "--format", "xml"], id="format-xml"),
        pytest.param(["export", "--repo", ".", "--timeout", "601"], id="timeout-601"),
        pytest.param(["export", "--repo"], id="flag-without-value"),
        pytest.param(["check", "--repo", ".", "--deps", "d.json", "--format", "json", "--format", "text"], id="repeated-flag"),
        pytest.param(["check", "--repo", ".", "--deps", "d.json", "--scope", "a,,b"], id="empty-scope-item"),
    ],
)
def test_usage_errors_end_to_end(args: list[str]) -> None:
    proc = run_tool(*args)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith("error: usage: ")


def test_timeout_zero(tmp_path) -> None:
    proc = run_tool("export", "--repo", make_repo(tmp_path), "--timeout", "0")
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc) == [line for line in error_lines(proc) if line.startswith("error: timeout: ")]
    assert error_lines(proc)


def test_repo_and_model_paths(tmp_path) -> None:
    assert error_lines(run_tool("export", "--repo", tmp_path / "missing"))[0].startswith("error: bad-input: ")
    repo = make_repo(tmp_path)
    assert error_lines(run_tool("export", "--repo", repo, "--model", "nope"))[0].startswith("error: bad-input: ")
    assert error_lines(run_tool("export", "--repo", repo, "--model", ".."))[0].startswith("error: outside-repo: ")


def test_repo_version_note(tmp_path) -> None:
    repo = make_repo(tmp_path)
    make_shim(repo / "node_modules", version="1.59.0")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    assert "note: likec4 1.59.0 from repo; tested with 1.60.0" in proc.stderr.splitlines()


def test_repo_version_is_cleaned_in_the_note(tmp_path) -> None:
    repo = make_repo(tmp_path)
    make_shim(repo / "node_modules", version="1.59.0\u001b[2J")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    assert "note: likec4 1.59.0 from repo; tested with 1.60.0" in proc.stderr.splitlines()
    assert "\x1b" not in proc.stderr


def test_model_strings_are_cleaned_in_export(tmp_path) -> None:
    model = (
        "model {\n  a = component 'A' {\n    metadata {\n      code 'x\u001b[31my'\n"
        "      rules 'BR-1\u202e, " + "R" * 250 + "'\n    }\n  }\n}\n"
    )
    repo = make_repo(tmp_path, model)
    data = json.loads(run_tool("export", "--repo", repo).stdout)
    assert data["elements"][0]["code"] == ["xy"]
    assert data["elements"][0]["rules"] == ["BR-1", "R" * 199 + "…"]


def test_missing_likec4_from_a_copied_engine(tmp_path) -> None:
    script = copy_engine(tmp_path / unique("copy"))
    proc = run_tool("export", "--repo", make_repo(tmp_path), script=script)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: likec4-missing: ")


def test_check_is_not_available_yet(tmp_path) -> None:
    proc = run_tool("check", "--repo", make_repo(tmp_path), "--deps", "d.json")
    assert proc.returncode == 2
    assert error_lines(proc)[0] == "error: internal: check is not available in this build"
