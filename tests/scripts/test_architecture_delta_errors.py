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
    assert clean("x\x00y\x7fz\x85w‮q⁦r\n") == "xyzwqr"


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
