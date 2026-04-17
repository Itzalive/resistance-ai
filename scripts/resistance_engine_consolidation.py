from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import TypedDict

CONSOLIDATION_OVERRIDE_RELATIVE_PATH = Path("consolidation") / "consolidation_overrides.json"
VALID_LOCAL_SYNC_POLICIES = frozenset({"required", "pruned"})


class ConsolidationOverride(TypedDict):
    entry_id: str
    source_file: str
    local_sync_policy: str


def load_consolidation_overrides(output_root: Path) -> tuple[list[ConsolidationOverride], str | None]:
    override_path = output_root / CONSOLIDATION_OVERRIDE_RELATIVE_PATH
    if not override_path.exists():
        return [], None

    raw_text = override_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw_text)
    except JSONDecodeError as exc:
        raise ValueError("invalid JSON in consolidation overrides") from exc

    if not isinstance(payload, list):
        raise ValueError("consolidation overrides must be a JSON list")

    overrides: list[ConsolidationOverride] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"override entry {index} must be a JSON object")

        entry_id = item.get("entry_id")
        source_file = item.get("source_file")
        local_sync_policy = item.get("local_sync_policy")
        if not isinstance(entry_id, str) or not isinstance(source_file, str):
            raise ValueError(f"override entry {index} must include string entry_id and source_file")
        if local_sync_policy not in VALID_LOCAL_SYNC_POLICIES:
            raise ValueError(
                f"override entry {index} has invalid local_sync_policy: {local_sync_policy!r}"
            )

        overrides.append(
            {
                "entry_id": entry_id,
                "source_file": source_file,
                "local_sync_policy": local_sync_policy,
            }
        )

    return overrides, raw_text


def write_consolidation_override_text(output_root: Path, raw_text: str | None) -> None:
    if raw_text is None:
        return

    override_path = output_root / CONSOLIDATION_OVERRIDE_RELATIVE_PATH
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_path.write_text(raw_text, encoding="utf-8")


def build_policy_index(
    overrides: list[ConsolidationOverride], *, valid_targets: set[tuple[str, str]]
) -> dict[tuple[str, str], str]:
    policy_index: dict[tuple[str, str], str] = {}
    for override in overrides:
        key = (override["entry_id"], override["source_file"])
        if key not in valid_targets:
            raise ValueError(
                f"override references unknown imported file: {override['entry_id']} -> {override['source_file']}"
            )
        policy_index[key] = override["local_sync_policy"]
    return policy_index
