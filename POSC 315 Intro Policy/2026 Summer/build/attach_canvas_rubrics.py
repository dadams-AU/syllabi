#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_COURSE_ID = "3579299"


@dataclass(frozen=True)
class Criterion:
    description: str
    points: float
    long_description: str


@dataclass(frozen=True)
class RubricSpec:
    assignment_id: int
    assignment_name: str
    title: str
    criteria: tuple[Criterion, ...]


RUBRICS: tuple[RubricSpec, ...] = (
    RubricSpec(
        assignment_id=39703220,
        assignment_name="Policy Problem Proposal",
        title="Policy Problem Proposal Rubric",
        criteria=(
            Criterion(
                "Policy problem",
                3,
                "Identifies a clear public policy problem appropriate for analysis.",
            ),
            Criterion(
                "Significance",
                2,
                "Explains why the problem matters in public policy terms.",
            ),
            Criterion(
                "Policy actors",
                2,
                "Identifies the principal policy actors involved in the problem.",
            ),
            Criterion(
                "Memo organization and clarity",
                2,
                "Presents the proposal as a focused 1-page memo with clear organization and readable prose.",
            ),
            Criterion(
                "Google Doc submission",
                1,
                "Submits the shareable Google Doc link and ensures the instructor has Editor access.",
            ),
        ),
    ),
    RubricSpec(
        assignment_id=39703221,
        assignment_name="Problem Definition Memo",
        title="Problem Definition Memo Rubric",
        criteria=(
            Criterion(
                "Problem definition",
                4,
                "Clearly defines the chosen policy problem.",
            ),
            Criterion(
                "Policy context",
                3,
                "Includes relevant policy context needed to understand the problem.",
            ),
            Criterion(
                "Stakeholders",
                3,
                "Identifies and explains key stakeholders connected to the problem.",
            ),
            Criterion(
                "Memo organization and clarity",
                3,
                "Presents a coherent 1-2 page memo with clear structure and readable prose.",
            ),
            Criterion(
                "Google Doc submission",
                2,
                "Submits the shareable Google Doc link and ensures the instructor has Editor access.",
            ),
        ),
    ),
    RubricSpec(
        assignment_id=39703222,
        assignment_name="Alternatives and Evaluation Matrix",
        title="Alternatives and Evaluation Matrix Rubric",
        criteria=(
            Criterion(
                "Policy alternatives",
                4,
                "Summarizes at least three possible solutions to the policy problem.",
            ),
            Criterion(
                "Evaluation matrix",
                3,
                "Organizes the alternatives in a matrix that supports comparison.",
            ),
            Criterion(
                "Evaluation criteria narrative",
                3,
                "Provides a half-page to one-page narrative explaining the evaluation criteria.",
            ),
            Criterion(
                "Policy analysis",
                3,
                "Connects alternatives and criteria to the policy problem in a reasoned way.",
            ),
            Criterion(
                "Clarity and submission",
                2,
                "Uses clear prose and submits the shareable Google Doc link with Editor access.",
            ),
        ),
    ),
    RubricSpec(
        assignment_id=39703223,
        assignment_name="Draft Policy Memo",
        title="Draft Policy Memo Rubric",
        criteria=(
            Criterion(
                "Required memo components",
                4,
                "Combines the Executive Summary, Problem Definition, Alternatives Matrix, and preliminary Recommendation.",
            ),
            Criterion(
                "Problem and alternatives analysis",
                3,
                "Develops the problem definition and alternatives in a connected draft memo.",
            ),
            Criterion(
                "Preliminary recommendation",
                3,
                "Includes a preliminary recommendation supported by the draft analysis.",
            ),
            Criterion(
                "Google Doc process",
                2,
                "Continues in the same Google Doc and uses Suggesting mode so edits are visible.",
            ),
            Criterion(
                "Memo organization and clarity",
                3,
                "Presents a coherent 3-4 page draft memo with clear organization and readable prose.",
            ),
        ),
    ),
    RubricSpec(
        assignment_id=39703224,
        assignment_name="Final Policy Memo",
        title="Final Policy Memo Rubric",
        criteria=(
            Criterion(
                "Revision in response to feedback",
                5,
                "Revises the memo in response to instructor feedback.",
            ),
            Criterion(
                "Problem and executive summary",
                4,
                "Presents a clear executive summary and problem definition.",
            ),
            Criterion(
                "Alternatives and recommendation",
                5,
                "Uses the alternatives matrix and analysis to support a final recommendation.",
            ),
            Criterion(
                "Policy analysis",
                3,
                "Applies course concepts and policy analysis reasoning to the chosen problem.",
            ),
            Criterion(
                "Final memo format and submission",
                3,
                "Produces a clean 4-5 page final memo at the top of the Google Doc and submits the shareable link with Editor access.",
            ),
        ),
    ),
    RubricSpec(
        assignment_id=39703225,
        assignment_name="Final Reflection",
        title="Final Reflection Rubric",
        criteria=(
            Criterion(
                "Public policy learning",
                1,
                "Reflects on what was learned about public policy.",
            ),
            Criterion(
                "Policy analysis learning",
                1,
                "Reflects on what was learned about policy analysis.",
            ),
            Criterion(
                "Writing process",
                1,
                "Reflects on the student's own writing process.",
            ),
            Criterion(
                "Personal reflection",
                1,
                "Offers a personal and specific reflection rather than only a summary.",
            ),
            Criterion(
                "Clarity and completion",
                1,
                "Submits a clear 1-page reflection.",
            ),
        ),
    ),
)


