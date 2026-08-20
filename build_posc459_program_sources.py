#!/usr/bin/env python3
"""Policy Brief program sources: upload the per-program canon and build one page.

The PapyrusAI Policy Brief Scaffold modules carry these same documents as hidden
background context. Students cannot open a module's attached files, so the
prompts send them to the public locations -- and to this page, which holds the
same PDFs as Canvas files plus the public links. One page, eight sections, one
per program (OASDI, SSI, TANF, UI, Medicaid, Medicare, SNAP, EITC).

Source of the files: the vault, "Program Sources/<program>/*.pdf". Every PDF in
a program folder is uploaded to "course files/program sources/<program>".

Idempotent like the other builders: a file of the same display name and byte
size is left alone; the page is updated in place and keeps its publish state;
module items are not duplicated. New content is UNPUBLISHED (AGENTS.md).

Run:  python3 build_posc459_program_sources.py [--dry-run]
"""

import glob
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_posc459_canvas import (  # noqa: E402
    COURSE_ID, BASE_URL, api, list_all, upload_file, require_env,
)

VAULT = os.path.expanduser(
    "~/obsidian-vaults/snags/9. Teaching/2026-T1 Fall/"
    "POSC 459 - Welfare Politics and Policy/Program Sources")
PAGE_TITLE = "Policy Brief — Program Sources"
FOLDER_ROOT = "course files/program sources"
CRS = "https://www.congress.gov/crs-product/"
CBO = "https://www.cbo.gov/data/baseline-projections-selected-programs"

