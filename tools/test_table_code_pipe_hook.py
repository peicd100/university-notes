import unittest

import markdown
from bs4 import BeautifulSoup
from tools.table_code_pipe_hook import on_page_content


def repair(html):
    return on_page_content(html, page=None, config=None, files=None)


class TableCodePipeTests(unittest.TestCase):
    def test_markdown_table_operators(self):
        source = '| Operator | Meaning |\n|---|---|\n| `! && \\|\\|` | Logical |\n| `~ & \\| ^` | Bitwise |\n| `& ~& \\| ~\\|` | Reduction |'
        html = markdown.markdown(source, extensions=['tables'])
        soup = BeautifulSoup(repair(html), 'html.parser')
        self.assertEqual([c.get_text() for c in soup.select('td code')], ['! && ||', '~ & | ^', '& ~& | ~|'])
        self.assertTrue(all(len(row.select('td')) == 2 for row in soup.select('tbody tr')))
        self.assertEqual(repair(repair(html)), repair(html))

    def test_only_inline_table_code_changes(self):
        before = '<p><code>\\|</code></p><table><tr><td>\\|<pre><code>\\|</code></pre><code>\\|</code></td></tr></table>'
        self.assertEqual(repair(before), before.replace('<code>\\|</code></td>', '<code>|</code></td>'))

    def test_preserve_explicit_double_backslashes_and_entities(self):
        html = '<table><tr><th><code>\\\\| &amp; \\| &lt;</code></th></tr></table>'
        self.assertEqual(repair(html), html.replace('&amp; \\|', '&amp; |'))

    def test_offsets_and_markup_preserved(self):
        html = '<TABLE>\r\n<TR><TD><code class="x">中文 \\|<span>\\|</span></code></TD></TR>\r\n</TABLE>'
        self.assertEqual(repair(html), html.replace('\\|', '|'))
        self.assertEqual(repair('<!-- <td><code>\\|</code></td> -->'), '<!-- <td><code>\\|</code></td> -->')


if __name__ == '__main__':
    unittest.main()
