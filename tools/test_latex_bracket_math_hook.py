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
    def test_indented_aligned_rows_preserve_dollar_boundaries(self):
        formula = (
            "$$\n\\begin{aligned}\n"
            "1&=28-27\\\\\n"
            " &=28-[111-3(28)]\\\\\n"
            " &=4(28)-111\\\\\n"
            " &=4[250-2(111)]-111\\\\\n"
            " &=4(250)-9(111).\n"
            "\\end{aligned}\n$$"
        )
        source = formula + "\n\nVerification.\n\n$$\n7a-5b=1\n$$\n"
        self.assertEqual(normalize(source), source)
        blocks = render(source).select('pre.arithmatex')
        self.assertEqual(len(blocks), 2)
        self.assertIn('4[250-2(111)]', blocks[0].get_text())
        self.assertEqual(blocks[0].get_text().count('\\\\'), 4)
        self.assertIn('7a-5b=1', blocks[1].get_text())
        self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_aligned_indentation_stays_within_quote_container(self):
        source = "> $$\n> \\begin{aligned}\n> x&=1\\\\\n>     &=2\n> \\end{aligned}\n> $$\n"
        self.assertEqual(len(render(source).select('blockquote pre.arithmatex')), 1)
        crossed = "> $$\n> \\begin{aligned}\n  &=2\n> \\end{aligned}\n> $$\n"
        self.assertEqual(normalize(crossed), crossed)

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

    def test_gpt_escaped_product_lower_limit(self):
        tex = r"\boxed{p\mid\prod\_{i=1}^{n}a_i\implies\exists i,\ p\mid a_i}"
        expected = tex.replace(r"\prod\_", r"\prod_")
        for opening, closing in ((r"\[", r"\]"), (r"\\[", r"\\]"), (r"\(", r"\)")):
            source = opening + tex + closing
            with self.subTest(opening=opening):
                self.assertIn(expected, render(source).select_one(".arithmatex").get_text())
                self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_operator_repair_does_not_unescape_other_tex_or_code(self):
        for source in (r"`\\[\prod\_{i=1}^n a_i\\]`",
                       "```tex\n" + r"\prod\_{i=1}^n a_i" + "\n```\n",
                       r"outside \prod\_{i=1}^n", r"\[x\_i+\text{file\_name}\]",
                       r"\[\prod_{i=1}^n a_i\]", r"\[\\prod\_{i=1}^n\]"):
            with self.subTest(source=source):
                if source.startswith(r"\["):
                    self.assertIn(source[2:-2], render(source).select_one(".arithmatex").get_text())
                else:
                    self.assertEqual(normalize(source), source)
        for operator in ("prod", "sum", "coprod"):
            source = r"\[" + "\\" + operator + r"\_{i=1}^n a_i\]"
            self.assertIn("\\" + operator + "_{i=1}", normalize(source))

    def test_pasted_escaped_less_than_in_inline_and_display_math(self):
        source = r"這裡 \\(p_1\<p_2<\cdots\<p_k\\)，各 \\(a_i\\) 為正整數。"
        soup = render(source)
        self.assertEqual(len(soup.select("span.arithmatex")), 2)
        self.assertIn(r"p_1<p_2<\cdots<p_k", soup.select_one(".arithmatex").get_text())
        self.assertIn("為正整數。", soup.get_text())
        for tex in (r"m=ab,\qquad 1\<a\<m,\quad1\<b\<m",
                    r"a\>b\quad x\leq y\quad p\mid n"):
            for opening, closing in ((r"\[", r"\]"), (r"\\[", r"\\]")):
                expression = opening + tex + closing
                self.assertIn(tex.replace(r"\<", "<"), render(expression).select_one(".arithmatex").get_text())
                self.assertEqual(normalize(normalize(expression)), normalize(expression))

    def test_escaped_less_than_preserves_code_and_row_breaks(self):
        for source in (r"`\\(p_1\<p_2\\)`", "```tex\n" + r"\(a\<b\)" + "\n```\n",
                       r"outside a\<b", "    " + r"\(a\<b\)"):
            self.assertEqual(normalize(source), source)
        tex = r"\begin{matrix}a\\<b\end{matrix}"
        self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())

    def test_pasted_boxed_aligned_cartesian_sets(self):
        ab = r"\boxed{ \begin{aligned} A\times B=\\{&(2,4),(2,5),\\\ &(3,4),(3,5),\\\ &(4,4),(4,5)\\} \end{aligned} }"
        ba = r"\boxed{ \begin{aligned} B\times A=\\{&(4,2),(4,3),(4,4),\\\ &(5,2),(5,3),(5,4)\\} \end{aligned} }"
        source = r"我們先算 \\(A\times B\\)：\\[ " + ab + r" \\]再將順序顛倒，計算 \\(B\times A\\)：\\[ " + ba + r" \\]"
        soup = render(source)
        formulas = soup.select("pre.arithmatex")
        self.assertEqual(len(formulas), 2)
        self.assertEqual(len(soup.select("span.arithmatex")), 2)
        for node, tex in zip(formulas, (ab, ba)):
            expected = tex.replace(r"\\{", r"\{").replace(r"\\}", r"\}")
            self.assertIn(expected, node.get_text())
            self.assertEqual(node.get_text().count(r"\\\ &"), tex.count(r"\\\ &"))
        self.assertEqual(normalize(normalize(source)), normalize(source))
        self.assertIn("再將順序顛倒", soup.get_text())

    def test_pasted_set_braces_preserve_code_and_real_row_breaks(self):
        for source in (r"`\\[A=\\{1,2\\}\\]`", "```tex\n" + r"A=\\{1,2\\}" + "\n```\n",
                       r"outside \\{1,2\\}", "    " + r"\(A=\\{1,2\\}\)"):
            self.assertEqual(normalize(source), source)
        for tex in (r"\begin{matrix}a\\{b}&c\end{matrix}", r"A=\{1,2\}",
                    r"\begin{matrix}a&b\\c&d\end{matrix}", r"\\\{literal\\\}"):
            self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())
        source = r"\(A=\\{1,2\\}, B=\\{3,4\\}\)"
        self.assertIn(r"A=\{1,2\}, B=\{3,4\}", render(source).select_one(".arithmatex").get_text())

    def test_nested_pasted_power_set_braces(self):
        tex = r"A=\mathcal P(B) =\\{\varnothing,\\{1\\},\\{2\\},\\{1,2\\}\\}"
        expected = r"A=\mathcal P(B) =\{\varnothing,\{1\},\{2\},\{1,2\}\}"
        for opening, closing in ((r"\\[", r"\\]"), (r"\[", r"\]"), (r"\\(", r"\\)")):
            source = opening + tex + closing
            self.assertIn(expected, render(source).select_one(".arithmatex").get_text())
            self.assertEqual(normalize(normalize(source)), normalize(source))
        deep = r"S=\\{\\{\\{1\\}\\},\\{2\\}\\}"
        self.assertIn(deep.replace(r"\\{", r"\{").replace(r"\\}", r"\}"),
                      render(r"\[" + deep + r"\]").select_one(".arithmatex").get_text())

    def test_unbalanced_nested_braces_and_code_remain_literal(self):
        for tex in (r"\\{1,\\{2\\}", r"\\}\\{1\\}", r"\\{1\\}\\}",
                    r"\begin{matrix}a\\{b}&c\end{matrix}"):
            self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())
        source = "```tex\n" + r"\\{\varnothing,\\{1\\}\\}" + "\n```\n"
        self.assertEqual(normalize(source), source)

    def test_pasted_function_count_hash(self):
        for tex, expected in (
            (r"\\#(A\to B)=4^3=64", r"\#(A\to B)=4^3=64"),
            (r"\\#(B\to A)=3^4=81", r"\#(B\to A)=3^4=81"),
            (r"\\# (A\to B)", r"\# (A\to B)"),
        ):
            self.assertTrue(tex.startswith(chr(92) * 2 + "#"))
            for opening, closing in ((r"\\[", r"\\]"), (r"\[", r"\]"), (r"\\(", r"\\)")):
                source = opening + tex + closing
                self.assertIn(expected, render(source).select_one(".arithmatex").get_text())
                self.assertNotIn(chr(92) * 2 + "#", normalize(source))
                self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_count_hash_preserves_code_and_real_row_breaks(self):
        for tex in (r"\#(A\to B)", r"\\\#(A\to B)",
                    r"\begin{aligned}x&=1\\\#(A\to B)&=64\end{aligned}"):
            self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())
        for source in (r"`\\[\\#(A\to B)\\]`", "```tex\n" + r"\\#(A\to B)" + "\n```\n",
                       "    " + r"\(\\#(A\to B)\)", r"outside \\#(A to B)"):
            self.assertEqual(normalize(source), source)

    def test_underbrace_escaped_annotation_subscript(self):
        for tex, expected in (
            (r"\underbrace{n\times n\times\cdots\times n}\_{m\text{ 次}} =\boxed{n^m}",
             r"\underbrace{n\times n\times\cdots\times n}_{m\text{ 次}} =\boxed{n^m}"),
            (r"\underbrace{\text{a\_b}+\{x\}} \_{m}",
             r"\underbrace{\text{a\_b}+\{x\}} _{m}"),
            (r"\underbrace{\underbrace{x}\_{i}+y}\_{m}",
             r"\underbrace{\underbrace{x}_{i}+y}_{m}"),
        ):
            source = r"\\[" + tex + r"\\]"
            self.assertIn(expected, render(source).select_one(".arithmatex").get_text())
            self.assertEqual(normalize(normalize(source)), normalize(source))
        for tex in (r"x\_{i}", r"\text{file\_name}", r"\underbrace{x}_{i}",
                    r"\underbrace{x}\\\_{i}", r"\underbrace{x\_{i}"):
            self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())

    def test_labeled_count_hash_and_literal_code(self):
        for label, power in (("Functions", "n^m"), ("Relations", "2^{mn}"),
                             ("Injective Functions", r"\frac{2!}{0!}"), ("All Functions", "2^2"),
                             ("Injective", "0"), ("Other", "1")):
            tex = r"\boxed{\\#\text{ " + label + r"}(A\to B)=" + power + "}"
            expected = tex.replace(chr(92) * 2 + "#", chr(92) + "#")
            for opening, closing in ((r"\\[", r"\\]"), (r"\(", r"\)")):
                self.assertIn(expected, render(opening + tex + closing).select_one(".arithmatex").get_text())
        for tex in (r"\\\#\text{ Functions}(A\to B)",
                    r"\#\text{ Relations}(A\to B)"):
            self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())
        for tex in (r"\underbrace{x}\_{m}", r"\\#\text{ Functions}(A\to B)"):
            for source in ("`" + tex + "`", "```tex\n" + tex + "\n```\n", "    " + tex):
                self.assertEqual(normalize(source), source)

    def test_hash_repair_without_label_or_argument_whitelist(self):
        for tex in (r"\\#x", r"\\#\text{Injective Functions}=0",
                    r"\\#\text{All Functions}=2^2=4", r"\\#\text{未來的新標籤}", r"\\#"):
            expected = tex.replace(chr(92) * 2 + "#", chr(92) + "#")
            for opening, closing in ((r"\\[", r"\\]"), (r"\\(", r"\\)")):
                source = opening + tex + closing
                self.assertIn(expected, render(source).select_one(".arithmatex").get_text())
                self.assertEqual(normalize(normalize(source)), normalize(source))
        for slashes in (1, 3, 4, 5):
            tex = chr(92) * slashes + r"#\text{Injective Functions}"
            self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())

    def test_injective_aligned_and_cases_preserve_row_breaks(self):
        texes = (
            r"\begin{aligned} \\#\text{Injective Functions} &=n(n-1)(n-2)\cdots(n-m+1)\\\ &=\boxed{\frac{n!}{(n-m)!}}\\\ &=P(n,m) \end{aligned}",
            r"\boxed{ \\#\text{Injective}(A\to B)= \begin{cases} \dfrac{n!}{(n-m)!},&m\le n\\\ 0,&m>n \end{cases} }",
        )
        for tex in texes:
            expected = tex.replace(chr(92) * 2 + "#", chr(92) + "#")
            source = r"\\[" + tex + r"\\]"
            self.assertIn(expected, render(source).select_one(".arithmatex").get_text())
            self.assertEqual(normalize(normalize(source)), normalize(source))
        for source in (r"`\\#\text{Injective}`", "```tex\n" + texes[0] + "\n```\n",
                       "    " + texes[1], r"outside \\#\text{All Functions}"):
            self.assertEqual(normalize(source), source)

    def test_tex_body_row_breaks_and_paths_not_unescaped(self):
        tex = r"\begin{matrix}1&2\\3&4\end{matrix}"
        source = r"\\[" + tex + r"\\]"
        self.assertIn(tex, render(source).select_one("pre.arithmatex").get_text())
        self.assertEqual(normalize(normalize(source)), normalize(source))
        for source in (r"C:\\notes\\folder", r"\\server\share", r"\\\(x\\\)", r"\\(x\)", r"\\[ \\]", r"\\(x"):
            self.assertEqual(normalize(source), source)

    def test_pasted_aligned_equivalence_spacing(self):
        for left, middle, right in (
            (r"(x,y)\in A\times(B\cap C)", r"x\in A\land y\in B\land y\in C", r"(x,y)\in(A\times B)\cap(A\times C)"),
            (r"(x,y)\in A\times(B\cup C)", r"x\in A\land(y\in B\lor y\in C)", r"(x,y)\in(A\times B)\cup(A\times C)"),
            (r"(x,y)\in(A\cap B)\times C", r"x\in A\land x\in B\land y\in C", r"(x,y)\in(A\times C)\cap(B\times C)"),
            (r"(x,y)\in(A\cup B)\times C", r"(x\in A\lor x\in B)\land y\in C", r"(x,y)\in(A\times C)\cup(B\times C)"),
        ):
            tex = r"\begin{aligned} &" + left + r"\\\ \iff\\;&" + middle + r"\\\ \iff\\;&" + right + r". \end{aligned}"
            expected = tex.replace(r"\iff\\;", r"\iff\;")
            for opening, closing in ((r"\\[", r"\\]"), (r"\[", r"\]"), (r"\\(", r"\\)")):
                source = opening + tex + closing
                actual = render(source).select_one(".arithmatex").get_text()
                self.assertIn(expected, actual)
                self.assertEqual(actual.count(r"\\\ "), 2)
                self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_equivalence_spacing_preserves_other_tex_and_code(self):
        for tex in (
            r"\begin{aligned}&A\\\ \iff\;&B\end{aligned}",
            r"\begin{aligned}&A\\[6pt]\iff\;&B\end{aligned}",
            r"\begin{aligned}&A\\\ \iff\\\;&B\end{aligned}",
            r"\begin{aligned}&A\\\ \iff\\;B\end{aligned}",
            r"\begin{aligned}&A\iff\\;&B\end{aligned}",
            r"\begin{aligned}&A\\; &B\end{aligned}",
            r"\begin{aligned}&A\\\ \iff\\;&B",
            r"\begin{matrix}&A\\\ \iff\\;&B\end{matrix}",
            r"A\\\ \iff\\;&B",
        ):
            self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())
        tex = r"\begin{aligned}&A\\\ \iff\\;&B\end{aligned}"
        for source in ("`" + r"\\[" + tex + r"\\]`", "```tex\n" + tex + "\n```\n",
                       "    " + r"\[" + tex + r"\]", "outside " + tex):
            self.assertEqual(normalize(source), source)

    def test_pasted_aligned_numeric_row_gaps(self):
        for gap in ("5pt", "6pt", ".5em", "-1ex", "+2mm"):
            tex = (r"\begin{aligned}&A\\\\[" + gap + r"] \iff\\;&B"
                   + r"\\\ &\quad C\\\\[" + gap + r"]\iff\\;&D\end{aligned}")
            expected = tex.replace(r"\\\\[", r"\\[").replace(r"\iff\\;", r"\iff\;")
            for opening, closing in ((r"\\[", r"\\]"), (r"\\(", r"\\)")):
                source = opening + tex + closing
                actual = render(source).select_one(".arithmatex").get_text()
                self.assertIn(expected, actual)
                self.assertEqual(actual.count("[" + gap + "]"), 2)
                self.assertIn(r"\\\ &\quad C", actual)
                self.assertEqual(normalize(normalize(source)), normalize(source))
        tex = r"\begin{aligned}&A\\[5pt] \iff\\;&B\end{aligned}"
        self.assertIn(tex.replace(r"\iff\\;", r"\iff\;"),
                      render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())

    def test_row_gap_repair_is_scoped_to_pasted_aligned_math(self):
        for tex in (
            r"\begin{matrix}A\\\\[5pt]B\end{matrix}",
            r"\begin{aligned}A\\\\[unknown]B\end{aligned}",
            r"\begin{aligned}A\\\\[5]B\end{aligned}",
            r"\begin{aligned}A\\\\[5pt]B",
        ):
            self.assertIn(tex, render(r"\\[" + tex + r"\\]").select_one(".arithmatex").get_text())
        for count in (2, 3, 5, 6):
            tex = r"\begin{aligned}A" + chr(92) * count + r"[5pt]B\end{aligned}"
            self.assertIn(tex, render(r"\\[" + tex + r"\\]").select_one(".arithmatex").get_text())
        tex = r"\begin{aligned}A\\\\[5pt]B\end{aligned}"
        self.assertIn(tex, render(r"\[" + tex + r"\]").select_one(".arithmatex").get_text())
        for source in (r"`\\[" + tex + r"\\]`", "```tex\n" + tex + "\n```\n",
                       "    " + r"\\[" + tex + r"\\]", "outside " + tex):
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
        self.assertIsNotNone(danger.select_one("h2 span.arithmatex, h3 span.arithmatex"))
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
