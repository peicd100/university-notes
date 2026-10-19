"""Whole-site MkDocs preview with validated, cross-process Markdown render reuse.

Page.render and Material's pure search-entry extraction are cached. Source
reading, metadata, hooks, templates, index assembly and encryption still run.
"""
from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Mapping
from functools import partial
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any
import uuid

import mkdocs
import yaml
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import get_toc

log = logging.getLogger("mkdocs.preview_cache")
SCHEMA = 1


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _stable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_stable(v) for v in value]
    if isinstance(value, partial):
        return {"partial": _stable(value.func), "args": _stable(value.args),
                "kwargs": _stable(value.keywords)}
    if callable(value) and hasattr(value, "__qualname__"):
        module = getattr(value, "__module__", None) or getattr(value, "__objclass__", type(value)).__module__
        return {"callable": module + "." + value.__qualname__}
    raise ValueError("Unsupported render configuration; bypass cache")


def _toc_tokens(items: Any) -> list[dict[str, Any]]:
    return [{"name": item.title, "id": item.id, "level": item.level,
             "children": _toc_tokens(item.children)} for item in items]


def _config_inputs(path: Path, seen: set[Path] | None = None) -> dict[str, str]:
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        return {}
    seen.add(path)
    raw = path.read_bytes()
    result = {str(path): _hash(raw)}
    data = yaml.load(raw, Loader=yaml.BaseLoader)
    inherited = data.get("INHERIT") if isinstance(data, dict) else None
    if inherited:
        result.update(_config_inputs(path.parent / inherited, seen))
    return result


class RenderCache:
    def __init__(self, enabled: bool = True):
        # This adapter restores the Page.render fields used by MkDocs 1.6.1.
        self.enabled = enabled and mkdocs.__version__ == "1.6.1"
        # sys.path may expose the same local distribution more than once.
        # Duplicate discovery is not an environment change.
        self.versions = sorted({(d.metadata.get("Name", ""), d.version)
                                for d in importlib.metadata.distributions()})
        self.scope: str | None = None
        self.directory: Path | None = None
        self.bypassed = False
        self.hits = self.misses = self.skipped = 0

    def begin_build(self) -> None:
        self.scope = None
        self.bypassed = False
        self.hits = self.misses = self.skipped = 0

    def _prepare(self, config: Any, files: Any) -> str:
        if self.scope is not None:
            return self.scope
        config_path = Path(config["config_file_path"]).resolve()
        project = config_path.parent
        dependencies = _config_inputs(config_path)
        # Local extension/hook implementations and theme changes invalidate reuse.
        paths = [p for p in (project / "tools").glob("*.py") if not p.name.startswith("test_")]
        custom = getattr(config["theme"], "custom_dir", None)
        if custom:
            theme = (project / custom).resolve()
            paths.extend(p for p in theme.rglob("*") if p.is_file())
        paths.extend(p for p in (project / "requirements.txt", project / "pyproject.toml") if p.is_file())
        dependencies.update({str(p.resolve()): _hash(p.read_bytes()) for p in paths})
        signature = {"schema": SCHEMA, "dependencies": dependencies,
                     "versions": self.versions, "python": sys.version,
                     "extensions": _stable(config["markdown_extensions"]),
                     "extension_options": _stable(config["mdx_configs"]),
                     "site_url": config["site_url"],
                     "directory_urls": config["use_directory_urls"],
                     "catalog": sorted((f.src_uri, f.dest_uri, f.inclusion.value) for f in files)}
        self.scope = _hash(_json(signature).encode())
        self.directory = project / ".cache/preview-render"
        return self.scope

    def render(self, original: Any, page: Page, config: Any, files: Any) -> None:
        text = page.markdown or ""
        # Includes can read arbitrary nested/local/remote dependencies. Re-run them
        # rather than claiming that the parent Markdown hash validates those inputs.
        if (not self.enabled or self.bypassed or type(page) is not Page or "--8<" in text or "{!" in text
                or config["strict"] or log.getEffectiveLevel() <= logging.DEBUG):
            self.skipped += 1
            return original(page, config, files)
        try:
            scope = self._prepare(config, files)
        except (OSError, ValueError, TypeError, yaml.YAMLError):
            self.bypassed = True
            self.skipped += 1
            return original(page, config, files)
        key = _hash(_json([scope, page.file.src_uri, page.file.dest_uri, text]).encode())
        slot = self.directory / (_hash(page.file.src_uri.encode()) + ".json")
        try:
            envelope = json.loads(slot.read_text(encoding="utf8"))
            payload = envelope["payload"]
            if (envelope["schema"] != SCHEMA or envelope["key"] != key
                    or _hash(_json(payload).encode()) != envelope["sha256"]
                    or not isinstance(payload["content"], str)
                    or not (payload["title"] is None or isinstance(payload["title"], str))):
                raise ValueError("Invalid preview render cache")
            toc = get_toc(payload["toc"])
            anchors = set(payload["anchors"]) if payload["anchors"] is not None else None
            links = None
            if payload["links"] is not None:
                links = {}
                for src, targets in payload["links"]:
                    file = files.get_file_from_path(src)
                    if file is None or not isinstance(targets, dict):
                        raise ValueError("Cached link target no longer exists")
                    links[file] = targets
            page.content, page.toc = payload["content"], toc
            page._title_from_render = payload["title"]
            page.present_anchor_ids, page.links_to_anchors = anchors, links
            self.hits += 1
            return
        except (OSError, ValueError, KeyError, TypeError, AttributeError, AssertionError):
            pass  # Missing, changed, partial or corrupt cache: parse the real source.
        self.misses += 1
        original(page, config, files)
        payload = {"content": page.content, "title": page._title_from_render,
                   "toc": _toc_tokens(page.toc),
                   "anchors": sorted(page.present_anchor_ids, key=_json) if page.present_anchor_ids is not None else None,
                   "links": [[f.src_uri, targets] for f, targets in page.links_to_anchors.items()]
                            if page.links_to_anchors is not None else None}
        envelope = {"schema": SCHEMA, "key": key, "payload": payload,
                    "sha256": _hash(_json(payload).encode())}
        temporary = slot.with_suffix(f".{uuid.uuid4().hex}.tmp")
        try:
            slot.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(_json(envelope), encoding="utf8")
            os.replace(temporary, slot)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            log.warning("Preview render cache could not be saved: %s", error)


