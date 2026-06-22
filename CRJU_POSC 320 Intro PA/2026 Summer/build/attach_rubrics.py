#!/usr/bin/env python3
"""Attach rubrics to the 5 Management Brief stages and 5 graded Discussions for
CRJU/POSC 320 Summer Session B 2026. Mirrors the pattern established in
POSC 315's attach_canvas_rubrics.py, but looks assignment IDs up from
build/ids.json (written by create_core_assignments.py) instead of hardcoding
them, since this is a from-scratch build rather than a one-off patch.
"""
from __future__ import annotations

import argparse
import json
import sys

from canvas_common import Criterion, RubricSpec, TARGET_COURSE_ID, canvas_request, load_ids


def policy_brief_specs(ids: dict[str, int]) -> tuple[RubricSpec, ...]:
    return (
        RubricSpec(
            assignment_id=ids["Management Brief Stage 1: Problem Statement and Research Foundation"],
            assignment_name="Management Brief Stage 1: Problem Statement and Research Foundation",
            title="Management Brief Stage 1 Rubric",
            criteria=(
                Criterion("Problem definition", 3, "States a clear, specific public administration problem with a focused angle."),
                Criterion("Significance and evidence", 3, "Explains why the issue matters using 2-3 current (2022+) sources."),
                Criterion("Kettl Ch. 1-2 integration", 2, "Applies the public values triangle and 'what government does' concepts with citations."),
                Criterion("Writing clarity", 1, "Writes clearly and stays within the 400-600 word range."),
                Criterion("Google Doc submission", 1, "Shares the Google Doc with the instructor as Editor and submits the link."),
            ),
        ),
        RubricSpec(
            assignment_id=ids["Management Brief Stage 2: Stakeholder Analysis and Context"],
            assignment_name="Management Brief Stage 2: Stakeholder Analysis and Context",
            title="Management Brief Stage 2 Rubric",
            criteria=(
                Criterion("Stakeholder mapping", 4, "Identifies primary and secondary stakeholders and their interests/incentives."),
                Criterion("Contextual factors", 4, "Identifies political, legal, and resource constraints affecting implementation."),
                Criterion("Kettl Ch. 3-4 integration", 3, "Applies at least two concepts from Ch. 3-4 with page citations."),
                Criterion("Writing clarity and development", 2, "Builds clearly on Stage 1 within the 500-700 word range."),
                Criterion("Google Doc process", 2, "Continues in the same shared Google Doc with Suggesting mode on."),
            ),
        ),
        RubricSpec(
            assignment_id=ids["Management Brief Stage 3: Organizational Theory Application"],
            assignment_name="Management Brief Stage 3: Organizational Theory Application",
            title="Management Brief Stage 3 Rubric",
            criteria=(
                Criterion("Structural analysis", 5, "Analyzes organizational design, coordination, and accountability issues."),
                Criterion("Human capital challenges", 5, "Analyzes personnel, management capacity, and organizational culture issues."),
                Criterion("Kettl Ch. 5-6 integration", 4, "Applies executive-branch and human-capital concepts with page citations."),
                Criterion("Writing clarity and development", 3, "Builds clearly on prior stages within the 500-700 word range."),
                Criterion("Google Doc process", 3, "Continues in the same shared Google Doc with Suggesting mode on."),
            ),
        ),
        RubricSpec(
            assignment_id=ids["Management Brief Stage 4: Management Challenges and Solutions"],
            assignment_name="Management Brief Stage 4: Management Challenges and Solutions",
            title="Management Brief Stage 4 Rubric",
            criteria=(
                Criterion("Administrative challenges", 6, "Analyzes decision-making, implementation, and performance-measurement problems."),
                Criterion("Preliminary solutions", 6, "Proposes practical process, resource, or structural solutions."),
                Criterion("Kettl Ch. 7-8 integration", 5, "Applies decision-making and budgeting/performance concepts with citations."),
                Criterion("Writing clarity and development", 4, "Builds clearly on prior stages within the 600-800 word range."),
                Criterion("Google Doc process", 4, "Continues in the same shared Google Doc with Suggesting mode on."),
            ),
        ),
        RubricSpec(
            assignment_id=ids["Management Brief Stage 5: Final Recommendations and Executive Summary"],
            assignment_name="Management Brief Stage 5: Final Recommendations and Executive Summary",
            title="Management Brief Stage 5 Rubric",
            criteria=(
                Criterion("Final recommendations", 8, "Proposes three specific recommendations with implementation strategy, feasibility, and expected outcomes."),
                Criterion("Kettl Ch. 9-10 integration", 6, "Applies regulation, accountability, and courts concepts with page citations."),
                Criterion("Executive summary", 6, "Revises a clear, compelling, stand-alone summary with a call to action."),
                Criterion("Project cohesion and APA citations", 5, "Presents all five stages as one coherent document with complete APA citations."),
                Criterion("Final Google Doc submission", 5, "Uses Suggesting mode, accepts suggestions for a clean final version, and submits the link."),
            ),
        ),
    )


