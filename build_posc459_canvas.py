#!/usr/bin/env python3
"""Build the POSC 459 (Fall 2026) Canvas shell.

Source of truth: POSC 459 Welfare Politics/posc459-syllabus-fa26-papyrus.tex
Follows AGENTS.md: everything created unpublished, week labels verbatim,
policy wording copied rather than summarized.

Idempotent by title/name: re-running updates existing pages and skips
modules that already exist.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

COURSE_ID = "3592717"
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")


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
as AI use under this policy. Everything below is detail.</p>

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

<p><strong>AI built into tools you already use.</strong> This is the part people miss. The policy
also covers AI features embedded in ordinary software: Google Docs Smart Compose and &ldquo;Help me
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
and so is the flagging half of Grammarly. The line is the same one as above: a tool that tells you
something may be wrong is fine; a tool that writes the replacement is not.</p>

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
submit</strong>. A good-faith question asked in advance is treated as exactly that. It is not a
confession and it does not put you under suspicion.</p>

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
in-class writing, the midterm exam, and the final exam. Everything else is Green or Yellow, and here
is the whole list, so you are not waiting for a Canvas page to open to find out.</p>

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
<tr><td{TD}>Discussion papers (5 of 10)</td><td{TD}>YELLOW</td><td{TD}>All</td></tr>
<tr><td{TD}>Documentary responses (async weeks)</td><td{TD}>YELLOW</td><td{TD}>All</td></tr>
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
you. Modules in this course are designed to <em>coach</em>, not to write for you. They will ask
questions, push back on weak claims, and point you to readings, but they will not produce paragraphs
you can paste into an assignment.</p>

<p>Specific PapyrusAI modules accompany the reading journal, the policy brief, the term paper, and
the graduate research milestones. <strong>Access PapyrusAI from the left-hand navigation menu inside
our Canvas course site.</strong> There is no separate login and no password to remember. The first
time you open it you will be asked for a course code; ours is <strong>FALL2026-POSC459</strong>.
Enter it exactly as written. A mistyped code does not give you an error; it puts you somewhere that
is not this class, and you will not see our modules. If PapyrusAI does not appear in the navigation
menu, or the code does not work, tell me before you spend time working around it. Use of these
modules is encouraged but not required; they exist to make productive AI use easy to access and
unproductive use harder to fall into.</p>

<p>You may also use general-purpose AI tools (ChatGPT, Claude, Gemini, etc.) outside PapyrusAI
subject to the rules below. The permitted/not-permitted list applies equally regardless of which
tool you use.</p>

<p><strong>You can complete this entire course without PapyrusAI.</strong> Every graded assignment
is written to be done on a non-PapyrusAI path, and taking that path costs you nothing in points or
standing. Where an assignment asks you to show that you talked your work through with someone, a
module session, a CSUF Writing Center appointment, and a conversation with me all count equally.
<strong>Neither path is the default and neither is worth more.</strong> You do not owe me a reason
for your choice, and you can change it at any point in the semester. <strong>If you switch in the
middle of a multi-stage assignment, whatever you have already produced still counts and you do not
redo any of it</strong>. Tell me you have switched and keep going.</p>

<p><strong>And if the tool is broken, that is not your problem to solve at midnight.</strong>
PapyrusAI is new, and some of you will hit a wrong code, a missing menu item, or a module that will
not load. <strong>The module is never the reason an assignment is late.</strong> Email me with what
happened, submit what you have, and we will sort it out. I would rather get that email at 11 p.m.
than read an apology in week fourteen.</p>

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

<p><strong>Where editing ends and rewriting begins.</strong> This is the boundary students ask about
most, so here it is plainly: <strong>AI may identify problems in your writing. It may not supply the
prose that fixes them.</strong> &ldquo;This paragraph buries its main claim&rdquo; is fine; act on it
yourself. &ldquo;Here is a clearer version of your paragraph&rdquo; is not, even if you edit it
afterward. Asking <em>what is wrong</em> is permitted; asking it to <em>write the fix</em> is not.</p>

<p><strong>On outlines, since this is where the line looks blurry.</strong> Thinking through an
outline with a tool <em>before</em> you draft is permitted. That is planning, and the plan is still
yours to argue for. Handing it a draft you have written and asking it to reorganize the piece is not,
because at that point the structure is a finding about your argument and finding it is the work. The
short version: plan with it, do not let it rearrange you.</p>

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

<p>You deserve reasons, not just rules.</p>

<p><strong>AI makes breadth cheap.</strong> When summarizing a fifth reading costs nothing, you
summarize the fifth reading instead of sitting with the second one until you understand what it is
actually claiming. The tool quietly relocates your effort from understanding to coverage. Coverage is
not what this course, or your career, rewards. The claim here is about where the path of least
resistance leads when a genuinely useful tool is available. Laziness has nothing to do with it.</p>

<p><strong>These systems are agreeable.</strong> They will validate a weak thesis enthusiastically,
produce fluent prose about things they have no basis for asserting, and fabricate citations that look
exactly like real ones. Fluency is not accuracy. In a field where you will be asked to defend claims
about what programs do and whom they affect, a confident and compliant reader is worse than no reader
at all, unless you are already doing the judging.</p>

<p><strong>And in this course specifically.</strong> This policy supports Outcomes 3, 4, and 6 because
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
<li><strong>Authorship.</strong> All submitted prose is written by you. AI may critique; it may not
generate or rewrite your sentences, paragraphs, or structure.</li>
<li><strong>Verification.</strong> Check every fact, quotation, and citation before it enters your
work. Fabricated sources are the failure mode most likely to hurt you, and they are convincing.</li>
<li><strong>Bias.</strong> These systems reproduce the assumptions in their training data. Read
outputs critically for whose perspective is centered and whose is missing. That is a skill this course
is teaching you anyway.</li>
<li><strong>Privacy and security.</strong> Do not paste anything sensitive, private, or confidential
into a chatbot: student records, personnel matters, unpublished data, or others' personal information.
Assume anything you enter may be retained <em>by the company</em>, indefinitely and beyond your reach.
That is a separate question from whether <em>you</em> will still be able to open a past conversation
in the product, which no vendor guarantees. That is why the advice above is to download anything you
need at the end of a session. Plan for both: it may outlive you wanting it, and it may vanish before
you need it.</li>
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

HOME_BODY = f"""
<p>Welcome to <strong>POSC 459, Social Welfare Politics and Policy</strong>. This course is an
intensive introduction to U.S. social welfare policy and politics. It has four parts: the big picture
(who are the poor, and how did the welfare state develop?); the programs (social insurance, the safety
net, tax expenditures); two case studies in major reform (welfare reform and the ACA); and the
political forces that shape all of it (public opinion, interest groups, race, and gender).</p>

