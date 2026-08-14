#!/usr/bin/env python3
"""Build a Canvas overview page for each POSC 459 week and fill the modules.

Content is parsed from the syllabus schedule in
  POSC 459 Welfare Politics/posc459-syllabus-fa26-papyrus.tex
so the pages cannot drift from the governing document. Re-run after editing
the .tex and the pages follow.

Each week module ends up holding its overview page followed by the
assignments due that week. Idempotent: pages update in place, module items
are only added when missing.
"""
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zoneinfo

COURSE_ID = "3592717"
BASE_URL = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "")
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "POSC 459 Welfare Politics", "posc459-syllabus-fa26-papyrus.tex")

NAVY, ACCENT, INK = "#00244E", "#C25100", "#1F2933"
MUTED, LINE, WASH = "#52606D", "#D8DEE6", "#F4F7FA"

# Which assignments belong to which week. Keyed off what the week is ABOUT,
# not the due date: the Sunday-due discussion papers and the Week 1 film
# response both fall outside their own week's calendar range.
WEEK_ASSIGNMENTS = {
    1: ["Documentary Response 1"],
    2: ["Baseline Writing Diagnostic", "Discussion Paper 1"],
    3: ["Discussion Paper 2"],
    4: ["Documentary Response 2"],
    5: ["Discussion Paper 3", "Policy Brief: Program Selection"],
    6: ["Discussion Paper 4"],
    7: ["Discussion Paper 5", "Research Proposal (Graduate",
        "Policy Brief: Source and Claims Memo"],
    8: ["Reading Journal — Checkpoint 1", "Midterm Exam"],
    9: ["Documentary Response 3"],
    10: ["Policy Brief (Undergraduates)"],
    11: ["Discussion Paper 6"],
    12: ["Discussion Paper 7"],
    13: ["Discussion Paper 8"],
    14: ["Term Paper (Undergraduates)", "Introduction, Outline, and Annotated"],
    15: ["Discussion Paper 9", "Discussion Paper 10", "Reading Journal — Checkpoint 2"],
    16: ["Final Research Paper (Graduate", "Final Exam"],
}

# Monday of each week -> the span shown on the page.
WEEK_SPAN = {
    1: "August 24–28", 2: "August 31 – September 4", 3: "September 7–11",
    4: "September 14–18", 5: "September 21–25", 6: "September 28 – October 2",
    7: "October 5–9", 8: "October 12–16", 9: "October 19–23",
    10: "October 26–30", 11: "November 2–6", 12: "November 9–13",
    13: "November 16–20", 14: "November 30 – December 4", 15: "December 7–11",
    16: "December 14–18",
}

PART = {1: "Part I · The Big Picture", 5: "Part II · Programs of the Welfare State",
        9: "Part III · Case Studies in Reform",
        12: "Part IV · Political Forces Shaping the Welfare State"}


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


def tex2html(s):
    """LaTeX fragment -> Canvas HTML. Links are lifted out first so the
    typographic substitutions cannot corrupt a URL."""
    stash = []

    def keep(html):
        stash.append(html)
        return f"\x00{len(stash) - 1}\x00"

    s = re.sub(r"\\href\{([^}]*)\}\{([^}]*)\}",
               lambda m: keep(f'<a href="{m.group(1)}">{m.group(2)}</a>'), s)
    s = re.sub(r"\\url\{([^}]*)\}",
               lambda m: keep(f'<a href="{m.group(1)}">{m.group(1)}</a>'), s)

    s = s.replace(r"\&", "&amp;").replace(r"\%", "%").replace(r"\$", "$")
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"<strong>\1</strong>", s)
    s = re.sub(r"\\(emph|textit)\{([^{}]*)\}", r"<em>\2</em>", s)
    s = s.replace(r"$\sim$", "~").replace(r"\ldots", "…")
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("``", "\u201c").replace("''", "\u201d")
    s = re.sub(r"\\\\", " ", s)
    # LaTeX spacing commands. Only the punctuation forms: the named ones fall to
    # the generic strip below, and a bare ~ has already been produced by the
    # $\sim$ rule above, so it must survive.
    s = re.sub(r"\\[ ,;:]", " ", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)
    s = s.replace("{", "").replace("}", "").strip()
    s = re.sub(r"\s+", " ", s)

    for i, html in enumerate(stash):
        s = s.replace(f"\x00{i}\x00", html)
    return s


TZ = zoneinfo.ZoneInfo("America/Los_Angeles")


def fmt_due(due_at):
    if not due_at:
        return "no set date"
    d = datetime.datetime.fromisoformat(due_at.replace("Z", "+00:00")).astimezone(TZ)
    stamp = d.strftime("%-I:%M %p").replace("11:59 PM", "11:59 p.m.")
    return f"{d.strftime('%a, %b %-d')}, {stamp}"


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def parse_weeks():
    t = open(TEX, encoding="utf-8").read()
    sched = t[t.index(r"\section*{Calendar of Topics"):]
    parts = re.split(r"\\subsection\*\{(\d+/\d+) -- (Week \d+):\s*(.*)\}\s*\n", sched)
    weeks = []
    for i in range(1, len(parts), 4):
        date, label, topic, body = parts[i], parts[i + 1], parts[i + 2], parts[i + 3]
        body = body.split(r"\noindent\rule")[0]           # stop at a PART divider
        n = int(label.split()[1])

        note = ""
        m = re.match(r"\s*\\emph\{(.*?)\}\s*\n", body, re.S)
        if m:
            note = tex2html(m.group(1))

        sections = []
        for sm in re.finditer(r"\\subsubsection\*\{(.*?)\}(.*?)(?=\\subsubsection\*\{|\Z)",
                              body, re.S):
            head = tex2html(sm.group(1))
            items = [tex2html(x) for x in re.findall(r"\\item\s+(.*?)(?=\n\s*\\item|\n\s*\\end)",
                                                     sm.group(2), re.S)]
            items = [x for x in items if x]
            if items:
                sections.append((head, items))

        weeks.append({"n": n, "date": date, "topic": tex2html(topic),
                      "note": note, "sections": sections,
                      "async": "ASYNC" in topic})
    return weeks


