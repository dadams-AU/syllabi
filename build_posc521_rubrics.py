#!/usr/bin/env python3
"""Build the POSC 521 (Fall 2026) Canvas rubrics for every assignment except
the two Seminar Performance checkpoints.

Course 3592849. The Seminar Performance rubrics live in
build_posc521_assignments.py and are deliberately not touched here; they are
working instruments and a second script editing them would fork them.

Adapted from the Spring 2026 course (3566245), with the Fall redesign written
in: the page-number locator on every annotation, the three-reading depth cap
on the synthesis paper, the Comparative Matrix and its revision weeks, the
Field Map, and the Recoding America concentration paper. Rubrics are keyed to
assignment names, one rubric per assignment, so re-running updates in place.
Canvas forks a rubric that is shared across assignments when you edit it,
which is where the Spring course's "Rubric (1)", "(2)", "(3)" duplicates came
from; one-per-assignment avoids that entirely.

Deliberate departures from the Spring 2026 rubrics, all of them judgment calls
worth revisiting:

  - Spring's Book Deep-Dive Part B scored a criterion called "Independent
    Analysis (No AI)," whose failing level read "Apparent AI Use or Generic
    Analysis." That is the judgment the Fall syllabus refuses to make: it
    turns off Turnitin's AI indicator and says so in writing, on the grounds
    that the call falls hardest on second-language writers. Scoring a point
    for not sounding like a model contradicts the policy. The point moved to
    "Theory and evidence from the book."

  - Facilitation reweighted. Integration went from 15 to 20 and its Coverage
    level now names the reading-by-reading walkthrough explicitly, because
    the Spring observation notes say that is what most facilitators actually
    did. Adaptability dropped 15 to 10 and Professional Communication 10 to
    5 to pay for it, and a 10-point criterion was added for the post-class
    reflection, which the assignment requires and Spring's rubric never
    scored.

  - Four levels everywhere, not three, on the Seminar Performance ladder:
    Command, Working command, Coverage, Not yet. Spring used bare labels with
    no descriptions, which is a rubric you cannot hand a student.

  - free_form_criterion_comments is sent and Canvas ignores it in this
    payload shape. The Seminar Performance rubrics come back False the same
    way. Left as-is so all 43 rubrics behave alike.

Usage:  python3 build_posc521_rubrics.py [--dry-run]

Requires CANVAS_BASE_URL and CANVAS_TOKEN in the environment.
"""

import json
import os
import sys
import urllib.error
import urllib.request

COURSE_ID = 3592849
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")


# --- Level ladder ----------------------------------------------------------
# The same four levels the Seminar Performance rubric uses, on a scale built
# backward from the syllabus: a paper that gives every reading equal,
# summary-level treatment "will not earn above a B." Coverage across the board
# lands at 80 percent, working command at 90, not yet at 55.
def q(x):
    return round(x * 4) / 4


def scale(p):
    return (p, q(p * 0.90), q(p * 0.80), q(p * 0.55))


def levels(p, command, working, coverage, notyet):
    hi, mid, lo, floor = scale(p)
    return [
        {"description": "Command", "long_description": command, "points": hi},
        {"description": "Working command", "long_description": working, "points": mid},
        {"description": "Coverage", "long_description": coverage, "points": lo},
        {"description": "Not yet", "long_description": notyet, "points": floor},
    ]


def four(name, p, command, working, coverage, notyet):
    return (name, levels(p, command, working, coverage, notyet))


def steps(name, *pairs):
    """Criterion with explicit (points, label, description) levels."""
    return (name, [{"points": pt, "description": lbl, "long_description": desc}
                   for pt, lbl, desc in pairs])


