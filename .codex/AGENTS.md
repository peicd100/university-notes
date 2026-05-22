# PEICD AGENTS.md

版本：1.1.1

本檔是 PEICD 的通用代理工作規則。目標是讓不同代理在不同專案中都能穩定接手、查到正確上下文、延續使用者要求、避免重踩舊坑，並讓每個專案的 `.codex/codex/` 資料夾能隨專案自然成長。

`.codex/AGENTS.md` 或 `AGENTS.md` 只放「每次工作一定要遵守的啟動規則與工作協議」。專案知識、技術細節、決策、踩坑、交接狀態，放到專案自己的 `.codex/codex/`。

本版規則採「`.codex/` 集中式協作目錄」：原本放在專案根目錄、但本質上屬於協作、交接、代理記憶、暫存、備份、腳本輔助或本機輸出的檔案與資料夾，都必須移到 `.codex/` 之下。根目錄只保留原始碼、產品必要設定、公開 README、授權檔與專案真正需要暴露在根層的檔案。

---

## 0. 啟動規則

- 每次收到使用者新指令時，必須重新尋找並完整讀取代理規則檔，不得依賴上次記憶。
- 尋找順序：
  1. 目前工作目錄的 `.codex/AGENTS.md`。
  2. 目前工作目錄的 `AGENTS.md`，僅作為舊專案相容入口。
  3. 從目前目錄往上尋找最近的 `.codex/AGENTS.md`。
  4. 從目前目錄往上尋找最近的 `AGENTS.md`，僅作為舊專案相容入口。
  5. 使用者資料夾中的 `~/.codex/AGENTS.md`。
- 讀完後先用繁體中文回覆：`我已閱讀AGENTS.md：` 後接實際讀到的完整路徑，路徑用反引號包住。
- 若找不到任何代理規則檔，必須告知使用者並停止後續動作。
- 全程使用繁體中文。所有中文文字檔必須使用 UTF-8 無 BOM。
- 若同時存在 `.codex/AGENTS.md` 與根目錄 `AGENTS.md`，以 `.codex/AGENTS.md` 為準；根目錄 `AGENTS.md` 視為 legacy 或轉址檔，不可反向覆蓋 `.codex/AGENTS.md`。

---

## 1. 優先順序

規則衝突時依下列順序處理：

1. 系統、安全、工具與平台限制。
2. 使用者最新明確指令。
3. 目前工作目錄或最近上層的 `.codex/AGENTS.md`。
4. 目前工作目錄或最近上層的 `AGENTS.md`，僅限舊專案相容。
5. 使用者資料夾的全域 `~/.codex/AGENTS.md`。
6. 專案 `.codex/codex/` 中狀態為 `active` 或明確仍有效的長期要求、決策與踩坑紀錄。
7. 尚未遷移的舊版根目錄 `codex/` 中狀態明確有效的紀錄。
8. 舊紀錄、歸檔紀錄、狀態為 `candidate`、`superseded` 或 `archived` 的內容。

遇到衝突時不要猜測；先說明衝突，依優先順序處理。若本次會修改專案，將處理結果記錄到 `.codex/codex/DECISIONS.md`、`.codex/codex/GOTCHAS.md` 或既有等價文件。

---

## 2. 工作原則

- 先理解，再修改。進入專案後先讀入口文件、目前狀態、長期要求、已知踩坑與近期紀錄。
- 使用者沒有要求修改檔案時，不主動修改檔案。
- 使用者要求實作、修正、整理或建立檔案時，預設完成到可驗證狀態，不只停在建議。
- 對使用者既有變更保持尊重。不要還原、刪除或覆蓋你沒有做的修改，除非使用者明確要求。
- 搜尋檔案與文字時優先使用 `rg` / `rg --files`；缺少 `rg` 時再使用其他工具。
- 手動編輯檔案時優先使用 patch 型工具，保持 diff 小而可 review。
- 不要用臨時腳本大段重寫人類文件，除非是明確的機械化整理或使用者要求。
- 任何可能產生大量輸出的未知命令，都要先限制輸出大小或先查檔案大小，避免污染上下文。
- 對於版本、套件、API、法規、平台政策、部署、安裝、資安、醫療、法律、金融、外部服務與可能過時的資訊，必須查網路或官方文件。
- 純本地、可由 repo、程式碼與測試直接驗證的小決策，不需要為每個細節查網路；以本地證據與專案既有慣例為準。
- 查網路時優先官方文件、原始 repo、標準文件、issue/PR；社群經驗可作風險參考，但不可取代可驗證來源。
- 如果採用比使用者原要求更穩定的做法，可以直接執行；完成後必須說明差異與原因。

