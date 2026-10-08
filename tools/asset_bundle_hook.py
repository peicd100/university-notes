"""Bundle the two same-directory custom stylesheets without changing cascade order."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import tinycss2
from mkdocs.structure.files import File

_BUNDLE: tuple[str, str] | None = None
_ORIGINAL_EXTRAS: list[Any] | None = None
_GROUPS = {"media", "supports", "container", "layer", "scope"}


def _compact(tokens: list[Any]) -> list[Any]:
    result = []
    for token in tokens:
        if token.type == "comment":
            continue
        if token.type == "whitespace":
            token.value = " "  # Retain required selector/calc token separation.
            if result and result[-1].type == "whitespace":
                continue
        if hasattr(token, "content") and token.content is not None:
            token.content = _compact(token.content)
        if hasattr(token, "arguments"):
            token.arguments = _compact(token.arguments)
        result.append(token)
    return result


def compact_css(source: str) -> str:
    """Remove comments, whitespace and earlier exact duplicate rules only.

    Never discard merely overridden declarations, fallbacks, differently scoped
    rules, or reorder selectors; those transformations can change appearance.
    """
    rules = tinycss2.parse_stylesheet(source, skip_comments=True, skip_whitespace=True)

    def process(items):
        seen = set()
        keep = []
        for rule in reversed(items):
            if rule.type == "error":
                raise ValueError(f"CSS parse error at {rule.source_line}: {rule.message}")
            if rule.type == "qualified-rule":
                rule.prelude = _compact(rule.prelude)
                rule.content = _compact(rule.content)
                key = (tinycss2.serialize(rule.prelude).strip(), tinycss2.serialize(rule.content).strip())
                if key in seen:
                    continue
                seen.add(key)
            elif rule.type == "at-rule":
                rule.prelude = _compact(rule.prelude)
                if rule.content is not None:
                    if rule.lower_at_keyword in _GROUPS:
                        children = tinycss2.parse_rule_list(rule.content, skip_comments=True, skip_whitespace=True)
                        rule.content = tinycss2.parse_component_value_list(process(children))
                    else:
                        rule.content = _compact(rule.content)
            keep.append(rule)
        return tinycss2.serialize(list(reversed(keep)))

    return process(rules)


def on_config(config: Any) -> Any:
    global _BUNDLE, _ORIGINAL_EXTRAS
    extras = list(config["extra_css"])
    # MkDocs can reuse its Config on dirty rebuilds. Recover the author-provided
    # inputs instead of losing the generated file or bundling yesterday's bundle.
    if _BUNDLE and _ORIGINAL_EXTRAS and _BUNDLE[0] in extras:
        index = extras.index(_BUNDLE[0])
        originals = [x for x in _ORIGINAL_EXTRAS if urlsplit(str(x)).path in {
            "assets/pymdownx-extras/extra-8611f6c398.css", "assets/pymdownx-extras/自定義.css"}]
        extras[index:index+1] = originals
    _BUNDLE = None
    wanted = {"assets/pymdownx-extras/extra-8611f6c398.css", "assets/pymdownx-extras/自定義.css"}
    matches = [(i, urlsplit(str(url)).path) for i, url in enumerate(extras) if urlsplit(str(url)).path in wanted]
    # Only merge adjacent files in their existing order; intervening stylesheets
    # or a changed custom_dir must retain their original cascade.
    if len(matches) != 2 or matches[1][0] != matches[0][0] + 1:
        return config
    custom = Path(config["theme"].get("custom_dir") or "theme")
    if not custom.is_absolute():
        custom = Path(config["config_file_path"]).resolve().parent / custom
    paths = [custom / name for _, name in matches]
    if not all(path.is_file() for path in paths):
        return config
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    bundled = compact_css(source)
    digest = hashlib.sha256(bundled.encode("utf-8")).hexdigest()[:20]
    # Same directory preserves relative URLs embedded in either stylesheet.
    name = f"assets/pymdownx-extras/peicd-site.{digest}.css"
    config["extra_css"] = extras[:matches[0][0]] + [name] + extras[matches[1][0]+1:]
    _BUNDLE = (name, bundled)
    _ORIGINAL_EXTRAS = extras
    return config


def on_files(files: Any, /, *, config: Any) -> Any:
    if _BUNDLE:
        name, content = _BUNDLE
        files.append(File.generated(config, name, content=content))
    return files