# --- Weekly readings -------------------------------------------------------
ANNOTATED_BIB = [
    steps(
        "Citation and locator",
        (1.0, "Correct and located",
         "Every entry carries a correct APA or Chicago author-date citation and one page "
         "number pointing at the passage where the author makes the central claim you "
         "summarize. The page holds the claim."),
        (0.5, "Cited, not located",
         "Citations are correct, but a locator is missing, points at the reading in general, "
         "or lands somewhere the claim is not made."),
        (0.0, "Not yet",
         "Citations are missing or malformed, or no locators appear at all."),
    ),
    four(
        "Central argument", 2,
        "Each annotation says what the author argues, in about 150 words, and keeps the "
        "author's claim separate from your reading of it. Someone who has not read the piece "
        "would know what position it takes.",
        "The argument is substantially right but blurs into your gloss on it, or one "
        "annotation reports the topic where it should report the claim.",
        "The annotations report what the readings are about. They name subject matter and "
        "reproduce the gist rather than the argument.",
        "Annotations are well short of length, or they attribute positions the readings do "
        "not take.",
    ),
    steps(
        "Relevance and implications",
        (1.0, "Specific to the reading",
         "You say what the reading does for this week's question and what follows from it for "
         "public administration. The connection could not be moved to another reading."),
        (0.5, "Generic",
         "Relevance is asserted in a sentence that would fit any reading in the course."),
        (0.0, "Not yet", "No relevance statement."),
    ),
    steps(
        "Feedback Appendix",
        (1.0, "Complete",
         "The Track A protocol worked through on your own entry or a classmate's, or the full "
         "unedited ChatGPT Edu transcript under the verbatim prompt. Either way it is here and "
         "it is about this week's entries."),
        (0.5, "Partial",
         "The appendix is present and thin: a protocol answered in a word or two, or a "
         "transcript that has been trimmed, summarized, or run under a prompt you altered."),
        (0.0, "Not yet",
         "No appendix. The submission is incomplete. There are no optional weeks on either "
         "track."),
    ),
]

COMPARATIVE_MATRIX = [
    four(
        "Rows derived from the text", 5,
        "The rows name dimensions on which the four positions actually disagree: who the "
        "citizen is, what the public interest rests on, what accountability answers to, what "
        "model of rationality is assumed. You derived them from Chapters 1 through 6 rather "
        "than waiting for a list.",
        "The rows are genuine dimensions, and one or two are topics rather than points of "
        "disagreement, so the cells beside them do not diverge.",
        "The rows are chapter headings or subject areas. The matrix organizes the book rather "
        "than the argument.",
        "Rows are missing, or there are too few of them to hold six chapters.",
    ),
    four(
        "Cell accuracy", 6,
        "Each cell reports what Denhardt and Denhardt say that position holds, and the four "
        "stay distinct. New Public Administration and New Public Service do not collapse into "
        "one another.",
        "Most cells are accurate. One row runs the positions together, or one column comes out "
        "thinner than the other three.",
        "Cells are filled and broadly plausible, and the distinctions are soft enough that "
        "swapping two of them would not be obvious.",
        "Cells are empty, or they report the position the row asks about incorrectly.",
    ),
    four(
        "Your own words", 3,
        "One or two sentences per cell, written by you. No quotations and no keyword fragments.",
        "A few cells fall back on the book's phrasing or shrink to a keyword.",
        "The matrix is largely quotation and keyword. It records vocabulary rather than "
        "positions.",
        "Cells are quotation with no paraphrase, or run long enough to turn the matrix into "
        "prose.",
    ),
    four(
        "The 300-word statement", 5,
        "You name the single row where the four positions are least reconcilable and argue why "
        "that row is the one that matters. The argument would survive someone naming a "
        "different row.",
        "You name the row and defend it, and the defense rests on the row being important "
        "rather than on the positions being irreconcilable there.",
        "You describe the row and how the four positions differ, without saying why the "
        "difference cannot be split.",
        "The statement is missing, or it names several rows rather than one.",
    ),
    steps(
        "Usable as a scaffold",
        (1.0, "A working document",
         "Legible and complete enough to revise in Weeks 5, 6, 7, and 10."),
        (0.5, "Usable with gaps",
         "You will have to reconstruct parts of it before you can revise it."),
        (0.0, "Not yet", "Not a document you can work from."),
    ),
]

ROUGH_DRAFT = [
    four(
        "Patterns and contradictions", 4,
        "You find where the readings converge and where they cannot both be right, and you say "
        "what the disagreement is actually about.",
        "You identify real connections and one contradiction, and you treat the contradiction "
        "as a difference in emphasis rather than a conflict.",
        "You move through the readings in order, a section each. The connections are announced "
        "rather than shown.",
        "The draft summarizes without relating the readings to one another.",
    ),
    four(
        "Implications for theory and practice", 3,
        "You say what follows for how public administration gets theorized and what an "
        "administrator would do differently on Tuesday.",
        "Implications are drawn for one side, theory or practice, and left implicit for the "
        "other.",
        "Implications appear as a closing gesture toward relevance.",
        "No implications are drawn.",
    ),
    four(
        "Ready for the studio", 3,
        "Three pages of your own thinking with a position visible in it, so your partner has "
        "something to push on Monday.",
        "Complete and close to length, with the position stated late enough that a reader has "
        "to hunt for it.",
        "Short of length, or written as notes toward a paper rather than as a draft.",
        "Too thin to work with in the studio.",
    ),
]

