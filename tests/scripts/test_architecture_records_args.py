"""Flags of the architecture records tool (spec 2026-11-21-defining-architecture-records-design.md, "`change`")."""

from __future__ import annotations

import pytest

from arch_delta_support import RECORDS_LIB, call, require_node

require_node()

BASE = ["change", "--repo", ".", "--deps", "d.json", "--name", "first", "--date", "2026-11-21", "--run", "epic"]
TEXT = ["--asked-by", "#1", "--summary", "S."]


def parse(*argv: str) -> dict:
    return call("args.mjs", "parseArgs", list(argv), lib=RECORDS_LIB)


def test_defaults_and_values() -> None:
    out = parse(*BASE, *TEXT)
    assert out == {"ok": True, "value": {
        "command": "change", "repo": ".", "model": "docs/architecture", "before": None, "deps": "d.json",
        "separator": ".", "name": "first", "date": "2026-11-21", "run": "epic", "askedBy": "#1", "summary": "S.",
        "rejected": [], "compare": False, "timeout": 60}}


def test_rejected_repeats_in_order() -> None:
    out = parse(*BASE, *TEXT, "--rejected", "B.", "--rejected", "A.")
    assert out["value"]["rejected"] == ["B.", "A."]


def test_compare_needs_no_text_flags() -> None:
    out = parse(*BASE, "--compare")
    assert out["ok"] is True
    assert (out["value"]["compare"], out["value"]["askedBy"], out["value"]["summary"]) == (True, None, None)


def test_empty_text_values_are_left_to_the_validator() -> None:
    out = parse(*BASE, "--asked-by", "", "--summary", "")
    assert (out["value"]["askedBy"], out["value"]["summary"]) == ("", "")


@pytest.mark.parametrize(("argv", "detail"), [
    (["cycles-ish"], "unknown subcommand cycles-ish; use change or cycles"),
    ([*BASE, *TEXT, "--colour", "x"], "unknown flag for change: --colour"),
    ([*BASE, *TEXT, "--name", "again"], "--name given twice"),
    ([*BASE, *TEXT, "--compare", "--compare"], "--compare given twice"),
    ([*BASE[:-2], *TEXT], "--run is required"),
    ([*BASE, "--summary", "S."], "--asked-by is required without --compare"),
    ([*BASE, *TEXT, "--before"], "--before needs a value"),
    ([*BASE, *TEXT, "--timeout", "601"], "--timeout must be a whole number from 0 to 600"),
    ([*BASE, *TEXT, "--separator", ""], "--separator must not be empty"),
], ids=["subcommand", "unknown flag", "twice", "switch twice", "required", "text required", "no value", "timeout",
        "separator"])
def test_usage_errors(argv: list, detail: str) -> None:
    out = parse(*argv)
    assert (out["ok"], out["token"], out["details"]) == (False, "usage", [detail])


def test_cycles_defaults() -> None:
    out = parse("cycles", "--repo", ".", "--deps", "d.json")
    assert out == {"ok": True, "value": {"command": "cycles", "repo": ".", "model": "docs/architecture", "deps": "d.json",
                                         "separator": ".", "format": "text", "timeout": 60}}


@pytest.mark.parametrize(("argv", "detail"), [
    (["cycles", "--repo", ".", "--deps", "d.json", "--format", "xml"], "--format must be text or json"),
    (["cycles", "--repo", "."], "--deps is required"),
    (["cycles", "--repo", ".", "--deps", "d.json", "--compare"], "unknown flag for cycles: --compare"),
], ids=["format", "deps", "switch"])
def test_cycles_usage_errors(argv: list, detail: str) -> None:
    out = parse(*argv)
    assert (out["ok"], out["token"], out["details"]) == (False, "usage", [detail])
