# log

## 2026-05-31 20:45：MkDocs 設定拆分與 theme 移動

- 任務類型：refactor
- 修改範圍：`mkdocs.yml`、`docs/.mkdocs/site.yml`、`theme/`、`.gitignore`、`2.py`、`.codex/codex/`。
- 主要決策：`mkdocs.yml` 保留技術設定並繼承 `docs/.mkdocs/site.yml`；自訂 theme 從 `docs/theme/` 移到根目錄 `theme/`；根目錄 `指令.txt` 改為本機忽略檔。
- 驗證結果：JS 語法檢查、`source_jump_hook.py` 編譯、完整 build 與 preview build 都通過；`docs/.mkdocs/site.yml` 未輸出到 `site/`。
- 尚未完成：沒有。
- 下次建議先讀：`docs/.mkdocs/site.yml`、`mkdocs.yml`、`theme/`、`CURRENT_STATE.md`。
- 相關檔案：`mkdocs.yml`、`docs/.mkdocs/site.yml`、`theme/main.html`、`.gitignore`、`.codex/codex/archive/current-state-2026-05-31-site-config-reorg.md`、`.codex/codex/archive/log-2026-05-31-site-config-reorg.md`。