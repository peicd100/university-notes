# COMMANDS

## 環境安裝

```bat
conda create -n mkdocs python=3.11 pip git ffmpeg -y
conda activate mkdocs
python -m pip install -r requirements.txt pyinstaller
```

## Preview

```bat
p.bat
p.bat docs\md\114-2\電機_作業系統\ch 6.md
preview.bat docs\md\114-2\電機_作業系統\ch 6.md
Y:\conda\envs\mkdocs\python.exe -m mkdocs serve -f mkdocs.preview.yml --dirty
```

在 cmd 內用 `p.bat` 或 `preview.bat` 啟動 serve 後，Ctrl+C 應直接結束，不應停在「要終止批次工作嗎 (Y/N)」。

## Build

```bat
Y:\conda\envs\mkdocs\python.exe -m mkdocs build --clean
Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
```

## Source Jump 驗證

```bat
Y:\conda\envs\mkdocs\python.exe -m py_compile tools\source_jump_hook.py
node --check theme\assets\pymdownx-extras\source-jump.js
```

## Logged 驗證

```bat
Y:\conda\envs\mkdocs\python.exe tools\run_logged.py --name preview-build -- Y:\conda\envs\mkdocs\python.exe -m mkdocs build -f mkdocs.preview.yml --clean
```

輸出檔應放在 `.codex/codex/tmp/`。
