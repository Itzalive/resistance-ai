"""Bump the release version across every packaging manifest.

Usage:
    python scripts/bump_version.py 1.6.0
    python scripts/bump_version.py minor        # major | minor | patch
    python scripts/bump_version.py --check      # report versions, fail if they disagree
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
PROJECT_NAME = "resistance-ai"


def _json_top(path: Path):
    def read() -> str:
        return json.loads(path.read_text(encoding="utf-8"))["version"]

    def write(text: str, version: str) -> str:
        return re.sub(r'^(  "version": ")[^"]+(")', rf"\g<1>{version}\g<2>", text, count=1, flags=re.M)

    return read, write


def _marketplace(path: Path):
    def read() -> str:
        plugins = json.loads(path.read_text(encoding="utf-8"))["plugins"]
        return next(p["version"] for p in plugins if p["name"] == "resistance-engine")

    def write(text: str, version: str) -> str:
        return re.sub(
            r'("name": "resistance-engine",(?:[^{}]*?)"version": ")[^"]+(")',
            rf"\g<1>{version}\g<2>",
            text,
            count=1,
            flags=re.S,
        )

    return read, write


def _toml_project(path: Path, header: str):
    pattern = re.compile(rf'({re.escape(header)}\s*\n(?:name = "{PROJECT_NAME}"\s*\n)?version = ")[^"]+(")')

    def read() -> str:
        match = pattern.search(path.read_text(encoding="utf-8"))
        if not match:
            raise ValueError(f"no version found in {path}")
        return re.search(r'version = "([^"]+)"', match.group(0)).group(1)

    def write(text: str, version: str) -> str:
        return pattern.sub(rf"\g<1>{version}\g<2>", text, count=1)

    return read, write


TARGETS = {
    ROOT / "package.json": _json_top(ROOT / "package.json"),
    ROOT / ".claude-plugin" / "plugin.json": _json_top(ROOT / ".claude-plugin" / "plugin.json"),
    ROOT / ".claude-plugin" / "marketplace.json": _marketplace(ROOT / ".claude-plugin" / "marketplace.json"),
    ROOT / "pyproject.toml": _toml_project(ROOT / "pyproject.toml", "[project]\nname = \"resistance-ai\""),
    ROOT / "uv.lock": _toml_project(ROOT / "uv.lock", "[[package]]\nname = \"resistance-ai\""),
}


def current_versions() -> dict[Path, str]:
    return {path: read() for path, (read, _) in TARGETS.items()}


def next_version(current: str, part: str) -> str:
    major, minor, patch = (int(n) for n in current.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(n) for n in version.split("."))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("version", nargs="?", help="explicit X.Y.Z, or major/minor/patch")
    parser.add_argument("--check", action="store_true", help="only report versions; exit 1 if they disagree")
    args = parser.parse_args(argv)

    versions = current_versions()
    for path, version in versions.items():
        print(f"  {version:<10} {path.relative_to(ROOT).as_posix()}")

    if args.check or not args.version:
        return 0 if len(set(versions.values())) == 1 else 1

    if args.version in ("major", "minor", "patch"):
        # Manifests have drifted before; bump from the highest one.
        target = next_version(max(versions.values(), key=_key), args.version)
    elif SEMVER.match(args.version):
        target = args.version
    else:
        parser.error(f"not a version: {args.version}")

    for path, (read, write) in TARGETS.items():
        text = path.read_text(encoding="utf-8")
        updated = write(text, target)
        if updated == text and read() != target:
            raise SystemExit(f"failed to update {path}")
        path.write_text(updated, encoding="utf-8", newline="")
        if read() != target:
            raise SystemExit(f"verification failed for {path}")

    print(f"-> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
