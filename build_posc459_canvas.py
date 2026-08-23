#!/usr/bin/env python3
"""Build the POSC 459 (Fall 2026) Canvas shell.

Source of truth: POSC 459 Welfare Politics/posc459-syllabus-fa26-papyrus.tex
Follows AGENTS.md: everything created unpublished, week labels verbatim,
policy wording copied rather than summarized.

Idempotent by title/name: re-running updates existing pages and skips
modules that already exist.
"""
import json
import mimetypes
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

COURSE_ID = "3592717"
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")

HERE = os.path.dirname(os.path.abspath(__file__))
SYLLABUS_PDF = os.path.join(HERE, "POSC 459 Welfare Politics",
                            "posc459-syllabus-fa26-papyrus.pdf")
# Replaced at build time with a Canvas file link once the PDF is uploaded.
SYLLABUS_PDF_MARKER = "<!--SYLLABUS_PDF_LINK-->"


def require_env():
    missing = [n for n, v in (("CANVAS_BASE_URL", BASE_URL), ("CANVAS_TOKEN", TOKEN)) if not v]
    if missing:
        raise SystemExit(f"Missing required environment variable(s): {', '.join(missing)}")


def api(method, path, payload=None, params=None):
    if params:
        sep = "&" if "?" in path else "?"
        path = f"{path}{sep}{urllib.parse.urlencode(params, doseq=True)}"
    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc


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
    uploaded = upload_file(SYLLABUS_PDF)
    print(f"  file uploaded : {name} (id {uploaded['id']}, {uploaded['size']:,} bytes)")
    return uploaded


VAULT_459 = ("/home/dadams/obsidian-vaults/snags/9. Teaching/2026-T1 Fall/"
             "POSC 459 - Welfare Politics and Policy")


def vault_md_to_html(relpath):
    """Convert a vault note to Canvas HTML, dropping instructor-only callouts.

    Unlike the assignment sheets, this note carries its callout mid-document,
    so whole Obsidian callout blocks are removed in place rather than the file
    being truncated at the first one.
    """
    text = open(os.path.join(VAULT_459, relpath), encoding="utf-8").read()
    if text.startswith("---"):
        text = text[text.index("\n---", 3) + 4:]

    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        if re.match(r"^>\s*\[!", lines[i]):
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue
        out.append(lines[i])
        i += 1
    text = "\n".join(out)

    text = re.sub(r"^#\s+.*\n", "", text.lstrip("\n"), count=1)
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

    html = subprocess.run(["pandoc", "-f", "markdown+pipe_tables", "-t", "html",
                           "--wrap=none"], input=text, capture_output=True,
                          text=True, check=True).stdout.strip()
    for probe in ("instructor note", "not student-facing", "answer key"):
        if probe in html.lower():
            raise SystemExit(f"REFUSING TO BUILD: {relpath} still contains {probe!r}.")
    return html


def syllabus_link_html(f):
    if not f:
        return "<p><strong>[UPLOAD THE SYLLABUS PDF AND LINK IT HERE.]</strong></p>"
    href = f"/courses/{COURSE_ID}/files/{f['id']}"
    return (
        f'<p><a class="instructure_file_link inline_disabled" '
        f'title="{f["display_name"]}" href="{href}?wrap=1" target="_blank" '
        f'rel="noopener" data-api-endpoint="{BASE_URL}/api/v1/courses/{COURSE_ID}/files/{f["id"]}" '
        f'data-api-returntype="File">Download the full syllabus (PDF)</a></p>'
    )


# --------------------------------------------------------------------------
# Page bodies.  NOTE: the Canvas page title renders as the H1, so no body
# starts with <h1>; section headings begin at <h2>.
# --------------------------------------------------------------------------

TABLE_STYLE = ' style="border-collapse:collapse;width:100%;"'
TD = ' style="border:1px solid #ccc;padding:6px 10px;"'
TH = ' style="border:1px solid #ccc;padding:6px 10px;background:#eee;text-align:left;"'

