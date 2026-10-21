"""Remove Markdown pipe escapes from rendered inline code in table cells."""
from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Any


_PIPE_ESCAPE = re.compile(r"(?<!\\)\\\|")


class _TableCodeParser(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.offsets = [0]
        for match in re.finditer('\n', source):
            self.offsets.append(match.end())
        self.depths = dict.fromkeys(('td', 'th', 'code', 'pre', 'script', 'style'), 0)
        self.edits: list[tuple[int, int, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.depths:
            self.depths[tag] += 1

    def handle_endtag(self, tag):
        if tag in self.depths:
            self.depths[tag] = max(0, self.depths[tag] - 1)

    def handle_data(self, data):
        d = self.depths
        if d['code'] and (d['td'] or d['th']) and not (d['pre'] or d['script'] or d['style']):
            repaired = _PIPE_ESCAPE.sub('|', data)
            if repaired != data:
                line, column = self.getpos()
                start = self.offsets[line - 1] + column
                self.edits.append((start, start + len(data), repaired))


def on_page_content(html: str, /, *, page: Any, config: Any, files: Any) -> str:
    if '\\|' not in html:
        return html
    parser = _TableCodeParser(html)
    parser.feed(html)
    parser.close()
    for start, end, replacement in reversed(parser.edits):
        html = html[:start] + replacement + html[end:]
    return html
