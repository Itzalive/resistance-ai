from __future__ import annotations

import json

from arch_delta_support import call, lib_url, require_node, run_module

require_node()


def clean(text: str) -> str:
    result = call("errors.mjs", "clean", text)
    assert result["ok"], result
    return result["value"]


def test_clean_removes_ansi_sequences_first() -> None:
    assert clean("a\x1b[31mred\x1b[0m b\x1b]0;title\x07c") == "ared bc"


def test_clean_removes_c0_del_c1_and_bidi_controls() -> None:
    assert clean("x\x00y\x7fz\x85w\u202eq\u2066r\n") == "xyzwqr"


def test_clean_removes_osc_with_st_and_csi_with_intermediates() -> None:
    assert clean("a\x1b]0;title\x1b\x5cb\x1b[1 qc") == "abc"


def test_clean_removes_the_ends_of_each_control_range() -> None:
    assert clean("x\x9fy\u202az\u2069w") == "xyzw"


def test_clean_keeps_exactly_200_code_points() -> None:
    assert clean("a" * 200) == "a" * 200


def test_clean_cuts_201_code_points_to_199_plus_ellipsis() -> None:
    out = clean("b" * 201)
    assert out == "b" * 199 + "…"
    assert len(out) == 200


def test_clean_counts_code_points() -> None:
    assert clean("\U0001f600" * 150) == "\U0001f600" * 150
    out = clean("\U0001f600" * 201)
    assert out == "\U0001f600" * 199 + "…"


def test_error_lines_clean_each_detail() -> None:
    code = (
        f"import {{ ToolError, errorLines }} from {json.dumps(lib_url('errors.mjs'))};\n"
        "const err = new ToolError('usage', ['bad \\u001b[1mflag', 'second\\nline']);\n"
        "process.stdout.write(JSON.stringify({ token: err.token, lines: errorLines(err) }));\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "token": "usage",
        "lines": ["error: usage: bad flag", "error: usage: secondline"],
    }


def test_single_detail_becomes_one_line() -> None:
    code = (
        f"import {{ ToolError, errorLines }} from {json.dumps(lib_url('errors.mjs'))};\n"
        "process.stdout.write(JSON.stringify(errorLines(new ToolError('timeout', 'run exceeded'))));\n"
    )
    proc = run_module(code)
    assert json.loads(proc.stdout) == ["error: timeout: run exceeded"]


def test_check_json_cleans_every_id_after_sorting() -> None:
    dirty = "z\x1b[31m.a"
    result = {
        "breaches": [{"from": dirty, "to": "b\u202e", "edges": [["m", "n"]], "gap": "new"}],
        "notYetReached": [{"from": dirty, "to": "c\u202e"}],
        "unmapped": [],
        "hotSpots": [{"element": dirty, "shards": ["s\u202e", "r"]}],
        "gap": {"known": [{"from": dirty, "to": "d\u202e"}], "new": [{"from": dirty, "to": "b\u202e"}],
                "stale": [{"from": dirty, "to": "e\u202e"}]},
    }
    out = call("report.mjs", "checkJson", result, {"version": "1", "source": "plugin"})
    assert out["ok"], out
    data = out["value"]
    assert (data["breaches"][0]["from"], data["breaches"][0]["to"]) == ("z.a", "b")
    assert data["not_yet_reached"] == [{"from": "z.a", "to": "c"}]
    assert data["hot_spots"] == [{"element": "z.a", "shards": ["r", "s"]}]
    assert data["gap"] == {"known": [{"from": "z.a", "to": "d"}], "new": [{"from": "z.a", "to": "b"}],
                           "stale": [{"from": "z.a", "to": "e"}]}
