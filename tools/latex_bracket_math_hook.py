from __future__ import annotations

import re
from typing import Any


_FENCE_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
_CONTAINER_RE = re.compile(r"^(?P<prefix>(?:[ ]{0,3}>[ \t]?)*[ \t]*)(?P<body>.*)$")
_DISPLAY_DELIMITERS = {"[": "]", r"\[": r"\]", r"\\[": r"\\]", "$$": "$$"}
_LIST_MARKER_RE = re.compile(r"^(?:[-+*]|\d+[.)])[ \t]+(?:\S|$)")
_MATH_TOKEN_RE = re.compile(r"(?<!\\)(?P<slashes>\\{1,2})(?P<delimiter>[\(\)\[\]])")
_CODE_SPAN_RE = re.compile(r"(?<![\\`])(?P<ticks>`+)(?!`)(?P<code>.*?)(?<!`)(?P=ticks)(?!`)", re.S)


def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    """Isolate pasted display math for Arithmatex, without editing source files.

    Python-Markdown requires block math to start a separate paragraph. GPT
    often omits those blank lines, especially inside blockquotes. Preserve
    quote prefixes, line endings, and literal code while adding render-only
    paragraph boundaries. List continuations are normalized separately so GPT's
    three-space math/prose stays inside Python-Markdown list items. Bare [ ... ]
    remains supported for legacy notes.
    """
    lines = _normalize_list_continuations(markdown.splitlines(keepends=True))
    code_spans = _inline_code_spans(lines)
    converted_lines: list[str] = []
    index = 0
    open_fence: tuple[str, int] | None = None
    fence_quote_depth = 0

    while index < len(lines):
        content, newline = _split_line_ending(lines[index])
        prefix, body = _split_container(content)

        # A fenced block inside a quote ends when that quote container ends.
        if open_fence is not None and body.strip() and prefix.count(">") < fence_quote_depth:
            open_fence = None
        if open_fence is not None:
            converted_lines.append(lines[index])
            if prefix.count(">") == fence_quote_depth and _is_closing_fence(body, *open_fence):
                open_fence = None
            index += 1
            continue

        opening_fence = _parse_opening_fence(body)
        if opening_fence is not None:
            open_fence = opening_fence
            fence_quote_depth = prefix.count(">")
            converted_lines.append(lines[index])
            index += 1
            continue

        stripped = body.strip()
        # Four-space indentation after the quote marker is literal code.
        is_code = _container_key(prefix)[1] >= 4 or any(a <= len(prefix) < b for a, b in code_spans[index])
        closing_token = _DISPLAY_DELIMITERS.get(stripped)
        closing_index = None
        if closing_token is not None and not is_code:
            closing_index = _find_closing_delimiter(lines, index + 1, prefix, closing_token)

        if closing_index is None:
            converted_lines.append(lines[index])
            index += 1
            continue

        blank_line = prefix.rstrip(" \t") + (newline or "\n")
        if converted_lines and not _is_blank(converted_lines[-1]):
            converted_lines.append(blank_line)

        if stripped in ("[", r"\\["):
            converted_lines.append(f"{prefix}\\[{newline}")
            converted_lines.extend(lines[index + 1 : closing_index])
            close_content, close_newline = _split_line_ending(lines[closing_index])
            close_prefix, _ = _split_container(close_content)
            converted_lines.append(f"{close_prefix}\\]{close_newline}")
        else:
            converted_lines.extend(lines[index : closing_index + 1])

        if closing_index + 1 < len(lines) and not _is_blank(lines[closing_index + 1]):
            converted_lines.append(blank_line)
        index = closing_index + 1

    return "".join(converted_lines)


def _with_indent(prefix: str, indent: int) -> str:
    if "\t" in prefix or _container_key(prefix)[1] == indent:
        return prefix
    # Quote separator space is not part of the list's content indentation.
    quote = prefix.rsplit(">", 1)[0] + "> " if ">" in prefix else ""
    return quote + " " * indent


