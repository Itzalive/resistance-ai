from __future__ import annotations

import json
import shutil

import pytest

from arch_delta_support import (
    call, copy_engine, error_lines, link_dir, make_repo, make_shim, require_node, run_tool, unique, write_json, LIKEC4_ENTRY, SHIPPED_SPEC, SHOP_MODEL,
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
    nested = repo / "docs" / "architecture" / "nested"
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
    link_dir(target, repo / "docs" / "architecture" / "link")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: model-symlink: ")


def test_export_checks_the_spec_copy(tmp_path) -> None:
    missing = make_repo(tmp_path, spec=False)
    assert error_lines(run_tool("export", "--repo", missing))[0].startswith("error: spec-copy: ")
    crlf = make_repo(tmp_path)
    (crlf / "docs" / "architecture" / "c4.c4").write_bytes(SHIPPED_SPEC.read_text(encoding="utf-8").replace("\n", "\r\n").encode())
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


def test_model_that_is_a_file_is_bad_input(tmp_path) -> None:
    repo = make_repo(tmp_path)
    proc = run_tool("export", "--repo", repo, "--model", "docs/architecture/c4.c4")
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: bad-input: ")


def test_model_only_in_the_old_folder_is_not_found(tmp_path) -> None:
    repo = make_repo(tmp_path)
    (repo / "docs" / "architecture").rename(repo / "architecture")
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith("error: bad-input: ")
    assert run_tool("export", "--repo", repo, "--model", "architecture").returncode == 0


def test_repo_given_through_a_link_exports(tmp_path) -> None:
    repo = make_repo(tmp_path)
    link = tmp_path / unique("link")
    link_dir(repo, link)
    proc = run_tool("export", "--repo", link)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["format"] == 1


def test_unexpected_error_is_internal_exit_2(tmp_path) -> None:
    preload = tmp_path / unique("preload")
    preload.mkdir()
    hook = preload / "throw.mjs"
    hook.write_text("process.stdout.write = () => { throw new Error('boom'); };\n", encoding="utf-8")
    proc = run_tool("export", "--repo", make_repo(tmp_path), preload=hook)
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: internal: boom"]


def test_an_input_error_ends_without_waiting_for_the_deadline(tmp_path) -> None:
    proc = run_tool("export", "--repo", make_repo(tmp_path), "--model", "nope", "--timeout", "120", timeout=60)
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: bad-input: --model directory not found"]


def test_export_sorts_by_code_unit_not_locale(tmp_path) -> None:
    model = "model {\n  a = component 'A'\n  B = component 'B'\n  a -> B\n  B -> a\n}\n"
    data = json.loads(run_tool("export", "--repo", make_repo(tmp_path, model)).stdout)
    assert [e["id"] for e in data["elements"]] == ["B", "a"]
    assert data["allowed"] == [{"from": "B", "to": "a"}, {"from": "a", "to": "B"}]


def test_deadline_check_fails_without_the_timer(tmp_path) -> None:
    hook = tmp_path / f"{unique('no-timer')}.mjs"
    hook.write_text(
        "const real = globalThis.setTimeout;\n"
        "let first = true;\n"
        "globalThis.setTimeout = (...args) => {\n"
        "  if (first) { first = false; return { unref() {}, ref() {} }; }\n"
        "  return real(...args);\n"
        "};\n",
        encoding="utf-8",
    )
    proc = run_tool("export", "--repo", make_repo(tmp_path), "--timeout", "0", preload=hook)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc) == ["error: timeout: run exceeded --timeout 0s"]


def test_timer_ends_a_slow_load_at_the_deadline(tmp_path) -> None:
    repo = make_repo(tmp_path)
    slow = (
        "await new Promise((resolve) => setTimeout(resolve, 30000));\n"
        f"export * from {json.dumps(LIKEC4_ENTRY.as_uri())};\n"
    )
    make_shim(repo / "node_modules", source=slow)
    proc = run_tool("export", "--repo", repo, "--timeout", "1", timeout=20)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc) == ["error: timeout: run exceeded --timeout 1s"]