FINAL_SYNTHESIS = [
    four(
        "Depth and selection", 6,
        "Your opening paragraph names the readings you chose to work with, no more than three, "
        "and says why they carry the most weight for the question you are pursuing. The rest of "
        "the week is handled as context. The paper stays inside four pages.",
        "You name the readings and go deep on them, and the reason for choosing them is "
        "asserted rather than argued, or a fourth reading gets full treatment.",
        "Every reading gets equal, summary-level attention. This is the paper the reading cap "
        "and the page cap exist to prevent, and it does not score above this level however well "
        "written it is.",
        "No selection is stated, or the paper runs well past four pages while covering "
        "everything.",
    ),
    four(
        "Integration and analysis", 5,
        "The chosen readings are made to work on one another. You build an argument that none "
        "of them states on its own.",
        "The readings are genuinely related and the analysis is yours, and the argument stays "
        "close to what one author already says.",
        "The readings appear in sequence with transitions between them.",
        "Summary with citations attached.",
    ),
    four(
        "Page locators", 3,
        "Every sentence that attributes a position to an author carries a page number, and the "
        "page holds the claim.",
        "Locators run throughout, with one or two attributions left unlocated.",
        "Locators appear for quotations only. Paraphrased attributions float.",
        "Attributions carry no page numbers, or the numbers do not correspond to the claims. A "
        "locator that looks right and is wrong is worse than none.",
    ),
    four(
        "Theory to practice", 2,
        "You take the argument into a setting where an administrator has to act, and say what "
        "changes there.",
        "The practice connection is specific and arrives at the end, after the analysis has "
        "closed.",
        "Practice is mentioned in general terms.",
        "No connection to practice.",
    ),
    four(
        "Revision from discussion and the studio", 2,
        "The paper has changed since Monday in ways traceable to the discussion or to your "
        "partner's two suggestions, and the change is in the argument rather than the wording.",
        "Real revision, working mostly at the level of organization and evidence rather than "
        "claim.",
        "The draft has been tidied.",
        "The rough draft, resubmitted.",
    ),
    steps(
        "Feedback Appendix and Next-Week Plan",
        (2.0, "Complete",
         "The completed Track A protocol or the full unedited ChatGPT Edu transcript under the "
         "verbatim prompt, plus five to seven bullets naming what you will do differently in "
         "next week's synthesis."),
        (1.0, "Partial",
         "One of the two is here and the other is missing or thin. A plan that resolves to try "
         "harder counts as thin."),
        (0.0, "Not yet",
         "Neither is here, or the transcript has been edited, summarized, or produced under an "
         "altered prompt."),
    ),
]

REFLECTION_STANDARD = [
    four(
        "Evolution of thinking", 5,
        "You name something you thought on Monday and no longer think, and what moved you. The "
        "change is about the readings rather than about your study habits.",
        "A real shift, described at one remove: your understanding deepened, without saying "
        "from what to what.",
        "You report what happened during the week and what the readings covered.",
        "Summary of the readings, or a reflection that could have been written before the week "
        "began.",
    ),
    four(
        "Grounding in the week's work", 3,
        "You point at the moment: a passage, a claim a classmate made in discussion, a question "
        "from the peer review studio.",
        "Grounded, in the week generally rather than in a specific exchange.",
        "Grounded in the topic rather than in the week's actual work.",
        "Nothing ties the reflection to this week.",
    ),
    steps(
        "Next week, specifically",
        (1.0, "Checkable",
         "You name a move you will make, specific enough that I could check whether you made "
         "it."),
        (0.5, "General",
         "A plan aimed at the right problem, stated too generally to check, or a resolution to "
         "read more carefully."),
        (0.0, "Not yet", "No forward statement."),
    ),
    steps(
        "Length",
        (1.0, "250 to 300 words", "Within range."),
        (0.5, "Near range", "Somewhat under or over."),
        (0.0, "Not yet", "Far outside the range."),
    ),
]

