# PROJECT

## 專案用途

`university notes` 是 MkDocs Material 筆記網站，用來維護大學課程筆記、Verilog 筆記、自訂前端互動與本機 preview 工具。

## 環境

- 專案目錄：`Y:\github_note\university notes`
- Python/conda 環境：`mkdocs`
- 常用 Python：`Y:\conda\envs\mkdocs\python.exe`
- 主要設定：`mkdocs.yml`
- 單頁 preview 設定：`mkdocs.preview.yml`

## 主要結構

- `docs/`：Markdown 內容、圖片、Logo。
- `docs/theme/`：覆蓋 Material 的模板與前端資產。
- `docs/theme/assets/pymdownx-extras/`：自訂 JS/CSS。
- `tools/`：MkDocs hooks 與輔助腳本。
- `preview.bat`、`p.bat`：Windows 單頁 preview 入口。
- `.codex/vbs_bat/`：雙擊啟動包裝。
- `.codex/codex/`：代理協作記憶、決策、踩坑與驗證紀錄。
- `docs/md/多益600/`：主專案內的小專案，含筆記、圖片與 TTS/影片工具源碼。

## 重要功能

- 本機 `mkdocs serve` 預覽時，右鍵可開啟 Markdown 原文檔案位置。
- `p.bat` / `preview.bat` 可指定 Markdown 路徑啟動單頁 preview；零參數時沿用 `mkdocs.preview.yml` 上次目標。
- 站點保留 Material 內建 `Back to top`，並另有右下角 `Back to bottom` 浮動按鈕。

## 常用入口

詳見 `COMMANDS.md`。
