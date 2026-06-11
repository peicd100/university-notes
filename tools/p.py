#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    launcher = Path(sys.argv[0]).resolve()
    if (launcher.parent / "tools").is_dir():
        return launcher.parent
    return Path(__file__).resolve().parents[1]


ROOT = _project_root()


def _print_usage() -> None:
    print("Usage: p [Markdown path]")
    print(r"Example: p docs\md\...\file.md")
    print("Without a path, p uses the previous target in mkdocs.preview.yml.")


def _run(command: list[str]) -> int:
    return subprocess.call(command, cwd=str(ROOT))


def _wait_for_server(command: list[str]) -> int:
    process = subprocess.Popen(command, cwd=str(ROOT))
    try:
        return process.wait()
    except KeyboardInterrupt:
        try:
            return process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                return process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return 130


def main() -> int:
    args = sys.argv[1:]
    if args and args[0].lower() in {"/?", "-h", "--help"}:
        _print_usage()
        return 0

    update_command = [sys.executable, str(ROOT / "tools" / "update_preview_config.py"), *args]
    result = _run(update_command)
    if result:
        return result

    if os.environ.get("PREVIEW_SKIP_SERVE", "").lower() == "1":
        print("Prepared preview target. Skipped mkdocs serve because PREVIEW_SKIP_SERVE=1.")
        return 0

    serve_command = [
        sys.executable,
        "-m",
        "mkdocs",
        "serve",
        "-f",
        str(ROOT / "mkdocs.preview.yml"),
        "--dirty",
    ]
    return _wait_for_server(serve_command)


if __name__ == "__main__":
    raise SystemExit(main())