AI_POLICY_BODY = f"""
<p>Generative AI is permitted in this course, but use must be transparent, intentional,
and in service of learning. The core principle is simple: <strong>you must do the
intellectual work of this course</strong>. AI can amplify your thinking, but not replace it.</p>

<p style="border-left:4px solid #666;padding:10px 14px;background:#f6f6f6;">
<strong>Short version:</strong> if a tool suggests new words and you use them, that counts
as AI use under this policy. And the rule that governs all of it: <strong>AI may identify problems
in your writing. It may not supply the prose that fixes them.</strong> Everything below is
detail.</p>

<p><em>This page is the full policy. The syllabus carries the short version; where the two
differ, this page governs and you should tell me so I can fix the syllabus.</em></p>

<h2>What counts as generative AI</h2>

<p>For this course, generative AI means any system that produces or suggests human-like text,
images, data analysis, or other content, <strong>whether you asked for it or it appeared on
its own</strong>. This includes:</p>

<ul>
<li>Large language models (ChatGPT, Claude, Gemini, Copilot, TitanGPT, and any successor products)</li>
<li>Text-to-image and multimodal generators (DALL-E, Midjourney, and equivalents)</li>
<li>AI writing assistants and summarizers</li>
<li>Automated coding, data, and content generators</li>
</ul>

<p>The policy also covers AI features embedded in ordinary software: Google Docs Smart Compose and &ldquo;Help me
write,&rdquo; Gmail Smart Reply, Microsoft Word Copilot, Apple Intelligence and other phone or
operating-system writing assistants, Google and Bing AI search summaries, and PDF readers or
reference managers that summarize sources or answer questions about them. <strong>You do not have
to feel like you &ldquo;used AI&rdquo; for it to count.</strong></p>

<h2>Basic mechanics versus generative assistance</h2>

<p>Always fine, and never needs disclosure: spellcheck, punctuation correction, dictionary and
thesaurus lookup, grammar flags.</p>

<p>Covered by this policy: sentence rewriting, paraphrasing, summarizing, tone or style shifting,
drafting, generating analysis.</p>

<p><strong>The test, for tools that do both.</strong> Most tools now flag <em>and</em> offer to fix.
The distinction is what the tool hands you: if it only flags a possible problem, that is basic
mechanics. If it proposes new wording, a summary, or a rewritten version for you to adopt, this
policy covers it. A squiggly underline is a flag; a suggested replacement sentence is generative,
even inside a spellchecker or grammar tool. Grammarly is the common case: its spelling and
punctuation corrections are basic mechanics; its rewriting, paraphrasing, and &ldquo;sound more
professional&rdquo; features are not.</p>

<p><strong>What you can use freely, and where to go instead.</strong> Ordinary spelling, grammar,
and punctuation checking is always fine and never needs disclosure. <strong>Microsoft Word's
built-in spelling and grammar checker, LanguageTool, and equivalents are all permitted</strong>,
and so is the flagging half of Grammarly.</p>

<p>If what you actually want is help making your writing <em>sound better</em>, that is a completely
reasonable thing to want, particularly if you have been told your whole life that your writing is
too casual or not academic enough. The honest answer is that a rewrite button does not teach you to
do it yourself, and it is the part of your writing this course is trying to develop.
<strong>The CSUF Writing Center</strong> (Pollak Library North 199, in person and online, free,
appointments and drop-in) does the same job in a way that leaves the skill with you. I will also
read a draft paragraph and tell you what is making it land flat. Neither of those requires
disclosing anything, and neither costs you points.</p>

<p><strong>Features you did not turn on.</strong> Some software has AI switched on by default.
<strong>What counts is what you adopt.</strong> If your word processor suggests the rest of your
sentence and you accept it, that is use; if it suggests and you ignore it, nothing has happened.
You are responsible for what you accept, not for what a company enabled without asking you. Turning
these features off is worth doing; it removes the temptation and the ambiguity at once. I am happy
to show you how.</p>

<p><strong>On edge cases.</strong> AI is now embedded in enough ordinary software that neither of us
will anticipate every case. If you are unsure whether something counts, <strong>ask before you
submit</strong>. A good-faith question asked in advance is treated as exactly that.</p>

<h2>Where AI fits: assignment labels</h2>

<p>Every assignment in this course carries one of three labels, stated on the assignment itself.
You should never have to infer it.</p>

<ul>
<li><strong>GREEN</strong> &mdash; AI use permitted, within the course-wide limits below. No
disclosure needed. Green is not blanket permission: the &ldquo;not permitted&rdquo; list applies to
every assignment, on every label.</li>
<li><strong>YELLOW</strong> &mdash; Permitted within stated limits, plus the course-wide limits.
<strong>Disclosure required.</strong> The assignment says what is in bounds.</li>
<li><strong>RED</strong> &mdash; No AI. The assignment is designed to be completed without it, and
doing so is the point.</li>
</ul>

<p><strong>Red assignments in this course:</strong> the Week 2 baseline writing diagnostic, all
in-class writing, the midterm exam, and the final exam. Everything else is Green or Yellow:</p>

<table{TABLE_STYLE}>
<thead>
<tr><th{TH}>Assignment</th><th{TH}>Label</th><th{TH}>Who</th></tr>
</thead>
<tbody>
<tr><td{TD}>Reading journal (ten entries, participation)</td><td{TD}>GREEN</td><td{TD}>All</td></tr>
<tr><td{TD}>Week 2 baseline writing diagnostic</td><td{TD}>RED</td><td{TD}>All</td></tr>
<tr><td{TD}>All in-class writing and in-class activities</td><td{TD}>RED</td><td{TD}>All</td></tr>
<tr><td{TD}>Midterm exam</td><td{TD}>RED</td><td{TD}>All</td></tr>
<tr><td{TD}>Final exam</td><td{TD}>RED</td><td{TD}>All</td></tr>
<tr><td{TD}>Discussion papers (five; three are film weeks)</td><td{TD}>YELLOW</td><td{TD}>All</td></tr>
<tr><td{TD}>Policy brief: program selection</td><td{TD}>YELLOW</td><td{TD}>Undergraduate</td></tr>
<tr><td{TD}>Policy brief: source and claims memo</td><td{TD}>YELLOW</td><td{TD}>Undergraduate</td></tr>
<tr><td{TD}>Policy brief</td><td{TD}>YELLOW</td><td{TD}>Undergraduate</td></tr>
<tr><td{TD}>Term paper</td><td{TD}>YELLOW</td><td{TD}>Undergraduate</td></tr>
<tr><td{TD}>Research proposal</td><td{TD}>YELLOW</td><td{TD}>Graduate</td></tr>
<tr><td{TD}>Introduction, outline, annotated bibliography</td><td{TD}>YELLOW</td><td{TD}>Graduate</td></tr>
<tr><td{TD}>Final research paper</td><td{TD}>YELLOW</td><td{TD}>Graduate</td></tr>
</tbody>
</table>

<p>The label also appears on each assignment sheet. If the two ever disagree, tell me and use this
table until I fix it.</p>

<p><strong>If an assignment has no label</strong>, treat it as Yellow and ask me before using
anything beyond basic mechanics. An unlabeled assignment is my oversight, not an opening.</p>

<p>Red assignments are not punishments or trust tests. Some capacities only develop when you build
them yourself, and I need to see your unaided thinking at least once to be useful to you for the
rest of the term.</p>

<h2>Course-supported AI environment: PapyrusAI</h2>

<p>This course uses <strong>PapyrusAI</strong>
(<a href="https://www.genaied.org/papyrusai.html">genaied.org/papyrusai</a>) as the supported AI
environment for graded writing. PapyrusAI is an instructor-configured, contained LLM environment:
I build the modules, set the source materials the AI may draw on, and define how it interacts with
you. No module here will produce paragraphs you can paste into an assignment, which is the
course rule rather than something PapyrusAI costs you.</p>

<p>Most modules here are <em>coaching</em> modules attached to one assignment. They ask questions,
push back on weak claims, and point you to readings rather than answering for you. <strong>Four were
built for specific assignments in this course</strong>, and those assignments are marked
<em>(PapyrusAI module)</em> in the weighting tables in the syllabus:</p>

<ul style="line-height:1.7;">
<li><strong>Idea Catcher</strong> &mdash; the reading journal. Takes an entry in under three minutes,
never grades it, and does the counting for you.</li>
<li><strong>Policy Brief Scaffold</strong> &mdash; the Source and Claims Memo and the Policy Brief.
Per-program modules that ask what a program does, whom it reaches, and where each claim came
from.</li>
<li><strong>Term Paper Dialectical Partner</strong> &mdash; the term paper. Built to take the opposing
position on your reform proposal and make you defend it.</li>
<li><strong>Research Paper Coach</strong> &mdash; the graduate track, opening once your proposal is in.
Argues against your thesis rather than helping you state it.</li>
</ul>

<p><strong>There is also a <em>General Use</em> module</strong>, which is not attached to any
assignment and does not coach. It answers what you ask, the way you would expect ChatGPT or Claude
to. Use it for the discussion papers, the graduate milestones, anything
else in the course, or a question that is not an assignment at all. It runs under the same
permitted/not-permitted list as every other tool, so it is no more and no less restricted than the
ChatGPT Edu account the CSU gave you.</p>

<p><strong>It can search the web</strong>, so when it gives you a number about a program it is
built to name the document that number came from and link it, and to say plainly when it could not
find something rather than produce a plausible substitute. Click the links. <strong>It will not
summarize a reading you have not read</strong>, or go find a summary of one, and the same goes for
the assigned documentaries &mdash; the one place it is stricter than a general tool. If you have
read something and want to talk about it, it will talk for as long as you like.</p>

<p><strong>A module session can stand in for your disclosure sentence.</strong> Sessions are
logged and you can read the log yourself; attaching one to a Yellow assignment satisfies the
disclosure requirement, and the mechanics are under <em>Disclosure requirement</em> below. If you
would rather write the sentence, write the sentence. Both are complete.</p>

<p>You may also use general-purpose AI tools outside PapyrusAI. Everything below applies the same
way to all of them. <strong>Getting into PapyrusAI &mdash; the course code and the menu &mdash; is
on the course home page.</strong></p>

<p><strong>You can complete this entire course without PapyrusAI</strong>, and taking that path
costs you nothing in points or standing. Every graded assignment is written to be done without it.
Where an assignment asks you to show that you talked your work through with someone, a module
session, a CSUF Writing Center appointment, and a conversation with me all count equally, and none
of the three is the default. You do not owe me a reason for your choice, and you can change it at
any point in the semester. <strong>If you switch in the middle of a multi-stage assignment, whatever
you have already produced still counts and you do not redo any of it</strong>. Tell me you have
switched and keep going.</p>

<p><strong>About the research study.</strong> PapyrusAI is being studied at CSUF under IRB protocol
HSR-24-25-240, <em>Enhancing Academic Writing and Digital Literacy with an AI Coach</em>. You will
hear about it in Week 2 and decide then whether to take part. Participation is voluntary, you may
withdraw at any time, and declining puts you on the non-PapyrusAI path described above, which is a
complete path, not a reduced one. Nothing about that decision affects your grade, and I will not
treat it as a statement about your work.</p>

<h2>Permitted uses</h2>

<ul>
<li>Brainstorming, and working out an outline with it before you have written the piece</li>
<li>Explaining concepts you don't understand (then explaining it back in your own words). Concept
explanation is permitted; uploading an assigned reading for the tool to summarize or explain is not,
unless I explicitly allow it.</li>
<li>Literature searching and locating sources, which you then read yourself</li>
<li>Diagnosing problems in your clarity, grammar, or organization</li>
<li>Sanity-checking your analysis or logic</li>
<li>Generating synthetic examples or test cases for your ideas</li>
</ul>

<p><strong>Where editing ends and rewriting begins.</strong> &ldquo;This paragraph buries its
main claim&rdquo; is fine; act on it
yourself. &ldquo;Here is a clearer version of your paragraph&rdquo; is not, even if you edit it
afterward. Asking <em>what is wrong</em> is permitted; asking it to <em>write the fix</em> is not.</p>

<p><strong>On outlines.</strong> Thinking through an
outline with a tool <em>before</em> you draft is permitted. That is planning, and the plan is still
yours to argue for. Handing it a draft you have written and asking it to reorganize the piece is not,
because at that point the structure is a finding about your argument and finding it is the work.
Plan with it; do not let it rearrange you.</p>

<h2>Not permitted</h2>

<ul>
<li>Using AI to generate your analysis, arguments, or conclusions</li>
<li>Submitting AI-generated text as your own writing</li>
<li>Using AI to avoid engaging with course concepts or readings</li>
<li>Letting AI do the intellectual heavy lifting (interpreting sources, building arguments,
synthesizing ideas)</li>
</ul>

<h2>Baseline writing diagnostic</h2>

<p>During Week 2, you will complete a short in-class writing exercise (unaided, handwritten or in a
locked-down Canvas window) responding to a course prompt. This is not graded for content and counts
toward participation. Its purpose is to establish a baseline sample of your own writing voice early
in the semester, before AI-supported assignments begin.</p>

<h2>Disclosure requirement</h2>

<p>On Yellow work, include a brief note at the end of the assignment: what tool, and what you used it
for (e.g., &ldquo;I used Claude to check whether my argument in Section 3 held together, and to find
two CBO reports that I then read. All prose and all structure are mine.&rdquo;). One or two sentences
is the whole requirement. <strong>You do not need to attach prompts, transcripts, or logs unless an
assignment specifically asks for them</strong>. And if one does, it will say so. For work completed
inside a PapyrusAI module, you can download the conversation from its three-dot menu and attach that
file instead of writing the sentence. <strong>The download is a manual step. Nothing attaches on its
own, and the vendor does not promise to retain your conversations indefinitely, so save what you will
need at the end of a session rather than at the deadline.</strong></p>

<p><strong>Disclosure is a description of your process</strong>, the same way a methods section
describes how a study was run. It is not a confession. Disclosing use has never lowered a grade in my
courses and it is not going to start. What creates a problem is undisclosed use that shows up in the
work. And it does show up.</p>

<h2>Why this policy exists</h2>

<p><strong>AI makes breadth cheap.</strong> When summarizing a fifth reading costs nothing, you
summarize the fifth reading instead of sitting with the second one until you understand what it is
actually claiming. The tool quietly relocates your effort from understanding to coverage. Coverage is
not what this course, or your career, rewards. Laziness has nothing to do with it.</p>

<p><strong>These systems are agreeable.</strong> They will validate a weak thesis enthusiastically,
produce fluent prose about things they have no basis for asserting, and fabricate citations that look
exactly like real ones. Fluency is not accuracy. In a field where you will be asked to defend claims
about what programs do and whom they affect, a confident and compliant reader is worse than no reader
at all, unless you are already doing the judging.</p>

<p><strong>In this course specifically.</strong> This policy supports Outcomes 3, 4, and 6 because
you must practice those judgments without outsourcing them. You are asked to apply policy-analytic
concepts to evaluate welfare programs (Outcome 3), to analyze how race and gender structured both
program design and access to benefits (Outcome 4), and to construct evidence-based arguments from
primary sources (Outcome 6). Every one of those is a judgment you have to make yourself.</p>

<p>There is a sharper problem here than in most courses. A model trained on the existing public
conversation about welfare will reproduce the dominant American framing of it&mdash;deservingness
distinctions, work-ethic moralism, the residue of the &ldquo;welfare queen&rdquo;
narrative&mdash;because that framing saturates the text it learned from. That is precisely the set of
assumptions this course exists to interrogate. Use such a tool uncritically and you hand your analysis
over to the thing you are supposed to be analyzing. The weaker paper is the smaller cost. We will look
at this directly in an early-semester exercise, because it is a course concept as much as a technology
caution.</p>

<h2>Guidance: using these tools well</h2>

<ul>
<li><strong>Authorship.</strong> All submitted prose is written by you.</li>
<li><strong>Verification.</strong> Check every fact, quotation, and citation before it enters your
work. Fabricated sources are the failure mode most likely to hurt you, and they are convincing.</li>
<li><strong>Bias.</strong> These systems reproduce the assumptions in their training data. Read
outputs critically for whose perspective is centered and whose is missing. That is a skill this course
is teaching you anyway.</li>
<li><strong>Privacy and security.</strong> Do not paste anything sensitive, private, or confidential
into a chatbot: student records, personnel matters, unpublished data, or others' personal information.
Assume anything you enter may be retained <em>by the company</em>, indefinitely and beyond your
reach, and assume separately that you may not be able to open it again yourself. Plan for both: it
may outlive you wanting it, and it may vanish before you need it.</li>
<li><strong>Do not feed it the course.</strong> Unless I explicitly say otherwise, do not paste full
assigned readings, a classmate's work, or confidential course materials into a public AI system. Much
of what we read is licensed to the university, not to you to redistribute. And metabolizing a reading
is the work itself; hand that to a tool and the work has not happened.</li>
<li><strong>Sustainability.</strong> These systems carry real energy and water costs. Thoughtful use
is part of responsible use.</li>
<li><strong>Opting out is legitimate.</strong> If you would rather not use AI at
all&mdash;for labor, environmental, privacy, or any other principled reason&mdash;that is a respected
choice here. The PapyrusAI modules are genuinely optional, and no part of your grade depends on using
them. If a required activity is a problem for you, come talk to me and we will find an
alternative.</li>
</ul>

<p>Further reading:
<a href="https://genai.calstate.edu/communities/students/ethical-and-responsible-use-ai">CSU AI
Commons&mdash;Ethical and Responsible Use of AI for Students</a>.</p>

<h2>When the policy is broken</h2>

<p><strong>Misuse includes</strong> submitting AI-generated or AI-rewritten prose as your own; using
AI on a Red assignment; failing to disclose on Yellow work; and submitting fabricated citations or
facts you did not verify.</p>

<p><strong>Consequences</strong>, proportionate to what happened: a conversation and a revision
requirement; a grade penalty; or, for serious or repeated violations, a formal referral under CSUF's
Academic Dishonesty Policy (UPS 300.021), which can carry sanctions up to dismissal.</p>

<p><strong>How I judge severity.</strong> These are not all the same thing and I will not treat them
as if they were. I weigh the nature of the assignment; whether the use replaced core intellectual work
or sat at the margins of it; <strong>whether the problem was non-disclosure or substantive
substitution</strong>; and whether it is a first occurrence or a repeated one. Forgetting a disclosure
sentence on otherwise honest work is an omission. Passing off generated analysis as your own is
deception. They land in very different places.</p>

<p><strong>On detection.</strong> I am not going to pretend I can catch everything with software, and
<strong>I will not run your writing through an AI detector and treat the output as evidence</strong>.
Those tools are unreliable, and their errors are not evenly distributed. They flag multilingual writers
and plain prose at higher rates. Making accusations on that basis would be both unfair and bad
reasoning, and I teach you not to reason that way. What I will do is read carefully, ask you to explain
your process, and make judgments based on the work, the assignment rules, and that conversation.
<em>Walk me through how you got here.</em> If you did the thinking, that is an easy conversation and
often a good one. If you did not, it is not. That is the actual standard, and it does not depend on
which tool produced the prose.</p>

<h2>How AI use is assessed</h2>

<p>AI use is evaluated by boundaries and learning, not polish: whether assignment-level rules were
followed (Red assignments stayed Red); the quality of disclosure where required; whether the final work
shows original analysis and a consistent authorial voice; and whether you can explain and defend your
argument, evidence, and revisions without external support. If you cannot defend the work, it does not
count as yours, regardless of how it was produced.</p>

<h2>Revisiting this policy</h2>

<p>This policy is a working document, not a settled one. AI is embedded in enough ordinary software
that good-faith students will hit cases neither of us anticipated. <strong>We will take a few minutes
at several points in the term to revisit this policy and work through edge cases that have actually
come up.</strong> Bring them. A case you are unsure about is more useful to the class than a rule I
wrote in August.</p>

<p>And a standing invitation, which I mean: this is a course about how rules get made, whom they
burden, and whether they accomplish what they claim. That includes this rule. If you think this policy
is poorly designed, imposes burden it does not justify, or fails on its own terms, say so, in class or
to me directly. I would rather hear it in week three than read it in evaluations.</p>
"""

