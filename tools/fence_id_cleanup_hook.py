from __future__ import annotations

import re
from typing import Any


_FENCE_WITH_BARE_ID_RE = re.compile(
    r'^(?P<indent>[ ]{0,3})(?P<fence>`{3,}|~{3,})(?P<space>\s*)(?P<info>[^\s`~]+)?(?P<suffix>.*\bid="[^"]*".*)$'
)


def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    cleaned_lines: list[str] = []

    for line in markdown.splitlines(keepends=True):
        newline = ""
        content = line
        if line.endswith("\r\n"):
            content = line[:-2]
            newline = "\r\n"
        elif line.endswith("\n"):
            content = line[:-1]
            newline = "\n"

        match = _FENCE_WITH_BARE_ID_RE.match(content)
        if not match:
            cleaned_lines.append(line)
            continue

        rebuilt = f"{match.group('indent')}{match.group('fence')}"
        info = match.group("info") or ""
        if info:
            rebuilt += f"{match.group('space')}{info}"
        cleaned_lines.append(rebuilt + newline)

    return "".join(cleaned_lines)
