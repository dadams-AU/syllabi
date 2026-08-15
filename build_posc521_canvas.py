#!/usr/bin/env python3
"""Build the POSC 521 (Fall 2026) Canvas shell: pages, modules, and module items.

Course 3592849. Companion to build_posc521_assignments.py, which owns the
assignment groups, assignments, due dates, and rubrics. This script owns
everything else: the front page, the AI policy page, the week modules, and the
placement of assignments inside those modules.

Idempotent. Pages are matched by title, modules by name, and module items by
title, so re-running after a syllabus change updates in place rather than
duplicating. Everything is created unpublished except the front page, which
Canvas requires to be published before it can be designated as such.

Content is transcribed from
  POSC 521 MPA Capstone/2026-27 Fall/posc521_2026_fall.tex
Where the two disagree, the .tex governs and this script is the thing to fix.

Usage:  python3 build_posc521_canvas.py [--dry-run]

Requires CANVAS_BASE_URL and CANVAS_TOKEN in the environment.
"""

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

COURSE_ID = 3592849
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")
DRY_RUN = "--dry-run" in sys.argv

COURSE_DIR = "/home/dadams/Repos/syllabi/POSC 521 MPA Capstone/2026-27 Fall"
SYLLABUS_PDF = os.path.join(COURSE_DIR, "posc521_2026_fall.pdf")
SYLLABUS_PDF_MARKER = "<!--SYLLABUS_PDF_LINK-->"

TRACK_A = "track-a-the-self-critique-protocol"
TRACK_B = "track-b-using-the-approved-prompts"
AI_POLICY_TITLE = "Policy on the Use of Generative AI and Other Technology"
HOME_TITLE = "Course Home"


# --- Canvas plumbing -------------------------------------------------------
def require_env():
    missing = [n for n, v in (("CANVAS_BASE_URL", BASE_URL), ("CANVAS_TOKEN", TOKEN)) if not v]
    if missing:
        raise SystemExit(f"Missing required environment variable(s): {', '.join(missing)}")


def api(method, path, payload=None, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} failed: {e.code} {e.read().decode()[:500]}")
    return json.loads(body) if body else None


def list_all(path):
    rows, page = [], 1
    while True:
        batch = api("GET", path, params={"per_page": 100, "page": page})
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        page += 1


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Canvas' upload step answers 3xx; we need the Location, not a blind follow."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _multipart(fields, field_name, filename, payload, content_type):
    boundary = uuid.uuid4().hex
    out = []
    for key, value in fields.items():
        out.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n"
                   .encode("utf-8"))
    out.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; "
        f"filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode("utf-8"))
    out.append(payload)
    out.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def upload_file(local_path, folder_path="course files"):
    """Canvas three-step upload: request a slot, POST the bytes, confirm."""
    name = os.path.basename(local_path)
    content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(local_path, "rb") as fh:
        payload = fh.read()

    slot = api("POST", f"/api/v1/courses/{COURSE_ID}/files", {
        "name": name,
        "size": len(payload),
        "content_type": content_type,
        "parent_folder_path": folder_path,
        "on_duplicate": "overwrite",
    })

    body, ctype = _multipart(slot["upload_params"], "file", name, payload, content_type)
    req = urllib.request.Request(slot["upload_url"], data=body,
                                 headers={"Content-Type": ctype}, method="POST")
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=300) as resp:
            location, raw = resp.headers.get("Location"), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303):
            raise
        location, raw = exc.headers.get("Location"), ""

    if location:
        return api("GET", location)
    return json.loads(raw)


def ensure_syllabus_pdf():
    """Return the Canvas file object for the syllabus PDF, uploading if needed."""
    if not os.path.exists(SYLLABUS_PDF):
        print(f"  !! syllabus PDF not found at {SYLLABUS_PDF}; leaving placeholder")
        return None
    name = os.path.basename(SYLLABUS_PDF)
    local_size = os.path.getsize(SYLLABUS_PDF)
    for f in list_all(f"/api/v1/courses/{COURSE_ID}/files"):
        if f.get("display_name") == name:
            if f.get("size") == local_size:
                print(f"  file current  : {name} (id {f['id']})")
                return f
            print(f"  file stale    : {name} -> re-uploading")
            break
    if DRY_RUN:
        print(f"  file would upload: {name}")
        return None
    uploaded = upload_file(SYLLABUS_PDF)
    print(f"  file uploaded : {name} (id {uploaded['id']}, {uploaded['size']:,} bytes)")
    return uploaded


def syllabus_link_html(f, label="Download the full syllabus (PDF)"):
    if not f:
        return f'<p><strong>[UPLOAD THE SYLLABUS PDF AND LINK IT HERE: {label}]</strong></p>'
    href = f"/courses/{COURSE_ID}/files/{f['id']}"
    return (
        f'<a class="instructure_file_link inline_disabled" '
        f'title="{f["display_name"]}" href="{href}?wrap=1" target="_blank" '
        f'rel="noopener" data-api-endpoint="{BASE_URL}/api/v1/courses/{COURSE_ID}/files/{f["id"]}" '
        f'data-api-returntype="File">{label}</a>'
    )


# --- Design tokens (shared with the POSC 459 build) ------------------------
NAVY, ACCENT, INK = "#00244E", "#C25100", "#1F2933"
MUTED, LINE, WASH = "#52606D", "#D8DEE6", "#F4F7FA"
RED_INK, YELLOW_INK = "#8C1D18", "#7A4B00"

TABLE_STYLE = ' style="border-collapse:collapse;width:100%;"'
TD = ' style="border:1px solid #ccc;padding:6px 10px;"'
# scope="col" is required for screen readers to associate cells with headers.
TH = (' scope="col" style="border:1px solid #ccc;padding:6px 10px;'
      'background:#eee;text-align:left;"')

CARD = (f"flex:1 1 240px;border:1px solid {LINE};border-left:5px solid {NAVY};"
        "border-radius:6px;padding:16px 18px;background:#fff;min-width:240px;")
CARD4 = (f"flex:1 1 42%;border:1px solid {LINE};border-left:5px solid {NAVY};"
         "border-radius:6px;padding:16px 18px;background:#fff;min-width:280px;")
PILL = (f"display:inline-block;background:{WASH};border:1px solid {LINE};border-radius:999px;"
        f"padding:3px 12px;margin:0 6px 6px 0;font-size:0.85em;color:{INK};")
H2 = f' style="border-bottom:3px solid {ACCENT};padding-bottom:6px;"'
ROW = "display:flex;flex-wrap:wrap;gap:16px;margin:18px 0 26px;"

AI_HREF = f"/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology"
A_HREF = f"/courses/{COURSE_ID}/pages/{TRACK_A}"
B_HREF = f"/courses/{COURSE_ID}/pages/{TRACK_B}"