# start: the two documents each Scaffold prompt names first, as (label, public url,
#        substring that identifies the matching uploaded PDF)
# links: other public locations worth having in one place
PROGRAMS = [
    {
        "key": "OASDI", "anchor": "oasdi",
        "name": "OASDI — Social Security (retirement, survivors, and disability insurance)",
        "agency": "Administered by the Social Security Administration. No state runs any part of it.",
        "start": [
            ("SSA, <em>Understanding the Benefits</em> (publication 05-10024, 2026)",
             "https://www.ssa.gov/pubs/EN-05-10024.pdf", "EN-05-10024"),
            ("CRS R42035, <em>Social Security Primer</em>", CRS + "R42035", "R42035"),
        ],
        "links": [
            ("SSA retirement benefits pages", "https://www.ssa.gov/benefits/retirement/"),
            ("2026 Trustees Report summary", "https://www.ssa.gov/oact/trsum/"),
            ("CRS R49058, Social Security Fairness Act of 2023", CRS + "R49058"),
            ("CRS IF13181, Social Security Fairness Act implementation", CRS + "IF13181"),
            ("CBO baseline projections (Social Security and the trust funds)", CBO),
        ],
    },
    {
        "key": "SSI", "anchor": "ssi",
        "name": "SSI — Supplemental Security Income",
        "agency": "Administered by the Social Security Administration and paid from general revenue; some states add a supplement.",
        "start": [
            ("SSA, <em>Understanding SSI</em> (2026 edition)", "https://www.ssa.gov/ssi/text-understanding-ssi.htm", "Understanding SSI"),
            ("CRS IF10482, <em>Supplemental Security Income (SSI)</em>", CRS + "IF10482", "IF10482"),
        ],
        "links": [
            ("SSA, Supplemental Security Income booklet (publication 05-11000)", "https://www.ssa.gov/pubs/EN-05-11000.pdf"),
            ("SSA SSI home page", "https://www.ssa.gov/ssi/"),
            ("CRS R44948, SSDI and SSI: Eligibility, Benefits, and Financing (2018 — dated)", CRS + "R44948"),
            ("CBO baseline projections (SSI)", CBO),
        ],
    },
    {
        "key": "TANF", "anchor": "tanf",
        "name": "TANF — Temporary Assistance for Needy Families",
        "agency": "Administered federally by the HHS Administration for Children and Families, Office of Family Assistance; run by the states.",
        "start": [
            ("HHS ACF, <em>About TANF</em>", "https://acf.gov/ofa/programs/tanf/about", "About TANF"),
            ("CRS R48413, <em>TANF Block Grant: A Primer</em>", CRS + "R48413", "R48413"),
        ],
        "links": [
            ("CRS RL32760, The TANF Block Grant: Responses to Frequently Asked Questions", CRS + "RL32760"),
            ("CRS R44668, The TANF Block Grant: A Legislative History", CRS + "R44668"),
            ("CRS R48827, TANF work standard", CRS + "R48827"),
            ("CBO baseline projections (TANF)", CBO),
        ],
    },
    {
        "key": "UI", "anchor": "ui",
        "name": "Unemployment Insurance",
        "agency": "A federal-state program: the Department of Labor sets the framework; each state sets eligibility, benefits, duration, and the employer tax.",
        "start": [
            ("DOL, <em>About Unemployment Insurance</em>", "https://oui.doleta.gov/unemploy/aboutui.asp", "About Unemployment Insurance"),
            ("CRS IF10336, <em>Fundamentals of Unemployment Compensation</em>", CRS + "IF10336", "IF10336"),
        ],
        "links": [
            ("CRS RL33362, Unemployment Insurance: Programs and Benefits (2019 — dated but the full treatment)", CRS + "RL33362"),
            ("CRS R48447, Unemployment Insurance: Legislative Issues in the 119th Congress", CRS + "R48447"),
            ("DOL, Comparison of State Unemployment Insurance Laws", "https://oui.doleta.gov/unemploy/statelaws.asp"),
            ("CBO baseline projections (Unemployment Compensation)", CBO),
        ],
    },
    {
        "key": "Medicaid", "anchor": "medicaid",
        "name": "Medicaid",
        "agency": "Administered federally by the Centers for Medicare &amp; Medicaid Services; run by the states under a federal-state match. Every state's program is different.",
        "start": [
            ("Medicaid.gov program overview", "https://www.medicaid.gov/medicaid/index.html", "Medicaid Overview"),
            ("CRS R43357, <em>Medicaid: An Overview</em>", CRS + "R43357", "R43357"),
        ],
        "links": [
            ("CRS R48633, Health Provisions in P.L. 119-21 (the 2025 reconciliation law)", CRS + "R48633"),
            ("CRS R48755, Work Requirements: Comparison of Medicaid and SNAP After P.L. 119-21", CRS + "R48755"),
            ("CBO baseline projections (Medicaid)", CBO),
        ],
    },
    {
        "key": "Medicare", "anchor": "medicare",
        "name": "Medicare",
        "agency": "Administered by the Centers for Medicare &amp; Medicaid Services; private plans deliver a large share of it.",
        "start": [
            ("Medicare.gov, <em>Parts of Medicare</em>", "https://www.medicare.gov/basics/get-started-with-medicare/medicare-basics/parts-of-medicare", "Parts of Medicare"),
            ("CRS R40425, <em>Medicare Primer</em> (2020 — dated; pair it with the Trustees summary)", CRS + "R40425", "R40425"),
        ],
        "links": [
            ("Medicare.gov, What's Medicare?", "https://www.medicare.gov/what-medicare-covers/your-medicare-coverage-choices/whats-medicare"),
            ("2026 Trustees Report summary", "https://www.ssa.gov/oact/trsum/"),
            ("CRS R48633, Health Provisions in P.L. 119-21 (Medicare section)", CRS + "R48633"),
            ("CBO baseline projections (Medicare)", CBO),
        ],
    },
    {
        "key": "SNAP", "anchor": "snap",
        "name": "SNAP — Supplemental Nutrition Assistance Program",
        "agency": "Administered by the USDA Food and Nutrition Service; delivered by state agencies.",
        "start": [
            ("USDA FNS, SNAP eligibility", "https://www.fns.usda.gov/snap/recipient/eligibility", "SNAP Eligibility"),
            ("CRS R42505, <em>SNAP: A Primer on Eligibility and Benefits</em>", CRS + "R42505", "R42505"),
        ],
        "links": [
            ("CRS R48552, SNAP and Related Nutrition Programs in P.L. 119-21", CRS + "R48552"),
            ("CBO baseline projections (SNAP)", CBO),
        ],
    },
    {
        "key": "EITC", "anchor": "eitc",
        "name": "EITC — Earned Income Tax Credit",
        "agency": "Administered by the Internal Revenue Service through the annual tax return; many states add their own credit.",
        "start": [
            ("IRS, <em>Earned Income Tax Credit (EITC)</em>", "https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit-eitc", "Earned Income Tax Credit"),
            ("CRS R43805, <em>The Earned Income Tax Credit (EITC): How It Works and Who Receives It</em>", CRS + "R43805", "R43805"),
        ],
        "links": [
            ("CRS R48611, Tax Provisions in P.L. 119-21", CRS + "R48611"),
        ],
    },
]

