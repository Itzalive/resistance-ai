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


STRICT_NO_NETWORK = """\
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import tls from 'node:tls';

const deny = () => {
  process.stderr.write('network access attempted\\n');
  process.exit(97);
};
globalThis.fetch = deny;
for (const mod of [http, https]) {
  mod.request = deny;
  mod.get = deny;
}
net.connect = deny;
net.createConnection = deny;
tls.connect = deny;
"""


def test_no_network_even_when_the_error_would_be_caught(tmp_path) -> None:
    preload = tmp_path / "strict-no-network.mjs"
    preload.write_text(STRICT_NO_NETWORK, encoding="utf-8")
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": CLEAN_EDGES})
    for args in (["check", "--repo", repo, "--deps", deps], ["export", "--repo", repo]):
        proc = run_tool(*args, preload=preload)
        assert proc.returncode == 0, proc.stderr
        assert "network access attempted" not in proc.stderr


CLOCK_JUMP = """\
import fs from 'node:fs';

const read = fs.readFileSync;
const now = Date.now;
let jump = 0;
fs.readFileSync = function (file, ...rest) {
  const out = read.call(this, file, ...rest);
  if (String(file).endsWith(process.env.JUMP_AFTER)) jump = 3600 * 1000;
  return out;
};
Date.now = () => now() + jump;
"""


@pytest.mark.parametrize("name", ["deps.json", "known-gap.json", "shards.json"])
def test_deadline_is_checked_after_each_input_file(tmp_path, monkeypatch, name: str) -> None:
    preload = tmp_path / "clock-jump.mjs"
    preload.write_text(CLOCK_JUMP, encoding="utf-8")
    monkeypatch.setenv("JUMP_AFTER", name)
    repo = make_repo(tmp_path)
    deps = write_json(repo / "deps.json", {"edges": CLEAN_EDGES})
    write_json(repo / "architecture" / "known-gap.json", {"entries": []})
    shards = write_json(repo / "shards.json", {"shards": {}})
    proc = run_tool("check", "--repo", repo, "--deps", deps, "--shards", shards, preload=preload)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert error_lines(proc)[0].startswith("error: timeout: ")


CLOCK_JUMP_IN_MATCHING = """\
const now = Date.now;
Date.now = () => (new Error().stack.includes('match.mjs') ? now() + 3600 * 1000 : now());
"""


def test_deadline_is_checked_while_matching(tmp_path) -> None:
    preload = tmp_path / "clock-jump-matching.mjs"
    preload.write_text(CLOCK_JUMP_IN_MATCHING, encoding="utf-8")
    repo = make_repo(tmp_path)
    edges = [[f"shop.orders.api.m{i}", "shop.checkout.s"] for i in range(10_001)]
    deps = write_json(repo / "deps.json", {"edges": edges})
    proc = run_tool("check", "--repo", repo, "--deps", deps, preload=preload)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: timeout: ")
