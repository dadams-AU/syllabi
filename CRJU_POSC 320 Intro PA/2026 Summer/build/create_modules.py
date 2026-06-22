#!/usr/bin/env python3
"""Create Module 0 (Welcome) + Week 1-5 modules for CRJU/POSC 320 Summer
Session B 2026, wiring in the quizzes/assignments/discussions created by the
earlier build scripts plus the still-live courses.dadams.io lecture notes
from last year's course. Lecture videos are intentionally omitted -- new
ones are being recorded for this term and will be added separately.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from canvas_common import TARGET_COURSE_ID, canvas_get_all, canvas_request, load_ids, upload_course_file

HANDOUT_BASE = "https://courses.dadams.io/POSC320/handouts"
LECTURE_BASE = "https://courses.dadams.io/POSC320/html_page"
SYLLABUS_RAW_URL = (
    "https://raw.githubusercontent.com/dadams-AU/syllabi/main/"
    "CRJU_POSC%20320%20Intro%20PA/2026%20Summer/CRJU-POSC_320.pdf"
)
BUILD_DIR = Path(__file__).parent
SYLLABUS_LOCAL_PATH = BUILD_DIR.parent / "CRJU-POSC_320.pdf"
LOGO_LOCAL_PATH = BUILD_DIR.parent / "csuf_logo.png"

WEEK_MODULES: tuple[dict[str, object], ...] = (
    {
        "week": 1,
        "name": "Week 1: Modules 1 and 2",
        "submodules": (
            {
                "subheader": "Module 1",
                "notes": (("1 Lecture Notes", f"{LECTURE_BASE}/module_1_WhatIsPA.html"),),
                "quiz": "Module 1 Quiz: Intro and Overview",
            },
            {
                "subheader": "Module 2",
                "notes": (
                    ("2-1 Lecture Notes", f"{LECTURE_BASE}/module_2-1_basics.html"),
                    ("2-2 Lecture Notes", f"{LECTURE_BASE}/module_2-2erasofpa.html"),
                ),
                "quiz": "Module 2 Quiz: Basics and Eras",
            },
        ),
        "policy_brief": "Management Brief Stage 1: Problem Statement and Research Foundation",
        "research_log": "Research Log: Week 1",
        "discussion": "Week 1 Discussion: Your Experience with Government",
    },
    {
        "week": 2,
        "name": "Week 2: Modules 3 and 4",
        "submodules": (
            {
                "subheader": "Module 3",
                "notes": (
                    ("3-1 Lecture Notes", f"{LECTURE_BASE}/module_3-1_what_govt_does.html"),
                    ("3-2 Lecture Notes", f"{LECTURE_BASE}/module_3-2_govt_functions.html"),
                ),
                "quiz": "Quiz Module 3: What Government Does—And How It Does It",
            },
            {
                "subheader": "Module 4",
                "notes": (
                    ("4-1 Lecture Notes", f"{LECTURE_BASE}/module_4-1_orgtheory.html"),
                    ("4-2 Lecture Notes", f"{LECTURE_BASE}/module_4-2_org_problems.html"),
                ),
                "quiz": "Quiz Module 4: Organizational Theory and Organizational Problems",
            },
        ),
        "policy_brief": "Management Brief Stage 2: Stakeholder Analysis and Context",
        "research_log": "Research Log: Week 2",
        "discussion": "Week 2 Discussion: Who's Involved, and Why It's Complicated",
    },
    {
        "week": 3,
        "name": "Week 3: Modules 5 and 6",
        "submodules": (
            {
                "subheader": "Module 5",
                "notes": (
                    ("5-1 Lecture Notes", f"{LECTURE_BASE}/module_5-1_executive.html"),
                    ("5-2 Lecture Notes", f"{LECTURE_BASE}/module_5-2_reform.html"),
                ),
                "quiz": "Module 5 Quiz: Executive and Admin Reform",
            },
            {
                "subheader": "Module 6",
                "notes": (
                    ("6-1 Lecture Notes", f"{LECTURE_BASE}/module_6-1_civilservice.html"),
                    ("6-2 Lecture Notes", f"{LECTURE_BASE}/module_6-2_humancapital.html"),
                ),
                "quiz": "Module 6 Quiz: Civil Service and Human Capital",
            },
        ),
        "policy_brief": "Management Brief Stage 3: Organizational Theory Application",
        "research_log": "Research Log: Week 3",
        "discussion": "Week 3 Discussion: Structure, Staffing, and the Struggle to Perform",
    },
    {
        "week": 4,
        "name": "Week 4: Modules 7 and 8",
        "submodules": (
            {
                "subheader": "Module 7: Decision Making and Budgeting",
                "notes": (
                    ("7-1 Lecture Notes", f"{LECTURE_BASE}/module_7-1_decisionmaking.html"),
                    ("7-2 Lecture Notes", f"{LECTURE_BASE}/module_7-2_budgeting.html"),
                ),
                "quiz": "Module 7 Quiz: Decision Making and Budgeting",
            },
            {
                "subheader": "Module 8: Implementation and Performance",
                "notes": (("8-1 Lecture Notes", f"{LECTURE_BASE}/module_8-1_performance_implementation.html"),),
                "quiz": "Module 8 Quiz: Implementation and Performance",
            },
        ),
        "policy_brief": "Management Brief Stage 4: Management Challenges and Solutions",
        "research_log": "Research Log: Week 4",
        "discussion": "Week 4 Discussion: Decision-Making Under Pressure",
    },
    {
        "week": 5,
        "name": "Week 5: Modules 9 and 10",
        "submodules": (
            {
                "subheader": "Module 9: Regulation and the Courts",
                "notes": (("9 Lecture Notes", f"{LECTURE_BASE}/module_9_regulationandcourts.html"),),
                "quiz": "Module 9 Quiz: Regulation and Oversight",
            },
            {
                "subheader": "Module 10: Accountability and Oversight",
                "notes": (("10 Lecture Notes", f"{LECTURE_BASE}/module_10_accountability.html"),),
                "quiz": "Module 10 Quiz: Accountability",
            },
        ),
        "wrap_up": {
            "subheader": "Module 11: The End and Farewell",
            "notes": (
                ("\U0001f919 Course Wrap-Up and Looking Forward", f"{LECTURE_BASE}/module_11_wrap-up.html"),
            ),
        },
        "policy_brief": "Management Brief Stage 5: Final Recommendations and Executive Summary",
        "research_log": "Research Log: Final Reflection",
        "discussion": "Week 5 Discussion: Balancing Regulation and Innovation",
    },
)

WELCOME_PAGE_TITLE = "\U0001f31e Welcome to CRJU/POSC 320: Introduction to Public Administration"


def add_item(module_id: int, params: list[tuple[str, str]], dry_run: bool, label: str) -> None:
    if dry_run:
        print(f"    DRY RUN item: {label}")
        return
    canvas_request(
        "POST",
        f"/api/v1/courses/{{course_id}}/modules/{module_id}/items",
        params,
        course_id=TARGET_COURSE_ID,
    )


def subheader_params(title: str) -> list[tuple[str, str]]:
    return [("module_item[title]", title), ("module_item[type]", "SubHeader")]


def external_url_params(title: str, url: str) -> list[tuple[str, str]]:
    return [
        ("module_item[title]", title),
        ("module_item[type]", "ExternalUrl"),
        ("module_item[external_url]", url),
        ("module_item[new_tab]", "1"),
    ]


def content_item_params(item_type: str, title: str, content_id: int) -> list[tuple[str, str]]:
    return [
        ("module_item[title]", title),
        ("module_item[type]", item_type),
        ("module_item[content_id]", str(content_id)),
    ]


def page_item_params(page_url: str) -> list[tuple[str, str]]:
    return [("module_item[type]", "Page"), ("module_item[page_url]", page_url)]


def build_module_0(dry_run: bool) -> None:
    name = "Module 0: Welcome, Overview, Syllabus"
    if not dry_run:
        existing = {m["name"] for m in canvas_get_all("/api/v1/courses/{course_id}/modules", TARGET_COURSE_ID)}
        if name in existing:
            print(f"Skipping existing module: {name}")
            return

    if dry_run:
        print(f"DRY RUN: create module {name!r}")
        print(f"    upload {LOGO_LOCAL_PATH.name} and {SYLLABUS_LOCAL_PATH.name} as course files")
        print("    create welcome wiki page")
        for label in (
            "SubHeader Welcome!",
            "Page: welcome page",
            "SubHeader Important Documents",
            "ExternalUrl Syllabus Online",
            "File Syllabus PDF",
            "ExternalUrl Scaffolded Management Brief Assignment",
            "ExternalUrl Management Brief Grading Rubric",
            "ExternalUrl Research Log Guidelines",
            "SubHeader Lecture Notes",
            "ExternalUrl Lecture Notes - Module 0",
        ):
            print(f"    DRY RUN item: {label}")
        return

    logo_file = upload_course_file(TARGET_COURSE_ID, LOGO_LOCAL_PATH, "image/png")
    syllabus_file = upload_course_file(TARGET_COURSE_ID, SYLLABUS_LOCAL_PATH, "application/pdf")

    welcome_body = f"""
