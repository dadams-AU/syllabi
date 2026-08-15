#!/usr/bin/env python3
"""Build the POSC 521 (Fall 2026) Canvas assignment shell, groups, and rubrics.

Course 3592849. Idempotent: groups and assignments are matched by name and
updated in place, so re-running after a syllabus change does not duplicate
anything. Nothing is published -- "Assign to" and publication stay manual.

The weights here must match Table 2 in
  POSC 521 MPA Capstone/2026-27 Fall/posc521_2026_fall.tex
and the script refuses to run if they do not sum to 100.

Usage:  python3 build_posc521_assignments.py [--dry-run]

Requires CANVAS_BASE_URL and CANVAS_TOKEN in the environment.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

COURSE_ID = 3592849
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")

# Pacific time. DST ends 2026-11-01, so anything from November on is -08:00.
def when(date, time):
    offset = "-07:00" if date < "2026-11-01" else "-08:00"
    return f"{date}T{time}{offset}"


CLASS_TIME = "19:00:00"   # Mondays, 7:00 p.m.
MIDNIGHT = "23:59:00"

GROUPS = [
    ("Weekly Readings Assignments", 35),
    ("Reading Discussion Facilitation", 5),
    ("Seminar Performance", 8),
    ("Integration Seminar and Field Map", 5),
    ("MPA Comprehensive General Area Essay Exam", 35),
    ("Concentration Area Paper", 12),
]

UPLOAD = ["online_upload", "online_text_entry"]

# (group, name, points, due, submission_types, grading_type, label, blurb)
A = []


def add(group, name, points, due, subs, grading, label, blurb):
    A.append(
        {
            "group": group,
            "name": name,
            "points": points,
            "due": due,
            "subs": subs,
            "grading": grading,
            "label": label,
            "blurb": blurb,
        }
    )


W = "Weekly Readings Assignments"

BIB = (
    "One 150-word annotation per assigned reading: the central argument, its relevance to "
    "the week, and a page number locating the passage your summary describes. "
    "Your Feedback Appendix is the Track A protocol you worked through, or your Track B "
    "transcript. That completed work is the appendix; there is nothing else to write. "
    "It exists for reflection and improvement next week. It is not a revision aid for "
    "this submission."
)
ROUGH = (
    "Three pages. Patterns, connections, and contradictions across the week's readings, "
    "written entirely by you and brought to Monday's discussion and peer review studio."
)
FINAL = (
    "Four pages maximum, refined from your rough draft using class discussion and the peer "
    "review studio. Go deep on no more than three readings and say in your opening paragraph "
    "which you chose and why. Every claim about a reading carries a page number. "
    "Attach your Feedback Appendix: the Track A protocol you worked through or your Track B "
    "transcript, whichever you did, plus your Next-Week Plan of five to seven bullets."
)
def refl(denhardt=None):
    """Reflection blurb. Denhardt weeks also owe a Comparative Matrix revision."""
    base = ("250-300 words on how your thinking changed this week and what you will do "
            "differently next.")
    if denhardt:
        base += (f" Add or revise at least one row of your Comparative Matrix against Denhardt "
                 f"{denhardt}, and say in one sentence what forced the change.")
    return base

# --- Week 2: matrix week, no synthesis paper -------------------------------
add(W, "Week 2 - Annotated Bibliography (Denhardt Ch. 1-6)", 5,
    when("2026-08-31", CLASS_TIME), UPLOAD, "points", "YELLOW", BIB)
add(W, "Week 2 - Comparative Matrix, Version 1", 20,
    when("2026-09-04", MIDNIGHT), UPLOAD, "points", "RED",
    "Four columns (Old PA, New PA, NPM, NPS), rows derived yourself from Denhardt Ch. 1-6, "
    "one or two sentences per cell in your own words. Below the matrix, 300 words on the row "
    "where the four positions are least reconcilable, and why that row is the one that matters. "
    "No AI, on either track. You are building the instrument you will think with.")
add(W, "Week 2 - Reflection", 10,
    when("2026-09-04", MIDNIGHT), UPLOAD, "points", "RED", refl())

# --- Week 3: reading week, Labor Day ---------------------------------------
add(W, "Week 3 - Annotated Bibliography (Classical Foundations)", 5,
    when("2026-09-11", MIDNIGHT), UPLOAD, "points", "YELLOW", BIB)

# --- Week 4 through Week 11 ------------------------------------------------
# (week label, bib due or None, rough due, final due, reflection due, Denhardt chapter)
# The chapter is the one the syllabus makes that week's reflection revise the matrix against.
CYCLES = [
    ("Week 4 - Classical Foundations", None, "2026-09-14", "2026-09-16", "2026-09-18", None),
    ("Week 5 - Ethics and Values", "2026-09-21", "2026-09-21", "2026-09-23", "2026-09-25", "Ch. 7"),
    ("Week 6 - Leadership and Motivation", "2026-09-28", "2026-09-28", "2026-09-30", "2026-10-02", "Ch. 8"),
    ("Week 7 - Performance Management", "2026-10-05", "2026-10-05", "2026-10-07", "2026-10-09", "Ch. 9"),
    ("Week 9 - Privatization and Contracting", "2026-10-19", "2026-10-19", "2026-10-21", "2026-10-23", None),
    ("Week 10 - Social Equity", "2026-10-26", "2026-10-26", "2026-10-28", "2026-10-30", "Ch. 10-12"),
]

for label, bib, rough, final, refl_due, denhardt in CYCLES:
    if bib:
        add(W, f"{label} - Annotated Bibliography", 5,
            when(bib, CLASS_TIME), UPLOAD, "points", "YELLOW", BIB)
    add(W, f"{label} - Rough Draft Synthesis Paper", 10,
        when(rough, CLASS_TIME), UPLOAD, "points", "RED", ROUGH)
    add(W, f"{label} - Final Synthesis Paper", 20,
        when(final, MIDNIGHT), UPLOAD, "points", "YELLOW", FINAL)
    add(W, f"{label} - Reflection", 10,
        when(refl_due, MIDNIGHT), UPLOAD, "points", "RED", refl(denhardt))

# --- Weeks 8 and 11: book deep-dives ---------------------------------------
DEEP = [
    ("Week 8 - Street-Level Bureaucracy", "2026-10-12", "2026-10-14", "2026-10-16",
     "how the book reshaped your view of frontline public service"),
    ("Week 11 - Unmasking Administrative Evil", "2026-11-02", "2026-11-04", "2026-11-06",
     "how ordinary professional competence can produce harm and hide it from the people producing it"),
]

for label, mon, wed, fri, refl_topic in DEEP:
    add(W, f"{label} - Annotated Bibliography", 5,
        when(mon, CLASS_TIME), UPLOAD, "points", "YELLOW", BIB)
    add(W, f"{label} - Part A: Concept Application Analysis", 10,
        when(mon, CLASS_TIME), UPLOAD, "points", "RED",
        "Two pages. Three core concepts from the book applied to a real or hypothetical public "
        "service setting, including one explicit dilemma or tradeoff a public servant faces there.")
    add(W, f"{label} - Part B: Decision and Practice Analysis", 20,
        when(wed, MIDNIGHT), UPLOAD, "points", "RED",
        "Two pages proposing a response to your dilemma using course theory and evidence from the "
        "book, with one paragraph on equity implications and one on implementation constraints. "
        "No AI assistance. Peer feedback is welcome; AI feedback is not.")
    add(W, f"{label} - Reflection", 10,
        when(fri, MIDNIGHT), UPLOAD, "points", "RED",
        f"250-300 words on {refl_topic}.")

# --- Facilitation ----------------------------------------------------------
add("Reading Discussion Facilitation",
    "Reading Discussion Facilitation and Post-Class Reflection", 100,
    None, UPLOAD, "points", "RED",
    "In pairs, one 45-minute segment in your assigned week (Weeks 5-11): opening synthesis, "
    "facilitated discussion, and practical connections. Each facilitator submits an individual "
    "250-word reflection within 24 hours of the session. Questions, activities, and the "
    "reflection are yours; due date follows your pair's assigned week.")

# --- Seminar Performance ---------------------------------------------------
add("Seminar Performance", "Seminar Performance - Checkpoint 1 (Weeks 2-7)", 100,
    when("2026-10-12", CLASS_TIME), ["none"], "points", "RED",
    "Your contribution to seminar discussion and the peer review studio across Weeks 2-7, "
    "scored on the attached rubric and returned 10/12. Nothing is submitted. "
    "Volume is not scored. Four sentences that reorganize a discussion outrank forty that "
    "keep it moving.")
add("Seminar Performance", "Seminar Performance - Checkpoint 2 (Weeks 8-16)", 100,
    when("2026-12-07", CLASS_TIME), ["none"], "points", "RED",
    "Your contribution from Week 8 forward, plus the cold defense of your concentration paper "
    "at the 12/7 workshop: why these sources, why this position on the tradeoff, and what the "
    "position costs and who pays. Scored on the attached rubric. Nothing is submitted.")

# --- Field Map -------------------------------------------------------------
add("Integration Seminar and Field Map", "Field Map (Week 12)", 100,
    when("2026-11-09", CLASS_TIME), UPLOAD, "pass_fail", "RED",
    "One page, no prose paragraphs, built from your Comparative Matrix. Place the semester's "
    "theories in relation to one another, mark where the Denhardt frame breaks, and name the "
    "three arguments you would stake a comprehensive exam answer on with the strongest "
    "objection to each. Presented in three minutes on 11/9. Credit / no credit. "
    "No AI, on either track.")

# --- Comprehensive exam ----------------------------------------------------
add("MPA Comprehensive General Area Essay Exam",
    "MPA Comprehensive General Area Essay Exam", 100,
    when("2026-11-16", "16:59:00"), UPLOAD, "pass_fail", "RED",
    "Distributed Monday 11/9 at 9:45 p.m. at the close of the integration seminar. Two questions; "
    "answer one. 1,620 words maximum. Pass/fail. Retake window during finals week, 12/12-12/18. "
    "No AI.")

# --- Concentration paper ---------------------------------------------------
CP = "Concentration Area Paper"
add(CP, "Concentration Paper - Topic Selection", 20,
    when("2026-11-30", MIDNIGHT), UPLOAD, "points", "RED",
    "One page: your topic, your research question, the concepts from Recoding America you will "
    "use, the tradeoff you expect to confront, and your provisional position on it.")
add(CP, "Concentration Paper - Literature Review Draft", 40,
    when("2026-12-07", CLASS_TIME), UPLOAD, "points", "RED",
    "A literature review synthesizing Recoding America, relevant course readings, and additional "
    "scholarship in your concentration. Bring it to the 12/7 workshop.")
add(CP, "Concentration Paper - Final Paper", 100,
    when("2026-12-14", MIDNIGHT), UPLOAD, "points", "RED",
    "8-10 pages excluding references, double-spaced, APA or Chicago author-date. Adjudicate your "
    "tradeoff: take a defensible position and state plainly what it costs and who pays. Include an "
    "explicit equity assessment drawing on the Week 10 readings. No AI assistance of any kind.")


# --- Rubrics ---------------------------------------------------------------
# Four levels, named from the course's own argument about coverage and mastery.
def levels(pts, command, working, coverage, notyet):
    hi, mid, lo, floor = pts
    return [
        {"description": "Command", "long_description": command, "points": hi},
        {"description": "Working command", "long_description": working, "points": mid},
        {"description": "Coverage", "long_description": coverage, "points": lo},
        {"description": "Not yet", "long_description": notyet, "points": floor},
    ]


def seminar_criteria(per_criterion_points, include_defense):
    p = per_criterion_points
    scale = (p, round(p * 0.76), round(p * 0.52), round(p * 0.24))
    crits = [
        (
            "Command under question",
            levels(scale,
                   "Asked what an author argued, you give the argument itself and keep the author's "
                   "claim distinct from your reading of it. When you do not know, you say so plainly "
                   "and say what you would need to read.",
                   "You get the argument substantially right but blur the author's claim into your own "
                   "gloss on it, or need a prompt before the two come apart.",
                   "You name the reading and its topic and reproduce the gist rather than the argument. "
                   "Details go vague or wrong under follow-up.",
                   "You reach for a plausible-sounding version of an argument that is not in the text, "
                   "or cannot engage the reading when asked."),
        ),
        (
            "Selection and justification",
            levels(scale,
                   "You name the frameworks that genuinely bear on the problem, give reasons for the "
                   "selection, and say what you set aside and why. The reasons hold up when pressed.",
                   "You select well and justify thinly, or you justify what you chose without "
                   "accounting for what you dropped.",
                   "You list frameworks that are relevant without saying which carry the most weight, "
                   "treating the problem as an occasion to survey.",
                   "You apply whichever framework came up most recently, or wait for the selection to "
                   "be made for you."),
        ),
        (
            "Response to challenge",
            levels(scale,
                   "You take the objection on its merits and either revise your position out loud or "
                   "defend it with reasons that actually meet it.",
                   "You engage the objection but answer a weaker version of it, or defend by restating "
                   "your original claim more firmly.",
                   "You acknowledge the objection, agree that it is interesting, and continue unchanged.",
                   "You treat the objection as a personal challenge, or go silent."),
        ),
        (
            "Contribution to another student's work",
            levels(scale,
                   "Both suggestions name a specific move your partner could make by Tuesday, and your "
                   "question opens something they had not considered. Handed over in writing every "
                   "synthesis week.",
                   "Suggestions are specific but minor, or one of the two is general. The written "
                   "handoff is complete.",
                   "Suggestions are encouraging and general -- 'tighten the argument,' 'good use of "
                   "Lipsky.' Your partner cannot act on them.",
                   "The written handoff is missing or incomplete in one or more weeks."),
        ),
    ]
    if include_defense:
        crits.append(
            (
                "Defense of your own work",
                levels(scale,
                       "You answer why these sources, why this position, and what it costs and who pays, "
                       "out of the paper's own reasoning. You concede its weak points without abandoning "
                       "the argument.",
                       "You answer from the paper but cannot say what your position costs, or you name a "
                       "cost without saying who bears it.",
                       "You recite the paper's summary rather than its reasoning. The answers restate the "
                       "introduction.",
                       "You cannot account for the choices in your own paper."),
            )
        )
    return crits


# Only the two Seminar Performance rubrics live here. Every other rubric in
# the course is in build_posc521_rubrics.py; these two stay put because they
# were built first and work, and a second script editing them would fork them.
RUBRICS = {
    "Seminar Performance - Checkpoint 1 (Weeks 2-7)": (
        "Seminar Performance - Checkpoint 1",
        seminar_criteria(25, include_defense=False),
    ),
    "Seminar Performance - Checkpoint 2 (Weeks 8-16)": (
        "Seminar Performance - Checkpoint 2",
        seminar_criteria(20, include_defense=True),
    ),
}


# --- Canvas plumbing -------------------------------------------------------
def require_env():
    missing = [n for n, v in (("CANVAS_BASE_URL", BASE_URL), ("CANVAS_TOKEN", TOKEN)) if not v]
    if missing:
        raise SystemExit(f"Missing required environment variable(s): {', '.join(missing)}")


def api(method, path, payload=None):
    url = f"{BASE_URL}/api/v1{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} failed: {e.code} {e.read().decode()[:400]}")
    return json.loads(body) if body else None


def paged(path):
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        chunk = api("GET", f"{path}{sep}per_page=100&page={page}")
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return out


def description_html(label, blurb):
    # The AI label used to be its own paragraph containing nothing but bold text,
    # which UDOIT reads as a heading faked with styling: 43 hits, one per
    # assignment. As a run-in on the blurb it is just as prominent and is an
    # ordinary paragraph.
    return f'<p><strong>{label}</strong> &mdash; {blurb}</p>'


def sync_groups():
    existing = {g["name"]: g for g in paged(f"/courses/{COURSE_ID}/assignment_groups")}
    ids = {}
    for position, (name, weight) in enumerate(GROUPS, start=1):
        payload = {"name": name, "group_weight": weight, "position": position}
        if name in existing:
            g = api("PUT", f"/courses/{COURSE_ID}/assignment_groups/{existing[name]['id']}", payload)
        else:
            g = api("POST", f"/courses/{COURSE_ID}/assignment_groups", payload)
        ids[name] = g["id"]
    # Canvas seeds every new course with a default "Assignments" group. Leaving a
    # zero-weight group behind is harmless but confusing in the gradebook.
    for name, g in existing.items():
        if name not in ids and not g.get("assignment_count"):
            api("DELETE", f"/courses/{COURSE_ID}/assignment_groups/{g['id']}")
            print(f"  removed empty leftover group: {name}")
    api("PUT", f"/courses/{COURSE_ID}", {"course": {"apply_assignment_group_weights": True}})
    return ids


def sync_assignments(group_ids):
    existing = {a["name"]: a for a in paged(f"/courses/{COURSE_ID}/assignments")}
    result = {}
    created = updated = 0
    for spec in A:
        payload = {
            "assignment": {
                "name": spec["name"],
                "description": description_html(spec["label"], spec["blurb"]),
                "points_possible": spec["points"],
                "assignment_group_id": group_ids[spec["group"]],
                "submission_types": spec["subs"],
                "grading_type": spec["grading"],
                # Re-running SETS this on every assignment, so a run after you have
                # published assignments will quietly unpublish all 43. The course
                # itself and its modules are untouched. Check before re-running
                # mid-term; the fix is to publish again, not to edit this.
                "published": False,
                "omit_from_final_grade": False,
            }
        }
        if spec["due"]:
            payload["assignment"]["due_at"] = spec["due"]
        if spec["name"] in existing:
            a = api("PUT", f"/courses/{COURSE_ID}/assignments/{existing[spec['name']]['id']}", payload)
            updated += 1
        else:
            a = api("POST", f"/courses/{COURSE_ID}/assignments", payload)
            created += 1
        result[spec["name"]] = a["id"]
    print(f"  assignments: {created} created, {updated} updated")
    return result


def sync_rubrics(assignment_ids):
    existing = {r["title"]: r for r in paged(f"/courses/{COURSE_ID}/rubrics")}
    for assignment_name, (title, criteria) in RUBRICS.items():
        crit_payload = {}
        for i, (desc, ratings) in enumerate(criteria):
            crit_payload[str(i)] = {
                "description": desc,
                "points": max(r["points"] for r in ratings),
                "criterion_use_range": False,
                "ratings": {str(j): r for j, r in enumerate(ratings)},
            }
        payload = {
            "rubric": {
                "title": title,
                "free_form_criterion_comments": True,
                "criteria": crit_payload,
            },
            "rubric_association": {
                "association_id": assignment_ids[assignment_name],
                "association_type": "Assignment",
                "use_for_grading": True,
                "hide_score_total": False,
                "purpose": "grading",
            },
        }
        if title in existing:
            api("PUT", f"/courses/{COURSE_ID}/rubrics/{existing[title]['id']}", payload)
            print(f"  rubric updated: {title} ({len(criteria)} criteria)")
        else:
            api("POST", f"/courses/{COURSE_ID}/rubrics", payload)
            print(f"  rubric created: {title} ({len(criteria)} criteria)")


def main():
    total = sum(w for _, w in GROUPS)
    if total != 100:
        raise SystemExit(f"Group weights sum to {total}, not 100. Fix GROUPS before running.")

    if "--dry-run" in sys.argv:
        print(f"{len(GROUPS)} groups, weights sum to 100")
        print(f"{len(A)} assignments")
        for name, (title, criteria) in RUBRICS.items():
            print(f"rubric '{title}' -> {name}: {len(criteria)} criteria, "
                  f"{sum(max(r['points'] for r in c[1]) for c in criteria)} points")
        by_group = {}
        for spec in A:
            by_group.setdefault(spec["group"], []).append(spec)
        for name, weight in GROUPS:
            items = by_group.get(name, [])
            print(f"  {name} ({weight}%): {len(items)} assignments, "
                  f"{sum(i['points'] for i in items)} points")
        return

    require_env()
    print("Syncing groups...")
    group_ids = sync_groups()
    print("Syncing assignments...")
    assignment_ids = sync_assignments(group_ids)
    print("Syncing rubrics...")
    sync_rubrics(assignment_ids)
    print("Done. Nothing published; set 'Assign to' and publish manually.")


if __name__ == "__main__":
    main()