---

## 3. `.codex/codex/` 專案記憶系統

每個專案應使用 `.codex/codex/` 作為長期記憶。`.codex/` 是協作與代理相關檔案的集中根目錄；根目錄只應保留專案本體需要的檔案，例如原始碼、正式設定檔、公開文件、授權、套件管理檔、建置設定與使用者明確要求放在根目錄的檔案。

`.codex/` 不等於全部忽略版本控制；其中可交接的文件應能被 Git 追蹤，只有暫存、私密與大型輸出預設忽略。

推薦結構如下：

```text
.codex/
  AGENTS.md
  codex/
    00_START_HERE.md
    PROJECT.md
    CURRENT_STATE.md
    USER_REQUIREMENTS.md
    ARCHITECTURE.md
    DECISIONS.md
    GOTCHAS.md
    VERIFY.md
    COMMANDS.md
    log.md
    playbooks/
    knowledge/
    archive/
    tmp/
    private/
    artifacts/
  codex_compressed/
  codex_tmp/
  tmp/
  private/
  artifacts/
  vbs_bat/
```

用途：

- `.codex/AGENTS.md`：專案代理啟動規則。若根目錄保留 `AGENTS.md`，根目錄檔只能作轉址或舊相容。
- `.codex/codex/00_START_HERE.md`：入口索引、必讀順序、任務路由、重要文件地圖。
- `.codex/codex/PROJECT.md`：專案用途、技術棧、環境、入口、常用操作。
- `.codex/codex/CURRENT_STATE.md`：目前進度、最近完成、下一步、阻塞點、最後驗證。
- `.codex/codex/USER_REQUIREMENTS.md`：長期有效的使用者偏好、要求與限制。
- `.codex/codex/ARCHITECTURE.md`：架構、資料流、模組邊界、技術限制。
- `.codex/codex/DECISIONS.md`：重要決策與取捨，採 ADR 精神記錄。
- `.codex/codex/GOTCHAS.md`：踩坑、防回歸、相容性問題、不可重犯事項。
- `.codex/codex/VERIFY.md`：測試、打包、部署、UI、發版、平台驗證清單。
- `.codex/codex/COMMANDS.md`：常用命令、環境啟動、平台差異。
- `.codex/codex/log.md`：近期工作摘要。為了 Windows / NTFS 相容，預設使用小寫 `log.md`，不要同時建立 `LOG.md` 與 `log.md`。舊內容要壓縮或移到 `archive/`。
- `.codex/codex/playbooks/`：特定任務流程，例如 release、debug、deploy、migration。
- `.codex/codex/knowledge/`：技術細節與領域知識，例如 Flutter、Apps Script、本機 AI。
- `.codex/codex/tmp/`、`.codex/codex/private/`、`.codex/codex/artifacts/`：與長期記憶直接相關的暫存、私密、本機輸出，預設不提交版本控制。
- `.codex/codex_compressed/`：完整 `.codex/codex/` 的壓縮備份輸出位置，不得放入 `.codex/codex/` 內。
- `.codex/codex_tmp/`、`.codex/tmp/`、`.codex/private/`、`.codex/artifacts/`：專案層級代理暫存、私密資料與輸出。
- `.codex/vbs_bat/`：Windows 雙擊啟動輔助腳本。

---

## 4. 根目錄協作檔交接與舊版 `codex/` 自動遷移