REFLECTION_MATRIX = [
    four(
        "Evolution of thinking", 3,
        "You name something you thought on Monday and no longer think, and what moved you. The "
        "change is about the readings rather than about your study habits.",
        "A real shift, described at one remove: your understanding deepened, without saying "
        "from what to what.",
        "You report what happened during the week and what the readings covered.",
        "Summary of the readings, or a reflection that could have been written before the week "
        "began.",
    ),
    four(
        "Comparative Matrix revision", 3,
        "You added or revised at least one row and said in one sentence what forced the change. "
        "The sentence names the reading or the exchange that did it.",
        "A row changed, and the sentence explains the change in terms of the framework rather "
        "than in terms of what you read this week.",
        "A row changed cosmetically, or you report that the matrix still holds without having "
        "tested it against this week's chapter.",
        "No revision, and no account of why none was needed.",
    ),
    four(
        "Grounding in the week's work", 2,
        "You point at the moment: a passage, a claim a classmate made in discussion, a question "
        "from the peer review studio.",
        "Grounded, in the week generally rather than in a specific exchange.",
        "Grounded in the topic rather than in the week's actual work.",
        "Nothing ties the reflection to this week.",
    ),
    steps(
        "Next week, specifically",
        (1.0, "Checkable",
         "You name a move you will make, specific enough that I could check whether you made "
         "it."),
        (0.5, "General",
         "A plan aimed at the right problem, stated too generally to check, or a resolution to "
         "read more carefully."),
        (0.0, "Not yet", "No forward statement."),
    ),
    steps(
        "Length",
        (1.0, "250 to 300 words", "Within range."),
        (0.5, "Near range", "Somewhat under or over."),
        (0.0, "Not yet", "Far outside the range."),
    ),
]

DEEP_DIVE_A = [
    four(
        "Concept identification", 3,
        "Three concepts from the book, each stated the way the book states it, explained fully "
        "enough that the application later has something to stand on.",
        "Three concepts, one of them named rather than explained.",
        "Two concepts, or three reduced to their labels.",
        "The concepts are not the book's, or fewer than two appear.",
    ),
    four(
        "Application to a setting", 4,
        "A setting concrete enough to have staffing, caseloads, and rules in it, and all three "
        "concepts do work there.",
        "The setting is concrete and two of the three concepts do real work. The third is "
        "asserted to apply.",
        "The setting is a category rather than a place, and the concepts are matched to it by "
        "label.",
        "No setting, or the concepts are restated without being applied.",
    ),
    four(
        "The dilemma", 2,
        "One dilemma, stated so that both horns cost something and a public servant has to "
        "choose.",
        "A genuine dilemma, with one side clearly preferable as you have set it up.",
        "A difficulty rather than a dilemma. Nothing is given up either way.",
        "No dilemma named.",
    ),
    steps(
        "Length and organization",
        (1.0, "Meets the standard", "About two pages, organized so a reader can follow it."),
        (0.5, "Short or loose", "Under length, or organized so the reader assembles it."),
        (0.0, "Not yet", "Well under length or difficult to follow."),
    ),
]

DEEP_DIVE_B = [
    four(
        "Response to the dilemma", 8,
        "You propose a response, say what it gives up, and defend the choice with course theory "
        "and evidence from the book. The response answers the dilemma you set in Part A.",
        "A defended response that treats the horn you rejected as a cost to be noted rather "
        "than argued against.",
        "A recommendation that both horns would allow, so nothing has actually been decided.",
        "No response, or a response to a different problem than the one in Part A.",
    ),
    four(
        "Equity implications", 4,
        "A paragraph naming who bears the burden your response creates and who is left outside "
        "its benefit, in this setting rather than in general.",
        "The paragraph identifies a burdened group and stops short of who is excluded.",
        "Equity is treated as a value your response honors.",
        "No equity paragraph.",
    ),
    four(
        "Implementation constraints", 4,
        "A paragraph on what would actually stop this: the budget, the statute, the contract "
        "terms, the staffing, the information system nobody can change. Constraints specific to "
        "the setting.",
        "Real constraints named, one of them generic.",
        "Constraints are acknowledged as things that exist.",
        "No constraints paragraph.",
    ),
    four(
        "Theory and evidence from the book", 3,
        "The book is used as evidence rather than as authority. Specific passages carry weight "
        "in the argument.",
        "The book is cited at the right moments and quoted where it should have been worked "
        "into the argument.",
        "The book is invoked by name. The argument would stand unchanged without it.",
        "The book does no work here.",
    ),
    steps(
        "Length and organization",
        (1.0, "Meets the standard", "About two pages, organized so a reader can follow it."),
        (0.5, "Short or loose", "Under length, or organized so the reader assembles it."),
        (0.0, "Not yet", "Well under length or difficult to follow."),
    ),
]

DEEP_DIVE_REFLECTION = [
    four(
        "Perspective shift", 6,
        "You name a view you held about frontline public service, or about how ordinary "
        "professional competence produces harm and hides it from the people producing it, and "
        "you say what the book did to that view.",
        "A real shift, reported without saying what you thought before.",
        "You report that the book was illuminating and describe what it argues.",
        "Summary of the book.",
    ),
    four(
        "Grounding in the book", 3,
        "Specific scenes, cases, or arguments from the book, located.",
        "Specific content, referred to in general terms.",
        "The book's thesis, restated.",
        "Nothing specific from the book.",
    ),
    steps(
        "Length",
        (1.0, "250 to 300 words", "Within range."),
        (0.5, "Near range", "Somewhat under or over."),
        (0.0, "Not yet", "Far outside the range."),
    ),
]

