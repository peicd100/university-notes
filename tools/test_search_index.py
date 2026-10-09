"""Verify that literal search consumes the filtered Material index, not private sources.

Run with the project's mkdocs Conda environment.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from mkdocs.commands.build import build
from mkdocs.config import load_config


class SearchVisibilityTests(unittest.TestCase):
    def test_encrypted_and_explicitly_excluded_content_stay_out_of_public_index(self):
        root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            temp = Path(directory)
            docs = temp / "docs"
            docs.mkdir()
            (docs / "index.md").write_text(
                "# 公開文章\n\n我們會第一直覺用一個 always。\n\n## 程式碼\n\n```verilog\nq <= d;\n```\n",
                encoding="utf-8",
            )
            # A synthetic fixture password, not a real credential.
            (docs / "locked.md").write_text(
                "---\npassword: test-only-fixture\n---\n# Locked\n\nprivate-sentinel-body\n",
                encoding="utf-8",
            )
            (docs / "excluded.md").write_text(
                "---\nsearch:\n  exclude: true\n---\n# Excluded\n\nexcluded-sentinel-body\n",
                encoding="utf-8",
            )
            config_path = temp / "mkdocs.yml"
            config_path.write_text(
                "site_name: Search visibility regression\nuse_directory_urls: false\n"
                "theme:\n  name: material\n  font: false\n  custom_dir: "
                + json.dumps((root / "theme").as_posix())
                + "\nplugins:\n  - search:\n      separator: '[\\s\\u200b\\-]'\n"
                "  - encryptcontent:\n      search_index: encrypted\n",
                encoding="utf-8",
            )
            config = load_config(config_file=str(config_path))
            build(config)
            index_path = temp / "site/search/search_index.json"
            raw = index_path.read_text(encoding="utf-8")
            index = json.loads(raw)
            self.assertNotIn("private-sentinel-body", raw)
            self.assertNotIn("excluded-sentinel-body", raw)
            self.assertTrue(index["docs"])
            self.assertTrue(all(entry["location"].startswith("index.html") for entry in index["docs"]))
            text = " ".join(entry["text"] for entry in index["docs"]).replace("\u200b", "")
            self.assertIn("會第一直覺用一", text)
            self.assertIn("q &lt;= d", text)
            for filename in ["assets/javascripts/workers/search-peicd.js", "assets/pymdownx-extras/search-core.js"]:
                self.assertTrue((temp / "site" / filename).is_file(), filename)


if __name__ == "__main__":
    unittest.main()