<div style="text-align: center;">
<img src="{logo_file['url']}" alt="CSUF public administration logo" width="275" height="182">
<p style="font-size: 1.2em;">Summer Session B 2026 &bull; Asynchronous Online &bull; June 29 &ndash; July 31</p>
</div>
<hr>
<h2>\U0001f4cb What This Course Is</h2>
<p>Public administration is how ideas become action&mdash;how policy gets done (or doesn't). In this course, we'll explore how public agencies work, how decisions are made, and what values like <strong>accountability, efficiency, and equity</strong> really mean in practice.</p>
<p>This is a fully asynchronous, five-week course. Plan to invest the equivalent of a full-time course's effort during each week of the term. Check Canvas and your CSUF email <strong>at least once daily</strong>, including weekends.</p>
<h2>\U0001f680 Quick Start</h2>
<ul>
<li>&#9989; <strong>Start with Modules</strong> &mdash; each week runs Monday to Friday</li>
<li>&#128196; <strong>Read the <a href="{syllabus_file['url']}" target="_blank">Syllabus</a></strong></li>
<li>&#128218; <strong>Textbook:</strong> <em>Kettl, Politics of the Administrative Process (9th ed.)</em></li>
<li>&#129489;&#8205;&#127979; <strong>Lecture slides</strong> are available in the modules and <a href="https://courses.dadams.io/#posc320-async" target="_blank">here</a></li>
<li>&#127909; <strong>Video lectures + quizzes</strong> posted weekly</li>
<li>&#128221; <strong>Major assignment:</strong> Scaffolded <a href="{HANDOUT_BASE}/paper_assignment.html" target="_blank">Management Brief Project</a> (worth 45%)</li>
<li>&#128270; <strong>Check the <a href="{HANDOUT_BASE.rsplit('/', 1)[0]}/posc320_async_handouts.html" target="_blank">Handouts &amp; Resources page</a></strong> for the assignment overview, rubric, and research log guidelines</li>
</ul>
<h2>\U0001f334 A Friendly Summer Reminder</h2>
<p>This course is compressed into five weeks, but it's still summer. A few gentle suggestions, in no particular order:</p>
<ul>
<li>&#127807; Touch grass from time to time &mdash; preferably grass that is not part of a course module</li>
<li>&#129380; Drink something cold. Hydration counts as self-care</li>
<li>&#127754; Get to the ocean, the mountains, or at least somewhere with a decent breeze, when you can</li>
<li>&#127749; Let yourself have a slow afternoon every now and then &mdash; the reading will still be there</li>
<li>&#127942; A well-rested brain writes a better Management Brief than an exhausted one. Pace yourself</li>
</ul>
<h2>\U0001f464 Instructor</h2>
<ul>
<li><strong>David P. Adams, Ph.D.</strong></li>
<li>Office: 516 Gordon Hall</li>
<li>Phone/Text: (657) 278-4770</li>
<li>Email: <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a></li>
<li>Website: <a href="https://dadams.io">dadams.io</a></li>
<li>Zoom: <a href="https://fullerton.zoom.us/j/3347502369">fullerton.zoom.us/j/3347502369</a></li>
<li>Schedule a meeting: <a href="https://dadams.io/appointments">dadams.io/appointments</a></li>
</ul>
<h2>\U0001f550 Virtual Office Hours</h2>
<p>Tuesdays 9:30&ndash;10:30 a.m. and 7:00&ndash;8:00 p.m. on the <a href="https://discord.com/channels/1128747433636135113/1154048074172354600">Discord Office Hours Channel</a>, and by <a href="https://dadams.io/appointments">appointment</a>.</p>
<h2>\U0001f4e8 Response Time</h2>
<p>I will strive to respond to all student emails, Discord posts, and Canvas messages within 24 hours, except on weekends and holidays. If you have not received a response within 24 hours, please send a follow-up message. If you are still waiting after 48 hours, contact me via phone or SMS at (657) 278-4770.</p>
<h2>\U0001f4af Grading Summary</h2>
<ul>
<li>Video Lectures and Reading Quizzes (10) &mdash; <strong>30%</strong> (Fridays, weekly)</li>
<li>Discussion Posts (5) &mdash; <strong>15%</strong> (Fridays, weekly)</li>
<li>Management Brief Stage 1: Problem Statement and Research Foundation &mdash; <strong>4.5%</strong> (Fri, July 3)</li>
<li>Management Brief Stage 2: Stakeholder Analysis and Context &mdash; <strong>6.75%</strong> (Fri, July 10)</li>
<li>Management Brief Stage 3: Organizational Theory Application &mdash; <strong>9%</strong> (Fri, July 17)</li>
<li>Management Brief Stage 4: Management Challenges and Solutions &mdash; <strong>11.25%</strong> (Fri, July 24)</li>
<li>Management Brief Stage 5: Final Recommendations and Executive Summary &mdash; <strong>13.5%</strong> (Fri, July 31)</li>
<li>Research Logs (5) &mdash; <strong>10%</strong> (Fridays, weekly)</li>
</ul>
<h2>\U0001f4e4 Submission Format &mdash; Google Docs</h2>
<p>All stages of the Management Brief Project must be drafted and submitted as a single Google Doc that you carry forward across all five weeks. <strong>Before your first submission, share the document with <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a> as an Editor</strong>. Each week, paste the shareable link into the Canvas assignment by the Friday deadline. Microsoft Word, PDF, or other file uploads will not be accepted.</p>
<h2>\U0001f4c5 Schedule Highlights</h2>
<ul>
<li>Course begins: Monday, June 29</li>
<li>Independence Day: Saturday, July 4 (falls on a weekend &mdash; no deadlines affected)</li>
<li>Last day of class: Friday, July 31</li>
</ul>
<h2>\U0001f4da Required Text</h2>
<p>Kettl, Daniel F. 2023. <em>Politics of the Administrative Process</em>, 9th ed. Washington, D.C.: CQ Press.</p>
"""

    page = canvas_request(
        "POST",
        "/api/v1/courses/{course_id}/pages",
        [
            ("wiki_page[title]", WELCOME_PAGE_TITLE),
            ("wiki_page[body]", welcome_body),
            ("wiki_page[published]", "false"),
        ],
        course_id=TARGET_COURSE_ID,
    )

    module = canvas_request(
        "POST",
        "/api/v1/courses/{course_id}/modules",
        [("module[name]", name), ("module[position]", "1")],
        course_id=TARGET_COURSE_ID,
    )
    module_id = module["id"]

    add_item(module_id, subheader_params("Welcome!"), False, "SubHeader Welcome!")
    add_item(module_id, page_item_params(page["url"]), False, "Page: welcome page")
    add_item(module_id, subheader_params("Important Documents"), False, "SubHeader Important Documents")
    add_item(module_id, external_url_params("Syllabus Online", SYLLABUS_RAW_URL), False, "ExternalUrl Syllabus Online")
    add_item(
        module_id,
        content_item_params("File", "Syllabus PDF", syllabus_file["id"]),
        False,
        "File Syllabus PDF",
    )
    add_item(
        module_id,
        external_url_params("Scaffolded Management Brief Assignment", f"{HANDOUT_BASE}/paper_assignment.html"),
        False,
        "ExternalUrl Management Brief handout",
    )
    add_item(
        module_id,
        external_url_params("Management Brief Grading Rubric", f"{HANDOUT_BASE}/paper_assignment_rubric.html"),
        False,
        "ExternalUrl rubric handout",
    )
    add_item(
        module_id,
        external_url_params("Research Log Guidelines", f"{HANDOUT_BASE}/research_log_guidelines.html"),
        False,
        "ExternalUrl research log handout",
    )
    add_item(module_id, subheader_params("Lecture Notes"), False, "SubHeader Lecture Notes")
    add_item(
        module_id,
        external_url_params("Lecture Notes - Module 0: Welcome!", f"{LECTURE_BASE}/module_0_Welcome.html"),
        False,
        "ExternalUrl Module 0 notes",
    )

    print(f"Created module 0: id={module_id}")


def build_week_module(spec: dict[str, object], position: int, ids: dict[str, object], dry_run: bool) -> None:
    name = spec["name"]
    if not dry_run:
        existing = {m["name"] for m in canvas_get_all("/api/v1/courses/{course_id}/modules", TARGET_COURSE_ID)}
        if name in existing:
            print(f"Skipping existing module: {name}")
            return

    if dry_run:
        print(f"DRY RUN: create module {name!r} (position {position})")
        for sub in spec["submodules"]:
            print(f"    SubHeader: {sub['subheader']}")
            for title, url in sub["notes"]:
                print(f"      ExternalUrl notes: {title} -> {url}")
            print(f"      Quiz: {sub['quiz']}")
        if "wrap_up" in spec:
            wrap_up = spec["wrap_up"]
            print(f"    SubHeader: {wrap_up['subheader']}")
            for title, url in wrap_up["notes"]:
                print(f"      ExternalUrl: {title} -> {url}")
        print("    SubHeader: Assignments")
        print(f"      Assignment: {spec['policy_brief']}")
        print(f"      Assignment: {spec['research_log']}")
        print(f"      Discussion: {spec['discussion']}")
        return

    module = canvas_request(
        "POST",
        "/api/v1/courses/{course_id}/modules",
        [("module[name]", name), ("module[position]", str(position))],
        course_id=TARGET_COURSE_ID,
    )
    module_id = module["id"]

    quizzes = ids.get("quizzes", {})
    core = ids.get("core_assignments", {})

    for sub in spec["submodules"]:
        add_item(module_id, subheader_params(sub["subheader"]), False, sub["subheader"])
        for title, url in sub["notes"]:
            add_item(module_id, external_url_params(title, url), False, title)
        quiz_id = quizzes[sub["quiz"]]
        add_item(module_id, content_item_params("Quiz", sub["quiz"], quiz_id), False, sub["quiz"])

    if "wrap_up" in spec:
        wrap_up = spec["wrap_up"]
        add_item(module_id, subheader_params(wrap_up["subheader"]), False, wrap_up["subheader"])
        for title, url in wrap_up["notes"]:
            add_item(module_id, external_url_params(title, url), False, title)

    add_item(module_id, subheader_params("Assignments"), False, "Assignments subheader")
    add_item(
        module_id,
        content_item_params("Assignment", spec["policy_brief"], core[spec["policy_brief"]]),
        False,
        spec["policy_brief"],
    )
    add_item(
        module_id,
        content_item_params("Assignment", spec["research_log"], core[spec["research_log"]]),
        False,
        spec["research_log"],
    )
    add_item(
        module_id,
        content_item_params("Discussion", spec["discussion"], core[spec["discussion"]]),
        False,
        spec["discussion"],
    )

    print(f"Created module: {name} id={module_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ids = load_ids()

    build_module_0(args.dry_run)
    for position, spec in enumerate(WEEK_MODULES, start=2):
        build_week_module(spec, position, ids, args.dry_run)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
