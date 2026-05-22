from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(os.path.abspath(__file__)).parent.parent
LOG_DIR = ROOT / ".codex" / "codex" / "tmp"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    slug = slug.strip("-._")
    return slug or "command"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="執行命令並把 stdout/stderr 統一寫到 .codex/codex/tmp。",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="這次驗證的短名稱，會出現在輸出檔名中。",
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="子程序工作目錄，預設為專案根目錄。",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="要執行的命令。請用 -- 把工具參數和命令本體分開。",
    )
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("缺少要執行的命令。用法：run_logged.py --name <name> -- <command> ...")
    return args


def main() -> int:
    args = parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _slugify(args.name)
    stem = f"{stamp}-{slug}"

    out_path = LOG_DIR / f"{stem}.out.log"
    err_path = LOG_DIR / f"{stem}.err.log"
    meta_path = LOG_DIR / f"{stem}.meta.json"
    cwd = Path(os.path.abspath(os.path.join(str(ROOT), args.cwd)))

    completed = subprocess.run(
        args.command,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    out_path.write_text(completed.stdout or "", encoding="utf-8", newline="\n")
    err_path.write_text(completed.stderr or "", encoding="utf-8", newline="\n")
    meta_path.write_text(
        json.dumps(
            {
                "command": args.command,
                "cwd": str(cwd),
                "returncode": completed.returncode,
                "stdout_log": str(out_path.relative_to(ROOT)),
                "stderr_log": str(err_path.relative_to(ROOT)),
                "timestamp": stamp,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"returncode: {completed.returncode}")
    print(f"stdout log: {out_path.relative_to(ROOT)}")
    print(f"stderr log: {err_path.relative_to(ROOT)}")
    print(f"meta log:   {meta_path.relative_to(ROOT)}")

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
