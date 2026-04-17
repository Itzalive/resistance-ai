from __future__ import annotations

from pathlib import Path


def test_canonical_repo_contains_release_surfaces() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    required = [
        "README.md",
        "LICENSE",
        "pyproject.toml",
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "package.json",
        "vendor/obra-superpowers",
    ]
    missing = [path for path in required if not (repo_root / path).exists()]
    assert missing == []
