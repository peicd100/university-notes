# log

## 2026-04-12
- 使用者需求：希望 `mkdocs serve -f mkdocs.preview.yml --dirty` 也能使用右鍵「開啟原文檔案 / 複製」功能。
- 先比對 `mkdocs.yml` / `mkdocs.preview.yml`，確認截圖功能來自 `docs/theme/assets/pymdownx-extras/source-jump.js`。
- 查閱官方 MkDocs 文件與 GitHub 社群 issue，確認 `on_files` 與 `File.content_string` 是穩定 API，且 `serve` / dirty reload 本來就有一些已知邊界情況。
- 本機實測：
  - `__peicd/source-jump` probe endpoint 正常回應。
  - preview 頁面原本會出現 `page not indexed`，表示索引建立時機不夠穩。
  - 用 MkDocs API 讀 `mkdocs.preview.yml`，確認目前 preview 指向 `VHDL.md`。
- 實際修改：
  - 更新 `tools/source_jump_hook.py`
  - 新增 `on_files`
  - 新增 `_iter_documentation_files`、`_read_markdown_content`、`_index_page_markdown`
  - 保留 `on_page_markdown` 作索引覆寫精修
  - `.gitignore` 新增 `*.out.log`、`*.err.log`
  - `.gitignore` 將 `README_PEICD100.md`、`專案規格書.md`、`log.md` 改成根目錄限定忽略，避免 `codex/` 內的新正式協作檔被一起忽略
  - 新增 `codex/` 協作檔
- 驗證方式：
  - `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`
  - `node --check docs\theme\assets\pymdownx-extras\source-jump.js`
  - `mkdocs serve -f mkdocs.preview.yml --dirty` 下對 `VHDL.html` 的 lookup endpoint 回傳 200，並可定位到 `VHDL.md:1:3`
  - `mkdocs serve --dirty` 下同一路徑 lookup endpoint 也回傳 200
- 結果：preview 模式後端索引問題已修正，source jump lookup 可在主站與 preview 的 dirty serve 下正常定位 Markdown 原始檔。
