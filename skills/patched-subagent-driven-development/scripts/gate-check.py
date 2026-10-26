#!/usr/bin/env python3
"""Check a plan against a spec's acceptance table.

Usage:
  python gate-check.py --spec SPEC --plan PLAN [--json] [--strict]

Checks:
  1. Every acceptance ID in the spec has exactly one coverage row in the plan.
  2. Every coverage row names a task and evidence.
  3. Every task declares a Type (apply/build) -- warning unless --strict.
  4. The plan's Spec hash matches the spec's sha256 -- warning unless --strict.
  5. The spec status is Approved; the plan has a Definition of Done.

Exit: 0 pass, 1 fail, 2 input error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SPEC_ID = re.compile(r"^\|\s*(A\d+)\s*\|(.*)$")
COVERAGE_ID = re.compile(r"^\|\s*(A\d+)\s*\|\s*([^|]*)\|\s*([^|]*)\|")
TASK_HEAD = re.compile(r"^###\s+Task\s+(\d+)\b")
TASK_TYPE = re.compile(r"\*\*Type:\*\*\s*(apply|build)", re.IGNORECASE)
HASH_LINE = re.compile(r"\*\*Spec hash:\*\*\s*(?:sha256:)?([0-9a-fA-F]{12,64})")
SPEC_STATUS = re.compile(r"\*\*Status:\*\*\s*(.+)", re.IGNORECASE)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def spec_ids(text: str) -> list[str]:
    ids: list[str] = []
    for line in text.splitlines():
        m = SPEC_ID.match(line.strip())
        if m:
            ids.append(m.group(1))
    return ids


def parse_plan(text: str) -> dict:
    lines = text.splitlines()
    hash_value = None
    for line in lines:
        m = HASH_LINE.search(line)
        if m:
            hash_value = m.group(1).lower()
            break

    coverage: list[tuple[str, str, str]] = []
    in_coverage = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_coverage = "spec coverage" in stripped.lower()
            continue
        if in_coverage:
            m = COVERAGE_ID.match(stripped)
            if m:
                coverage.append((m.group(1), m.group(2).strip(), m.group(3).strip()))

    tasks: dict[str, str | None] = {}
    current = None
    for line in lines:
        m = TASK_HEAD.match(line.strip())
        if m:
            current = m.group(1)
            tasks[current] = None
            continue
        if current is not None:
            tm = TASK_TYPE.search(line)
            if tm:
                tasks[current] = tm.group(1).lower()
    return {"hash": hash_value, "coverage": coverage, "tasks": tasks}


def has_section(text: str, name: str) -> bool:
    target = name.lower()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and target in stripped.lower():
            return True
    return False


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    spec_path = Path(args.spec)
    plan_path = Path(args.plan)
    try:
        spec_text = read(spec_path)
        plan_text = read(plan_path)
    except OSError as exc:
        print(f"gate-check: INPUT ERROR: {exc}", file=sys.stderr)
        return 2

    sids = spec_ids(spec_text)
    parsed = parse_plan(plan_text)
    cids = [row[0] for row in parsed["coverage"]]
    tasks = parsed["tasks"]

    missing = [i for i in sids if i not in cids]
    extra = [i for i in cids if i not in sids]
    empty = [row[0] for row in parsed["coverage"] if not row[1] or not row[2]]
    no_type = [t for t, v in tasks.items() if v is None]
    spec_hash = sha256_file(spec_path)

    status_match = SPEC_STATUS.search(spec_text)
    spec_status = status_match.group(1).strip() if status_match else None
    spec_approved = bool(spec_status) and "approved" in spec_status.lower()
    dod = has_section(plan_text, "definition of done")

    hash_status = "MISSING"
    if parsed["hash"]:
        given = parsed["hash"]
        hash_status = "MATCH" if spec_hash.startswith(given) else "MISMATCH"

    errors: list[str] = []
    warnings: list[str] = []
    if not sids:
        errors.append("no acceptance table (IDs like | A1 | ... |) in the spec")
    if missing:
        errors.append("unmapped acceptance IDs: " + ", ".join(missing))
    if extra:
        errors.append("coverage IDs not in the spec: " + ", ".join(extra))
    if empty:
        errors.append("coverage rows without task/evidence: " + ", ".join(empty))
    if hash_status == "MISMATCH":
        errors.append(f"spec hash mismatch: plan says {parsed['hash']}, spec is {spec_hash[:12]}")
    elif hash_status == "MISSING":
        (errors if args.strict else warnings).append("plan has no **Spec hash:** line")
    if no_type:
        (errors if args.strict else warnings).append("tasks without **Type:**: " + ", ".join(no_type))
    if spec_status is None:
        (errors if args.strict else warnings).append("spec has no **Status:** line (expected Approved)")
    elif not spec_approved:
        errors.append(f"spec status is not Approved: {spec_status!r}")
    if not dod:
        (errors if args.strict else warnings).append("plan has no ## Definition of Done section")

    ok = not errors
    result = {
        "ok": ok,
        "spec": str(spec_path),
        "plan": str(plan_path),
        "spec_sha256": spec_hash,
        "acceptance_ids": sids,
        "coverage_rows": len(cids),
        "missing": missing,
        "extra": extra,
        "empty_evidence": empty,
        "tasks": len(tasks),
        "tasks_without_type": no_type,
        "spec_status": spec_status,
        "definition_of_done": dod,
        "hash_status": hash_status,
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"gate-check: {'PASS' if ok else 'FAIL'}")
        print(f"  spec: {spec_path} (sha256 {spec_hash[:12]})")
        print(f"  plan: {plan_path}")
        print(f"  acceptance IDs: {len(sids)}" + (f" ({', '.join(sids)})" if sids else ""))
        print(f"  coverage rows: {len(cids)}")
        print(f"  spec hash: {hash_status}")
        print(f"  spec status: {spec_status!r}; definition of done: {dod}")
        print(f"  tasks: {len(tasks)}; without type: {len(no_type)}")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN: {w}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
