#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


COURSE_ID = "3631775"
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")
DASH = "\u2014"


def require_env():
    missing = [name for name, value in (("CANVAS_BASE_URL", BASE_URL), ("CANVAS_TOKEN", TOKEN)) if not value]
    if missing:
        raise SystemExit(f"Missing required environment variable(s): {', '.join(missing)}")


def api_request(method, path, payload=None, params=None):
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        sep = "&" if "?" in path else "?"
        path = f"{path}{sep}{query}"

    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    data = None
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {body}") from exc


def list_all(path):
    rows = []
    page = 1
    while True:
        batch = api_request("GET", path, params={"per_page": 100, "page": page})
        if not isinstance(batch, list):
            raise RuntimeError(f"Expected list from {path}, got {type(batch).__name__}")
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        page += 1


def html_list(items):
    return "<ul>\n" + "\n".join(f"<li>{item}</li>" for item in items) + "\n</ul>"


def landing_page_body():
    return f"""
<h2>Welcome</h2>
<p>Metropolitan politics is the study of how fragmented systems attempt to govern interdependent regional problems. This five-week independent study introduces major theories and institutional frameworks associated with metropolitan governance and policymaking, focusing on fragmentation, polycentric governance, intergovernmental relations, and regional policy coordination.</p>
<p>The independent study also serves as a pilot version of a future full-semester course on metropolitan governance (POSC 427). The central question guiding the work is:</p>
<blockquote><p><em>Why is metropolitan governance in Southern California so fragmented, and how does anything get solved anyway?</em></p></blockquote>

<h2>Instructor Contact</h2>
<dl>
<dt>Instructor</dt><dd>David P. Adams, Ph.D.</dd>
<dt>Office</dt><dd>516 Gordon Hall</dd>
<dt>Phone/Text</dt><dd>(657) 278-4770</dd>
<dt>Email</dt><dd><a href="mailto:dpadams@fullerton.edu">dpadams@fullerton.edu</a></dd>
<dt>Website</dt><dd><a href="https://dadams.io">dadams.io</a></dd>
<dt>Office Hours / meetings</dt><dd>By <a href="https://dadams.io/appointments">appointment</a> -- <a href="https://dadams.io/appointments">dadams.io/appointments</a></dd>
</dl>

<h2>Course Format</h2>
<p>Independent study, fully online/asynchronous with weekly instructor check-ins.</p>
<p>All readings, assignments, and announcements are organized in <em>Canvas</em>, and we will communicate via <em>Canvas</em> and university email. Check both at least once daily during the five-week term.</p>
<p><strong>Response time:</strong> I will strive to respond to email and <em>Canvas</em> messages within 24 hours, except on weekends and holidays. If you have not heard back within 24 hours, send a follow-up; after 48 hours, contact me via phone or SMS at (657) 278-4770.</p>
<p><strong>Weekly check-in:</strong> We will meet once each week (in person or by video) to discuss the week's readings, review your written work, and set goals for the following week. Meeting times are arranged at <a href="https://dadams.io/appointments">dadams.io/appointments</a>.</p>

<h2>Grading Summary</h2>
<table>
<thead><tr><th scope="col">Assignment</th><th scope="col">Weight</th><th scope="col">Canvas Points</th><th scope="col">Due</th></tr></thead>
<tbody>
<tr><td>Weekly Analytical Reflections (5)</td><td>30%</td><td>30 total; 6 each</td><td>Weekly, before check-in</td></tr>
<tr><td>Governance Mapping Exercise</td><td>20%</td><td>20</td><td>End of Week 2</td></tr>
<tr><td>Final Metropolitan Governance Analysis</td><td>50%</td><td>50</td><td>End of Week 5</td></tr>
<tr><td><strong>Total</strong></td><td><strong>100%</strong></td><td><strong>100</strong></td><td></td></tr>
</tbody>
</table>

<h2>Schedule Highlights</h2>
<table>
<thead><tr><th scope="col">Week</th><th scope="col">Dates</th><th scope="col">Theme</th><th scope="col">Due Date</th></tr></thead>
<tbody>
<tr><td>Week 1</td><td>May 26-29, 2026</td><td>What Is Metropolitan Governance?</td><td>Friday, May 29, 2026</td></tr>
<tr><td>Week 2</td><td>June 1-5, 2026</td><td>Polycentric Governance and Institutional Collective Action</td><td>Friday, June 5, 2026</td></tr>
<tr><td>Week 3</td><td>June 8-12, 2026</td><td>Power and Political Economy</td><td>Friday, June 12, 2026</td></tr>
<tr><td>Week 4</td><td>June 15-20, 2026</td><td>Governing Metropolitan Problems</td><td>Saturday, June 20, 2026; June 19 is Juneteenth</td></tr>
<tr><td>Week 5</td><td>June 22-26, 2026</td><td>Metropolitan Futures</td><td>Friday, June 26, 2026</td></tr>
</tbody>
</table>

<h2>Student Resources Website</h2>
<p>It is the student's responsibility to read and understand the required and important <a href="https://fdc.fullerton.edu/teaching/student-info-syllabi.html">student information for course syllabi</a>. Included is information about:</p>
<ul>
<li>University learning goals and General Education learning objectives</li>
<li>Students' rights to accommodations</li>
<li>Campus student support resources and academic integrity</li>
<li>Emergency preparedness; library and IT services</li>
<li>Software privacy, accessibility statement, diversity statement, and land acknowledgement</li>
<li>Final exam schedule and semester calendar</li>
</ul>

<h2>Course Policies</h2>
<h3>Make-up and late submission policy</h3>
<p>Because this is a compressed five-week term with weekly check-ins, deadlines matter. Extensions must be requested in writing before the due date and will be granted only for illness or other documented unforeseen circumstances. Late work without an approved extension loses one-third of a letter grade per calendar day.</p>

<h3>Alternative procedures for submitting work</h3>
<p>The student submits all written work via <em>Canvas</em>. If you cannot submit via <em>Canvas</em>, contact the professor immediately to arrange an alternative.</p>

<h3>Academic Integrity</h3>
<p>The student is expected to adhere to the highest standards of academic integrity. Academic dishonesty will be subject to the sanctions described in the <a href="https://www.fullerton.edu/senate/publications_policies_resolutions/ups/UPS%20300/UPS%20300.021.pdf">Academic Dishonesty Policy</a> (UPS 300.021), which includes, but is not limited to, cheating, plagiarism, fabrication, facilitating academic dishonesty, and submitting previously graded work without prior authorization.</p>

<h3>Policy on the Use of Generative AI and Other Technology</h3>
<p>Generative AI (including large language models, image generators, and other tools) is permitted in this course, but use must be transparent, intentional, and in service of learning. The core principle is simple: <strong>you must do the intellectual work of this course</strong>. AI can amplify your thinking, but not replace it.</p>
<h4>Permitted uses:</h4>
<ul>
<li>Brainstorming and outlining arguments</li>
<li>Explaining concepts you don't understand (then explaining it back in your own words)</li>
<li>Literature searching and summarizing sources</li>
<li>Editing, proofreading, and revising your work</li>
<li>Sanity-checking your analysis or logic</li>
<li>Generating synthetic examples or test cases for your ideas</li>
</ul>
<h4>Not permitted:</h4>
<ul>
<li>Using AI to generate your analysis, arguments, or conclusions</li>
<li>Submitting AI-generated text as your own writing</li>
<li>Using AI to avoid engaging with course concepts or readings</li>
<li>Letting AI do the intellectual heavy lifting (interpreting sources, building arguments, synthesizing ideas)</li>
</ul>
<h4>Disclosure requirement:</h4>
<p>If you use generative AI tools in ways beyond basic editing, you must disclose your use. Include a brief note at the end of your assignment explaining what tools you used and how (e.g., "I used Claude to help organize my outline and check the logic of my argument in Section 3"). This is not a confession&mdash;it's transparency about your process.</p>
<h4>What this means:</h4>
<p>The goal of this course is for <em>you</em> to learn to think like a policy analyst and to develop your own informed arguments about metropolitan governance. AI is a tool that can enhance that learning if used thoughtfully. Using it to avoid thinking will undermine your own education and violates academic integrity. Questions about what constitutes appropriate use? Ask before you submit.</p>
"""