NAVY, ACCENT, INK = "#00244E", "#C25100", "#1F2933"
MUTED, LINE, WASH = "#52606D", "#D8DEE6", "#F4F7FA"

CARD = (f"flex:1 1 240px;border:1px solid {LINE};border-left:5px solid {NAVY};"
        "border-radius:6px;padding:16px 18px;background:#fff;min-width:240px;")
PILL = (f"display:inline-block;background:{WASH};border:1px solid {LINE};border-radius:999px;"
        f"padding:3px 12px;margin:0 6px 6px 0;font-size:0.85em;color:{INK};")

HOME_BODY = f"""
<div style="background:{NAVY};color:#fff;padding:26px 28px;border-radius:8px;">
  <div style="font-size:0.8em;letter-spacing:0.14em;text-transform:uppercase;opacity:0.85;">
    Fall 2026 &middot; Section 01 &middot; Schedule Code 17538</div>
  <div style="font-size:1.85em;font-weight:700;line-height:1.2;margin:6px 0 4px;">
    POSC 459: Social Welfare Politics and Policy</div>
  <div style="font-size:1.02em;opacity:0.95;">
    Monday &amp; Wednesday, 1:00&ndash;2:15 p.m. &middot; GH 305 &middot; 3 units<br>
    First class Monday, August 24 &middot; Dr. David P. Adams</div>
</div>

<p style="font-size:1.06em;line-height:1.6;margin:22px 0;">This course is an intensive introduction
to U.S. social welfare policy and politics. Political science helps explain <em>why</em> we get the
policies we get; policy analysis helps evaluate <em>whether those policies do what they claim</em>.
Both lenses are at work all semester.</p>

<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:6px;">Start here</h2>

<div style="display:flex;flex-wrap:wrap;gap:16px;margin:18px 0 26px;">
  <div style="{CARD}">
    <div style="font-weight:700;font-size:1.05em;margin-bottom:6px;">
      <a href="/courses/{COURSE_ID}/pages/course-syllabus" style="color:{NAVY};">Course Syllabus</a></div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">The governing document. Texts, the
    full week-by-week schedule, grading, and every policy. Download the PDF and keep it.</div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;font-size:1.05em;margin-bottom:6px;">
      <a href="/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology"
      style="color:{NAVY};">AI Policy</a></div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">AI is permitted here, with rules.
    Every assignment is labeled GREEN, YELLOW, or RED. <strong>Read this before the first
    assignment.</strong></div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;font-size:1.05em;margin-bottom:6px;">
      <a href="/courses/{COURSE_ID}/pages/policy-brief-scaffold-how-to-use-it"
      style="color:{NAVY};">PapyrusAI Guide</a></div>
    <div style="color:{MUTED};font-size:0.93em;line-height:1.5;">How the optional writing-coach
    module works, and how to opt out. Ungraded and never required.</div>
  </div>
</div>

<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:6px;">Getting into PapyrusAI</h2>

<p><strong>PapyrusAI is in the left-hand navigation menu of this course.</strong> The first
time you open it, you will set up a PapyrusAI account and enter our course code,
<strong>FALL2026-POSC459</strong>. Enter the code exactly as written &mdash; a mistyped code does
not give you an error, it puts you somewhere that is not this class, and you will not see our
modules. After that one-time setup the menu link takes you straight in, with no separate login. The
<a href="https://docs.google.com/document/d/1hVXs5RwWi8Pau1YlhwoF5Y5zO3-1hMZAyUxych7iIDo"
target="_blank" rel="noopener">PapyrusAI Student Guide</a> walks through the setup step by step. If
PapyrusAI does not appear in the menu, or the code does not work, tell me before you spend time
working around it.</p>

<p>The modules are optional and ungraded, and they exist to make productive AI use easy to reach and
unproductive use harder to fall into. What each one does, and how to do the course without them, is
on the <a href="/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology">AI
policy page</a>.</p>

<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:6px;">The first two weeks</h2>

<table{TABLE_STYLE}>
<thead><tr><th{TH}>When</th><th{TH}>What</th></tr></thead>
<tbody>
<tr><td{TD}><strong>Mon, Aug 24</strong></td><td{TD}>First class. Rank et al., <em>Poorly
Understood</em>, Section 1, pp. 15&ndash;49 &mdash; a Pollak Library ebook, so you do not need to have
bought a book yet. <em>Growing Up Poor in America</em>, Part 1 assigned for viewing on your own.</td></tr>
<tr><td{TD}><strong>Mon, Aug 31</strong></td><td{TD}><strong>Baseline writing diagnostic</strong>, in
class, about 20 minutes, no AI. Not graded for content &mdash; it establishes what your own writing
sounds like before anything AI-supported begins.</td></tr>
<tr><td{TD}><strong>Wed, Sep 2</strong></td><td{TD}>Research pre-survey, PapyrusAI sign-up, and a
class discussion treating this course's AI policy as something to critique.</td></tr>
</tbody>
</table>

<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:6px;">Dates worth putting in your calendar now</h2>

<table{TABLE_STYLE}>
<thead><tr><th{TH}>Date</th><th{TH}>What</th><th{TH}>Who</th></tr></thead>
<tbody>
<tr><td{TD}>Fri, Sep 18</td><td{TD}>Discussion Paper 1, 11:59 p.m. (the first of five; the others are Fridays Oct 2, Oct 23, Nov 6, Nov 20)</td><td{TD}>All</td></tr>
<tr><td{TD}>Mon, Sep 21</td><td{TD}>Policy brief program selection</td><td{TD}>Undergraduates</td></tr>
<tr><td{TD}>Mon, Oct 5</td><td{TD}>Research proposal</td><td{TD}>Graduate students</td></tr>
<tr><td{TD}>Fri, Oct 9</td><td{TD}>Source and claims memo (5%)</td><td{TD}>Undergraduates</td></tr>
<tr><td{TD}><strong>Wed, Oct 14</strong></td><td{TD}><strong>Midterm exam</strong>, in class</td><td{TD}>All</td></tr>
<tr><td{TD}>Wed, Oct 28</td><td{TD}>Policy brief (15%)</td><td{TD}>Undergraduates</td></tr>
<tr><td{TD}>Wed, Dec 2</td><td{TD}>Term paper &middot; graduate outline</td><td{TD}>All</td></tr>
<tr><td{TD}>Wed, Dec 9</td><td{TD}>Last day of instruction &middot; reading journal checkpoint 2</td><td{TD}>All</td></tr>
<tr><td{TD}><strong>Mon, Dec 14</strong></td><td{TD}><strong>Final exam, 1:00&ndash;2:50 p.m., GH 305.</strong>
Graduate final research papers are due at the start of it.</td><td{TD}>All</td></tr>
</tbody>
</table>

<p style="margin-top:14px;"><span style="{PILL}">No class Mon, Sep 7 &mdash; Labor Day</span>
<span style="{PILL}">No class Wed, Nov 11 &mdash; Veterans Day</span>
<span style="{PILL}">No class Nov 23&ndash;27 &mdash; Thanksgiving</span></p>

<p><strong>Three weeks have no in-person meetings</strong> and run asynchronously: Week 4
(Sep 14&ndash;16), Week 9 (Oct 19&ndash;21), and Week 14 (Nov 30&ndash;Dec 2). Weeks 4 and 9 pair a
documentary with that week's discussion paper. Week 14 is reading and independent work with nothing new to
submit.</p>

<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:6px;">How the grade works</h2>

<div style="display:flex;flex-wrap:wrap;gap:16px;margin:18px 0;">
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">Everyone</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Attendance and participation &mdash; <strong>10%</strong><br>
      Discussion papers, five across the term &mdash; <strong>10%</strong><br>
      Midterm exam &mdash; <strong>20%</strong><br>
      Final exam &mdash; <strong>20%</strong></div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">Undergraduates &mdash; the other 40%</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Program selection &mdash; <strong>credit/no credit</strong><br>
      Source and claims memo &mdash; <strong>5%</strong><br>
      Policy brief &mdash; <strong>15%</strong><br>
      Term paper &mdash; <strong>20%</strong></div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">Graduate students &mdash; the other 40%</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Research proposal &mdash; <strong>10%</strong><br>
      Introduction, outline, bibliography &mdash; <strong>10%</strong><br>
      Final research paper &mdash; <strong>20%</strong></div>
  </div>
</div>

<p style="background:{WASH};border-left:5px solid {ACCENT};padding:12px 16px;">
<strong>The reading journal.</strong> Ten short entries across the term, credited for existing rather
than graded on content, counting toward participation. I check twice: five entries by October 14, five
more by December 9. Keep it wherever you like &mdash; the PapyrusAI Idea Catcher, a document, or a
paper notebook all count the same.</p>

<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:6px;">Reaching me</h2>

<div style="display:flex;flex-wrap:wrap;gap:16px;margin:18px 0;">
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">David P. Adams, Ph.D.</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Gordon Hall 516<br>
      <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a><br>
      Phone or text: (657) 278-4770<br>
      <a href="https://dadams.io/appointments">Book a meeting</a> &middot;
      <a href="https://dadams.io">dadams.io</a></div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">Office hours</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.8;">
      Mondays 3:00&ndash;4:00 and 5:30&ndash;6:30<br>
      Tuesdays 12:00&ndash;1:00<br>
      Or by <a href="https://dadams.io/appointments">appointment</a> any day</div>
  </div>
  <div style="{CARD}">
    <div style="font-weight:700;margin-bottom:8px;color:{NAVY};">What to expect</div>
    <div style="color:{INK};font-size:0.95em;line-height:1.6;">
      I answer email and Canvas messages <strong>within 24 hours</strong>, except weekends and
      holidays. No reply after 24 hours? Send a follow-up. Still nothing after 48? Call or text me
      &mdash; something went wrong.</div>
  </div>
</div>

<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:6px;">When technology breaks</h2>

<p><strong>Tell me first</strong>, so the problem is documented, then contact the
<a href="http://www.fullerton.edu/it/students/helpdesk/index.php">student IT help desk</a>
(<a href="mailto:StudentITHelpDesk@fullerton.edu">email</a>, (657) 278-8888) or walk in to the
<a href="http://www.fullerton.edu/it/students/sgc/index.php">Student Genius Center</a>.</p>

<p><strong>Canvas specifically:</strong> (657) 278-8888, the
<a href="https://canvashelp.fullerton.edu/">CSUF Canvas Guides</a>, or
<a href="https://titans.service-now.com/sp?id=sc_cat_item&amp;sys_id=f88efe80ebea6a10fb7cfcffcad0cdc6&amp;subject=Canvas">report
a problem</a>.</p>

<p style="background:{WASH};border-left:5px solid {NAVY};padding:12px 16px;">
<strong>If Canvas will not take your submission, email it to me before the deadline.</strong> A broken
upload is not a late assignment. The same goes for PapyrusAI: a module that will not load is never the
reason something is late. Email me what happened, submit what you have, and we will sort it out. I
would rather get that email at 11 p.m. than read an apology in week fourteen.</p>
"""

