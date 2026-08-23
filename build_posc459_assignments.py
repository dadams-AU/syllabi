#!/usr/bin/env python3
"""Build POSC 459 (Fall 2026) Canvas assignment groups, assignments, and rubrics.

Sources of truth, in this order:
  - the vault assignment sheets (student-facing text, converted with pandoc)
  - "00 - Assignment Index.md" for weights, dates, and AI labels
  - posc459-syllabus-fa26-papyrus.tex for the weighting tables

Follows AGENTS.md: everything unpublished, nothing invented, ambiguous dates
left unset with (DATE NEEDED) in the title.

Idempotent by name: re-running updates existing assignments and replaces their
rubrics rather than duplicating.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zoneinfo

COURSE_ID = "3592717"
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")
TZ = zoneinfo.ZoneInfo("America/Los_Angeles")

SHEETS = ("/home/dadams/obsidian-vaults/snags/9. Teaching/2026-T1 Fall/"
          "POSC 459 - Welfare Politics and Policy/Assignments")


def require_env():
    missing = [n for n, v in (("CANVAS_BASE_URL", BASE_URL), ("CANVAS_TOKEN", TOKEN)) if not v]
    if missing:
        raise SystemExit(f"Missing required environment variable(s): {', '.join(missing)}")


def api(method, path, payload=None, params=None):
    if params:
        sep = "&" if "?" in path else "?"
        path = f"{path}{sep}{urllib.parse.urlencode(params, doseq=True)}"
    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
               "Accept": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: "
                           f"{exc.read().decode('utf-8', 'replace')}") from exc


def list_all(path):
    rows, page = [], 1
    while True:
        batch = api("GET", path, params={"per_page": 100, "page": page})
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        page += 1


def due(date_str, hour=23, minute=59):
    """'2026-09-04' -> ISO8601 with the correct PDT/PST offset."""
    if not date_str:
        return None
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime.datetime(y, m, d, hour, minute, tzinfo=TZ).isoformat()


def sheet_html(filename, start_heading=None):
    """Student-facing body of an assignment sheet, as Canvas HTML.

    start_heading, if given, drops everything before that markdown heading: the
    discussion papers share sheet 03, whose header block and five-row table are
    an overview that reads as noise repeated on each of the five assignments
    (David, 2026-08-23), so those start at "## What you're doing".

    Strips YAML frontmatter and everything from the first Obsidian callout
    onward — every callout in this folder is an instructor note marked
    'not student-facing', and they must never reach Canvas.
    """
    if not filename:
        return ""
    path = os.path.join(SHEETS, filename)
    text = open(path, encoding="utf-8").read()

    if text.startswith("---"):
        end = text.index("\n---", 3)
        text = text[end + 4:]

    cut = re.search(r"^> \[!", text, re.M)
    if cut:
        text = text[:cut.start()]
        text = re.sub(r"\n---\s*$", "", text.rstrip()) + "\n"

    # Drop the H1 title: the Canvas assignment name already carries it.
    text = re.sub(r"^#\s+.*\n", "", text.lstrip("\n"), count=1)
    if start_heading:
        i = text.find(start_heading)
        if i < 0:
            raise SystemExit(f"{filename}: start heading {start_heading!r} not found")
        text = text[i:]
    # Sheet 04's film table points a student row at an instructor-only note.
    # The underlying Week 14 decision is flagged on the assignment itself.
    text = text.replace("**Unresolved — see instructor note**", "**To be announced**")
    # Wikilinks would 404 in Canvas; keep the label only.
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

    out = subprocess.run(["pandoc", "-f", "markdown+pipe_tables", "-t", "html",
                          "--wrap=none"], input=text, capture_output=True,
                         text=True, check=True)
    html = out.stdout.strip()

    # Nothing instructor-facing may reach a student. Fail the build rather than
    # publish it; a new stray reference should stop the run, not slip through.
    for probe in ("instructor note", "not student-facing", "answer key",
                  "audit score", "planted error"):
        if probe in html.lower():
            raise SystemExit(f"REFUSING TO BUILD: {filename} still contains "
                             f"{probe!r} after stripping. Fix the sheet or the filter.")
    return html


def prompt_lead(n):
    """The prompt for Discussion Paper n, from the vault sheet 03b, as Canvas HTML.

    Each paper carries its own prompt above the shared rules from sheet 03, so a
    student opening the assignment sees what to write about without a second
    click. Section headers in 03b are "## n · title".
    """
    path = os.path.join(SHEETS, "03b - Discussion Prompts.md")
    text = open(path, encoding="utf-8").read()
    m = re.search(rf"^## {n} · (.*?)\n(.*?)(?=^## \d+ · |^> \[!|\Z)", text, re.M | re.S)
    if not m:
        raise SystemExit(f"prompt {n} not found in 03b")
    title, body = m.group(1).strip(), m.group(2).strip().rstrip("-").strip()
    body = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", body)
    body = re.sub(r"\[\[([^\]]+)\]\]", r"\1", body)
    html = subprocess.run(["pandoc", "-f", "markdown+pipe_tables", "-t", "html", "--wrap=none"],
                          input=body, capture_output=True, text=True, check=True).stdout.strip()
    title = re.sub(r"\*(.+?)\*", r"<em>\1</em>", title)
    return f"<h3>Prompt {n} &mdash; {title}</h3>\n{html}"


LABEL_BOX = {
    "GREEN": ("#1b5e20", "#e8f5e9", "GREEN — AI use permitted. No disclosure needed."),
    "YELLOW": ("#8d6e00", "#fff8e1", "YELLOW — AI permitted within stated limits. Disclosure required."),
    "RED": ("#b71c1c", "#ffebee", "RED — No AI. This assignment is designed to be done without it."),
}


def label_html(label):
    if not label:
        return ""
    color, bg, text = LABEL_BOX[label]
    return (f'<p style="border-left:5px solid {color};background:{bg};padding:10px 14px;">'
            f'<strong>AI label: {text}</strong><br>'
            f'<span style="font-size:0.9em;">The full policy is on the Canvas page '
            f'&ldquo;Policy on the Use of Generative AI and Other Technology.&rdquo;</span></p>')


def flag_html(msg):
    return (f'<p style="border:2px dashed #b71c1c;padding:10px 14px;">'
            f'<strong>UNRESOLVED &mdash; do not publish until fixed:</strong> {msg}</p>')


# --------------------------------------------------------------------------
# Assignment groups.  One "Major Written Work" group at 40% holds BOTH the
# undergraduate and the graduate track: Canvas group weights are course-wide,
# but an assignment a student is not assigned to drops out of their own
# calculation, so each population's 40% comes from its own track.  Setting
# "Assign to" per track needs a roster and is a manual step before publishing.
# --------------------------------------------------------------------------
GROUPS = [
    {"name": "Attendance and Participation", "weight": 10},
    # Five required papers since 2026-08-23; no drop rule (David: "no dropping lowest score").
    {"name": "Discussion Papers", "weight": 10},
    {"name": "Midterm Exam", "weight": 20},
    {"name": "Major Written Work", "weight": 40},
    {"name": "Final Exam", "weight": 20},
]

UPLOAD = ["online_upload"]
TEXT_OR_UPLOAD = ["online_upload", "online_text_entry"]

A = [
    # ---- Attendance and Participation (10%) -------------------------------
    {"name": "Attendance", "group": "Attendance and Participation", "points": 50,
     "types": ["none"], "due": None,
     "body": "<p>Instructor-recorded attendance. Students are expected to attend all "
             "in-person sessions. If you are unable to attend, notify me in advance. You are "
             "responsible for obtaining any materials or information covered during absences. "
             "<strong>Participation in in-class activities cannot be made up.</strong></p>"},

    # Monday 8/31, not Wednesday: the 8/5 day-swap put the unaided diagnostic
    # before any contact with PapyrusAI. Class meets 1:00-2:15, so it is due at
    # the end of that session.
    {"name": "Baseline Writing Diagnostic",
     "group": "Attendance and Participation", "points": 20, "types": ["on_paper"],
     "due": due("2026-08-31", 14, 15), "sheet": "02 - Baseline Writing Diagnostic.md",
     "label": "RED"},

    {"name": "Reading Journal — Checkpoint 1", "group": "Attendance and Participation",
     "points": 25, "types": TEXT_OR_UPLOAD, "due": due("2026-10-14"),
     "sheet": "01 - Reading Journal.md", "label": "GREEN",
     "lead": "<p><strong>Checkpoint 1 of 2: five entries by Wednesday, October 14.</strong> "
             "If you keep your journal in the PapyrusAI Idea Catcher module, nothing needs "
             "uploading and I will check it there. If you keep it anywhere else, upload it "
             "here.</p>"},

    {"name": "Reading Journal — Checkpoint 2", "group": "Attendance and Participation",
     "points": 25, "types": TEXT_OR_UPLOAD, "due": due("2026-12-09"),
     "sheet": "01 - Reading Journal.md", "label": "GREEN",
     "lead": "<p><strong>Checkpoint 2 of 2: five more entries by Wednesday, December 9</strong>, "
             "for ten across the term. Same rule as the first checkpoint: if it lives in Idea "
             "Catcher, nothing to upload.</p>"},

    # Documentary Responses 1-3 were folded into Discussion Papers 1, 3, and 4 on
    # 2026-08-23 and deleted from Canvas the same night; the films are the spine of
    # those three papers (sheet 03, prompts in 03b).
    # Week 14 carries no documentary response (resolved 8/11). It is reading and
    # independent work: the week opens after Thanksgiving with term papers and
    # graduate outlines due that Wednesday. Three responses, not four.

    # ---- Discussion Papers (10%), five required, Fridays 11:59 p.m. --------
    # Restructured 2026-08-23 from ten-choose-five (David). Papers 1, 3, 4 carry
    # the films that used to be separate documentary responses. Weeks chosen so
    # nothing else is due: grad proposal 10/5, memo 10/9, midterm 10/14, brief
    # 10/28, term paper 12/2 all fall elsewhere.
    *[{"name": f"Discussion Paper {n} — {title}", "group": "Discussion Papers",
       "points": 20, "types": UPLOAD, "due": due(d),
       "sheet": "03 - Discussion Papers.md", "start": "## What you're doing",
       "label": "YELLOW", "rubric": "discussion", "lead": prompt_lead(n)}
      for n, title, d in [
          (1, "Growing Up Poor in America and policy feedback (Week 4)", "2026-09-18"),
          (2, "Deservingness in the safety net (Week 6)", "2026-10-02"),
          (3, "Two American Families and welfare reform (Week 9)", "2026-10-23"),
          (4, "Welfare reform and the ACA, with Poverty, Politics and Profit (Week 11)", "2026-11-06"),
          (5, "Gender, federalism, and design (Week 13)", "2026-11-20"),
      ]],

    # ---- Midterm (20%) ----------------------------------------------------
    {"name": "Midterm Exam", "group": "Midterm Exam", "points": 100, "types": ["on_paper"],
     "due": due("2026-10-14", 14, 15), "label": "RED",
     "body": "<p>In class, written by hand in a blue book, Wednesday, October 14, "
             "1:00&ndash;2:15 p.m. <strong>Bring a blue book.</strong></p>"
             "<p><strong>This exam is course-concept heavy.</strong> It draws on the "
             "architecture of the American welfare state, the political development of its "
             "programs, policy feedback, institutional design, and the arguments we will have "
             "had about who the poor are and how we decided to help them &mdash; from the "
             "assigned readings and from class.</p>"
             "<p>It closes with <strong>one question about your own program or research "
             "topic</strong>, which by then you will have chosen and begun working in the "
             "sources. The final exam in December is the reverse: mostly your topic, applying "
             "the concepts throughout.</p>"
             "<p>A review session runs Monday, October 12.</p>"},

    # ---- Major Written Work (40%) — undergraduate track --------------------
    {"name": "Policy Brief: Program Selection (Undergraduates)",
     "group": "Major Written Work", "points": 0, "types": TEXT_OR_UPLOAD,
     "grading_type": "pass_fail", "due": due("2026-09-21"),
     "sheet": "05 - Policy Brief - Program Selection.md", "label": "YELLOW"},

    {"name": "Policy Brief: Source and Claims Memo (Undergraduates)",
     "group": "Major Written Work", "points": 50, "types": UPLOAD,
     "due": due("2026-10-09"), "sheet": "06 - Policy Brief - Source and Claims Memo.md",
     "label": "YELLOW", "rubric": "memo"},

    {"name": "Policy Brief (Undergraduates)", "group": "Major Written Work", "points": 150,
     "types": UPLOAD, "due": due("2026-10-28"), "sheet": "07 - Policy Brief.md",
     "label": "YELLOW", "rubric": "brief"},

    {"name": "Term Paper (Undergraduates)", "group": "Major Written Work", "points": 200,
     "types": UPLOAD, "due": due("2026-12-02"), "sheet": "08 - Term Paper.md",
     "label": "YELLOW", "rubric": "term"},

    # ---- Major Written Work (40%) — graduate track -------------------------
    {"name": "Research Proposal (Graduate students)", "group": "Major Written Work",
     "points": 100, "types": UPLOAD, "due": due("2026-10-05"),
     "sheet": "09 - Graduate Research Proposal.md", "label": "YELLOW", "rubric": "proposal"},

    {"name": "Introduction, Outline, and Annotated Bibliography (Graduate students)",
     "group": "Major Written Work", "points": 100, "types": UPLOAD, "due": due("2026-12-02"),
     "sheet": "10 - Graduate Introduction, Outline, and Annotated Bibliography.md",
     "label": "YELLOW", "rubric": "outline"},

    # Due at the start of the final exam session, per the sheet.
    {"name": "Final Research Paper (Graduate students)", "group": "Major Written Work",
     "points": 200, "types": UPLOAD, "due": due("2026-12-14", 13, 0),
     "sheet": "11 - Graduate Final Research Paper.md", "label": "YELLOW", "rubric": "gradfinal"},

    # ---- Final Exam (20%) -------------------------------------------------
    {"name": "Final Exam", "group": "Final Exam", "points": 100,
     "types": ["on_paper"], "due": due("2026-12-14", 14, 50), "label": "RED",
     "body": "<p>In class, written by hand in a blue book. <strong>Monday, December 14, "
             "1:00&ndash;2:50 p.m., GH 305. Bring a blue book.</strong></p>"
             "<p>This is not a survey of the whole course. It asks you to write at length about "
             "<strong>your own program or research topic</strong> &mdash; what it does, whom it "
             "reaches, how it was built, and what you would change &mdash; using the concepts and "
             "evidence of the course. If you have done your own work all semester, you are already "
             "prepared for it. Graduate final research papers are due at the start of this "
             "session.</p>"},
]

# --------------------------------------------------------------------------
# Rubrics.  Criterion weights are copied from the "How it's graded" tables in
# the sheets; nothing here is invented EXCEPT the four equal weights on the
# Source and Claims Memo, whose table deliberately carries no weights.
# --------------------------------------------------------------------------
FULL, STRONG, PARTIAL, NONE = 1.0, 0.75, 0.5, 0.0


def graded(points, full_desc, partial_desc=None):
    """Four-level rating scale for a weighted criterion."""
    return [
        ("Full marks", round(points * FULL, 2), full_desc),
        ("Strong", round(points * STRONG, 2), "Meets the criterion with gaps in depth or precision."),
        ("Partial", round(points * PARTIAL, 2),
         partial_desc or "Addresses the criterion but does not meet it."),
        ("Not met", 0, "Does not address the criterion."),
    ]


RUBRICS = {
    "discussion": ("Discussion Paper", [
        ("Engagement and position", 20,
         "Engages a specific claim from the assigned reading, quoted or closely paraphrased "
         "with a page number; takes a defensible position and supports it from the reading.",
         [("Full credit", 20, "Engages a specific claim, takes a defensible position, supports "
                              "it from the reading; in a film week, specific film detail, a "
                              "specific reading claim, and a defended relationship between them."),
          ("Partial credit", 10, "Summarizes accurately but does not take or defend a position, "
                                 "or engages film and reading but stays general."),
          ("No credit", 0, "Does not engage the assigned reading, or, in a film week, could "
                           "have been written without watching the film.")])]),

    # Four criteria, no weights given in the sheet -> split equally. FLAGGED.
    "memo": ("Source and Claims Memo", [
        ("Claims are specific", 12.5,
         "Statements about this program that could turn out to be wrong, rather than "
         "generalities that could not.", None),
        ("The columns are honest", 12.5,
         "Column A claims tie to a named source you have read; Column B actually has things in "
         "it. A memo claiming everything is supported scores lower than one admitting half is "
         "assumed.", None),
        ("Sources are real and read", 12.5,
         "Each source exists, says what you say it says, and you can discuss it.", None),
        ("Direction is visible", 12.5,
         "The closing note says what you still need to find out.", None),
    ]),

    "brief": ("Policy Brief", [
        ("Stated purpose", 22.5,
         "Accurate account of design intent, with the gap between stated purpose and actual "
         "operation named where one exists.", None),
        ("Who it serves", 30,
         "Eligibility, enrollment, and exclusion distinguished and explained.", None),
        ("Design features", 30,
         "Financing, benefits, and administration described accurately and tied to "
         "consequences.", None),
        ("Reform debate: position and defense", 45,
         "A position taken and defended against the strongest available counterargument, stated "
         "fairly. A both-sides summary earns at most half.",
         [("Full marks", 45, "A position taken and defended against the strongest available "
                             "counterargument, stated fairly."),
          ("Strong", 33.75, "A position defended, but against a weaker counterargument than the "
                            "strongest available."),
          ("At most half — both-sides summary", 22.5,
           "Presents both sides and declines to judge. Per the assignment, this has not "
           "completed the element."),
          ("Not met", 0, "No position, or no engagement with the reform debate.")]),
        ("Evidence and citation", 22.5,
         "Primary sources including at least one published before 1996; figures verified; no "
         "uncited claims; APA.", None),
    ]),

    "term": ("Term Paper", [
        ("Problem definition", 30, "Specific, evidenced, arguable.", None),
        ("Application of course concepts", 60,
         "Policy feedback, institutional design, interest groups, or public opinion used to "
         "explain why the problem persists, not merely named.", None),
        ("Reform proposal", 50,
         "Specific enough to act on, and connected to the analysis that precedes it.", None),
        ("Political obstacles", 30, "Who loses, who blocks, what would have to change.", None),
        ("Evidence, citation, writing", 30,
         "Sources carried forward and extended; APA; readable.", None),
    ]),

    "proposal": ("Graduate Research Proposal", [
        ("Research question", 30, "Specific, answerable, non-obvious.", None),
        ("Significance", 20, "A clear account of what answering it contributes.", None),
        ("Working thesis", 15, "A stated expectation, not a hedge.", None),
        ("Bibliography", 35,
         "Six or more credible sources, scholarly among them, each with a reason for inclusion, "
         "all verified real.", None),
    ]),

    "outline": ("Graduate Introduction, Outline, and Annotated Bibliography", [
        ("Introduction and thesis", 25, "Arguable claim, clear roadmap.", None),
        ("Outline", 30, "Argument flow visible; evidence attached to claims.", None),
        ("Annotations", 30,
         "Accurate on what each source argues, and specific about its relation to your project.",
         None),
        ("Evidence of revision", 15,
         "Demonstrable development from the October proposal.", None),
    ]),

    "gradfinal": ("Graduate Final Research Paper", [
        ("Thesis and argument", 50,
         "Arguable, sustained, and actually argued rather than asserted.", None),
        ("Synthesis and use of concepts", 50,
         "Literature in conversation; course concepts doing analytic work.", None),
        ("Evidence", 40, "Appropriate, accurate, verified, sufficient to the claims.", None),
        ("Counterargument and limitations", 30,
         "Strongest objection stated fairly and answered; limits acknowledged.", None),
        ("Writing and citation", 30, "Organized, readable, APA throughout.", None),
    ]),
}


def build_rubric_payload(key, assignment_id, assignment_name):
    # Title after the assignment: the discussion-paper and documentary rubrics
    # are reused across many assignments, and a shared title makes Canvas
    # auto-suffix them "(1)", "(2)"... which breaks idempotent lookup.
    _, criteria = RUBRICS[key]
    title = f"{assignment_name} — rubric"
    crit = {}
    total = 0
    for i, (desc, pts, long_desc, ratings) in enumerate(criteria):
        levels = ratings if ratings else graded(pts, long_desc)
        crit[str(i)] = {
            "description": desc,
            "long_description": long_desc,
            "points": pts,
            "criterion_use_range": False,
            "ratings": {str(j): {"description": rd, "points": rp, "long_description": rl}
                        for j, (rd, rp, rl) in enumerate(levels)},
        }
        total += pts
    return {
        "rubric": {"title": title, "points_possible": total,
                   "free_form_criterion_comments": True, "criteria": crit},
        "rubric_association": {"association_id": assignment_id, "association_type": "Assignment",
                               "use_for_grading": True, "hide_score_total": False,
                               "purpose": "grading"},
    }


def main():
    require_env()
    course = api("GET", f"/api/v1/courses/{COURSE_ID}")
    print(f"Course: {course['name']} ({course['workflow_state']})\n")

    # Weighted groups, and turn on weighting at the course level.
    existing = {g["name"]: g for g in list_all(f"/api/v1/courses/{COURSE_ID}/assignment_groups")}
    gid = {}
    for i, g in enumerate(GROUPS, start=1):
        # Drop rules are applied after the assignments exist; Canvas rejects a
        # drop_lowest higher than the current assignment count.
        payload = {"name": g["name"], "group_weight": g["weight"], "position": i}
        if g["name"] in existing:
            res = api("PUT", f"/api/v1/courses/{COURSE_ID}/assignment_groups/"
                             f"{existing[g['name']]['id']}", payload)
            print(f"  group updated : {g['name']} ({g['weight']}%)")
        else:
            res = api("POST", f"/api/v1/courses/{COURSE_ID}/assignment_groups", payload)
            print(f"  group created : {g['name']} ({g['weight']}%)")
        gid[g["name"]] = res["id"]
    api("PUT", f"/api/v1/courses/{COURSE_ID}",
        {"course": {"apply_assignment_group_weights": True}})
    print("  weighting     : enabled\n")

    have = {a["name"]: a for a in list_all(f"/api/v1/courses/{COURSE_ID}/assignments")}
    made = []
    for spec in A:
        body = spec.get("body") or ""
        if spec.get("sheet"):
            body = sheet_html(spec["sheet"], spec.get("start"))
        parts = [label_html(spec.get("label")), spec.get("lead", ""), body]
        if spec.get("flag"):
            parts.insert(0, flag_html(spec["flag"]))
        html = "\n".join(p for p in parts if p)

        payload = {
            "name": spec["name"],
            "description": html,
            "points_possible": spec["points"],
            "grading_type": spec.get("grading_type", "points"),
            "submission_types": spec["types"],
            "assignment_group_id": gid[spec["group"]],
            "published": False,
        }
        if spec.get("due"):
            payload["due_at"] = spec["due"]

        if spec["name"] in have:
            res = api("PUT", f"/api/v1/courses/{COURSE_ID}/assignments/{have[spec['name']]['id']}",
                      {"assignment": payload})
            verb = "updated"
        else:
            res = api("POST", f"/api/v1/courses/{COURSE_ID}/assignments",
                      {"assignment": payload})
            verb = "created"
        made.append((res, spec))
        flag = "  <-- FLAG" if spec.get("flag") else ""
        print(f"  {verb:7s} {spec['points']:>4} pts  {spec['name'][:62]}{flag}")

    # Now that the assignments exist, the drop rules will validate.
    for g in GROUPS:
        if g.get("rules"):
            api("PUT", f"/api/v1/courses/{COURSE_ID}/assignment_groups/{gid[g['name']]}",
                {"name": g["name"], "group_weight": g["weight"], "rules": g["rules"]})
            print(f"\n  rule applied  : {g['name']} -> {g['rules'].strip()}")

    # Rubrics: the five discussion papers share one definition (a copy per assignment).
    print()
    existing_rubrics = {r["title"]: r for r in list_all(f"/api/v1/courses/{COURSE_ID}/rubrics")}
    for res, spec in made:
        key = spec.get("rubric")
        if not key:
            continue
        payload = build_rubric_payload(key, res["id"], spec["name"])
        title = payload["rubric"]["title"]
        if title in existing_rubrics:
            payload["id"] = existing_rubrics[title]["id"]
            api("PUT", f"/api/v1/courses/{COURSE_ID}/rubrics/{existing_rubrics[title]['id']}",
                payload)
            print(f"  rubric updated: {spec['name'][:60]}")
        else:
            api("POST", f"/api/v1/courses/{COURSE_ID}/rubrics", payload)
            print(f"  rubric created: {spec['name'][:60]}")

    print(f"\nDone. {len(GROUPS)} groups, {len(A)} assignments. All unpublished.")


if __name__ == "__main__":
    sys.exit(main())