WEEKS = [
    {
        "num": 1,
        "title": "What Is Metropolitan Governance?",
        "dates": "May 26-29, 2026",
        "due_label": "Friday, May 29, 2026",
        "due_at": "2026-05-29T23:59:00-07:00",
        "topics": [
            "Metropolitan regions",
            "Urbanization",
            "Governance and fragmentation",
        ],
        "readings": [
            "Judd and Hinze, chapters 1&ndash;2",
            "Peterson, Paul E. 1981. <em>City Limits.</em> Chicago, IL: University of Chicago Press (selected chapters).",
            'Ostrom, Vincent, Charles M. Tiebout, and Robert Warren. 1961. "The Organization of Government in Metropolitan Areas: A Theoretical Inquiry." <em>American Political Science Review</em> 55(4): 831&ndash;842.',
            'Ansell, Chris, and Alison Gash. 2008. "Collaborative Governance in Theory and Practice." <em>Journal of Public Administration Research and Theory</em> 18(4): 543&ndash;571.',
        ],
        "assignments": ["Weekly Analytical Reflection 1"],
    },
    {
        "num": 2,
        "title": "Polycentric Governance and Institutional Collective Action",
        "dates": "June 1-5, 2026",
        "due_label": "Friday, June 5, 2026",
        "due_at": "2026-06-05T23:59:00-07:00",
        "topics": [
            "Polycentric systems",
            "Institutional collective action",
            "Regional coordination",
        ],
        "readings": [
            "Feiock, Richard C., and John T. Scholz, eds. 2010. <em>Self-Organizing Federalism: Collaborative Mechanisms to Mitigate Institutional Collective Action Dilemmas</em>. Cambridge University Press (selected chapters provided on Canvas).",
            "Oakerson, Ronald J. 1999. <em>Governing Local Public Economies: Creating a Civic Metropolis</em>. ICS Press (selected chapters provided on Canvas).",
            'Ostrom, Elinor. 2010. "Beyond Markets and States: Polycentric Governance of Complex Economic Systems." <em>American Economic Review</em> 100(3): 641&ndash;672.',
            'Dietz, Thomas, Elinor Ostrom, and Paul C. Stern. 2003. "The Struggle to Govern the Commons." <em>Science</em> 302(5652): 1907&ndash;1912.',
        ],
        "assignments": ["Weekly Analytical Reflection 2", "Governance Mapping Exercise"],
    },
    {
        "num": 3,
        "title": "Power and Political Economy",
        "dates": "June 8-12, 2026",
        "due_label": "Friday, June 12, 2026",
        "due_at": "2026-06-12T23:59:00-07:00",
        "topics": [
            "Urban regimes",
            "Growth machine theory",
            "Development politics",
        ],
        "readings": [
            "Stone, Clarence N. 1989. <em>Regime Politics: Governing Atlanta, 1946&ndash;1988.</em> Lawrence, KS: University Press of Kansas (selected chapters).",
            'Logan, John R., and Harvey L. Molotch. 1987. <em>Urban Fortunes: The Political Economy of Place.</em> Berkeley, CA: University of California Press, "The City as a Growth Machine" chapter.',
            'O\'Toole, Laurence J., and Kenneth J. Meier. 2004. "Desperately Seeking Selznick: Cooptation and the Dark Side of Public Management in Networks." <em>Public Administration Review</em> 64(6): 681&ndash;693.',
        ],
        "assignments": ["Weekly Analytical Reflection 3"],
    },
    {
        "num": 4,
        "title": "Governing Metropolitan Problems",
        "dates": "June 15-20, 2026",
        "due_label": "Saturday, June 20, 2026",
        "due_at": "2026-06-20T23:59:00-07:00",
        "topics": [
            "Housing",
            "Transportation",
            "Climate governance",
            "Homelessness",
        ],
        "readings": [
            'Lubell, Mark, Adam Douglas Henry, and Mike McCoy. 2010. "Collaborative Institutions in an Ecology of Games." <em>American Journal of Political Science</em> 54(2): 287&ndash;300.',
            'Bryson, John M., Barbara C. Crosby, and Melissa Middleton Stone. 2006. "The Design and Implementation of Cross-Sector Collaborations: Propositions from the Literature." <em>Public Administration Review</em> 66(s1): 44&ndash;55.',
            'Imperial, Mark T. 2005. "Using Collaboration as a Governance Strategy: Six Lessons from Watershed Management Programs." <em>Administration &amp; Society</em> 37(3): 281&ndash;320.',
            'Gerlak, Andrea K. 2006. "Federalism and U.S. Water Policy: Lessons for the Twenty-First Century." <em>Publius: The Journal of Federalism</em> 36(2): 231&ndash;257.',
        ],
        "assignments": ["Weekly Analytical Reflection 4"],
        "note": "June 19 is Juneteenth; this week's due date is moved to Saturday.",
    },
    {
        "num": 5,
        "title": "Metropolitan Futures",
        "dates": "June 22-26, 2026",
        "due_label": "Friday, June 26, 2026",
        "due_at": "2026-06-26T23:59:00-07:00",
        "topics": [
            "Smart cities",
            "Resilience",
            "Crisis governance",
        ],
        "readings": [
            "Emerson, Kirk, and Tina Nabatchi. 2015. <em>Collaborative Governance Regimes</em>. Georgetown University Press (selected chapters; integrative framework).",
            'Thomson, Ann Marie, and James L. Perry. 2006. "Collaboration Processes: Inside the Black Box." <em>Public Administration Review</em> 66(s1): 20&ndash;32.',
            'Scholz, John T., Ramiro Berardo, and Brad Kile. 2008. "Do Networks Solve Collective Action Problems? Credibility, Search, and Collaboration." <em>Journal of Politics</em> 70(2): 393&ndash;406.',
            'Meijer, Albert, and Manuel Pedro Rodr&iacute;guez Bol&iacute;var. 2016. "Governing the Smart City: A Review of the Literature on Smart Urban Governance." <em>International Review of Administrative Sciences</em> 82(2): 392&ndash;408.',
        ],
        "assignments": ["Weekly Analytical Reflection 5", "Final Metropolitan Governance Analysis"],
    },
]


