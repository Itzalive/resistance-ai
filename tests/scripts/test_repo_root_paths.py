from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def test_import_superpowers_catalog_defaults_to_repo_root_paths() -> None:
    import import_superpowers_catalog as module

    assert module.DEFAULT_SOURCE_ROOT == module.REPO_ROOT / "vendor" / "obra-superpowers"
    assert module.DEFAULT_OUTPUT_ROOT == module.REPO_ROOT
    assert module._LOCAL_AUTHORING_SKILLS_ROOT == module.REPO_ROOT / "skills"
