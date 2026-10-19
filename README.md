# PEICD100

## 安裝環境

```
conda create -n mkdocs python=3.11 -y
activate mkdocs
conda install pip -y 
conda install -n mkdocs -y -c conda-forge ffmpeg pyside6
pip install -r requirements.txt
conda install git -y

```

## 整站快速預覽

執行 `s.bat`（PowerShell 使用 `.\s.bat`），自動使用 `mkdocs_desk` 與專案根目錄：

```bat
s
```

第一次建置整站，之後以 `--dirty` 增量重建，所有頁面仍可瀏覽。Markdown 轉換結果保留在 `.cache/preview-render/`，每頁搜尋資料保留在 `.cache/preview-search/`，重新啟動可重用；來源、設定、hook、主題或套件版本變更時會重新檢查／轉換。搜尋另檢查頁面內容、metadata 與目錄，並正常組合整站索引。導覽、加密與頁面範本仍正常執行。

圖片處理只掃描標籤、轉換實際圖片；需要補齊 HTML 標籤的舊頁面保留原本的修補流程。CSS 內容未變時重用記憶體快取。右鍵定位索引在該頁第一次右鍵時才建立，之後依原文內容更新。

開啟終端機顯示的網址，按 Ctrl+C 停止。`s --fresh` 可略過 Markdown／搜尋的跨次啟動快取；不要在每次預覽前刪除 `.cache/`。含外部 include 的頁面會直接重新轉換，避免引用內容過期。嚴格檢查／詳細診斷也會略過這兩種快取。

可轉交 MkDocs serve 參數，例如 `s -a 127.0.0.1:8001`。修改導覽、共用範本、CSS 或跨頁設定後，請停止再啟動；若需每次完整重建，使用 `s --clean`。局部單頁預覽仍使用 `p`。

## 每次寫完檢查／推送

`g.bat` 沿用已配置的 `mkdocs_desk` 環境（須能使用 `activate`）。

```bat
g --check
```

只做完整本機建置，不 commit、部署或 push。輸出放在 `.peicd100/codex/tmp/g-deploy/site/`，不覆蓋 `p` 使用的預覽 `site/`。

確認檢查正常、且目前位於 `main` 後，再自行執行：

```bat
g
```

流程：建置成功 → stage／必要時 commit 原始碼 → 發布已驗證產物 → push main。只建置一次；部署記錄會使用本次 source commit。不會自動重新命名分支，無內容變更時跳過 commit。

任一步驟失敗立即停止，顯示失敗階段並保留非零 exit code。不要只看最後一行來判斷網站是否更新；若仍失敗，提供該階段與前面的錯誤訊息。

PEICD／舊 Codex 記憶不由 `g` 自動 stage；若它們已被手動 staged，`g` 會要求先檢查 index。不會替你 untrack、清掉既有 staged 內容或改寫歷史。
