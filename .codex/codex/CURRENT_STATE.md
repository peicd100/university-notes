# CURRENT STATE

## 目前狀態

- 2026-05-24 已修正中/窄版側邊欄開啟時的藍灰底：`自定義.css` 讓 primary drawer 的 sidebar/inner/scrollwrap/nav/list/item 都強制為 `#000000`，overlay 改為黑色半透明，`mkdocs.yml` 將 CSS cache 版本更新為 `20260524-7`。
- 2026-05-24 已改良 TTS 面板與路徑下拉選單視覺：`tts.html` 的語音面板改為純黑薄線、緊湊控制列與固定 cyan 重點色；`自定義.css` 讓深色路徑 dropdown 取消厚重四角框，改為小圓角薄選取底色；`folder-path-bar.js` 開啟頁面選單時會自動捲到目前頁，`mkdocs.yml` 更新 CSS/JS cache 版本。
- 2026-05-24 已修正中版面深色側欄目前頁重複：`自定義.css` 在 `max-width: 76.249em` 隱藏 primary sidebar 的 `label[for="__toc"]`，只保留真正頁面連結；同時提高深色路徑列目前資料夾/頁面的文字對比，`mkdocs.yml` 將 CSS cache 版本更新為 `20260524-5`。
- 2026-05-24 已限制文章圖片寬度：`自定義.css` 使用 `--peicd-article-img-max-width`，桌機文章圖片最多佔內容寬度 70%，小圖不放大；窄螢幕回到 100%，`mkdocs.yml` 將 CSS cache 版本更新為 `20260524-4`。
- 2026-05-24 已修正標題錨點換行：`自定義.css` 將 h2~h6 從可換行 flex 改為 block + 左側預留錨點空間，`.headerlink` 用 absolute 定位在同一行，`mkdocs.yml` 將 CSS cache 版本更新為 `20260524-2`。
- 2026-05-24 已改善深色主題 `==mark==` 高亮：`自定義.css` 將深色模式 mark 改為暖黃色漸層、細外框與微光，`mkdocs.yml` 將 CSS cache 版本更新為 `20260524-1`。
- 2026-05-23 已簡化 Source Jump 右鍵選單：只保留「開啟原文檔案」，移除「複製」按鈕與 clipboard 相關程式碼，`mkdocs.yml` 將 `source-jump.js` cache 版本更新為 `20260523-2`。
- 2026-05-23 已將深色主題背景調成接近 ChatGPT 的黑底：body/container/main/content 為 `#000000`，header/tabs 為近黑透明底，Mermaid 圖卡與右側 TOC 改成黑底漸層。
- 2026-05-23 已改善深色主題 Mermaid flowchart 對比：`mermaid-config-override.js` 合併高對比暗色 themeVariables/themeCSS，`自定義.css` 加外層保底樣式，`mkdocs.yml` 更新 cache 版本。
- 2026-05-23 已修正 Source Jump「開啟原文檔案」看似沒反應的問題：後端會等待 VS Code CLI 回傳並把錯誤傳回前端；前端成功時會顯示短暫狀態，且右鍵事件會先阻止原生選單競態。
- 2026-05-22 已將根目錄 `codex/`、`codex_tmp/`、`.codex_tmp/`、`vbs_bat/` 遷移到 `.codex/` 集中式協作目錄。
- 2026-05-22 已修正 Mermaid htmlLabels 英文字母 descender 被切到的問題：`docs/theme/assets/pymdownx-extras/自定義.css` 將 Mermaid label 行高調整為 `1.18`，`docs/theme/assets/pymdownx-extras/mermaid-render-fix.js` 會在渲染後把每個 label `foreignObject` 高度加大 5px，並更新 `mkdocs.yml` CSS/JS cache 版本。
- `mkdocs.preview.yml` 目前 preview 目標是 `md/114-2/電機_作業系統/ch 6.md`。

## 近期功能方向

- 前端 `source-jump.js` 會送出 block index、區段內 index、整頁進度比例、標題路徑與鄰近段落。
- 後端 `source_jump_hook.py` 會把這些位置指紋納入候選分數，降低重複文字跳錯位置的機率。
- 後端索引會把常見渲染標記 `==...==`、`^^...^^` 視為渲染後文字，讓右鍵未選字時也能落在可見文字位置。

## 既有工作樹注意

- Mermaid 對比修正只改共用樣式、Mermaid config 與協作目錄；未改動 `docs/md/114-2/電機_作業系統/ch 7.md` 筆記內容。
- `mkdocs.yml` 另有既有工作樹變更加入 `docs/md/114-2/電機_作業系統/ch 7.md` 導覽，非本次對比修正新增。

## 最後驗證

- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name drawer-black-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`，returncode 0。
- 已完成：本機 `http://127.0.0.1:8043/` 開啟 `ch 8.html`；1212px 中版面打開 drawer 後，`.md-sidebar--primary`、`.md-sidebar__scrollwrap`、`.md-nav`、`.md-nav__list` 均為 `rgb(0, 0, 0)`，`.md-overlay` 為 `rgba(0, 0, 0, 0.78)`，console error 為空。
- 已完成：`node --check docs\theme\assets\pymdownx-extras\folder-path-bar.js`。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name ui-polish-tts-pathbar-build-2 -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`，returncode 0。
- 已完成：本機 `http://127.0.0.1:8042/` 開啟 `ch 8.html`；TTS 面板背景為 `rgb(5, 6, 7)`、邊框 `rgba(114, 227, 253, 0.22)`、重點色 `#72e3fd`；路徑頁面選單開啟後目前 `Ch 8` 可見、選取背景 `rgba(114, 227, 253, 0.12)`、無角框 background-image，console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name sidebar-pathbar-contrast-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`，returncode 0。
- 已完成：本機 `http://127.0.0.1:8041/` 開啟 `ch 1.html`；1212px 中版面確認 `.md-sidebar--primary label.md-nav__link[for="__toc"]` 為 `display:none`、目前頁只剩一個可見 `Ch 1` 連結、路徑列目前段落為 `rgb(226, 251, 255)`；766px 窄版確認兩個 pathbar select 也為 `rgb(226, 251, 255)`，console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`。
- 已完成：本機啟動 `mkdocs serve -f mkdocs.preview.yml --dirty -a 127.0.0.1:8037`，開啟 `ch 7.html`，桌機 1440px 量測文章圖片 `maxRatio=0.7`、`maxWidth=70%`；手機 390px 量測 `maxRatio=1`、`maxWidth=100%`，console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`。
- 已完成：本機啟動 `mkdocs serve -f mkdocs.preview.yml --dirty -a 127.0.0.1:8035`，開啟 `ch 7.html` 的 `⭐Resource-Allocation Graph Algorithm` h2，量測 `.headerlink` 與標題文字第一行 `sameLine=true`，console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name dark-mark-contrast-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`，returncode 0。
- 已完成：本機啟動 `mkdocs serve -f mkdocs.preview.yml --dirty -a 127.0.0.1:8035`，開啟 `ch 7.html` 目標 `==等它能重新取得舊資源和新資源時==`，確認 mark 套用暖黃色漸層、`rgb(255, 246, 207)` 文字、黑底 `rgb(0, 0, 0)`，console error/warn 為空。
- 已完成：`node --check docs/theme/assets/pymdownx-extras/source-jump.js`。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name source-jump-menu-single-action-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`，returncode 0。
- 已完成：本機啟動 `mkdocs serve -f mkdocs.preview.yml --dirty -a 127.0.0.1:8034`，開啟 `ch 7.html` 後右鍵段落，確認 `#peicd-source-jump-menu` 只有 1 顆 `data-role="jump"` 按鈕，文字為「開啟原文檔案」，`hasCopy=false`，console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name dark-background-black-build-2 -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`，returncode 0。
- 已完成：本機 `http://127.0.0.1:8033/` 開啟 `ch 7.html`，量測 `dracula` 主題下 body/container/main/content 均為 `rgb(0, 0, 0)`，header/tabs 為 `rgba(0, 0, 0, 0.98)`，Mermaid 圖卡與右側 TOC 為黑底漸層，console error/warn 為空。
- 已完成：`node --check docs/theme/assets/pymdownx-extras/mermaid-config-override.js`。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name mermaid-dark-contrast-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean`，returncode 0。
- 已完成：以本機靜態 server `http://127.0.0.1:8033/` 開啟 `ch 7.html` 的 deadlock Mermaid 圖，確認 `dracula` 主題下 node label 為 `rgb(248, 251, 255)`、node fill 為 `rgb(49, 40, 77)`、node stroke 為 `rgb(114, 227, 253)`、edge label 背景為 `rgb(20, 27, 42)`，console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`
- 已完成：`node --check docs\theme\assets\pymdownx-extras\source-jump.js`
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`
- 已完成：本機啟動 `mkdocs serve -f mkdocs.preview.yml --dirty -a 127.0.0.1:8028`，以瀏覽器右鍵 `ready queue 像 FCFS 一樣排隊` 並點「開啟原文檔案」，確認按鈕會進入「開啟中...」、endpoint 回傳 line 1564 column 4、`opened: true` 與成功訊息；console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py`
- 已完成：`node --check docs\theme\assets\pymdownx-extras\source-jump.js`
- 已完成：以 `ch 6.md` line 746 的 `==...==` 段落做定位函式 smoke test，回傳 line 746 column 3。
- 已完成：`Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name source-jump-preview-build-2 -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`，returncode 0。
- 已完成：本機啟動 `mkdocs serve -f mkdocs.preview.yml --dirty -a 127.0.0.1:8026`，直接呼叫 `__peicd/source-jump` endpoint，`ch 6.md` 高亮段落回傳 line 746 column 3；測完已停止 server。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean`，returncode 0。
- 已完成：以本機靜態預覽開啟 `ch 6.html`，確認 `Priority-based Preemptive Scheduling` Mermaid 圖表的 label `divHeight` 均小於或等於 `foreignObject` 高度，瀏覽器 console error/warn 為空。
- 已完成：再次依使用者截圖回測底部 `Higher priority` / `Lower priority`，確認 `foreignObject` 由 19px 增為 24px，底部字母 `y` 不再被裁切，瀏覽器 console error/warn 為空。
- 已完成：`Y:\conda\envs\mkdocs\python.exe -m py_compile tools\run_logged.py`。
- 已完成：`tools\run_logged.py --name run-logged-smoke`，確認輸出改到 `.codex/codex/tmp/`。
