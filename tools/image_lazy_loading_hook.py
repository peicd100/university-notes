"""Optimize article images and expose page feature flags for asset loading."""

from __future__ import annotations

import base64
import hashlib
from html.parser import HTMLParser
import posixpath
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from tools.optimized_images import derive_image

DATA_IMAGE_RE = re.compile(r"^data:(image/[A-Za-z0-9.+-]+)(;[^,]*)?,(.*)$", re.DOTALL)
EXTENSION_BY_MIME = {
    "image/apng": ".apng",
    "image/avif": ".avif",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
}
GENERATED_IMAGE_DIR = "assets/generated/base64-images"
_LOGOS: dict[str, dict[str, Any] | None] = {}


def on_config(config: Any) -> Any:
    _LOGOS.clear()
    return config


def on_pre_build(*, config: Any) -> None:
    # Every clean/dirty build must re-stage cached logo files in its site_dir.
    _LOGOS.clear()


def _local_image(src: str, page: Any, config: Any) -> Path | None:
    # Remote/data URLs, fragments and paths outside docs are never read.
    parsed = urlsplit(src)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    docs = Path(config["docs_dir"]).resolve()
    page_source = str(getattr(getattr(page, "file", None), "src_uri", "index.md"))
    relative = unquote(parsed.path)
    if relative.startswith("/"):
        source = docs / relative.lstrip("/")
    else:
        source = docs / Path(page_source).parent / relative
    source = source.resolve()
    if source.is_relative_to(docs) and source.is_file():
        return source
    # Already-externalized base64 images live in staging site_dir, not docs.
    site = Path(config["site_dir"]).resolve()
    generated = (site / Path(_page_url(page)).parent / relative).resolve()
    if generated.is_relative_to(site / "assets/generated") and generated.is_file():
        return generated
    return None


def _intrinsic_dimensions(source: Path) -> tuple[int, int] | None:
    # Header-only read; no conversion or source mutation. JPEG/GIF/WebP and PNGs
    # retained by the optimizer still need space reserved before lazy loading.
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(source) as image:
            width, height = image.size
            if image.getexif().get(274) in (5, 6, 7, 8):
                width, height = height, width  # Match browser EXIF orientation.
            return (width, height) if width > 0 and height > 0 else None
    except (OSError, ValueError, Image.DecompressionBombError):
        return None


def _optimize_image(img: Any, page: Any, config: Any) -> None:
    src = str(img.get("src") or "")
    width = re.search(r"=(\d+)%x$", src)
    if width:
        src = src[:width.start()]
        img["style"] = (str(img.get("style") or "").rstrip("; ") +
                        f"; width:{width.group(1)}%; height:auto;").lstrip("; ")
        img["src"] = src  # Apply legacy width before a browser makes a malformed request.
    source = _local_image(src, page, config)
    if source is None:
        return
    derived = derive_image(source, config)
    if derived:
        img["src"] = _relative_asset_url(page, derived["url"])
        img["data-peicd-optimized-image"] = "lossless"
    if not img.get("width") and not img.get("height"):
        dimensions = (derived["width"], derived["height"]) if derived else _intrinsic_dimensions(source)
        if dimensions:
            img["width"], img["height"] = map(str, dimensions)


def on_page_context(context: dict[str, Any], /, *, page: Any, config: Any, nav: Any) -> dict[str, Any]:
    for key, favicon in (("logo", False), ("favicon", True)):
        raw = config["theme"].get(key)
        if not raw or urlsplit(str(raw)).scheme or str(raw).startswith("//"):
            continue
        docs = Path(config["docs_dir"]).resolve()
        source = (docs / str(raw)).resolve()
        if not source.is_relative_to(docs):
            continue
        cache_key = str(source) + f"/favicon={favicon}"
        if cache_key not in _LOGOS:
            _LOGOS[cache_key] = derive_image(source, config, logo=not favicon, favicon=favicon)
        derived = _LOGOS[cache_key]
        if derived:
            context[f"peicd_optimized_{key}"] = derived["url"]
            context[f"peicd_{key}_width"] = derived["width"]
            context[f"peicd_{key}_height"] = derived["height"]
            if favicon:
                page.meta["peicd_optimized_favicon"] = _relative_asset_url(page, derived["url"])
    return context


