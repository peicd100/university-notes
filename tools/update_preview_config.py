from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
PREVIEW_CONFIG = ROOT / "mkdocs.preview.yml"
MANAGED_START = "# preview-target:start"
MANAGED_END = "# preview-target:end"
NAV_BLOCK_PATTERN = re.compile(
    r"(?ms)^nav:\n(?:^[ \t].*\n|^\n)*^exclude_docs:\s*\|\n(?:^[ \t].*\n|^\n)*(?=^\S|\Z)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="更新 mkdocs.preview.yml 的單頁 preview 目標。",
    )
    parser.add_argument(
        "path_parts",
        nargs="*",
        help="目標 Markdown 路徑，可用 docs/... 或 docs_dir 相對路徑。省略時沿用上一次 preview 目標。",
    )
    return parser.parse_args()


def _clean_input(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts).strip().strip("\"'")


def _resolve_candidate(raw_path: str) -> Path | None:
    normalized = raw_path.replace("/", os.sep).replace("\\", os.sep)
    candidate_path = Path(normalized)

    candidates: list[Path] = []
    if candidate_path.is_absolute():
        candidates.append(candidate_path)
    else:
        candidates.append(ROOT / candidate_path)
        if normalized.lower().startswith(f"docs{os.sep}"):
            candidates.append(DOCS_ROOT / normalized.split(os.sep, 1)[1])
        else:
            candidates.append(DOCS_ROOT / candidate_path)

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return None


def normalize_markdown_path(raw_path: str) -> tuple[Path, str]:
    if not raw_path:
        raise SystemExit("請提供要預覽的 Markdown 路徑。")

    target = _resolve_candidate(raw_path)
    if target is None:
        raise SystemExit(f"找不到檔案：{raw_path}")

    try:
        relative_to_docs = target.relative_to(DOCS_ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(f"目標檔案必須位於 docs 目錄內：{target}") from exc

    if target.suffix.lower() != ".md":
        raise SystemExit(f"只支援 Markdown 檔案：{target}")

    return target, relative_to_docs.as_posix()


def yaml_single_quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_managed_block(relative_markdown_path: str) -> str:
    quoted = yaml_single_quoted(relative_markdown_path)
    return (
        f"{MANAGED_START}\n"
        "nav:\n"
        f"  - {quoted}\n"
        "\n"
        "exclude_docs: |\n"
        "  *.md\n"
        f"  !/{relative_markdown_path}\n"
        "  !/index.md\n"
        f"{MANAGED_END}\n"
    )


def _yaml_unquote_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def read_current_preview_target(config_text: str) -> str:
    if MANAGED_START not in config_text or MANAGED_END not in config_text:
        raise SystemExit("mkdocs.preview.yml 缺少 preview managed 區塊，請先用 preview.bat <Markdown path> 設定一次。")

    start = config_text.index(MANAGED_START) + len(MANAGED_START)
    end = config_text.index(MANAGED_END, start)
    managed_block = config_text[start:end]
    nav_match = re.search(r"(?m)^[ \t]*-[ \t]*(.+?)\s*$", managed_block)
    if nav_match is None:
        raise SystemExit("mkdocs.preview.yml 找不到上一次 preview 目標。")

    target = _yaml_unquote_scalar(nav_match.group(1))
    if not target:
        raise SystemExit("mkdocs.preview.yml 的上一次 preview 目標是空值。")
    return target


def replace_managed_block(config_text: str, managed_block: str) -> str:
    if MANAGED_START in config_text and MANAGED_END in config_text:
        start = config_text.index(MANAGED_START)
        end = config_text.index(MANAGED_END) + len(MANAGED_END)
        if end < len(config_text) and config_text[end:end + 1] == "\n":
            end += 1
        return config_text[:start] + managed_block + config_text[end:]

    match = NAV_BLOCK_PATTERN.search(config_text)
    if match is None:
        raise SystemExit("在 mkdocs.preview.yml 中找不到可更新的 nav / exclude_docs 區塊。")
    return config_text[:match.start()] + managed_block + config_text[match.end():]


def main() -> int:
    args = parse_args()
    raw_path = _clean_input(args.path_parts)

    config_text = PREVIEW_CONFIG.read_text(encoding="utf-8")
    if raw_path:
        absolute_target, relative_markdown_path = normalize_markdown_path(raw_path)
        updated = replace_managed_block(config_text, build_managed_block(relative_markdown_path))
        PREVIEW_CONFIG.write_text(updated, encoding="utf-8", newline="\n")
        print(f"preview target: {relative_markdown_path}")
        print(f"absolute file:  {absolute_target}")
        print(f"updated config: {PREVIEW_CONFIG}")
        return 0

    relative_markdown_path = read_current_preview_target(config_text)
    absolute_target, relative_markdown_path = normalize_markdown_path(relative_markdown_path)
    print(f"preview target: {relative_markdown_path}")
    print(f"absolute file:  {absolute_target}")
    print(f"using config:   {PREVIEW_CONFIG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
