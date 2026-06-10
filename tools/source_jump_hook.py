from __future__ import annotations

import json
import logging
import os
import posixpath
import re
import shutil
import subprocess
import urllib.parse
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from mkdocs.plugins import event_priority


log = logging.getLogger("mkdocs.hooks.source_jump")

_LOCAL_ENDPOINT_SUFFIX = "/__peicd/source-jump"
_CONTEXT_FALLBACK_MIN_SCORE = 2500.0
_VSCODE_OPEN_TIMEOUT_SECONDS = 8
_MARKDOWN = MarkdownIt("commonmark", {"html": True}).enable("table")
_PAGE_INDEX: dict[str, "PageRecord"] = {}
_VSCODE_COMMAND: str | None = None
_MARK_EXTENSION_RE = re.compile(r"==([^\s=](?:[^=\n]*?[^\s=])?)==")
_CARET_EXTENSION_RE = re.compile(r"\^\^([^\s^](?:[^^\n]*?[^\s^])?)\^\^")
_FENCE_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})")
_ADMONITION_START_RE = re.compile(
    r'^(?P<indent>[ \t]{0,3})(?P<marker>!!!|\?\?\?\+?)\s+'
    r'(?P<type>[A-Za-z0-9_-]+)(?:[ \t]+"(?P<title>[^"]*)")?[ \t]*$'
)
_SLASH_ADMONITION_START_RE = re.compile(
    r'^(?P<indent>[ \t]{0,3})///\s+'
    r'(?P<type>[A-Za-z0-9_-]+)'
    r'(?:(?:[ \t]+"(?P<quoted_title>[^"]*)")|(?:[ \t]*\|[ \t]*(?P<pipe_title>.*?)))?[ \t]*$'
)
_SLASH_ADMONITION_END_RE = re.compile(r"^[ \t]{0,3}///[ \t]*$")
_ADMONITION_TYPE_LABELS = {
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
_ADMONITION_TITLE_SEPARATOR = " | "


@dataclass
class BlockRecord:
    kind: str
    tag: str
    order_index: int
    section_index: int
    start_line: int
    end_line: int
    visible_text: str
    normalized_text: str
    normalized_source_offsets: list[int]
    heading_path: tuple[str, ...]
    normalized_heading_path: str
    prev_text: str = ""
    next_text: str = ""


@dataclass
class PageRecord:
    src_uri: str
    abs_src_path: str
    dest_uri: str
    markdown: str
    line_starts: list[int]
    blocks: list[BlockRecord]


@dataclass
class AdmonitionSpan:
    syntax: str
    start_line: int
    end_line: int
    start_offset: int
    type_name: str
    title: str | None
    content_markdown: str
    content_offset_map: list[int]
    content_line_number_map: list[int]


def on_config(config: Any) -> Any:
    _PAGE_INDEX.clear()
    return config


@event_priority(-100)
def on_files(files: Any, /, *, config: Any) -> Any:
    _PAGE_INDEX.clear()

    for file_obj in _iter_documentation_files(files):
        markdown = _read_markdown_content(file_obj)
        if markdown is None:
            continue

        _index_page_markdown(markdown, file_obj)

    return files


def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    file_obj = getattr(page, "file", None)
    if file_obj is None:
        return markdown

    source_markdown = _read_source_markdown_content(file_obj, markdown)
    _index_page_markdown(source_markdown, file_obj)

    return markdown


def on_serve(server: Any, /, *, config: Any, builder: Any) -> Any:
    original_app = server.serve_request

    def serve_request(environ, start_response):
        path = _decode_path(environ.get("PATH_INFO", ""))
        if _is_lookup_request(path):
            return _handle_lookup_request(environ, start_response, server)
        return original_app(environ, start_response)

    server.set_app(serve_request)
    return server


def _decode_path(path: str) -> str:
    return urllib.parse.unquote(path or "")


def _is_lookup_request(path: str) -> bool:
    if not path:
        return False
    normalized = path.rstrip("/")
    return normalized == _LOCAL_ENDPOINT_SUFFIX or normalized.endswith(_LOCAL_ENDPOINT_SUFFIX)


def _handle_lookup_request(environ, start_response, server):
    params = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    page_param = params.get("page", [""])[0]
    selection = params.get("selection", [""])[0]
    container = params.get("container", [""])[0]
    prefix = params.get("prefix", [""])[0]
    heading_path = params.get("heading_path", [""])[0]
    prev_block = params.get("prev_block", [""])[0]
    next_block = params.get("next_block", [""])[0]
    block_tag = params.get("block_tag", [""])[0]
    block_index_raw = params.get("block_index", [""])[0]
    section_index_raw = params.get("section_index", [""])[0]
    block_progress_raw = params.get("block_progress", [""])[0]
    action = params.get("action", ["lookup"])[0].strip().lower()
    try:
        block_index = int(block_index_raw)
    except (TypeError, ValueError):
        block_index = None
    try:
        section_index = int(section_index_raw)
    except (TypeError, ValueError):
        section_index = None
    try:
        block_progress = float(block_progress_raw)
    except (TypeError, ValueError):
        block_progress = None

    if selection == "__probe__":
        return _json_response(
            start_response,
            status="200 OK",
            payload={"ok": True, "probe": True},
        )

    if not selection.strip() and not container.strip():
        return _json_response(
            start_response,
            status="400 Bad Request",
            payload={"ok": False, "message": "selection or container is required"},
        )

    page_key = _normalize_page_key(page_param, getattr(server, "mount_path", "/"))
    record = _PAGE_INDEX.get(page_key)
    if record is None:
        return _json_response(
            start_response,
            status="404 Not Found",
            payload={"ok": False, "message": f"page not indexed: {page_key}"},
        )

    result = _locate_selection(
        record,
        selection,
        container,
        prefix,
        heading_path,
        prev_block,
        next_block,
        block_tag,
        block_index,
        section_index,
        block_progress,
    )
    if result.get("ok") and action == "open":
        opened, message = _open_in_vscode(
            result["abs_path"],
            int(result["line"]),
            int(result["column"]),
        )
        result["opened"] = opened
        if message:
            result["message"] = message
        if not opened:
            return _json_response(
                start_response,
                status="500 Internal Server Error",
                payload=result,
            )

    status = "200 OK" if result.get("ok") else "404 Not Found"
    return _json_response(start_response, status=status, payload=result)


def _json_response(start_response, *, status: str, payload: dict[str, Any]):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ],
    )
    return [body]


