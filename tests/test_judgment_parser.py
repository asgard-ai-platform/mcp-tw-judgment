"""Unit tests for parser/judgment_parser.py.

Fixtures:
  tests/fixtures/search_result.html  — /FJUD/qryresult.aspx response (= data.html)
  tests/fixtures/list_result.html    — /FJUD/qryresultlst.aspx response (iframe content)

No network calls — all tests run against saved HTML files.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.judgment_parser import ParseError, extract_qid, parse_result_count, parse_result_list

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load(filename: str) -> str:
    with open(os.path.join(FIXTURES, filename), encoding="utf-8") as f:
        return f.read()


class TestExtractQid(unittest.TestCase):

    def setUp(self):
        self.html = load("search_result.html")

    def test_extracts_known_qid(self):
        self.assertEqual(extract_qid(self.html), "9da06ee5ce59f0e31bd8741089a8ed56")

    def test_raises_parse_error_when_missing(self):
        with self.assertRaises(ParseError):
            extract_qid("<html><body>no hidden input here</body></html>")


class TestParseResultCount(unittest.TestCase):

    def setUp(self):
        self.html = load("search_result.html")

    def test_extracts_known_count(self):
        self.assertEqual(parse_result_count(self.html), 55265)

    def test_returns_none_when_missing(self):
        self.assertIsNone(parse_result_count("<html></html>"))


class TestParseResultList(unittest.TestCase):

    def setUp(self):
        self.results = parse_result_list(load("list_result.html"))

    def test_returns_one_page(self):
        self.assertEqual(len(self.results), 20)

    def test_first_entry_fields(self):
        first = self.results[0]
        self.assertEqual(first["title"], "智慧財產及商業法院 114 年度 民著訴 字第 52 號民事判決")
        self.assertEqual(first["date"], "115.04.15")
        self.assertEqual(first["case_reason"], "侵害著作權有關人格權爭議")
        self.assertTrue(first["url"].startswith("data.aspx?ty=JD&id="))
        self.assertTrue(len(first["summary"]) > 0)

    def test_all_entries_have_required_keys(self):
        for entry in self.results:
            for key in ("title", "date", "case_reason", "url", "summary"):
                self.assertIn(key, entry, msg=f"Missing key '{key}' in entry: {entry}")

    def test_no_size_suffix_in_title(self):
        for entry in self.results:
            self.assertNotRegex(entry["title"], r"（\d+K）")

    def test_empty_html_returns_empty_list(self):
        self.assertEqual(parse_result_list("<html></html>"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
