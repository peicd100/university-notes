from __future__ import annotations

import html
import logging
import os
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import markdown as markdown_lib
from mkdocs.structure.files import File, InclusionLevel


log = logging.getLogger("mkdocs.hooks.markdown_embed")

_FENCE_RE = re.compile(r"^(?P<indent>[ ]{0,3})(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
_EMBED_COMMAND_RE = re.compile(r"^(?P<indent>[ ]{0,3})!embed(?:\s*:\s*|\s+)(?P<body>.+?)\s*$")
_WIKI_EMBED_RE = re.compile(r"^(?P<indent>[ ]{0,3})!\[\[(?P<body>.+?)\]\]\s*$")
_MARKDOWN_LINK_RE = re.compile(r"^\[(?P<title>[^\]]+)\]\((?P<path>[^)]+)\)$")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_EMBED_SCROLL_GUARD_MARKER = "data-peicd-markdown-embed-scroll-guard"
_EMBED_SCROLL_GUARD_STYLE = f"""<style {_EMBED_SCROLL_GUARD_MARKER}>
  html, body {{
    overscroll-behavior: contain;
  }}
  body {{
    overflow-x: hidden;
  }}
</style>"""
_EMBED_SCROLL_GUARD_SCRIPT = f"""<script {_EMBED_SCROLL_GUARD_MARKER}>
(function () {{
  function scrollingElement() {{
    return document.scrollingElement || document.documentElement;
  }}

  document.addEventListener("wheel", function (event) {{
    var scroller = scrollingElement();
    if (!scroller) return;

    var maxY = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
    var top = scroller.scrollTop;
    var scrollingUpPastTop = event.deltaY < 0 && top <= 0;
    var scrollingDownPastBottom = event.deltaY > 0 && top >= maxY - 1;

    if (maxY <= 0 || scrollingUpPastTop || scrollingDownPastBottom) {{
      event.preventDefault();
    }}
  }}, {{ passive: false }});

  window.addEventListener("message", function (event) {{
    if (!event.data || event.data.type !== "peicd-markdown-embed-scroll") return;

    var scroller = scrollingElement();
    if (!scroller) return;

    scroller.scrollBy({{
      left: Number(event.data.deltaX) || 0,
      top: Number(event.data.deltaY) || 0,
      behavior: "auto"
    }});
  }});
}})();
</script>"""


@dataclass(frozen=True)
class EmbedRequest:
    path: str
    title: str | None = None


@dataclass(frozen=True)
class ResolvedTarget:
    src_uri: str
    fragment: str


def on_files(files: Any, /, *, config: Any) -> Any:
    file_by_src_uri = {_src_uri(file_obj): file_obj for file_obj in files if _src_uri(file_obj)}
    queue = [file_obj for file_obj in files if _is_markdown_page(file_obj)]
    generated_embed_uris = {
        _src_uri(file_obj)
        for file_obj in files
        if _src_uri(file_obj).endswith(".embed.html")
    }
    scanned: set[str] = set()

    while queue:
        file_obj = queue.pop(0)
        src_uri = _src_uri(file_obj)
        if not src_uri or src_uri in scanned:
            continue

        scanned.add(src_uri)
        markdown = _read_text(file_obj)
        if markdown is None:
            continue

        for request in _iter_embed_requests(markdown):
            target = _resolve_embed_path(request.path, file_obj, config)
            if target is None:
                continue

            _ensure_clean_embed_file(target.src_uri, request, files, config, generated_embed_uris)

            existing_file = file_by_src_uri.get(target.src_uri)
            if existing_file is not None:
                if target.src_uri not in scanned:
                    queue.append(existing_file)
                continue

            abs_path = _abs_docs_path(target.src_uri, config)
            if not abs_path.is_file():
                log.warning("Markdown embed target not found: %s", request.path)
                continue

            new_file = File(
                target.src_uri.replace("/", os.sep),
                config["docs_dir"],
                config["site_dir"],
                config["use_directory_urls"],
                inclusion=InclusionLevel.INCLUDED,
            )
            files.append(new_file)
            file_by_src_uri[target.src_uri] = new_file
            queue.append(new_file)
            log.debug("Added markdown embed target to files: %s", target.src_uri)

    return files


def on_page_markdown(markdown: str, /, *, page: Any, config: Any, files: Any) -> str:
    file_obj = getattr(page, "file", None)
    if file_obj is None:
        return markdown

    file_by_src_uri = {_src_uri(candidate): candidate for candidate in files if _src_uri(candidate)}
    converted_lines: list[str] = []
    open_fence: tuple[str, int] | None = None

    for line in markdown.splitlines(keepends=True):
        content, newline = _split_line_ending(line)

        if open_fence is not None:
            converted_lines.append(line)
            if _is_closing_fence(content, *open_fence):
                open_fence = None
            continue

        opening_fence = _parse_opening_fence(content)
        if opening_fence is not None:
            open_fence = opening_fence
            converted_lines.append(line)
            continue

        request = _parse_embed_line(content)
        if request is None:
            converted_lines.append(line)
            continue

        converted_lines.append(_render_embed(request, file_obj, config, file_by_src_uri) + newline)

    return "".join(converted_lines)


def _render_embed(
    request: EmbedRequest,
    source_file: Any,
    config: Any,
    file_by_src_uri: dict[str, Any],
) -> str:
    target = _resolve_embed_path(request.path, source_file, config)
    if target is None:
        return _render_warning(f"無法解析嵌入路徑：{request.path}")

    embed_src_uri = _embed_src_uri(target.src_uri)
    target_file = file_by_src_uri.get(embed_src_uri)
    if target_file is None:
        abs_path = _abs_docs_path(embed_src_uri, config)
        if abs_path.is_file():
            target_file = File(
                embed_src_uri.replace("/", os.sep),
                config["docs_dir"],
                config["site_dir"],
                config["use_directory_urls"],
            )
        else:
            return _render_warning(f"找不到嵌入檔案：{request.path}")

    url = target_file.url_relative_to(source_file)
    if target.fragment:
        url = f"{url}#{target.fragment}"

    title = request.title or PurePosixPath(target.src_uri).stem
    escaped_title = html.escape(title, quote=True)
    escaped_url = html.escape(url, quote=True)
    open_label = html.escape("開啟", quote=True)
    preview_label = html.escape("放大預覽", quote=True)
    close_label = html.escape("關閉預覽", quote=True)

    return "\n".join(
        [
            '<div class="peicd-markdown-embed" data-peicd-markdown-embed>',
            '  <div class="peicd-markdown-embed__toolbar">',
            f'    <div class="peicd-markdown-embed__title">{escaped_title}</div>',
            '    <div class="peicd-markdown-embed__actions">',
            f'      <a class="peicd-markdown-embed__control" href="{escaped_url}" target="_blank" rel="noreferrer noopener">{open_label}</a>',
            f'      <button class="peicd-markdown-embed__control" type="button" data-peicd-markdown-embed-preview aria-expanded="false">{preview_label}</button>',
            f'      <button class="peicd-markdown-embed__control peicd-markdown-embed__close" type="button" data-peicd-markdown-embed-close aria-label="{close_label}" title="{close_label}">×</button>',
            "    </div>",
            "  </div>",
            f'  <iframe class="peicd-markdown-embed__frame" src="{escaped_url}" title="{escaped_title}" loading="lazy"></iframe>',
            "</div>",
        ]
    )


def _render_warning(message: str) -> str:
    escaped = html.escape(message)
    return f'<div class="peicd-markdown-embed peicd-markdown-embed--missing">{escaped}</div>'


def _ensure_clean_embed_file(
    target_src_uri: str,
    request: EmbedRequest,
    files: Any,
    config: Any,
    generated_embed_uris: set[str],
) -> None:
    embed_src_uri = _embed_src_uri(target_src_uri)
    if embed_src_uri in generated_embed_uris:
        return

    source_path = _abs_docs_path(target_src_uri, config)
    if not source_path.is_file():
        log.warning("Markdown embed target not found: %s", request.path)
        return

    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("Failed to read markdown embed target: %s", exc)
        return

    content = _render_clean_embed_document(source_text, request.title or PurePosixPath(target_src_uri).stem)
    files.append(
        File.generated(
            config,
            embed_src_uri,
            content=content,
            inclusion=InclusionLevel.INCLUDED,
        )
    )
    generated_embed_uris.add(embed_src_uri)
    log.debug("Generated clean markdown embed page: %s", embed_src_uri)


def _render_clean_embed_document(source_text: str, title: str) -> str:
    stripped = source_text.lstrip()
    lowered = stripped[:128].lower()
    if lowered.startswith("<!doctype html") or lowered.startswith("<html"):
        return _with_embed_scroll_guard(source_text)

    markdown_text = _strip_front_matter(source_text)
    body = markdown_lib.markdown(
        markdown_text,
        extensions=[
            "markdown.extensions.extra",
            "markdown.extensions.attr_list",
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.nl2br",
            "pymdownx.superfences",
            "pymdownx.tasklist",
            "pymdownx.tilde",
            "pymdownx.caret",
            "pymdownx.mark",
            "pymdownx.keys",
        ],
        output_format="html5",
    )
    escaped_title = html.escape(title)
    return _with_embed_scroll_guard(f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escaped_title}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #fff;
    color: #1f2937;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", Arial, sans-serif;
    line-height: 1.65;
  }}
  main {{
    max-width: 1120px;
    margin: 0 auto;
    padding: 24px 18px 40px;
  }}
  img, svg, video, canvas {{ max-width: 100%; }}
  pre {{ overflow: auto; padding: 12px; background: #0f172a; color: #e5e7eb; border-radius: 8px; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #d1d5db; padding: 8px; }}
</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
""")


def _with_embed_scroll_guard(document: str) -> str:
    if _EMBED_SCROLL_GUARD_MARKER in document:
        return document

    with_style = _inject_before_closing_tag(document, "head", _EMBED_SCROLL_GUARD_STYLE)
    return _inject_before_closing_tag(with_style, "body", _EMBED_SCROLL_GUARD_SCRIPT)


def _inject_before_closing_tag(document: str, tag: str, snippet: str) -> str:
    match = re.search(rf"</{tag}\s*>", document, flags=re.IGNORECASE)
    if match is None:
        return f"{document}\n{snippet}"
    return f"{document[:match.start()]}\n{snippet}\n{document[match.start():]}"


def _strip_front_matter(source_text: str) -> str:
    if not source_text.startswith("---"):
        return source_text
    lines = source_text.splitlines(keepends=True)
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(lines[index + 1 :])
    return source_text


def _iter_embed_requests(markdown: str) -> list[EmbedRequest]:
    requests: list[EmbedRequest] = []
    open_fence: tuple[str, int] | None = None

    for line in markdown.splitlines():
        if open_fence is not None:
            if _is_closing_fence(line, *open_fence):
                open_fence = None
            continue

        opening_fence = _parse_opening_fence(line)
        if opening_fence is not None:
            open_fence = opening_fence
            continue

        request = _parse_embed_line(line)
        if request is not None:
            requests.append(request)

    return requests


def _parse_embed_line(line: str) -> EmbedRequest | None:
    command_match = _EMBED_COMMAND_RE.match(line)
    if command_match:
        return _parse_embed_body(command_match.group("body"))

    wiki_match = _WIKI_EMBED_RE.match(line)
    if wiki_match:
        return _parse_embed_body(wiki_match.group("body"))

    return None


def _parse_embed_body(body: str) -> EmbedRequest | None:
    body = body.strip()
    if not body:
        return None

    link_match = _MARKDOWN_LINK_RE.match(body)
    if link_match:
        return EmbedRequest(
            path=_strip_wrappers(link_match.group("path")),
            title=link_match.group("title").strip() or None,
        )

    if "|" in body:
        path, title = body.split("|", 1)
        return EmbedRequest(path=_strip_wrappers(path), title=title.strip() or None)

    return EmbedRequest(path=_strip_wrappers(body))


def _strip_wrappers(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == "<" and value[-1] == ">":
        value = value[1:-1].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1].strip()
    return value


def _resolve_embed_path(raw_path: str, source_file: Any, config: Any) -> ResolvedTarget | None:
    path_part, fragment = _split_fragment(raw_path)
    path_part = _strip_wrappers(path_part)
    if not path_part:
        return None

    absolute_src_uri = _absolute_path_to_src_uri(path_part, config)
    if absolute_src_uri is not None:
        return _as_markdown_target(absolute_src_uri, fragment)

    normalized = path_part.replace("\\", "/").strip()
    normalized = normalized.lstrip("/")
    if normalized.lower().startswith("docs/"):
        normalized = normalized[5:]
    elif normalized.startswith("./") or normalized.startswith("../"):
        source_dir = posixpath.dirname(_src_uri(source_file))
        normalized = posixpath.normpath(posixpath.join(source_dir, normalized))
    else:
        normalized = posixpath.normpath(normalized)

    return _as_markdown_target(normalized, fragment)


def _as_markdown_target(src_uri: str, fragment: str) -> ResolvedTarget | None:
    src_uri = src_uri.replace("\\", "/").lstrip("/")
    if not src_uri.lower().endswith(".md"):
        return None
    if src_uri.startswith("../") or "/../" in src_uri:
        return None
    return ResolvedTarget(src_uri=src_uri, fragment=fragment)


def _embed_src_uri(src_uri: str) -> str:
    return re.sub(r"\.md$", ".embed.html", src_uri, flags=re.IGNORECASE)


def _absolute_path_to_src_uri(raw_path: str, config: Any) -> str | None:
    if not (_WINDOWS_ABSOLUTE_RE.match(raw_path) or raw_path.startswith("\\\\")):
        return None

    candidate = Path(raw_path)
    try:
        abs_candidate = candidate.resolve()
    except OSError:
        abs_candidate = candidate.absolute()

    docs_dir = Path(config["docs_dir"]).resolve()
    try:
        return abs_candidate.relative_to(docs_dir).as_posix()
    except ValueError:
        return None


def _split_fragment(raw_path: str) -> tuple[str, str]:
    if "#" not in raw_path:
        return raw_path, ""
    path_part, fragment = raw_path.split("#", 1)
    return path_part, fragment.strip()


def _abs_docs_path(src_uri: str, config: Any) -> Path:
    return Path(config["docs_dir"], *src_uri.split("/"))


def _is_markdown_page(file_obj: Any) -> bool:
    return bool(getattr(file_obj, "is_documentation_page", False)) and _src_uri(file_obj).lower().endswith(".md")


def _read_text(file_obj: Any) -> str | None:
    try:
        return Path(file_obj.abs_src_path).read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("Failed to read markdown file for embed scan: %s", exc)
        return None


def _src_uri(file_obj: Any) -> str:
    return str(getattr(file_obj, "src_uri", "") or "").replace("\\", "/")


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
