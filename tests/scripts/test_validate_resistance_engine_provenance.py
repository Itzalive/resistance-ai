"""Tests for scripts/validate_resistance_engine_provenance.py."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = str(Path(__file__).parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _run_import(
    tmp_path: Path, *, overrides: list[dict[str, str]] | None = None
) -> Path:
    from import_superpowers_catalog import main as import_main

    source_root = Path(__file__).parents[2] / "vendor" / "obra-superpowers"

    output_root = tmp_path / "resistance-engine"
    if overrides is not None:
        override_path = output_root / "consolidation" / "consolidation_overrides.json"
        override_path.parent.mkdir(parents=True, exist_ok=True)
        override_path.write_text(json.dumps(overrides, indent=2) + "\n")

    exit_code = import_main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "fixture-rev",
            "--imported-at",
            "2026-04-15T00:00:00Z",
        ]
    )
    assert exit_code == 0
    return output_root


def test_validate_provenance_passes_clean_import(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "provenance manifest valid" in captured.out


def test_validate_provenance_requires_authoring_default_contracts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], section_text
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    brainstorming_root = output_root / "skills" / "brainstorming"
    writing_plans_root = output_root / "skills" / "writing-plans"

    assert (
        brainstorming_root / "SPEC_REVIEW_MANIFEST.md"
    ).is_file(), "expected skill-local SPEC_REVIEW_MANIFEST.md to be imported"
    assert (
        brainstorming_root / "SPEC_RUBRIC.md"
    ).is_file(), "expected skill-local SPEC_RUBRIC.md to be imported"
    assert (
        brainstorming_root / "SPEC_STANDARDS.md"
    ).is_file(), "expected skill-local SPEC_STANDARDS.md to be imported"

    brainstorming_skill = (brainstorming_root / "SKILL.md").read_text()
    assert '## Anti-Pattern: "This Is Too Simple To Need A Design"' in brainstorming_skill
    assert "## Checklist" in brainstorming_skill
    assert "## Process Flow" in brainstorming_skill
    assert "## After the Design" in brainstorming_skill
    assert "`APPROVED - CROSS-MODEL AUDIT` is required before plan writing" in brainstorming_skill
    assert ".review_log.jsonl" in brainstorming_skill
    checklist_text = section_text(brainstorming_skill, "Checklist")
    after_text = section_text(brainstorming_skill, "After the Design")
    assert "APPROVED - CROSS-MODEL AUDIT" in checklist_text
    assert ".review_log.jsonl" in checklist_text
    assert "[SPEC-APPROVED]" in after_text
    assert ".review_log.jsonl" in after_text
    process_flow_text = section_text(brainstorming_skill, "Process Flow")
    assert '"Ask blocking question" -> "Assumptions / blockers" [label="answered"]' in process_flow_text
    assert "Revise design (pre-spec)" in process_flow_text
    assert "Revise design (post-review)" in process_flow_text
    assert '"Cross-model spec audit" -> "User review" [label="[SPEC-APPROVED]"]' in process_flow_text
    assert '"User review" ->  "Checklist Retrospective" [label="approved"]' in process_flow_text
    assert '"Checklist Retrospective" -> "Invoke writing-plans"' in process_flow_text
    assert "## Checklist Retrospective" in brainstorming_skill
    assert "### Threat Model (CIA)" in brainstorming_skill
    assert "cite repository proof" in brainstorming_skill
    assert "emit a blocker" in brainstorming_skill

    rubric_text = (brainstorming_root / "SPEC_RUBRIC.md").read_text()
    assert "No Hallucinated Dependencies" in rubric_text
    standards_text = (brainstorming_root / "SPEC_STANDARDS.md").read_text()
    assert "## 1. The CIA+ Threat Model" in standards_text
    assert "## 4. Post-Fix Consistency Check" in standards_text

    writing_plans_skill = (writing_plans_root / "SKILL.md").read_text()
    assert "## Scope Check" in writing_plans_skill
    assert "## File Structure" in writing_plans_skill
    assert "## Task Structure" in writing_plans_skill
    assert "## No Placeholders" in writing_plans_skill
    assert "## Execution Handoff" in writing_plans_skill
    assert "subagent-driven-development" in writing_plans_skill
    assert "executing-plans" in writing_plans_skill
    assert "### Risk & Confidence Assessment" in writing_plans_skill
    assert "RED / GREEN / REFACTOR" in writing_plans_skill
    assert "[APPROVED - READY FOR EXECUTION]" in writing_plans_skill
    assert "[REJECTED - PLAN DRIFT]" in writing_plans_skill
    assert "[REJECTED - SPEC INCOMPLETE]" in writing_plans_skill
    assert "## Process Flow" in writing_plans_skill
    task_structure_text = section_text(writing_plans_skill, "Task Structure")
    handoff_text = section_text(writing_plans_skill, "Execution Handoff")
    no_placeholders_text = section_text(writing_plans_skill, "No Placeholders")
    assert "### Task N: [single execution goal]" in task_structure_text
    assert "**Files:**" in task_structure_text
    assert "Step 1: write RED tests for the happy path AND at least two failure modes." in task_structure_text
    assert "Step 6: commit the finished slice" in task_structure_text
    assert "subagent-driven-development" in handoff_text
    assert "executing-plans" in handoff_text
    assert "Tabula Rasa" in handoff_text
    assert "RED/GREEN/REFACTOR" in handoff_text
    assert "exact `pytest` command" in no_placeholders_text

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming_entry = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )
    writing_plans_entry = next(
        entry for entry in manifest if entry["entry_id"] == "skill:writing-plans"
    )
    overlay_records = {
        file_record["local_file"]: file_record
        for file_record in brainstorming_entry["files"] + writing_plans_entry["files"]
        if file_record["local_file"]
        in {
            "skills/brainstorming/SKILL.md",
            "skills/brainstorming/SPEC_REVIEW_MANIFEST.md",
            "skills/brainstorming/SPEC_RUBRIC.md",
            "skills/brainstorming/SPEC_STANDARDS.md",
            "skills/writing-plans/SKILL.md",
        }
    }
    assert overlay_records["skills/brainstorming/SKILL.md"]["source_file"] == "skills/brainstorming/SKILL.md"
    assert overlay_records["skills/brainstorming/SKILL.md"]["source_repo"] == "."
    assert overlay_records["skills/brainstorming/SPEC_REVIEW_MANIFEST.md"]["source_file"] == (
        "skills/brainstorming/SPEC_REVIEW_MANIFEST.md"
    )
    assert overlay_records["skills/brainstorming/SPEC_REVIEW_MANIFEST.md"]["source_repo"] == "."
    assert overlay_records["skills/brainstorming/SPEC_RUBRIC.md"]["source_file"] == (
        "skills/brainstorming/SPEC_RUBRIC.md"
    )
    assert overlay_records["skills/brainstorming/SPEC_RUBRIC.md"]["source_repo"] == "."
    assert overlay_records["skills/brainstorming/SPEC_STANDARDS.md"]["source_file"] == (
        "skills/brainstorming/SPEC_STANDARDS.md"
    )
    assert overlay_records["skills/brainstorming/SPEC_STANDARDS.md"]["source_repo"] == "."
    assert overlay_records["skills/writing-plans/SKILL.md"]["source_file"] == "skills/writing-plans/SKILL.md"
    assert overlay_records["skills/writing-plans/SKILL.md"]["source_repo"] == "."

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "provenance manifest valid" in captured.out


def test_validate_provenance_accepts_pruned_file_absence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(
        tmp_path,
        overrides=[
            {
                "entry_id": "skill:brainstorming",
                "source_file": "skills/brainstorming/scripts/helper.js",
                "local_sync_policy": "pruned",
            }
        ],
    )
    (output_root / "skills" / "brainstorming" / "scripts" / "helper.js").unlink()

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )

    assert exit_code == 0
    assert helper_record["local_sync_policy"] == "pruned"
    assert helper_record["file_state"] == "missing-local-copy"
    assert "provenance manifest valid" in captured.out


def test_validate_provenance_rejects_present_pruned_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(
        tmp_path,
        overrides=[
            {
                "entry_id": "skill:brainstorming",
                "source_file": "skills/brainstorming/scripts/helper.js",
                "local_sync_policy": "pruned",
            }
        ],
    )

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "pruned file must be absent locally: skills/brainstorming/scripts/helper.js" in captured.err


def test_validate_provenance_rejects_manifest_policy_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )
    helper_record["local_sync_policy"] = "pruned"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        "manifest override mismatch for file: skill:brainstorming -> skills/brainstorming/scripts/helper.js"
        in captured.err
    )


def test_validate_provenance_rejects_invalid_manifest_policy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["files"][0]["local_sync_policy"] = "skip"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid local_sync_policy for file: skills/brainstorming/SKILL.md" in captured.err


def test_validate_provenance_rejects_catalog_entry_without_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.pop()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "catalog entry missing manifest entry: agent:code-reviewer" in captured.err


def test_validate_provenance_rejects_imported_entry_with_missing_local_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    (output_root / "skills" / "brainstorming" / "SKILL.md").unlink()

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )

    assert exit_code == 1
    assert brainstorming["manifest_state"] == "missing-local-copy"
    assert "missing local file for imported entry: skill:brainstorming" in captured.err


def test_validate_provenance_rejects_drift_detected_file_digest_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    helper_path = output_root / "agents" / "code-reviewer.md"
    helper_path.write_text("# changed reviewer\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    reviewer = next(entry for entry in manifest if entry["entry_id"] == "agent:code-reviewer")

    assert exit_code == 1
    assert reviewer["manifest_state"] == "drift-detected"
    assert "digest mismatch for local file: agents/code-reviewer.md" in captured.err


def test_validate_provenance_rejects_file_state_entry_state_disagreement(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["files"][0]["file_state"] = "drift-detected"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "entry/file state disagreement: skill:brainstorming" in captured.err


def test_validate_provenance_rejects_source_missing_entry_with_local_file_present(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from import_superpowers_catalog import main as import_main
    from validate_resistance_engine_provenance import main

    source_root = tmp_path / "vendor" / "obra-superpowers"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming").mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming" / "SKILL.md").write_text(
        "---\nname: brainstorming\n---\n"
    )
    (source_root / "agents").mkdir(parents=True, exist_ok=True)
    (source_root / "agents" / "code-reviewer.md").write_text("# reviewer\n")

    output_root = tmp_path / "resistance-engine"
    assert (
        import_main(
            [
                "--source-root",
                str(source_root),
                "--output-root",
                str(output_root),
                "--source-repo",
                "vendor/obra-superpowers",
                "--source-revision",
                "first-rev",
                "--imported-at",
                "2026-04-15T00:00:00Z",
            ]
        )
        == 0
    )

    shutil.rmtree(source_root / "skills" / "brainstorming")
    assert (
        import_main(
            [
                "--source-root",
                str(source_root),
                "--output-root",
                str(output_root),
                "--source-repo",
                "vendor/obra-superpowers",
                "--source-revision",
                "second-rev",
                "--imported-at",
                "2026-04-16T00:00:00Z",
            ]
        )
        == 0
    )

    local_file = output_root / "skills" / "brainstorming" / "SKILL.md"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text("unexpected resurrection\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "source-missing entry still has local file: skill:brainstorming" in captured.err


def test_validate_provenance_rejects_source_missing_entry_missing_lineage_metadata(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from import_superpowers_catalog import main as import_main
    from validate_resistance_engine_provenance import main

    source_root = tmp_path / "vendor" / "obra-superpowers"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming").mkdir(parents=True, exist_ok=True)
    (source_root / "skills" / "brainstorming" / "SKILL.md").write_text(
        "---\nname: brainstorming\n---\n"
    )
    (source_root / "agents").mkdir(parents=True, exist_ok=True)
    (source_root / "agents" / "code-reviewer.md").write_text("# reviewer\n")

    output_root = tmp_path / "resistance-engine"
    assert (
        import_main(
            [
                "--source-root",
                str(source_root),
                "--output-root",
                str(output_root),
                "--source-repo",
                "vendor/obra-superpowers",
                "--source-revision",
                "first-rev",
                "--imported-at",
                "2026-04-15T00:00:00Z",
            ]
        )
        == 0
    )
    shutil.rmtree(source_root / "skills" / "brainstorming")
    assert (
        import_main(
            [
                "--source-root",
                str(source_root),
                "--output-root",
                str(output_root),
                "--source-repo",
                "vendor/obra-superpowers",
                "--source-revision",
                "second-rev",
                "--imported-at",
                "2026-04-16T00:00:00Z",
            ]
        )
        == 0
    )

    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    source_missing_entry = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )
    source_missing_entry.pop("source_repo")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "malformed manifest entry missing field: source_repo" in captured.err


@pytest.mark.parametrize("digest_value", [None, "sha256:not-valid"])
def test_validate_provenance_rejects_missing_or_malformed_digest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], digest_value: str | None
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if digest_value is None:
        manifest[0]["files"][0].pop("source_digest")
    else:
        manifest[0]["files"][0]["source_digest"] = digest_value
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "missing or malformed digest for file: skills/brainstorming/SKILL.md" in captured.err


def test_validate_provenance_uses_deterministic_precedence_for_mixed_local_states(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    (output_root / "skills" / "brainstorming" / "SKILL.md").unlink()
    (output_root / "skills" / "brainstorming" / "scripts" / "helper.js").write_text(
        "console.log('changed helper');\n"
    )

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )

    assert exit_code == 1
    assert brainstorming["manifest_state"] == "drift-detected"
    assert "missing local file for imported entry: skill:brainstorming" in captured.err
    assert "digest mismatch for local file: skills/brainstorming/scripts/helper.js" in captured.err


def test_validate_provenance_rejects_duplicate_manifest_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.append(dict(manifest[0]))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "duplicate manifest entry_id: skill:brainstorming" in captured.err


def test_validate_provenance_rejects_manifest_entry_without_catalog_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    orphan_path = output_root / "skills" / "orphan" / "SKILL.md"
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_text("---\nname: orphan\n---\n")

    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    orphan_entry = dict(manifest[0])
    orphan_entry["entry_id"] = "skill:orphan"
    orphan_entry["name"] = "orphan"
    orphan_entry["source_path"] = "skills/orphan"
    orphan_entry["local_path"] = "skills/orphan"
    orphan_entry["files"] = [
        {
            **dict(orphan_entry["files"][0]),
            "source_file": "skills/orphan/SKILL.md",
            "local_file": "skills/orphan/SKILL.md",
        }
    ]
    manifest.append(orphan_entry)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "manifest entry missing catalog entry: skill:orphan" in captured.err


def test_validate_provenance_rejects_manifest_file_coverage_gap(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["files"].pop()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "manifest file coverage mismatch: skill:brainstorming" in captured.err


def test_validate_provenance_rejects_manifest_metadata_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["local_path"] = "skills/not-brainstorming"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "manifest metadata mismatch for entry: skill:brainstorming (local_path)" in captured.err


def test_validate_provenance_accepts_recorded_missing_local_copy_on_rerun(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    (output_root / "skills" / "brainstorming" / "SKILL.md").unlink()

    first_exit = main([str(output_root)])
    first = capsys.readouterr()
    second_exit = main([str(output_root)])
    second = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )

    assert first_exit == 1
    assert "missing local file for imported entry: skill:brainstorming" in first.err
    assert second_exit == 0
    assert brainstorming["manifest_state"] == "missing-local-copy"
    assert "provenance manifest valid" in second.out


def test_validate_provenance_accepts_recorded_drift_detected_on_rerun(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    (output_root / "skills" / "brainstorming" / "scripts" / "helper.js").write_text(
        "console.log('changed helper');\n"
    )

    first_exit = main([str(output_root)])
    first = capsys.readouterr()
    second_exit = main([str(output_root)])
    second = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )

    assert first_exit == 1
    assert (
        "digest mismatch for local file: skills/brainstorming/scripts/helper.js" in first.err
    )
    assert second_exit == 0
    assert brainstorming["manifest_state"] == "drift-detected"
    assert "provenance manifest valid" in second.out


def test_validate_provenance_accepts_recorded_mixed_local_states_on_rerun(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    (output_root / "skills" / "brainstorming" / "SKILL.md").unlink()
    (output_root / "skills" / "brainstorming" / "scripts" / "helper.js").write_text(
        "console.log('changed helper');\n"
    )

    first_exit = main([str(output_root)])
    first = capsys.readouterr()
    second_exit = main([str(output_root)])
    second = capsys.readouterr()

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )
    skill_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "resistance-engine/skills/brainstorming/SKILL.md"
    )
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )

    assert first_exit == 1
    assert "missing local file for imported entry: skill:brainstorming" in first.err
    assert "digest mismatch for local file: skills/brainstorming/scripts/helper.js" in first.err
    assert second_exit == 0
    assert brainstorming["manifest_state"] == "drift-detected"
    assert skill_record["file_state"] == "missing-local-copy"
    assert helper_record["file_state"] == "drift-detected"
    assert "provenance manifest valid" in second.out


def test_validate_provenance_rejects_missing_manifest_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    (output_root / "provenance" / "provenance_manifest.json").unlink()

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "missing required artifact: provenance/provenance_manifest.json" in captured.err


@pytest.mark.parametrize("field_name", ["local_path", "imported_files"])
def test_validate_provenance_rejects_malformed_catalog_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field_name: str
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    catalog_path = output_root / "catalog" / "catalog_index.json"
    catalog = json.loads(catalog_path.read_text())
    catalog[0].pop(field_name)
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert f"malformed catalog entry missing field: {field_name}" in captured.err


def test_validate_provenance_rejects_malformed_catalog_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    catalog_path = output_root / "catalog" / "catalog_index.json"
    catalog_path.write_text("{broken json\n")

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid JSON in artifact: catalog/catalog_index.json" in captured.err


def test_validate_provenance_rejects_malformed_manifest_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    manifest_path = output_root / "provenance" / "provenance_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[0].pop("entry_id")
    broken_manifest = json.dumps(manifest, indent=2) + "\n"
    manifest_path.write_text(broken_manifest)

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "malformed manifest entry missing field: entry_id" in captured.err
    assert manifest_path.read_text() == broken_manifest


def test_validate_provenance_rejects_directory_at_expected_file_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from validate_resistance_engine_provenance import main

    output_root = _run_import(tmp_path)
    agent_path = output_root / "agents" / "code-reviewer.md"
    agent_path.unlink()
    agent_path.mkdir()

    exit_code = main([str(output_root)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "expected file path is a directory: agents/code-reviewer.md" in captured.err
