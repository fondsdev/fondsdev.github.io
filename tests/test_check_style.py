"""The identity's numeric rules, made checkable.

Three amber marks and one font-weight are not aesthetic preferences — they are
the discipline that makes the accent mean anything and keeps the type to one
voice. Left to memory they drift on the first edit that "just needs a bit of
colour here". Each test below is a rule from DESIGN.md that a well-meaning
change would otherwise break silently.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import check_style

CLEAN = """
<style>
.mark .spn { fill: var(--accent); }
h2[data-sec="04"] { border-bottom-color: var(--accent); }
h2[data-sec="04"]::after { content: "  X"; color: var(--accent); }
strong, b { font-weight: inherit; }
</style>
<a href="https://github.com/fondsdev/fonds">repo</a>
"""


class AccentTest(unittest.TestCase):
    def test_counts_every_use(self):
        self.assertEqual(len(check_style.accent_uses(CLEAN)), 3)

    def test_a_fourth_accent_is_reported(self):
        problems = check_style.check(CLEAN + "a { color: var(--accent); }")
        self.assertTrue(any("accent" in p for p in problems))

    def test_a_missing_accent_is_reported(self):
        page = CLEAN.replace('h2[data-sec="04"] { border-bottom-color: var(--accent); }', "")
        self.assertTrue(any("accent" in p for p in check_style.check(page)))


class WeightTest(unittest.TestCase):
    def test_inherit_alone_is_clean(self):
        self.assertEqual(check_style.font_weights(CLEAN), ["inherit"])

    def test_bold_is_reported(self):
        problems = check_style.check(CLEAN + "h1 { font-weight: bold; }")
        self.assertTrue(any("font-weight" in p for p in problems))

    def test_numeric_weight_is_reported(self):
        problems = check_style.check(CLEAN + "h1 { font-weight: 600; }")
        self.assertTrue(any("font-weight" in p for p in problems))


class ExternalRefTest(unittest.TestCase):
    def test_anchor_href_is_not_a_request(self):
        self.assertEqual(check_style.external_refs(CLEAN), [])

    def test_canonical_link_is_not_a_request(self):
        """The page carries one; flagging it would make the check untrustworthy."""
        page = CLEAN + '<link rel="canonical" href="https://fonds.dev/">'
        self.assertEqual(check_style.external_refs(page), [])

    def test_remote_stylesheet_is_reported(self):
        page = CLEAN + '<link rel="stylesheet" href="https://cdn.example.com/x.css">'
        self.assertTrue(any("external" in p for p in check_style.check(page)))

    def test_webfont_import_is_reported(self):
        page = CLEAN + "@import url('https://fonts.googleapis.com/css?family=X');"
        problems = check_style.check(page)
        self.assertTrue(any("external" in p for p in problems))

    def test_remote_script_is_reported(self):
        problems = check_style.check(CLEAN + '<script src="https://cdn.example.com/x.js"></script>')
        self.assertTrue(any("external" in p for p in problems))


class CleanPageTest(unittest.TestCase):
    def test_clean_page_has_no_problems(self):
        self.assertEqual(check_style.check(CLEAN), [])


if __name__ == "__main__":
    unittest.main()
