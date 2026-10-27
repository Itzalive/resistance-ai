from __future__ import annotations

import re
from typing import Callable

import pytest


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