def _normalize_page_key(page_path: str, mount_path: str) -> str:
    path = urllib.parse.urlsplit(page_path or "").path or ""
    path = _decode_path(path).replace("\\", "/")
    mount = (mount_path or "/").replace("\\", "/")
    if path == mount.rstrip("/"):
        path = ""
    elif mount and mount != "/" and path.startswith(mount):
        path = path[len(mount) :]
    path = path.lstrip("/")
    if not path:
        path = "index.html"
    elif path.endswith("/"):
        path = f"{path}index.html"
    return posixpath.normpath("/" + path).lstrip("/")


def _iter_documentation_files(files: Any) -> list[Any]:
    documentation_pages = getattr(files, "documentation_pages", None)
    if callable(documentation_pages):
        return list(documentation_pages())

    collected: list[Any] = []
    for file_obj in files:
        src_uri = str(getattr(file_obj, "src_uri", "") or "").lower()
        if src_uri.endswith((".md", ".markdown")):
            collected.append(file_obj)
    return collected


def _read_markdown_content(file_obj: Any) -> str | None:
    try:
        content = getattr(file_obj, "content_string")
    except Exception:
        content = None

    if isinstance(content, bytes):
        return content.decode("utf-8")
    if isinstance(content, str):
        return content

    abs_src_path = getattr(file_obj, "abs_src_path", None)
    if abs_src_path and os.path.exists(abs_src_path):
        return Path(abs_src_path).read_text(encoding="utf-8")

    return None


def _read_source_markdown_content(file_obj: Any, fallback: str) -> str:
    abs_src_path = getattr(file_obj, "abs_src_path", None)
    if abs_src_path and os.path.exists(abs_src_path):
        return Path(abs_src_path).read_text(encoding="utf-8")

    content = _read_markdown_content(file_obj)
    if content is not None:
        return content
    return fallback


def _index_page_markdown(markdown: str, file_obj: Any) -> None:
    try:
        record = _build_page_record(markdown, file_obj)
        _PAGE_INDEX[record.dest_uri] = record
    except Exception:
        log.exception("Failed to index page source for %s", getattr(file_obj, "src_uri", "<unknown>"))


def _build_page_record(markdown: str, file_obj: Any) -> PageRecord:
    line_starts = _line_starts(markdown)
    blocks: list[BlockRecord] = []
    heading_stack: list[str] = []
    admonition_spans = _iter_admonition_spans(markdown, line_starts)
    slash_admonition_ranges = [
        (span.start_line, span.end_line) for span in admonition_spans if span.syntax == "slash"
    ]
    tokens = _MARKDOWN.parse(markdown)

    for token_index, token in enumerate(tokens):
        block = _build_block_record(
            token=token,
            tokens=tokens,
            token_index=token_index,
            markdown=markdown,
            line_starts=line_starts,
            heading_stack=heading_stack,
        )
        if block is None:
            continue
        if _block_within_line_ranges(block, slash_admonition_ranges):
            continue
        blocks.append(block)
        if block.kind == "heading":
            heading_stack = list(block.heading_path)

    blocks.extend(_build_admonition_block_records(admonition_spans, blocks))
    blocks.sort(key=_block_sort_key)
    _attach_neighbor_context(blocks)

    return PageRecord(
        src_uri=str(getattr(file_obj, "src_uri", "")).replace("\\", "/"),
        abs_src_path=str(getattr(file_obj, "abs_src_path", "")),
        dest_uri=str(getattr(file_obj, "dest_uri", "")).replace("\\", "/"),
        markdown=markdown,
        line_starts=line_starts,
        blocks=blocks,
    )