本章集中放「舊專案交接、根目錄協作檔搬遷、舊版 `codex/` 自動遷移」相關規則。等所有專案都完成 `.codex/` 遷移，且不再需要相容根目錄 `codex/`、`codex_compressed/`、`codex_tmp/`、`vbs_bat/` 等舊路徑時，可以整章刪除，不需要到其他章節逐段清理。

### 4.1 新舊路徑交接原則

- 新版標準：所有協作檔案、交接檔案、代理記憶、額外輔助檔案、暫存輸出、備份壓縮檔與本機執行輔助檔，預設都放在 `.codex/` 底下。
- 若舊規則或舊專案曾把檔案放在根目錄，交接時的基本規則是「在原路徑前面加上 `.codex/`」。
- 遷移前必須先保留全文或完整檔案；遷移後才移除根目錄舊檔。若封存或驗證失敗，不得移除舊檔。
- 若只是唯讀問答且使用者沒有要求改檔，先不要改檔，但要在回答中指出偵測到舊格式並建議遷移。

### 4.2 標準路徑映射

| 舊路徑 | 新標準路徑 | 用途 |
|---|---|---|
| `AGENTS.md` | `.codex/AGENTS.md` | 專案代理啟動規則；根目錄版本只作舊相容或轉址 |
| `codex/` | `.codex/codex/` | 長期記憶、交接、決策、踩坑、驗證文件 |
| `codex_compressed/` | `.codex/codex_compressed/` | `.codex/codex/` 的壓縮備份 |
| `codex_tmp/` | `.codex/codex_tmp/` | 代理工作暫存，不應提交 |
| `tmp/` | `.codex/tmp/` | 代理或協作暫存，不應提交 |
| `private/` | `.codex/private/` | 私密資料、token、個人路徑，不應提交 |
| `artifacts/` | `.codex/artifacts/` | 代理產物、截圖、打包輸出，依內容決定是否提交 |
| `vbs_bat/` | `.codex/vbs_bat/` | Windows 雙擊啟動輔助腳本 |

### 4.3 舊專案接手規則

- 若專案已存在 `.codex/codex/`，一律以它作為長期記憶主目錄。
- 若專案只有根目錄 `codex/`，視為舊版 PEICD 協作目錄。唯讀任務先讀取它；只要本次進入修改階段，或使用者要求整理、更新、維護、交接、重構協作檔，就必須遷移到 `.codex/codex/`。
- 若 `.codex/codex/` 與根目錄 `codex/` 同時存在，不可直接合併或覆蓋。必須先讀 `.codex/codex/00_START_HERE.md`，再檢查根目錄 `codex/` 是否為未遷移舊資料；需要處理時，將根目錄 `codex/` 完整封存到 `.codex/codex/archive/root-codex-YYYY-MM-DD/`，再把仍有效的高訊號內容整理進新版文件。
- 若發現根目錄 `codex_compressed/`、`codex_tmp/`、`vbs_bat/`、`tmp/`、`private/`、`artifacts/` 是協作或代理用途，也應遷移到 `.codex/` 對應位置。

### 4.4 舊版 PEICD `codex/` 自動遷移

若在專案中發現下列舊版協作檔，視為舊版 PEICD codex 格式：

- `codex/README_PEICD100.md`
- `codex/專案規格書.md`
- `codex/log.md`
- `codex/使用者要求.md`
- `codex/協作重要事項.md`

只要本次任務已進入專案修改階段，或使用者要求整理、更新、維護、交接、重構協作記憶，就必須主動把舊格式遷移成 `.codex/codex/` 新版分層結構，不需要再詢問使用者是否遷移。

遷移規則：

