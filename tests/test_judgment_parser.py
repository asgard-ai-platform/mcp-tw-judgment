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

from parser.judgment_parser import (
    ParseError, extract_qid, parse_result_count, parse_result_list,
    extract_pdf_url, parse_paragraphs, parse_detail,
)

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


class TestExtractPdfUrl(unittest.TestCase):

    def test_returns_absolute_url_from_fixture(self):
        html = load("detail_result.html")
        url = extract_pdf_url(html)
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith("https://judgment.judicial.gov.tw/FILES/"),
                        f"unexpected URL: {url}")
        self.assertTrue(url.endswith(".pdf"))

    def test_returns_none_when_no_pdf_link(self):
        html = "<html><body><a href='other.aspx'>not a pdf</a></body></html>"
        self.assertIsNone(extract_pdf_url(html))


class TestParseParagraphs(unittest.TestCase):

    def setUp(self):
        self.paragraphs = parse_paragraphs(load("detail_result.html"))

    def test_returns_non_empty_list(self):
        self.assertGreater(len(self.paragraphs), 0)

    def test_each_paragraph_has_required_keys(self):
        for p in self.paragraphs:
            for key in ("id", "section", "level", "heading", "text"):
                self.assertIn(key, p, msg=f"missing {key} in {p}")

    def test_ids_are_unique(self):
        ids = [p["id"] for p in self.paragraphs]
        self.assertEqual(len(ids), len(set(ids)),
                         "paragraph IDs must be globally unique")

    def test_has_main_sections(self):
        sections = {p["section"] for p in self.paragraphs}
        # Every judgment has at least 主文 + (事實 or 事實及理由 or 理由)
        self.assertIn("主文", sections)
        self.assertTrue(
            sections & {"事實", "事實及理由", "理由"},
            f"expected one of 事實/事實及理由/理由, got {sections}",
        )

    def test_level_1_ids_match_section_names(self):
        for p in self.paragraphs:
            if p["level"] == 1:
                self.assertEqual(p["id"], p["section"])

    def test_level_2_id_format(self):
        # 理由.一, 理由.二, ...
        lvl2 = [p for p in self.paragraphs if p["level"] == 2]
        for p in lvl2:
            self.assertRegex(p["id"], r"^[^.]+\.[一二三四五六七八九十百]+$")

    def test_fallback_when_no_sections(self):
        plain = "<html><body><div class='htmlcontent'>隨便一段文字沒有章節。</div></body></html>"
        result = parse_paragraphs(plain)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["section"], "全文")
        self.assertEqual(result[0]["id"], "全文")
        self.assertEqual(result[0]["level"], 1)
        self.assertIn("隨便一段文字", result[0]["text"])

    def test_empty_body_returns_empty_list(self):
        self.assertEqual(parse_paragraphs("<html></html>"), [])


class TestParseDetailBackwardCompat(unittest.TestCase):

    def setUp(self):
        self.result = parse_detail(load("detail_result.html"))

    def test_original_fields_still_present(self):
        for key in ("title", "date", "case_reason", "content"):
            self.assertIn(key, self.result)

    def test_content_is_nonempty_string(self):
        self.assertIsInstance(self.result["content"], str)
        self.assertGreater(len(self.result["content"]), 100)

    def test_paragraphs_field_added(self):
        self.assertIn("paragraphs", self.result)
        self.assertIsInstance(self.result["paragraphs"], list)
        self.assertGreater(len(self.result["paragraphs"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