# --------------------------------------------------------------------------
# Front page.  The Canvas page title renders as the H1, so the body opens
# with its own banner and headings start at H2.
# --------------------------------------------------------------------------
HOME_BODY = f"""
<div style="background:{NAVY};color:#fff;padding:26px 28px;border-radius:8px;">
  <div style="font-size:0.8em;letter-spacing:0.14em;text-transform:uppercase;opacity:0.85;">
    Fall 2026 &middot; Section 01 &middot; Schedule Code 16622</div>
  <div style="font-size:1.85em;font-weight:700;line-height:1.2;margin:6px 0 4px;">
    POSC 521: MPA Capstone Seminar</div>
  <div style="font-size:1.15em;opacity:0.95;margin-bottom:12px;">Public Administration Theory</div>
  <div style="font-size:1.02em;opacity:0.95;">
    Mondays, 7:00&ndash;9:45 p.m. &middot; Gordon Hall 204 &middot; 3 units &middot; hybrid<br>
    First class Monday, August 24 &middot; Dr. David P. Adams</div>
</div>

<p style="font-size:1.08em;line-height:1.6;margin:22px 0 14px;">This is the culminating seminar of
the MPA program, and it rests on a single premise: <strong>you are here to master public
administration, not to survey it.</strong></p>

<p style="line-height:1.6;">Mastery means something specific. It means you can state what Wilson
actually argued and explain why Simon thought the whole edifice was incoherent. It means that when
you meet a contested problem, you can select the two or three theories that genuinely bear on it,
justify that selection, and defend it against a colleague who would have chosen differently. It
means you know where the field's arguments remain unsettled, and you can say something useful about
why they stay that way. Coverage is not mastery, and a response that names every framework while
commanding none of them is the single most common way that otherwise strong students fail the
comprehensive exam.</p>

<p style="background:{WASH};border-left:5px solid {ACCENT};padding:12px 16px;line-height:1.6;">
This is a professional degree. You are entering a field where the cost of shallow judgment is paid
by the public, and usually by the part of the public with the least room to absorb it. Read
accordingly.</p>

<h2{H2}>Start here</h2>

<div style="{ROW}">
  <div style="{CARD4}">
    <div style="font-weight:700;font-size:1.05em;margin-bottom:6px;color:{NAVY};">Course syllabus</div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">The governing document. Texts, the
    full week-by-week schedule, grading, every assignment in detail, and every policy.
    {SYLLABUS_PDF_MARKER} and keep it.</div>
  </div>
  <div style="{CARD4}">
    <div style="font-weight:700;font-size:1.05em;margin-bottom:6px;">
      <a href="{AI_HREF}" style="color:{NAVY};">AI policy</a></div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">AI is permitted here in exactly one
    form: as a source of questions you have to answer yourself. Nine of the eleven assignment types
    are RED. <strong>Read this before Week 2.</strong></div>
  </div>
  <div style="{CARD4}">
    <div style="font-weight:700;font-size:1.05em;margin-bottom:6px;">
      <a href="{A_HREF}" style="color:{NAVY};">Track A: the self-critique protocol</a></div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">The no-AI feedback track. Available
    to you immediately, costs you nothing in points or standing, and needs no justification.</div>
  </div>
  <div style="{CARD4}">
    <div style="font-weight:700;font-size:1.05em;margin-bottom:6px;">
      <a href="{B_HREF}" style="color:{NAVY};">Track B: the approved prompts</a></div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">The AI feedback track, ChatGPT Edu
    only, prompts copied verbatim, full transcript in your appendix.
    <strong>Request Edu access in Week 1.</strong></div>
  </div>
</div>

<h2{H2}>How a week works</h2>

<p>Weeks 4 through 11 run the same cycle. Learn it once and the semester stops being a surprise.</p>

<table{TABLE_STYLE}>
<thead><tr><th{TH}>When</th><th{TH}>What</th><th{TH}>AI</th></tr></thead>
<tbody>
<tr><td{TD}><strong>Monday, by class time</strong></td>
    <td{TD}>Annotated bibliography (5 pts) and rough draft synthesis paper, three pages (10 pts)</td>
    <td{TD} nowrap><span style="color:{YELLOW_INK};font-weight:700;">YELLOW</span> /
           <span style="color:{RED_INK};font-weight:700;">RED</span></td></tr>
<tr><td{TD}><strong>Monday, in class</strong></td>
    <td{TD}>Discussion, then the 30-minute peer review studio. Two actionable suggestions and one
    question to your partner, in writing, before you leave.</td>
    <td{TD}><span style="color:{RED_INK};font-weight:700;">RED</span></td></tr>
<tr><td{TD}><strong>Wednesday, 11:59 p.m.</strong></td>
    <td{TD}>Final synthesis paper, four pages maximum, deep on no more than three readings, page
    numbers on every claim about a text (20 pts)</td>
    <td{TD}><span style="color:{YELLOW_INK};font-weight:700;">YELLOW</span></td></tr>
<tr><td{TD}><strong>Friday, 11:59 p.m.</strong></td>
    <td{TD}>Personal reflection, 250&ndash;300 words (10 pts)</td>
    <td{TD}><span style="color:{RED_INK};font-weight:700;">RED</span></td></tr>
</tbody>
</table>

<p style="margin-top:14px;"><strong>The Feedback Appendix rides along every week</strong>, on either
track. It is the completed protocol or transcript itself, handed in; there is no separate document to
write. It is diagnostic: it informs next week's work and may not be used to revise the submission it
critiques. What gets scored is what you did with the critique, never the quality of the critique you
received.</p>

<h2{H2}>The weeks that break the pattern</h2>

<table{TABLE_STYLE}>
<thead><tr><th{TH}>Week</th><th{TH}>What is different</th></tr></thead>
<tbody>
<tr><td{TD}><strong>Week 2 (8/31)</strong></td><td{TD}>No synthesis paper. You build the
Comparative Matrix instead &mdash; four columns, rows you derive yourself, due Friday 9/4. It is the
instrument you will think with all semester, and it becomes your Field Map in Week 12.</td></tr>
<tr><td{TD}><strong>Weeks 3&ndash;4 (9/7, 9/14)</strong></td><td{TD}>Labor Day closes campus on 9/7,
so the classical foundations get a two-week runway. Week 3 is reading only, with the annotated
bibliography due Friday 9/11. Week 4 discusses the whole set.</td></tr>
<tr><td{TD}><strong>Weeks 8 and 11 (10/12, 11/2)</strong></td><td{TD}>Book deep-dives on Lipsky and
on Balfour, Adams, and Nickels. Part A Monday, Part B Wednesday, reflection Friday, no AI at any
point on either track.</td></tr>
<tr><td{TD}><strong>Week 12 (11/9)</strong></td><td{TD}>Integration seminar. Field Map due at class
time, three-minute presentations from everyone, and the comprehensive exam is distributed at
9:45 p.m.</td></tr>
<tr><td{TD}><strong>Week 13 (11/16)</strong></td><td{TD}>No meeting. The exam is due Monday at
4:59 p.m. Concentration paper guidelines post the same day, and you start
<em>Recoding America</em>.</td></tr>
<tr><td{TD}><strong>Week 14 (11/23)</strong></td><td{TD}>Fall recess. Nothing is due. Finish Pahlka
if you can; if you cannot, take the holiday and finish it next weekend.</td></tr>
<tr><td{TD}><strong>Weeks 15&ndash;16 and finals</strong></td><td{TD}>The concentration paper, in
three stages. Topic 11/30, literature review draft for the 12/7 workshop, final paper 12/14.</td></tr>
</tbody>
</table>

<h2{H2}>Dates worth putting in your calendar now</h2>

<table{TABLE_STYLE}>
<thead><tr><th{TH}>Date</th><th{TH}>What</th></tr></thead>
<tbody>
<tr><td{TD}>Mon, Aug 24</td><td{TD}>First class. No reading due. Read Denhardt and Denhardt
chs. 1&ndash;6 for Week 2, sign up for a facilitation pair, and request ChatGPT Edu if you intend to
use Track B.</td></tr>
<tr><td{TD}>Fri, Sep 4</td><td{TD}>Comparative Matrix, Version 1, and reflection, 11:59 p.m.</td></tr>
<tr><td{TD}>Fri, Sep 11</td><td{TD}>Annotated bibliography on the classical foundations,
11:59 p.m.</td></tr>
<tr><td{TD}>Mon, Sep 21</td><td{TD}>Twenty minutes in class on this course's AI policy, read as a
Friedrich&ndash;Finer case. Come prepared to argue.</td></tr>
<tr><td{TD}>Mon, Oct 12</td><td{TD}>Seminar Performance Checkpoint 1 returned (Weeks 2&ndash;7).</td></tr>
<tr><td{TD}><strong>Mon, Nov 9</strong></td><td{TD}><strong>Field Map due at class time.</strong>
Integration seminar. <strong>Comprehensive exam distributed at 9:45 p.m.</strong></td></tr>
<tr><td{TD}><strong>Mon, Nov 16</strong></td><td{TD}><strong>MPA comprehensive general area essay
exam due, 4:59 p.m.</strong> Two questions, answer one, 1,620 words maximum, pass/fail, no AI.</td></tr>
<tr><td{TD}>Mon, Nov 30</td><td{TD}>Concentration paper topic selection, 11:59 p.m.</td></tr>
<tr><td{TD}><strong>Mon, Dec 7</strong></td><td{TD}><strong>Last meeting.</strong> Literature review
draft due at class time, peer review, and three questions on your own paper put to you cold.
Checkpoint 2 is scored from this session.</td></tr>
<tr><td{TD}><strong>Mon, Dec 14</strong></td><td{TD}><strong>Final concentration area paper due,
11:59 p.m.</strong></td></tr>
<tr><td{TD}>Fri, Dec 18</td><td{TD}>Semester ends. Exam retake window, if you need one, runs through
this date.</td></tr>
</tbody>
</table>

<p style="margin-top:14px;"><span style="{PILL}">No class Mon, Sep 7 &mdash; Labor Day</span>
<span style="{PILL}">No class Nov 23&ndash;29 &mdash; fall recess</span>
<span style="{PILL}">Last day of classes Fri, Dec 11</span>
<span style="{PILL}">Finals week Dec 12&ndash;18</span></p>

<h2{H2}>How the grade works</h2>

<div style="{ROW}">
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">The weekly work &mdash; 40%</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Weekly readings assignments &mdash; <strong>35%</strong><br>
      Reading discussion facilitation &mdash; <strong>5%</strong></div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">The room &mdash; 13%</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Seminar performance &mdash; <strong>8%</strong><br>
      Integration seminar and Field Map &mdash; <strong>5%</strong></div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">The culminating work &mdash; 47%</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      MPA comprehensive essay exam &mdash; <strong>35%</strong><br>
      Concentration area paper &mdash; <strong>12%</strong></div>
  </div>
</div>

<p><strong>Seminar performance is scored, not counted.</strong> Volume is not the measure. The rubric
asks whether you can give an author's argument rather than its gist, whether you can say what you set
aside and why, whether you take an objection on its merits, and what you hand your partner in the
peer review studio. Its rubric can only score what I saw, so tell me in advance when a council
meeting or a shift takes your Monday, and we will talk about it.</p>

<h2{H2}>Four books</h2>

<ul style="line-height:1.7;">
<li>Denhardt, Janet V., and Robert B. Denhardt. 2015. <em>The New Public Service: Serving, Not
Steering.</em> 4th ed. Routledge. <span style="color:{MUTED};">Weeks 2, 5&ndash;7, 10</span></li>
<li>Lipsky, Michael. 2010. <em>Street-Level Bureaucracy: Dilemmas of the Individual in Public
Services.</em> Russell Sage Foundation. <span style="color:{MUTED};">Week 8</span></li>
<li>Balfour, Danny L., Guy B. Adams, and Ashley E. Nickels. 2020. <em>Unmasking Administrative
Evil.</em> 5th ed. Routledge. <span style="color:{MUTED};">Week 11</span></li>
<li>Pahlka, Jennifer. 2023. <em>Recoding America: Why Government Is Failing in the Digital Age and
How We Can Do Better.</em> Metropolitan Books. <span style="color:{MUTED};">Weeks 13&ndash;16</span></li>
</ul>

<p>Everything else is an article, and all of it is on Canvas or through Pollak Library.</p>

<h2{H2}>Reaching me</h2>

<div style="{ROW}">
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">David P. Adams, Ph.D.</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Gordon Hall 521<br>
      <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a><br>
      Phone or text: (657) 278-4770<br>
      <a href="https://dadams.io">dadams.io</a></div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">Office hours</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Mondays 12:00&ndash;2:00 and 5:30&ndash;6:30<br>
      Tuesdays 12:00&ndash;2:00<br>
      Or by <a href="https://dadams.io/appointments">appointment</a> any day<br>
      In person or by Zoom, ID 334 750 2639</div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">Response time</div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">Within 24 hours, weekends and
    holidays excepted. No answer in 24 hours, send a follow-up. No answer in 48, follow up again and
    text me.</div>
  </div>
</div>

<p style="background:{WASH};border-left:5px solid {NAVY};padding:12px 16px;line-height:1.6;">
<strong>A standing invitation, which I mean.</strong> This is a capstone in a field that studies how
rules get made, whom they burden, and whether they accomplish what they claim. That includes the
rules in this course. If you think a policy here is poorly designed, imposes burden it does not
justify, or fails on its own terms, say so, in class or to me directly. I would rather hear it in
week three than read it in evaluations.</p>
"""


