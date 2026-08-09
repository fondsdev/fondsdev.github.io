#!/usr/bin/env python3
"""Check the landing page against a checkout of fondsdev/fonds.

The page restates things the fonds repo owns: the install command, the name of
the console script, and a link to every guide. The two move independently and
nothing in either repo reads the page, so drift is invisible until a stranger
clicks a 404. This is what notices.

    python3 tools/check_links.py ../fonds
"""

import re
import sys
import tomllib
from pathlib import Path

REPO = "fondsdev/fonds"
CONSOLE_SCRIPT = "fonds"

# https://github.com/fondsdev/fonds/blob/main/<path>, stopping at an anchor,
# a quote, whitespace or a closing bracket.
BLOB = re.compile(rf"https://github\.com/{REPO}/blob/main/([^\"'#\s>)]+)")

# pip install -e '.[<extra>]', or a comma-list of them. The comma has to be in
# the class: with `\w+` alone a line like '.[a,b]' matches nothing at all, and
# a page carrying one valid extra elsewhere would sail past the empty-set guard
# below having never checked it.
EXTRA = re.compile(r"pip install -e '\.\[([\w,]+)\]'")


def blob_paths(page: str) -> list[str]:
    """Every repo-relative path the page deep-links to, in order, deduplicated."""
    return list(dict.fromkeys(BLOB.findall(page)))


def quoted_extras(page: str) -> list[str]:
    """Every optional-dependency name the page tells the reader to install."""
    names = []
    for match in EXTRA.findall(page):
        names.extend(name for name in match.split(",") if name)
    return list(dict.fromkeys(names))


def check(page: str, checkout: Path) -> list[str]:
    """Return a list of problems with `page`. Empty means it is clean."""
    problems = []

    pyproject = tomllib.loads((checkout / "pyproject.toml").read_text())
    project = pyproject.get("project", {})
    known_extras = set(project.get("optional-dependencies", {}))
    known_scripts = set(project.get("scripts", {}))

    paths = blob_paths(page)
    extras = quoted_extras(page)

    # Rule 3 first: a page these selectors cannot parse must fail loudly rather
    # than sail through having checked nothing.
    if not paths:
        problems.append(
            "found no github.com/{}/blob/main/... links on the page — either "
            "the page lost its links or BLOB stopped matching".format(REPO))
    if not extras:
        problems.append(
            "found no `pip install -e '.[extra]'` on the page — either the "
            "page lost its install table or EXTRA stopped matching")

    # Rule 2: every deep link resolves to a file that is actually there.
    for path in paths:
        if not (checkout / path).exists():
            problems.append(f"page links to {path}, which is not in {checkout}")

    # Rule 1: the install commands are real.
    if CONSOLE_SCRIPT not in known_scripts:
        problems.append(
            f"page promises the `{CONSOLE_SCRIPT}` command, but "
            f"[project.scripts] defines {sorted(known_scripts) or 'nothing'}")
    for extra in extras:
        if extra not in known_extras:
            problems.append(
                f"page quotes the '{extra}' extra, which is not in "
                f"[project.optional-dependencies] ({sorted(known_extras)})")

    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    checkout = Path(argv[1]).expanduser().resolve()
    if not (checkout / "pyproject.toml").exists():
        print(f"{checkout} is not a fonds checkout — no pyproject.toml",
              file=sys.stderr)
        return 2

    page = Path(__file__).resolve().parents[1] / "index.html"
    problems = check(page.read_text(), checkout)

    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    if problems:
        return 1

    print(f"ok — {page.name} agrees with {checkout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
