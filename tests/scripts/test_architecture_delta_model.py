from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from arch_delta_support import SHIPPED_SPEC, call, link_dir, require_node, unique

require_node()

MB = 1024 * 1024


def model_dir(tmp_path: Path) -> Path:
    folder = tmp_path / unique("model")
    folder.mkdir()
    shutil.copyfile(SHIPPED_SPEC, folder / "c4.c4")
    return folder


def walk(folder: Path) -> dict:
    return call("walk.mjs", "walkModelDir", str(folder))


def test_clean_folder_passes(tmp_path) -> None:
    folder = model_dir(tmp_path)
    (folder / "sub").mkdir()
    (folder / "sub" / "more.c4").write_text("model {\n}\n", encoding="utf-8")
    (folder / "known-gap.json").write_text('{"entries": []}', encoding="utf-8")
    assert walk(folder) == {"ok": True, "value": None}


@pytest.mark.parametrize("name", ["likec4.config.mjs", "LikeC4.Config.json", ".likec4rc", "likec4.config.ts"])
def test_config_file_at_any_depth_is_refused(tmp_path, name: str) -> None:
    folder = model_dir(tmp_path)
    (folder / "deep" / "er").mkdir(parents=True)
    (folder / "deep" / "er" / name).write_text("export default {}\n", encoding="utf-8")
    result = walk(folder)
    assert result["ok"] is False
    assert result["token"] == "model-config"


def test_link_inside_the_model_folder_is_refused(tmp_path) -> None:
    folder = model_dir(tmp_path)
    target = tmp_path / unique("elsewhere")
    target.mkdir()
    link_dir(target, folder / "linked")
    assert walk(folder)["token"] == "model-symlink"


@pytest.mark.parametrize(
    ("files", "sizes", "ok"),
    [
        pytest.param(1999, [], True, id="2000-files-ok"),
        pytest.param(2000, [], False, id="2001-files-refused"),
        pytest.param(0, [25 * MB, 25 * MB - 2000], True, id="50mb-total-ok"),
        pytest.param(0, [25 * MB, 25 * MB], False, id="over-50mb-refused"),
    ],
)
def test_folder_limits(tmp_path, files: int, sizes: list[int], ok: bool) -> None:
    folder = model_dir(tmp_path)  # c4.c4 is one file of under 2,000 bytes
    for i in range(files):
        (folder / f"f{i}.txt").write_text("x", encoding="utf-8")
    for i, size in enumerate(sizes):
        (folder / f"big{i}.bin").write_bytes(b"\0" * size)
    result = walk(folder)
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "model-size"


def spec_copy(folder: Path) -> dict:
    return call("walk.mjs", "checkSpecCopy", str(folder), str(SHIPPED_SPEC))


def test_spec_copy_identical_is_accepted(tmp_path) -> None:
    assert spec_copy(model_dir(tmp_path))["ok"] is True


def test_spec_copy_with_crlf_is_accepted(tmp_path) -> None:
    folder = model_dir(tmp_path)
    text = SHIPPED_SPEC.read_text(encoding="utf-8").replace("\n", "\r\n")
    (folder / "c4.c4").write_bytes(text.encode("utf-8"))
    assert spec_copy(folder)["ok"] is True


def test_spec_copy_missing_or_changed_is_refused(tmp_path) -> None:
    missing = tmp_path / unique("model")
    missing.mkdir()
    assert spec_copy(missing)["token"] == "spec-copy"
    changed = model_dir(tmp_path)
    (changed / "c4.c4").write_text(SHIPPED_SPEC.read_text(encoding="utf-8") + "// extra\n", encoding="utf-8")
    assert spec_copy(changed)["token"] == "spec-copy"