- 舊版檔案必須採「完整封存後移除」策略：先把偵測到的舊檔全文移入或複製到 `.codex/codex/archive/legacy-YYYY-MM-DD/`，確認新版摘要與索引已建立後，才移除根目錄 `codex/` 中的舊版檔案。
- 不得直接刪除舊檔內容；必須先在 `.codex/codex/archive/` 留下可回查全文。若移動失敗、封存不完整或驗證失敗，停止移除並回報阻塞。
- 必須建立缺少的新骨架：`.codex/AGENTS.md`、`.codex/codex/00_START_HERE.md`、`.codex/codex/PROJECT.md`、`.codex/codex/CURRENT_STATE.md`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/ARCHITECTURE.md`、`.codex/codex/DECISIONS.md`、`.codex/codex/GOTCHAS.md`、`.codex/codex/VERIFY.md`、`.codex/codex/COMMANDS.md`、`.codex/codex/playbooks/`、`.codex/codex/knowledge/`、`.codex/codex/archive/`、`.codex/codex/tmp/`、`.codex/codex/private/`、`.codex/codex/artifacts/`。
- `log.md` 使用小寫檔名，不要建立 `LOG.md`。若舊專案已有 `codex/log.md`，先把舊內容封存到 `.codex/codex/archive/legacy-YYYY-MM-DD/log.md`；新版 `.codex/codex/log.md` 不沿用舊全文，只能在需要近期工作摘要時用新版格式重建。
- 新檔以「高訊號摘要 + 路由索引」為主，不要把舊檔全文複製到新檔。
- 舊檔與新檔要建立清楚映射：`README_PEICD100.md` -> `.codex/codex/PROJECT.md`，`專案規格書.md` -> `.codex/codex/ARCHITECTURE.md`，`使用者要求.md` -> `.codex/codex/USER_REQUIREMENTS.md`，`協作重要事項.md` -> `.codex/codex/GOTCHAS.md`，`log.md` -> `.codex/codex/archive/log-history-summary.md` 與必要時的新格式 `.codex/codex/log.md`。
- 若舊 `log.md` 很大，先完整封存，再建立 `.codex/codex/archive/log-history-summary.md` 摘要舊版本脈絡。不要因大小寫或新舊格式覆蓋掉舊 log。
- 遷移完成後，必須在 `.codex/codex/00_START_HERE.md` 記錄讀取順序、任務路由、新舊檔案映射與高風險注意事項。
- 遷移完成後，必須在 `.codex/codex/DECISIONS.md` 記錄「採用 `.codex/codex/` 分層結構」、舊檔已封存並從根目錄移除，以及任何檔名相容決策，例如 Windows 下使用 `log.md`。
- 遷移完成後，不再同步更新舊 `README_PEICD100.md`、`專案規格書.md`、`使用者要求.md`、`協作重要事項.md`。這些舊檔只作為 `.codex/codex/archive/legacy-YYYY-MM-DD/` 中的歷史全文供查閱。
- 遷移完成前必須驗證：舊檔全文在 `.codex/codex/archive/legacy-YYYY-MM-DD/` 存在、根目錄 `codex/` 不再有舊版檔案、新版入口檔能指向封存位置、中文文字檔為 UTF-8 無 BOM。
- 若專案 `.gitignore` 已忽略整個 `codex/`，先維持現狀，不擅自改提交策略；但在完成回報中提醒使用者：若希望不同代理或不同電腦透過 Git 取得舊 `codex/` 或新版 `.codex/codex/`，需要另行調整 `.gitignore`。

### 4.5 根目錄轉址檔規則

- 新專案優先不要在根目錄建立協作檔。
- 若某些工具只能自動讀取根目錄 `AGENTS.md`，可以建立極短轉址檔，但內容只能指向 `.codex/AGENTS.md`，不得維護第二份完整規則。
- 根目錄轉址檔範例：

```md
# AGENTS.md

本專案代理規則已集中於 `.codex/AGENTS.md`。請先讀取該檔，並以該檔內容為準。
```

### 4.6 遷移完成時的交接摘要模板

當完成根目錄協作檔搬遷到 `.codex/` 時，必須在 `.codex/codex/log.md` 或 `.codex/codex/CURRENT_STATE.md` 留下以下摘要：

```md
## YYYY-MM-DD：`.codex/` 集中式協作目錄遷移

- 狀態：completed | partial | blocked
- 本次遷移範圍：
  - `codex/` -> `.codex/codex/`
  - `codex_compressed/` -> `.codex/codex_compressed/`
  - `codex_tmp/` -> `.codex/codex_tmp/`
  - 其他：
