# VERIFY

## Source Jump

最小驗證：

```bat
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py
node --check docs\theme\assets\pymdownx-extras\source-jump.js
Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
```

手動驗證：

- 啟動 `p.bat` 或 `preview.bat docs\md\114-2\電機_作業系統\ch 6.md`。
- 在 preview 頁右鍵一般段落、`==...==` 高亮段落、code block、重複短句。
- 確認 VS Code 開到同一 Markdown 的正確行附近。

## 前端互動

- 使用瀏覽器確認選字右鍵與未選字右鍵都可顯示選單。
- 若涉及 Material instant navigation，從其他頁切到目標頁後再測一次。
- 若修改 Mermaid 樣式，至少開啟 `docs/md/114-2/電機_作業系統/ch 6.md` 的 RM 關係圖，確認 `Priority-based Preemptive Scheduling`、`Shorter period`、`Higher priority` 等英文字下緣沒有被裁切。
- Mermaid htmlLabels 可用瀏覽器量測：目標圖表每個 `g.node foreignObject` 都應帶 `data-peicd-descender-pad="true"`；單行 label 高度應從原始 19px 增到約 24px，且 `Higher priority`、`Lower priority` 最後的 `y` 必須可見。

## 輸出管理

若需要保留驗證輸出，使用：

```bat
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name <name> -- <command...>
```

輸出應落在 `.codex/codex/tmp/`。
