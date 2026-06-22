#!/usr/bin/env python3
"""Create the 15 core graded items for CRJU/POSC 320 Summer Session B 2026:
5 Management Brief stages, 5 Research Logs, 5 Discussions (4 adapted from last
year's course + a new Week 5 discussion the old 10-week course didn't have).

Content is adapted from course 3548509 rather than copied verbatim: dates move
from Saturday to Friday, and the Kettl chapter citations are corrected to match
the already-finalized 2026 syllabus's reading schedule (Wk1 ch1-2, Wk2 ch3-4,
Wk3 ch5-6, Wk4 ch7-8, Wk5 ch9-10) -- the source course was a 10-week offering
with a different, finer-grained chapter pace, so its citations don't line up
with the new 5-week schedule.
"""
from __future__ import annotations

import argparse
import json
import sys

from canvas_common import TARGET_COURSE_ID, WEEK_DATES, canvas_get_all, canvas_request, iso, load_ids, merge_ids

HANDOUT_BASE = "https://courses.dadams.io/POSC320/handouts"

DUE_LABEL = {
    1: "Friday, July 3",
    2: "Friday, July 10",
    3: "Friday, July 17",
    4: "Friday, July 24",
    5: "Friday, July 31",
}


def group_ids() -> dict[str, int]:
    ids = load_ids().get("assignment_groups", {})
    if not ids:
        groups = canvas_get_all("/api/v1/courses/{course_id}/assignment_groups", TARGET_COURSE_ID)
        ids = {g["name"]: g["id"] for g in groups}
    return ids


# ---------------------------------------------------------------------------
# Management Brief Project (45%): 5 stages, online_url submission
# ---------------------------------------------------------------------------