- 已封存舊資料：
- 已建立或更新的新入口：
- `.gitignore` 調整：
- 驗證結果：
- 尚未處理：
- 下一位代理接手時必讀：
```

若遷移被阻塞，必須明確留下阻塞原因、已完成步驟、未完成步驟與不可刪除的舊檔清單。

---

## 5. 每次任務的讀取流程

進入專案後：

1. 讀取 `.codex/AGENTS.md` 或實際找到的 `AGENTS.md`，並回報完整路徑。
2. 若存在 `.codex/codex/00_START_HERE.md`，先讀它。
3. 再讀 `.codex/codex/CURRENT_STATE.md`、`.codex/codex/USER_REQUIREMENTS.md`、`.codex/codex/GOTCHAS.md`。
4. 依任務類型從 `.codex/codex/00_START_HERE.md` 路由讀取 `.codex/codex/ARCHITECTURE.md`、`.codex/codex/VERIFY.md`、`.codex/codex/playbooks/` 或 `.codex/codex/knowledge/` 中相關文件。
5. 若不存在 `.codex/codex/00_START_HERE.md` 但偵測到舊版 PEICD `codex/` 格式，依第 4 章判斷：本次已進入專案修改或使用者要求整理協作記憶時建立新版骨架；唯讀任務只回報建議，不改檔。
6. 若是尚未遷移的舊結構，至少讀取 `codex/README_PEICD100.md`、`codex/專案規格書.md`、`codex/使用者要求.md`、`codex/協作重要事項.md`、`codex/log.md`。
7. 若 `.codex/codex/` 與根目錄 `codex/` 同時存在，先以 `.codex/codex/` 為主，根目錄 `codex/` 只作待檢查 legacy 資料，不能直接覆蓋新版記憶。
8. 若協作檔不存在，而本次任務會修改專案，先建立必要的 `.codex/` 與 `.codex/codex/` 骨架。

不要把整個 `.codex/codex/` 當作無限制 context dump。入口檔負責路由，細節檔按需讀取。

---

## 6. 自適應成長規則

`.codex/codex/` 可以隨專案成長，但必須受控。記憶生命週期：

- `observation`：本次觀察、錯誤、使用者修正，先寫入 `.codex/codex/log.md` 或相關暫存紀錄。
- `candidate`：可能再次影響協作，但尚未證實。
- `stable`：已重複出現或已被驗證，提升到要求、決策、踩坑或 checklist。
- `archived`：歷史保留，不再主動套用。

成長操作：

- `Promote`：同一問題、偏好或錯誤出現兩次以上，提升到長期記憶。
- `Specialize`：單一主題內容過長或反覆被使用時，拆成 `.codex/codex/knowledge/<topic>.md` 或 `.codex/codex/playbooks/<topic>.md`。
- `Compress`：舊 log 壓縮成摘要，細節移到 `.codex/codex/archive/`。
- `Retire`：被新規則取代時標記 `superseded`，不要直接刪除。
- `Link`：決策、踩坑、檢查清單、相關檔案與驗證方式要互相連結。

每次新增、拆分、合併或歸檔長期記憶，都要同步更新 `.codex/codex/00_START_HERE.md` 或既有索引。

---

## 7. 記憶品質與格式

- `.codex/codex/00_START_HERE.md` 目標維持在 150 行內。
- `.codex/codex/CURRENT_STATE.md` 只保留目前交接需要的資訊，不寫長篇歷史。
- `.codex/codex/log.md` 只保留近期紀錄；舊紀錄定期壓縮到 `.codex/codex/archive/`。
- 每個 `.codex/codex/knowledge/*.md` 或 `.codex/codex/playbooks/*.md` 只記一個主題。
- 不要把一次性聊天內容、未驗證猜測、完整錯誤長文、API token、密碼、私密路徑或大型輸出塞進長期記憶。
- 長期記憶必須能讓下一個代理直接行動，避免只寫「已修正」這種無法執行的句子。

重要記憶建議格式：

```md
## <條目名稱>

- 狀態：active | candidate | superseded | archived
- 證據：user-requested | verified | observed | inferred
- 日期：YYYY-MM-DD
- 影響範圍：
- 正確做法：
- 不要做：
- 驗證方式：
- 相關檔案：
```

重要決策建議格式：

```md
## ADR-0001：<決策標題>

- 狀態：proposed | accepted | deprecated | superseded
- 日期：YYYY-MM-DD
- 背景：
- 選項：
- 決策：
- 原因：
- 後果：
- 取代：
- 相關檔案：
```

---

## 8. 修改專案時的維護要求

只要修改專案檔案，完成前必須更新 `.codex/codex/` 的對應文件：

- 新增或改變使用者長期要求：更新 `.codex/codex/USER_REQUIREMENTS.md` 或舊結構的 `codex/使用者要求.md`。
- 新增功能、調整架構、改資料流、改打包或部署：更新 `.codex/codex/ARCHITECTURE.md`、`.codex/codex/PROJECT.md` 或舊結構的 `codex/專案規格書.md`。
- 做出重要技術取捨：更新 `.codex/codex/DECISIONS.md`。
- 發現坑、相容性問題、未來容易重犯的錯：更新 `.codex/codex/GOTCHAS.md` 或舊結構的 `codex/協作重要事項.md`。
- 改變測試、打包、部署方式：更新 `.codex/codex/VERIFY.md`、`.codex/codex/COMMANDS.md` 或專案 README。
- 每次實際修改完成：更新 `.codex/codex/log.md`。
- 只要本次任務修改了專案 `.codex/codex/` 中任何檔案或資料夾，完成前必須將整個專案 `.codex/codex/` 壓縮到 `.codex/codex_compressed/` 資料夾。
- `.codex/codex_compressed/` 中只保留一個壓縮檔；建立新壓縮檔前或確認新壓縮檔成功後，移除舊壓縮檔。壓縮檔使用日期時間命名，例如 `2026-05-18_113000.tar.gz`。
- 壓縮內容必須包含完整 `.codex/codex/` 目錄結構，輸出位置不得放在 `.codex/codex/` 內，避免把備份壓縮檔再次納入下一次壓縮。
- 這個流程可以用腳本執行；若使用腳本，腳本必須從專案根目錄執行，確認 `.codex/codex/` 存在後再壓縮，並在完成回報中列出產生的壓縮檔完整路徑。
- 產生暫存檔、輸出檔、協作檔或建置產物時，檢查 `.gitignore` 是否需要加入 `.codex/codex/tmp/`、`.codex/codex/private/`、`.codex/codex/artifacts/`、`.codex/codex_tmp/`、`.codex/tmp/`、`.codex/private/`、`.codex/artifacts/`、build output、敏感檔。
- 新專案或尚未有 `.gitignore` 的專案，只要本次進入修改階段，就必須新增 `.gitignore`；至少忽略 `.codex/codex/tmp/`、`.codex/codex/private/`、`.codex/codex/artifacts/`、`.codex/codex_tmp/`、`.codex/tmp/`、`.codex/private/`、`.codex/artifacts/`、常見 build output、暫存檔與敏感檔。

若既有專案已把整個 `codex/` 或 `.codex/` 加入 `.gitignore`，先維持現狀，不要擅自改提交策略。新專案必須只忽略暫存、私密、artifacts 與機器本地輸出，讓可交接的記憶檔能進版本控制。

若專案是 Python 程式，且使用者需要雙擊執行，應維護：

- `.codex/vbs_bat/<專案資料夾名>.vbs`
- `.codex/vbs_bat/run.bat`

若入口、conda 環境或參數改變，必須同步更新。

---

## 9. 驗證要求

- 修改程式碼後，依專案慣例執行最小可靠驗證；例如 format、lint、typecheck、unit test、build、smoke test。
- 若無法執行驗證，必須說明原因與剩餘風險。
- 修 bug 時優先新增或更新防回歸測試。
- 不要平行執行會搶同一 build cache 或測試資源的命令。
- 若任務涉及 UI，應視專案技術棧使用截圖、瀏覽器、模擬器或實機做視覺檢查；若使用者明確取消，就不要啟動。
- 若任務涉及 PDF 且可能是掃描圖，必須配合視覺理解，不只讀文字層。
- 若本次做了 `.codex/` 遷移，至少驗證：舊檔完整封存、新路徑存在、根目錄不再殘留應遷移的協作檔、`.gitignore` 規則沒有誤忽略可交接文件、中文文字檔為 UTF-8 無 BOM。

---

## 10. Git 與發布

- 不要自動 commit、push、開 PR，除非使用者明確要求。
- 使用者說「推送到 git」時，表示要協助完成合理 commit 並推送；commit 訊息由代理依修改內容決定。
- 不要使用 `git reset --hard`、`git checkout --`、`git clean -fd` 等破壞性操作，除非使用者明確要求或已清楚確認。
- 提交前要檢查 `git status`，分辨自己修改與使用者既有修改，不要把不相關變更混入說明。
- 若 `.codex/` 中包含可交接文件，提交前要確認 `.gitignore` 沒有把 `.codex/AGENTS.md` 與 `.codex/codex/` 的核心文件整個擋掉。
- 使用者要求打包時，先打包 debug 版並驗證可執行，再打包 noconsole / release 或平台等價產物。
- Android `.apk` 檔名要包含版本號，版本號如何變化由代理依專案狀態決定。

---

## 11. 多代理模式

只有使用者明確要求多代理、第二代理、reviewer 或 parallel agents 時才啟用。

- 全部任務完成後，必須由第二代理從頭重檢。
- 第二代理必須從 `.codex/AGENTS.md` 與 `.codex/codex/00_START_HERE.md` 開始讀取，不得只看主代理摘要。
- 主代理依 reviewer 意見修正後再送審，直到沒有實質改進建議才可宣布完成。
- 不得因等待逾時就再開一個代理；等待太久時回報狀態，由使用者決定是否中止或改派。

---

## 12. PEICD 個人偏好

- 全程繁體中文。
- GUI / 介面 / 視窗主題色預設使用 `#72e3fd`，但應作為重點色，不要無腦大面積鋪滿。
- UI 要避免陽春感；優先使用一致 spacing、8px 左右圓角、清楚層級、可掃描資訊密度與穩定 safe area。
- 若專案使用 conda，環境名稱優先從專案 README 或 `.codex/codex/` 記錄讀取；沒有記錄時預設 `PEICD100`。若不適合，先提出原因再建立新環境。
- 不假設 conda 已加入 PowerShell PATH。需要 conda 時優先使用 batch activate 流程：

```bat
call "<CONDA_BASE>\Scripts\activate.bat" "<CONDA_BASE>"
conda activate base
conda activate PEICD100
```

- 若需要語音，英文預設使用 Microsoft Edge / Azure Neural TTS 的 `en-US-JennyNeural`。
- 若專案是 Android app，簽名預設使用 `PEICD100`，除非專案記憶另有規定。
- 若專案有 GPU/CPU 路徑，優先提供 GPU 可用時的加速路徑；但任何可能造成閃退或相容風險的 GPU 路徑必須做成明確選項與 fallback。
- CLI 長時間執行若專案有既定格式，底部 spinner 使用 `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`，整行只放 spinner 與 4 個空格。
- 進度條使用類似 `⣿⣿⣿⣿⣿⣿⣷⣦⣀⣀⣀⣀⣀⣀⣀ 37%` 的格式。

---

## 13. 完成回報格式

任務完成後，回覆分三部分：

1. 已完成：說明做了什麼、怎麼做、使用了什麼。
2. 未完成：說明哪些要求沒有做到，以及原因。
3. 需要使用者手動處理：若有，列出具體步驟；若沒有，明確說沒有。

回覆要直接、具體，不要空泛稱讚。涉及檔案時使用完整路徑。涉及網路查證時附來源連結。
