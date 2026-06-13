"""Add conservative lazy loading hints to article images."""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup


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


def on_page_content(html: str, /, *, page: Any, config: Any, files: Any) -> str:
    soup = BeautifulSoup(html, "html.parser")
    images = [img for img in soup.find_all("img") if _is_article_image(img)]

    for index, img in enumerate(images):
        img["decoding"] = "async"
        if index == 0:
            if img.get("loading") == "lazy":
                del img["loading"]
        elif not img.get("loading"):
            img["loading"] = "lazy"

    return str(soup)
