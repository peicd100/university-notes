from __future__ import annotations

import re
from typing import Any


_FENCE_RE = re.compile(r"^(?P<indent>[ ]{0,3})(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")


def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    lines = markdown.splitlines(keepends=True)
    converted_lines: list[str] = []
    index = 0
    open_fence: tuple[str, int] | None = None

    while index < len(lines):
        content, newline = _split_line_ending(lines[index])

        if open_fence is not None:
            converted_lines.append(lines[index])
            if _is_closing_fence(content, *open_fence):
                open_fence = None
            index += 1
            continue

        opening_fence = _parse_opening_fence(content)
        if opening_fence is not None:
            open_fence = opening_fence
            converted_lines.append(lines[index])
            index += 1
            continue

        if content.strip() != "[":
            converted_lines.append(lines[index])
            index += 1
            continue

        closing_index = _find_closing_bracket(lines, index + 1)
        if closing_index is None:
            converted_lines.append(lines[index])
            index += 1
            continue

        open_indent = _leading_spaces(content)
        close_content, close_newline = _split_line_ending(lines[closing_index])
        close_indent = _leading_spaces(close_content)

        converted_lines.append(f"{open_indent}\\[{newline}")
        for inner_index in range(index + 1, closing_index):
            converted_lines.append(lines[inner_index])
        converted_lines.append(f"{close_indent}\\]{close_newline}")
        index = closing_index + 1

    return "".join(converted_lines)


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def _parse_opening_fence(line: str) -> tuple[str, int] | None:
    match = _FENCE_RE.match(line)
    if match is None:
        return None
    fence = match.group("fence")
    return fence[0], len(fence)


def _is_closing_fence(line: str, fence_char: str, fence_len: int) -> bool:
    match = _FENCE_RE.match(line)
    if match is None:
        return False
    fence = match.group("fence")
    return fence[0] == fence_char and len(fence) >= fence_len and not match.group("rest").strip()


def _find_closing_bracket(lines: list[str], start_index: int) -> int | None:
    saw_non_empty_content = False

    for index in range(start_index, len(lines)):
        content, _ = _split_line_ending(lines[index])
        stripped = content.strip()

        if stripped == "]":
            return index if saw_non_empty_content else None

        if not stripped:
            continue

        saw_non_empty_content = True

    return None


def _leading_spaces(text: str) -> str:
    return text[: len(text) - len(text.lstrip(" "))]
