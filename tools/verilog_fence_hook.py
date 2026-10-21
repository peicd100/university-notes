"""Add render-only language hints to unlabelled HDL code fences."""
from __future__ import annotations

import re
from typing import Any


_FENCE = re.compile(r"^(?P<prefix>(?:[ ]{0,3}>[ \t]?)*[ ]{0,3})(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)$")
_COMMENTS = re.compile(r'"(?:\\.|[^"\\])*"|/\*.*?\*/|//[^\n]*', re.S)
_HDL = re.compile(
    r"^\s*(?:"
    r"assign\s+[A-Za-z_][\w$]*(?:\s*\[[^\]\n]+\])?\s*="
    r"|always\s*@\s*\("
    r"|always_(?:comb|ff|latch)\b"
    r"|initial\s+begin\b"
    r"|(?:reg|wire)\s+(?:signed\s+)?(?:\[[^\]\n]+\]\s*)?[A-Za-z_][\w$]*(?:\s*,\s*[A-Za-z_][\w$]*)*\s*;"
    r"|\$(?:display|monitor|finish|stop|dumpfile|dumpvars)\s*(?:\(|;)"
    r")", re.M
)


def _is_verilog(code: str) -> bool:
    # Ignore signatures pasted in comments or strings.
    code = _COMMENTS.sub(' ', code)
    return bool(
        re.search(r"^\s*module\s+[A-Za-z_][\w$]*\b", code, re.M)
        and re.search(r"^\s*endmodule\b", code, re.M)
        or _HDL.search(code)
    )


def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    src = str(getattr(getattr(page, 'file', None), 'src_uri', '')).replace('\\', '/')
    if '\u786c\u9ad4\u63cf\u8ff0\u8a9e\u8a00' not in src.split('/'):
        return markdown
    lines = markdown.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        opening = _FENCE.match(lines[index].rstrip('\r\n'))
        if opening is None:
            index += 1
            continue
        end = index + 1
        code = []
        while end < len(lines):
            line = lines[end].rstrip('\r\n')
            close = _FENCE.match(line)
            if (close and close['prefix'] == opening['prefix']
                    and close['fence'][0] == opening['fence'][0]
                    and len(close['fence']) >= len(opening['fence'])
                    and not close['info'].strip()):
                break
            prefix = opening['prefix']
            code.append(lines[end][len(prefix):] if prefix and lines[end].startswith(prefix) else lines[end])
            end += 1
        if end == len(lines):
            break  # An incomplete fence must remain literal.
        if not opening['info'].strip() and _is_verilog(''.join(code)):
            insertion = len(opening['prefix']) + len(opening['fence'])
            lines[index] = lines[index][:insertion] + 'verilog' + lines[index][insertion:]
        index = end + 1
    return ''.join(lines)
