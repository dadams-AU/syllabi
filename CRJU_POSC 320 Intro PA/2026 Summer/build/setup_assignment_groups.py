#!/usr/bin/env python3
"""Create the 4 weighted assignment groups for CRJU/POSC 320 Summer Session B 2026."""
from __future__ import annotations

import argparse
import json
import sys

from canvas_common import TARGET_COURSE_ID, canvas_get_all, canvas_request, merge_ids

GROUPS: tuple[tuple[str, float], ...] = (
    ("Management Brief Project", 45.0),
    ("Quizzes", 30.0),
    ("Discussion Posts", 15.0),
    ("Research Log", 10.0),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-id", default=TARGET_COURSE_ID)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    existing = canvas_get_all(
        "/api/v1/courses/{course_id}/assignment_groups", args.course_id
    )
    existing_by_name = {g["name"]: g for g in existing}

    created: list[dict[str, object]] = []
    skipped: list[str] = []
    ids: dict[str, int] = {}

    for position, (name, weight) in enumerate(GROUPS, start=1):
        if name in existing_by_name:
            skipped.append(name)
            ids[name] = existing_by_name[name]["id"]
            continue

        if args.dry_run:
            print(f"DRY RUN: create group {name!r} weight={weight} position={position}")
            continue

        response = canvas_request(
            "POST",
            "/api/v1/courses/{course_id}/assignment_groups",
            [
                ("name", name),
                ("group_weight", f"{weight:g}"),
                ("position", str(position)),
            ],
            course_id=args.course_id,
        )
        ids[name] = response["id"]
        created.append({"name": name, "weight": weight, "id": response["id"]})

    if not args.dry_run:
        merge_ids("assignment_groups", ids)

    print(
        json.dumps(
            {"created": created, "skipped_existing": skipped, "ids": ids},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
