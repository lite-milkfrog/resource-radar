"""Offline tests: deterministic fixtures, no live calls, no script execution."""

import tempfile
import unittest
from pathlib import Path

from resource_radar.catalog import Catalog, canonicalize, parse_markdown


SAMPLE = """# Video tools
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - download videos
- [Example](https://example.com/?utm_source=spam) - utility
## AI models
- [Ollama](https://ollama.com/) - local AI models
"""


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cat = Catalog(Path(self.tmp.name) / "db.sqlite3")

    def tearDown(self):
        self.cat.close()
        self.tmp.cleanup()

    def test_parsing_and_normalization(self):
        rows = list(parse_markdown(SAMPLE, "fmhy"))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]["url"], "https://example.com/")
        self.assertEqual(rows[2]["category"], "AI models")
        self.assertEqual(canonicalize("http://localhost/x"), "")
        self.assertEqual(canonicalize("file:///etc/passwd"), "")

    def test_import_search_inspect_dedup(self):
        self.cat.import_markdown("fmhy", SAMPLE)
        self.assertEqual(self.cat.count(), 3)
        self.assertEqual(self.cat.search("Ollama")[0]["title"], "Ollama")
        self.assertEqual(self.cat.search("local AI")[0]["title"], "Ollama")
        self.cat.import_markdown("awesome", "# Software\n[Ollama](https://ollama.com/) - another description")
        self.assertEqual(self.cat.count(), 3)
        self.assertEqual(self.cat.inspect("https://ollama.com/")["provenance"][0]["source"], "awesome")
        self.assertEqual(len(self.cat.inspect("https://ollama.com/")["provenance"]), 2)
        self.assertFalse(self.cat.inspect("https://missing.invalid")["found"])

    def test_unknown_source_and_invalid_empty_data(self):
        with self.assertRaises(ValueError):
            self.cat.import_markdown("unknown", SAMPLE)
        with self.assertRaises(ValueError):
            self.cat.import_markdown("fmhy", "no links")
        self.assertEqual(self.cat.count(), 0)

    def test_source_filter(self):
        self.cat.import_markdown("fmhy", SAMPLE)
        self.assertEqual(self.cat.search("Ollama", source="awesome"), [])

    def test_userscript_html_summary_import(self):
        text = '# Extensions\n<summary><a href="https://github.com/example/userscript/#readme">YouTube Helper</a> - Enhance the page.</summary><br>'
        self.cat.import_markdown("awesome_userscripts", text)
        hits = self.cat.search("YouTube", source="awesome_userscripts")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["description"], "Enhance the page.")
        self.assertEqual(hits[0]["url"], "https://github.com/example/userscript")
        self.assertEqual(hits[0]["category"], "Extensions")


if __name__ == "__main__":
    unittest.main()
