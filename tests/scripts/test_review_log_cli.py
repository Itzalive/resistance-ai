from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CLI = Path("skills/shared/scripts/review-log.py").resolve()


def run(tmp_path: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=tmp_path,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def append_args(**overrides: str) -> list[str]:
    fields = {
        "--item-id": "re-11",
        "--skill": "specifying-work-items",
        "--phase": "INDEPENDENT_AUDIT",
        "--round": "1",
        "--verdict": "APPROVED",
        "--orchestrator": "claude-opus-5-5",
        "--reviewer-model": "claude-sonnet-5-5",
        "--independence": "fresh-context",
    }
    fields.update(overrides)
    return ["append", *[part for pair in fields.items() for part in pair]]


def read_log(tmp_path: Path, name: str = ".review_log.jsonl") -> list[dict]:
    return [json.loads(line) for line in (tmp_path / name).read_text(encoding="utf-8").splitlines()]


def test_append_writes_one_schema_entry(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(), "--tokens", "120000", "--reason", "Approved after r1.")

    assert result.returncode == 0, result.stderr
    [entry] = read_log(tmp_path)
    assert entry["item_id"] == "re-11"
    assert entry["skill"] == "specifying-work-items"
    assert entry["phase"] == "INDEPENDENT_AUDIT"
    assert entry["round"] == 1
    assert entry["verdict"] == "APPROVED"
    assert entry["reviewer_model"] == "claude-sonnet-5-5"
    assert entry["independence"] == "fresh-context"
    assert entry["findings"] == []
    assert entry["tokens"] == 120000
    assert entry["reason"] == "Approved after r1."
    assert entry["ts"].endswith("Z")


def test_findings_keep_colons_backslashes_and_quotes_in_text(tmp_path: Path) -> None:
    text = r'breaks stub at C:\repo\test_handler.py:531 "one-arg"'
    result = run(
        tmp_path,
        *append_args(**{"--verdict": "REJECTED"}),
        "--finding",
        f"critical:missed-caller:{text}",
        "--finding",
        "minor:wording:typo",
    )

    assert result.returncode == 0, result.stderr
    [entry] = read_log(tmp_path)
    assert entry["findings"] == [
        {"severity": "critical", "kind": "missed-caller", "text": text},
        {"severity": "minor", "kind": "wording", "text": "typo"},
    ]


def test_appends_after_existing_line_without_trailing_newline(tmp_path: Path) -> None:
    (tmp_path / ".review_log.jsonl").write_text('{"legacy": true}', encoding="utf-8")

    result = run(tmp_path, *append_args())

    assert result.returncode == 0, result.stderr
    entries = read_log(tmp_path)
    assert entries[0] == {"legacy": True}
    assert entries[1]["item_id"] == "re-11"


def test_rejects_unknown_phase_and_writes_nothing(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--phase": "SPEC2_PLAN_COHERENCE"}))

    assert result.returncode == 2
    assert "phase" in result.stderr
    assert not (tmp_path / ".review_log.jsonl").exists()


def test_rejects_legacy_skill_name(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--skill": "brainstorming"}))

    assert result.returncode == 2
    assert "skill" in result.stderr


def test_rejects_bracketed_status_string_as_verdict(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--verdict": "[APPROVED - READY FOR EXECUTION]"}))

    assert result.returncode == 2
    assert "verdict" in result.stderr


def test_rejected_verdict_requires_a_finding(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--verdict": "REJECTED"}))

    assert result.returncode == 2
    assert "finding" in result.stderr
    assert not (tmp_path / ".review_log.jsonl").exists()


def test_rejects_finding_with_unknown_kind(tmp_path: Path) -> None:
    result = run(
        tmp_path,
        *append_args(**{"--verdict": "FAIL", "--phase": "SURVIVABILITY", "--skill": "survivability"}),
        "--finding",
        "critical:style:not a kind",
    )

    assert result.returncode == 2
    assert "kind" in result.stderr


def test_rejects_round_zero(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--round": "0"}))

    assert result.returncode == 2
    assert "round" in result.stderr


def test_self_review_requires_self_independence(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--phase": "SPEC_REVIEW", "--independence": "cross-family"}))

    assert result.returncode == 2
    assert "independence" in result.stderr


def test_independent_audit_rejects_self_independence(tmp_path: Path) -> None:
    result = run(tmp_path, *append_args(**{"--independence": "self"}))

    assert result.returncode == 2
    assert "independence" in result.stderr


RUN_RECORD = {
    "item_id": "re-13",
    "plan": "docs/plans/2026-10-27-review-log.md",
    "tasks": 4,
    "tiers": {"haiku": 2, "sonnet": 2},
    "escalations": [{"task": "2", "from": "haiku", "to": "sonnet", "reason": "failed twice"}],
    "attempts": {"1": 1, "2": 3},
    "tokens": {"planning": 300000, "execution": 600000, "code-review": 120000},
    "findings": {"checkpoint": {"weak-test": 2}, "code-review": {"real-bug": 1}},
    "plan_changes": ["Task 3 split after checkpoint"],
    "slips": ["executor skipped RED run on task 1"],
}


def test_run_record_from_stdin_appends_validated_record(tmp_path: Path) -> None:
    result = run(tmp_path, "run-record", "--from", "-", stdin=json.dumps(RUN_RECORD))

    assert result.returncode == 0, result.stderr
    [record] = read_log(tmp_path, ".run_records.jsonl")
    assert record["ts"].endswith("Z")
    assert {k: v for k, v in record.items() if k != "ts"} == RUN_RECORD


def test_run_record_rejects_unknown_finding_kind_and_writes_nothing(tmp_path: Path) -> None:
    bad = {**RUN_RECORD, "findings": {"checkpoint": {"nit": 1}}}

    result = run(tmp_path, "run-record", "--from", "-", stdin=json.dumps(bad))

    assert result.returncode == 2
    assert "kind" in result.stderr
    assert not (tmp_path / ".run_records.jsonl").exists()


def test_run_record_rejects_missing_field(tmp_path: Path) -> None:
    bad = {k: v for k, v in RUN_RECORD.items() if k != "slips"}

    result = run(tmp_path, "run-record", "--from", "-", stdin=json.dumps(bad))

    assert result.returncode == 2
    assert "slips" in result.stderr


def test_run_record_rejects_malformed_json(tmp_path: Path) -> None:
    result = run(tmp_path, "run-record", "--from", "-", stdin=r'{"item_id": "C:\query"}')

    assert result.returncode == 2
    assert "JSON" in result.stderr