def overview_body(week):
    due_note = f"<p><strong>Due:</strong> {', '.join(week['assignments'])} by 11:59 p.m. on {week['due_label']}.</p>"
    holiday_note = f"<p><strong>Holiday adjustment:</strong> {week['note']}</p>" if week.get("note") else ""
    return f"""
<h2>Week {week['num']} {DASH} {week['title']}</h2>
<p><strong>Dates:</strong> {week['dates']}</p>
{due_note}
{holiday_note}
<h3>Topics</h3>
{html_list(week['topics'])}
<h3>Readings</h3>
{html_list(week['readings'])}
<h3>Assignments</h3>
{html_list(week['assignments'])}
"""


def weekly_reflection_description(week):
    if week["num"] == 1:
        return f"""
<h2>Purpose</h2>
<p>This short paper asks you to use the first week's readings to make a focused argument about the course's central question: <em>Why is metropolitan governance in Southern California so fragmented, and how does anything get solved anyway?</em></p>

<h2>Length</h2>
<p>500-700 words, not including a works cited list. This should be a focused 2-3 page paper, not a summary of every reading.</p>

<h2>Prompt</h2>
<p>Use at least two Week 1 readings to answer this question: <strong>What makes metropolitan governance different from ordinary city government, and why does fragmentation matter?</strong></p>

<h2>What to Include</h2>
<ul>
<li>A clear opening claim in the first paragraph.</li>
<li>A brief explanation of one key concept from the readings, such as fragmentation, metropolitan regions, local public economies, or collaborative governance.</li>
<li>A concrete application to Southern California or another metropolitan region.</li>
<li>A short conclusion explaining what your example shows about metropolitan governance.</li>
</ul>

<h2>Brief Example</h2>
<p>A strong reflection might argue that transportation and housing problems in Southern California do not fit neatly inside city boundaries, even though cities remain central decision makers. For example, a student might connect Ostrom, Tiebout, and Warren's argument about fragmented metropolitan institutions to the difficulty of coordinating housing production across many municipalities, then use Ansell and Gash to explain why collaboration is possible but politically demanding.</p>

<h2>Due</h2>
<p>{week['due_label']} at 11:59 p.m. Pacific time.</p>
"""

    return f"""
<p>A short analytical reflection each week connecting that week's readings to the course's central question. Submitted via Canvas before the weekly check-in.</p>
<p><strong>Week {week['num']} focus:</strong> {week['title']}</p>
<p><strong>Due:</strong> {week['due_label']} at 11:59 p.m. Pacific time.</p>
"""


