from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen


WEBHOOK_URL = (
    "https://discord.com/api/webhooks/"
    "1411555147670097940/"
    "jHBSFWEVlC4sEthiTmYw6I0HrDqyr7ZFDQdyuzrR_627q1aYi80IYhUwqp5S3U7T5bKG"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="傳送 Codex 完成通知到 Discord。")
    parser.add_argument("title", help="通知標題")
    parser.add_argument("summary", help="通知摘要")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    content = f"{args.title}\n已完成{args.summary}"
    payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
    request = Request(
        WEBHOOK_URL,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "CodexNotifier/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            status = getattr(response, "status", 204)
    except Exception as exc:
        print(f"通知失敗：{exc}", file=sys.stderr)
        return 1
    if status >= 400:
        print(f"通知失敗：HTTP {status}", file=sys.stderr)
        return 1
    print("通知成功")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