def env(name: str, fallback: str | None = None) -> str | None:
    return os.environ.get(name) or (os.environ.get(fallback) if fallback else None)


def canvas_request(
    method: str,
    course_id: str,
    path: str,
    params: list[tuple[str, str]] | None = None,
) -> Any:
    base_url = env("CANVAS_BASE_URL", "canvas_base_url")
    token = env("CANVAS_TOKEN", "canvas_token")
    if not base_url:
        raise RuntimeError("Missing CANVAS_BASE_URL")
    if not token:
        raise RuntimeError("Missing CANVAS_TOKEN")

    url = f"{base_url.rstrip('/')}/{path.lstrip('/').format(course_id=course_id)}"
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if method == "GET" and params:
        parsed = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        query.extend(params)
        url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))
    elif params:
        data = urllib.parse.urlencode(params).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {body}") from e
    return json.loads(body) if body else None


def assignment_has_rubric(course_id: str, assignment_id: int) -> bool:
    assignment = canvas_request(
        "GET",
        course_id,
        "/api/v1/courses/{course_id}/assignments/" + str(assignment_id),
        [("include[]", "rubric")],
    )
    return bool(assignment.get("rubric"))


def assignment_name(course_id: str, assignment_id: int) -> str:
    assignment = canvas_request(
        "GET",
        course_id,
        "/api/v1/courses/{course_id}/assignments/" + str(assignment_id),
    )
    return str(assignment.get("name", ""))


def rating_rows(points: float) -> tuple[tuple[str, float, str], ...]:
    return (
        ("Exceeds expectations", points, "Complete, specific, and well developed."),
        ("Meets expectations", round(points * 0.85, 2), "Satisfies the criterion with minor room for improvement."),
        ("Developing", round(points * 0.65, 2), "Partially satisfies the criterion but needs revision or more detail."),
        ("Not yet", 0, "Does not yet satisfy the criterion."),
    )


def params_for(spec: RubricSpec) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = [
        ("rubric[title]", spec.title),
        ("rubric[free_form_criterion_comments]", "0"),
        ("rubric_association[association_id]", str(spec.assignment_id)),
        ("rubric_association[association_type]", "Assignment"),
        ("rubric_association[use_for_grading]", "1"),
        ("rubric_association[purpose]", "grading"),
    ]
    for index, criterion in enumerate(spec.criteria):
        prefix = f"rubric[criteria][{index}]"
        params.extend(
            [
                (f"{prefix}[description]", criterion.description),
                (f"{prefix}[long_description]", criterion.long_description),
                (f"{prefix}[points]", f"{criterion.points:g}"),
                (f"{prefix}[criterion_use_range]", "0"),
            ]
        )
        for rating_index, (rating, points, long_description) in enumerate(rating_rows(criterion.points)):
            rating_prefix = f"{prefix}[ratings][{rating_index}]"
            params.extend(
                [
                    (f"{rating_prefix}[description]", rating),
                    (f"{rating_prefix}[long_description]", long_description),
                    (f"{rating_prefix}[points]", f"{points:g}"),
                ]
            )
    return params


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-id", default=DEFAULT_COURSE_ID)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    created: list[dict[str, Any]] = []
    skipped_existing: list[str] = []
    for spec in RUBRICS:
        total = sum(c.points for c in spec.criteria)
        if args.dry_run:
            print(f"DRY RUN: {spec.assignment_name} -> {spec.title} ({total:g} pts)")
            for criterion in spec.criteria:
                print(f"  - {criterion.description}: {criterion.points:g}")
            continue

        actual_name = assignment_name(args.course_id, spec.assignment_id)
        if actual_name != spec.assignment_name:
            raise RuntimeError(
                f"Assignment ID {spec.assignment_id} expected {spec.assignment_name!r}, "
                f"but Canvas returned {actual_name!r}"
            )

        if assignment_has_rubric(args.course_id, spec.assignment_id):
            skipped_existing.append(spec.assignment_name)
            continue

        response = canvas_request(
            "POST",
            args.course_id,
            "/api/v1/courses/{course_id}/rubrics",
            params_for(spec),
        )
        created.append(
            {
                "assignment_id": spec.assignment_id,
                "assignment_name": spec.assignment_name,
                "rubric_title": spec.title,
                "rubric_id": response.get("rubric", {}).get("id") if isinstance(response, dict) else None,
            }
        )

    print(
        json.dumps(
            {
                "created_count": len(created),
                "skipped_existing_count": len(skipped_existing),
                "skipped_existing": skipped_existing,
                "created": created,
            },
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