<h2>Start here</h2>

<ul>
<li><a href="/courses/{COURSE_ID}/pages/course-syllabus">Course Syllabus</a> &mdash; full syllabus, texts, and schedule</li>
<li><a href="/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology">Policy on the Use of Generative AI and Other Technology</a> &mdash; read before the first assignment</li>
</ul>

<h2>Instructor</h2>

<p>David P. Adams, Ph.D.<br>
Office: 516 Gordon Hall<br>
Phone/Text: (657) 278-4770<br>
Email: <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a><br>
Website: <a href="https://dadams.io">dadams.io</a><br>
Office Hours: Mondays and Wednesdays, [TBD], and by
<a href="https://dadams.io/appointments">appointment</a><br>
Schedule meetings: <a href="https://dadams.io/appointments">dadams.io/appointments</a></p>

<p><strong>Response time:</strong> I will strive to respond to all student emails and Canvas messages
within 24 hours, except on weekends and holidays. If you have not received a response within 24 hours,
please send a follow-up message. If you are still waiting after 48 hours, contact me via phone or SMS
at (657) 278-4770.</p>

<h2>Meeting times</h2>

<p>In-Person, Monday &amp; Wednesday, 1:00&ndash;2:15 p.m., [Room TBD]. 3 units.<br>
Three weeks are asynchronous: Week 4 (Sep 14&ndash;16), Week 9 (Oct 19&ndash;21), and Week 14
(Nov 30&ndash;Dec 2).</p>

<h2>Grading summary</h2>

