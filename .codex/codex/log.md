# log

## 2026-05-24 19:19：TTS 面板與路徑下拉選單視覺改良

- 任務類型：ui
- 修改範圍：`docs/theme/tts.html`、`docs/theme/assets/pymdownx-extras/自定義.css`、`docs/theme/assets/pymdownx-extras/folder-path-bar.js`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：TTS 面板改為純黑薄線工具面板、控制列更緊湊並固定 cyan 重點色；路徑 dropdown 移除厚重四角框，改小圓角與薄選取底色，且開啟時自動捲到目前頁。
- 驗證結果：`folder-path-bar.js` node check 通過；`mkdocs build --clean` 通過；本機 `ch 8.html` 實測 TTS 面板與路徑 dropdown 色彩/目前頁可視狀態，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`ARCHITECTURE.md` 的 Folder Path Bar、`VERIFY.md` 的前端互動。
- 相關檔案：`docs/theme/tts.html`、`docs/theme/assets/pymdownx-extras/自定義.css`、`docs/theme/assets/pymdownx-extras/folder-path-bar.js`、`mkdocs.yml`。

## 2026-05-24 19:01：中版面側欄重複目前頁與路徑列對比修正

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：中版面隱藏 primary sidebar 的目前頁 TOC toggle label，只保留真正頁面連結；深色路徑列目前段落改為高對比淺青白，CSS cache 版本更新為 `20260524-5`。
- 驗證結果：`mkdocs build --clean` 通過；本機 `ch 1.html` 在 1212px 與 766px 實測左側不再重複目前頁，路徑列目前文字為 `rgb(226, 251, 255)`，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`GOTCHAS.md` 的中版面左側目前頁條目、`VERIFY.md` 的前端互動清單。
- 相關檔案：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`。

## 2026-05-24 13:02：文章圖片桌機寬度改為 70%

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：文章圖片桌機最大寬度從 60% 改為 70%，窄螢幕仍回到 100%，且不限制 image viewer；`自定義.css` cache 版本更新為 `20260524-4`。
- 驗證結果：`mkdocs build -f mkdocs.preview.yml --clean` 通過；本機 preview `ch 7.html` 桌機量測 `maxRatio=0.7`、`maxWidth=70%`，手機量測 `maxRatio=1`、`maxWidth=100%`，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`GOTCHAS.md` 的文章圖片寬度條目。
- 相關檔案：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`。

## 2026-05-24 12:56：文章圖片寬度限制

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：文章圖片新增 `--peicd-article-img-max-width`，桌機最多 60%，小圖不放大；窄螢幕回到 100%，且不限制 image viewer；`自定義.css` cache 版本更新為 `20260524-3`。
- 驗證結果：`mkdocs build -f mkdocs.preview.yml --clean` 通過；本機 preview `ch 7.html` 桌機量測 `maxRatio=0.6`、手機量測 `maxRatio=1`，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`GOTCHAS.md` 的文章圖片寬度條目。
- 相關檔案：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`。

## 2026-05-24 12:39：標題錨點同行修正

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：h2~h6 不再使用可換行 flex；改成 block + 左側預留錨點空間，`.headerlink` 用 absolute 定位在同一行開頭；`自定義.css` cache 版本更新為 `20260524-2`。
- 驗證結果：`mkdocs build -f mkdocs.preview.yml --clean` 通過；本機 preview 開啟 `ch 7.html`，量測 `⭐Resource-Allocation Graph Algorithm` h2 的 `.headerlink` 與標題文字第一行 `sameLine=true`，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`GOTCHAS.md` 的標題錨點條目。
- 相關檔案：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`。

