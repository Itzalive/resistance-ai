from __future__ import annotations

import pytest

from arch_delta_support import call, require_node

require_node()

DEFAULTS = {
    "deps": None, "model": "architecture", "gap": None, "scope": None, "shards": None,
    "separator": ".", "format": "text", "timeout": 60,
}


def parse(argv: list[str]) -> dict:
    return call("args.mjs", "parseArgs", argv)


def test_check_defaults() -> None:
    result = parse(["check", "--repo", "r", "--deps", "d.json"])
    assert result == {"ok": True, "value": {**DEFAULTS, "command": "check", "repo": "r", "deps": "d.json"}}


def test_export_defaults() -> None:
    result = parse(["export", "--repo", "r"])
    assert result == {"ok": True, "value": {**DEFAULTS, "command": "export", "repo": "r"}}


def test_every_check_flag() -> None:
    result = parse([
        "check", "--repo", "r", "--deps", "d", "--model", "m", "--gap", "g", "--scope", "a, b",
        "--shards", "s", "--separator", "/", "--format", "json", "--timeout", "600",
    ])
    assert result["value"] == {
        "command": "check", "repo": "r", "deps": "d", "model": "m", "gap": "g", "scope": ["a", "b"],
        "shards": "s", "separator": "/", "format": "json", "timeout": 600,
    }


def test_timeout_zero_is_valid() -> None:
    assert parse(["export", "--repo", "r", "--timeout", "0"])["value"]["timeout"] == 0


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param([], id="no-command"),
        pytest.param(["nope"], id="unknown-command"),
        pytest.param(["export"], id="missing-repo"),
        pytest.param(["check", "--repo", "r"], id="missing-deps"),
        pytest.param(["export", "--repo", "r", "--deps", "d"], id="deps-on-export"),
        pytest.param(["export", "--repo", "r", "--bogus", "x"], id="unknown-flag"),
        pytest.param(["export", "--repo"], id="flag-without-value"),
        pytest.param(["check", "--repo", "r", "--scope", "--deps", "d"], id="value-is-a-flag"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--scope", ""], id="scope-empty-string"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--scope", "a, ,b"], id="scope-blank-item"),
        pytest.param(["export", "--repo", "a", "--repo", "b"], id="repeated-flag"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--format", "xml"], id="format-xml"),
        pytest.param(["export", "--repo", "r", "--timeout", "601"], id="timeout-601"),
        pytest.param(["export", "--repo", "r", "--timeout", "-1"], id="timeout-negative"),
        pytest.param(["export", "--repo", "r", "--timeout", "1.5"], id="timeout-1.5"),
        pytest.param(["export", "--repo", "r", "--timeout", "x"], id="timeout-text"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--separator", ""], id="empty-separator"),
        pytest.param(["check", "--repo", "r", "--deps", "d", "--scope", "a,,b"], id="empty-scope-item"),
    ],
)
def test_usage_errors(argv: list[str]) -> None:
    result = parse(argv)
    assert result["ok"] is False
    assert result["token"] == "usage"