def _normalize_list_continuations(lines: list[str]) -> list[str]:
    """Map GPT list continuation indent 3 -> Python-Markdown's 4, in memory.

    Track actual list scopes, not arbitrary three-space paragraphs. Nested
    items and their prose stay together. Relative code indentation is retained;
    fenced contents are never parsed as list markers or math delimiters.
    """
    result: list[str] = []
    code_spans = _inline_code_spans(lines)
    stack: list[tuple[int, int]] = []  # source item indent, render item indent
    depth = 0
    fence: tuple[str, int] | None = None
    fence_depth = 0
    last_eol = "\n"
    index = 0

    def mapped(prefix: str) -> str:
        if not stack:
            return prefix
        source_indent, render_indent = stack[-1]
        relative = _container_key(prefix)[1] - source_indent
        if relative in (3, 4):
            return _with_indent(prefix, render_indent + 4)
        if relative >= 7:
            # 3-space item + 4-space code -> 4-space item + 4-space code.
            return _with_indent(prefix, render_indent + relative + (relative % 4 == 3))
        return prefix

    while index < len(lines):
        content, newline = _split_line_ending(lines[index])
        if newline:
            last_eol = newline
        prefix, body = _split_container(content)
        quote_depth, indent = _container_key(prefix)
        if fence is not None and body.strip() and quote_depth < fence_depth:
            fence = None
        if fence is not None:
            # Only consume the fence's real quote container. A literal '>' or
            # list marker inside its code must not change structural scope.
            literal = re.fullmatch(
                rf"(?P<prefix>(?:[ ]{{0,3}}>[ \t]?){{{fence_depth}}}[ \t]*)(?P<body>.*)", content
            )
            if literal:
                result.append(mapped(literal['prefix']) + literal['body'] + newline)
                if _is_closing_fence(literal['body'], *fence):
                    fence = None
            else:
                result.append(lines[index])
            index += 1
            continue
        if body.strip() and quote_depth != depth:
            stack.clear()
            depth = quote_depth
        if not body.strip():
            result.append(lines[index])
            index += 1
            continue

        while stack and indent <= stack[-1][0]:
            stack.pop()
        marker = _LIST_MARKER_RE.match(body)
        if re.fullmatch(r"(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}", body.strip()):
            marker = None  # A thematic break is not a bullet-list scope.
        if marker and "\t" not in prefix:
            if not stack and indent < 4:
                stack.append((indent, 0))
            elif stack and indent - stack[-1][0] in (3, 4):
                stack.append((indent, stack[-1][1] + 4))
            else:
                marker = None  # Deeply indented list-looking text is literal code.
        if marker and stack:
            render_prefix = _with_indent(prefix, stack[-1][1])
        else:
            render_prefix = mapped(prefix)

        opening_fence = _parse_opening_fence(body)
        if opening_fence:
            fence, fence_depth = opening_fence, quote_depth
        closing = _DISPLAY_DELIMITERS.get(body.strip())
        eligible = (((stack and indent - stack[-1][0] in (3, 4)) or (not stack and indent < 4))
                    and not opening_fence and not any(a <= len(prefix) < b for a, b in code_spans[index]))
        end = _find_closing_delimiter(lines, index + 1, prefix, closing) if closing and eligible else None
        if end is not None:
            blank = render_prefix.rstrip(" \t") + (newline or "\n")
            if result and not _is_blank(result[-1]):
                result.append(blank)
            for position in range(index, end + 1):
                inner_content, inner_newline = _split_line_ending(lines[position])
                inner_prefix, inner_body = _split_container(inner_content)
                if body.strip() in ("[", r"\\[") and position in (index, end):
                    inner_body = r"\[" if position == index else r"\]"
                result.append(mapped(inner_prefix) + inner_body + inner_newline)
            if end + 1 < len(lines) and not _is_blank(lines[end + 1]):
                result.append(blank)
            index = end + 1
            continue
        relative = indent - stack[-1][0] if stack else indent
        is_code = relative >= (7 if stack else 4)
        if not opening_fence and not is_code:
            protected = [(max(0, a - len(prefix)), b - len(prefix)) for a, b in code_spans[index]]
            continuation = _with_indent(render_prefix, stack[-1][1] + 4) if marker and stack else render_prefix
            result.extend(_normalize_math_line(body, render_prefix, newline, protected, continuation, last_eol))
        else:
            result.append(render_prefix + body + newline)
        index += 1
    return result


def _inline_code_spans(lines: list[str]) -> list[list[tuple[int, int]]]:
    """Locate inline literals, including multiline spans, without crossing blocks."""
    spans: list[list[tuple[int, int]]] = [[] for _ in lines]
    region: list[int] = []
    fence: tuple[str, int] | None = None
    fence_depth = 0

    def flush() -> None:
        text = "".join(lines[i] for i in region)
        matches = list(_CODE_SPAN_RE.finditer(text))
        offset = 0
        for i in region:
            end = offset + len(lines[i])
            spans[i] = [(max(offset, m.start()) - offset, min(end, m.end()) - offset)
                        for m in matches if m.start() < end and m.end() > offset]
            offset = end
        region.clear()

    for i, line in enumerate(lines):
        content, _ = _split_line_ending(line)
        prefix, body = _split_container(content)
        depth = prefix.count(">")
        if fence and body.strip() and depth < fence_depth:
            fence = None
        if fence:
            if depth == fence_depth and _is_closing_fence(body, *fence):
                fence = None
            continue
        opening = _parse_opening_fence(body)
        if opening:
            flush()
            fence, fence_depth = opening, depth
        elif not body.strip():
            flush()
        else:
            region.append(i)
    flush()
    return spans