def on_post_page(output: str, /, *, page: Any, config: Any) -> str:
    favicon = page.meta.get("peicd_optimized_favicon")
    if favicon:
        output = re.sub(r'(<link\s+rel="icon"\s+href=")[^"]+("[^>]*>)',
                        lambda m: m.group(1) + favicon + m.group(2), output, count=1)
    return output


def _classes(node: Any) -> set[str]:
    value = node.get("class", []) if node else []
    if isinstance(value, str):
        return set(value.split())
    return {str(item) for item in value}


def _is_article_image(img: Any) -> bool:
    classes = _classes(img)
    parent_classes = _classes(getattr(img, "parent", None))
    if "twemoji" in classes or "twemoji" in parent_classes:
        return False
    if "peicd-image-viewer__img" in classes or "peicd-mermaid-viewer__svg" in classes:
        return False
    return bool(img.get("src"))


def _config_get(config: Any, key: str, default: Any = None) -> Any:
    if hasattr(config, "get"):
        return config.get(key, default)
    return getattr(config, key, default)


def _page_url(page: Any) -> str:
    value = getattr(page, "url", "") or getattr(getattr(page, "file", None), "url", "")
    return str(value or "index.html").replace("\\", "/")


def _relative_asset_url(page: Any, asset_url: str) -> str:
    page_url = _page_url(page)
    page_dir = page_url.rstrip("/") if page_url.endswith("/") else posixpath.dirname(page_url)
    return posixpath.relpath(asset_url, start=page_dir or ".")


def _decode_base64_image(src: str) -> tuple[str, bytes] | None:
    match = DATA_IMAGE_RE.match(src.strip())
    if not match:
        return None

    mime_type = match.group(1).lower()
    metadata = match.group(2) or ""
    payload = match.group(3)
    if "base64" not in metadata.lower():
        return None

    extension = EXTENSION_BY_MIME.get(mime_type)
    if not extension:
        return None

    compact_payload = re.sub(r"\s+", "", payload)
    try:
        return extension, base64.b64decode(compact_payload, validate=True)
    except ValueError:
        return None