def governance_mapping_description():
    return """
<h2>Purpose</h2>
<p>The governance mapping exercise asks you to identify the institutions, actors, and intergovernmental relationships involved in one regional policy problem. Your goal is to show how fragmentation shapes policy action: where it creates obstacles, where it creates useful specialization or flexibility, and where coordination is needed.</p>

<h2>Length</h2>
<p>1,000-1,400 words, plus one governance map. The map can be a simple diagram, table, flow chart, or clearly organized actor list. The prose should be about 4-5 double-spaced pages.</p>

<h2>Prompt</h2>
<p>Choose one metropolitan policy problem, preferably in Southern California. Examples include housing, homelessness, transportation, climate adaptation, water, policing, emergency management, or economic development. Map the main public, nonprofit, private, and intergovernmental actors involved, then explain how authority, funding, information, and accountability move among them.</p>

<h2>What to Submit</h2>
<ul>
<li><strong>Governance map:</strong> a visual or structured representation of the main actors and relationships.</li>
<li><strong>Short analysis:</strong> a written explanation of what the map shows.</li>
</ul>

<h2>Suggested Structure</h2>
<ol>
<li><strong>Policy problem and region:</strong> Identify the problem and explain why it is metropolitan rather than purely local.</li>
<li><strong>Actors and institutions:</strong> Identify the major governments, agencies, special districts, regional bodies, nonprofits, private actors, and community stakeholders.</li>
<li><strong>Relationships:</strong> Explain who has authority, who controls resources, who coordinates with whom, and where responsibilities overlap.</li>
<li><strong>Fragmentation analysis:</strong> Explain where fragmentation helps, where it hinders, and what collective-action problem appears most important.</li>
<li><strong>Coordination options:</strong> Briefly identify one practical way coordination could be improved.</li>
</ol>

<h2>Brief Example</h2>
<p>A student writing about homelessness in Orange County might map city governments, the county, the Continuum of Care, nonprofit service providers, housing authorities, police departments, state housing agencies, and neighborhood groups. The analysis might show that fragmentation allows cities to tailor services locally, but also creates disputes over shelter siting, uneven funding, and weak regional accountability. The paper could then use institutional collective action to explain why cooperation is difficult even when every jurisdiction is affected by the same regional problem.</p>

<h2>Due</h2>
<p>Friday, June 5, 2026 at 11:59 p.m. Pacific time.</p>
"""


def final_analysis_description():
    return """
<h2>Purpose</h2>
<p>The final analysis is an original paper applying course frameworks to a metropolitan governance problem. The paper should make an argument, not simply describe a policy area. You should explain how a metropolitan governance problem is structured, why it is difficult to solve, and what the course readings help us understand about it.</p>

<h2>Length</h2>
<p>2,000-2,500 words, not including references. This is roughly 7-9 double-spaced pages. For a five-week summer course, the priority is a focused, well-supported argument rather than a broad research paper.</p>

<h2>Prompt</h2>
<p>Choose one metropolitan governance problem, ideally from Southern California. Use course concepts such as fragmentation, polycentric governance, institutional collective action, collaborative governance, urban regimes, growth machines, or cross-sector collaboration to analyze why the problem is difficult to govern and what kinds of coordination might improve the situation.</p>

<h2>Suggested Outline</h2>
<ol>
<li><strong>Introduction and thesis:</strong> State the policy problem, the metropolitan region, and your main argument.</li>
<li><strong>Why this is a metropolitan problem:</strong> Explain why the issue crosses city, county, agency, sector, or jurisdictional boundaries.</li>
<li><strong>Governance landscape:</strong> Identify the main institutions and actors involved.</li>
<li><strong>Course framework:</strong> Explain the concept or concepts you will use to analyze the case.</li>
<li><strong>Analysis:</strong> Show how the governance structure creates obstacles, opportunities, incentives, or collective-action problems.</li>
<li><strong>Policy implications:</strong> Identify a realistic coordination strategy, reform, or governance arrangement and explain its tradeoffs.</li>
<li><strong>Conclusion:</strong> Return to the course's central question and explain what your case teaches us about metropolitan governance.</li>
</ol>

<h2>Brief Example</h2>
<p>A paper on regional transportation in Los Angeles might ask why a labor market and travel network that operate regionally are governed through a mix of Metro, municipal governments, SCAG, Caltrans, county actors, and state and federal funding rules. The paper could apply polycentric governance and institutional collective action to argue that overlapping authority can create local responsiveness and experimentation, but also delays, uneven priorities, and coordination costs. A focused policy implication might evaluate whether stronger regional planning incentives, shared funding agreements, or project-specific collaboration would address the problem without eliminating local authority.</p>

<h2>Due</h2>
<p>Friday, June 26, 2026 at 11:59 p.m. Pacific time.</p>
"""


ASSIGNMENTS = []
for week in WEEKS:
    ASSIGNMENTS.append(
        {
            "name": f"Weekly Analytical Reflection {week['num']}",
            "points_possible": 6,
            "due_at": week["due_at"],
            "week": week["num"],
            "description": weekly_reflection_description(week),
        }
    )

ASSIGNMENTS.extend(
    [
        {
            "name": "Governance Mapping Exercise",
            "points_possible": 20,
            "due_at": "2026-06-05T23:59:00-07:00",
            "week": 2,
            "description": governance_mapping_description(),
        },
        {
            "name": "Final Metropolitan Governance Analysis",
            "points_possible": 50,
            "due_at": "2026-06-26T23:59:00-07:00",
            "week": 5,
            "description": final_analysis_description(),
        },
    ]
)

