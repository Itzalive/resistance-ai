#!/usr/bin/env python3
"""Append validated entries to .review_log.jsonl and .run_records.jsonl.

The schema is documented in ../review-log-jsonl.md. Standard library only.

  review-log.py append --item-id ID --skill SKILL --phase PHASE --round N
      --verdict VERDICT --orchestrator MODEL --reviewer-model MODEL
      --independence LEVEL [--finding SEVERITY:KIND:TEXT ...] [--tokens N]
      [--reason TEXT] [--log PATH]

  review-log.py run-record --from FILE|- [--log PATH]

Exit codes: 0 written, 2 invalid input (nothing written).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILLS = (
    "specifying-epics",
    "specifying-work-items",
    "writing-plans",
    "subagent-driven-development",
    "executing-plans",
    "requesting-code-review",
    "survivability",
    "finishing-a-development-branch",
)
SELF_PHASES = ("EPIC_REVIEW", "SPEC_REVIEW", "PLAN_SELF_REVIEW")
REVIEWER_PHASES = ("INDEPENDENT_AUDIT", "PLAN_REVIEW", "CHECKPOINT_REVIEW", "CODE_REVIEW")
PHASES = SELF_PHASES + REVIEWER_PHASES + ("SURVIVABILITY",)
VERDICTS = ("APPROVED", "REJECTED", "PASS", "FAIL")
INDEPENDENCE = ("self", "fresh-context", "cross-family")
SEVERITIES = ("critical", "important", "minor")
KINDS = ("missed-caller", "weak-test", "plan-hole", "spec-hole", "real-bug", "slip", "wording")
LAYERS = ("self-review", "spec-audit", "plan-review", "checkpoint", "code-review", "survivability")
RUN_RECORD_FIELDS = (
    "item_id",
    "plan",
    "tasks",
    "tiers",
    "escalations",
    "attempts",
    "tokens",
    "findings",
    "plan_changes",
    "slips",
)


class InvalidEntry(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidEntry(message)


def one_of(name: str, value: str, allowed: tuple[str, ...]) -> str:
    require(value in allowed, f"{name} must be one of {', '.join(allowed)}; got {value!r}")
    return value


def non_empty(name: str, value: object) -> str:
    require(isinstance(value, str) and value.strip() != "", f"{name} must be a non-empty string")
    return value  # type: ignore[return-value]


def count(name: str, value: object, minimum: int = 0) -> int:
    require(
        isinstance(value, int) and not isinstance(value, bool) and value >= minimum,
        f"{name} must be an integer >= {minimum}; got {value!r}",
    )
    return value  # type: ignore[return-value]


def parse_finding(raw: str) -> dict[str, str]:
    parts = raw.split(":", 2)
    require(len(parts) == 3, f"finding must be SEVERITY:KIND:TEXT; got {raw!r}")
    severity, kind, text = parts
    return {
        "severity": one_of("finding severity", severity, SEVERITIES),
        "kind": one_of("finding kind", kind, KINDS),
        "text": non_empty("finding text", text),
    }


def build_entry(args: argparse.Namespace) -> dict[str, object]:
    phase = one_of("phase", args.phase, PHASES)
    independence = one_of("independence", args.independence, INDEPENDENCE)
    if phase in SELF_PHASES:
        require(independence == "self", f"independence must be 'self' for {phase}")
    if phase in REVIEWER_PHASES:
        require(independence != "self", f"independence must not be 'self' for {phase}")
    findings = [parse_finding(raw) for raw in args.finding]
    verdict = one_of("verdict", args.verdict, VERDICTS)
    if verdict in ("REJECTED", "FAIL"):
        require(findings != [], f"a {verdict} verdict needs at least one --finding")
    entry: dict[str, object] = {
        "ts": now(),
        "item_id": non_empty("item_id", args.item_id),
        "skill": one_of("skill", args.skill, SKILLS),
        "phase": phase,
        "round": count("round", args.round, minimum=1),
        "verdict": verdict,
        "orchestrator": non_empty("orchestrator", args.orchestrator),
        "reviewer_model": non_empty("reviewer_model", args.reviewer_model),
        "independence": independence,
        "findings": findings,
    }
    if args.tokens is not None:
        entry["tokens"] = count("tokens", args.tokens)
    if args.reason is not None:
        entry["reason"] = args.reason
    return entry


def counts_map(name: str, value: object) -> dict[str, int]:
    require(isinstance(value, dict), f"{name} must be an object")
    for key, n in value.items():  # type: ignore[union-attr]
        non_empty(f"{name} key", key)
        count(f"{name}[{key}]", n)
    return value  # type: ignore[return-value]


def string_list(name: str, value: object) -> list[str]:
    require(isinstance(value, list), f"{name} must be a list")
    for item in value:  # type: ignore[union-attr]
        non_empty(f"{name} item", item)
    return value  # type: ignore[return-value]


def validate_run_record(record: object) -> dict[str, object]:
    require(isinstance(record, dict), "run record must be a JSON object")
    missing = [field for field in RUN_RECORD_FIELDS if field not in record]  # type: ignore[operator]
    require(missing == [], f"run record is missing: {', '.join(missing)}")
    unknown = [field for field in record if field not in RUN_RECORD_FIELDS]  # type: ignore[union-attr]
    require(unknown == [], f"run record has unknown fields: {', '.join(unknown)}")
    non_empty("item_id", record["item_id"])  # type: ignore[index]
    non_empty("plan", record["plan"])  # type: ignore[index]
    count("tasks", record["tasks"])  # type: ignore[index]
    counts_map("tiers", record["tiers"])  # type: ignore[index]
    counts_map("attempts", record["attempts"])  # type: ignore[index]
    counts_map("tokens", record["tokens"])  # type: ignore[index]
    escalations = record["escalations"]  # type: ignore[index]
    require(isinstance(escalations, list), "escalations must be a list")
    for escalation in escalations:
        require(isinstance(escalation, dict), "each escalation must be an object")
        for field in ("task", "from", "to", "reason"):
            non_empty(f"escalation {field}", escalation.get(field))
    findings = record["findings"]  # type: ignore[index]
    require(isinstance(findings, dict), "findings must be an object of layer -> kind -> count")
    for layer, kinds in findings.items():
        one_of("findings layer", layer, LAYERS)
        counts_map(f"findings[{layer}]", kinds)
        for kind in kinds:
            one_of("finding kind", kind, KINDS)
    string_list("plan_changes", record["plan_changes"])  # type: ignore[index]
    string_list("slips", record["slips"])  # type: ignore[index]
    return {"ts": now(), **record}  # type: ignore[dict-item]


def append_line(path: Path, entry: dict[str, object]) -> None:
    line = json.dumps(entry, ensure_ascii=False)
    needs_newline = path.exists() and path.stat().st_size > 0 and not path.read_bytes().endswith(b"\n")
    with path.open("a", encoding="utf-8", newline="\n") as log:
        if needs_newline:
            log.write("\n")
        log.write(line + "\n")


def read_json(source: str) -> object:
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise InvalidEntry(f"run record is not valid JSON: {error}") from error


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = root.add_subparsers(dest="command", required=True)

    append = commands.add_parser("append", help="append one review entry")
    append.add_argument("--item-id", required=True)
    append.add_argument("--skill", required=True)
    append.add_argument("--phase", required=True)
    append.add_argument("--round", required=True, type=int)
    append.add_argument("--verdict", required=True)
    append.add_argument("--orchestrator", required=True)
    append.add_argument("--reviewer-model", required=True)
    append.add_argument("--independence", required=True)
    append.add_argument("--finding", action="append", default=[], metavar="SEVERITY:KIND:TEXT")
    append.add_argument("--tokens", type=int)
    append.add_argument("--reason")
    append.add_argument("--log", default=".review_log.jsonl")

    run_record = commands.add_parser("run-record", help="append one per-plan run record")
    run_record.add_argument("--from", dest="source", required=True, metavar="FILE|-")
    run_record.add_argument("--log", default=".run_records.jsonl")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "append":
            entry = build_entry(args)
        else:
            entry = validate_run_record(read_json(args.source))
    except InvalidEntry as error:
        print(f"review-log: {error}", file=sys.stderr)
        return 2
    append_line(Path(args.log), entry)
    print(json.dumps(entry, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