## 2026-05-24 00:19：深色 mark 高亮對比改善

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：深色模式 `==mark==` 改用暖黃色漸層、細外框、微光與淺暖色文字，提高黑底辨識度；`自定義.css` cache 版本更新為 `20260524-1`。
- 驗證結果：`mkdocs build -f mkdocs.preview.yml --clean` 透過 `tools/run_logged.py` returncode 0；本機 `ch 7.html` 量測目標 mark 已套用新漸層、文字 `rgb(255, 246, 207)`、黑底 `rgb(0, 0, 0)`，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`CURRENT_STATE.md` 的深色 mark 驗證。
- 相關檔案：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/artifacts/dark-mark-contrast-20260524.png`。

## 2026-05-23 22:48：Source Jump 右鍵選單移除複製

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/source-jump.js`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：右鍵選單只保留「開啟原文檔案」，移除「複製」按鈕、事件處理、顯示切換與 clipboard fallback；`source-jump.js` cache 版本更新為 `20260523-2`。
- 驗證結果：`node --check` 通過；`mkdocs build --clean` 透過 `tools/run_logged.py` returncode 0；本機 preview 右鍵段落後選單只有 1 顆 `data-role="jump"` 按鈕，`hasCopy=false`，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`GOTCHAS.md` 的 Source Jump 右鍵選單條目。
- 相關檔案：`docs/theme/assets/pymdownx-extras/source-jump.js`、`mkdocs.yml`。

## 2026-05-23 21:02：深色主題黑底調整

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/自定義.css`、`docs/theme/assets/pymdownx-extras/mermaid-config-override.js`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：深色主題主背景改為接近 ChatGPT 的黑底；header/tabs、Mermaid 圖卡與右側 TOC 同步改為近黑或黑底漸層，保留 `#72e3fd` 作重點色。
- 驗證結果：`node --check` 通過；`mkdocs build --clean` 透過 `tools/run_logged.py` returncode 0；本機 `ch 7.html` 量測 body/container/main/content 為 `rgb(0, 0, 0)`、header/tabs 為 `rgba(0, 0, 0, 0.98)`，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`USER_REQUIREMENTS.md` 的 Preview 與 UI 偏好、`GOTCHAS.md` 的深色主題不要回到藍灰底。
- 相關檔案：`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`。

## 2026-05-23 20:20：Mermaid 深色對比改善

- 任務類型：ui
- 修改範圍：`docs/theme/assets/pymdownx-extras/mermaid-config-override.js`、`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`、`.codex/codex/`。
- 主要決策：暗色 flowchart 同時用 Mermaid themeVariables/themeCSS 與外層 CSS 保底，避免節點、edge label、SVG text 或放大檢視漏套高對比色。
- 驗證結果：`node --check` 通過；`mkdocs build --clean` 透過 `tools/run_logged.py` returncode 0；本機 `http://127.0.0.1:8033/` 開啟 `ch 7.html`，deadlock 圖文字與 edge label 為高對比，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`GOTCHAS.md` 的 Mermaid 深色主題文字對比、`VERIFY.md` 的前端互動。
- 相關檔案：`docs/theme/assets/pymdownx-extras/mermaid-config-override.js`、`docs/theme/assets/pymdownx-extras/自定義.css`、`mkdocs.yml`。

## 2026-05-23 12:39：Source Jump 開檔回饋修正

- 任務類型：bugfix
- 修改範圍：`docs/theme/assets/pymdownx-extras/source-jump.js`、`tools/source_jump_hook.py`、`mkdocs.yml`、`.codex/codex/` 交接文件。
- 主要決策：VS Code 開檔改為等待 CLI 回傳並檢查 exit code；前端成功時短暫顯示狀態再收起選單，右鍵事件先阻止原生選單競態。
- 驗證結果：`py_compile`、`node --check`、`mkdocs build -f mkdocs.preview.yml --clean` 均通過；本機 preview 右鍵 `ready queue 像 FCFS 一樣排隊` 可送出開檔，endpoint 回傳 `opened: true`、line 1564 column 4，console error/warn 為空。
- 尚未完成：無。
- 下次建議先讀：`GOTCHAS.md` 的 Source Jump 條目、`VERIFY.md` 的 Source Jump 驗證。
- 相關檔案：`tools/source_jump_hook.py`、`docs/theme/assets/pymdownx-extras/source-jump.js`、`mkdocs.yml`。

