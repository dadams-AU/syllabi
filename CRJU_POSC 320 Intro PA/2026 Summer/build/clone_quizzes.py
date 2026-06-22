#!/usr/bin/env python3
"""Clone the 10 module quizzes (with full question banks) from last year's 10-week
course (3548509) into the new 5-week Summer Session B 2026 course (3579296), with
updated due/unlock/lock dates. Settings (time limit, attempts, etc.) are read from
the source quiz rather than hardcoded, so this stays faithful to what's already
proven to work.
"""
from __future__ import annotations

import argparse
import json
import sys

from canvas_common import (
    SOURCE_COURSE_ID,
    TARGET_COURSE_ID,
    WEEK_DATES,
    canvas_get_all,
    canvas_request,
    iso,
    load_ids,
    merge_ids,
)

QUIZ_POINTS_POSSIBLE = 10.0  # matches the source gradebook (equal weight per quiz)

# (source_quiz_id, week_number)
SOURCE_QUIZZES: tuple[tuple[int, int], ...] = (
    (9061287, 1),  # Module 1 Quiz: Intro and Overview
    (9061292, 1),  # Module 2 Quiz: Basics and Eras
    (9061283, 2),  # Quiz Module 3: What Government Does
    (9061290, 2),  # Quiz Module 4: Organizational Theory and Organizational Problems
    (9061288, 3),  # Module 5 Quiz: Executive and Admin Reform
    (9061286, 3),  # Module 6 Quiz: Civil Service and Human Capital
    (9061291, 4),  # Module 7 Quiz: Decision Making and Budgeting
    (9061285, 4),  # Module 8 Quiz: Implementation and Performance
    (9061284, 5),  # Module 9 Quiz: Regulation and Oversight
    (9061289, 5),  # Module 10 Quiz: Accountability
)


def quizzes_group_id(course_id: str) -> int:
    ids = load_ids()
    group_id = ids.get("assignment_groups", {}).get("Quizzes")
    if group_id:
        return int(group_id)
    groups = canvas_get_all("/api/v1/courses/{course_id}/assignment_groups", course_id)
    for g in groups:
        if g["name"] == "Quizzes":
            return g["id"]
    raise RuntimeError("Quizzes assignment group not found - run setup_assignment_groups.py first")


def clone_one_quiz(source_quiz_id: int, week: int, group_id: int, dry_run: bool) -> dict[str, object]:
    source = canvas_request(
        "GET",
        "/api/v1/courses/{course_id}/quizzes/" + str(source_quiz_id),
        course_id=SOURCE_COURSE_ID,
    )
    title = source["title"].strip()
    questions = canvas_get_all(
        "/api/v1/courses/{course_id}/quizzes/" + str(source_quiz_id) + "/questions",
        SOURCE_COURSE_ID,
    )

    dates = WEEK_DATES[week]
    quiz_params = [
        ("quiz[title]", title),
        ("quiz[quiz_type]", "assignment"),
        ("quiz[assignment_group_id]", str(group_id)),
        ("quiz[time_limit]", str(source.get("time_limit") or "")),
        ("quiz[shuffle_answers]", "1" if source.get("shuffle_answers") else "0"),
        ("quiz[allowed_attempts]", str(source.get("allowed_attempts", 1))),
        ("quiz[one_question_at_a_time]", "1" if source.get("one_question_at_a_time") else "0"),
        ("quiz[scoring_policy]", source.get("scoring_policy", "keep_highest")),
        ("quiz[show_correct_answers]", "1" if source.get("show_correct_answers") else "0"),
        ("quiz[points_possible]", f"{QUIZ_POINTS_POSSIBLE:g}"),
        ("quiz[due_at]", iso(dates["due_at"])),
        ("quiz[unlock_at]", iso(dates["unlock_at"])),
        ("quiz[lock_at]", iso(dates["lock_at"])),
    ]

    if dry_run:
        print(f"DRY RUN: clone quiz {title!r} (week {week}, {len(questions)} questions)")
        for k, v in quiz_params:
            print(f"    {k} = {v}")
        return {"title": title, "question_count": len(questions)}

    created = canvas_request(
        "POST",
        "/api/v1/courses/{course_id}/quizzes",
        quiz_params,
        course_id=TARGET_COURSE_ID,
    )
    new_quiz_id = created["id"]

    for q in questions:
        answer_params: list[tuple[str, str]] = []
        for i, answer in enumerate(q.get("answers", [])):
            answer_params.append((f"question[answers][{i}][answer_text]", answer["text"]))
            answer_params.append((f"question[answers][{i}][answer_weight]", str(answer["weight"])))

        question_params = [
            ("question[question_name]", q.get("question_name", "Question")),
            ("question[question_text]", q.get("question_text", "")),
            ("question[question_type]", q.get("question_type", "multiple_choice_question")),
            ("question[points_possible]", str(q.get("points_possible", 1))),
            *answer_params,
        ]
        canvas_request(
            "POST",
            f"/api/v1/courses/{{course_id}}/quizzes/{new_quiz_id}/questions",
            question_params,
            course_id=TARGET_COURSE_ID,
        )

    # Canvas recalculates quiz/assignment points_possible from question totals once
    # questions are added; force it back to the equal-weight value used last year.
    canvas_request(
        "PUT",
        "/api/v1/courses/{course_id}/quizzes/" + str(new_quiz_id),
        [("quiz[points_possible]", f"{QUIZ_POINTS_POSSIBLE:g}")],
        course_id=TARGET_COURSE_ID,
    )

    return {"title": title, "new_quiz_id": new_quiz_id, "question_count": len(questions)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    group_id = quizzes_group_id(TARGET_COURSE_ID)

    existing_titles = set()
    if not args.dry_run:
        existing_titles = {
            q["title"].strip() for q in canvas_get_all("/api/v1/courses/{course_id}/quizzes", TARGET_COURSE_ID)
        }

    results: list[dict[str, object]] = []
    skipped: list[str] = []
    quiz_ids: dict[str, int] = {}

    for source_quiz_id, week in SOURCE_QUIZZES:
        source = canvas_request(
            "GET",
            "/api/v1/courses/{course_id}/quizzes/" + str(source_quiz_id),
            course_id=SOURCE_COURSE_ID,
        )
        title = source["title"].strip()

        if title in existing_titles:
            skipped.append(title)
            continue

        result = clone_one_quiz(source_quiz_id, week, group_id, args.dry_run)
        results.append(result)
        if "new_quiz_id" in result:
            quiz_ids[result["title"]] = result["new_quiz_id"]

    if not args.dry_run and quiz_ids:
        merge_ids("quizzes", quiz_ids)

    print(json.dumps({"created": results, "skipped_existing": skipped}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
