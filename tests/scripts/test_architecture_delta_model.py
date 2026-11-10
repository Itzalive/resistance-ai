from __future__ import annotations

import json
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


from arch_delta_support import ENGINE, SHOP_MODEL, load_model, make_shim  # noqa: E402


def write_model(tmp_path: Path, text: str) -> Path:
    folder = model_dir(tmp_path)
    (folder / "model.c4").write_text(text, encoding="utf-8")
    return folder


def test_shop_model_loads_elements_and_relationships(tmp_path) -> None:
    result = load_model(write_model(tmp_path, SHOP_MODEL))
    assert result["ok"], result
    elements = {e["id"]: e for e in result["value"]["elements"]}
    assert set(elements) == {"shop", "shop.orders", "shop.orders.api", "shop.checkout", "shop.payments", "shop.payments.card"}
    assert elements["shop.payments"] == {
        "id": "shop.payments", "kind": "container", "tags": ["protected"], "code": ["shop.payments"], "rules": [],
    }
    assert elements["shop"]["code"] == []
    assert sorted((r["from"], r["to"]) for r in result["value"]["relationships"]) == [
        ("shop.checkout", "shop.payments"), ("shop.orders", "shop.checkout"),
    ]


def test_code_and_rules_are_split_and_trimmed(tmp_path) -> None:
    text = "model {\n  a = component 'A' {\n    metadata {\n      code 'a.one , a.two'\n      rules 'BR-1,  BR-2'\n    }\n  }\n}\n"
    element = load_model(write_model(tmp_path, text))["value"]["elements"][0]
    assert element["code"] == ["a.one", "a.two"]
    assert element["rules"] == ["BR-1", "BR-2"]


def test_model_errors_name_file_and_line(tmp_path) -> None:
    text = "model {\n  a = component 'A'\n  a -> missing\n  b = nosuchkind 'B'\n}\n"
    result = load_model(write_model(tmp_path, text))
    assert result["token"] == "model-error"
    assert len(result["details"]) >= 2
    assert any(d.startswith("model.c4:3:") for d in result["details"])
    assert any(d.startswith("model.c4:4:") for d in result["details"])


@pytest.mark.parametrize(
    ("codes", "label"),
    [
        pytest.param(["shared", "shared"], "duplicate", id="duplicate"),
        pytest.param(["a,,b", "c"], "empty", id="empty-item"),
    ],
)
def test_prefix_errors(tmp_path, codes: list[str], label: str) -> None:
    text = "model {\n" + "".join(
        f"  e{i} = component 'E{i}' {{\n    metadata {{\n      code '{code}'\n    }}\n  }}\n" for i, code in enumerate(codes)
    ) + "}\n"
    result = load_model(write_model(tmp_path, text))
    assert result["token"] == "model-error"
    assert label in result["details"][0]


BAD_ELEMENT = """export class LikeC4 {
  static async fromWorkspace() {
    return {
      getErrors() { return []; },
      async computedModel() {
        return { elements() { return [ELEMENT]; }, relationships() { return [RELATIONSHIP]; } };
      },
    };
  }
}
"""


