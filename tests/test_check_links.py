"""The guard has to fail on a broken page, not just pass on a good one.

Each test builds a throwaway `fonds` checkout on disk and a page string, so
what is being asserted is the checker's verdict rather than the state of any
real repository.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import check_links

PYPROJECT = """\
[project]
name = "fonds"

[project.optional-dependencies]
transcribe = ["mlx-whisper>=0.4"]
calendar = ["google-auth-oauthlib>=1.2"]

[project.scripts]
fonds = "fonds.cli:main"
"""

GOOD_PAGE = """\
<a href="https://github.com/fondsdev/fonds/blob/main/docs/mac.md">mac.md</a>
<code>pip install -e '.[transcribe]'</code>
"""


def checkout(tmp: str) -> Path:
    """A minimal stand-in for a clone of fondsdev/fonds."""
    root = Path(tmp)
    (root / "docs").mkdir()
    (root / "docs" / "mac.md").write_text("# mac\n")
    (root / "pyproject.toml").write_text(PYPROJECT)
    return root


class ExtractionTest(unittest.TestCase):
    def test_finds_blob_paths(self):
        self.assertEqual(check_links.blob_paths(GOOD_PAGE), ["docs/mac.md"])

    def test_ignores_the_anchor_on_a_blob_link(self):
        page = 'href="https://github.com/fondsdev/fonds/blob/main/docs/pin.md#sync"'
        self.assertEqual(check_links.blob_paths(page), ["docs/pin.md"])

    def test_finds_quoted_extras(self):
        self.assertEqual(check_links.quoted_extras(GOOD_PAGE), ["transcribe"])

    def test_finds_each_name_in_a_comma_list(self):
        """`\\w` alone would match none of this, letting it through unchecked."""
        page = "pip install -e '.[transcribe,calendar]'"
        self.assertEqual(check_links.quoted_extras(page),
                         ["transcribe", "calendar"])


class CheckTest(unittest.TestCase):
    def test_clean_page_has_no_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(check_links.check(GOOD_PAGE, checkout(tmp)), [])

    def test_missing_doc_is_reported(self):
        page = 'href="https://github.com/fondsdev/fonds/blob/main/docs/gone.md"' + GOOD_PAGE
        with tempfile.TemporaryDirectory() as tmp:
            problems = check_links.check(page, checkout(tmp))
        self.assertEqual(len(problems), 1)
        self.assertIn("docs/gone.md", problems[0])

    def test_unknown_extra_is_reported(self):
        page = GOOD_PAGE + "<code>pip install -e '.[gpu]'</code>"
        with tempfile.TemporaryDirectory() as tmp:
            problems = check_links.check(page, checkout(tmp))
        self.assertEqual(len(problems), 1)
        self.assertIn("gpu", problems[0])

    def test_missing_console_script_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = checkout(tmp)
            (root / "pyproject.toml").write_text(
                PYPROJECT.replace('fonds = "fonds.cli:main"', 'other = "x:main"'))
            problems = check_links.check(GOOD_PAGE, root)
        self.assertEqual(len(problems), 1)
        self.assertIn("fonds", problems[0])


class VacuousPassTest(unittest.TestCase):
    """The guard's own guard: a page it cannot parse must fail, not pass."""

    def test_page_with_no_links_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems = check_links.check("<p>nothing here</p>", checkout(tmp))
        self.assertTrue(any("no " in p for p in problems))

    def test_page_with_links_but_no_extras_is_reported(self):
        page = 'href="https://github.com/fondsdev/fonds/blob/main/docs/mac.md"'
        with tempfile.TemporaryDirectory() as tmp:
            problems = check_links.check(page, checkout(tmp))
        self.assertTrue(any("extra" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
