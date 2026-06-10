from __future__ import annotations

import re
from typing import Any

from mkdocs.plugins import event_priority


_TYPE_LABELS = {
    "new": "New",
    "settings": "Settings",
    "note": "Note",
    "abstract": "Abstract",
    "info": "Info",
    "tip": "Tip",
    "success": "Success",
    "question": "Question",
    "warning": "Warning",
    "failure": "Failure",
    "danger": "Danger",
    "bug": "Bug",
    "example": "Example",
    "quote": "Quote",
}
_TITLE_SEPARATOR = " | "

_ADMONITION_TITLE_RE = re.compile(
    r'^(?P<indent>[ \t]{0,3})(?P<marker>!!!|\?\?\?\+?)\s+'
    r'(?P<type>[A-Za-z0-9_-]+)(?P<space>[ \t]+)"(?P<title>[^"]*)"(?P<trailing>[ \t]*)$'
)
_SLASH_ADMONITION_START_RE = re.compile(
    r'^(?P<indent>[ \t]{0,3})///\s+'
    r'(?P<type>[A-Za-z0-9_-]+)'
    r'(?:(?:[ \t]+"(?P<quoted_title>[^"]*)")|(?:[ \t]*\|[ \t]*(?P<pipe_title>.*?)))?[ \t]*$'
)
_SLASH_ADMONITION_END_RE = re.compile(r"^[ \t]{0,3}///[ \t]*$")
_FENCE_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})")


@event_priority(-50)
def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    if "!!!" not in markdown and "???" not in markdown and "///" not in markdown:
        return markdown

    lines = markdown.splitlines(keepends=True)
    rewritten: list[str] = []
    changed = False
    fence: str | None = None
    index = 0

    while index < len(lines):
        line = lines[index]
        body, newline = _split_line_ending(line)

        fence_match = _FENCE_RE.match(body)
        if fence_match is not None:
            marker = fence_match.group("fence")
            if fence is None:
                fence = marker[0]
            elif marker.startswith(fence):
                fence = None

            rewritten.append(line)
            index += 1
            continue

        if fence is not None:
            rewritten.append(line)
            index += 1
            continue

        slash_match = _SLASH_ADMONITION_START_RE.match(body)
        if slash_match is not None and _is_known_admonition_type(slash_match.group("type")):
            closing_index = _find_slash_admonition_end(lines, index + 1)
            if closing_index is not None:
                rewritten.append(f"{_rewrite_slash_admonition_start(slash_match)}{newline}")
                content_indent = f"{slash_match.group('indent')}    "
                for content_line in lines[index + 1 : closing_index]:
                    content_body, content_newline = _split_line_ending(content_line)
                    if content_body.strip():
                        rewritten.append(f"{content_indent}{content_body}{content_newline}")
                    else:
                        rewritten.append(content_newline)
                changed = True
                index = closing_index + 1
                continue

        replacement = _rewrite_admonition_title(body)
        if replacement is None:
            rewritten.append(line)
            index += 1
            continue

        rewritten.append(f"{replacement}{newline}")
        changed = True
        index += 1

    return "".join(rewritten) if changed else markdown


def _find_slash_admonition_end(lines: list[str], start_index: int) -> int | None:
    fence: str | None = None
    for index in range(start_index, len(lines)):
        body, _newline = _split_line_ending(lines[index])
        fence_match = _FENCE_RE.match(body)
        if fence_match is not None:
            marker = fence_match.group("fence")
            if fence is None:
                fence = marker[0]
            elif marker.startswith(fence):
                fence = None
            continue

        if fence is None and _SLASH_ADMONITION_END_RE.match(body):
            return index

    return None


def _rewrite_slash_admonition_start(match: re.Match[str]) -> str:
    type_name = match.group("type")
    opening = f"{match.group('indent')}!!! {type_name}"
    title = _slash_admonition_title(match)
    if not title:
        return opening

    label = _TYPE_LABELS[type_name.lower()]
    formatted_title = _format_admonition_title(title, label)
    if not formatted_title:
        return opening
    return f'{opening} "{formatted_title}"'


def _slash_admonition_title(match: re.Match[str]) -> str | None:
    quoted_title = match.group("quoted_title")
    if quoted_title is not None:
        return quoted_title
    return match.group("pipe_title")


def _rewrite_admonition_title(line: str) -> str | None:
    match = _ADMONITION_TITLE_RE.match(line)
    if match is None:
        return None

    label = _TYPE_LABELS.get(match.group("type").lower())
    title = match.group("title")
    if label is None or not title:
        return None

    formatted_title = _format_admonition_title(title, label)
    if formatted_title == title:
        return None

    return (
        f"{match.group('indent')}{match.group('marker')} "
        f"{match.group('type')}{match.group('space')}\"{formatted_title}\""
        f"{match.group('trailing')}"
    )


def _is_known_admonition_type(type_name: str) -> bool:
    return type_name.lower() in _TYPE_LABELS


def _split_line_ending(line: str) -> tuple[str, str]:
    body = line.rstrip("\r\n")
    return body, line[len(body) :]


def _format_admonition_title(title: str, label: str) -> str:
    stripped = title.strip()
    if not stripped:
        return stripped

    label_match = re.match(
        rf"^{re.escape(label)}(?:\s*(?P<separator>\||[:：-])\s*|\s+)?(?P<rest>.*)$",
        stripped,
        re.IGNORECASE,
    )
    if label_match is None:
        return f"{label}{_TITLE_SEPARATOR}{stripped}"

    rest = label_match.group("rest").strip()
    if not rest:
        return label
    return f"{label}{_TITLE_SEPARATOR}{rest}"
