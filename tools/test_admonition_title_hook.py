"""Regression tests for title-only slash danger blocks and existing syntax."""
import unittest

import markdown
from bs4 import BeautifulSoup

from tools.admonition_title_hook import on_page_markdown, parse_slash_admonition_start
from tools.source_jump_hook import _iter_admonition_spans


def normalize(source):
    return on_page_markdown(source, page=None, config=None, files=None)


def render(source):
    return BeautifulSoup(markdown.markdown(normalize(source), extensions=[
        'admonition', 'pymdownx.superfences', 'pymdownx.blocks.details',
    ]), 'html.parser')


class SlashDefaultDangerTests(unittest.TestCase):
    def test_requested_empty_block(self):
        source = '///早安\n///\n'
        self.assertEqual(normalize(source), '!!! danger "Danger | 早安"\n')
        self.assertEqual(str(render(source)), str(render('/// danger|早安\n///\n')))
        self.assertEqual(render(source).select_one('.admonition-title').text, 'Danger | 早安')

    def test_content_and_spacing(self):
        for opener in ('///早安', '/// 早安', '///Good morning', '///今天的重點 1'):
            with self.subTest(opener=opener):
                title = opener[3:].strip()
                source = opener + '\n第一段。\n\n- 項目\n///\n'
                soup = render(source)
                self.assertEqual(soup.select_one('.admonition-title').text, 'Danger | ' + title)
                self.assertEqual(soup.select_one('.danger li').text, '項目')
                self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_explicit_types_stay_explicit(self):
        for opener in ('/// note|早安', '///note|早安', '/// note "早安"'):
            self.assertEqual(render(opener+'\n內容\n///').select_one('.note .admonition-title').text, 'Note | 早安')
        self.assertEqual(render('///danger|早安\n///').select_one('.danger .admonition-title').text, 'Danger | 早安')
        self.assertEqual(render('///danger|Danger | 早安\n///').select_one('.admonition-title').text, 'Danger | 早安')

    def test_reserved_native_blocks_are_untouched(self):
        for opener in ('/// details|摺疊', '///details|摺疊', '/// details-note | 摺疊',
                       '/// details open', '/// html | div', '/// define', '/// definition',
                       '/// tab | 分頁', '/// custom|自訂'):
            source = opener+'\n內容\n///\n'
            self.assertEqual(normalize(source), source)
            self.assertIsNone(parse_slash_admonition_start(opener))
        self.assertIsNotNone(render('/// details | 摺疊\n內容\n///').select_one('details'))

    def test_code_and_indented_code_are_untouched(self):
        for source in ('```text\n///早安\n///\n```\n', '~~~\n///早安\n///\n~~~\n',
                       '    ///早安\n    ///\n'):
            self.assertEqual(normalize(source), source)

    def test_code_inside_block_does_not_close_block(self):
        source = '///早安\n```text\n///\n```\n後文\n///\n'
        soup = render(source)
        self.assertEqual(soup.select_one('.danger code').text.strip(), '///')
        self.assertIn('後文', soup.select_one('.danger').text)

    def test_unclosed_and_lone_closer_are_untouched(self):
        for source in ('///早安\n未結束', '///\n', '前文\n///\n'):
            self.assertEqual(normalize(source), source)

    def test_crlf_and_no_final_newline(self):
        result = normalize('///早安\r\n內容\r\n///')
        self.assertEqual(result, '!!! danger "Danger | 早安"\r\n    內容\r\n')

    def test_source_jump_sees_original_title_and_body(self):
        source = '前文\n\n///早安\n內容\n///\n'
        starts = [0]
        for line in source.splitlines(keepends=True):
            starts.append(starts[-1]+len(line))
        spans = _iter_admonition_spans(source, starts)
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual((span.type_name, span.title, span.start_line, span.end_line), ('danger', '早安', 3, 5))
        self.assertEqual(span.content_markdown.strip(), '內容')


if __name__ == '__main__':
    unittest.main()