# --------------------------------------------------------------------------
# AI policy page, transcribed from the syllabus.
# --------------------------------------------------------------------------
AI_POLICY_BODY = f"""
<p style="border-left:4px solid {ACCENT};padding:10px 14px;background:{WASH};">
<strong>Short version:</strong> if a tool suggests new words and you use them, that counts as AI use
under this policy. AI is permitted in this course in exactly one form: <strong>as a source of
questions you must answer yourself.</strong> Everything below is detail.</p>

<p><em>This page is the full policy as it appears in the syllabus. Where the two differ, tell me and
I will fix the one that is wrong.</em></p>

<h2{H2}>What counts as generative AI</h2>

<p>For this course, generative AI means any system capable of producing or suggesting human-like
text, images, data analysis, or other content, <strong>whether you asked for it or it appeared on its
own</strong>. Examples include:</p>

<ul>
<li>Large language models (ChatGPT, Claude, Gemini, Copilot, TitanGPT, and any successor products)</li>
<li>Text-to-image and multimodal generators (DALL-E, Midjourney, and equivalents)</li>
<li>AI writing assistants and summarizers</li>
<li>Automated coding, data, and content generators</li>
</ul>

<p><strong>AI built into tools you already use.</strong> This is the part people miss. The policy also
covers AI features embedded in ordinary software: Google Docs Smart Compose and &ldquo;Help me
write,&rdquo; Gmail Smart Reply, Microsoft Word Copilot, Apple Intelligence and other phone or
operating-system writing assistants, Google and Bing AI search summaries, and PDF readers or
reference managers that summarize sources or answer questions about them. <strong>You do not have to
feel like you &ldquo;used AI&rdquo; for it to count.</strong></p>

<p><strong>The test, for tools that do both.</strong> Most tools now flag <em>and</em> offer to fix.
The distinction is what the tool hands you: if it only flags a possible problem, that is basic
mechanics. If it proposes new wording, a summary, or a rewritten version for you to adopt, this
policy covers it. A squiggly underline is a flag; a suggested replacement sentence is generative,
even inside a spellchecker or grammar tool.</p>

<p><strong>What you can use freely, and where to go instead.</strong> Ordinary spelling, grammar, and
punctuation checking is always fine and never needs disclosure. Microsoft Word's built-in checker,
LanguageTool, and the flagging half of Grammarly are all permitted. The line is the one just above: a
tool that tells you something may be wrong is fine, and a tool that writes the replacement is
not.</p>

<p>If what you want is help making your writing <em>sound better</em>, that is a reasonable thing to
want, and in a capstone it is also the thing you are here to build. A rewrite button does not leave
the skill with you. <strong>The CSUF Writing Center</strong> (Pollak Library North 199, in person and
online, free, appointments and drop-in) does the same job in a way that does, and it works with
graduate writers. So will I, if you bring me a paragraph and ask what is making it land flat. Neither
of those requires disclosing anything and neither costs you points.</p>

<p><strong>Features you did not turn on.</strong> Some software has AI switched on by default.
<strong>What counts is what you adopt.</strong> If Word suggests the rest of your sentence and you
accept it, that is use; if it suggests and you ignore it, nothing has happened. You are responsible
for what you accept, not for what a company enabled without asking you. This is the one place Copilot
may appear in your workflow without your having chosen it, and the same rule applies. Turning these
features off removes the temptation and the ambiguity at once, and I am happy to show you how.</p>

<p><strong>On edge cases.</strong> AI is now embedded in enough ordinary software that neither of us
will anticipate every case. If you are unsure whether something counts, <strong>ask before you
submit</strong>. A good-faith question asked in advance is treated as exactly that. It is not a
confession and it does not put you under suspicion. The only version of this that creates a problem
is the one where you had the question and submitted anyway.</p>

<h2{H2}>The approved tool: ChatGPT Edu, and only ChatGPT Edu</h2>

<p>If you use AI in this course, you will use <strong>ChatGPT Edu</strong> through the CSU workspace,
authenticated with your CSUF credentials. No other tool is permitted for any graded work. This
includes TitanGPT, Microsoft Copilot, Google Gemini, Claude, a personal ChatGPT account under your own
email, and any paid consumer tier of any product.</p>

<ul>
<li><strong>Set this up in Week 1.</strong> ChatGPT Edu is not automatic. You must submit an opt-in
request through the CSUF IT service catalog and wait for provisioning (typically 30&ndash;60 minutes,
but do not test that assumption on a Sunday night). Instructions:
<a href="https://www.fullerton.edu/it/services/software/chatgpt-edu.html">fullerton.edu/it/services/software/chatgpt-edu.html</a>.</li>
<li><strong>Why one tool.</strong> Two reasons, and the second matters more than the first. Your data
stays inside a CSU agreement with real privacy protections. And every one of you gets the same
instrument. When students bring whatever they happen to subscribe to, the class quietly stratifies by
who can spend two hundred dollars a month, and the assignment stops measuring what it claims to
measure. One tool, one baseline, one standard.</li>
<li><strong>If you cannot get access</strong>, tell me. Do not substitute another tool and do not
stall. <a href="{A_HREF}">Track A</a> is available to you immediately and costs you nothing in points
or standing.</li>
</ul>

<h2{H2}>The rules, in full</h2>

<ul>
<li><strong>Approved prompts only, verbatim.</strong> The prompts on the
<a href="{B_HREF}">Track B page</a> and in the assignment descriptions are the only permitted
prompts. Copy them character for character. Do not add context, do not append a clarifying
instruction, do not ask a follow-up question, and do not continue the conversation after the tool
responds. One prompt, one response, done. A modified prompt is a policy violation regardless of how
reasonable the modification seems to you.</li>
<li><strong>Questions only.</strong> The approved prompts instruct the tool to return nothing but
questions. If it disregards its instructions and returns statements, assessments, or proposed text
anyway, that is not your violation, but you may not use that material, and it must still appear in
your transcript exactly as it came back.</li>
<li><strong>Never show it the readings.</strong> Do not upload, paste, quote at length, or summarize
an assigned reading for the tool. It may see your writing and nothing else. Metabolizing a reading is
the work itself; hand that to a tool and the work has not happened. Skipping it is how a capable
student ends up writing a comprehensive exam answer that touches every framework and understands
none.</li>
<li><strong>Complete transcript required.</strong> Your Feedback Appendix must contain the entire
exchange: your prompt as sent, the full unedited response, and the date. <strong>Paste the text into
the appendix.</strong> A share link may accompany it, but the link is not the record. Links break,
conversations get deleted, and no vendor promises to keep yours available as long as you want it. Copy
the exchange at the end of the session rather than at the deadline. Excerpts, paraphrases, and
tidied-up versions do not satisfy this requirement.</li>
<li><strong>Not allowed, on either track.</strong> Rough drafts, the Comparative Matrix, the weekly
personal reflections, your discussion-facilitation questions and post-class reflection, the Field Map,
the book deep-dive analyses, the comprehensive exam, and every stage of the concentration paper are
written entirely by you with <strong>no AI assistance whatsoever</strong>: no outlining, summarizing,
drafting, rewriting, or editing.</li>
<li><strong>Not allowed, ever.</strong> Using AI to draft, rewrite, restructure, or polish any portion
of submitted work, on any assignment, on either track.</li>
<li><strong>Diagnostic only.</strong> Feedback informs <strong>next week's</strong> work. It may not be
used to revise the submission it critiques.</li>
<li><strong>Allowed (basic mechanics).</strong> Grammarly is permitted for spelling, grammar, and
punctuation. Do not use it for rewriting, paraphrasing, or style transformation.</li>
</ul>

<h2{H2}>Assignment labels: GREEN, YELLOW, RED</h2>

<p>Every graded assignment in this course carries a label, printed on the assignment itself in Canvas
and listed in the table below. You should never have to infer one.</p>

<table{TABLE_STYLE}>
<thead><tr><th{TH}>Label</th><th{TH}>What it means here</th></tr></thead>
<tbody>
<tr><td{TD}><strong>GREEN</strong></td><td{TD}>Unused in this course. No assignment here leaves
general AI assistance open, so you will not see a GREEN label on anything, and its absence is
deliberate rather than an omission.</td></tr>
<tr><td{TD}><strong style="color:{YELLOW_INK};">YELLOW</strong></td><td{TD}>AI is permitted at one
specified point inside the assignment, under an approved prompt copied verbatim, with the complete
transcript in your Feedback Appendix. Two assignments carry this label. Permitted is not required: on
Track A you complete these same assignments with no AI at all and lose nothing for it.</td></tr>
<tr><td{TD}><strong style="color:{RED_INK};">RED</strong></td><td{TD}>No AI. The assignment is built
to be done without it, and doing it without it is the point.</td></tr>
</tbody>
</table>

<p style="margin-top:14px;"><strong>Labels are always written out</strong>, as the words GREEN,
YELLOW, and RED rather than as a color alone, so that nothing here depends on your being able to tell
two colors apart.</p>

<p><strong>The words carry across courses. What they permit does not.</strong> I use these three
labels in every course I teach, and you may meet them elsewhere in the division. What a given label
allows is always set by the assignment in front of you. A YELLOW in a course where AI may help you
search for sources is not the YELLOW defined above, and carrying that meaning into this seminar will
put you outside this policy. You are already tracking a different AI rule in every course you take,
which is a real burden and one I am contributing to; a shared vocabulary shrinks it and does not
remove it.</p>

<h2{H2}>Where AI fits, assignment by assignment</h2>

<p>Two assignments in this course admit AI, in one place inside each of them, under one approved
prompt. Everything else is yours alone. You should not have to work that out from the assignment
descriptions, so here is the whole course in one table.</p>

<table{TABLE_STYLE}>
<thead><tr><th{TH}>Assignment</th><th{TH}>Label</th><th{TH}>Where AI may be used</th></tr></thead>
<tbody>
<tr><td{TD}>Annotated bibliography (weekly)</td>
    <td{TD}><strong style="color:{YELLOW_INK};">YELLOW</strong></td>
    <td{TD}>Feedback Appendix only, Track B approved prompt</td></tr>
<tr><td{TD}>Final synthesis paper (weekly)</td>
    <td{TD}><strong style="color:{YELLOW_INK};">YELLOW</strong></td>
    <td{TD}>Feedback Appendix only, Track B approved prompt</td></tr>
<tr><td{TD}>Rough draft synthesis paper (weekly)</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td><td{TD}>Nowhere</td></tr>
<tr><td{TD}>Personal reflection (weekly)</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td><td{TD}>Nowhere</td></tr>
<tr><td{TD}>Comparative Matrix, Version 1 (Week 2)</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td>
    <td{TD}>Nowhere, on either track</td></tr>
<tr><td{TD}>Book deep-dive, Parts A and B (Weeks 8, 11)</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td>
    <td{TD}>Nowhere, on either track</td></tr>
<tr><td{TD}>Reading discussion facilitation</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td>
    <td{TD}>Nowhere: questions, activities, and the post-class reflection are yours</td></tr>
<tr><td{TD}>Seminar performance (both checkpoints)</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td>
    <td{TD}>Nowhere: nothing is submitted and nothing is written in advance</td></tr>
<tr><td{TD}>Field Map (Week 12)</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td>
    <td{TD}>Nowhere, on either track</td></tr>
<tr><td{TD}>MPA comprehensive general area essay exam</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td><td{TD}>Nowhere</td></tr>
<tr><td{TD}>Concentration area paper (every stage, including the 12/7 defense)</td>
    <td{TD}><strong style="color:{RED_INK};">RED</strong></td><td{TD}>Nowhere</td></tr>
</tbody>
</table>

<p style="margin-top:14px;">Basic mechanics are the exception that runs underneath all of it: spelling,
grammar, and punctuation checking is fine everywhere, including on the assignments listed as no-AI,
and it never needs disclosing.</p>

<p><strong>If an assignment carries no label, it is RED.</strong> Ask me and I will fix it, and asking
costs you nothing. This policy opens one narrow door, so silence is not a second one. An assignment I
forgot to mark is my oversight rather than a gap for you to work in.</p>

<h2{H2}>Why the policy is this narrow</h2>

<p>You deserve to know why rather than simply being told.</p>

<p>The comprehensive exam rewards depth. The answers that succeed are narrower and deeper: two or
three frameworks genuinely commanded, not every framework named. Unstructured AI use pushes writing in
exactly the opposite direction, toward responses that are impressively broad and genuinely shallow,
and that is the profile the exam is built to catch. Depth is what the exam measures, and depth is what
the profession requires.</p>

<p>This is because AI makes breadth cheap. Laziness has nothing to do with it. When summarizing a
fifth reading costs nothing, you summarize the fifth reading instead of sitting with the second one
until you understand what it is really claiming. The tool quietly relocates your effort from thinking
to assembling, and assembling feels productive right up until someone asks you a hard question.</p>

<p><strong>There is nobody in there.</strong> A language model holds no position and has no interests
or moral commitments; it returns the text that is probable given the text in front of it. When it
agrees with your thesis, nothing has agreed with you, and when its questions sound insightful, no one
found them insightful. A student who understands only that the output can be biased will keep arguing
with the tool as though someone were on the other side of it, and will start trusting it the moment it
sounds fair. Weber on rationalization and Simon on the limits of the administrative principles are
both, in their different ways, about what happens when a procedure gets mistaken for a judgment. You
read them in September.</p>

<p><strong>The same prompt does not return the same answer.</strong> These systems are probabilistic,
so an identical input run twice produces different output, sometimes different enough to change what
you would conclude about the tool. One run is not a test. If you try something once and like what
comes back, you have learned that the result is possible and nothing else. I found this out about my
own course materials this summer, in a single afternoon, by running one prompt twice and getting two
different answers, one of which I had already written up as a flaw in the prompt. I will show you both
transcripts.</p>

<p>So the policy narrows AI to the one function that cannot substitute for your thinking:
<strong>asking you questions you have to answer yourself</strong>.</p>

<h2{H2}>Ethics and responsible use</h2>

<ul>
<li><strong>Authorship.</strong> All submitted prose must be written by you. AI may provide critique,
but may not generate or rewrite your sentences, paragraphs, or structure.</li>
<li><strong>Attribution.</strong> When AI feedback is used, paste the complete transcript into the
Feedback Appendix with the date, and label it (&ldquo;ChatGPT Edu critique, 9/16/26&rdquo;). A share
link is welcome alongside the text and is not a substitute for it. Do not treat AI text as source
material to incorporate into your writing.</li>
<li><strong>Bias awareness.</strong> AI outputs reflect biases. Evaluate them critically for fairness
and accuracy.</li>
<li><strong>Verification.</strong> Validate AI-suggested facts or sources before using them in your
work.</li>
<li><strong>Confidentiality.</strong> Do not upload sensitive, private, or proprietary information
into AI tools. Several of you work in agencies; personnel matters, client records, and unpublished
agency data do not go into a chatbot, Edu tier or not. Assume anything you enter may be retained
<em>by the company</em>, indefinitely and beyond your reach. That is a separate question from whether
<em>you</em> will still be able to open a past conversation, which no vendor guarantees. Plan for
both: it may outlive your wanting it, and it may vanish before you need it.</li>
<li><strong>Sustainability.</strong> Be mindful of AI's environmental footprint and use tools
thoughtfully.</li>
<li><strong>Opting out is legitimate.</strong> If you would rather not use AI at all, for labor,
environmental, privacy, or any other principled reason, that is a respected choice in this course.
<a href="{A_HREF}">Track A</a> is available to you immediately and costs you nothing in points or
standing. You do not owe me a justification.</li>
</ul>

<p>Further reading:
<a href="https://genai.calstate.edu/communities/students/ethical-and-responsible-use-ai">CSU AI
Commons, Ethical and Responsible Use of AI for Students</a>.</p>

<h2{H2}>Repercussions for misuse</h2>

<ul>
<li><strong>Misuse includes</strong> submitting AI-generated or AI-edited prose as your own; using any
tool other than ChatGPT Edu; modifying an approved prompt; continuing a conversation past the single
approved exchange; showing an assigned reading to the tool; submitting an incomplete, edited, or
reconstructed transcript; using AI on a no-AI assignment; and using diagnostic feedback to revise the
submission it critiqued.</li>
<li>Consequences may include revision requirements, grade penalties, or formal academic integrity
proceedings under UPS 300.021.</li>
<li><strong>How I judge severity.</strong> These are not all the same thing and I will not treat them
as if they were. I weigh the nature of the assignment; whether the use replaced core intellectual work
or sat at the margins of it; <strong>whether the problem was a disclosure failure or a substantive
substitution</strong>; and whether it is a first occurrence or a repeated one. Submitting a tidied-up
transcript is an omission. Passing off generated analysis as your own is deception. They land in very
different places.</li>
<li><strong>On tool restrictions.</strong> The ChatGPT Edu requirement exists for equity, so that
everyone gets the same instrument rather than the class stratifying by who can afford a paid tier, and
for privacy, since your data stays inside a CSU agreement. If that reasoning does not fit your
situation, come tell me rather than quietly substituting.</li>
<li><strong>A note on detection.</strong> I am not going to pretend I can catch everything with
software, and <strong>I am not going to run your prose through an AI detector and treat the output as
evidence</strong>. Those tools are unreliable and their errors are not evenly distributed; they flag
multilingual writers and plain prose at higher rates, and making an accusation on that basis would be
bad reasoning of exactly the kind this degree trains you to refuse. Turnitin is used in this course
for source matching, which is a different instrument answering a different question, and its AI
indicator plays no part in how I evaluate your work. What I can do is read carefully, and ask you
about your own argument. If you cannot explain why you chose the sources you chose, defend the claims
you made, or account for the objection you did not address, the work does not meet the standard of
this course, whatever produced it. That conversation is the assessment.</li>
</ul>

<h2{H2}>How AI use is assessed</h2>

<p>AI use is evaluated by boundaries and learning, not polish.</p>

<ul>
<li>Compliance with the assignment-specific rules in the table above.</li>
<li>The <strong>Feedback Appendix</strong>, required every week. <strong>What is scored is what you
did with the critique, never the quality of the critique you received.</strong> On Track B that
distinction is a matter of fairness rather than generosity: the tool draws its questions from a
distribution, and two of you can send the identical prompt and get back questions of very different
use. You do not control the draw, so you are not graded on it. Submitting the complete transcript is a
condition of the assignment being complete; it is not a component of its score, and it has never cost
anyone points to disclose.</li>
<li>The <strong>Next-Week Plan</strong> (five to seven bullets) showing how you will apply the
critique to next week's work. This is the part of the appendix carrying the weight.</li>
<li>Independent engagement with readings and theory in discussion and in-class writing, scored under
seminar performance.</li>
<li>Final work that demonstrates original analysis and a consistent authorial voice.</li>
</ul>

<p>The goal is to treat AI as a <em>feedback partner</em>: a tool to sharpen your analysis, deepen
your questions, and strengthen your voice in public administration. If you cannot explain and defend
your argument, evidence choices, and revisions without external support, then the work does not meet
the course standard.</p>

<h2{H2}>Revisiting this policy</h2>

<p>This policy is a working document, not a settled one. AI is embedded in enough ordinary software
that good-faith students will hit cases neither of us anticipated: a search engine that summarizes a
source before you click it, a phone that offers to rewrite a sentence, a PDF reader that answers
questions about a reading. Some of that is hard to even notice, let alone name in a transcript.</p>

<p><strong>Week 5 carries a scheduled twenty minutes on this policy, and it is not a housekeeping
slot.</strong> Week 5 is the Friedrich&ndash;Finer week, and this policy is a Friedrich&ndash;Finer
problem at small scale. The transcript requirement, the single approved tool, and the verbatim-prompt
rule are external controls in Finer's sense: specified in advance, checkable by someone who was not
there, and indifferent to what you intended. The standard I actually assess by, that work you cannot
defend does not count as yours, is Friedrich's: an internal professional norm that no rule can verify
from the outside and no amount of compliance can produce. This document runs both instruments at once
and they do not sit comfortably together. Come prepared to say which one is doing the real work here,
and what the fact that I wrote both tells you about how administrative rules get made.</p>

<p>Bring edge cases to that session and to any other. A case you are unsure about is more useful to
the whole class than a rule I wrote in August.</p>
"""