class SearchCache:
    """Replay validated per-page entries into each new Material SearchIndex.

    The plugin still handles exclusion, data-search attributes, dirty merging
    and writing the complete index. No plugin instance or page object is saved.
    """

    def __init__(self, render_cache: RenderCache, index_type: type):
        self.render_cache, self.index_type = render_cache, index_type
        try:
            self.enabled = importlib.metadata.version("mkdocs-material") == "9.7.1"
        except importlib.metadata.PackageNotFoundError:
            self.enabled = False
        self.begin_build()

    def begin_build(self) -> None:
        self.hits = self.misses = self.skipped = 0

    def add(self, original: Any, index: Any, page: Page) -> None:
        cache = self.render_cache
        if (not self.enabled or not cache.enabled or cache.bypassed or cache.scope is None
                or type(index) is not self.index_type
                or index.config.get("jieba_dict") or index.config.get("jieba_dict_user")):
            self.skipped += 1
            return original(index, page)
        try:
            key = _hash(_json([cache.scope, _stable(index.config), page.file.src_uri,
                               page.url, page.title, _stable(page.meta),
                               _toc_tokens(page.toc), page.content]).encode())
        except (ValueError, TypeError):
            self.skipped += 1
            return original(index, page)
        slot = cache.directory.parent / "preview-search" / (_hash(page.file.src_uri.encode()) + ".json")
        try:
            envelope = json.loads(slot.read_text(encoding="utf8"))
            entries = envelope["payload"]
            if (envelope["schema"] != SCHEMA or envelope["key"] != key
                    or _hash(_json(entries).encode()) != envelope["sha256"]
                    or not isinstance(entries, list)
                    or any(not isinstance(entry, dict) or
                           any(not isinstance(entry.get(k), str) for k in ("location", "title", "text"))
                           for entry in entries)):
                raise ValueError("Invalid preview search cache")
            index.entries.extend(entries)
            self.hits += 1
            return
        except (OSError, ValueError, KeyError, TypeError):
            pass
        self.misses += 1
        before = len(index.entries)
        original(index, page)
        entries = index.entries[before:]
        try:
            payload_hash = _hash(_json(entries).encode())
        except (TypeError, ValueError):
            return  # Material's final writer can stringify custom metadata.
        envelope = {"schema": SCHEMA, "key": key, "payload": entries,
                    "sha256": payload_hash}
        temporary = slot.with_suffix(f".{uuid.uuid4().hex}.tmp")
        try:
            slot.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(_json(envelope), encoding="utf8")
            os.replace(temporary, slot)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            log.warning("Preview search cache could not be saved: %s", error)


@contextmanager
def cached_preview(enabled: bool = True):
    from mkdocs.commands import serve
    cache = RenderCache(enabled)
    try:
        from material.plugins.search.plugin import SearchIndex
    except ImportError:
        SearchIndex = None
    search = SearchCache(cache, SearchIndex) if SearchIndex is not None else None
    cache.search_cache = search
    original_search = SearchIndex.add_entry_from_context if search else None
    original_render, original_build = Page.render, serve.build
    def render(page, config, files):
        return cache.render(original_render, page, config, files)
    def add_search(index, page):
        return search.add(original_search, index, page)
    def build(config, **kwargs):
        cache.begin_build()
        if search:
            search.begin_build()
        result = original_build(config, **kwargs)
        log.info("Preview render cache: %d reused, %d rebuilt, %d bypassed",
                 cache.hits, cache.misses, cache.skipped)
        if search:
            log.info("Preview search cache: %d reused, %d rebuilt, %d bypassed",
                     search.hits, search.misses, search.skipped)
        return result
    Page.render, serve.build = render, build
    if search:
        SearchIndex.add_entry_from_context = add_search
    try:
        yield cache
    finally:
        Page.render, serve.build = original_render, original_build
        if search:
            SearchIndex.add_entry_from_context = original_search


def main(argv: list[str] | None = None) -> None:
    from mkdocs.__main__ import cli
    args = list(sys.argv[1:] if argv is None else argv)
    fresh = "--fresh" in args
    args = [arg for arg in args if arg != "--fresh"]
    if "--help" in args or "-h" in args:
        print("s: whole-site cached preview. --fresh bypasses persistent render/search caches.")
    with cached_preview(enabled=not fresh and "--clean" not in args and "-c" not in args):
        cli(["serve", "--dirty", *args], prog_name="s")


if __name__ == "__main__":
    main()
