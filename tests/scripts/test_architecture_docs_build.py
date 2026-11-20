"""The documents of one build (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

from arch_delta_support import DOCS_LIB, call, require_node

require_node()


def test_clean_gap() -> None:  # AC-12 (known-gap text is cleaned like export output)
    entries = [{"from": "a" * 250, "to": "b", "reason": "r" * 250 + chr(27) + "[31m" + chr(0x202E) + "\nnext", "close_by": None}]
    result = call("build.mjs", "cleanGap", entries, lib=DOCS_LIB)
    assert result["value"] == [{"from": "a" * 199 + chr(0x2026), "to": "b", "reason": "r" * 250 + "\nnext", "close_by": None}]


def test_clean_gap_cleans_to_and_close_by() -> None:  # AC-12 (known-gap text): `to` is cut like an id, `close_by` cleaned like text
    entries = [{"from": "a", "to": "b" * 250, "reason": "r", "close_by": "2027" + chr(27) + "[31m" + chr(0x202E)}]
    result = call("build.mjs", "cleanGap", entries, lib=DOCS_LIB)
    assert result["value"] == [{"from": "a", "to": "b" * 199 + chr(0x2026), "reason": "r", "close_by": "2027"}]
