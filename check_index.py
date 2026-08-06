#!/usr/bin/env python3
"""Check that index.html and README.md point at the syllabi they claim to.

Six ways a correct, committed syllabus has failed to reach a student here:

  broken     a link points at a file that is not in the repo
  stale      a linked PDF is older than the .tex sitting beside it
  unpushed   a linked file differs from origin/main, so GitHub serves something
             other than what is on disk (the links resolve against main)
  unlinked   a syllabus built for the current term is not linked from the page
  superseded a course is linked at an older term than the newest one it has
  mislabeled a syllabus header and the folder it sits in disagree on the term

Usage:
    ./check_index.py                  # check against the current term
    ./check_index.py --term "Fall 2026"
    ./check_index.py --quiet          # exit code only
    ./check_index.py --pre-push       # what hooks/pre-push runs

Exit status is 1 if anything failed, 0 if clean.
"""

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import urllib.parse

REPO = os.path.dirname(os.path.abspath(__file__))
# Every surface that publishes a link to a syllabus. README.md carried the same
# stale POSC 521 link index.html did, so checking one of them is not enough.
PAGES = ["index.html", "README.md"]
RAW_PREFIX = "https://raw.githubusercontent.com/dadams-AU/syllabi/main/"

# Calendar order within a year, so "newest term" is comparable.
SEASONS = {"intersession": 0, "winter": 0, "spring": 1, "summer": 2, "fall": 3}
SEASON_RE = re.compile(r"(intersession|winter|spring|summer|fall)", re.I)
# An academic-year folder, "2024-25 Spring". Fall belongs to the first year;
# everything after it belongs to the second, so this is Spring *2025*.
ACADEMIC_YEAR_RE = re.compile(
    r"\b(20\d\d)-(\d\d)\D{0,3}(intersession|winter|spring|summer|fall)", re.I)
# Matches "Fall 2026", "spring_26", "fa26", "2026 Summer", "Spring 2027".
TERM_RES = [
    re.compile(r"(intersession|winter|spring|summer|fall)\D{0,3}(20\d\d|\d\d)\b", re.I),
    re.compile(r"\b(20\d\d)\D{0,3}(intersession|winter|spring|summer|fall)", re.I),
    re.compile(r"\b(sp|su|fa|wi)(\d\d)\b", re.I),
]
ABBREV = {"sp": "spring", "su": "summer", "fa": "fall", "wi": "winter"}

# Folders that hold proposals, templates, and shells rather than a syllabus of
# record. Nothing here is expected to be linked from the page.
SKIP = re.compile(r"(proposal|template|shell|POSC 3XX|POSC 428)", re.I)


def parse_term(text):
    """Return (year, season) from a path fragment or file header, or None."""
    m = ACADEMIC_YEAR_RE.search(text)
    if m:
        start, end, season = int(m.group(1)), m.group(2), m.group(3).lower()
        return (start if season == "fall" else int(str(start)[:2] + end), season)
    for pattern in TERM_RES:
        m = pattern.search(text)
        if not m:
            continue
        a, b = m.group(1), m.group(2)
        season, year = (a, b) if SEASON_RE.fullmatch(a) or a.lower() in ABBREV else (b, a)
        season = ABBREV.get(season.lower(), season.lower())
        if season not in SEASONS:
            continue
        year = int(year)
        return (year + 2000 if year < 100 else year, season)
    return None


def header_term(tex_path):
    """The term the source file claims in its opening comments."""
    try:
        with open(tex_path, encoding="utf-8", errors="replace") as f:
            return parse_term("".join(f.readlines()[:15]))
    except OSError:
        return None


def term_of(tex_path):
    """A syllabus's term. The folder wins: header comments survive copy-then-edit
    (posc315_summer_2025.tex still says "Spring 2025" at the top) and the folder
    is the deliberate choice. Falls back to the header when the path has none."""
    return parse_term(tex_path) or header_term(tex_path)


def current_term(today):
    """Months 1-5 Spring, 6-7 Summer, 8-12 Fall: fall prep starts in August."""
    season = "spring" if today.month <= 5 else "summer" if today.month <= 7 else "fall"
    return (today.year, season)


def show(term):
    return f"{term[1].capitalize()} {term[0]}" if term else "unknown term"


def linked_paths(page):
    """Repo-relative paths a page points at, from href="..." and markdown (...)."""
    with open(page, encoding="utf-8") as f:
        text = f.read()
    out = []
    for url in re.findall(r'href="([^"]+)"', text) + re.findall(r"\]\(([^)\s]+)\)", text):
        if url.startswith(RAW_PREFIX):
            out.append(urllib.parse.unquote(url[len(RAW_PREFIX):]))
        elif not re.match(r"(https?:|mailto:|#)", url):
            out.append(urllib.parse.unquote(url))
    return list(dict.fromkeys(out))  # a PDF linked twice is still one file


def git(*args):
    try:
        r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    except OSError:
        return None


