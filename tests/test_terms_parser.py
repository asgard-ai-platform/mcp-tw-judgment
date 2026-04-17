"""Unit tests for parser/terms_parser.py.

Fixture:
  tests/fixtures/terms_result.html  — /TermContent.aspx?TRMTERM=比例原則&SYS=V response

No network calls — all tests run against the saved HTML file.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.terms_parser import parse_term_definitions

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "terms_result.html")


def load_fixture() -> str:
    with open(FIXTURE, encoding="utf-8") as f:
        return f.read()


class TestParseTermDefinitions(unittest.TestCase):

    def setUp(self):
        self.result = parse_term_definitions(load_fixture())

    def test_term_name_extracted(self):
        self.assertEqual(self.result["term"], "比例原則")

    def test_four_definitions_returned(self):
        self.assertEqual(len(self.result["definitions"]), 4)

    def test_all_domains_present(self):
        domains = {d["domain"] for d in self.result["definitions"]}
        self.assertEqual(domains, {"民事", "行政", "家事", "刑事"})

    def test_each_definition_has_explanation(self):
        for d in self.result["definitions"]:
            self.assertTrue(d["explanation"], f"Empty explanation for domain: {d['domain']}")

    def test_disclaimer_extracted(self):
        self.assertEqual(self.result["disclaimer"], "本解釋內容僅供參考，不拘束個案")

    def test_empty_html_returns_empty(self):
        result = parse_term_definitions("<html></html>")
        self.assertEqual(result["term"], "")
        self.assertEqual(result["definitions"], [])
        self.assertEqual(result["disclaimer"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