INTRO = """
<p>These are the primary sources for the Policy Brief, one set per program. They are the same
documents the <strong>Policy Brief Scaffold</strong> module in PapyrusAI works from — the module
cannot hand them to you or summarize them, and it will tell you to read them yourself, so here
they are. Each set holds the agency's own description of the program, the Congressional Research
Service report that explains it, and the Congressional Budget Office baseline. Every one of them is
public; the outside links go to the same documents at their source.</p>
<p><strong>Start with the two documents marked "start here" for your program.</strong> The module
will ask what you have read before it does anything else. These two are where every program's
analysis begins: what the program is, who it serves, and how it is financed, in the agency's own
words and then in CRS's.</p>
<p>Reminder from the assignment sheet: the brief also needs <strong>at least one source published
before 1996</strong>, which none of these are. Those you find yourself.</p>
"""


def file_link(f):
    href = f"/courses/{COURSE_ID}/files/{f['id']}"
    return (f'<a class="instructure_file_link inline_disabled" title="{html.escape(f["display_name"])}" '
            f'href="{href}?wrap=1" target="_blank" rel="noopener" '
            f'data-api-endpoint="{BASE_URL}/api/v1/courses/{COURSE_ID}/files/{f["id"]}" '
            f'data-api-returntype="File">{html.escape(f["display_name"])}</a>')


def ext_link(label, url):
    return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'


def build_page(uploaded):
    """uploaded: {program key: [file objects]}"""
    parts = [INTRO.strip()]
    parts.append("<p><strong>Jump to:</strong> " + " · ".join(
        f'<a href="#{p["anchor"]}">{p["key"]}</a>' for p in PROGRAMS) + "</p>")
    for p in PROGRAMS:
        files = uploaded.get(p["key"], [])
        parts.append(f'<h2 id="{p["anchor"]}">{p["name"]}</h2>')
        parts.append(f"<p>{p['agency']}</p>")
        parts.append("<p><strong>Start here</strong></p><ul>")
        used = set()
        for label, url, probe in p["start"]:
            match = next((f for f in files if probe in f["display_name"]), None)
            item = f"{label} — {ext_link('at the source', url)}"
            if match:
                item += f" · {file_link(match).replace(html.escape(match['display_name']), 'PDF on Canvas')}"
                used.add(match["id"])
            parts.append(f"<li>{item}</li>")
        parts.append("</ul>")
        rest = [f for f in files if f["id"] not in used]
        if rest:
            parts.append("<p><strong>Also in this set</strong> (PDFs on Canvas)</p><ul>")
            for f in sorted(rest, key=lambda f: f["display_name"]):
                parts.append(f"<li>{file_link(f)}</li>")
            parts.append("</ul>")
        if p["links"]:
            parts.append("<p><strong>At the source</strong></p><ul>")
            for label, url in p["links"]:
                parts.append(f"<li>{ext_link(label, url)}</li>")
            parts.append("</ul>")
    parts.append("<p><em>Files gathered August 20, 2026. CRS reports are the latest version as of that "
                 "date; check congress.gov for updates before you cite one.</em></p>")
    return "\n".join(parts)


