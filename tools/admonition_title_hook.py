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

_ADMONITION_TITLE_RE = re.compile(
    r'^(?P<indent>[ \t]{0,3})(?P<marker>!!!|\?\?\?\+?)\s+'
    r'(?P<type>[A-Za-z0-9_-]+)(?P<space>[ \t]+)"(?P<title>[^"]*)"(?P<trailing>[ \t]*)$'
)
_FENCE_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})")


@event_priority(-50)
def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    if "!!!" not in markdown and "???" not in markdown:
        return markdown

    lines = markdown.splitlines(keepends=True)
    rewritten: list[str] = []
    changed = False
    fence: str | None = None

    for line in lines:
        body = line.rstrip("\r\n")
        newline = line[len(body) :]

        fence_match = _FENCE_RE.match(body)
        if fence_match is not None:
            marker = fence_match.group("fence")
            if fence is None:
                fence = marker[0]
            elif marker.startswith(fence):
                fence = None

            rewritten.append(line)
            continue

        if fence is not None:
            rewritten.append(line)
            continue

        replacement = _rewrite_admonition_title(body)
        if replacement is None:
            rewritten.append(line)
            continue

        rewritten.append(f"{replacement}{newline}")
        changed = True

    return "".join(rewritten) if changed else markdown


def _rewrite_admonition_title(line: str) -> str | None:
    match = _ADMONITION_TITLE_RE.match(line)
    if match is None:
        return None

    label = _TYPE_LABELS.get(match.group("type").lower())
    title = match.group("title")
    if label is None or not title or _has_type_label(title, label):
        return None

    return (
        f"{match.group('indent')}{match.group('marker')} "
        f"{match.group('type')}{match.group('space')}\"{label} {title}\""
        f"{match.group('trailing')}"
    )


def _has_type_label(title: str, label: str) -> bool:
    return re.match(rf"^{re.escape(label)}(?:\s|[:：-]|$)", title.strip(), re.IGNORECASE) is not None