## 2026-05-22：`.codex/` 集中式協作目錄遷移

- 狀態：completed
- 本次遷移範圍：
  - `codex/` -> `.codex/codex/`
  - `codex_tmp/` -> `.codex/codex_tmp/legacy-codex_tmp/`
  - `.codex_tmp/` -> `.codex/codex_tmp/legacy-dot-codex_tmp/`
  - `vbs_bat/` -> `.codex/vbs_bat/`
- 已封存舊資料：既有 `archive/legacy-2026-05-18/` 隨 `codex/` 完整移到 `.codex/codex/archive/legacy-2026-05-18/`。
- 已建立或更新的新入口：`.codex/AGENTS.md`、`.codex/codex/00_START_HERE.md`。
- `.gitignore` 調整：新增 `.codex/` 暫存、私密、artifacts、壓縮備份忽略規則；保留舊 `/codex/` 忽略規則作相容。
- 驗證結果：根目錄不再有 `codex/`、`codex_tmp/`、`.codex_tmp/`、`vbs_bat/`；`.codex/codex/` 核心文件存在。
- 尚未處理：無。
- 下一位代理接手時必讀：`.codex/codex/00_START_HERE.md`、`.codex/codex/CURRENT_STATE.md`、`.codex/codex/GOTCHAS.md`。

## 2026-05-22

- 修正 Mermaid flowchart htmlLabels 英文字母 descender 被裁切：
  - `docs/theme/assets/pymdownx-extras/自定義.css` 將 `foreignObject > div` 行高從 `1.4` 改為 `1.18`，並明確保留 `overflow: visible`。
  - 使用者回報底部 `Higher priority` / `Lower priority` 的 `y` 仍像被切成 `v` 後，新增 `mermaid-render-fix.js` 渲染後補強：每個 `g.label > foreignObject` 高度額外加 5px，並把 `foreignObject` overflow 設成 visible。
  - `mkdocs.yml` 將 `自定義.css` cache 版本更新為 `20260522-2`，`mermaid-render-fix.js` 更新為 `20260522-1`。
- 驗證：
  - `Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`
  - `node --check docs\theme\assets\pymdownx-extras\mermaid-render-fix.js`
  - 以本機靜態預覽檢查 `docs/md/114-2/電機_作業系統/ch 6.md` 的 RM 關係圖；目標節點 `divHeight <= foreignObject height`，瀏覽器 console error/warn 為空。
  - 再次截圖確認 `Higher priority`、`Lower priority` 的 `y` 下緣完整；單行 label `foreignObject` 由 19px 增為 24px。
  - `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\run_logged.py`
  - `tools\run_logged.py --name run-logged-smoke`，確認輸出落在 `.codex/codex/tmp/`。

## 2026-05-18

- 將舊版協作檔完整封存到 `.codex/codex/archive/legacy-2026-05-18/`，並建立新版分層結構。
- 改善 Preview 右鍵「開啟原文檔案」定位準確度：
  - 前端新增 `section_index` 與 `block_progress` 位置指紋。
  - 後端新增 section order、page progress 加權。
  - 後端索引會把 `==...==` 與 `^^...^^` 視為渲染後文字。
- 驗證：
  - `Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`
  - `node --check docs\theme\assets\pymdownx-extras\source-jump.js`
  - 以 `docs/md/114-2/電機_作業系統/ch 6.md` line 746 做定位 smoke test，回傳 line 746 column 3。
  - `Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name source-jump-preview-build-2 -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`，returncode 0，歷史輸出已隨遷移移到 `.codex/codex/tmp/`。
  - 啟動本機 preview server 後以 HTTP 查詢 `__peicd/source-jump`，`ch 6.md` 高亮段落回傳 line 746 column 3；測完已停止 server。