FACILITATION = [
    four(
        "Preparation and collaboration", 20,
        "You and your partner traded annotated bibliographies before class, found where you "
        "disagreed, and built the segment around that. Six to eight questions prepared, and it "
        "shows that you wrote them together.",
        "Prepared jointly and prepared well, with the questions divided by reading rather than "
        "built around a shared line of inquiry.",
        "Both partners prepared and then split the readings between them. The segment runs as "
        "two presentations in sequence.",
        "Preparation was one partner's, or the questions arrived in the room.",
    ),
    four(
        "Critical inquiry", 20,
        "Your questions push past what the reading says to whether it holds, what it cannot "
        "account for, and what an administrator would do with it. Students had to think in "
        "front of each other to answer.",
        "Strong questions, with two or three that can be answered by pointing at a page.",
        "Comprehension questions that check whether people read.",
        "Questions were not prepared, or were abandoned once the discussion started.",
    ),
    four(
        "Integration across readings", 20,
        "You put the readings in contact with one another and with the course, and the "
        "connections were argued rather than announced. Nobody walked through the readings one "
        "at a time.",
        "Connections were made, mostly at the end, after the readings had been handled "
        "separately.",
        "The segment moved through the readings in order, summarizing each. This is the "
        "standard failure in this assignment and it is scored as one.",
        "No connection across the readings.",
    ),
    four(
        "Discussion leadership", 15,
        "Forty-five minutes held to shape. Quiet students brought in, talkative ones managed, "
        "and neither of you held the floor for long. The opening synthesis ran about ten "
        "minutes and the practical segment got its ten.",
        "Well run, with one section eating another's time, or one or two students never brought "
        "in.",
        "The time was filled and the discussion stayed in the room, and you carried it.",
        "The segment ran out of material or ran over, and the class waited.",
    ),
    four(
        "Adaptability", 10,
        "When the discussion went somewhere you had not planned and it was worth going, you "
        "followed it and brought it back.",
        "You adapted once, and returned to the script where the detour was the more interesting "
        "thing.",
        "You ran the plan through what was actually happening in the room.",
        "Unplanned turns stopped the segment.",
    ),
    four(
        "Professional communication", 5,
        "Scholarly and generous. Disagreement was welcomed and half-formed ideas were treated "
        "as worth having. Facilitation was visibly shared.",
        "Respectful and clear, with the share of facilitation uneven.",
        "Correct and flat. Nobody in the room took a risk.",
        "A student was handled dismissively, or one partner was absent from the facilitation.",
    ),
    four(
        "Post-class reflection", 10,
        "Filed within 24 hours, about 250 words, naming what worked, what your partnership did "
        "to the segment, and something that emerged in the room you had not anticipated.",
        "On time and honest, with the partnership handled generically.",
        "A report of what happened in the segment.",
        "Late, missing, or written as self-assessment with nothing behind it.",
    ),
]

# Credit / no credit. Attached for feedback only; the grade is pass or fail.
FIELD_MAP = [
    steps(
        "Theories placed in relation",
        (1.0, "Present",
         "The map shows where the semester's theories agree, where they collide, and which "
         "questions force a choice between them."),
        (0.0, "Not yet",
         "The theories appear beside one another without relation, or the map inventories the "
         "course."),
    ),
    steps(
        "Where the Denhardt frame breaks",
        (1.0, "Present",
         "The map marks the readings that will not sit in any column and says what their "
         "refusal tells you about the frame. Simon, Lipsky, and the administrative evil "
         "argument are the obvious candidates."),
        (0.0, "Not yet",
         "No breaks are marked. A map with no breaks in it is a map of the textbook rather than "
         "of the field."),
    ),
    steps(
        "Three arguments, with objections",
        (1.0, "Present",
         "Three arguments you would stake a comprehensive exam answer on, each with the "
         "strongest objection to it."),
        (0.0, "Not yet",
         "Fewer than three, or arguments named without the objection that would be put to "
         "them."),
    ),
    steps(
        "One page, and not prose",
        (1.0, "Present",
         "One page, in whatever structure genuinely holds your thinking: a map, a matrix, a "
         "decision tree, a photographed mess."),
        (0.0, "Not yet", "Prose paragraphs, or longer than a page."),
    ),
    steps(
        "Built from your own matrix",
        (1.0, "Present",
         "The map carries ten weeks of revision in it and is unmistakably yours."),
        (0.0, "Not yet",
         "The map was assembled from the syllabus rather than from the document you have been "
         "maintaining since Labor Day."),
    ),
]

