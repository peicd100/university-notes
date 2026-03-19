# 基本指令

| 指令 | 主要功能 | 常見寫法 | 例子 | 重點提醒 |
| :---- | :---- | :---- | :---- | :---- |
| `pwd` | 顯示目前工作目錄(current working directory) | `pwd` | `pwd` | 你現在「站在哪個資料夾」就靠它看 |
| `ls(dir)` | 列出檔案與目錄 | `ls`、`ls -l`、`ls -a` | `ls -la` | `-l` 看詳細資訊；`-a` 顯示隱藏檔 |
| `cd` | 切換目錄(change directory) | `cd 目錄名`、`cd ..`、`cd ~` | `cd Documents` | `..` 是上一層；`~` 是家目錄(home) |
| `mkdir` | 建立新目錄(make directory) | `mkdir 目錄名`、`mkdir -p 路徑` | `mkdir hw1` | `-p` 可一次建立多層目錄 |
| `touch` | 建立空檔案，或更新檔案時間戳(timestamp) | `touch 檔名` | `touch note.txt` | 很多人拿它快速建空白檔 |
| `rm` | 刪除檔案或目錄(remove) | `rm 檔名`、`rm -r 目錄`、`rm -f 檔名` | `rm note.txt` | 最危險；刪掉通常不能直接還原 |

# 進入共用資料夾

cd /media

# 