SYLLABUS_BODY = f"""
<p><em>The PDF syllabus is the governing document for this course. This page carries the essentials;
anything that disagrees with the PDF is an error on this page, and I would like to know about it.</em></p>

{SYLLABUS_PDF_MARKER}

<h2>Catalog description</h2>

<p>American social policies&mdash;welfare, Social Security, health care&mdash;and the political
environment in which they exist. Origins, implementation, and reforms of current social policies,
emphasizing questions of effectiveness and policy improvement.</p>

<p><strong>Course requisite(s):</strong> POSC 100 or graduate standing</p>

<h2>Student learning outcomes</h2>

<p>By the end of the semester, students will be able to:</p>

<ol>
<li>Describe the core architecture of the U.S. welfare state: social insurance, public assistance, tax
expenditures, and public-private arrangements.</li>
<li>Trace the political development of major programs (Social Security, TANF, Medicaid, ACA) and
connect that history to current policy debates.</li>
<li>Apply key concepts from political science and policy analysis to evaluate welfare programs: policy
feedback, institutional design, interest group politics, and public opinion.</li>
<li>Analyze how race and gender have structured both program design and access to benefits.</li>
<li>Situate U.S. welfare policy within a comparative frame and explain the sources of American
exceptionalism.</li>
<li>Construct an evidence-based policy argument using primary sources and scholarly literature.</li>
</ol>

<h2>Required texts</h2>

<p>Howard (2007); Campbell (2014); Desmond (2023); plus ebook readings through Pollak Library. See the
syllabus PDF for full citations and which titles are available as Pollak Library ebooks.</p>

<h2>Reading structure</h2>

<p>Core Readings are required. Recommended Readings are optional but encouraged. Grad Extension
Readings are required for graduate students.</p>

<h2>Academic integrity</h2>

<p>The question this course asks about your work is <strong>whether you did the thinking</strong>.
Most syllabi ask a different one &mdash; whether you wrote these particular words, authorship as a
solitary act &mdash; and that standard cannot do much work in a course that asks you to use tools
which produce text. Susan Blum made the case that authorship-as-solitude was never quite right in
<em>My Word! Plagiarism and College Culture</em> (2009), well before any of this existed.</p>

<p>In practice, represent your process accurately. Cite what you drew on. Working through a reading
with classmates is good and expected; turning in work you produced together as individual work is
not. Work you wrote for another course needs my agreement before it counts again here. And if you
are unsure whether something is in bounds, ask before you submit &mdash; asking has never counted
against anyone.</p>

<p>Where AI is involved, the
<a href="/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology">AI
policy page</a> is the operative document, including what counts as misuse and what follows from it.
It also explains why I will not run your writing through an AI detector.</p>

<p>CSUF's <a href="https://www.fullerton.edu/senate/publications_policies_resolutions/ups/UPS%20300/UPS%20300.021.pdf">Academic
Dishonesty Policy</a> (UPS 300.021) governs this course and carries the formal sanctions. What is
written above is how I read it.</p>

<h2>Generative AI</h2>

<p>See <a href="/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology">Policy
on the Use of Generative AI and Other Technology</a> for the full policy.</p>
"""