# --------------------------------------------------------------------------
# Modules.  Week labels and readings transcribed from the .tex schedule.
# `notes` become SubHeader items; `assignments` are matched against the
# assignment list the companion script built.
# --------------------------------------------------------------------------
MODULES = [
    {
        "name": "Start Here",
        "notes": [],
        "pages": [HOME_TITLE, AI_POLICY_TITLE,
                  "Track A: The Self-Critique Protocol",
                  "Track B: Using the Approved Prompts"],
        "syllabus_pdf": True,
        "assignments": [],
    },
    {
        "name": "Week 1 (8/24) — Course Launch: What Mastery Means",
        "notes": [
            "Monday 8/24, in person: What Mastery Means, the Comprehensive Exam, and How This Course Works",
            "No reading due. Read Denhardt and Denhardt, The New Public Service, chs. 1–6 for Week 2.",
            "This week: sign up for a facilitation pair, and request ChatGPT Edu through CSUF IT if you intend to use Track B. Do not wait until Week 2.",
        ],
        "assignments": ["Reading Discussion Facilitation and Post-Class Reflection"],
    },
    {
        "name": "Week 2 (8/31) — Public Administration Theory I: The New Public Service",
        "notes": [
            "Monday 8/31, in person: Serving, Not Steering. Setting the frame — Old PA, New PA, NPM, NPS. Class discussion plus matrix-building workshop.",
            "Read: Denhardt and Denhardt, The New Public Service, chs. 1–6",
            "No synthesis paper this week. You are building the instrument instead.",
        ],
        "prefix": "Week 2 - ",
    },
    {
        "name": "Week 3 (9/7) — Classical Foundations: Reading Week (Labor Day)",
        "notes": [
            "No class meeting: Labor Day, campus closed",
            "Read (the heaviest set of the semester; the two-week runway is deliberate): Wilson (1887), “The Study of Administration”; Weber (1946), “Bureaucracy”; Gulick (1937), “Notes on the Theory of Organization”; Follett (1926), “The Giving of Orders”; Simon (1946), “Proverbs of Administration”",
            "No synthesis paper and no reflection this week.",
        ],
        "prefix": "Week 3 - ",
    },
    {
        "name": "Week 4 (9/14) — Public Administration Theory II: Classical Foundations",
        "notes": [
            "Monday 9/14, in person: The Founding Arguments and Simon's Demolition. Class discussion plus peer review studio.",
            "Read: the Week 3 set, discussed in full",
        ],
        "prefix": "Week 4 - ",
    },
    {
        "name": "Week 5 (9/21) — Ethics and Values in Public Administration",
        "notes": [
            "Monday 9/21, in person: Public Service Values and Ethics. Class discussion plus peer review studio.",
            "Read: Friedrich (1940), “Public Policy and the Nature of Administrative Responsibility”; Finer (1941), “Administrative Responsibility in Democratic Government”; Goss (1996), “A Distinct Public Administration Ethics?”; Denhardt and Denhardt, ch. 7",
            "Also in class, 20 minutes: this course's AI policy, read as a Friedrich–Finer case. We return to the question in Week 11, and it will not survive the encounter intact. Keep your answer somewhere you can find it.",
            "Friday's reflection adds or revises at least one Comparative Matrix row (Denhardt ch. 7).",
        ],
        "prefix": "Week 5 - ",
    },
    {
        "name": "Week 6 (9/28) — Leadership and Motivation",
        "notes": [
            "Monday 9/28, in person: Leadership and Motivation. Class discussion plus peer review studio.",
            "Read: Christensen, Paarlberg, and Perry (2017), “Public Service Motivation Research”; Denhardt and Denhardt, ch. 8; Lachance (2017), “Public Service Motivation”; Perry and Wise (1990), “The Motivational Bases of Public Service”; Fairholm (2004), “Different Perspectives on the Practice of Leadership”",
            "Friday's reflection adds or revises at least one Comparative Matrix row (Denhardt ch. 8).",
        ],
        "prefix": "Week 6 - ",
    },
    {
        "name": "Week 7 (10/5) — Performance Management",
        "notes": [
            "Monday 10/5, in person: Performance Management. Class discussion plus peer review studio.",
            "Read: Behn (2003), “Why Measure Performance?”; Denhardt and Denhardt, ch. 9; Douglas and Ansell (2021), “Getting a Grip on Performance of Collaborations”; Marvel (2015), “Unconscious Bias in Citizens' Evaluations”; Nicholson-Crotty (2004), “Public Management and Organizational Performance”",
            "Friday's reflection adds or revises at least one Comparative Matrix row (Denhardt ch. 9).",
        ],
        "prefix": "Week 7 - ",
    },
    {
        "name": "Week 8 (10/12) — Street-Level Bureaucrats (Book Deep-Dive)",
        "notes": [
            "Monday 10/12, in person: Street-Level Bureaucrats. Class discussion plus peer review studio.",
            "Read: Lipsky (2010), Street-Level Bureaucracy",
            "Deep-dive week: Part A Monday, Part B Wednesday, reflection Friday. No AI at any point, on either track.",
            "Returned Monday 10/12: Seminar Performance, Checkpoint 1 (Weeks 2–7)",
        ],
        "prefix": "Week 8 - ",
        "assignments": ["Seminar Performance - Checkpoint 1 (Weeks 2-7)"],
    },
    {
        "name": "Week 9 (10/19) — Privatization and Contracting",
        "notes": [
            "Monday 10/19, in person: Privatization and Contracting. Class discussion plus peer review studio.",
            "Read: Milward and Provan (2000), “Governing the Hollow State”; Hood (1991), “A Public Management for All Seasons?”; Brown, Potoski, and Van Slyke (2006), “Managing Public Service Contracts”; Jos and Tompkins (2009), “Keeping it Public”; Rainey and Bozeman (2000), “Comparing Public and Private Organizations”",
        ],
        "prefix": "Week 9 - ",
    },
    {
        "name": "Week 10 (10/26) — 21st Century Challenges and Social Equity",
        "notes": [
            "Monday 10/26, in person: 21st Century Challenges. Class discussion plus peer review studio.",
            "Read: Maynard-Moody and Musheno (2012), “Social Equities and Inequities in Practice”; Gooden (2017), “Social Equity and Evidence”; McCandless et al. (2022), “A Long Road”; Denhardt and Denhardt, chs. 10–12",
            "Friday's reflection adds or revises at least one Comparative Matrix row (Denhardt chs. 10–12).",
        ],
        "prefix": "Week 10 - ",
    },
    {
        "name": "Week 11 (11/2) — Unmasking Administrative Evil (Book Deep-Dive)",
        "notes": [
            "Monday 11/2, in person: Technical Rationality, Moral Inversion, and the Masking of Administrative Evil. Class discussion plus peer review studio.",
            "Read: Balfour, Adams, and Nickels (2020), Unmasking Administrative Evil, 5th ed.",
            "Deep-dive week: Part A Monday, Part B Wednesday, reflection Friday. No AI at any point, on either track.",
        ],
        "prefix": "Week 11 - ",
    },
    {
        "name": "Week 12 (11/9) — Integration Seminar",
        "notes": [
            "Monday 11/9, in person: Assembling the Field. Three-minute Field Map presentations from every student, collective diagnosis of what we all missed, and open review. Bring your hardest unresolved question about the discipline.",
            "Read: revisit core course texts. Reread your own synthesis papers and your Comparative Matrix.",
            "Monday 11/9 at 9:45 p.m.: the MPA Comprehensive General Area Essay Exam is distributed.",
        ],
        "assignments": ["Field Map (Week 12)"],
    },
    {
        "name": "Week 13 (11/16) — Comprehensive Exam and Concentration Paper Launch",
        "notes": [
            "No class meeting. Asynchronous.",
            "Posted Monday 11/16: Concentration Area Paper guidelines and concentration-specific assignment sheets",
            "Begin reading: Pahlka (2023), Recoding America",
        ],
        "assignments": ["MPA Comprehensive General Area Essay Exam"],
    },
    {
        "name": "Week 14 (11/23) — Fall Recess",
        "notes": [
            "No class. Fall recess, 11/23–11/29. Campus open 11/23–11/25 and closed 11/26–11/27.",
            "Nothing is due this week. Finish Pahlka if you can; if you cannot, take the holiday and finish it next weekend.",
        ],
    },
    {
        "name": "Week 15 (11/30) — Concentration Area Paper: Topic",
        "notes": [
            "No class meeting. Asynchronous.",
            "Draft your literature review this week for Monday's workshop.",
        ],
        "assignments": ["Concentration Paper - Topic Selection"],
    },
    {
        "name": "Week 16 (12/7) — Concentration Area Paper Workshop",
        "notes": [
            "Monday 12/7, in person: Concentration Area Paper Workshop. Our last meeting.",
            "Peer review: come prepared to attack a classmate's tradeoff position, and to have yours attacked.",
            "Paper defense: three questions on your own paper, put to you cold. Seminar Performance Checkpoint 2 is scored from this session.",
            "Last day of classes: Friday 12/11",
        ],
        "assignments": ["Concentration Paper - Literature Review Draft",
                        "Seminar Performance - Checkpoint 2 (Weeks 8-16)"],
    },
    {
        "name": "Finals Week (12/12–12/18)",
        "notes": [
            "Comprehensive exam retake window, if you need one, runs through Friday 12/18.",
            "Semester ends Friday 12/18.",
        ],
        "assignments": ["Concentration Paper - Final Paper"],
    },
]