def page_body(w, assignments):
    n = w["n"]
    kind = ("No in-person meetings this week" if w["async"]
            else "Monday &amp; Wednesday, 1:00&ndash;2:15 p.m., GH 305")
    part = PART.get(n) or next((v for k, v in sorted(PART.items(), reverse=True) if n >= k), "")

    out = [
        f'<div style="background:{NAVY};color:#fff;padding:18px 22px;border-radius:8px;">',
        f'  <div style="font-size:0.78em;letter-spacing:0.14em;text-transform:uppercase;'
        f'opacity:0.85;">{part}</div>',
        f'  <div style="font-size:1.45em;font-weight:700;line-height:1.25;margin:5px 0 3px;">'
        f'Week {n}: {w["topic"]}</div>',
        f'  <div style="opacity:0.95;">{WEEK_SPAN.get(n, "")} &middot; {kind}</div>',
        "</div>",
    ]
    if w["note"]:
        out.append(f'<p style="background:#FFF4E5;border-left:5px solid {ACCENT};'
                   f'padding:11px 15px;margin-top:18px;"><strong>Note:</strong> {w["note"]}</p>')

    for head, items in w["sections"]:
        out.append(f'<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:5px;">{head}</h2>')
        out.append('<ul style="line-height:1.7;">')
        out.extend(f"<li>{it}</li>" for it in items)
        out.append("</ul>")

    if assignments:
        out.append(f'<h2 style="border-bottom:3px solid {ACCENT};padding-bottom:5px;">'
                   f'Due this week</h2>')
        out.append('<ul style="line-height:1.9;">')
        for a in assignments:
            # due_at is UTC; a 11:59 p.m. Pacific deadline renders as the NEXT
            # day unless it is converted back to course time first.
            due = fmt_due(a["due_at"])
            out.append(f'<li><a href="/courses/{COURSE_ID}/assignments/{a["id"]}">'
                       f'{a["name"]}</a> <span style="color:{MUTED};">&mdash; due {due}</span></li>')
        out.append("</ul>")
    else:
        out.append(f'<p style="background:{WASH};border-left:5px solid {NAVY};padding:11px 15px;">'
                   f'<strong>Nothing due this week.</strong> Read, and keep the reading journal '
                   f'going.</p>')

    out.append(f'<p style="margin-top:22px;color:{MUTED};font-size:0.92em;">'
               f'The <a href="/courses/{COURSE_ID}/pages/course-syllabus">syllabus</a> is the '
               f'governing document; if this page disagrees with it, the syllabus wins and I want '
               f'to know.</p>')
    return "\n".join(out)


def main():
    require_env()
    print(f"Course: {api('GET', f'/api/v1/courses/{COURSE_ID}')['name']}\n")

    weeks = parse_weeks()
    assignments = list_all(f"/api/v1/courses/{COURSE_ID}/assignments")
    modules = {m["name"]: m for m in list_all(f"/api/v1/courses/{COURSE_ID}/modules")}
    pages = {p["title"]: p for p in list_all(f"/api/v1/courses/{COURSE_ID}/pages")}

    for w in weeks:
        n = w["n"]
        wanted = WEEK_ASSIGNMENTS.get(n, [])
        mine = [a for pref in wanted for a in assignments if a["name"].startswith(pref)]

        # Page titles are plain text: tex2html emits markup on the ASYNC weeks.
        title = f"Week {n:02d} — {strip_tags(w['topic'])}"
        payload = {"wiki_page": {"title": title, "body": page_body(w, mine),
                                 "published": False}}
        if title in pages:
            res = api("PUT", f"/api/v1/courses/{COURSE_ID}/pages/{pages[title]['url']}", payload)
            verb = "updated"
        else:
            res = api("POST", f"/api/v1/courses/{COURSE_ID}/pages", payload)
            verb = "created"

        mod = next((m for name, m in modules.items() if name.startswith(f"Week {n} (")), None)
        if not mod:
            print(f"  !! no module for week {n}")
            continue

        have = {i.get("title") for i in
                list_all(f"/api/v1/courses/{COURSE_ID}/modules/{mod['id']}/items")}
        added = 0
        if title not in have:
            api("POST", f"/api/v1/courses/{COURSE_ID}/modules/{mod['id']}/items",
                {"module_item": {"type": "Page", "page_url": res["url"], "title": title,
                                 "position": 1}})
            added += 1
        for pos, a in enumerate(mine, start=2):
            if a["name"] in have:
                continue
            api("POST", f"/api/v1/courses/{COURSE_ID}/modules/{mod['id']}/items",
                {"module_item": {"type": "Assignment", "content_id": a["id"],
                                 "position": pos, "indent": 1}})
            added += 1
        print(f"  page {verb}: {title[:58]:60s} +{added} module items ({len(mine)} assignments)")

    print(f"\nDone. {len(weeks)} week pages. All unpublished.")


if __name__ == "__main__":
    sys.exit(main())