SCAFFOLD_GUIDE_LEAD = f"""
<p style="border-left:5px solid #8d6e00;background:#fff8e1;padding:10px 14px;">
<strong>Reference, not an assignment. Nothing here is graded and nothing here is required.</strong><br>
<span style="font-size:0.9em;">This guide explains the optional PapyrusAI Policy Brief Scaffold
module. The full AI policy is on the page
<a href="/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology">Policy
on the Use of Generative AI and Other Technology</a>.</span></p>
"""

PAGES = [
    ("Course Home", HOME_BODY, True),
    ("Course Syllabus", SYLLABUS_BODY, False),
    ("Policy on the Use of Generative AI and Other Technology", AI_POLICY_BODY, False),
    ("Policy Brief Scaffold — How to Use It", None, False),  # body built from the vault note
]

# Week labels transcribed verbatim from the .tex schedule; Part dividers match
# the PART I-IV rules in the syllabus.
MODULES = [
    "Start Here",
    "PART I: The Big Picture",
    "Week 1 (8/24) — Introduction: What Is the American Welfare State?",
    "Week 2 (8/31) — Why Are So Many Americans Poor?",
    "Week 3 (9/7) — American Exceptionalism?",
    "Week 4 (9/14) — ASYNC: Political Development of the Welfare State",
    "PART II: Programs of the Welfare State",
    "Week 5 (9/21) — Social Security and Medicare",
    "Week 6 (9/28) — The Safety Net, Part 1: TANF, SNAP, and the EITC",
    "Week 7 (10/5) — The Safety Net, Part 2: Housing, Income, and Medicaid",
    "Week 8 (10/12) — Midterm Review and Midterm Exam",
    "PART III: Case Studies in Reform",
    "Week 9 (10/19) — ASYNC: Welfare Reform",
    "Week 10 (10/26) — Health Care Reform and the ACA",
    "Week 11 (11/2) — Documentary Screening and Synthesis Discussion",
    "PART IV: Political Forces Shaping the Welfare State",
    "Week 12 (11/9) — Race and the Welfare State, Part 1",
    "Week 13 (11/16) — Race Part 2 and Gender and the Welfare State",
    "Week 14 (11/30) — ASYNC: Public Opinion and Interest Groups",
    "Week 15 (12/7) — Solutions and Course Synthesis",
    "Week 16 (12/14) — Finals Week",
]


