"""Regression tests: python -m unittest tools.test_latex_bracket_math_hook."""
from pathlib import Path
import unittest

import markdown
from bs4 import BeautifulSoup

from tools.latex_bracket_math_hook import on_page_markdown


def normalize(source: str) -> str:
    return on_page_markdown(source, page=None, config=None, files=None)


def render(source: str) -> BeautifulSoup:
    html = markdown.markdown(
        normalize(source),
        extensions=["nl2br", "pymdownx.superfences", "pymdownx.arithmatex"],
        extension_configs={"pymdownx.arithmatex": {"generic": True, "block_tag": "pre"}},
    )
    return BeautifulSoup(html, "html.parser")


class PastedDisplayMathTests(unittest.TestCase):
    def test_gpt_quote_without_blank_lines(self):
        source = "> 前文  \n> \\[\n> \\boxed{0,1,2,\\ldots,b-1}\n> \\]\n> 之中。\n"
        soup = render(source)
        quote = soup.select_one("blockquote")
        math = quote.select_one("pre.arithmatex")
        self.assertIsNotNone(math)
        self.assertIn(r"\boxed{0,1,2,\ldots,b-1}", math.get_text())
        self.assertEqual([p.get_text().strip() for p in quote.find_all("p")], ["前文", "之中。"])
        self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_display_delimiters_and_nested_quotes(self):
        for prefix in ("", "> ", "> > ", ">>"):
            for opening, closing in ((r"\[", r"\]"), ("$$", "$$"), ("[", "]")):
                with self.subTest(prefix=prefix, opening=opening):
                    source = "\n".join(prefix + line for line in ("前文", opening, "x=1", closing, "後文"))
                    self.assertEqual(len(render(source).select("pre.arithmatex")), 1)
                    self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_existing_spacing_and_inline_math_unchanged(self):
        for source in (
            "前文\n\n\\[\nx=1\n\\]\n\n後文\n",
            "> 前文\n>\n> \\[\n> x=1\n> \\]\n>\n> 後文\n",
            r"inline $x=1$ and \(y=2\), [link](https://example.com).",
        ):
            self.assertEqual(normalize(source), source)

    def test_code_fences_unchanged(self):
        for prefix in ("", "> ", "> > ", "    "):
            for fence in ("```", "~~~~"):
                source = "\n".join(prefix + line for line in (fence + "text", "[", "x=1", "]", r"\[", "x=2", r"\]", "$$", "x=3", "$$", fence))
                self.assertEqual(normalize(source), source)

    def test_quote_markers_inside_fenced_code_unchanged(self):
        source = "```text\n> ```\n\\[\nx=1\n\\]\n```\n"
        self.assertEqual(normalize(source), source)

    def test_unclosed_quote_fence_does_not_hide_later_math(self):
        source = "> ```text\n> x\n\n前文\n\\[\nx=1\n\\]\n後文\n"
        result = normalize(source)
        self.assertIn("前文\n\n\\[", result)
        self.assertTrue(result.startswith("> ```text\n> x\n\n"))

    def test_indented_code_unchanged(self):
        for prefix in ("    ", "\t", ">     "):
            source = "\n".join(prefix + line for line in (r"\[", "x=1", r"\]"))
            self.assertEqual(normalize(source), source)

    def test_unclosed_empty_or_cross_container_math_unchanged(self):
        for source in (
            "> \\[\n> x=1\n後文\n\\]",
            "\\[\nx=1\n> \\]",
            "\\[\n\\]",
            "[\n```text\nx\n```\n]",
            "前文\n\\[\nx=1\n",
        ):
            self.assertEqual(normalize(source), source)

    def test_crlf_and_no_final_newline(self):
        source = "> 前文\r\n> \\[\r\n> x=1\r\n> \\]\r\n> 後文"
        result = normalize(source)
        self.assertNotIn("\n", result.replace("\r\n", ""))
        self.assertFalse(result.endswith("\n"))
        self.assertEqual(len(render(source).select("pre.arithmatex")), 1)

    def test_three_space_list_math_and_following_prose(self):
        source = "1. 常數和：\n\n   $$\n   \\sum_{k=1}^{n} c = nc\n   $$\n\n2. 係數可以提出：\n\n   $$\n   c \\sum_{k=1}^{n} a_k\n   $$\n\n   其中 \\(c\\) 是常數。\n"
        soup = render(source)
        items = soup.select("ol > li")
        self.assertEqual(len(items), 2)
        self.assertTrue(all(item.select_one("pre.arithmatex") for item in items))
        self.assertIn("其中", items[1].get_text())
        self.assertEqual(len(items[1].select("span.arithmatex")), 1)
        self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_list_delimiters_without_blank_lines_and_nested_quotes(self):
        for quote in ("", "> ", "> > "):
            for marker in ("1.", "-", "10."):
                for indent in (3, 4):
                    for opening, closing in (("$$", "$$"), (r"\[", r"\]"), ("[", "]")):
                        with self.subTest(quote=quote, marker=marker, indent=indent, opening=opening):
                            source = "\n".join(quote + line for line in (
                                marker + " 說明", " " * indent + opening, " " * indent + "x=1",
                                " " * indent + closing, " " * indent + "後文"))
                            soup = render(source)
                            item = soup.select_one("li")
                            self.assertIsNotNone(item.select_one("pre.arithmatex"))
                            self.assertIn("後文", item.get_text())
                            self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_indented_root_list_markers(self):
        for indent in (1, 2, 3):
            source = " " * indent + "1. 說明\n\n" + "\n".join(" " * (indent+3) + line for line in ("$$", "x=1", "$$"))
            self.assertIsNotNone(render(source).select_one("li pre.arithmatex"))
            self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_nested_three_space_lists(self):
        source = "1. 外層\n\n   - 內層\n\n      $$\n      x=1\n      $$\n\n      說明\n\n   外層後文\n"
        soup = render(source)
        self.assertIsNotNone(soup.select_one("ol > li > ul > li pre.arithmatex"))
        self.assertIn("說明", soup.select_one("ul > li").get_text())
        self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_list_literal_code_not_treated_as_math(self):
        source = "1. code\n\n   ```text\n   > literal\n   1. literal\n   $$\n   x=1\n   $$\n   ```\n\n   $$\n   y=2\n   $$\n"
        soup = render(source)
        self.assertEqual(len(soup.select("pre.arithmatex")), 1)
        self.assertIn("$$", soup.select_one("code").get_text())
        self.assertIn("> literal", soup.select_one("code").get_text())
        source = "1. code\n\n       $$\n       x=1\n       $$\n"
        soup = render(source)
        self.assertFalse(soup.select(".arithmatex"))
        self.assertIn("$$", soup.select_one("code").get_text())
        standalone = "    1. literal code\n       $$\n       x=1\n       $$\n"
        self.assertEqual(normalize(standalone), standalone)

    def test_thematic_break_is_not_a_list(self):
        source = "* * *\n\n   原本三空白\n"
        self.assertEqual(normalize(source), source)

    def test_list_scope_and_crlf(self):
        source = "1. 列表\r\n\r\n   $$\r\n   x=1\r\n   $$\r\n\r\n外部段落\r\n\r\n   原本三空白"
        result = normalize(source)
        self.assertTrue(result.endswith("   原本三空白"))
        self.assertNotIn("\n", result.replace("\r\n", ""))
        self.assertFalse(result.endswith("\n"))
        self.assertEqual(len(render(source).select("pre.arithmatex")), 1)

    def test_double_escaped_inline_in_headings_and_prose(self):
        source = r"## 消去律：\\(a\\)" + "\n\n" + r"假設 \\(ax=ay\\)，其中 \\(a\neq0\\)。"
        soup = render(source)
        self.assertIsNotNone(soup.select_one("h2 span.arithmatex"))
        self.assertEqual(len(soup.select("span.arithmatex")), 3)
        self.assertIn(r"a\neq0", soup.get_text())
        self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_single_line_and_adjacent_display_in_quotes(self):
        for slash in ("\\", "\\\\"):
            with self.subTest(slash=slash):
                source = f"> Then {slash}[ ax-ay=0 {slash}] {slash}[ a(x-y)=0. {slash}]\n"
                soup = render(source)
                quote = soup.select_one("blockquote")
                self.assertEqual(len(quote.select("pre.arithmatex")), 2)
                self.assertIn("Then", quote.get_text())
                self.assertEqual(normalize(normalize(source)), normalize(source))
        soup = render(r"前文 \\[x=y\\] 後文")
        self.assertEqual(len(soup.select("pre.arithmatex")), 1)
        self.assertIn("前文", soup.get_text())
        self.assertIn("後文", soup.get_text())

    def test_double_escaped_multiline_display(self):
        for prefix in ("", "> "):
            source = "\n".join(prefix+line for line in ("前文", r"\\[", r"\boxed{x=y}", r"\\]", "後文"))
            self.assertEqual(len(render(source).select("pre.arithmatex")), 1)
            self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_escaped_math_keeps_inline_code_literal(self):
        for source in (
            r"`\\(a\\) \\[x=y\\]`",
            r"``code ` \\(a\\) \\[x=y\\]``",
            "`example\n" + r"\\[" + "\nx=1\n" + r"\\]" + "\n`",
            "```text\n" + r"\\(a\\) \\[x=y\\]" + "\n```\n",
            "    " + r"\\(a\\) \\[x=y\\]",
        ):
            with self.subTest(source=source):
                self.assertEqual(normalize(source), source)
                self.assertFalse(render(source).select(".arithmatex"))
        source = r"`\\(literal\\)`，真公式 \\(a\\)。"
        soup = render(source)
        self.assertEqual(len(soup.select("span.arithmatex")), 1)
        self.assertIn(r"\\(literal\\)", soup.select_one("code").get_text())

    def test_tex_body_row_breaks_and_paths_not_unescaped(self):
        tex = r"\begin{matrix}1&2\\3&4\end{matrix}"
        source = r"\\[" + tex + r"\\]"
        self.assertIn(tex, render(source).select_one("pre.arithmatex").get_text())
        self.assertEqual(normalize(normalize(source)), normalize(source))
        for source in (r"C:\\notes\\folder", r"\\server\share", r"\\\(x\\\)", r"\\(x\)", r"\\[ \\]", r"\\(x"):
            self.assertEqual(normalize(source), source)

    def test_escaped_math_in_list_continuations_and_marker_line(self):
        for source in (
            "1. 項目\n\n   " + r"\\[x=y\\]" + "\n\n   後文 " + r"\\(x\\)",
            r"1. 項目 \\[x=y\\] 結尾",
            r"1. \\[x=y\\]",
            "1. 項目\n\n   " + r"\\[" + "\n   x=y\n   " + r"\\]",
        ):
            with self.subTest(source=source):
                self.assertIsNotNone(render(source).select_one("li pre.arithmatex"))
                self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_escaped_display_crlf_and_no_final_newline(self):
        source = "> 前文\r\n> " + r"\\[x=y\\]"
        result = normalize(source)
        self.assertNotIn("\n", result.replace("\r\n", ""))
        self.assertFalse(result.endswith("\n"))
        self.assertEqual(normalize(result), result)
        self.assertEqual(len(render(source).select("blockquote pre.arithmatex")), 1)

    def test_entire_zero_product_danger_block(self):
        from tools.admonition_title_hook import on_page_markdown as normalize_titles
        path = Path(__file__).resolve().parents[1] / "docs/md/115-1/離散/L03.md"
        if not path.exists():
            self.skipTest("Local note is not available")
        source = path.read_text(encoding="utf8")
        marker = "/// danger|Zero-Product Property"
        if marker not in source:
            self.skipTest("Local Zero-Product block is not available")
        start = source.index(marker)
        end = source.index("\n///", start+len(marker))
        block = source[start:end+4]
        html = markdown.markdown(normalize_titles(normalize(block),page=None,config=None,files=None),
                                 extensions=["admonition","nl2br","pymdownx.superfences","pymdownx.arithmatex"],
                                 extension_configs={"pymdownx.arithmatex":{"generic":True,"block_tag":"pre"}})
        danger = BeautifulSoup(html,"html.parser").select_one(".admonition.danger")
        self.assertIsNotNone(danger.select_one("h2 span.arithmatex"))
        self.assertEqual(len(danger.select("pre.arithmatex")),13)
        self.assertEqual(len(danger.select("blockquote pre.arithmatex")),2)
        self.assertEqual(len(danger.select("span.arithmatex")),19)
        self.assertIn("Phase A",danger.select_one("code").get_text())
        self.assertEqual(path.read_text(encoding="utf8"),source)

    def test_preview_note_renders_without_source_changes(self):
        path = Path(__file__).resolve().parents[1] / "docs/md/115-1/離散/L03.md"
        if not path.exists():
            self.skipTest("Local preview note is not available")
        source = path.read_text(encoding="utf-8")
        soup = render(source)
        quote = next(q for q in soup.find_all("blockquote") if "隨便剩下多少" in q.get_text())
        self.assertIn(r"\boxed{0,1,2,\ldots,b-1}", quote.select_one(".arithmatex").get_text())
        self.assertEqual(path.read_text(encoding="utf-8"), source)


if __name__ == "__main__":
    unittest.main()
