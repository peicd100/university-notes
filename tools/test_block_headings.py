"""Block heading hierarchy, nested scopes and TOC regressions."""
import unittest
from types import SimpleNamespace

from bs4 import BeautifulSoup
from markdown import Markdown

from tools.block_headings import BlockHeadingExtension


class BlockHeadingTests(unittest.TestCase):
    def render(self, text):
        self.renderer = Markdown(extensions=[
            "admonition", "pymdownx.details", "md_in_html", "pymdownx.superfences", "toc", "attr_list",
            "pymdownx.blocks.admonition", "pymdownx.blocks.details", "pymdownx.tabbed",
            BlockHeadingExtension(),
        ], extension_configs={"pymdownx.tabbed": {"alternate_style": True}})
        return BeautifulSoup(self.renderer.convert(text), "html.parser")

    def levels(self, soup):
        return [int(node.name[1]) for node in soup.select("h1,h2,h3,h4,h5,h6")]

    def test_danger_under_h3_preserves_relative_levels_and_outer_heading(self):
        soup = self.render("### Outside\n\n!!! danger\n\n    # Inner\n\n    ## Child\n\n## Next")
        self.assertEqual(self.levels(soup), [3, 4, 5, 2])
        self.assertEqual(soup.select_one(".admonition h4").get_text(), "Inner")

    def test_details_syntax_uses_surrounding_h3(self):
        soup = self.render("### Outside\n\n???+ note\n\n    ## Inner\n\n    ### Child")
        self.assertEqual(self.levels(soup), [3, 4, 5])
        self.assertTrue(soup.select_one("details").has_attr("open"))

    def test_markdown_in_html_details(self):
        soup = self.render('### Outside\n\n<details markdown="1"><summary>Open</summary>\n\n# Inner\n\n## Child\n\n</details>')
        self.assertEqual(self.levels(soup), [3, 4, 5])

    def test_nested_blocks_use_local_heading_and_restore_outer_scope(self):
        soup = self.render("### Outside\n\n!!! danger\n\n    # Inner\n\n    ??? note\n\n        # Nested\n\n        ## Child\n\n    ## Sibling\n\n!!! note\n\n    # Separate")
        self.assertEqual(self.levels(soup), [3, 4, 5, 6, 5, 4])

    def test_empty_wrapper_inherits_outer_context(self):
        soup = self.render("### Outside\n\n!!! danger\n\n    ??? note\n\n        # Nested")
        self.assertEqual(self.levels(soup), [3, 4])

    def test_correct_deeper_headings_keep_their_levels(self):
        soup = self.render("### Outside\n\n!!! note\n\n    ##### Inner\n\n    ###### Child")
        self.assertEqual(self.levels(soup), [3, 5, 6])

    def test_h6_is_maximum(self):
        soup = self.render("###### Outside\n\n!!! danger\n\n    # Inner\n\n    ## Child")
        self.assertEqual(self.levels(soup), [6, 6, 6])
        self.assertFalse(soup.select("h7"))

    def test_code_and_raw_html_are_preserved(self):
        text = '### Outside\n\n!!! note\n\n    ```markdown\n    # Literal\n    ```\n\n    # Inner\n\n<details><summary>Raw</summary><h1>Raw heading</h1></details>'
        soup = self.render(text)
        self.assertIn("# Literal", soup.select_one("code").get_text())
        self.assertEqual(self.levels(soup), [3, 4, 1])

    def test_blockquote_and_tabs(self):
        soup = self.render('### Outside\n\n> # Quote\n>\n> ## Child\n\n=== "One"\n\n    # Tab\n\n    ## Child')
        self.assertEqual(self.levels(soup), [3, 4, 5, 4, 5])

    def test_toc_sees_adjusted_levels_and_existing_ids(self):
        soup = self.render("### Outside {#custom}\n\n!!! danger\n\n    # Inner\n\n    ## Child")
        tokens = self.renderer.toc_tokens
        self.assertEqual(tokens[0]["level"], 3)
        self.assertEqual(tokens[0]["children"][0]["level"], 4)
        self.assertEqual(tokens[0]["children"][0]["children"][0]["level"], 5)
        self.assertEqual(soup.select_one(".admonition h4")["id"], "inner")
        self.assertEqual(soup.select_one("h3")["id"], "custom")

    def test_slash_admonition_and_details(self):
        soup = self.render("### Outside\n\n/// danger\n\n# Inner\n\n## Child\n\n///\n\n/// details | Expand\n\n# Detail\n\n///")
        self.assertEqual(self.levels(soup), [3, 4, 5, 4])

    def test_document_without_blocks_is_unchanged(self):
        soup = self.render("# First\n\n### Third\n\n## Second")
        self.assertEqual(self.levels(soup), [1, 3, 2])

    def test_reusing_renderer_resets_section_context(self):
        self.render("##### Last")
        soup = BeautifulSoup(self.renderer.reset().convert("!!! note\n\n    # Inner"), "html.parser")
        self.assertEqual(self.levels(soup), [1])

    def test_adjusted_heading_still_locates_original_source(self):
        from tools import source_jump_hook as jump

        source = "### Outside\n\n!!! danger\n\n    # Inner"
        self.assertEqual(self.render(source).select_one(".admonition h4").get_text(), "Inner")
        record = jump._build_page_record(source, SimpleNamespace(
            src_uri="test.md", dest_uri="test.html", abs_src_path="C:/notes/test.md"))
        position = jump._locate_selection(record, "Inner", "Inner", "",
            heading_path="Outside / Inner", prev_block="", next_block="", block_tag="h4",
            block_index=None, section_index=None, block_progress=None, caret_offset=1)
        self.assertTrue(position["ok"])
        self.assertEqual(position["line"], 5)
        self.assertEqual(position["column"], 8)


if __name__ == "__main__":
    unittest.main()