POLICY_BRIEF: tuple[dict[str, object], ...] = (
    {
        "week": 1,
        "name": "Management Brief Stage 1: Problem Statement and Research Foundation",
        "points": 10,
        "description": """
<h2>📌 Management Brief Stage 1: Problem Statement and Research Foundation</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 400–600 words<br>
<strong>Points:</strong> 10 (Management Brief Project, 45% of final grade)</p>
<hr>
<h3>📝 What to Do</h3>
<p>This is the first building block of your <a href="{handout_base}/paper_assignment.html" target="_blank">Management Brief</a>. Choose one of the three approved topics and write a clear, focused <strong>problem statement</strong>. Then explain why the issue matters for public administration today—using current evidence and <strong>Kettl Chapters 1–2</strong>.</p>
<hr>
<h3>✍️ Required Elements</h3>
<h4>1. Problem Definition (200–300 words)</h4>
<ul>
<li>State your public administration problem clearly.</li>
<li>Narrow your focus to a specific angle or case.</li>
<li>Connect to <strong>Kettl Ch. 1</strong> using the public values triangle (accountability, efficiency, equity). Include citations.</li>
</ul>
<h4>2. Significance &amp; Evidence (200–300 words)</h4>
<ul>
<li>Why does this issue matter for PA practice?</li>
<li>Use at least 2–3 recent sources (2022–2024) to support your claims.</li>
<li>Apply <strong>Kettl Ch. 2</strong> concepts on "what government does."</li>
</ul>
<hr>
<h3>📤 Submission Instructions — Google Docs Only</h3>
<p><strong>Before you submit</strong>, share your Google Doc with <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a> and set access to <strong>Editor</strong> (Share → add dpadams@fullerton.edu → Editor). Then paste the shareable link into this Canvas assignment. Microsoft Word, PDF, or other file uploads will not be accepted.</p>
<hr>
<h3>✅ Grading Criteria</h3>
<ul>
<li>Clear, specific problem definition</li>
<li>Use of course concepts (Kettl Ch. 1–2)</li>
<li>Relevance and quality of sources</li>
<li>Writing clarity and structure</li>
</ul>
<p>See the full <a href="{handout_base}/paper_assignment_rubric.html" target="_blank">grading rubric</a> and <a href="{handout_base}/paper_assignment.html" target="_blank">assignment overview</a>.</p>
""",
    },
    {
        "week": 2,
        "name": "Management Brief Stage 2: Stakeholder Analysis and Context",
        "points": 15,
        "description": """
<h2>📌 Management Brief Stage 2: Stakeholder Analysis and Context</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 500–700 words (added to your existing Management Brief doc)<br>
<strong>Points:</strong> 15 (Management Brief Project, 45% of final grade)</p>
<hr>
<h3>What to Do</h3>
<p>This week, you're adding two new layers to your Management Brief:</p>
<ol>
<li>A <strong>stakeholder analysis</strong> to identify the actors involved in your issue</li>
<li>A review of the <strong>organizational and institutional context</strong> that shapes how the issue plays out</li>
</ol>
<p>Draw directly from <strong>Kettl Chapters 3–4</strong> to support your analysis. This part of your brief should show that you understand <strong>who matters</strong>, <strong>what they want</strong>, and <strong>why implementation is difficult</strong>.</p>
<hr>
<h3>Required Elements</h3>
<h4>1. Stakeholder Mapping (250–350 words)</h4>
<ul>
<li>Identify key stakeholders involved in your policy area.
  <ul>
    <li><strong>Primary:</strong> Government agencies, elected officials, affected communities</li>
    <li><strong>Secondary:</strong> Contractors, interest groups, other jurisdictions, etc.</li>
  </ul>
</li>
<li>Explain how their <strong>interests, incentives, and roles</strong> create administrative tension or tradeoffs.</li>
<li>Use <strong>Kettl Chapter 3</strong> to connect stakeholders to government tools or functions. Include citations.</li>
</ul>
<h4>2. Contextual Factors (250–350 words)</h4>
<ul>
<li>Identify political, legal, and resource-related challenges affecting implementation.</li>
<li>Apply <strong>at least two concepts from Kettl Chapter 4</strong> to explain why coordination is difficult (e.g., hierarchy, principal-agent dynamics, organizational culture). Include specific page numbers.</li>
</ul>
<hr>
<h3>📤 Submission Instructions — Google Docs Only</h3>
<p>Keep working in the <strong>same Google Doc</strong> you used for Stage 1 — just add your new content below it. Make sure <strong>Suggesting mode</strong> is turned on so I can leave comments, and that the document is still shared with <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a> as Editor. Paste the (same) shareable link into this Canvas assignment.</p>
<hr>
<h3>✅ Grading Criteria</h3>
<ul>
<li>Completeness of stakeholder analysis</li>
<li>Integration of course concepts (Kettl Ch. 3–4)</li>
<li>Clarity in identifying political/legal/resource constraints</li>
<li>Use of evidence and citation</li>
<li>Writing clarity and development</li>
</ul>
<p>See the full <a href="{handout_base}/paper_assignment_rubric.html" target="_blank">grading rubric</a>.</p>
""",
    },
    {
        "week": 3,
        "name": "Management Brief Stage 3: Organizational Theory Application",
        "points": 20,
        "description": """
<h2>📌 Management Brief Stage 3: Organizational Theory Application</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 500–700 words (added to your ongoing Google Doc)<br>
<strong>Points:</strong> 20 (Management Brief Project, 45% of final grade)</p>
<hr>
<h3>Assignment Overview</h3>
<p>This week, you'll add the third section to your Management Brief: a focused analysis of organizational and human capital challenges related to your topic, using <strong>Kettl Chapters 5–6</strong>. Your job: analyze how structure and staffing contribute to the problem you identified in Stage 1 — and what that means for making progress.</p>
<hr>
<h3>What to Include</h3>
<h4>Part 1: Structural Analysis (250–350 words)</h4>
<ul>
<li><strong>Organizational design:</strong> What structures are in place, and how do they shape the problem?</li>
<li><strong>Coordination challenges:</strong> Are there breakdowns across agencies, departments, or levels of government?</li>
<li><strong>Authority and accountability:</strong> Who's responsible for what? How is performance tracked—or not?</li>
<li><strong>Course connection:</strong> Use concepts from <strong>Kettl Chapter 5</strong> on the executive branch. Include specific terms, examples, or citations (with page numbers).</li>
</ul>
<h4>Part 2: Human Capital Challenges (250–350 words)</h4>
<ul>
<li><strong>Personnel issues:</strong> Are there problems with staffing, training, skills, or motivation?</li>
<li><strong>Management capacity:</strong> What leadership or oversight challenges exist?</li>
<li><strong>Organizational culture:</strong> How do norms or values shape performance and behavior?</li>
<li><strong>Course connection:</strong> Use concepts from <strong>Kettl Chapter 6</strong> on human capital. Include specific applications with page numbers.</li>
</ul>
<hr>
<h3>📤 Submission Instructions — Google Docs Only</h3>
<p>Continue in the same shared Google Doc, with <strong>Suggesting mode</strong> on. Paste the shareable link into this Canvas assignment.</p>
<hr>
<h3>✅ Grading Criteria</h3>
<ul>
<li>Structural and human-capital analysis quality</li>
<li>Integration of course concepts (Kettl Ch. 5–6)</li>
<li>Writing clarity and development</li>
</ul>
<p>See the full <a href="{handout_base}/paper_assignment_rubric.html" target="_blank">grading rubric</a>.</p>
""",
    },
    {
        "week": 4,
        "name": "Management Brief Stage 4: Management Challenges and Solutions",
        "points": 25,
        "description": """
<h2>📌 Management Brief Stage 4: Management Challenges and Solutions</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> Add 600–800 words to your existing management brief draft<br>
<strong>Points:</strong> 25 (Management Brief Project, 45% of final grade)</p>
<hr>
<p>This week, you'll extend your management brief by analyzing <strong>key management challenges</strong> and proposing <strong>practical solutions</strong>, drawing on <strong>Kettl Chapters 7–8</strong>. Your goal is to bridge analysis and action: show how theory helps explain what's going wrong—and what could go better.</p>
<h4>🔹 Part 1: Administrative Challenges (300–400 words)</h4>
<ul>
<li><strong>Decision-making problems:</strong> Are information gaps, conflicting priorities, or time pressures affecting quality decisions?</li>
<li><strong>Implementation barriers:</strong> What's preventing effective execution of the policy or program?</li>
<li><strong>Performance measurement gaps:</strong> How do agencies track success—and what's missing?</li>
</ul>
<p>Use <strong>Kettl Chapter 7</strong> to frame your analysis. Be specific—cite decision-making frameworks or examples from the reading.</p>
<h4>🔹 Part 2: Preliminary Solutions (300–400 words)</h4>
<ul>
<li><strong>Process improvements</strong> (e.g., communication, planning)</li>
<li><strong>Resource solutions</strong> (e.g., staffing, funding, tech)</li>
<li><strong>Structural reforms</strong> (e.g., reorganization, new authorities)</li>
</ul>
<p>Connect your proposals to <strong>Kettl Chapter 8</strong>, focusing on budgeting and performance tools.</p>
<hr>
<h3>📤 Submission Instructions — Google Docs Only</h3>
<p>Continue in the same shared Google Doc, with <strong>Suggesting mode</strong> on. Paste the shareable link into this Canvas assignment.</p>
<hr>
<h3>✅ Grading Criteria</h3>
<ul>
<li>Quality of administrative-challenges analysis</li>
<li>Practicality and integration of proposed solutions (Kettl Ch. 7–8)</li>
<li>Writing clarity and development</li>
</ul>
<p>See the full <a href="{handout_base}/paper_assignment_rubric.html" target="_blank">grading rubric</a>.</p>
""",
    },
    {
        "week": 5,
        "name": "Management Brief Stage 5: Final Recommendations and Executive Summary",
        "points": 30,
        "description": """
<h2>📌 Management Brief Stage 5: Final Recommendations and Executive Summary</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> ~400–600 words (recommendations) + revised executive summary (300–400 words)<br>
<strong>Readings:</strong> Kettl Chapters 9–10 (Regulation, Courts &amp; Accountability)<br>
<strong>Total Project Length:</strong> 7–10 pages (2,800–4,200 words)<br>
<strong>Points:</strong> 30 (Management Brief Project, 45% of final grade)</p>
<hr>
<h3>Final Policy Recommendations (400–600 words)</h3>
<p>Your final section should propose <strong>three specific, actionable recommendations</strong> to address the core problem you've been analyzing. Each recommendation should include:</p>
<ul>
<li><strong>Implementation strategy</strong> – How would this recommendation be carried out? Who would do what?</li>
<li><strong>Feasibility assessment</strong> – What political, financial, or administrative constraints might affect this?</li>
<li><strong>Expected outcomes</strong> – What would success look like? How will it be measured?</li>
<li><strong>Textbook integration</strong> – Use concepts from <strong>Kettl Chapters 9–10</strong> (regulation, accountability, courts) with page citations.</li>
</ul>
<h3>Executive Summary (300–400 words)</h3>
<p>Revise the summary you drafted in Stage 1. Include a concise problem overview, key findings, your top recommendations, and a call to action.</p>
<hr>
<h3>📤 Submission Instructions — Google Docs Only</h3>
<p>Use <strong>Suggesting mode</strong> for these final revisions, then <strong>accept your suggestions</strong> so a clean final version sits at the top of the document. Confirm the Google Doc is still shared with <a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a> as Editor, and paste the shareable link into this Canvas assignment.</p>
<hr>
<h3>Final Checklist</h3>
<ul>
<li>Your Google Doc includes all five stages in one place</li>
<li>Sections are clearly labeled with headers</li>
<li>APA in-text citations and reference list are complete</li>
<li>Writing is clean, polished, and professional</li>
<li>Revision history shows your process across all five weeks</li>
</ul>
<p>See the full <a href="{handout_base}/paper_assignment_rubric.html" target="_blank">grading rubric</a>.</p>
""",
    },
)

