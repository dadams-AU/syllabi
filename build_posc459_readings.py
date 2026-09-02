#!/usr/bin/env python3
"""Upload the POSC 459 readings that must be Canvas files and link them into weeks.

Two groups, same mechanics.

READINGS: library-licensed journal articles with no durable link -- CSUF has no
clean permalink route for them. All five come out of Zotero collection "459";
the Zotero item key is recorded so the source is traceable.

FREE: public documents that need no permission but still should not be assigned
as bare links, because the publisher revises in place. Sourced from the vault
under "Readings/Week NN/". The CBPP entry is the reason this group exists: that
page is revised at its live URL, its own "Download PDF" still serves the 2016
original, and a student reading in November would otherwise see numbers the
class never discussed.

Idempotent, like the other builders here: a file already in the course with
the same display name and byte size is left alone, and a module item pointing
at the same file is not duplicated. Safe to re-run after replacing a PDF.

Everything is created UNPUBLISHED, matching build_posc459_canvas.py. The
course itself is still unpublished pending the per-track Assign-to work.

Run:  python3 build_posc459_readings.py [--dry-run]
Needs CANVAS_BASE_URL and CANVAS_TOKEN in the environment (~/.zsh_secrets).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_posc459_canvas import (  # noqa: E402
    COURSE_ID, api, list_all, upload_file, require_env,
)

ZOTERO = os.path.expanduser("~/Zotero/storage")
VAULT = os.path.expanduser(
    "~/obsidian-vaults/snags/9. Teaching/2026-T1 Fall/"
    "POSC 459 - Welfare Politics and Policy/Readings")

# week_prefix matches the live Canvas module by prefix rather than by full
# title, so an em-dash or a date edit in the module name does not break this.
READINGS = [
    {
        "zotero": "QFZGIHMH",
        "src": f"{ZOTERO}/BHD9LME7/2026 - Privatizing Risk without Privatizing the Welfare State The Hidden Politics of Social Policy Retrenc.pdf",
        "name": "Hacker 2004 - Privatizing Risk without Privatizing the Welfare State (APSR 98-2).pdf",
        "week_prefix": "Week 3 (",
        "title": "Grad Extension - Hacker 2004, Privatizing Risk without Privatizing the Welfare State",
    },
    {
        "zotero": "B4XJH535",
        "src": f"{ZOTERO}/UMWLFSPA/Pierson - 1993 - When Effect Becomes Cause Policy Feedback and Political Change.pdf",
        "name": "Pierson 1993 - When Effect Becomes Cause (World Politics 45-4).pdf",
        "week_prefix": "Week 4 (",
        # Grad extension only: a review essay of four monographs, assigned in an
        # async week. Undergraduates read Pierson 1995 ch. 1-2 instead.
        "title": "Grad Extension - Pierson 1993, When Effect Becomes Cause",
    },
    {
        "zotero": "J2NRYHH6",
        # JZRE7I9T is the published APSR text (JSTOR, 101(1): 111-127). The
        # other PDF on this Zotero item is La Follette Working Paper 2006-025,
        # a preprint -- do not ship that one to students.
        "src": f"{ZOTERO}/JZRE7I9T/Soss and Schram - 2007 - A Public Transformed Welfare Reform as Policy Feedback.pdf",
        "name": "Soss and Schram 2007 - A Public Transformed (APSR 101-1).pdf",
        "week_prefix": "Week 9 (",
        "title": "Grad Extension - Soss and Schram 2007, A Public Transformed?",
    },
    {
        "zotero": "WWRX7UIS",
        "src": f"{ZOTERO}/Y8VWBDUL/2026 - The Road to Somewhere Why Health Reform Happened Or Why Political Scientists Who Write about Publi.pdf",
        "name": "Hacker 2010 - The Road to Somewhere (Perspectives 8-3).pdf",
        "week_prefix": "Week 10 (",
        "title": "Hacker 2010, The Road to Somewhere: Why Health Reform Happened",
    },
    {
        "zotero": "5DE6UCGM",
        "src": f"{ZOTERO}/LQRIH4EW/Michener - 2020 - Race, Politics, and the Affordable Care Act.pdf",
        "name": "Michener 2020 - Race, Politics, and the Affordable Care Act (JHPPL 45-4).pdf",
        "week_prefix": "Week 13 (",
        "title": "Michener 2020, Race, Politics, and the Affordable Care Act",
    },
]

# Public documents. Retrieved and filed 2026-08-13 (tududi 629-631).
FREE = [
    {
        "source": "Heritage IB5212",
        "src": f"{VAULT}/Week 05/Greszler 2021 - Seven Hard Truths About Social Security (Heritage IB5212).pdf",
        "name": "Greszler 2021 - Seven Hard Truths About Social Security (Heritage IB5212).pdf",
        "week_prefix": "Week 5 (",
        "title": "Recommended - Greszler 2021, Seven Hard Truths About Social Security (Heritage Issue Brief 5212)",
    },
    {
        "source": "CBPP snapshot",
        "src": f"{VAULT}/Week 05/CBPP 2024 - Top Ten Facts about Social Security (snapshot 2026-08-13).pdf",
        "name": "CBPP 2024 - Top Ten Facts about Social Security (course snapshot).pdf",
        "week_prefix": "Week 5 (",
        # Not CBPP's own PDF: theirs is the unrevised 2016 file. This is the
        # page as it stood on 2026-08-13, carrying "Updated May 31, 2024".
        "title": "Recommended - CBPP 2024, Top Ten Facts about Social Security (course snapshot, updated 5/31/2024)",
    },
    {
        "source": "Heritage IB5298",
        "src": f"{VAULT}/Week 09/Rector, Hall, and Ford 2022 - A Road Map for Conservative, Pro-Family Welfare Reform (Heritage IB5298).pdf",
        "name": "Rector, Hall, and Ford 2022 - A Road Map for Conservative, Pro-Family Welfare Reform (Heritage IB5298).pdf",
        "week_prefix": "Week 9 (",
        "title": "Recommended - Rector, Hall, and Ford 2022, A Road Map for Conservative, Pro-Family Welfare Reform (Heritage Issue Brief 5298)",
    },
    # Gilens chapters added 2026-08-30 (task 621, the last of the twelve scans).
    # The syllabus assigns ch. 3 and says "Skim chapter 5 ... also posted."
    # Esping-Andersen ch. 1 (Wk 3) was the twelfth scan and is deliberately NOT
    # here: it was grad-only, and no graduate students enrolled in Fall 2026
    # (David, 2026-08-30). If a grad ever adds, the 19 MB scan is in the vault
    # at Readings/Week 03/ and should be downsampled before upload.
    {
        "source": "Gilens ch. 3 scan",
        "src": f"{VAULT}/Week 12/Gilens 1999 Ch 3 - Racial Attitudes, the Undeserving Poor, and Opposition to Welfare.pdf",
        "name": "Gilens 1999 Ch 3 - Racial Attitudes, the Undeserving Poor, and Opposition to Welfare.pdf",
        "week_prefix": "Week 12 (",
        "title": "Gilens 1999, Why Americans Hate Welfare, ch. 3 - Racial Attitudes, the Undeserving Poor, and Opposition to Welfare",
    },
    {
        "source": "Gilens ch. 5 scan",
        "src": f"{VAULT}/Week 12/Gilens 1999 Ch 5 - The News Media and the Racialization of Poverty.pdf",
        "name": "Gilens 1999 Ch 5 - The News Media and the Racialization of Poverty.pdf",
        "week_prefix": "Week 12 (",
        "title": "Skim - Gilens 1999, Why Americans Hate Welfare, ch. 5 - The News Media and the Racialization of Poverty",
    },
]

FOLDER = "course files/readings"


def ensure_file(entry, existing, dry):
    """Upload unless a byte-identical file of the same name is already there."""
    src, name = entry["src"], entry["name"]
    if not os.path.exists(src):
        ref = entry.get("zotero") or entry["source"]
        raise SystemExit(f"REFUSING TO BUILD: source PDF missing for {ref}:\n  {src}")
    size = os.path.getsize(src)

    hit = existing.get(name)
    if hit and hit.get("size") == size:
        print(f"  file current  : {name} (id {hit['id']})")
        return hit
    if dry:
        print(f"  WOULD UPLOAD  : {name} ({size:,} bytes)")
        return None

    # Canvas keys uploads on the source basename, so stage a correctly-named
    # copy rather than shipping Zotero's auto-generated filename.
    staged = os.path.join("/tmp", name)
    with open(src, "rb") as fh, open(staged, "wb") as out:
        out.write(fh.read())
    try:
        up = upload_file(staged, folder_path=FOLDER)
    finally:
        os.unlink(staged)
    print(f"  file uploaded : {name} (id {up['id']}, {up['size']:,} bytes)")
    return up


def ensure_item(mod, entry, f, items, dry):
    if any(i.get("title") == entry["title"] for i in items):
        print(f"  item present  : {entry['title'][:60]}")
        return
    if dry or f is None:
        print(f"  WOULD LINK    : {entry['title'][:60]} -> {mod['name'][:40]}")
        return
    api("POST", f"/api/v1/courses/{COURSE_ID}/modules/{mod['id']}/items", {
        "module_item": {
            "title": entry["title"],
            "type": "File",
            "content_id": f["id"],
            "indent": 1,
            "published": False,
        }
    })
    print(f"  item linked   : {entry['title'][:60]}")


def main():
    dry = "--dry-run" in sys.argv
    require_env()
    print(f"POSC 459 readings -> course {COURSE_ID}{'  [DRY RUN]' if dry else ''}\n")

    existing = {f["display_name"]: f for f in list_all(f"/api/v1/courses/{COURSE_ID}/files")}
    modules = list_all(f"/api/v1/courses/{COURSE_ID}/modules")

    for entry in READINGS + FREE:
        matches = [m for m in modules if m["name"].startswith(entry["week_prefix"])]
        if len(matches) != 1:
            raise SystemExit(
                f"REFUSING TO BUILD: {len(matches)} modules match {entry['week_prefix']!r}. "
                "Run build_posc459_canvas.py first, or fix the prefix."
            )
        mod = matches[0]
        print(f"{entry.get('zotero') or entry['source']}  ->  {mod['name']}")
        f = ensure_file(entry, existing, dry)
        items = list_all(f"/api/v1/courses/{COURSE_ID}/modules/{mod['id']}/items")
        ensure_item(mod, entry, f, items, dry)
        print()

    print(f"Done. {len(READINGS)} licensed + {len(FREE)} free readings. All unpublished.")


if __name__ == "__main__":
    sys.exit(main())
