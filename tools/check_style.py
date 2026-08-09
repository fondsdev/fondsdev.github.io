#!/usr/bin/env python3
"""Check the page against the numeric rules in DESIGN.md.

Three rules, each one a number rather than a matter of taste, and each one the
kind that drifts silently:

  1. Exactly three var(--accent) uses. Scarcity is what makes the colour mean
     anything; a fourth is the beginning of a brand colour you paint things with.
  2. font-weight declared exactly once, as `inherit`. Bold is the reflex, and
     one weight is the whole type system.
  3. No external subresource. A privacy project whose landing page loads a font
     from Google loses the argument on first paint.

    python3 tools/check_style.py
"""

import re
import sys
from pathlib import Path

ACCENT_USES = 3

ACCENT = re.compile(r"var\(--accent\)")
WEIGHT = re.compile(r"font-weight:\s*([^;}\s]+)")
# A subresource the browser fetches: src=, url(), @import.
SUBRESOURCE = re.compile(
    r"""(?:src\s*=\s*["']|@import\s+url\(["']?|url\(["']?)(https?://[^"')\s]+)""",
    re.IGNORECASE)

LINK_TAG = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
ATTR = re.compile(r"""(\w+)\s*=\s*["']([^"']*)["']""")

# <link> only counts when its rel is one the browser actually fetches. The page
# carries rel="canonical" and rel="icon"; the first is metadata nothing
# requests, and treating it as a subresource is a false positive that would
# teach whoever hits it to stop believing this check.
FETCHING_RELS = {"stylesheet", "preload", "prefetch",
                 "preconnect", "dns-prefetch", "modulepreload"}


def accent_uses(page: str) -> list[str]:
    """Every var(--accent) occurrence, one entry each."""
    return ACCENT.findall(page)


def font_weights(page: str) -> list[str]:
    """Every font-weight value declared, in order."""
    return [w.strip() for w in WEIGHT.findall(page)]


def external_refs(page: str) -> list[str]:
    """Every off-host subresource the page would fetch.

    An <a href> is navigation and a <link rel="canonical"> is metadata; the
    browser requests neither, so neither counts.
    """
    found = list(SUBRESOURCE.findall(page))
    for tag in LINK_TAG.findall(page):
        attrs = {k.lower(): v for k, v in ATTR.findall(tag)}
        if attrs.get("rel", "").lower() in FETCHING_RELS:
            href = attrs.get("href", "")
            if href.startswith(("http://", "https://")):
                found.append(href)
    return found


def check(page: str) -> list[str]:
    problems = []

    uses = accent_uses(page)
    if len(uses) != ACCENT_USES:
        problems.append(
            f"found {len(uses)} var(--accent) uses, expected exactly "
            f"{ACCENT_USES} — the spine, §04's rule, and §04's tick")

    weights = font_weights(page)
    if weights != ["inherit"]:
        problems.append(
            f"font-weight declared as {weights or 'nothing'}; the only "
            "permitted declaration is a single `font-weight: inherit`")

    for ref in external_refs(page):
        problems.append(f"external subresource: {ref}")

    return problems


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print(__doc__, file=sys.stderr)
        return 2

    page = (Path(argv[1]) if len(argv) == 2
            else Path(__file__).resolve().parents[1] / "index.html")
    problems = check(page.read_text())

    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    if problems:
        return 1

    print(f"ok — {page.name} holds to the identity's numbers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