def resolve_assignments(mod, all_assignments):
    """Return the assignment objects belonging to a module, in due-date order."""
    by_due = lambda rows: sorted(rows, key=lambda a: (a["due_at"] or "9999", a["name"]))
    prefix = mod.get("prefix")
    picked = by_due([a for a in all_assignments if a["name"].startswith(prefix)]) if prefix else []
    named = []
    for name in mod.get("assignments", []):
        match = [a for a in all_assignments if a["name"] == name]
        if not match:
            raise SystemExit(f"REFUSING TO BUILD: no assignment named {name!r} in Canvas. "
                             "Run build_posc521_assignments.py first.")
        named += match
    # Week-cycle assignments first in due order, then the named extras (a
    # returned checkpoint belongs after the work of the week it interrupts).
    return picked + by_due(named)


def main():
    require_env()
    course = api("GET", f"/api/v1/courses/{COURSE_ID}")
    print(f"Course: {course['name']} ({course['workflow_state']})\n")

    assignments = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")
    print(f"  {len(assignments)} assignments found\n")

    syllabus_file = ensure_syllabus_pdf()
    pdf_link = syllabus_link_html(syllabus_file, "Download it")
    print()

    pages = [
        (HOME_TITLE, HOME_BODY, True),
        (AI_POLICY_TITLE, AI_POLICY_BODY, False),
    ]

    existing_pages = {p["title"]: p for p in list_all(f"/api/v1/courses/{COURSE_ID}/pages")}
    page_urls = {t: p["url"] for t, p in existing_pages.items()}

    for title, body, is_front in pages:
        body = body.replace(SYLLABUS_PDF_MARKER, pdf_link).strip()
        # Keep whatever publish state the page already has. Sending is_front on an
        # update unpublishes the AI policy page every time this runs, which is a
        # content sync quietly pulling a live page from students. The front page
        # stays published because a front page has to be. New pages start where
        # is_front says. (Modules are safe: published=False is only on create.)
        prior = existing_pages.get(title)
        published = bool(prior["published"]) if prior else is_front
        wiki = {"title": title, "body": body, "published": True if is_front else published}
        if is_front:
            wiki["front_page"] = True
        payload = {"wiki_page": wiki}
        if DRY_RUN:
            print(f"  page would sync: {title} ({len(body):,} bytes)")
            continue
        if title in existing_pages:
            res = api("PUT", f"/api/v1/courses/{COURSE_ID}/pages/{existing_pages[title]['url']}",
                      payload)
            print(f"  page updated  : {title}")
        else:
            res = api("POST", f"/api/v1/courses/{COURSE_ID}/pages", payload)
            print(f"  page created  : {title}")
        page_urls[title] = res["url"]

    for missing in ("Track A: The Self-Critique Protocol", "Track B: Using the Approved Prompts"):
        if missing not in page_urls:
            print(f"  !! page missing: {missing} (Start Here will skip it)")

    print()
    existing_mods = {m["name"]: m for m in list_all(f"/api/v1/courses/{COURSE_ID}/modules")}
    mod_ids = {}
    for i, mod in enumerate(MODULES, start=1):
        name = mod["name"]
        if name in existing_mods:
            mod_ids[name] = existing_mods[name]["id"]
            if existing_mods[name]["position"] != i and not DRY_RUN:
                api("PUT", f"/api/v1/courses/{COURSE_ID}/modules/{mod_ids[name]}",
                    {"module": {"position": i}})
            print(f"  module exists : {name}")
            continue
        if DRY_RUN:
            print(f"  module would create: {name}")
            mod_ids[name] = None
            continue
        res = api("POST", f"/api/v1/courses/{COURSE_ID}/modules",
                  {"module": {"name": name, "position": i, "published": False}})
        mod_ids[name] = res["id"]
        print(f"  module created: {name}")

    print()
    added = 0
    for mod in MODULES:
        mid = mod_ids[mod["name"]]
        have = set()
        if mid and not DRY_RUN:
            have = {it.get("title") for it in
                    list_all(f"/api/v1/courses/{COURSE_ID}/modules/{mid}/items")}

        items = []
        for note in mod.get("notes", []):
            items.append({"type": "SubHeader", "title": note})
        for title in mod.get("pages", []):
            if title in page_urls:
                items.append({"type": "Page", "page_url": page_urls[title], "title": title})
        if mod.get("syllabus_pdf") and syllabus_file:
            items.append({"type": "File", "content_id": syllabus_file["id"],
                          "title": syllabus_file["display_name"]})
        for a in resolve_assignments(mod, assignments):
            items.append({"type": "Assignment", "content_id": a["id"], "title": a["name"]})

        for pos, item in enumerate(items, start=1):
            if item["title"] in have:
                continue
            if DRY_RUN:
                print(f"  would add     : [{mod['name'][:26]:26}] {item['type']:10} {item['title'][:60]}")
                added += 1
                continue
            item["position"] = pos
            item["indent"] = 0 if item["type"] == "SubHeader" else 1
            api("POST", f"/api/v1/courses/{COURSE_ID}/modules/{mid}/items",
                {"module_item": item})
            print(f"  item added    : [{mod['name'][:26]:26}] {item['title'][:58]}")
            added += 1

    print(f"\nDone. {len(pages)} pages, {len(MODULES)} modules, {added} module items"
          f"{' (dry run, nothing written)' if DRY_RUN else ''}.")
    if not DRY_RUN:
        print(f"\nModules and their items are unpublished. '{HOME_TITLE}' is published and set as "
              "the front page.\nTo land students there instead of the module list: Home -> Choose "
              "Home Page -> Front Page.")


if __name__ == "__main__":
    sys.exit(main())