def _build_block_record(
    *,
    token: Any,
    tokens: list[Any],
    token_index: int,
    markdown: str,
    line_starts: list[int],
    heading_stack: list[str],
    offset_map: list[int] | None = None,
    line_number_map: list[int] | None = None,
) -> BlockRecord | None:
    if not token.map:
        return None

    visible_text = _strip_rendered_extension_markers(_visible_text_from_token(token))
    if not visible_text.strip():
        return None

    start_line0, end_line0 = token.map
    source_start = line_starts[start_line0]
    source_end = line_starts[end_line0] if end_line0 < len(line_starts) else len(markdown)
    source_slice = markdown[source_start:source_end]
    source_map = _align_visible_text_to_source(visible_text, source_slice, source_start)
    if offset_map is not None:
        source_map = [_map_synthetic_offset(offset_map, offset) for offset in source_map]
    normalized_text, normalized_source_offsets = _normalize_text_with_offsets(visible_text, source_map)

    if not normalized_text:
        return None

    kind, tag, block_heading_path = _resolve_block_context(tokens, token_index, heading_stack, visible_text)
    start_line = _map_synthetic_line(line_number_map, start_line0)
    end_line = _map_synthetic_line(line_number_map, max(start_line0, end_line0 - 1))

    return BlockRecord(
        kind=kind,
        tag=tag,
        order_index=-1,
        section_index=-1,
        start_line=start_line if start_line is not None else start_line0 + 1,
        end_line=end_line if end_line is not None else max(start_line0 + 1, end_line0),
        visible_text=visible_text,
        normalized_text=normalized_text,
        normalized_source_offsets=normalized_source_offsets,
        heading_path=block_heading_path,
        normalized_heading_path=_normalize_heading_path(block_heading_path),
    )


def _build_admonition_block_records(
    spans: list[AdmonitionSpan],
    existing_blocks: list[BlockRecord],
) -> list[BlockRecord]:
    if not spans:
        return []

    blocks: list[BlockRecord] = []
    for span in spans:
        heading_stack = list(_heading_path_before_line(existing_blocks, span.start_line))
        title_block = _build_admonition_title_block(span, heading_stack)
        if title_block is not None:
            blocks.append(title_block)

        if not span.content_markdown.strip():
            continue

        local_heading_stack = heading_stack
        tokens = _MARKDOWN.parse(span.content_markdown)
        span_line_starts = _line_starts(span.content_markdown)
        for token_index, token in enumerate(tokens):
            block = _build_block_record(
                token=token,
                tokens=tokens,
                token_index=token_index,
                markdown=span.content_markdown,
                line_starts=span_line_starts,
                heading_stack=local_heading_stack,
                offset_map=span.content_offset_map,
                line_number_map=span.content_line_number_map,
            )
            if block is None:
                continue
            blocks.append(block)
            if block.kind == "heading":
                local_heading_stack = list(block.heading_path)

    return blocks


def _iter_admonition_spans(markdown: str, line_starts: list[int]) -> list[AdmonitionSpan]:
    lines = markdown.splitlines(keepends=True)
    spans: list[AdmonitionSpan] = []
    fence_marker: str | None = None
    index = 0

    while index < len(lines):
        body, _newline = _split_line_ending(lines[index])
        fence_match = _FENCE_RE.match(body)
        if fence_match is not None:
            marker = fence_match.group("fence")
            if fence_marker is None:
                fence_marker = marker[0]
            elif marker.startswith(fence_marker):
                fence_marker = None
            index += 1
            continue

        if fence_marker is not None:
            index += 1
            continue

        slash_match = _SLASH_ADMONITION_START_RE.match(body)
        if slash_match is not None and _is_known_admonition_type(slash_match.group("type")):
            closing_index = _find_slash_admonition_end(lines, index + 1)
            if closing_index is None:
                index += 1
                continue

            content_markdown, offset_map, line_number_map = _copy_admonition_content(
                lines=lines,
                line_starts=line_starts,
                start_index=index + 1,
                end_index=closing_index,
            )
            spans.append(
                AdmonitionSpan(
                    syntax="slash",
                    start_line=index + 1,
                    end_line=max(index + 1, closing_index + 1),
                    start_offset=line_starts[index],
                    type_name=slash_match.group("type"),
                    title=_slash_admonition_title(slash_match),
                    content_markdown=content_markdown,
                    content_offset_map=offset_map,
                    content_line_number_map=line_number_map,
                )
            )
            index = closing_index + 1
            continue

        match = _ADMONITION_START_RE.match(body)
        if match is None:
            index += 1
            continue

        base_indent = _indent_width(match.group("indent"))
        content_start = index + 1
        content_end = content_start
        while content_end < len(lines):
            content_body, _content_newline = _split_line_ending(lines[content_end])
            if content_body.strip() and _indent_width(content_body) <= base_indent:
                break
            content_end += 1

        content_markdown, offset_map, line_number_map = _dedent_admonition_content(
            lines=lines,
            line_starts=line_starts,
            start_index=content_start,
            end_index=content_end,
            target_indent=base_indent + 4,
        )
        spans.append(
            AdmonitionSpan(
                syntax="python-markdown",
                start_line=index + 1,
                end_line=max(index + 1, content_end),
                start_offset=line_starts[index],
                type_name=match.group("type"),
                title=match.group("title"),
                content_markdown=content_markdown,
                content_offset_map=offset_map,
                content_line_number_map=line_number_map,
            )
        )
        index = content_end

    return spans