@pytest.mark.parametrize(
    ("element", "relationship"),
    [
        pytest.param("{ kind: 'component', tags: [], getMetadata() { return {}; } }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="no-id"),
        pytest.param("{ id: 'a', kind: 'component', tags: 'x', getMetadata() { return {}; } }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="tags-not-array"),
        pytest.param("{ id: 'a', kind: 'component', tags: [], getMetadata() { return { code: ['a'] }; } }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="code-array"),
        pytest.param("{ id: 'a', kind: 'component', tags: [], metadata: {} }", "{ source: { id: 'a' }, target: { id: 'a' } }", id="no-getmetadata"),
        pytest.param("{ id: 'a', kind: 'component', tags: [], getMetadata() { return {}; } }", "{ source: { id: 'a' } }", id="no-target"),
    ],
)
def test_unexpected_api_shapes_are_internal(tmp_path, element: str, relationship: str) -> None:
    shim = make_shim(tmp_path / unique("nm"), source=BAD_ELEMENT.replace("ELEMENT", element).replace("RELATIONSHIP", relationship))
    result = load_model(model_dir(tmp_path), entry=shim / "index.mjs")
    assert result["ok"] is False
    assert result["token"] == "internal"


@pytest.mark.parametrize(("count", "ok"), [pytest.param(5000, True, id="5000-ok"), pytest.param(5001, False, id="5001-refused")])
def test_element_cap(tmp_path, count: int, ok: bool) -> None:
    text = "model {\n" + "".join(f"  e{i} = component 'E{i}'\n" for i in range(count)) + "}\n"
    result = load_model(write_model(tmp_path, text))
    assert result["ok"] is ok
    if not ok:
        assert result["token"] == "element-cap"



def test_folder_at_exactly_50_mb_is_accepted(tmp_path) -> None:
    folder = model_dir(tmp_path)
    (folder / "big0.bin").write_bytes(b"\0" * (25 * MB))
    (folder / "big1.bin").write_bytes(b"\0" * (25 * MB - SHIPPED_SPEC.stat().st_size))
    assert call("walk.mjs", "walkModelDir", str(folder))["ok"] is True


def test_one_model_error_is_reported(tmp_path) -> None:
    folder = model_dir(tmp_path)
    (folder / "model.c4").write_text("model {\n  b = nosuchkind 'B'\n}\n", encoding="utf-8")
    result = load_model(folder)
    assert result["token"] == "model-error"
    assert any(d.startswith("model.c4:2:") for d in result["details"])


SHIM = """export class LikeC4 {
  static async fromWorkspace() {
    FROM_WORKSPACE
    return {
      getErrors() { return ERRORS; },
      async computedModel() {
        COMPUTED
        return { elements() { return [ELEMENT]; }, relationships() { return [RELATIONSHIP]; } };
      },
    };
  }
}
"""


GOOD = {
    "FROM_WORKSPACE": "", "ERRORS": "[]", "COMPUTED": "",
    "ELEMENT": "{ id: 'a', kind: 'component', tags: [], getMetadata() { return {}; } }",
    "RELATIONSHIP": "{ source: { id: 'a' }, target: { id: 'a' } }",
}


def shim_source(**changes: str) -> str:
    source = SHIM
    for key, value in {**GOOD, **changes}.items():
        source = source.replace(key, value)
    return source


def shim_load(tmp_path: Path, **changes: str) -> dict:
    shim = make_shim(tmp_path / unique("nm"), source=shim_source(**changes))
    return load_model(model_dir(tmp_path), entry=shim / "index.mjs")


def test_good_shim_loads(tmp_path) -> None:
    assert shim_load(tmp_path)["ok"] is True


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"ERRORS": "'oops'"}, id="errors-not-a-list"),
        pytest.param({"ELEMENT": "{ id: 'a', tags: [], getMetadata() { return {}; } }"}, id="no-kind"),
        pytest.param({"ELEMENT": "{ id: 'a', kind: 'component', tags: [1], getMetadata() { return {}; } }"}, id="tag-not-string"),
        pytest.param({"ELEMENT": "{ id: 'a', kind: 'component', tags: [], getMetadata() { return { rules: 1 }; } }"}, id="rules-number"),
        pytest.param({"RELATIONSHIP": "{ target: { id: 'a' } }"}, id="no-source"),
    ],
)

def test_more_unexpected_api_shapes_are_internal(tmp_path, changes: dict) -> None:
    result = shim_load(tmp_path, **changes)
    assert result["ok"] is False
    assert result["token"] == "internal"


@pytest.mark.parametrize("where", ["FROM_WORKSPACE", "COMPUTED"])

def test_likec4_exceptions_are_model_errors(tmp_path, where: str) -> None:
    result = shim_load(tmp_path, **{where: "throw new Error('boom');"})
    assert result["token"] == "model-error"
    assert result["details"] == ["boom"]


def test_every_likec4_error_gets_a_line(tmp_path) -> None:
    folder = model_dir(tmp_path)
    errors = (
        "[{ message: 'one', sourceFsPath: DIR + '/m.c4', line: 0 },"
        " { message: 'two', sourceFsPath: DIR + '/m.c4', line: 4 },"
        " { message: 'three' }]"
    ).replace("DIR", json.dumps(str(folder)))
    shim = make_shim(tmp_path / unique("nm"), source=shim_source(ERRORS=errors))
    result = load_model(folder, entry=shim / "index.mjs")
    assert result["token"] == "model-error"
    assert result["details"] == ["m.c4:1: one", "m.c4:5: two", "?:?: three"]


def test_config_name_anywhere_in_the_file_name_is_refused(tmp_path) -> None:
    folder = model_dir(tmp_path)
    (folder / "old-likec4.config.mjs.bak").write_text("x\n", encoding="utf-8")
    assert call("walk.mjs", "walkModelDir", str(folder))["token"] == "model-config"
