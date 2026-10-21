import unittest
from types import SimpleNamespace

import markdown
from bs4 import BeautifulSoup
from tools.verilog_fence_hook import on_page_markdown


def normalize(text, src='md/115-1/\u786c\u9ad4\u63cf\u8ff0\u8a9e\u8a00/L03.md'):
    return on_page_markdown(text, page=SimpleNamespace(file=SimpleNamespace(src_uri=src)), config=None, files=None)


class VerilogFenceTests(unittest.TestCase):
    def test_module_and_keyword_highlighting(self):
        source = '```\nmodule and2(input a, output y);\nassign y=a;\nendmodule\n```\n'
        output = normalize(source)
        self.assertEqual(output, source.replace('```\n', '```verilog\n', 1))
        self.assertEqual(normalize(output), output)
        html = markdown.markdown(output, extensions=['pymdownx.superfences'])
        soup = BeautifulSoup(html, 'html.parser')
        self.assertTrue(soup.select('.highlight .k'))
        self.assertEqual(soup.select_one('code').get_text().strip(), source.split('\n', 1)[1].rsplit('```', 1)[0].strip())

    def test_fragments(self):
        for code in ['assign y = a & b;', 'always @(posedge clk) q <= d;', 'initial begin\na=0;\nend', 'reg a, b;\nwire y;', '$display("hello");']:
            with self.subTest(code=code):
                self.assertTrue(normalize('```\n'+code+'\n```').startswith('```verilog\n'))

    def test_preserve_languages_other_notes_and_ambiguous_text(self):
        for language in ['text', 'python', 'bash', 'verilog', '{.text}']:
            source = '```'+language+'\nmodule m;\nendmodule\n```'
            self.assertEqual(normalize(source), source)
        source = '```\nmodule m;\nendmodule\n```'
        self.assertEqual(normalize(source, 'md/other/L03.md'), source)
        for code in ['a = b + c;', 'print("module m; endmodule")', '// assign y = x;', '/* initial begin */', 'O E O E', 'module is a word']:
            source = '```\n'+code+'\n```'
            self.assertEqual(normalize(source), source)

    def test_quotes_tildes_crlf_and_incomplete_fences(self):
        for prefix in ['', '> ', '> > ', '   ']:
            source = prefix+'~~~\r\n'+prefix+'module m;\r\n'+prefix+'endmodule\r\n'+prefix+'~~~~\r\n'
            self.assertEqual(normalize(source), source.replace('~~~\r\n', '~~~verilog\r\n', 1))
        source = '```\nmodule m;\nendmodule\n'
        self.assertEqual(normalize(source), source)

    def test_nested_fences_remain_code(self):
        source = '````text\n```\nmodule m;\nendmodule\n```\n````\n'
        self.assertEqual(normalize(source), source)


if __name__ == '__main__':
    unittest.main()