def _find_slash_admonition_end(lines: list[str], start_index: int) -> int | None:
    fence_marker: str | None = None
    for index in range(start_index, len(lines)):
        body, _newline = _split_line_ending(lines[index])
        fence_match = _FENCE_RE.match(body)
        if fence_match is not None:
            marker = fence_match.group("fence")
            if fence_marker is None:
                fence_marker = marker[0]
            elif marker.startswith(fence_marker):
                fence_marker = None
            continue

        if fence_marker is None and _SLASH_ADMONITION_END_RE.match(body):
            return index

    return None


def _copy_admonition_content(
    *,
    lines: list[str],
    line_starts: list[int],
    start_index: int,
    end_index: int,
) -> tuple[str, list[int], list[int]]:
    parts: list[str] = []
    offset_map: list[int] = []
    line_number_map: list[int] = []

    for line_index in range(start_index, end_index):
        body, newline = _split_line_ending(lines[line_index])
        original_body_offset = line_starts[line_index]
        original_newline_offset = line_starts[line_index] + len(body)

        parts.append(body)
        offset_map.extend(range(original_body_offset, original_body_offset + len(body)))
        if newline:
            parts.append(newline)
            offset_map.extend(range(original_newline_offset, original_newline_offset + len(newline)))
        line_number_map.append(line_index + 1)

    return "".join(parts), offset_map, line_number_map


def _dedent_admonition_content(
    *,
    lines: list[str],
    line_starts: list[int],
    start_index: int,
    end_index: int,
    target_indent: int,
) -> tuple[str, list[int], list[int]]:
    parts: list[str] = []
    offset_map: list[int] = []
    line_number_map: list[int] = []

    for line_index in range(start_index, end_index):
        body, newline = _split_line_ending(lines[line_index])
        stripped_body, stripped_chars = _strip_indent_to_width(body, target_indent)
        original_body_offset = line_starts[line_index] + stripped_chars
        original_newline_offset = line_starts[line_index] + len(body)

        parts.append(stripped_body)
        offset_map.extend(range(original_body_offset, original_body_offset + len(stripped_body)))
        if newline:
            parts.append(newline)
            offset_map.extend(range(original_newline_offset, original_newline_offset + len(newline)))
        line_number_map.append(line_index + 1)

    return "".join(parts), offset_map, line_number_map


def _build_admonition_title_block(
    span: AdmonitionSpan,
    heading_stack: list[str],
) -> BlockRecord | None:
    title = _render_admonition_title(span.type_name, span.title)
    if not title:
        return None

    offsets = [span.start_offset] * len(title)
    normalized_text, normalized_offsets = _normalize_text_with_offsets(title, offsets)
    if not normalized_text:
        return None

    return BlockRecord(
        kind="paragraph",
        tag="p",
        order_index=-1,
        section_index=-1,
        start_line=span.start_line,
        end_line=span.start_line,
        visible_text=title,
        normalized_text=normalized_text,
        normalized_source_offsets=normalized_offsets,
        heading_path=tuple(heading_stack),
        normalized_heading_path=_normalize_heading_path(tuple(heading_stack)),
    )


def _is_known_admonition_type(type_name: str) -> bool:
    return type_name.lower() in _ADMONITION_TYPE_LABELS


def _slash_admonition_title(match: re.Match[str]) -> str | None:
    quoted_title = match.group("quoted_title")
    if quoted_title is not None:
        return quoted_title
    return match.group("pipe_title")


def _render_admonition_title(type_name: str, raw_title: str | None) -> str:
    label = _ADMONITION_TYPE_LABELS.get(type_name.lower(), type_name.replace("-", " ").title())
    if raw_title is None:
        return label

    title = raw_title.strip()
    if not title:
        return ""
    return _format_admonition_title(title, label)


def _format_admonition_title(title: str, label: str) -> str:
    label_match = re.match(
        rf"^{re.escape(label)}(?:\s*(?P<separator>\||[:：-])\s*|\s+)?(?P<rest>.*)$",
        title,
        re.IGNORECASE,
    )
    if label_match is None:
        return f"{label}{_ADMONITION_TITLE_SEPARATOR}{title}"

    rest = label_match.group("rest").strip()
    if not rest:
        return label
    return f"{label}{_ADMONITION_TITLE_SEPARATOR}{rest}"


def _heading_path_before_line(blocks: list[BlockRecord], line: int) -> tuple[str, ...]:
    heading_path: tuple[str, ...] = ()
    for block in sorted(blocks, key=_block_sort_key):
        if block.start_line >= line:
            break
        if block.kind == "heading":
            heading_path = block.heading_path
    return heading_path


def _block_sort_key(block: BlockRecord) -> tuple[int, int, str, str]:
    return (block.start_line, block.end_line, block.tag, block.normalized_text)


def _block_within_line_ranges(block: BlockRecord, ranges: list[tuple[int, int]]) -> bool:
    for start_line, end_line in ranges:
        if block.start_line >= start_line and block.end_line <= end_line:
            return True
    return False


