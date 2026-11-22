"""Tests for make_banner.check(), the banner's self-lint (design Section 2 constraints).

Run from the repo root: python3 -m unittest discover -s tools/chessprot-banner -p 'test_*.py'
Needs no fonts and no packages beyond the standard library: check() works on SVG text only.
"""

import unittest

from make_banner import check

OK = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    "<title>t</title>"
    '<defs><linearGradient id="a-g1"/><linearGradient id="a-g2" href="#a-g1"/></defs>'
    '<path id="a-p" fill="url(#a-g2)" d="M0 0H1V1Z"/>'
    "</svg>\n"
)


def with_extra(markup: str) -> str:
    return OK.replace("</svg>", markup + "</svg>")


class CheckTest(unittest.TestCase):
    def test_clean_svg_passes(self):
        self.assertEqual(check(OK), [])

    def test_xmlns_is_not_an_external_reference(self):
        self.assertEqual(check(OK.replace("<svg ", '<svg xmlns:xlink="http://www.w3.org/1999/xlink" ')), [])

    def test_forbidden_elements(self):
        for tag in ("<text>x</text>", "<script/>", "<foreignObject/>", '<image href="#a-p"/>', "<style/>"):
            with self.subTest(tag=tag):
                self.assertTrue(check(with_extra(tag)))

    def test_external_href_and_url(self):
        self.assertIn("external reference http://x/y.png", check(with_extra('<use href="http://x/y.png"/>')))
        self.assertIn("url() to https://e/f", check(with_extra('<rect fill="url(https://e/f)"/>')))

    def test_duplicate_ids(self):
        self.assertIn("duplicate ids ['a-p']", check(with_extra('<rect id="a-p"/>')))

    def test_unresolved_reference(self):
        self.assertIn("unresolved references ['nope']", check(with_extra('<rect fill="url(#nope)"/>')))

    def test_title_required(self):
        self.assertIn("no <title>", check(OK.replace("<title>t</title>", "")))

    def test_invalid_xml(self):
        self.assertTrue(any(p.startswith("not valid XML") for p in check(OK.replace("</svg>", ""))))

    def test_size_limit(self):
        big = with_extra('<path d="' + "M0 0" * 40_000 + '"/>')
        self.assertTrue(any("bytes >" in p for p in check(big)))


if __name__ == "__main__":
    unittest.main()
