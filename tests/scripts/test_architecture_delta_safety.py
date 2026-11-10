from __future__ import annotations

import re

import pytest

from arch_delta_support import FIXTURES, LIB, SCRIPT, error_lines, make_repo, require_node, run_tool, write_json

require_node()

MB = 1024 * 1024
CLEAN_EDGES = [["shop.orders.api.handler", "shop.checkout.service"]]


def test_no_network_check_and_export(tmp_path) -> None:
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": CLEAN_EDGES})
    assert run_tool("check", "--repo", repo, "--deps", deps, preload=FIXTURES / "no-network.mjs").returncode == 0
    assert run_tool("export", "--repo", repo, preload=FIXTURES / "no-network.mjs").returncode == 0


@pytest.mark.parametrize("case", ["edge-cap", "file-size", "model-size", "timeout"])
def test_limits_end_to_end(tmp_path, case: str) -> None:
    repo = make_repo(tmp_path)
    deps = repo / "deps.json"
    write_json(deps, {"edges": CLEAN_EDGES})
    extra: list[str] = []
    if case == "edge-cap":
        deps.write_text('{"edges":[' + ",".join(['["a","b"]'] * 1_000_001) + "]}", encoding="utf-8")
    elif case == "file-size":
        deps.write_text('{"edges":[]}' + " " * (50 * MB), encoding="utf-8")
    elif case == "model-size":
        for i in range(2001):
            (repo / "architecture" / f"f{i}.txt").write_text("x", encoding="utf-8")
    elif case == "timeout":
        extra = ["--timeout", "0"]
    proc = run_tool("check", "--repo", repo, "--deps", deps, *extra)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith(f"error: {case}: ")


def test_unexpected_error_is_internal_never_one(tmp_path) -> None:
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": [["shop.orders.api.x", "shop.payments.card.y"]]})
    proc = run_tool("check", "--repo", repo, "--deps", deps, "--format", "json", preload=FIXTURES / "stdout-throws.mjs")
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: internal: forced stdout failure"]


def test_tool_source_never_spawns_or_writes() -> None:
    sources = [SCRIPT, *sorted(LIB.glob("*.mjs"))]
    forbidden = re.compile(
        r"child_process|worker_threads|fs/promises|\bopenSync\s*\(|(?<!stdout\.)(?<!stderr\.)\bwrite(Sync)?\s*\("
        r"|\b(writeFile|appendFile|mkdir|rm|unlink|rename|copyFile|cp|createWriteStream|symlink|link|truncate"
        r"|chmod|chown|utimes)(Sync)?\s*\("
    )
    for source in sources:
        assert not forbidden.search(source.read_text(encoding="utf-8")), source