def syllabus_pdfs():
    """Every built syllabus in the repo as (pdf, tex, course_dir, term)."""
    found = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in {".git", "build"}]
        for name in files:
            if not name.endswith(".tex"):
                continue
            tex = os.path.join(root, name)
            pdf = tex[:-4] + ".pdf"
            rel = os.path.relpath(tex, REPO)
            if not os.path.exists(pdf) or SKIP.search(rel):
                continue
            found.append((pdf, tex, rel.split(os.sep)[0], term_of(tex)))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--term", help='term to treat as current, e.g. "Fall 2026"')
    ap.add_argument("--index", help="check one page instead of all of them (for testing)")
    ap.add_argument("--pre-push", action="store_true",
                    help="the push about to run will publish the local commits, so "
                         "do not report them as unpushed; uncommitted work still is")
    ap.add_argument("--quiet", action="store_true", help="exit code only")
    args = ap.parse_args()

    term = parse_term(args.term) if args.term else current_term(dt.date.today())
    if args.term and not term:
        sys.exit(f"could not parse term: {args.term!r}")

    pages = [args.index] if args.index else [os.path.join(REPO, p) for p in PAGES]
    problems = []
    built = syllabus_pdfs()
    rank = lambda t: (t[0], SEASONS[t[1]])

    # 3. What GitHub serves is what is on disk. The links resolve against main.
    dirty = set()
    for line in (git("status", "--porcelain") or "").splitlines():
        dirty.add(line[3:].strip().strip('"'))
    ahead = set() if args.pre_push else set(
        (git("diff", "--name-only", "origin/main", "HEAD") or "").splitlines())
    if git("rev-parse", "--verify", "origin/main") is None:
        problems.append(("unpushed", "origin/main", "no origin/main to compare against"))

    total_links = 0
    for page in pages:
        name = os.path.basename(page)
        tag = lambda where: f"{name}: {where}" if len(pages) > 1 else where
        links = linked_paths(page)
        linked_abs = {os.path.normpath(os.path.join(REPO, p)) for p in links}
        total_links += len(links)

        # 1. Every link resolves to a file that is actually in the repo.
        for rel in links:
            if not os.path.exists(os.path.join(REPO, rel)):
                problems.append(("broken", tag(rel), "no such file in the repo"))

        # 2. A linked PDF is not older than the source beside it.
        for rel in links:
            pdf = os.path.join(REPO, rel)
            tex = pdf[:-4] + ".tex"
            if rel.endswith(".pdf") and os.path.exists(pdf) and os.path.exists(tex):
                if os.path.getmtime(pdf) < os.path.getmtime(tex):
                    problems.append(("stale", tag(rel),
                                     "PDF is older than its .tex; rebuild it"))

        # 3 (continued). Uncommitted or unpushed linked files.
        for rel in links:
            if rel in dirty:
                problems.append(("unpushed", tag(rel),
                                 "uncommitted changes; the live file is older"))
            elif rel in ahead:
                problems.append(("unpushed", tag(rel),
                                 "committed but not pushed; the live file is older"))

        # 4. Every course with a current-term syllabus is linked at that term.
        for course in sorted({c for _, _, c, t in built if t == term}):
            pdfs = [p for p, _, c, t in built if c == course and t == term]
            if not any(os.path.normpath(p) in linked_abs for p in pdfs):
                newest = max(pdfs, key=os.path.getmtime)
                problems.append(("unlinked", tag(os.path.relpath(newest, REPO)),
                                 f"{show(term)} syllabus is not linked from {name}"))

        # 5. No course is linked at an older term than the newest one it built.
        #    Rank by calendar order, not by the season's name: "fall" sorts
        #    before "spring" alphabetically, which passes every stale link.
        for course in sorted({c for _, _, c, _ in built}):
            terms = [t for _, _, c, t in built if c == course and t]
            linked = [t for p, _, c, t in built
                      if c == course and t and os.path.normpath(p) in linked_abs]
            if not linked:
                continue
            newest, shown = max(terms, key=rank), max(linked, key=rank)
            if rank(newest) > rank(shown):
                problems.append(("superseded", tag(course),
                                 f"newest built syllabus is {show(newest)}, "
                                 f"{name} links {show(shown)}"))

    # 6. A syllabus's own header agrees with the folder it sits in. Disagreement
    #    is copy-then-edit residue: the term got updated in one place, not both.
    #    Only current and future terms are reported; a past syllabus with a stale
    #    header is history, not a defect worth failing on.
    past = 0
    for _, tex, _, t in built:
        claimed, filed = header_term(tex), parse_term(tex)
        if not (claimed and filed) or claimed == filed:
            continue
        if t and rank(t) >= rank(term):
            problems.append(("mislabeled", os.path.relpath(tex, REPO),
                             f"folder says {show(filed)}, the file header says {show(claimed)}"))
        else:
            past += 1

    if not args.quiet:
        pages_shown = ", ".join(os.path.basename(p) for p in pages)
        print(f"{pages_shown}: {total_links} links, current term {show(term)}\n")
        if problems:
            width = max(len(kind) for kind, _, _ in problems)
            for kind, where, why in problems:
                print(f"  {kind:<{width}}  {where}\n  {'':<{width}}  {why}\n")
        print(f"{len(problems)} problem(s)." if problems else "Clean.")
        if past:
            s = "" if past == 1 else "es"
            print(f"({past} past syllabus{s} carr{'ies' if past == 1 else 'y'} a stale "
                  f"term in the file header; not reported.)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
