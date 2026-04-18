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

## 2026-04-12 驗證輸出整理
- 使用者需求：之後人工驗證產生的 `.out.log` / `.err.log` 不要再散在專案根目錄，統一改放 `codex/tmp/`。
- 查閱 Python `subprocess` 官方文件、Git `gitignore` 官方文件，以及社群對 `.gitkeep` / 空目錄保留的慣例後，採用較穩的專案內暫存目錄方案。
- 實際修改：
  - 新增 `tools/run_logged.py`
  - 新增 `codex/tmp/.gitkeep`
  - `.gitignore` 新增 `codex/tmp` 暫存忽略規則
  - `codex/README_PEICD100.md` 補充驗證輸出使用方式
  - `codex/專案規格書.md`、`codex/使用者要求.md`、`codex/協作重要事項.md` 同步記錄規則
  - 將根目錄既有 `.out.log` / `.err.log` 移入 `codex/tmp/`
- 驗證方式：
  - `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name pycheck-source-jump -- Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`
  - 確認 `codex/tmp/` 產生對應的 `.out.log`、`.err.log`、`.meta.json`
  - 確認專案根目錄不再殘留本次移動前的 `.out.log` / `.err.log`
- 結果：後續需要保留的人工驗證輸出已有固定落點，根目錄可維持乾淨。

## 2026-04-12 標題 inline code 排版修正
- 使用者需求：`docs/md/114-2/資工_電腦輔助 VLSI 設計/VHDL.md` 中，標題使用 backticks 後版面跑掉，要修正顯示。
- 先讀目標 Markdown 與既有專案協作檔，確認這不是單一標題手誤，而是頁面上多個含 code 的標題都會踩到相同版面問題。
- 查閱 CommonMark 規範、Python-Markdown TOC 官方文件，以及 Stack Overflow 上 heading 可含 inline code 的社群示例，確認 heading 內放 code span 本身是合法且常見的寫法。
- 實際根因確認：
  - 用 `mkdocs build -f mkdocs.preview.yml --clean --site-dir codex/tmp/preview-current` 重建預覽頁面。
  - 用 Playwright CLI 檢查目標 heading 的 computed style，確認 `h2~h6` 被自訂 CSS 設成 `display:flex`，且 `align-items: top` 是無效值，實際回退造成 code flex item 被拉高。
- 實際修改：
  - 更新 `docs/theme/assets/pymdownx-extras/自定義.css`
  - `h2~h6` 改成 `flex-wrap: wrap`、`align-items: flex-start`
  - 新增 heading 內 `code` 的專屬字級 / padding / 換行規則
  - `codex/README_PEICD100.md`、`codex/協作重要事項.md`、`codex/專案規格書.md` 同步補記這次決策
- 驗證方式：
  - `Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean --site-dir codex/tmp/preview-current`
  - `npx.cmd --yes @playwright/cli open http://127.0.0.1:8123/.../VHDL.html#3-...`
  - `npx.cmd --yes @playwright/cli eval ...` 檢查 heading 與 code span 的實際 computed style / bounding box
  - `npx.cmd --yes @playwright/cli run-code ...heading.screenshot(...)` 目視確認 code span 不再被拉成大方塊
- 結果：標題中的 code span 已恢復正常高度，且不再在桌機寬度下被拆成異常巨型區塊；窄螢幕則允許較溫和的換行。

## 2026-04-12 頁面內目錄標號修正
- 使用者需求：頁面內 `## 目錄` 區塊的頂層序號顯示錯誤，畫面出現 `a.` 而不是 `1.`、`2.`。
- 先比對靜態 HTML、右側 TOC 與頁面內目錄，確認右側 TOC 正常，只有手寫頁面內目錄有問題。
- 查閱 CommonMark / Python-Markdown 的清單解析規則與社群經驗後，確認 `- 1. ...` 在無序清單中會被當成巢狀 ordered list，而不是單純文字。
- 實際修改：
  - 更新 `docs/md/114-2/資工_電腦輔助 VLSI 設計/VHDL.md`
  - 將頁面內目錄頂層條目的 `- N. ...` 全部改成 `- N&#46; ...`
  - `codex/README_PEICD100.md`、`codex/協作重要事項.md`、`codex/專案規格書.md` 同步補記這個 Markdown 陷阱
