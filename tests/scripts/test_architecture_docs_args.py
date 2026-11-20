"""Command line of the architecture docs tool (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

import pytest

from arch_delta_support import DOCS_LIB, call, require_node

require_node()


def parse(*argv: str) -> dict:
    return call("args.mjs", "parseArgs", list(argv), lib=DOCS_LIB)


def test_docs_args_defaults() -> None:
    assert parse("build", "--repo", ".")["value"] == {
        "command": "build", "repo": ".", "model": "docs/architecture", "gap": None, "out": None, "timeout": 60,
    }
    assert parse("check", "--repo", "r", "--model", "m", "--gap", "g", "--out", "o", "--timeout", "5")["value"] == {
        "command": "check", "repo": "r", "model": "m", "gap": "g", "out": "o", "timeout": 5,
    }


@pytest.mark.parametrize(("argv", "detail"), [
    pytest.param((), "unknown subcommand (none); use build or check", id="none"),
    pytest.param(("export", "--repo", "."), "unknown subcommand export; use build or check", id="export"),
    pytest.param(("build",), "--repo is required", id="no-repo"),
    pytest.param(("build", "--repo", ".", "--deps", "x"), "unknown flag for build: --deps", id="deps"),
    pytest.param(("build", "--repo"), "--repo needs a value", id="no-value"),
    pytest.param(("check", "--repo", ".", "--repo", "."), "--repo given twice", id="twice"),
    pytest.param(("build", "--repo", ".", "--out", ""), "--out must not be empty", id="empty-out"),
    pytest.param(("build", "--repo", ".", "--timeout", "601"), "--timeout must be a whole number from 0 to 600", id="timeout"),
    pytest.param(("build", "--repo", ".", "--timeout", "-1"), "--timeout must be a whole number from 0 to 600", id="timeout-negative"),
    pytest.param(("build", "--repo", ".", "--model", "--out", "o"), "--model needs a value", id="flag-as-value"),
    pytest.param(("build", "--repo", ""), "--repo is required", id="empty-repo"),
    pytest.param(("build", "--repo", ".", "--model", ""), "--model must not be empty", id="empty-model"),
    pytest.param(("build", "--repo", ".", "--gap", ""), "--gap must not be empty", id="empty-gap"),
])
def test_docs_args_problems(argv: tuple, detail: str) -> None:
    result = parse(*argv)
    assert (result["token"], result["details"]) == ("usage", [detail])


def test_docs_args_timeout_bounds() -> None:
    assert [parse("build", "--repo", ".", "--timeout", s)["value"]["timeout"] for s in ("0", "600")] == [0, 600]