PROMPT_UPDATE_NAMES = {
    "Weekly Analytical Reflection 1",
    "Governance Mapping Exercise",
    "Final Metropolitan Governance Analysis",
}


def criterion(description, long_description, points, ratings):
    return {
        "description": description,
        "long_description": long_description,
        "points": points,
        "ratings": ratings,
    }


def rating(description, long_description, points):
    return {
        "description": description,
        "long_description": long_description,
        "points": points,
    }


RUBRIC_DEFINITIONS = [
    {
        "title": "Weekly Analytical Reflection Rubric",
        "assignment_names": [f"Weekly Analytical Reflection {num}" for num in range(1, 6)],
        "criteria": [
            criterion(
                "Focused argument",
                "The reflection directly answers the weekly prompt with a clear, specific claim rather than only summarizing the readings.",
                2,
                [
                    rating("Strong", "Clear, focused claim that addresses the prompt.", 2),
                    rating("Developing", "Claim is present but broad, descriptive, or only partly focused.", 1),
                    rating("Needs revision", "No clear claim or the response does not answer the prompt.", 0),
                ],
            ),
            criterion(
                "Use of readings and concepts",
                "The reflection accurately uses at least two assigned readings or course concepts to support the argument.",
                2,
                [
                    rating("Strong", "Uses readings or concepts accurately and connects them to the argument.", 2),
                    rating("Developing", "Uses course material, but the connection is thin or partly unclear.", 1),
                    rating("Needs revision", "Little or no meaningful use of assigned readings or course concepts.", 0),
                ],
            ),
            criterion(
                "Application and clarity",
                "The reflection applies the ideas to metropolitan governance and is organized, concise, and readable.",
                2,
                [
                    rating("Strong", "Applies ideas to a concrete governance issue and is clearly written.", 2),
                    rating("Developing", "Application or writing is present but uneven.", 1),
                    rating("Needs revision", "Application is missing or writing problems obscure the point.", 0),
                ],
            ),
        ],
    },
    {
        "title": "Governance Mapping Exercise Rubric",
        "assignment_names": ["Governance Mapping Exercise"],
        "criteria": [
            criterion(
                "Policy problem and metropolitan scope",
                "Defines a clear regional policy problem and explains why it crosses local jurisdictional or sectoral boundaries.",
                4,
                [
                    rating("Excellent", "Problem and metropolitan scope are clear, specific, and well motivated.", 4),
                    rating("Good", "Problem and regional scope are mostly clear.", 3),
                    rating("Developing", "Problem is identified but scope is underdeveloped.", 2),
                    rating("Missing", "Problem or metropolitan scope is unclear.", 0),
                ],
            ),
            criterion(
                "Governance map",
                "Identifies the central actors, institutions, and relationships involved in the policy problem.",
                5,
                [
                    rating("Excellent", "Map is accurate, readable, and captures major actors and relationships.", 5),
                    rating("Good", "Map includes major actors with mostly clear relationships.", 4),
                    rating("Developing", "Map is incomplete or relationships are only partly clear.", 2),
                    rating("Missing", "Map is absent or not usable.", 0),
                ],
            ),
            criterion(
                "Fragmentation and course-concept analysis",
                "Explains how fragmentation, polycentric governance, or institutional collective action shapes the case.",
                5,
                [
                    rating("Excellent", "Analysis clearly applies course concepts to explain governance dynamics.", 5),
                    rating("Good", "Uses course concepts with generally sound analysis.", 4),
                    rating("Developing", "Concepts are named but weakly applied.", 2),
                    rating("Missing", "Little or no course-concept analysis.", 0),
                ],
            ),
            criterion(
                "Coordination options and tradeoffs",
                "Identifies a practical coordination option and explains likely benefits and limits.",
                3,
                [
                    rating("Excellent", "Coordination option is realistic and includes clear tradeoffs.", 3),
                    rating("Developing", "Coordination option is plausible but thinly explained.", 2),
                    rating("Needs revision", "Coordination option is vague or unrealistic.", 1),
                    rating("Missing", "No coordination option is offered.", 0),
                ],
            ),
            criterion(
                "Organization, evidence, and writing",
                "The submission follows the assignment structure, uses appropriate evidence, and is clear enough for a compressed summer course.",
                3,
                [
                    rating("Excellent", "Well organized, appropriately supported, and clear.", 3),
                    rating("Developing", "Generally readable but uneven in organization or support.", 2),
                    rating("Needs revision", "Difficult to follow or weakly supported.", 1),
                    rating("Missing", "Does not meet basic submission expectations.", 0),
                ],
            ),
        ],
    },
    {
        "title": "Final Metropolitan Governance Analysis Rubric",
        "assignment_names": ["Final Metropolitan Governance Analysis"],
        "criteria": [
            criterion(
                "Thesis and problem framing",
                "States a clear argument about a metropolitan governance problem and frames why the problem matters.",
                10,
                [
                    rating("Excellent", "Specific, arguable thesis with strong problem framing.", 10),
                    rating("Good", "Clear thesis and adequate problem framing.", 8),
                    rating("Developing", "Thesis or framing is present but underdeveloped.", 6),
                    rating("Missing", "No clear thesis or policy problem.", 0),
                ],
            ),
            criterion(
                "Governance landscape and evidence",
                "Identifies relevant actors, institutions, jurisdictional relationships, and case evidence.",
                10,
                [
                    rating("Excellent", "Governance landscape is accurate, detailed, and supported.", 10),
                    rating("Good", "Key actors and institutions are identified with adequate support.", 8),
                    rating("Developing", "Coverage is incomplete or evidence is thin.", 6),
                    rating("Missing", "Little evidence of the governance landscape.", 0),
                ],
            ),
            criterion(
                "Use of course frameworks",
                "Applies course frameworks such as fragmentation, polycentric governance, institutional collective action, collaborative governance, regimes, or growth machines.",
                10,
                [
                    rating("Excellent", "Frameworks are explained and applied insightfully.", 10),
                    rating("Good", "Frameworks are used accurately with sound application.", 8),
                    rating("Developing", "Frameworks are named but only partly applied.", 6),
                    rating("Missing", "Little or no use of course frameworks.", 0),
                ],
            ),
            criterion(
                "Analysis and policy implications",
                "Explains why the problem is difficult to govern and evaluates a realistic coordination strategy or reform.",
                10,
                [
                    rating("Excellent", "Analysis is convincing and policy implications are realistic with tradeoffs.", 10),
                    rating("Good", "Analysis is sound and implications are plausible.", 8),
                    rating("Developing", "Analysis or implications are underdeveloped.", 6),
                    rating("Missing", "Mostly descriptive, with little analysis or implication.", 0),
                ],
            ),
            criterion(
                "Organization, writing, and citations",
                "The paper is well organized, readable, appropriately cited, and scaled to the assigned length.",
                10,
                [
                    rating("Excellent", "Clear structure, polished writing, and appropriate citation practice.", 10),
                    rating("Good", "Generally clear and organized with minor writing or citation issues.", 8),
                    rating("Developing", "Readable but uneven in structure, writing, or citations.", 6),
                    rating("Missing", "Major writing, structure, or citation problems.", 0),
                ],
            ),
        ],
    },
]