# Pass / fail. Feedback only; the exam grade is not computed from this.
COMP_EXAM = [
    steps(
        "Command of the arguments",
        (1.0, "Pass",
         "The positions you attribute are the positions the authors take, and you keep their "
         "claims separate from your reading of them."),
        (0.0, "Not yet",
         "Positions are attributed that the readings do not hold, or the authors' claims and "
         "your gloss on them are not distinguishable."),
    ),
    steps(
        "Selection and justification",
        (1.0, "Pass",
         "Inside 1,620 words you chose what genuinely bears on the question, said why, and said "
         "what you set aside and on what grounds."),
        (0.0, "Not yet",
         "The answer surveys the field. Everything is touched and nothing is held."),
    ),
    steps(
        "Adjudication",
        (1.0, "Pass",
         "You take a position where the theories collide rather than reporting that they "
         "collide, and you defend it."),
        (0.0, "Not yet",
         "Tensions are described and left open, or a position is stated without a defense."),
    ),
    steps(
        "Evidence and use of the literature",
        (1.0, "Pass",
         "The readings do work in the answer. Claims are attributed and located."),
        (0.0, "Not yet",
         "The literature is named rather than used, or the answer runs on assertion."),
    ),
]

TOPIC_SELECTION = [
    four(
        "Research question", 6,
        "A question narrow enough to answer in eight to ten pages and open enough that the "
        "answer is not obvious from the way you ask it.",
        "A real question, scoped wider than the page count will support.",
        "A topic announced in the grammar of a question.",
        "No question, or a question already answered by how it is put.",
    ),
    four(
        "Concepts from Recoding America", 5,
        "You name the specific concepts you will use, say where in the book they come from, and "
        "say what work each will do in the paper.",
        "Concepts named and located, with their role in the paper left to be worked out.",
        "The book is named as the central text without concepts specified.",
        "No engagement with the book.",
    ),
    four(
        "The tradeoff, and your provisional position", 7,
        "You name the tradeoff you expect to confront, state where you provisionally come down, "
        "and say what that position gives up. A provisional position is a claim you are willing "
        "to be argued out of rather than the absence of one.",
        "The tradeoff is named and the position stated, without saying what the position costs.",
        "A tension is described and both sides are given their due. No position is taken.",
        "No tradeoff named, or a preference for government working better.",
    ),
    four(
        "Scope, format, and concentration fit", 2,
        "One page. The topic sits inside your concentration and inside the options on your "
        "assignment sheet.",
        "Within scope, running long.",
        "Loosely tied to the concentration.",
        "Outside the concentration, or well past one page.",
    ),
]

LIT_REVIEW = [
    four(
        "Synthesis rather than annotation", 12,
        "The sources are organized by the questions they answer and by the disagreements among "
        "them. A reader learns where the field stands and where it is unsettled.",
        "Organized by theme, with the disagreements reported rather than staged.",
        "Source by source, in sequence. A bibliography in paragraphs.",
        "Sources are listed with little account of what they argue.",
    ),
    four(
        "Pahlka against your concentration's scholarship", 12,
        "You connect the policy-delivery divide, encoded discretion, and compliance over "
        "outcomes to established work in your concentration, and you say where the connections "
        "hold and where they do not.",
        "The connection is made for one or two of Pahlka's claims and asserted for the rest.",
        "Pahlka is summarized in one section and your concentration's literature in another.",
        "One body of work or the other is absent.",
    ),
    four(
        "Sources: range and evaluation", 8,
        "Scholarly sources from beyond the course, chosen because they bear on your question, "
        "and read critically rather than cited approvingly.",
        "Good range, with the evaluation left to the reader.",
        "Enough sources, drawn mostly from the course.",
        "Thin or off-topic sourcing.",
    ),
    four(
        "Ready for the 12/7 workshop", 4,
        "Complete enough that a classmate can attack your tradeoff position from it, and your "
        "position is visible in the draft.",
        "Substantial, with the position still implicit.",
        "A partial draft. The workshop will be about what is missing.",
        "Too little here to work with.",
    ),
    four(
        "Citation and format", 4,
        "APA or Chicago author-date, consistent, with page locators on attributed claims.",
        "Consistent style, with occasional lapses.",
        "Citations present, style mixed.",
        "Citations missing or unusable.",
    ),
]

