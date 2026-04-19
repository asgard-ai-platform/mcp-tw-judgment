"""E2E tests for MCP judgment tools.

Tests marked @live hit the live 司法院 API and are skipped by default.
Set the environment variable to opt in:

    RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v

Tests without @live always run and only verify tool registration (no network).
"""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools.judgment_tools  # noqa: F401 — side-effect: registers @mcp.tool()
from app import mcp


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def live(fn):
    """Mark a test as requiring live API access.

    Skipped unless RUN_LIVE_TESTS=1 is set in the environment.
    """
    return unittest.skipUnless(
        os.environ.get("RUN_LIVE_TESTS"),
        "live API test — set RUN_LIVE_TESTS=1 to run",
    )(fn)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestToolRegistration(unittest.TestCase):
    """Verify tools are registered correctly — no network required."""

    def setUp(self):
        self.tools = asyncio.run(mcp.list_tools())
        self.tool_names = {t.name for t in self.tools}

    def test_expected_tools_registered(self):
        self.assertIn("search_judgments", self.tool_names)
        self.assertIn("get_judgment", self.tool_names)

    def test_search_judgments_schema(self):
        tool = next(t for t in self.tools if t.name == "search_judgments")
        props = tool.inputSchema["properties"]
        self.assertIn("keyword", props)
        self.assertIn("page", props)
        self.assertEqual(props["page"]["default"], 1)

    def test_get_judgment_schema(self):
        tool = next(t for t in self.tools if t.name == "get_judgment")
        self.assertIn("judgment_id", tool.inputSchema["properties"])
        self.assertIn("judgment_id", tool.inputSchema["required"])

    def test_get_judgment_pdf_registered(self):
        self.assertIn("get_judgment_pdf", self.tool_names)

    def test_get_judgment_pdf_schema(self):
        tool = next(t for t in self.tools if t.name == "get_judgment_pdf")
        props = tool.inputSchema["properties"]
        self.assertIn("judgment_id", props)
        self.assertIn("save_to", props)
        self.assertIn("judgment_id", tool.inputSchema["required"])


class TestSearchJudgments(unittest.TestCase):

    @live
    def test_returns_results_for_valid_keyword(self):
        from tools.judgment_tools import search_judgments
        result = search_judgments(keyword="著作權", page=1)

        self.assertIn("total", result)
        self.assertIn("results", result)
        self.assertGreater(result["total"], 0)
        self.assertEqual(len(result["results"]), 20)

    @live
    def test_result_entry_has_required_fields(self):
        from tools.judgment_tools import search_judgments
        result = search_judgments(keyword="著作權", page=1)
        entry = result["results"][0]

        for field in ("judgment_id", "title", "date", "case_reason", "url", "summary"):
            self.assertIn(field, entry, msg=f"Missing field: {field}")
        self.assertTrue(entry["judgment_id"], "judgment_id should not be empty")

    @live
    def test_page_2_differs_from_page_1(self):
        from tools.judgment_tools import search_judgments
        page1 = search_judgments(keyword="著作權", page=1)
        page2 = search_judgments(keyword="著作權", page=2)

        ids1 = {e["judgment_id"] for e in page1["results"]}
        ids2 = {e["judgment_id"] for e in page2["results"]}
        self.assertTrue(ids1.isdisjoint(ids2), "Page 1 and page 2 should have different results")


class TestGetJudgment(unittest.TestCase):

    KNOWN_ID = "IPCV,114,民著訴,52,20260415,1"

    @live
    def test_returns_full_content(self):
        from tools.judgment_tools import get_judgment
        result = get_judgment(judgment_id=self.KNOWN_ID)

        for field in ("title", "date", "case_reason", "content"):
            self.assertIn(field, result)
        self.assertGreater(len(result["content"]), 100)

    @live
    def test_content_contains_keyword(self):
        from tools.judgment_tools import get_judgment
        result = get_judgment(judgment_id=self.KNOWN_ID)
        self.assertIn("著作權", result["content"])

    @live
    def test_search_then_get_roundtrip(self):
        """Verify judgment_id from search can be passed to get_judgment."""
        from tools.judgment_tools import get_judgment, search_judgments
        search = search_judgments(keyword="著作權", page=1)
        first_id = search["results"][0]["judgment_id"]

        detail = get_judgment(judgment_id=first_id)
        self.assertTrue(detail["title"])
        self.assertTrue(detail["content"])


class TestGetJudgmentPdf(unittest.TestCase):

    KNOWN_ID = "IPCV,114,民著訴,52,20260415,1"

    @live
    def test_returns_url_only_when_no_destination(self):
        from tools.judgment_tools import get_judgment_pdf
        # Ensure env var is not set for this call
        prev = os.environ.pop("MCP_TW_JUDGMENT_DOWNLOAD_DIR", None)
        try:
            result = get_judgment_pdf(judgment_id=self.KNOWN_ID)
        finally:
            if prev is not None:
                os.environ["MCP_TW_JUDGMENT_DOWNLOAD_DIR"] = prev

        self.assertEqual(result["judgment_id"], self.KNOWN_ID)
        self.assertTrue(result["url"].endswith(".pdf"))
        self.assertNotIn("path", result)
        self.assertNotIn("size_bytes", result)

    @live
    def test_downloads_to_tempdir(self):
        import tempfile
        from tools.judgment_tools import get_judgment_pdf

        with tempfile.TemporaryDirectory() as tmp:
            result = get_judgment_pdf(judgment_id=self.KNOWN_ID, save_to=tmp)
            self.assertFalse(result["cached"])
            self.assertGreater(result["size_bytes"], 1000)
            self.assertTrue(os.path.isfile(result["path"]))
            self.assertTrue(result["path"].endswith(".pdf"))

    @live
    def test_second_call_is_cached(self):
        import tempfile
        from tools.judgment_tools import get_judgment_pdf

        with tempfile.TemporaryDirectory() as tmp:
            first  = get_judgment_pdf(judgment_id=self.KNOWN_ID, save_to=tmp)
            second = get_judgment_pdf(judgment_id=self.KNOWN_ID, save_to=tmp)

            self.assertFalse(first["cached"])
            self.assertTrue(second["cached"])
            self.assertEqual(first["path"], second["path"])
            self.assertEqual(first["size_bytes"], second["size_bytes"])


class TestGetJudgmentParagraphs(unittest.TestCase):
    """Verify get_judgment now returns the new `paragraphs` field end-to-end."""

    KNOWN_ID = "IPCV,114,民著訴,52,20260415,1"

    @live
    def test_returns_paragraphs_list(self):
        from tools.judgment_tools import get_judgment
        result = get_judgment(judgment_id=self.KNOWN_ID)
        self.assertIn("paragraphs", result)
        self.assertIsInstance(result["paragraphs"], list)
        self.assertGreater(len(result["paragraphs"]), 0)
        first = result["paragraphs"][0]
        for key in ("id", "section", "level", "heading", "text"):
            self.assertIn(key, first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
