"""Point-source mapping regressions; never starts an editor."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode

from tools import source_jump_hook as jump
from tools.latex_bracket_math_hook import on_page_markdown


def record(source):
    return jump._build_page_record(source, SimpleNamespace(
        src_uri="point.md", dest_uri="point.html", abs_src_path="C:/notes/point.md"))


def lookup(page, selection="", container="", prefix="", **kwargs):
    context = dict(heading_path="", prev_block="", next_block="", block_tag="p",
                   block_index=None, section_index=None, block_progress=None)
    context.update(kwargs)
    return jump._locate_selection(page, selection, container, prefix, **context)


class SourceJumpCaretTests(unittest.TestCase):
    def assert_position(self, result, source, offset, precision="caret"):
        line = source.count("\n", 0, offset) + 1
        line_start = source.rfind("\n", 0, offset) + 1
        column = len(source[line_start:offset].encode("utf-16-le")) // 2 + 1
        self.assertTrue(result["ok"])
        self.assertEqual((result["line"], result["column"]), (line, column))
        self.assertEqual(result["precision"], precision)
        self.assertTrue(result["uri"].endswith(f":{line}:{column}"))

    def test_plain_bold_link_and_code_positions(self):
        source = "# Test\n\n前文😀 **粗體文字**，接著 [連結文字](https://example.com)，再 `inline_code`。\n"
        page = record(source)
        for anchor, caret in (("前文😀 ", 3), ("粗體文字", 2), ("連結文字", 3), ("inline_code", 7)):
            with self.subTest(anchor=anchor):
                self.assert_position(lookup(page, anchor, page.blocks[-1].visible_text, caret_offset=caret),
                                     source, source.index(anchor) + caret)

    def test_link_destination_is_not_visible_following_text(self):
        source = "[same](same) same tail\n"
        self.assert_position(lookup(record(source), " same tail", "same same tail", caret_offset=4),
                             source, source.index(" same tail") + 4)

    def test_emoji_utf16_and_caret_at_text_end(self):
        source = "😀ab😀末尾\n"
        for caret in range(1, len(source.strip()) + 1):
            self.assert_position(lookup(record(source), source.strip(), source.strip(), caret_offset=caret),
                                 source, caret)

    def test_end_of_formatted_text_is_before_closing_markers(self):
        source = "前 **重點** 後\n"
        self.assert_position(lookup(record(source), "重點", "前 重點 後", caret_offset=2),
                             source, source.index("重點") + 2)

    def test_decoded_entity_anchor_uses_visible_mapping(self):
        source = "before &amp; after\n"
        self.assert_position(lookup(record(source), "before & after", "before & after", caret_offset=9),
                             source, source.index("after"))

    def test_repeated_text_uses_prefix_within_block(self):
        source = "同文 同文 同文\n"
        self.assert_position(lookup(record(source), "同文", source, "同文 同文 ", caret_offset=1),
                             source, source.rfind("同文") + 1)

    def test_long_repeated_paragraph_uses_bounded_prefix_and_full_length(self):
        source = "重複 " * 1200 + "\n"
        anchor = source[2100:2180]
        self.assert_position(lookup(record(source), anchor, source[:2000], source[:500],
                                    caret_offset=40, point_prefix_length=2099), source, 2140)

    def test_repeated_paragraphs_use_heading_context(self):
        source = "# First\n\n同樣文字\n\n# Second\n\n同樣文字\n"
        self.assert_position(lookup(record(source), "同樣文字", "同樣文字", caret_offset=2,
                                    heading_path="Second", block_index=3), source, source.rfind("同樣文字") + 2)

    def test_multiline_and_crlf(self):
        for newline in ("\n", "\r\n"):
            source = newline.join(("開頭", "下一行😀文字", ""))
            self.assert_position(lookup(record(source), "下一行😀文字", "開頭 下一行😀文字", caret_offset=5),
                                 source, source.index("下一行") + 5)

    def test_out_of_bounds_caret_is_clamped(self):
        source = "abcdef\n"
        for value, offset in ((-20, 0), (100, 6)):
            self.assert_position(lookup(record(source), "abcdef", "abcdef", caret_offset=value), source, offset)

    def test_display_formula_start_after_render_normalization(self):
        source = "前文\n\n" + r"\\[ \boxed{\\#\text{Injective}=0} \\]" + "\n"
        raw_formula = source.splitlines()[2]
        normalized = on_page_markdown(raw_formula, page=None, config=None, files=None).strip()
        self.assert_position(lookup(record(source), container=normalized, math_source=normalized, block_tag="pre"),
                             source, source.index(chr(92) * 2 + "["), "formula")

    def test_inline_and_dollar_formula_starts(self):
        for formula in (r"\(A\times B\)", r"\\(A\times B\\)", "$A^2$", "$$A^2$$"):
            source = "前文 " + formula + " 後文\n"
            self.assert_position(lookup(record(source), container=source, math_source=formula, math_index=0),
                                 source, source.index(formula), "formula")

    def test_repeated_inline_formula_ordinal(self):
        formula = r"\(x=1\)"
        source = "first " + formula + " second " + formula + "\n"
        self.assert_position(lookup(record(source), container=source, math_source=formula, math_index=1),
                             source, source.rfind(formula), "formula")

    def test_formula_ignores_code_duplicates(self):
        formula = r"\[x=1\]"
        source = "```tex\n" + formula + "\n```\n\n`" + formula + "`\n\n" + formula + "\n"
        self.assert_position(lookup(record(source), container=formula, math_source=formula),
                             source, source.rfind(formula), "formula")

    def test_unknown_formula_and_missing_point_keep_block_fallback(self):
        source = "# Test\n\n段落文字\n"
        for kwargs in ({}, {"math_source": r"\[unknown\]"}):
            self.assert_position(lookup(record(source), container="段落文字", **kwargs),
                                 source, source.index("段落文字"), "block")

    def test_explicit_selection_behavior_unchanged(self):
        source = "開頭 **重點文字** 結束\n"
        self.assert_position(lookup(record(source), "重點文字", "開頭 重點文字 結束"),
                             source, source.index("重點文字"), "selection")

    def test_endpoint_forwards_point_and_formula_without_real_editor(self):
        source = "😀click here " + r"\(x=1\)" + "\n"
        page = record(source)
        for params, offset, precision in (
            ({"selection": "click here ", "caret_offset": "6"}, source.index("here"), "caret"),
            ({"selection": "", "math_source": r"\(x=1\)", "math_index": "0"}, source.index(r"\("), "formula"),
        ):
            query = {"page": "/point.html", "container": source, "action": "open", **params}
            statuses = []
            with patch.dict(jump._PAGE_INDEX, {"point.html": page}, clear=True), patch.object(jump, "_open_in_vscode", return_value=(True, "")) as editor:
                result = json.loads(b"".join(jump._handle_lookup_request(
                    {"QUERY_STRING": urlencode(query)}, lambda status, headers: statuses.append(status),
                    SimpleNamespace(mount_path="/"))))
            self.assertEqual(statuses, ["200 OK"])
            self.assert_position(result, source, offset, precision)
            editor.assert_called_once_with(page.abs_src_path, result["line"], result["column"])


if __name__ == "__main__":
    unittest.main()
