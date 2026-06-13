"""Optimize article images and expose page feature flags for asset loading."""

from __future__ import annotations

import base64
import hashlib
import posixpath
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

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


def on_page_content(html: str, /, *, page: Any, config: Any, files: Any) -> str:
    soup = BeautifulSoup(html, "html.parser")
    images = [img for img in soup.find_all("img") if _is_article_image(img)]
    externalized_count = 0

    for index, img in enumerate(images):
        if _externalize_base64_image(img, page, config):
            externalized_count += 1

        img["decoding"] = "async"
        if index == 0:
            if img.get("loading") == "lazy":
                del img["loading"]
        elif not img.get("loading"):
            img["loading"] = "lazy"

    _set_page_flags(page, soup, images, externalized_count)
    return str(soup)