<table{TABLE_STYLE}>
<thead>
<tr><th{TH}>Component</th><th{TH}>Weight</th><th{TH}>Who</th></tr>
</thead>
<tbody>
<tr><td{TD}>Attendance and Participation</td><td{TD}>10%</td><td{TD}>All</td></tr>
<tr><td{TD}>Discussion Papers (5 of 10)</td><td{TD}>10%</td><td{TD}>All</td></tr>
<tr><td{TD}>Midterm Exam</td><td{TD}>20%</td><td{TD}>All</td></tr>
<tr><td{TD}>Final Exam</td><td{TD}>20%</td><td{TD}>All</td></tr>
<tr><td{TD}>Policy Brief</td><td{TD}>20%</td><td{TD}>Undergraduate</td></tr>
<tr><td{TD}>Term Paper</td><td{TD}>20%</td><td{TD}>Undergraduate</td></tr>
<tr><td{TD}>Research Proposal</td><td{TD}>10%</td><td{TD}>Graduate</td></tr>
<tr><td{TD}>Introduction / Outline / Annotated Bibliography</td><td{TD}>10%</td><td{TD}>Graduate</td></tr>
<tr><td{TD}>Final Research Paper</td><td{TD}>20%</td><td{TD}>Graduate</td></tr>
</tbody>
</table>

<h2>Important dates</h2>

<ul>
<li>Midterm Exam: Wednesday, October 14 (in-class)</li>
<li>Graduate Research Proposals due: Monday, October 5</li>
<li>Policy Briefs due (undergraduates): Wednesday, October 28</li>
<li>Term Papers / Graduate Outlines due: Wednesday, December 2</li>
<li>Final Exam: Finals week, December 14&ndash;18 (Registrar-assigned)</li>
<li>Thanksgiving Break: November 23&ndash;27 (no class)</li>
</ul>

<h2>Technical problems</h2>

<p>If you encounter any technical difficulties, contact the instructor immediately to document the
problem. Then contact the
<a href="http://www.fullerton.edu/it/students/helpdesk/index.php">student IT help desk</a>,
<a href="mailto:StudentITHelpDesk@fullerton.edu">email</a>, phone (657) 278-8888, or walk in to the
<a href="http://www.fullerton.edu/it/students/sgc/index.php">student genius center</a>.</p>

<p><strong>For issues with Canvas:</strong> Canvas Support Hotline = (657) 278-8888,
<a href="https://canvashelp.fullerton.edu/">search the CSUF Canvas Guides</a>, or
<a href="https://titans.service-now.com/sp?id=sc_cat_item&amp;sys_id=f88efe80ebea6a10fb7cfcffcad0cdc6&amp;subject=Canvas">report a problem</a>.</p>

<p><strong>Alternative submission:</strong> If you cannot submit an assignment via Canvas, contact the
professor as soon as possible to document the issue and arrange an alternative.</p>
"""

SYLLABUS_BODY = f"""
<p><em>The PDF syllabus is the governing document for this course. This page carries the essentials;
anything that disagrees with the PDF is an error on this page, and I would like to know about it.</em></p>

<p><strong>[UPLOAD THE SYLLABUS PDF AND LINK IT HERE.]</strong></p>

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

<p>Students are expected to adhere to the highest standards of academic integrity. Any student found to
have engaged in academic dishonesty will be subject to the sanctions described in the
<a href="https://www.fullerton.edu/senate/publications_policies_resolutions/ups/UPS%20300/UPS%20300.021.pdf">Academic
Dishonesty Policy</a> (UPS 300.021). Academic dishonesty includes, but is not limited to, cheating,
plagiarism, fabrication, facilitating academic dishonesty, and submitting previously graded work without
prior authorization. Students are expected to be familiar with the university's policy and to adhere to
it in all aspects of this course.</p>

<h2>Generative AI</h2>

<p>See <a href="/courses/{COURSE_ID}/pages/policy-on-the-use-of-generative-ai-and-other-technology">Policy
on the Use of Generative AI and Other Technology</a> for the full policy.</p>
"""

PAGES = [
    ("Course Home", HOME_BODY),
    ("Course Syllabus", SYLLABUS_BODY),
    ("Policy on the Use of Generative AI and Other Technology", AI_POLICY_BODY),
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

    existing_pages = {p["title"]: p for p in list_all(f"/api/v1/courses/{COURSE_ID}/pages")}
    page_urls = {}
    for title, body in PAGES:
        payload = {"wiki_page": {"title": title, "body": body.strip(), "published": False}}
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
                                 "Policy on the Use of Generative AI and Other Technology"], start=1):
        if title in have:
            print(f"  item exists   : {title}")
            continue
        api("POST", f"/api/v1/courses/{COURSE_ID}/modules/{start_id}/items",
            {"module_item": {"type": "Page", "page_url": page_urls[title],
                             "title": title, "position": pos}})
        print(f"  item added    : {title} -> Start Here")

    print(f"\nDone. {len(PAGES)} pages, {len(MODULES)} modules. All unpublished.")


if __name__ == "__main__":
    sys.exit(main())