# Weights fixed by the syllabus: Depth 30, Sources 20, Clarity 20, Writing 15,
# Completeness 15. Depth carries the tradeoff, the administrative evil line, and
# the equity assessment, because that is how the syllabus scopes it.
FINAL_PAPER = [
    four(
        "Depth of Analysis", 30,
        "You adjudicate your tradeoff and say plainly what your position costs and who pays. "
        "You take a position on whether what Pahlka describes is masked administrative evil or "
        "administrative failure, and you defend where you drew the line. The equity assessment "
        "names who bears the burden and who is excluded from the benefit, out of the Week 10 "
        "readings. Pahlka, Balfour and Adams and Nickels, Lipsky, and the hollow state are made "
        "to work on one another rather than cited in turn.",
        "The tradeoff is adjudicated and defended, with the cost named and the payer left "
        "general, or the line between evil and failure is drawn and thinly defended.",
        "The paper explains the tradeoff well and stops short of taking a position on it, or it "
        "restates Pahlka's critique with the harder question deferred. Government should be "
        "more user-centered is where this level ends up.",
        "No position on the tradeoff, no equity assessment, and the administrative evil "
        "question is not engaged.",
    ),
    four(
        "Use of Sources", 20,
        "Recoding America and your concentration's literature are used as evidence, evaluated "
        "rather than deferred to, and located by page wherever they carry a claim.",
        "Strong sourcing, with the evaluation uneven.",
        "Sources are relevant and cited approvingly.",
        "Sources are thin, off-topic, or decorative.",
    ),
    four(
        "Clarity and Organization", 20,
        "The structure of the argument is visible from the headings, each section does one job, "
        "and the reader is never guessing what the paper is arguing.",
        "Clear throughout, with one section that does not earn its place.",
        "Organized by topic. The reader assembles the argument.",
        "The reader cannot follow the line of argument.",
    ),
    four(
        "Writing Quality", 15,
        "Sentence-level control. Twelve-point Times New Roman, one-inch margins, double-spaced, "
        "clean.",
        "Professional prose with scattered errors.",
        "Readable, with errors frequent enough to slow a reader.",
        "Errors interfere with the argument.",
    ),
    four(
        "Completeness and Accuracy", 15,
        "Eight to ten pages excluding references, APA or Chicago author-date, the equity "
        "assessment present as its own section, the earlier stages submitted on time, and every "
        "attributed claim carrying a locator that holds.",
        "Within requirements, with one lapse in length, format, or timeliness.",
        "Most requirements met. One required element is missing, or one deadline was missed.",
        "Several requirements unmet.",
    ),
]


# --- Assignment -> rubric map ----------------------------------------------
# (assignment name, criteria, use_for_grading)
def bib(week, topic):
    return (f"Week {week} - {topic} - Annotated Bibliography", ANNOTATED_BIB, True)