def create_or_get_page(title, body, front_page=False):
    pages = list_all(f"/api/v1/courses/{COURSE_ID}/pages")
    by_title = {page["title"]: page for page in pages}
    if title in by_title:
        return by_title[title], False

    payload = {
        "wiki_page": {
            "title": title,
            "body": body,
            "published": False,
            "front_page": front_page,
        }
    }
    return api_request("POST", f"/api/v1/courses/{COURSE_ID}/pages", payload), True


def create_or_get_module(name, position):
    modules = list_all(f"/api/v1/courses/{COURSE_ID}/modules")
    by_name = {module["name"]: module for module in modules}
    if name in by_name:
        return by_name[name], False

    payload = {"module": {"name": name, "position": position, "published": False}}
    return api_request("POST", f"/api/v1/courses/{COURSE_ID}/modules", payload), True


def create_or_get_assignment(assignment):
    existing = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")
    by_name = {item["name"]: item for item in existing}
    if assignment["name"] in by_name:
        return by_name[assignment["name"]], False

    payload = {
        "assignment": {
            "name": assignment["name"],
            "description": assignment["description"],
            "points_possible": assignment["points_possible"],
            "due_at": assignment["due_at"],
            "published": False,
            "submission_types": ["online_upload"],
            "grading_type": "points",
        }
    }
    return api_request("POST", f"/api/v1/courses/{COURSE_ID}/assignments", payload), True


def module_item_exists(module_id, item_type, content_id=None, page_url=None):
    items = list_all(f"/api/v1/courses/{COURSE_ID}/modules/{module_id}/items")
    for item in items:
        if item.get("type") != item_type:
            continue
        if item_type == "Assignment" and item.get("content_id") == content_id:
            return True
        if item_type == "Page" and item.get("page_url") == page_url:
            return True
    return False


def add_module_page(module_id, page, position):
    if module_item_exists(module_id, "Page", page_url=page["url"]):
        return None, False
    payload = {"module_item": {"type": "Page", "page_url": page["url"], "position": position}}
    return api_request("POST", f"/api/v1/courses/{COURSE_ID}/modules/{module_id}/items", payload), True


def add_module_assignment(module_id, assignment, position):
    if module_item_exists(module_id, "Assignment", content_id=assignment["id"]):
        return None, False
    payload = {"module_item": {"type": "Assignment", "content_id": assignment["id"], "position": position}}
    return api_request("POST", f"/api/v1/courses/{COURSE_ID}/modules/{module_id}/items", payload), True


def canvas_criteria(criteria):
    payload = {}
    for index, item in enumerate(criteria, start=1):
        payload[str(index)] = {
            "description": item["description"],
            "long_description": item["long_description"],
            "points": item["points"],
            "criterion_use_range": False,
            "ratings": {
                str(rating_index): {
                    "description": rating_item["description"],
                    "long_description": rating_item["long_description"],
                    "points": rating_item["points"],
                }
                for rating_index, rating_item in enumerate(item["ratings"], start=1)
            },
        }
    return payload


def rubric_points(rubric_definition):
    return sum(item["points"] for item in rubric_definition["criteria"])


def get_rubric_with_associations(rubric_id):
    return api_request(
        "GET",
        f"/api/v1/courses/{COURSE_ID}/rubrics/{rubric_id}",
        params={"include[]": "assignment_associations"},
    )


def associated_assignment_ids(rubric_id):
    rubric = get_rubric_with_associations(rubric_id)
    associations = rubric.get("associations") or rubric.get("assignment_associations") or []
    return {
        association.get("association_id")
        for association in associations
        if association.get("association_type") == "Assignment"
    }


def create_rubric(rubric_definition, first_assignment):
    payload = {
        "rubric": {
            "title": rubric_definition["title"],
            "free_form_criterion_comments": True,
            "criteria": canvas_criteria(rubric_definition["criteria"]),
        },
        "rubric_association": {
            "association_id": first_assignment["id"],
            "association_type": "Assignment",
            "title": first_assignment["name"],
            "use_for_grading": True,
            "purpose": "grading",
        },
    }
    response = api_request("POST", f"/api/v1/courses/{COURSE_ID}/rubrics", payload)
    return response.get("rubric", response), response.get("rubric_association")


