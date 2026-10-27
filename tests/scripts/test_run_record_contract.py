from __future__ import annotations

from pathlib import Path


def test_finishing_writes_run_record_before_presenting_options() -> None:
    skill_text = Path("skills/finishing-a-development-branch/SKILL.md").read_text(encoding="utf-8")

    assert "### Step 1b: Write the Run Record" in skill_text
    assert "review-log.py run-record" in skill_text
    assert skill_text.index("### Step 1b: Write the Run Record") < skill_text.index("### Step 3: Present Options")