SPECS = [
    ("Week 2 - Annotated Bibliography (Denhardt Ch. 1-6)", ANNOTATED_BIB, True),
    ("Week 2 - Comparative Matrix, Version 1", COMPARATIVE_MATRIX, True),
    ("Week 2 - Reflection", REFLECTION_STANDARD, True),
    ("Week 3 - Annotated Bibliography (Classical Foundations)", ANNOTATED_BIB, True),

    ("Week 4 - Classical Foundations - Rough Draft Synthesis Paper", ROUGH_DRAFT, True),
    ("Week 4 - Classical Foundations - Final Synthesis Paper", FINAL_SYNTHESIS, True),
    ("Week 4 - Classical Foundations - Reflection", REFLECTION_STANDARD, True),

    bib(5, "Ethics and Values"),
    ("Week 5 - Ethics and Values - Rough Draft Synthesis Paper", ROUGH_DRAFT, True),
    ("Week 5 - Ethics and Values - Final Synthesis Paper", FINAL_SYNTHESIS, True),
    ("Week 5 - Ethics and Values - Reflection", REFLECTION_MATRIX, True),

    bib(6, "Leadership and Motivation"),
    ("Week 6 - Leadership and Motivation - Rough Draft Synthesis Paper", ROUGH_DRAFT, True),
    ("Week 6 - Leadership and Motivation - Final Synthesis Paper", FINAL_SYNTHESIS, True),
    ("Week 6 - Leadership and Motivation - Reflection", REFLECTION_MATRIX, True),

    bib(7, "Performance Management"),
    ("Week 7 - Performance Management - Rough Draft Synthesis Paper", ROUGH_DRAFT, True),
    ("Week 7 - Performance Management - Final Synthesis Paper", FINAL_SYNTHESIS, True),
    ("Week 7 - Performance Management - Reflection", REFLECTION_MATRIX, True),

    bib(8, "Street-Level Bureaucracy"),
    ("Week 8 - Street-Level Bureaucracy - Part A: Concept Application Analysis",
     DEEP_DIVE_A, True),
    ("Week 8 - Street-Level Bureaucracy - Part B: Decision and Practice Analysis",
     DEEP_DIVE_B, True),
    ("Week 8 - Street-Level Bureaucracy - Reflection", DEEP_DIVE_REFLECTION, True),

    bib(9, "Privatization and Contracting"),
    ("Week 9 - Privatization and Contracting - Rough Draft Synthesis Paper", ROUGH_DRAFT, True),
    ("Week 9 - Privatization and Contracting - Final Synthesis Paper", FINAL_SYNTHESIS, True),
    ("Week 9 - Privatization and Contracting - Reflection", REFLECTION_STANDARD, True),

    bib(10, "Social Equity"),
    ("Week 10 - Social Equity - Rough Draft Synthesis Paper", ROUGH_DRAFT, True),
    ("Week 10 - Social Equity - Final Synthesis Paper", FINAL_SYNTHESIS, True),
    ("Week 10 - Social Equity - Reflection", REFLECTION_MATRIX, True),

    bib(11, "Unmasking Administrative Evil"),
    ("Week 11 - Unmasking Administrative Evil - Part A: Concept Application Analysis",
     DEEP_DIVE_A, True),
    ("Week 11 - Unmasking Administrative Evil - Part B: Decision and Practice Analysis",
     DEEP_DIVE_B, True),
    ("Week 11 - Unmasking Administrative Evil - Reflection", DEEP_DIVE_REFLECTION, True),

    ("Reading Discussion Facilitation and Post-Class Reflection", FACILITATION, True),
    ("Field Map (Week 12)", FIELD_MAP, False),
    ("MPA Comprehensive General Area Essay Exam", COMP_EXAM, False),
    ("Concentration Paper - Topic Selection", TOPIC_SELECTION, True),
    ("Concentration Paper - Literature Review Draft", LIT_REVIEW, True),
    ("Concentration Paper - Final Paper", FINAL_PAPER, True),
]


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


def criteria_payload(criteria):
    out = {}
    for i, (desc, ratings) in enumerate(criteria):
        out[str(i)] = {
            "description": desc,
            "points": max(r["points"] for r in ratings),
            "criterion_use_range": False,
            "ratings": {str(j): r for j, r in enumerate(ratings)},
        }
    return out


def total(criteria):
    return sum(max(r["points"] for r in ratings) for _, ratings in criteria)


def sync():
    assignments = {a["name"]: a for a in paged(f"/courses/{COURSE_ID}/assignments")}
    existing = {r["title"]: r for r in paged(f"/courses/{COURSE_ID}/rubrics")}
    created = updated = 0
    for name, criteria, for_grading in SPECS:
        a = assignments.get(name)
        if not a:
            raise SystemExit(f"No assignment named {name!r} in course {COURSE_ID}. "
                             "Run build_posc521_assignments.py first.")
        payload = {
            "rubric": {
                "title": name,
                "free_form_criterion_comments": True,
                "criteria": criteria_payload(criteria),
            },
            "rubric_association": {
                "association_id": a["id"],
                "association_type": "Assignment",
                "use_for_grading": for_grading,
                "hide_score_total": not for_grading,
                "purpose": "grading",
            },
        }
        if name in existing:
            api("PUT", f"/courses/{COURSE_ID}/rubrics/{existing[name]['id']}", payload)
            updated += 1
        else:
            api("POST", f"/courses/{COURSE_ID}/rubrics", payload)
            created += 1
        print(f"  {name}: {len(criteria)} criteria, {total(criteria)} pts"
              f"{'' if for_grading else '  [feedback only]'}")
    print(f"\nrubrics: {created} created, {updated} updated")


def main():
    if "--dry-run" in sys.argv:
        print(f"{len(SPECS)} rubrics\n")
        for name, criteria, for_grading in SPECS:
            flag = "" if for_grading else "  [feedback only, pass/fail assignment]"
            print(f"{name}{flag}")
            for desc, ratings in criteria:
                pts = "/".join(str(r["points"]) for r in ratings)
                print(f"    {desc}: {max(r['points'] for r in ratings)} pts  ({pts})")
            print(f"    TOTAL {total(criteria)}\n")
        return
    require_env()
    print(f"Syncing {len(SPECS)} rubrics to course {COURSE_ID}...")
    sync()


if __name__ == "__main__":
    main()
