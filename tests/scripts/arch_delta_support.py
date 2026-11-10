"""Shared helpers for the architecture-delta tests: paths, Node runners and fixture builders."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]
SCRIPT = ENGINE / "skills" / "shared" / "scripts" / "architecture-delta.mjs"
LIB = ENGINE / "skills" / "shared" / "scripts" / "architecture-delta"
SHIPPED_SPEC = ENGINE / "skills" / "shared" / "architecture" / "c4.c4"
LIKEC4_DIR = ENGINE / "node_modules" / "likec4"
LIKEC4_ENTRY = LIKEC4_DIR / "dist" / "index.mjs"
FIXTURES = ENGINE / "tests" / "fixtures" / "architecture"

SHOP_MODEL = """model {
  shop = system 'Shop' {
    orders = container 'Orders' {
      metadata {
        code 'shop.orders'
      }
      api = component 'Orders API' {
        metadata {
          code 'shop.orders.api'
        }
      }
    }
    checkout = container 'Checkout' {
      metadata {
        code 'shop.checkout'
      }
    }
    payments = container 'Payments' {
      #protected
      metadata {
        code 'shop.payments'
      }
      card = component 'Card' {
        metadata {
          code 'shop.payments.card'
        }
      }
    }
    orders -> checkout
    checkout -> payments
  }
}
"""


def require_node() -> None:
    """Fail (never skip) when Node or the pinned likec4 install is missing."""
    if shutil.which("node") is None or not (LIKEC4_DIR / "package.json").is_file():
        raise RuntimeError(
            "architecture-delta tests need Node and node_modules/likec4: run `npm ci` (as `npm ci --ignore-scripts`)"
        )


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def run_module(code: str) -> subprocess.CompletedProcess[str]:
    """Run an ES module snippet written to a temporary file (no command-line length limit)."""
    with tempfile.TemporaryDirectory() as folder:
        snippet = Path(folder) / "snippet.mjs"
        snippet.write_text(code, encoding="utf-8")
        return subprocess.run(
            ["node", str(snippet)], capture_output=True, text=True, encoding="utf-8", timeout=600
        )


def lib_url(module: str) -> str:
    return (LIB / module).as_uri()


def call(module: str, fn: str, *args: object) -> dict:
    """Call an exported function of a tool module; return {ok, value} or {ok, token, details, message}."""
    code = (
        f"import * as m from {json.dumps(lib_url(module))};\n"
        f"const args = {json.dumps(list(args))};\n"
        "try {\n"
        f"  const out = await m.{fn}(...args);\n"
        "  process.stdout.write(JSON.stringify({ ok: true, value: out === undefined ? null : out }));\n"
        "} catch (err) {\n"
        "  process.stdout.write(JSON.stringify({ ok: false, token: err.token ?? null,"
        " details: err.details ?? null, message: String(err.message) }));\n"
        "}\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def load_model(model_dir: Path, entry: Path = LIKEC4_ENTRY) -> dict:
    """Run model.mjs loadModel with the LikeC4 class from `entry`."""
    code = (
        f"import {{ LikeC4 }} from {json.dumps(entry.as_uri())};\n"
        f"import {{ loadModel }} from {json.dumps(lib_url('model.mjs'))};\n"
        "try {\n"
        f"  const out = await loadModel(LikeC4, {json.dumps(str(model_dir))});\n"
        "  process.stdout.write(JSON.stringify({ ok: true, value: out }));\n"
        "} catch (err) {\n"
        "  process.stdout.write(JSON.stringify({ ok: false, token: err.token ?? null,"
        " details: err.details ?? null, message: String(err.message) }));\n"
        "}\n"
    )
    proc = run_module(code)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def run_tool(
    *args: object, preload: Path | None = None, script: Path = SCRIPT, timeout: int = 600
) -> subprocess.CompletedProcess[str]:
    cmd = ["node"]
    if preload is not None:
        cmd += ["--import", preload.as_uri()]
    cmd += [str(script), *[str(a) for a in args]]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)


def error_lines(proc: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in proc.stderr.splitlines() if line.startswith("error: ")]


def make_repo(tmp_path: Path, model: str | None = SHOP_MODEL, *, spec: bool = True) -> Path:
    """A repository folder under tmp_path with docs/architecture/c4.c4 and docs/architecture/model.c4."""
    repo = tmp_path / unique("repo")
    model_dir = repo / "docs" / "architecture"
    model_dir.mkdir(parents=True)
    if spec:
        shutil.copyfile(SHIPPED_SPEC, model_dir / "c4.c4")
    if model is not None:
        (model_dir / "model.c4").write_text(model, encoding="utf-8")
    return repo


def write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def link_dir(target: Path, link: Path) -> None:
    """A directory symlink, or a junction where symlinks need rights the user lacks."""
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, link, target_is_directory=True)
    except OSError:
        import _winapi  # Windows only: junctions need no special rights

        _winapi.CreateJunction(str(target), str(link))


def copy_engine(dest: Path) -> Path:
    """Copy the tool and the shipped spec into dest/engine with no node_modules; return the script."""
    root = dest / "engine"
    shutil.copytree(LIB, root / "skills" / "shared" / "scripts" / "architecture-delta")
    shutil.copyfile(SCRIPT, root / "skills" / "shared" / "scripts" / "architecture-delta.mjs")
    (root / "skills" / "shared" / "architecture").mkdir(parents=True)
    shutil.copyfile(SHIPPED_SPEC, root / "skills" / "shared" / "architecture" / "c4.c4")
    return root / "skills" / "shared" / "scripts" / "architecture-delta.mjs"


def make_shim(node_modules: Path, version: object = "1.59.0", source: str | None = None,
              package: dict | None = None) -> Path:
    """A fake likec4 package; by default it re-exports the engine's installed copy."""
    pkg = node_modules / "likec4"
    pkg.mkdir(parents=True)
    manifest = package if package is not None else {
        "name": "likec4", "version": version, "exports": {".": {"import": "./index.mjs"}}
    }
    write_json(pkg / "package.json", manifest)
    text = source if source is not None else f"export * from {json.dumps(LIKEC4_ENTRY.as_uri())};\n"
    (pkg / "index.mjs").write_text(text, encoding="utf-8")
    return pkg
