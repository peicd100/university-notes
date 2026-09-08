# COMMANDS

## 環境安裝

```bat
conda create -n mkdocs python=3.11 pip git ffmpeg -y
conda activate mkdocs
python -m pip install -r requirements.txt pyinstaller
```

## Preview

```bat
p
p docs\md\114-2\電機_作業系統\ch 6.md
Y:\conda\envs\mkdocs\python.exe -m mkdocs serve -f mkdocs.preview.yml --dirty
```

在 cmd 內用 `p` 啟動 serve；目前 `p` 應解析到根目錄的 `p.exe`，不是 `p.bat`。Ctrl+C 應直接結束，不應停在「要終止批次工作嗎 (Y/N)」。不要用長時間執行的 `.bat` 當主要 preview 入口。

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