def _split_line_ending(line: str) -> tuple[str, str]:
    body = line.rstrip("\r\n")
    return body, line[len(body) :]


def _indent_width(line: str) -> int:
    width = 0
    for char in line:
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4 - (width % 4)
        else:
            break
    return width


def _strip_indent_to_width(line: str, target_width: int) -> tuple[str, int]:
    width = 0
    index = 0
    while index < len(line) and width < target_width:
        char = line[index]
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4 - (width % 4)
        else:
            break
        index += 1
    return line[index:], index


def _map_synthetic_offset(offset_map: list[int], offset: int) -> int:
    if not offset_map:
        return 0
    if offset < 0:
        return offset_map[0]
    if offset >= len(offset_map):
        return offset_map[-1]
    return offset_map[offset]


def _map_synthetic_line(line_number_map: list[int] | None, line_index: int) -> int | None:
    if not line_number_map:
        return None
    if line_index < 0:
        return line_number_map[0]
    if line_index >= len(line_number_map):
        return line_number_map[-1]
    return line_number_map[line_index]


def _visible_text_from_token(token: Any) -> str:
    token_type = getattr(token, "type", "")
    if token_type == "inline":
        return _visible_text_from_inline_children(getattr(token, "children", None))
    if token_type in {"fence", "code_block"}:
        return getattr(token, "content", "")
    if token_type == "html_block":
        return _html_to_text(getattr(token, "content", ""))
    return ""


def _visible_text_from_inline_children(children: Any) -> str:
    if not children:
        return ""

    parts: list[str] = []
    for child in children:
        child_type = getattr(child, "type", "")
        if child_type in {"text", "code_inline"}:
            parts.append(getattr(child, "content", ""))
        elif child_type in {"softbreak", "hardbreak"}:
            parts.append("\n")
        elif child_type == "image":
            alt_text = getattr(child, "content", "") or child.attrGet("alt") or ""
            parts.append(alt_text)
        elif child_type == "html_inline":
            parts.append(_html_to_text(getattr(child, "content", "")))
    return "".join(parts)


def _strip_rendered_extension_markers(text: str) -> str:
    if not text:
        return ""

    stripped = text
    for _ in range(4):
        previous = stripped
        stripped = _MARK_EXTENSION_RE.sub(r"\1", stripped)
        stripped = _CARET_EXTENSION_RE.sub(r"\1", stripped)
        if stripped == previous:
            break
    return stripped


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=False)


def _resolve_block_context(
    tokens: list[Any],
    token_index: int,
    heading_stack: list[str],
    visible_text: str,
) -> tuple[str, str, tuple[str, ...]]:
    token = tokens[token_index]
    token_type = getattr(token, "type", "")

    if token_type in {"fence", "code_block"}:
        return "code", "pre", tuple(heading_stack)
    if token_type == "html_block":
        return "html_block", "", tuple(heading_stack)
    if token_type != "inline":
        return token_type, getattr(token, "tag", "") or "", tuple(heading_stack)

    previous = tokens[token_index - 1] if token_index > 0 else None
    previous_type = getattr(previous, "type", "")
    previous_tag = getattr(previous, "tag", "") or ""

    if previous_type == "heading_open":
        heading_level = _heading_level_from_tag(previous_tag)
        heading_title = visible_text.strip()
        heading_path = tuple(heading_stack[: max(heading_level - 1, 0)] + ([heading_title] if heading_title else []))
        return "heading", previous_tag or "heading", heading_path

    if previous_type.endswith("_open"):
        open_type = previous_type[:-5]
        return _map_open_token_to_kind(open_type), previous_tag, tuple(heading_stack)

    return "inline", getattr(token, "tag", "") or "", tuple(heading_stack)


def _heading_level_from_tag(tag: str) -> int:
    if len(tag) == 2 and tag.startswith("h") and tag[1].isdigit():
        return int(tag[1])
    return 1


def _map_open_token_to_kind(open_type: str) -> str:
    if open_type == "paragraph":
        return "paragraph"
    if open_type == "list_item":
        return "list_item"
    if open_type in {"bullet_list", "ordered_list"}:
        return "list"
    if open_type in {"td", "th"}:
        return "table_cell"
    if open_type == "heading":
        return "heading"
    return open_type


def _normalize_heading_path(parts: tuple[str, ...]) -> str:
    normalized_parts: list[str] = []
    for part in parts:
        normalized_part = _normalize_text(part)
        if normalized_part:
            normalized_parts.append(normalized_part)
    return " / ".join(normalized_parts)


def _attach_neighbor_context(blocks: list[BlockRecord]) -> None:
    current_section_path: str | None = None
    current_section_index = 0
    for index, block in enumerate(blocks):
        block.order_index = index
        if block.kind == "heading":
            block.section_index = 0
            current_section_path = block.normalized_heading_path
            current_section_index = 1
        else:
            if block.normalized_heading_path != current_section_path:
                current_section_path = block.normalized_heading_path
                current_section_index = 0
            block.section_index = current_section_index
            current_section_index += 1
        block.prev_text = blocks[index - 1].normalized_text if index > 0 else ""
        block.next_text = blocks[index + 1].normalized_text if index + 1 < len(blocks) else ""