def _write_generated_image(config: Any, extension: str, data: bytes) -> str | None:
    site_dir = _config_get(config, "site_dir")
    if not site_dir:
        return None

    digest = hashlib.sha256(data).hexdigest()
    asset_url = posixpath.join(GENERATED_IMAGE_DIR, digest[:2], digest + extension)
    output_path = Path(site_dir).joinpath(*asset_url.split("/"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not output_path.exists() or output_path.read_bytes() != data:
        output_path.write_bytes(data)

    return asset_url


def _externalize_base64_image(img: Any, page: Any, config: Any) -> bool:
    decoded = _decode_base64_image(str(img.get("src") or ""))
    if not decoded:
        return False

    extension, data = decoded
    asset_url = _write_generated_image(config, extension, data)
    if not asset_url:
        return False

    img["src"] = _relative_asset_url(page, asset_url)
    img["data-peicd-externalized-image"] = "true"
    return True


def _set_page_flags(page: Any, soup: BeautifulSoup, images: list[Any], externalized_count: int) -> None:
    meta = getattr(page, "meta", None)
    if not isinstance(meta, dict):
        return

    meta["peicd_has_article_images"] = bool(images)
    meta["peicd_has_legacy_image_width"] = any(
        re.search(r"=\d+%x$", str(img.get("src") or "")) for img in images
    )
    meta["peicd_has_markdown_embed"] = bool(soup.select_one("[data-peicd-markdown-embed]"))
    meta["peicd_has_math"] = bool(soup.select_one(".arithmatex"))
    meta["peicd_has_mermaid"] = bool(soup.select_one("pre.diagram, .peicd-mermaid-host"))
    meta["peicd_externalized_images"] = externalized_count


def _soup_page_content(html: str, /, *, page: Any, config: Any, files: Any) -> str:
    """Compatibility fallback for HTML the streaming parser cannot read."""
    soup = BeautifulSoup(html, "html.parser")
    images = [img for img in soup.find_all("img") if _is_article_image(img)]
    externalized_count = 0

    for index, img in enumerate(images):
        if _externalize_base64_image(img, page, config):
            externalized_count += 1
        _optimize_image(img, page, config)

        img["decoding"] = "async"
        if index == 0:
            if img.get("loading") == "lazy":
                del img["loading"]
        elif not img.get("loading"):
            img["loading"] = "lazy"

    _set_page_flags(page, soup, images, externalized_count)
    return str(soup)


class _ArticleImages(HTMLParser):
    """Inspect tags once; keep the rest of the document out of an HTML tree."""

    _VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())

    def __init__(self, html: str):
        super().__init__(convert_charrefs=True)
        self.offsets = [0] + [m.end() for m in re.finditer("\n", html)]
        self.stack: list[tuple[str, set[str]]] = []
        self.images: list[tuple[int, str]] = []
        self.voids: list[tuple[int, str]] = []
        self.needs_tree = False
        self.flags = {"peicd_has_markdown_embed": False, "peicd_has_math": False,
                      "peicd_has_mermaid": False}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        self.flags["peicd_has_markdown_embed"] |= "data-peicd-markdown-embed" in values
        self.flags["peicd_has_math"] |= "arithmatex" in classes
        self.flags["peicd_has_mermaid"] |= (
            (tag == "pre" and "diagram" in classes) or "peicd-mermaid-host" in classes)
        parent_classes = self.stack[-1][1] if self.stack else set()
        if (tag == "img" and values.get("src") and "twemoji" not in parent_classes
                and not classes.intersection({"twemoji", "peicd-image-viewer__img", "peicd-mermaid-viewer__svg"})):
            line, column = self.getpos()
            self.images.append((self.offsets[line - 1] + column, self.get_starttag_text()))
        elif tag in self._VOID and not self.get_starttag_text().endswith("/>"):
            # Keep void-tag serialization consistent with the old soup output.
            # Some downstream parsers mishandle mixed <img> and <img/> forms.
            line, column = self.getpos()
            self.voids.append((self.offsets[line - 1] + column, self.get_starttag_text()))
        if tag not in self._VOID:
            self.stack.append((tag, classes))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self._VOID:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        if tag in self._VOID:
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.needs_tree |= index != len(self.stack) - 1
                del self.stack[index:]
                return
        self.needs_tree = True


def on_page_content(html: str, /, *, page: Any, config: Any, files: Any) -> str:
    parser = _ArticleImages(html)
    try:
        parser.feed(html)
        parser.close()
    except (AssertionError, ValueError):
        return _soup_page_content(html, page=page, config=config, files=files)
    if parser.needs_tree or parser.stack:
        # Legacy raw HTML can rely on soup inserting missing closing tags.
        # Retain that repair before search and other downstream HTML consumers.
        return _soup_page_content(html, page=page, config=config, files=files)

    replacements = [(offset, raw, raw[:-1] + "/>") for offset, raw in parser.voids]
    cursor = externalized = 0
    legacy_width = False
    for index, (offset, raw) in enumerate(parser.images):
        # Only individual image tags need BeautifulSoup's attribute handling.
        img = BeautifulSoup(raw, "html.parser").img
        if _externalize_base64_image(img, page, config):
            externalized += 1
        _optimize_image(img, page, config)
        img["decoding"] = "async"
        if index == 0 and img.get("loading") == "lazy":
            del img["loading"]
        elif index > 0 and not img.get("loading"):
            img["loading"] = "lazy"
        legacy_width |= bool(re.search(r"=\d+%x$", str(img.get("src") or "")))
        replacements.append((offset, raw, str(img)))
    pieces: list[str] = []
    for offset, raw, replacement in sorted(replacements):
        pieces.extend((html[cursor:offset], replacement))
        cursor = offset + len(raw)
    pieces.append(html[cursor:])
    if isinstance(getattr(page, "meta", None), dict):
        page.meta.update(parser.flags)
        page.meta.update(peicd_has_article_images=bool(parser.images),
                         peicd_has_legacy_image_width=legacy_width,
                         peicd_externalized_images=externalized)
    return "".join(pieces)