def ensure_files(dry):
    existing = {f["display_name"]: f for f in list_all(f"/api/v1/courses/{COURSE_ID}/files")}
    uploaded = {}
    for p in PROGRAMS:
        folder = f"{FOLDER_ROOT}/{p['key']}"
        pdfs = sorted(glob.glob(os.path.join(VAULT, p["key"], "*.pdf")))
        if not pdfs:
            raise SystemExit(f"REFUSING TO BUILD: no PDFs under {VAULT}/{p['key']}")
        print(f"{p['key']}: {len(pdfs)} PDFs -> {folder}")
        for src in pdfs:
            name = os.path.basename(src)
            size = os.path.getsize(src)
            hit = existing.get(name)
            if hit and hit.get("size") == size:
                print(f"  file current  : {name[:70]}")
                uploaded.setdefault(p["key"], []).append(hit)
                continue
            if dry:
                print(f"  WOULD UPLOAD  : {name[:70]} ({size:,} bytes)")
                continue
            up = upload_file(src, folder_path=folder)
            print(f"  file uploaded : {name[:70]} (id {up['id']}, {up['size']:,} bytes)")
            uploaded.setdefault(p["key"], []).append(up)
        print()
    return uploaded


def ensure_page(body, dry):
    pages = {pg["title"]: pg for pg in list_all(f"/api/v1/courses/{COURSE_ID}/pages")}
    prior = pages.get(PAGE_TITLE)
    published = bool(prior["published"]) if prior else False
    payload = {"wiki_page": {"title": PAGE_TITLE, "body": body, "published": published}}
    if dry:
        print(f"WOULD {'UPDATE' if prior else 'CREATE'} page: {PAGE_TITLE} ({len(body):,} chars, "
              f"{'published' if published else 'unpublished'})")
        return prior["url"] if prior else None
    if prior:
        res = api("PUT", f"/api/v1/courses/{COURSE_ID}/pages/{prior['url']}", payload)
        print(f"page updated : {PAGE_TITLE} ({'published' if published else 'unpublished'})")
    else:
        res = api("POST", f"/api/v1/courses/{COURSE_ID}/pages", payload)
        print(f"page created : {PAGE_TITLE} (unpublished)")
    return res["url"]


def ensure_module_items(page_url, dry):
    modules = list_all(f"/api/v1/courses/{COURSE_ID}/modules")
    for prefix in ("Start Here", "Week 5 ("):
        mods = [m for m in modules if m["name"].startswith(prefix)]
        if len(mods) != 1:
            raise SystemExit(f"REFUSING TO BUILD: {len(mods)} modules match {prefix!r}")
        mod = mods[0]
        items = list_all(f"/api/v1/courses/{COURSE_ID}/modules/{mod['id']}/items")
        if any(i.get("title") == PAGE_TITLE for i in items):
            print(f"item present : {PAGE_TITLE} in {mod['name'][:40]}")
            continue
        if dry or not page_url:
            print(f"WOULD LINK   : {PAGE_TITLE} -> {mod['name'][:40]}")
            continue
        api("POST", f"/api/v1/courses/{COURSE_ID}/modules/{mod['id']}/items", {
            "module_item": {"type": "Page", "page_url": page_url, "title": PAGE_TITLE,
                            "published": False}})
        print(f"item linked  : {PAGE_TITLE} -> {mod['name'][:40]}")


def main():
    dry = "--dry-run" in sys.argv
    require_env()
    print(f"POSC 459 program sources -> course {COURSE_ID}{'  [DRY RUN]' if dry else ''}\n")
    uploaded = ensure_files(dry)
    body = build_page(uploaded)
    url = ensure_page(body, dry)
    ensure_module_items(url, dry)
    n = sum(len(v) for v in uploaded.values())
    print(f"\nDone. {n} files across {len(PROGRAMS)} programs; page + 2 module items. New content unpublished.")


if __name__ == "__main__":
    sys.exit(main())