def _align_visible_text_to_source(visible_text: str, source_text: str, global_start: int) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    last_offset = global_start

    for char in visible_text:
        if _is_ignored_char(char):
            offsets.append(last_offset)
            continue

        if char.isspace():
            while cursor < len(source_text) and not source_text[cursor].isspace():
                cursor += 1
            if cursor < len(source_text):
                last_offset = global_start + cursor
                offsets.append(last_offset)
                cursor += 1
                while cursor < len(source_text) and source_text[cursor].isspace():
                    cursor += 1
            else:
                offsets.append(last_offset)
            continue

        found = source_text.find(char, cursor)
        if found == -1:
            offsets.append(last_offset)
            continue

        last_offset = global_start + found
        offsets.append(last_offset)
        cursor = found + 1

    return offsets


def _normalize_text(text: str) -> str:
    normalized, _ = _normalize_text_with_offsets(text, list(range(len(text))))
    return normalized


def _normalize_text_with_offsets(text: str, offsets: list[int]) -> tuple[str, list[int]]:
    output_chars: list[str] = []
    output_offsets: list[int] = []
    pending_space = False
    pending_space_offset = 0

    for index, char in enumerate(text):
        if _is_ignored_char(char):
            continue

        char = " " if char == "\xa0" else char
        source_offset = offsets[index] if index < len(offsets) else (offsets[-1] if offsets else 0)

        if char.isspace():
            if output_chars:
                pending_space = True
                pending_space_offset = source_offset
            continue

        if pending_space:
            output_chars.append(" ")
            output_offsets.append(pending_space_offset)
            pending_space = False

        output_chars.append(char)
        output_offsets.append(source_offset)

    return "".join(output_chars), output_offsets


def _locate_selection(
    record: PageRecord,
    selection: str,
    container: str,
    prefix: str,
    heading_path: str,
    prev_block: str,
    next_block: str,
    block_tag: str,
    block_index: int | None,
    section_index: int | None,
    block_progress: float | None,
) -> dict[str, Any]:
    selection_norm = _normalize_text(selection)
    container_norm = _normalize_text(container)
    prefix_norm = _normalize_text(prefix)
    heading_path_norm = _normalize_text(heading_path)
    prev_block_norm = _normalize_text(prev_block)
    next_block_norm = _normalize_text(next_block)
    block_tag_norm = _normalize_block_tag(block_tag)

    if not selection_norm and not container_norm:
        return {"ok": False, "message": "selection and container both became empty after normalization"}

    if not selection_norm:
        if not record.blocks:
            return {
                "ok": False,
                "message": "no indexed blocks available for container lookup",
                "src_uri": record.src_uri,
            }

        best_block = max(
            record.blocks,
            key=lambda block: _container_only_score(
                block,
                container_norm,
                heading_path_norm,
                prev_block_norm,
                next_block_norm,
                block_tag_norm,
                block_index,
                section_index,
                block_progress,
                len(record.blocks),
            ),
        )
        line, column = _block_start_line_column(record, best_block)
        return _success_payload(record, line, column)

    candidates = [block for block in record.blocks if selection_norm in block.normalized_text]
    if not candidates:
        contextual_match = _contextual_fallback_match(
            record,
            container_norm,
            heading_path_norm,
            prev_block_norm,
            next_block_norm,
            block_tag_norm,
            block_index,
            section_index,
            block_progress,
        )
        if contextual_match is not None:
            line, column = _block_start_line_column(record, contextual_match)
            return _success_payload(record, line, column)

        raw_match_offset = record.markdown.find(selection)
        if raw_match_offset == -1:
            return {
                "ok": False,
                "message": "no matching block found",
                "src_uri": record.src_uri,
            }
        line, column = _offset_to_line_column(record.line_starts, raw_match_offset)
        return _success_payload(record, line, column)

    best_block = max(
        candidates,
        key=lambda block: _block_score(
            block,
            selection_norm,
            container_norm,
            prefix_norm,
            heading_path_norm,
            prev_block_norm,
            next_block_norm,
            block_tag_norm,
            block_index,
            section_index,
            block_progress,
            len(record.blocks),
        ),
    )
    match_index = _choose_match_index(best_block.normalized_text, selection_norm, prefix_norm)
    if match_index < 0 or match_index >= len(best_block.normalized_source_offsets):
        match_index = 0

    source_offset = best_block.normalized_source_offsets[match_index]
    line, column = _offset_to_line_column(record.line_starts, source_offset)
    return _success_payload(record, line, column)


def _contextual_fallback_match(
    record: PageRecord,
    container_norm: str,
    heading_path_norm: str,
    prev_block_norm: str,
    next_block_norm: str,
    block_tag_norm: str,
    block_index: int | None,
    section_index: int | None,
    block_progress: float | None,
) -> BlockRecord | None:
    if not record.blocks:
        return None
    if not any(
        [
            container_norm,
            heading_path_norm,
            prev_block_norm,
            next_block_norm,
            block_tag_norm,
            block_index is not None,
            section_index is not None,
            block_progress is not None,
        ]
    ):
        return None

    scored_blocks = [
        (
            _container_only_score(
                block,
                container_norm,
                heading_path_norm,
                prev_block_norm,
                next_block_norm,
                block_tag_norm,
                block_index,
                section_index,
                block_progress,
                len(record.blocks),
            ),
            block,
        )
        for block in record.blocks
    ]
    best_score, best_block = max(scored_blocks, key=lambda item: item[0])
    if best_score < _CONTEXT_FALLBACK_MIN_SCORE:
        return None
    return best_block