def _normalize_math_line(
    body: str, prefix: str, newline: str, protected: list[tuple[int, int]], continuation: str, fallback_eol: str
) -> list[str]:
    """Canonicalize paired delimiters only; treat the enclosed TeX as opaque.

    Display math embedded in prose is emitted as its own paragraph, including
    repeated expressions in quotes/list items. Literal code stays byte-for-byte.
    """
    parts: list[tuple[str, str]] = []
    offset = 0
    cursor = 0
    while match := _MATH_TOKEN_RE.search(body, cursor):
        cursor = match.end()
        opening = match['delimiter']
        if opening not in ("(", "[") or any(a <= match.start() < b for a, b in protected):
            continue
        closing = ")" if opening == "(" else "]"
        end = next((m for m in _MATH_TOKEN_RE.finditer(body, cursor)
                    if m['delimiter'] == closing and m['slashes'] == match['slashes']), None)
        if end is None or any(a < end.end() and b > match.start() for a, b in protected):
            continue
        tex = body[match.end():end.start()]
        if not tex.strip():
            continue
        parts.append(("text", body[offset:match.start()]))
        if opening == "(":
            parts.append(("text", "\\(" + tex + "\\)"))
        else:
            parts.append(("display", tex))
        offset = cursor = end.end()
    parts.append(("text", body[offset:]))
    if not any(kind == "display" for kind, _ in parts):
        return [prefix + "".join(text for _, text in parts) + newline]

    eol = newline or fallback_eol
    output: list[str] = []
    text = ""
    active_prefix = prefix
    for kind, value in parts:
        if kind == "text":
            text += value
            continue
        if text.strip():
            output.append(active_prefix + text + eol)
        text = ""
        active_prefix = continuation
        blank = active_prefix.rstrip(" \t") + eol
        output.extend([blank, active_prefix + "\\[" + eol,
                       active_prefix + value.lstrip(" \t") + eol, active_prefix + "\\]" + eol, blank])
    if text.strip():
        output.append(active_prefix + text + newline)
    elif not newline:
        # Generated internal boundaries may add lines, never a final newline.
        while output and _is_blank(output[-1]):
            output.pop()
        output[-1] = output[-1].removesuffix(eol)
    return output


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def _split_container(line: str) -> tuple[str, str]:
    match = _CONTAINER_RE.fullmatch(line)
    assert match is not None
    return match.group("prefix"), match.group("body")


def _container_key(prefix: str) -> tuple[int, int]:
    # '>text' and '> text' belong to the same quote container.
    indent = prefix.rsplit(">", 1)[-1]
    if ">" in prefix and indent.startswith((" ", "\t")):
        indent = indent[1:]
    return prefix.count(">"), len(indent.expandtabs(4))


def _is_blank(line: str) -> bool:
    content, _ = _split_line_ending(line)
    _, body = _split_container(content)
    return not body.strip()


def _parse_opening_fence(body: str) -> tuple[str, int] | None:
    match = _FENCE_RE.match(body)
    if match is None:
        return None
    fence = match.group("fence")
    return fence[0], len(fence)


def _is_closing_fence(body: str, fence_char: str, fence_len: int) -> bool:
    match = _FENCE_RE.match(body)
    if match is None:
        return False
    fence = match.group("fence")
    return fence[0] == fence_char and len(fence) >= fence_len and not match.group("rest").strip()


def _find_closing_delimiter(
    lines: list[str], start_index: int, prefix: str, closing_token: str
) -> int | None:
    saw_non_empty_content = False
    key = _container_key(prefix)

    for index in range(start_index, len(lines)):
        content, _ = _split_line_ending(lines[index])
        inner_prefix, body = _split_container(content)
        # Never pair a delimiter across another quote/list/code container.
        if body.strip() and _container_key(inner_prefix) != key:
            return None
        stripped = body.strip()
        if stripped == closing_token:
            return index if saw_non_empty_content else None
        if _parse_opening_fence(body) is not None:
            return None
        if stripped in _DISPLAY_DELIMITERS:
            return None
        if stripped:
            saw_non_empty_content = True

    return None
