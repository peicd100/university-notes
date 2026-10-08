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
