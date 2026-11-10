from __future__ import annotations

import json
import re
import shutil

from arch_delta_support import ENGINE, LIKEC4_DIR, LIKEC4_ENTRY, SHIPPED_SPEC, require_node, run_module, unique

require_node()


def test_lockfile_pins_likec4_exactly() -> None:
    package = json.loads((ENGINE / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ENGINE / "package-lock.json").read_text(encoding="utf-8"))

    assert package["dependencies"] == {"likec4": "1.60.0"}
    assert lock["lockfileVersion"] == 3
    assert lock["packages"][""]["dependencies"] == {"likec4": "1.60.0"}
    assert lock["packages"]["node_modules/likec4"]["version"] == "1.60.0"


def test_installed_likec4_matches_the_pin() -> None:
    installed = json.loads((LIKEC4_DIR / "package.json").read_text(encoding="utf-8"))

    assert installed["version"] == "1.60.0"


def test_shipped_spec_declares_the_c4_kinds_and_tags() -> None:
    text = SHIPPED_SPEC.read_text(encoding="utf-8")

    for line in (
        "element system", "element container", "element component", "element external",
        "tag protected", "tag generic", "tag layer", "tag eval", "relationship uses",
    ):
        assert f"  {line}\n" in text
    assert "code" in text.split("specification {")[0]
    assert "rules" in text.split("specification {")[0]


def test_shipped_spec_header_documents_code_and_rules() -> None:
    header = SHIPPED_SPEC.read_text(encoding="utf-8").split("specification {")[0]

    assert re.search(r"^//\s+code\s+- ", header, re.M)
    assert re.search(r"^//\s+rules\s+- ", header, re.M)


def test_shipped_spec_loads_without_errors(tmp_path) -> None:
    model = tmp_path / unique("model")
    model.mkdir()
    shutil.copyfile(SHIPPED_SPEC, model / "c4.c4")
    code = (
        f"import {{ LikeC4 }} from {json.dumps(LIKEC4_ENTRY.as_uri())};\n"
        f"const lc = await LikeC4.fromWorkspace({json.dumps(str(model))}, {{ logger: false }});\n"
        "process.stdout.write(JSON.stringify(lc.getErrors()));\n"
    )

    proc = run_module(code)

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == []


def test_line_endings_and_ignores() -> None:
    assert "*.c4 text eol=lf" in (ENGINE / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "node_modules/" in (ENGINE / ".gitignore").read_text(encoding="utf-8").splitlines()