# ---------------------------------------------------------------------------
# Research Log (10%): 5 entries, online_text_entry
# ---------------------------------------------------------------------------

RESEARCH_LOG: tuple[dict[str, object], ...] = (
    {
        "week": 1,
        "name": "Research Log: Week 1",
        "description": """
<h2>🧠 Research Log: Week 1</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 2–3 thoughtful sentences<br>
<strong>Submission Type:</strong> Text Entry Box only (do not upload a file)<br>
<strong>Points:</strong> 10 (Research Log, 10% of final grade — 5 logs × 2% each)</p>
<hr>
<p>Each week, submit a short reflection on what you discovered, questioned, or learned while researching your management brief topic. This isn't a summary of what you wrote—it's about how you're thinking.</p>
<p>Answer this question in 2–3 sentences:</p>
<blockquote><strong>"What did I learn this week from my research that helped me understand the problem, context, or solutions better?"</strong></blockquote>
<p>Feel free to write informally and in first person. Be honest about surprises, confusion, or breakthroughs.</p>
""",
    },
    {
        "week": 2,
        "name": "Research Log: Week 2",
        "description": """
<h2>🧠 Research Log: Week 2</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 2–3 sentences<br>
<strong>Submission Type:</strong> Text Entry Box only<br>
<strong>Points:</strong> 10 (Research Log, 10% of final grade)</p>
<hr>
<p>What's one thing you learned this week that deepened your understanding of your policy's <strong>stakeholders</strong> or <strong>implementation challenges</strong>?</p>
<p>You don't need to recap your brief—just share an insight, surprise, or frustration from your research. Keep it honest, short, and connected to what you're building.</p>
""",
    },
    {
        "week": 3,
        "name": "Research Log: Week 3",
        "description": """
<h2>🧠 Research Log: Week 3</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 2–3 sentences<br>
<strong>Submission Type:</strong> Text Entry Box only<br>
<strong>Points:</strong> 10 (Research Log, 10% of final grade)</p>
<hr>
<p>Write a 2–3 sentence reflection on what you learned this week about organizational and management factors. This can be a quick summary, insight, or question.</p>
""",
    },
    {
        "week": 4,
        "name": "Research Log: Week 4",
        "description": """
<h2>🧠 Research Log: Week 4</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 2–3 sentences<br>
<strong>Submission Type:</strong> Text Entry Box only<br>
<strong>Points:</strong> 10 (Research Log, 10% of final grade)</p>
<hr>
<p>Write a brief update on your work this week. What source, example, or idea helped you most while writing this week's assignment? Be specific: name the reading, report, or conversation that shaped your thinking.</p>
""",
    },
    {
        "week": 5,
        "name": "Research Log: Final Reflection",
        "description": """
<h2>🧠 Research Log: Final Reflection</h2>
<p><strong>Due:</strong> {due} by 11:59 PM<br>
<strong>Length:</strong> 2–4 sentences<br>
<strong>Submission Type:</strong> Text Entry Box only<br>
<strong>Points:</strong> 10 (Research Log, 10% of final grade)</p>
<hr>
<p>In 2–4 sentences, summarize what you've learned in this project. What's one insight, concept, or skill you'll carry into future work in public service?</p>
""",
    },
)