def create_rubric_association(rubric_id, assignment):
    payload = {
        "rubric_association": {
            "rubric_id": rubric_id,
            "association_id": assignment["id"],
            "association_type": "Assignment",
            "title": assignment["name"],
            "use_for_grading": True,
            "purpose": "grading",
        }
    }
    return api_request("POST", f"/api/v1/courses/{COURSE_ID}/rubric_associations", payload)


def rubric_association_id(response):
    if not response:
        return None
    if "rubric_association" in response:
        return response["rubric_association"].get("id")
    return response.get("id")


def create_or_attach_rubrics():
    require_env()
    course = api_request("GET", f"/api/v1/courses/{COURSE_ID}")
    assignments = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")
    rubrics = list_all(f"/api/v1/courses/{COURSE_ID}/rubrics")
    assignments_by_name = {assignment["name"]: assignment for assignment in assignments}
    rubrics_by_title = {rubric["title"]: rubric for rubric in rubrics}
    result = {
        "course": {"id": course["id"], "name": course["name"]},
        "created_rubrics": [],
        "reused_rubrics": [],
        "created_associations": [],
        "reused_associations": [],
        "missing_assignments": [],
    }

    for rubric_definition in RUBRIC_DEFINITIONS:
        missing = [
            name
            for name in rubric_definition["assignment_names"]
            if name not in assignments_by_name
        ]
        result["missing_assignments"].extend(missing)
        if missing:
            continue

        assignments_for_rubric = [
            assignments_by_name[name]
            for name in rubric_definition["assignment_names"]
        ]

        rubric = rubrics_by_title.get(rubric_definition["title"])
        newly_associated_ids = set()
        if rubric:
            result["reused_rubrics"].append(
                {
                    "title": rubric["title"],
                    "id": rubric["id"],
                    "points_possible": rubric.get("points_possible"),
                }
            )
        else:
            rubric, association = create_rubric(rubric_definition, assignments_for_rubric[0])
            rubrics_by_title[rubric["title"]] = rubric
            result["created_rubrics"].append(
                {
                    "title": rubric["title"],
                    "id": rubric["id"],
                    "points_possible": rubric.get("points_possible", rubric_points(rubric_definition)),
                }
            )
            if association:
                result["created_associations"].append(
                    {
                        "rubric": rubric["title"],
                        "assignment": assignments_for_rubric[0]["name"],
                        "association_id": rubric_association_id(association),
                    }
                )
                newly_associated_ids.add(assignments_for_rubric[0]["id"])

        attached_ids = associated_assignment_ids(rubric["id"]) | newly_associated_ids
        for assignment in assignments_for_rubric:
            if assignment["id"] in newly_associated_ids:
                continue
            if assignment["id"] in attached_ids:
                result["reused_associations"].append(
                    {"rubric": rubric["title"], "assignment": assignment["name"]}
                )
                continue
            association = create_rubric_association(rubric["id"], assignment)
            attached_ids.add(assignment["id"])
            result["created_associations"].append(
                {
                    "rubric": rubric["title"],
                    "assignment": assignment["name"],
                    "association_id": rubric_association_id(association),
                }
            )

    print(json.dumps(result, indent=2))


def update_assignment_prompts():
    require_env()
    course = api_request("GET", f"/api/v1/courses/{COURSE_ID}")
    existing = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")
    by_name = {item["name"]: item for item in existing}
    updates = []
    missing = []

    for assignment in ASSIGNMENTS:
        if assignment["name"] not in PROMPT_UPDATE_NAMES:
            continue

        current = by_name.get(assignment["name"])
        if not current:
            missing.append(assignment["name"])
            continue

        response = api_request(
            "PUT",
            f"/api/v1/courses/{COURSE_ID}/assignments/{current['id']}",
            {
                "assignment": {
                    "description": assignment["description"],
                    "published": False,
                }
            },
        )
        updates.append(
            {
                "name": response.get("name"),
                "points_possible": response.get("points_possible"),
                "due_at": response.get("due_at"),
                "published": response.get("published"),
            }
        )

    result = {
        "course": {"id": course["id"], "name": course["name"]},
        "updated": updates,
        "missing": missing,
    }
    print(json.dumps(result, indent=2))