- 驗證方式：
  - `Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean --site-dir codex/tmp/preview-current`
  - 檢查輸出的 `VHDL.html`，確認 `## 目錄` 區塊不再產生巢狀 `<ol>`
  - 用 Playwright 重整頁面並截圖，確認頁面內目錄顯示為 `1.`、`2.`、`3.`
- 結果：頁面內目錄的頂層標號已恢復正常，不再顯示成 `a.`。

## 2026-04-12 標題 inline code 上下置中
- 使用者需求：希望標題中的 backticks 不是只看起來自然，而是上下真正置中。
- 先在預覽頁實測 `baseline`、`top` 微移、`align-self: center` 三種做法，最後以 `align-self: center` 效果最符合需求。
- 查閱 MDN flexbox / `align-self` 文件與社群對 flex item 垂直置中的經驗後，採用 flex 原生 cross-axis 對齊，而不是再疊一層 `top` 微調。
- 實際修改：
  - 更新 `docs/theme/assets/pymdownx-extras/自定義.css`
  - 在 heading code 規則改為 `align-self: center`
  - 移除先前的 `top` 微位移
  - `codex/README_PEICD100.md`、`codex/協作重要事項.md`、`codex/專案規格書.md` 同步補記這次做法
- 驗證方式：
  - `Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean --site-dir codex/tmp/preview-current`
  - `npx.cmd --yes @playwright/cli goto http://127.0.0.1:8123/.../VHDL.html?cb=20260412-center#123-d-flip-flop用-event`
  - `npx.cmd --yes @playwright/cli eval ...` 檢查 code item 的 `align-self` 已生效、`top` 已不再介入
  - `npx.cmd --yes @playwright/cli run-code ...heading.screenshot(...)` 比對 12.3 標題的最終顯示
- 結果：標題內 inline code 已改成真正的 cross-axis 置中，且未影響既有 heading 佈局。

## 2026-04-18 單頁 preview 快捷命令
- 使用者需求：希望能在終端直接輸入一個命令加 Markdown 路徑，例如 `docs\md\114-2\科技_計算機結構\ch 2.md`，就自動更新 `mkdocs.preview.yml`，並執行 `activate mkdocs_desk` + `mkdocs serve -f mkdocs.preview.yml --dirty`。
- 先查閱 MkDocs 官方 configuration / release notes，確認目前單頁 preview 做法可繼續沿用 `nav` + `exclude_docs`；同時查閱 Stack Overflow 上 Windows batch + Conda 啟用經驗，確認要用 `call activate.bat` 才不會中斷後續命令。
- 後續實測發現這台機器把 `activate.bat` 包進正式入口時，Anaconda 會在轉發 `conda activate <base>` 時出現異常；改成直接走 `condabin\\conda.bat activate mkdocs_desk` 後穩定通過，因此正式方案採後者。
- 另外實測發現，同一個已啟用的環境內，直接跑 `mkdocs serve` 的 console wrapper 沒有穩定拉起服務；改用 `python -m mkdocs serve` 後可正常啟動，因此正式入口也一併調整。
- 實際修改：
  - 新增 `preview.bat`
  - 新增 `tools/update_preview_config.py`
  - `mkdocs.preview.yml` 改成含 `preview-target` managed 區塊
  - `.gitignore` 新增 `codex_tmp/`
  - 更新 `README_DESK.md`
  - `codex/README_PEICD100.md`、`codex/專案規格書.md`、`codex/使用者要求.md`、`codex/協作重要事項.md` 同步補記
- 驗證方式：
  - 直接執行 `python tools/update_preview_config.py docs\md\114-2\科技_計算機結構\ch 2.md`
  - 用 `PREVIEW_SKIP_SERVE=1` 執行 `preview.bat ...`，確認可成功啟用 `mkdocs_desk` 並更新設定檔
  - 在 `mkdocs_desk` 環境下執行 `mkdocs build -f mkdocs.preview.yml --clean`，確認更新後的 preview 設定可正常被 MkDocs 載入
  - 直接執行 `.\preview.bat docs\md\114-2\科技_計算機結構\ch 2.md`，命令在 15 秒逾時前持續執行，代表 `serve` 未立即退出
  - 背景啟動 `preview.bat` 8 秒後檢查 `127.0.0.1:8000`，確認 port 處於 listening 狀態
- 結果：之後可直接用 `preview.bat <Markdown 路徑>`（PowerShell 用 `.\preview ...`）切換單頁 preview 並啟動預覽，不必再手改 `mkdocs.preview.yml`。
