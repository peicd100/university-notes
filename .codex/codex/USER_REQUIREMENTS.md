# USER REQUIREMENTS

## 長期要求

- 狀態：active
- 證據：user-requested
- 日期：2026-05-18
- 正確做法：
  - 全程使用繁體中文。
  - 中文文字檔使用 UTF-8 無 BOM。
  - 沒有被要求修改檔案時，不主動改檔。
  - 使用 conda 管理 Python；本專案使用 `mkdocs` 環境。
  - 完成任務後要說明做了什麼、怎麼做、用了什麼。
  - 專案修改時要同步維護 `.codex/codex/` 協作檔。
  - 人工驗證輸出統一放 `.codex/codex/tmp/`，不要散在根目錄。

## Preview 與 UI 偏好

- 狀態：active
- 證據：user-requested
- 日期：2026-05-18
- 正確做法：
  - 單頁 preview 可用 `.\p <Markdown 路徑>`，也可只輸入 `.\p` 沿用上次目標。
  - Preview 右鍵「開啟原文檔案」要優先追求定位準確度，避免跳到同頁錯誤段落。
  - 保留 Material 內建 `Back to top`，右下角 `Back to bottom` 是額外功能。
  - UI 預設重點色可用 `#72e3fd`，但不要大面積無腦鋪滿。

## 多益600

- 狀態：active
- 證據：user-requested
- 日期：2026-05-18
- 正確做法：
  - `docs/md/多益600` 併入主專案。
  - 保留筆記、圖片、includes、`紀錄.py` 與工具文件。
  - 生成影片、TTS 暫存、測試媒體與本機紀錄不得上傳到 Git。