def main():
    require_env()
    course = api_request("GET", f"/api/v1/courses/{COURSE_ID}")
    print(f"Course: {course['name']} ({course['id']})")

    created = {"pages": 0, "modules": 0, "assignments": 0, "module_items": 0}
    reused = {"pages": 0, "modules": 0, "assignments": 0, "module_items": 0}

    landing_page, was_created = create_or_get_page(
        "Welcome to POSC 427: Metropolitan Governance and Policymaking",
        landing_page_body(),
        front_page=False,
    )
    created["pages"] += 1 if was_created else 0
    reused["pages"] += 0 if was_created else 1

    modules = {}
    pages_by_week = {}
    for week in WEEKS:
        module_name = f"Week {week['num']} {DASH} {week['title']}"
        module, was_created = create_or_get_module(module_name, week["num"])
        modules[week["num"]] = module
        created["modules"] += 1 if was_created else 0
        reused["modules"] += 0 if was_created else 1

        page, was_created = create_or_get_page(
            f"Week {week['num']} Overview: {week['title']}",
            overview_body(week),
            front_page=False,
        )
        pages_by_week[week["num"]] = page
        created["pages"] += 1 if was_created else 0
        reused["pages"] += 0 if was_created else 1

    assignments = {}
    for item in ASSIGNMENTS:
        assignment, was_created = create_or_get_assignment(item)
        assignments[item["name"]] = assignment
        created["assignments"] += 1 if was_created else 0
        reused["assignments"] += 0 if was_created else 1

    for week in WEEKS:
        module_id = modules[week["num"]]["id"]
        _, was_created = add_module_page(module_id, pages_by_week[week["num"]], 1)
        created["module_items"] += 1 if was_created else 0
        reused["module_items"] += 0 if was_created else 1

        for offset, assignment_name in enumerate(week["assignments"], start=2):
            _, was_created = add_module_assignment(module_id, assignments[assignment_name], offset)
            created["module_items"] += 1 if was_created else 0
            reused["module_items"] += 0 if was_created else 1

    result = {
        "created": created,
        "reused": reused,
        "course": {"id": course["id"], "name": course["name"]},
        "review": [
            "Weekly Analytical Reflections are represented as 5 Canvas assignments worth 6 points each, matching the syllabus total of 30%.",
            "Week 5 schedule lists only the final assignment, but the grading table says Weekly Analytical Reflections (5); a Week 5 reflection was created to match the grading table.",
            "No rubrics or detailed prompt requirements were specified in the syllabus.",
            "Written work is configured as online upload based on the syllabus statement that all written work is submitted via Canvas.",
            "Canvas requires front pages to be published, so the landing page was created unpublished and not marked as the course front page.",
        ],
    }
    print(json.dumps(result, indent=2))


def verify():
    require_env()
    course = api_request("GET", f"/api/v1/courses/{COURSE_ID}")
    pages = list_all(f"/api/v1/courses/{COURSE_ID}/pages")
    modules = list_all(f"/api/v1/courses/{COURSE_ID}/modules")
    assignments = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")

    module_rows = []
    for module in modules:
        items = list_all(f"/api/v1/courses/{COURSE_ID}/modules/{module['id']}/items")
        module_rows.append(
            {
                "name": module["name"],
                "published": module.get("published"),
                "items": [
                    {
                        "position": item.get("position"),
                        "type": item.get("type"),
                        "title": item.get("title"),
                        "published": item.get("published"),
                    }
                    for item in items
                ],
            }
        )

    result = {
        "course": {"id": course["id"], "name": course["name"]},
        "counts": {
            "pages": len(pages),
            "modules": len(modules),
            "assignments": len(assignments),
        },
        "pages": [
            {
                "title": page.get("title"),
                "published": page.get("published"),
                "front_page": page.get("front_page"),
            }
            for page in sorted(pages, key=lambda item: item.get("title", ""))
        ],
        "assignments": [
            {
                "name": assignment.get("name"),
                "points_possible": assignment.get("points_possible"),
                "due_at": assignment.get("due_at"),
                "published": assignment.get("published"),
                "submission_types": assignment.get("submission_types"),
            }
            for assignment in sorted(assignments, key=lambda item: item.get("due_at") or "")
        ],
        "modules": module_rows,
    }
    print(json.dumps(result, indent=2))


def verify_prompts():
    require_env()
    course = api_request("GET", f"/api/v1/courses/{COURSE_ID}")
    assignments = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")
    rows = []

    for assignment in sorted(assignments, key=lambda item: item.get("name", "")):
        if assignment.get("name") not in PROMPT_UPDATE_NAMES:
            continue
        description = assignment.get("description") or ""
        rows.append(
            {
                "name": assignment.get("name"),
                "points_possible": assignment.get("points_possible"),
                "due_at": assignment.get("due_at"),
                "published": assignment.get("published"),
                "description_length": len(description),
                "has_example": "Example" in description,
                "has_outline": "Outline" in description,
                "has_length_guidance": "Length" in description,
            }
        )

    result = {
        "course": {"id": course["id"], "name": course["name"]},
        "assignments": rows,
    }
    print(json.dumps(result, indent=2))


def verify_rubrics():
    require_env()
    course = api_request("GET", f"/api/v1/courses/{COURSE_ID}")
    assignments = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")
    rubrics = list_all(f"/api/v1/courses/{COURSE_ID}/rubrics")
    assignment_names = {assignment["id"]: assignment["name"] for assignment in assignments}
    rubric_titles = {rubric_definition["title"] for rubric_definition in RUBRIC_DEFINITIONS}
    rows = []

    for rubric in sorted(rubrics, key=lambda item: item.get("title", "")):
        if rubric.get("title") not in rubric_titles:
            continue
        detail = get_rubric_with_associations(rubric["id"])
        associations = detail.get("associations") or detail.get("assignment_associations") or []
        criteria = detail.get("data") or detail.get("criteria") or []
        rows.append(
            {
                "title": detail.get("title"),
                "points_possible": detail.get("points_possible"),
                "criteria_count": len(criteria),
                "assignment_associations": [
                    {
                        "assignment": assignment_names.get(association.get("association_id")),
                        "use_for_grading": association.get("use_for_grading"),
                        "purpose": association.get("purpose"),
                    }
                    for association in associations
                    if association.get("association_type") == "Assignment"
                ],
            }
        )

    result = {
        "course": {"id": course["id"], "name": course["name"]},
        "rubrics": rows,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        if "--create-rubrics" in sys.argv:
            create_or_attach_rubrics()
        elif "--verify-rubrics" in sys.argv:
            verify_rubrics()
        elif "--update-prompts" in sys.argv:
            update_assignment_prompts()
        elif "--verify-prompts" in sys.argv:
            verify_prompts()
        elif "--verify" in sys.argv:
            verify()
        else:
            main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