def discussion_specs(ids: dict[str, int]) -> tuple[RubricSpec, ...]:
    standard = (
        Criterion("Initial post quality", 4, "Thoughtful, specific reflection of about 200-300 words."),
        Criterion("Concept connection", 2, "References at least one course concept relevant to the week's topic."),
        Criterion("Peer replies", 2, "Responds meaningfully to at least two classmates."),
        Criterion("Clarity and respect", 2, "Posts are clear, respectful, and professional in tone."),
    )
    week4 = (
        Criterion("Initial post quality", 4, "Specific decision point with thoughtful analysis connected to Kettl Ch. 7-8."),
        Criterion("Concept connection", 2, "References a decision-making or budgeting concept from the reading."),
        Criterion("Peer reply", 2, "Responds meaningfully to at least one classmate."),
        Criterion("Clarity and respect", 2, "Posts are clear, respectful, and professional in tone."),
    )
    titles = (
        ("Week 1 Discussion: Your Experience with Government", standard),
        ("Week 2 Discussion: Who's Involved, and Why It's Complicated", standard),
        ("Week 3 Discussion: Structure, Staffing, and the Struggle to Perform", standard),
        ("Week 4 Discussion: Decision-Making Under Pressure", week4),
        ("Week 5 Discussion: Balancing Regulation and Innovation", standard),
    )
    return tuple(
        RubricSpec(
            assignment_id=ids[title],
            assignment_name=title,
            title=f"{title} Rubric",
            criteria=criteria,
        )
        for title, criteria in titles
    )


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


def assignment_has_rubric(assignment_id: int) -> bool:
    assignment = canvas_request(
        "GET",
        "/api/v1/courses/{course_id}/assignments/" + str(assignment_id),
        [("include[]", "rubric")],
        course_id=TARGET_COURSE_ID,
    )
    return bool(assignment.get("rubric"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ids = load_ids()
    pb_and_discussion_ids = dict(ids.get("core_assignments", {}))
    pb_and_discussion_ids.update(ids.get("discussion_assignment_ids", {}))

    specs = policy_brief_specs(pb_and_discussion_ids) + discussion_specs(pb_and_discussion_ids)

    created: list[dict[str, object]] = []
    skipped_existing: list[str] = []

    for spec in specs:
        total = sum(c.points for c in spec.criteria)
        if args.dry_run:
            print(f"DRY RUN: {spec.assignment_name} -> {spec.title} ({total:g} pts)")
            for criterion in spec.criteria:
                print(f"  - {criterion.description}: {criterion.points:g}")
            continue

        if assignment_has_rubric(spec.assignment_id):
            skipped_existing.append(spec.assignment_name)
            continue

        response = canvas_request(
            "POST",
            "/api/v1/courses/{course_id}/rubrics",
            params_for(spec),
            course_id=TARGET_COURSE_ID,
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
