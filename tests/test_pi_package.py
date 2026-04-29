from __future__ import annotations

import json
from pathlib import Path


def test_package_json_exposes_pi_skills_manifest() -> None:
    package = json.loads(Path("package.json").read_text())

    assert package["pi"]["skills"] == ["./skills"]
    assert "pi-package" in package["keywords"]


def test_readme_documents_pi_installation() -> None:
    readme = Path("README.md").read_text()

    assert "## Pi" in readme
    assert "pi install" in readme