def _block_start_line_column(record: PageRecord, block: BlockRecord) -> tuple[int, int]:
    if block.normalized_source_offsets:
        return _offset_to_line_column(record.line_starts, block.normalized_source_offsets[0])
    return block.start_line, 1


def _success_payload(record: PageRecord, line: int, column: int) -> dict[str, Any]:
    return {
        "ok": True,
        "src_uri": record.src_uri,
        "abs_path": record.abs_src_path,
        "line": line,
        "column": column,
        "uri": _make_vscode_uri(record.abs_src_path, line, column),
    }


def _block_score(
    block: BlockRecord,
    selection_norm: str,
    container_norm: str,
    prefix_norm: str,
    heading_path_norm: str,
    prev_block_norm: str,
    next_block_norm: str,
    block_tag_norm: str,
    block_index: int | None,
    section_index: int | None,
    block_progress: float | None,
    total_blocks: int,
) -> float:
    score = 0.0

    if container_norm:
        if block.normalized_text == container_norm:
            score += 6000
        elif container_norm in block.normalized_text:
            score += 4200
        elif block.normalized_text in container_norm:
            score += _contained_block_score(block.normalized_text, container_norm, 3200)
        else:
            ratio = SequenceMatcher(None, block.normalized_text[:1500], container_norm[:1500]).ratio()
            score += ratio * 2500

        score -= abs(len(block.normalized_text) - len(container_norm)) / 5

    if prefix_norm:
        desired_index = len(prefix_norm)
        actual_index = _choose_match_index(block.normalized_text, selection_norm, prefix_norm)
        if actual_index >= 0:
            score += max(0, 1400 - abs(actual_index - desired_index) * 4)

    score += _context_score(
        block.normalized_heading_path,
        heading_path_norm,
        exact_bonus=2600,
        contain_bonus=1700,
        ratio_bonus=1400,
    )
    score += _context_score(
        block.prev_text,
        prev_block_norm,
        exact_bonus=1050,
        contain_bonus=760,
        ratio_bonus=700,
    )
    score += _context_score(
        block.next_text,
        next_block_norm,
        exact_bonus=1050,
        contain_bonus=760,
        ratio_bonus=700,
    )
    score += _block_tag_score(block, block_tag_norm)
    score += _block_order_score(block.order_index, block_index)
    score += _section_order_score(block.section_index, section_index)
    score += _block_progress_score(block.order_index, total_blocks, block_progress)

    score += max(0, 300 - (block.end_line - block.start_line))
    score += max(0, 200 - block.start_line / 10)
    return score


def _container_only_score(
    block: BlockRecord,
    container_norm: str,
    heading_path_norm: str,
    prev_block_norm: str,
    next_block_norm: str,
    block_tag_norm: str,
    block_index: int | None,
    section_index: int | None,
    block_progress: float | None,
    total_blocks: int,
) -> float:
    score = 0.0

    if container_norm:
        if block.normalized_text == container_norm:
            score += 6000
        elif container_norm in block.normalized_text:
            score += 4200
        elif block.normalized_text in container_norm:
            score += _contained_block_score(block.normalized_text, container_norm, 3200)
        else:
            ratio = SequenceMatcher(None, block.normalized_text[:1500], container_norm[:1500]).ratio()
            score += ratio * 2500

        score -= abs(len(block.normalized_text) - len(container_norm)) / 5

    score += _context_score(
        block.normalized_heading_path,
        heading_path_norm,
        exact_bonus=2600,
        contain_bonus=1700,
        ratio_bonus=1400,
    )
    score += _context_score(
        block.prev_text,
        prev_block_norm,
        exact_bonus=1050,
        contain_bonus=760,
        ratio_bonus=700,
    )
    score += _context_score(
        block.next_text,
        next_block_norm,
        exact_bonus=1050,
        contain_bonus=760,
        ratio_bonus=700,
    )
    score += _block_tag_score(block, block_tag_norm)
    score += _block_order_score(block.order_index, block_index)
    score += _section_order_score(block.section_index, section_index)
    score += _block_progress_score(block.order_index, total_blocks, block_progress)

    score += max(0, 300 - (block.end_line - block.start_line))
    score += max(0, 200 - block.start_line / 10)
    return score


def _context_score(
    candidate: str,
    observed: str,
    *,
    exact_bonus: float,
    contain_bonus: float,
    ratio_bonus: float,
) -> float:
    if not candidate or not observed:
        return 0.0
    if candidate == observed:
        return exact_bonus
    if observed in candidate:
        return contain_bonus
    if candidate in observed:
        return contain_bonus * 0.72
    return SequenceMatcher(None, candidate[:1200], observed[:1200]).ratio() * ratio_bonus


