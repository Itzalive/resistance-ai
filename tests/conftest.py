from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

import pytest

_SCRIPTS_DIR = str(Path(__file__).parents[1] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


@pytest.fixture
def section_text() -> Callable[[str, str], str]:
    """Extract a markdown section body from a heading."""

    def _section_text(text: str, heading: str) -> str:
        match = re.search(
            rf"^## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL | re.MULTILINE
        )
        assert match, f"missing {heading} section"
        return match.group(1)

    return _section_text