# ---------------------------------------------------------------------------
# Discussion Posts (15%): 5 graded discussions
# ---------------------------------------------------------------------------

DISCUSSIONS: tuple[dict[str, object], ...] = (
    {
        "week": 1,
        "title": "Week 1 Discussion: Your Experience with Government",
        "message": """
<p><strong>Due:</strong> {due} by 11:59 PM<br><strong>Replies:</strong> Respond to at least 2 classmates by Sunday</p>
<hr>
<p>Public administration isn't abstract—it shows up in your everyday life.</p>
<p>Think about a recent interaction you've had with government. This could be something personal (e.g., a police encounter, court appearance, DMV visit, applying for financial aid or healthcare) or something you've seen in the news that grabbed your attention. Local, state, federal—it all counts.</p>
<p>🔍 <strong>Reflect on:</strong></p>
<ul>
<li>Who were the public administrators involved? What were they doing?</li>
<li>What challenges do you think they face day to day?</li>
<li>How might the concepts we're studying—like accountability, efficiency, or equity—apply to this case?</li>
<li>What questions do you have about how public service actually works?</li>
</ul>
<hr>
<p>💬 <strong>Post your reflection</strong> in the discussion forum (about 200–300 words), then read your classmates' responses and <strong>respond to at least two</strong>.</p>
<hr>
<h3>Grading (10 points)</h3>
<table>
<thead><tr><th>Criteria</th><th>Points</th><th>What That Means</th></tr></thead>
<tbody>
<tr><td>Initial Post Quality</td><td>4 pts</td><td>Thoughtful, specific reflection that connects to public administration concepts. About 200–300 words.</td></tr>
<tr><td>Concept Connection</td><td>2 pts</td><td>References at least one idea from the course (e.g., public values, discretion, equity).</td></tr>
<tr><td>Peer Replies</td><td>2 pts</td><td>Responds meaningfully to at least two classmates.</td></tr>
<tr><td>Clarity &amp; Respect</td><td>2 pts</td><td>Posts are clear, respectful, and professional in tone.</td></tr>
</tbody>
</table>
""",
    },
    {
        "week": 2,
        "title": "Week 2 Discussion: Who's Involved, and Why It's Complicated",
        "message": """
<p><strong>Due:</strong> {due} by 11:59 PM<br><strong>Replies:</strong> Respond to at least 2 classmates by Sunday</p>
<hr>
<p>Public problems aren't just about laws and policies—they're also about people. Behind every issue are <strong>public servants trying to get things done</strong>, <strong>groups pushing their interests</strong>, and <strong>residents hoping for fair outcomes</strong>.</p>
<p>This week, we're asking: Who's actually involved in making public policy work? And what makes it so hard?</p>
<p>Reflect on a real-world issue—maybe your Management Brief topic, or something else you care about. Then answer:</p>
<ul>
<li>Who are the <strong>main stakeholders</strong> involved? (Think: government agencies, elected officials, interest groups, everyday residents.)</li>
<li>What are some <strong>conflicting goals or priorities</strong> they might have?</li>
<li>Why is this issue <strong>hard to manage</strong> from a public administration perspective?</li>
<li>What might make coordination, communication, or fairness difficult?</li>
</ul>
<p>Try to connect your ideas to something from the readings or lecture—like <strong>efficiency</strong>, <strong>equity</strong>, <strong>accountability</strong>, or <strong>tools of government</strong>.</p>
<p><strong>Post your response</strong> (~200 words), then <strong>reply to at least two classmates</strong>.</p>
<hr>
<h3>Grading (10 points)</h3>
<table>
<thead><tr><th>Criteria</th><th>Points</th><th>What That Means</th></tr></thead>
<tbody>
<tr><td>Initial Post</td><td>4 pts</td><td>Specific example, thoughtful reflection</td></tr>
<tr><td>Course Connection</td><td>2 pts</td><td>References a concept like stakeholders, public values, or government tools</td></tr>
<tr><td>Peer Replies</td><td>2 pts</td><td>Responds meaningfully to 2+ classmates</td></tr>
<tr><td>Clarity &amp; Respect</td><td>2 pts</td><td>Clear, respectful, easy to read</td></tr>
</tbody>
</table>
""",
    },
    {
        "week": 3,
        "title": "Week 3 Discussion: Structure, Staffing, and the Struggle to Perform",
        "message": """
<p><strong>Due:</strong> {due} by 11:59 PM<br><strong>Replies:</strong> Respond to at least 2 classmates by Sunday</p>
<hr>
<p>Policies don't implement themselves—people do. And the way government is structured, staffed, and managed has huge consequences for how well things work (or don't).</p>
<p>This week, let's dig into <strong>organizational theory and human capital</strong>. Think about a real-world issue—your Management Brief topic is a great option—and reflect on how structure and staffing affect public service delivery. Then answer:</p>
<ul>
<li>What's <em>one specific organizational challenge</em> affecting this issue? (Think: red tape, silos, unclear lines of authority, turf wars.)</li>
<li>What's <em>one human capital issue</em> that matters? (Think: not enough staff, wrong skills, low morale, leadership gaps.)</li>
<li>Why does this combination make public management difficult?</li>
<li>How might these problems affect real people or communities?</li>
</ul>
<p>Connect your post to something from this week's modules or <strong>Kettl Chapters 5–6</strong>. Use a short quote or page number if it helps.</p>
<p><strong>Post your response (~200 words)</strong>, then reply to two classmates.</p>
<hr>
<h3>Grading (10 points)</h3>
<table>
<thead><tr><th>Criteria</th><th>Points</th><th>What That Means</th></tr></thead>
<tbody>
<tr><td>Initial Post</td><td>4 pts</td><td>Thoughtful and specific example of an organizational or human capital challenge</td></tr>
<tr><td>Course Connection</td><td>2 pts</td><td>References Kettl concepts (e.g., structure, coordination, human capital) or modules</td></tr>
<tr><td>Peer Replies</td><td>2 pts</td><td>Responds meaningfully to 2+ classmates</td></tr>
<tr><td>Clarity &amp; Respect</td><td>2 pts</td><td>Writing is clear, respectful, and easy to follow</td></tr>
</tbody>
</table>
""",
    },
    {
        "week": 4,
        "title": "Week 4 Discussion: Decision-Making Under Pressure",
        "message": """
<p><strong>Due:</strong> {due} by 11:59 PM<br><strong>Replies:</strong> Respond to at least 1 classmate by Sunday</p>
<hr>
<p>Public managers constantly make decisions under conditions of uncertainty. In this week's readings, Kettl describes how information gaps, time constraints, and political pressure affect decision-making.</p>
<p><strong>Prompt:</strong> Think of a public policy or program you're familiar with. Identify a decision point where things went off track—where better information, coordination, or planning might have improved outcomes. What decision-making challenge was at play? What would you have done differently?</p>
<p><em>Notes for Week 4: feel free to stray from your Management Brief topic, especially if you need a little break. Same rubric applies as the previous week, but reply to just <strong>one</strong> classmate this week to save some time — reply to more if you have it.</em></p>
<hr>
<h3>Grading (10 points)</h3>
<table>
<thead><tr><th>Criteria</th><th>Points</th><th>What That Means</th></tr></thead>
<tbody>
<tr><td>Initial Post</td><td>4 pts</td><td>Specific decision point, thoughtful analysis connected to Kettl Ch. 7–8</td></tr>
<tr><td>Course Connection</td><td>2 pts</td><td>References a decision-making or budgeting concept from the reading</td></tr>
<tr><td>Peer Reply</td><td>2 pts</td><td>Responds meaningfully to at least one classmate</td></tr>
<tr><td>Clarity &amp; Respect</td><td>2 pts</td><td>Clear, respectful, easy to read</td></tr>
</tbody>
</table>
""",
    },
    {
        "week": 5,
        "title": "Week 5 Discussion: Balancing Regulation and Innovation",
        "message": """
<p><strong>Due:</strong> {due} by 11:59 PM<br><strong>Replies:</strong> Respond to at least 2 classmates by Sunday</p>
<hr>
<p>Regulation protects the public, but it can also slow things down. This week's readings (<strong>Kettl Chapters 9–10</strong>) look at how oversight, the courts, and accountability mechanisms shape — and sometimes constrain — what agencies can do.</p>
<p>Think of a real or hypothetical case where a regulation or oversight requirement created tension with innovation, speed, or flexibility (e.g., emergency response, new technology adoption, procurement rules, environmental review). Then answer:</p>
<ul>
<li>What was the regulation or oversight mechanism trying to accomplish?</li>
<li>How did it create friction with getting something done quickly or differently?</li>
<li>Where's the right balance between accountability and flexibility in this case?</li>
<li>How does this connect to the courts' or legislature's role in overseeing administrative action?</li>
</ul>
<p><strong>Post your response (~200–300 words)</strong>, then <strong>reply to at least two classmates</strong>.</p>
<hr>
<h3>Grading (10 points)</h3>
<table>
<thead><tr><th>Criteria</th><th>Points</th><th>What That Means</th></tr></thead>
<tbody>
<tr><td>Initial Post Quality</td><td>4 pts</td><td>Specific case, thoughtful reflection connected to regulation/accountability concepts. About 200–300 words.</td></tr>
<tr><td>Concept Connection</td><td>2 pts</td><td>References at least one idea from Kettl Ch. 9–10 (e.g., oversight, judicial review, accountability)</td></tr>
<tr><td>Peer Replies</td><td>2 pts</td><td>Responds meaningfully to at least two classmates</td></tr>
<tr><td>Clarity &amp; Respect</td><td>2 pts</td><td>Posts are clear, respectful, and professional in tone</td></tr>
</tbody>
</table>
""",
    },
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    groups = group_ids()

    existing_assignments = set()
    existing_discussions = set()
    if not args.dry_run:
        existing_assignments = {
            a["name"] for a in canvas_get_all("/api/v1/courses/{course_id}/assignments", TARGET_COURSE_ID)
        }
        existing_discussions = {
            d["title"] for d in canvas_get_all("/api/v1/courses/{course_id}/discussion_topics", TARGET_COURSE_ID)
        }

    created: list[dict[str, object]] = []
    skipped: list[str] = []
    new_ids: dict[str, int] = {}
    discussion_assignment_ids: dict[str, int] = {}

    # Management Brief
    for spec in POLICY_BRIEF:
        name = spec["name"]
        if name in existing_assignments:
            skipped.append(name)
            continue
        week = spec["week"]
        dates = WEEK_DATES[week]
        description = spec["description"].format(due=DUE_LABEL[week], handout_base=HANDOUT_BASE)
        params = [
            ("assignment[name]", name),
            ("assignment[description]", description),
            ("assignment[points_possible]", str(spec["points"])),
            ("assignment[assignment_group_id]", str(groups["Management Brief Project"])),
            ("assignment[submission_types][]", "online_url"),
            ("assignment[due_at]", iso(dates["due_at"])),
            ("assignment[unlock_at]", iso(dates["unlock_at"])),
            ("assignment[lock_at]", iso(dates["lock_at"])),
        ]
        if args.dry_run:
            print(f"DRY RUN: create assignment {name!r} ({spec['points']} pts, due {DUE_LABEL[week]})")
            continue
        resp = canvas_request("POST", "/api/v1/courses/{course_id}/assignments", params, course_id=TARGET_COURSE_ID)
        new_ids[name] = resp["id"]
        created.append({"type": "policy_brief", "name": name, "id": resp["id"]})

    # Research Log
    for spec in RESEARCH_LOG:
        name = spec["name"]
        if name in existing_assignments:
            skipped.append(name)
            continue
        week = spec["week"]
        dates = WEEK_DATES[week]
        description = spec["description"].format(due=DUE_LABEL[week])
        params = [
            ("assignment[name]", name),
            ("assignment[description]", description),
            ("assignment[points_possible]", "10"),
            ("assignment[assignment_group_id]", str(groups["Research Log"])),
            ("assignment[submission_types][]", "online_text_entry"),
            ("assignment[due_at]", iso(dates["due_at"])),
            ("assignment[unlock_at]", iso(dates["unlock_at"])),
            ("assignment[lock_at]", iso(dates["lock_at"])),
        ]
        if args.dry_run:
            print(f"DRY RUN: create assignment {name!r} (10 pts, due {DUE_LABEL[week]})")
            continue
        resp = canvas_request("POST", "/api/v1/courses/{course_id}/assignments", params, course_id=TARGET_COURSE_ID)
        new_ids[name] = resp["id"]
        created.append({"type": "research_log", "name": name, "id": resp["id"]})

    # Discussions (graded)
    for spec in DISCUSSIONS:
        title = spec["title"]
        if title in existing_discussions:
            skipped.append(title)
            continue
        week = spec["week"]
        dates = WEEK_DATES[week]
        message = spec["message"].format(due=DUE_LABEL[week])
        params = [
            ("title", title),
            ("message", message),
            ("discussion_type", "threaded"),
            ("published", "false"),
            ("assignment[points_possible]", "10"),
            ("assignment[assignment_group_id]", str(groups["Discussion Posts"])),
            ("assignment[due_at]", iso(dates["due_at"])),
            ("delayed_post_at", iso(dates["unlock_at"])),
            ("lock_at", iso(dates["lock_at"])),
        ]
        if args.dry_run:
            print(f"DRY RUN: create discussion {title!r} (10 pts, due {DUE_LABEL[week]})")
            continue
        resp = canvas_request(
            "POST", "/api/v1/courses/{course_id}/discussion_topics", params, course_id=TARGET_COURSE_ID
        )
        new_ids[title] = resp["id"]
        discussion_assignment_ids[title] = resp["assignment_id"]
        created.append(
            {"type": "discussion", "name": title, "id": resp["id"], "assignment_id": resp["assignment_id"]}
        )

    if not args.dry_run and new_ids:
        merge_ids("core_assignments", new_ids)
    if not args.dry_run and discussion_assignment_ids:
        merge_ids("discussion_assignment_ids", discussion_assignment_ids)

    print(json.dumps({"created": created, "skipped_existing": skipped}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
