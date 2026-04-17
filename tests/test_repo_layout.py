from __future__ import annotations

from pathlib import Path
import subprocess


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
    gitmodules = (repo_root / ".gitmodules").read_text()
    assert '[submodule "vendor/obra-superpowers"]' in gitmodules
    assert "path = vendor/obra-superpowers" in gitmodules
    assert "url = https://github.com/obra/superpowers" in gitmodules
    gitlink_entry = subprocess.run(
        ["git", "ls-files", "-s", "vendor/obra-superpowers"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert gitlink_entry.startswith("160000 ")
    submodule_status = subprocess.run(
        ["git", "submodule", "status", "--", "vendor/obra-superpowers"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert " vendor/obra-superpowers" in submodule_status
    assert not submodule_status.startswith("-")