def main():
    require_env()
    course = api("GET", f"/api/v1/courses/{COURSE_ID}")
    print(f"Course: {course['name']} ({course['workflow_state']})\n")

    syllabus_file = ensure_syllabus_pdf()
    link_html = syllabus_link_html(syllabus_file)
    print()

    existing_pages = {p["title"]: p for p in list_all(f"/api/v1/courses/{COURSE_ID}/pages")}
    page_urls = {}
    for title, body, is_front in PAGES:
        if body is None:
            body = SCAFFOLD_GUIDE_LEAD + "\n" + vault_md_to_html(
                "Assignments/07a - Policy Brief Scaffold - Student Guide.md")
        body = body.replace(SYLLABUS_PDF_MARKER, link_html)
        # Keep whatever publish state the page already has. Sending published=False
        # on an update pulls a live page from students every time this runs. New
        # pages still start unpublished per AGENTS.md, except the front page, which
        # Canvas requires to be published to be designated as such.
        prior = existing_pages.get(title)
        published = bool(prior["published"]) if prior else is_front
        wiki = {"title": title, "body": body.strip(),
                "published": True if is_front else published}
        if is_front:
            wiki["front_page"] = True
        payload = {"wiki_page": wiki}
        if title in existing_pages:
            res = api("PUT", f"/api/v1/courses/{COURSE_ID}/pages/{existing_pages[title]['url']}", payload)
            print(f"  page updated : {title}")
        else:
            res = api("POST", f"/api/v1/courses/{COURSE_ID}/pages", payload)
            print(f"  page created : {title}")
        page_urls[title] = res["url"]

    print()
    existing_mods = {m["name"]: m for m in list_all(f"/api/v1/courses/{COURSE_ID}/modules")}
    mod_ids = {}
    for i, name in enumerate(MODULES, start=1):
        if name in existing_mods:
            mod_ids[name] = existing_mods[name]["id"]
            print(f"  module exists : {name}")
            continue
        res = api("POST", f"/api/v1/courses/{COURSE_ID}/modules",
                  {"module": {"name": name, "position": i, "published": False}})
        mod_ids[name] = res["id"]
        print(f"  module created: {name}")

    print()
    start_id = mod_ids["Start Here"]
    have = {it.get("title") for it in list_all(f"/api/v1/courses/{COURSE_ID}/modules/{start_id}/items")}
    for pos, title in enumerate(["Course Syllabus",
                                 "Policy on the Use of Generative AI and Other Technology",
                                 "Policy Brief Scaffold — How to Use It"], start=1):
        if title in have:
            print(f"  item exists   : {title}")
            continue
        api("POST", f"/api/v1/courses/{COURSE_ID}/modules/{start_id}/items",
            {"module_item": {"type": "Page", "page_url": page_urls[title],
                             "title": title, "position": pos}})
        print(f"  item added    : {title} -> Start Here")

    print(f"\nDone. {len(PAGES)} pages, {len(MODULES)} modules. "
          "New content unpublished; existing publish states preserved.")


if __name__ == "__main__":
    sys.exit(main())
