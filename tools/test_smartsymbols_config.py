"""Regression: item labels must never become copyright symbols."""
import unittest

import markdown
from bs4 import BeautifulSoup
from mkdocs.config import load_config


class SmartSymbolsConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = [load_config(name) for name in ("mkdocs.yml", "mkdocs.preview.yml")]

    def render(self, config, source):
        return BeautifulSoup(markdown.markdown(
            source, extensions=config["markdown_extensions"],
            extension_configs=config["mdx_configs"],
        ), "html.parser").get_text()

    def test_main_and_preview_disable_only_copyright(self):
        for config in self.configs:
            with self.subTest(config=config.config_file_path):
                smart = config["mdx_configs"]["pymdownx.smartsymbols"]
                self.assertIs(smart["copyright"], False)
                self.assertNotIn("trademark", smart)
                self.assertNotIn("registered", smart)

    def test_item_labels_in_all_markdown_contexts(self):
        contexts = [
            "要注意，(c)、(d) 則是對有序對的第一個位置展開交集或聯集。",
            "(c) (C) (d) text(c) 中(c)文",
            "# (c) and (C)\n\n## (d)",
            "- (c)\n- (C)\n- (d)",
            "> (c) (C) (d)",
            "| Item | Value |\n| --- | --- |\n| (c) | (C) |\n| (d) | text |",
            "`(c) (C) (d)`",
            "```text\n(c) (C) (d)\n```",
            "<p>(c) (C) (d)</p>",
        ]
        for config in self.configs:
            for source in contexts:
                with self.subTest(config=config.config_file_path, source=source):
                    text = self.render(config, source)
                    self.assertNotIn("©", text)
                    for label in ("(c)", "(C)", "(d)"):
                        self.assertEqual(text.count(label), source.count(label))

    def test_literal_copyright_and_other_symbols_still_work(self):
        for config in self.configs:
            with self.subTest(config=config.config_file_path):
                self.assertEqual(self.render(config, "© &copy; &#169;"), "© © ©")
                text = self.render(config, "(tm) (r)")
                self.assertIn("™", text)
                self.assertIn("®", text)


if __name__ == "__main__":
    unittest.main()