def _contained_block_score(candidate: str, container: str, base_score: float) -> float:
    if not candidate or not container:
        return 0.0

    coverage = len(candidate) / max(len(container), 1)
    if coverage < 0.35:
        return base_score * coverage * 0.12
    return base_score * min(1.0, coverage)


def _normalize_block_tag(tag: str) -> str:
    return (tag or "").strip().lower()


def _block_tag_score(block: BlockRecord, block_tag: str) -> float:
    if not block_tag:
        return 0.0
    if block.tag == block_tag:
        return 700.0
    if _tags_compatible(block, block_tag):
        return 320.0
    return 0.0


def _tags_compatible(block: BlockRecord, block_tag: str) -> bool:
    if block_tag == "li" and block.kind in {"list_item", "paragraph"}:
        return True
    if block_tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and block.kind == "heading":
        return True
    if block_tag in {"td", "th"} and block.tag in {"td", "th"}:
        return True
    if block_tag == "pre" and block.kind == "code":
        return True
    if block_tag == "p" and block.kind == "paragraph":
        return True
    return False


def _block_order_score(order_index: int, block_index: int | None) -> float:
    if block_index is None or block_index < 0 or order_index < 0:
        return 0.0
    delta = abs(order_index - block_index)
    return max(0.0, 900.0 - delta * 35.0)


def _section_order_score(section_index: int, observed_section_index: int | None) -> float:
    if observed_section_index is None or observed_section_index < 0 or section_index < 0:
        return 0.0
    delta = abs(section_index - observed_section_index)
    return max(0.0, 1200.0 - delta * 90.0)


def _block_progress_score(order_index: int, total_blocks: int, observed_progress: float | None) -> float:
    if observed_progress is None or observed_progress < 0 or order_index < 0 or total_blocks <= 1:
        return 0.0
    progress = order_index / max(total_blocks - 1, 1)
    delta = abs(progress - min(max(observed_progress, 0.0), 1.0))
    return max(0.0, 900.0 - delta * 3600.0)


def _choose_match_index(text: str, needle: str, prefix_norm: str) -> int:
    positions = _find_all(text, needle)
    if not positions:
        return -1
    if not prefix_norm:
        return positions[0]

    desired_index = len(prefix_norm)
    return min(positions, key=lambda position: abs(position - desired_index))


def _find_all(text: str, needle: str) -> list[int]:
    positions: list[int] = []
    start = 0
    while True:
        index = text.find(needle, start)
        if index == -1:
            return positions
        positions.append(index)
        start = index + 1


def _make_vscode_uri(abs_path: str, line: int, column: int) -> str:
    posix_path = abs_path.replace("\\", "/")
    encoded_path = urllib.parse.quote(posix_path, safe="/:")
    return f"vscode://file/{encoded_path}:{line}:{column}"


def _find_vscode_command() -> str | None:
    global _VSCODE_COMMAND
    if _VSCODE_COMMAND:
        return _VSCODE_COMMAND

    candidates = [
        shutil.which("code"),
        shutil.which("code.cmd"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft VS Code", "Code.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft VS Code", "Code.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "bin", "code.cmd"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft VS Code", "bin", "code.cmd"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft VS Code", "bin", "code.cmd"),
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            _VSCODE_COMMAND = candidate
            return candidate

    return None


def _open_in_vscode(abs_path: str, line: int, column: int) -> tuple[bool, str]:
    command = _find_vscode_command()
    target = f"{abs_path}:{line}:{column}"

    if not command:
        return False, "找不到 VS Code 命令列程式，無法自動開啟檔案。"

    cmdline = [command, "--reuse-window", "--goto", target]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        completed = subprocess.run(
            cmdline,
            cwd=str(Path(abs_path).parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=_VSCODE_OPEN_TIMEOUT_SECONDS,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired:
        return True, "已送出 VS Code 開啟命令。"
    except Exception as exc:
        log.exception("Failed to open file in VS Code: %s", abs_path)
        return False, f"無法自動開啟 VS Code：{exc}"

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if detail:
            return False, f"VS Code 開啟失敗：{detail}"
        return False, f"VS Code 開啟失敗，結束碼 {completed.returncode}。"

    return True, "已送出 VS Code 開啟命令。"


def _offset_to_line_column(line_starts: list[int], offset: int) -> tuple[int, int]:
    left = 0
    right = len(line_starts) - 1

    while left <= right:
        middle = (left + right) // 2
        line_start = line_starts[middle]
        next_start = line_starts[middle + 1] if middle + 1 < len(line_starts) else 10**18
        if line_start <= offset < next_start:
            return middle + 1, (offset - line_start) + 1
        if offset < line_start:
            right = middle - 1
        else:
            left = middle + 1

    last_index = max(0, len(line_starts) - 1)
    return last_index + 1, 1


def _line_starts(text: str) -> list[int]:
    starts = [0]
    starts.extend(match.end() for match in re.finditer(r"\n", text))
    if starts[-1] != len(text):
        starts.append(len(text))
    return starts


def _is_ignored_char(char: str) -> bool:
    return char in {"\u200b", "\u200c", "\u200d", "\ufeff"}
