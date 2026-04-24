「


轉換規則（第一種純文字題目 → 第二種：Markdown + TTS + 正確答案標記 + 克漏字回填 + 句子切分）v2.2

【目標輸出（第二種）】
- 以 Markdown 結構化題目（## 題號 / ### 子題號）。
- 需要朗讀的文字行，加上 <span class="tts">…</span>（一律閉合）。
- 可判定正確答案時：在「正確選項那一行」的第一個字元插入「⭐」。不可判定則不插入。
- 文法題／克漏字題：題幹中的克漏字（例如 "------"）回填為 ^^<正確選項文字>^^。
- 長段落若同一行包含多個句子：轉換後「一句一行」，且每句各自包一個 <span class="tts">…</span>。
- 影像：不處理（忽略），由你後期自行加。

────────────────────────────────────────────────────────
0) 參數與外部資料（Inputs / Config）

0.1 必要外部資料
- ANSWER_KEY：{ 題號(int/str): "A"|"B"|"C"|"D" }
  用途：判定正確選項、克漏字回填。

0.2 固定設定
- CORRECT_MARKER = "⭐"
- CLOZE_TOKEN_REGEX = /-{2,}/  （2 個以上連字號視為克漏字 token）
- SENTENCE_SPLIT_REGEX = /(?<=[.!?])\s+/  （英文句尾 . ! ? 之後的空白作切分點；保留標點在前一句末尾）
  - 若要支援中文句號：可擴充為 /(?<=[.!?。！？])\s+/

0.3 可選外部資料（若你需要額外強調，不影響克漏字）
- HIGHLIGHT_MAP（可選）：{ 題號: [片語1, 片語2, ...] }
  用途：把題幹/敘述行中的指定片語包成 ^^片語^^。

0.4 渲染前提（環境要求）
- 你希望 ^^...^^ 有效果：需在 Markdown 渲染環境啟用 pymdownx.caret。
  （否則 ^^...^^ 可能只會顯示符號或效果不如預期。）

────────────────────────────────────────────────────────
1) 前處理（Normalization）

1.1 全文換行統一為 \n
1.2 去除每行行尾空白

1.3 連續 2 行以上空白行壓成最多 1 行空白

1.4 影像行忽略（不輸出、不參與解析）
- 若某行符合以下任一條件，直接略過：
  - 行首以 "![" 開頭（Markdown image）
  - 行首以 "![](" 或 "![alt" 等 image 變體開頭

────────────────────────────────────────────────────────
2) 題目區塊切分（Segmentation）

本規則把全文切成多個 block（題目區塊）。支援三種標頭：

2.1 單題標頭（single）
- Regex（允許前後空白；句點/冒號可有可無）：
  ^\s*Q\s*(\d+)\s*[\.:]?\s*$

2.2 題組範圍標頭（range-direct）
- Regex（允許空白；可寫 Q135-Q138 或 Q135 - Q138）：
  ^\s*Q\s*(\d+)\s*-\s*Q?\s*(\d+)\s*$

2.3 題組導語標頭（range-intro）
- Regex（大小寫不敏感；允許多空白）：
  ^\s*Questions\s+(\d+)\s+to\s+(\d+)\s+refer\s+to\b.*$

2.4 切分規則（狀態機）
- 遇到 2.2 或 2.3 → 開新 block.type = range，記錄 start/end。
- 遇到 2.1：
  - 若當前不在 range block → 結束上一個 block，開新 block.type = single。
  - 若當前在 range block：
    - 若題號 n ∈ [start, end] → 視為「子題標頭」（見 3.2/4.2），不得另開新 block。
    - 若題號 n ∉ [start, end] → 結束此 range block，另開新 single block。
- range block 的結束條件：
  - 遇到下一個 range 標頭（2.2/2.3），或
  - 遇到題號不在範圍內的 single 標頭（2.1）。

────────────────────────────────────────────────────────
3) Markdown 標頭輸出（Heading Rendering）

3.1 single block
- 輸出：## {題號}
- 後接 1 空行

3.2 range block
- 輸出：## {start}-{end}
- 後接 1 空行
- range-intro 的那一行（"Questions X to Y refer to ..."）屬於內容行：視為一般敘述行（5.3）輸出 TTS。

────────────────────────────────────────────────────────
4) 題內處理核心：current_qid + 兩階段解析

4.1 current_qid 狀態
- single block：current_qid = block.num（整題固定）
- range block：
  - 只有在遇到子題標頭（4.2）時才更新 current_qid。
  - 所有 ANSWER_KEY 查表、克漏字回填、正確選項加星，都以 current_qid 為準。

4.2 子題標頭（Sub-question Header）
- 僅在 range block 內啟用
- Regex（等同 2.1 但用作子題，不切 block）：
  ^\s*Q\s*(\d+)\s*[\.:]?\s*$

輸出：
- ### {題號}
- 後接 1 空行

4.3 題內「兩階段」處理（為了克漏字回填，但不改變輸出順序）
對於每個題號（single 的整題；range 的每個子題），採以下流程：

階段 A：解析（不輸出）
- 依原始行序掃描，分類並蒐集：
  A1) option_lines（選項行，保留原順序）
  A2) stem_lines（題幹/敘述/對話/段落行，保留原順序）
  A3) option_map：{A: textA, B: textB, C: textC, D: textD}（由選項行建立）

階段 B：渲染輸出（輸出順序固定：先題幹後選項）
- 先輸出 stem_lines（套用：克漏字回填 → 可選 HIGHLIGHT → 句子切分 → TTS 包裝）
- 再輸出 option_lines（套用：正確選項加星 → TTS 包裝）

────────────────────────────────────────────────────────
5) 行分類與輸出格式（Line Classification & Rendering）

（以下規則在「解析階段 A」用來分類；在「渲染階段 B」用來輸出格式。）

5.1 選項行（Option）
- Regex：^\s*([A-D])\)\s*(.+?)\s*$

解析階段：
- 存入 option_lines（保留原字母與文字）
- option_map[Letter] = OptionText

渲染階段：
- 先判定是否「可判定正解」：
  條件同時成立才算可判定：
    (1) ANSWER_KEY 存在且含 current_qid
    (2) ANSWER_KEY[current_qid] ∈ {A,B,C,D}
    (3) option_map 含該字母（可取得正確選項文字）

- 若可判定且此行 Letter == 正解字母：
    輸出：⭐{Letter}) <span class="tts">{OptionText}</span>
- 否則：
    輸出：{Letter}) <span class="tts">{OptionText}</span>

注意：
- 「⭐」必須是該行第一個字元（前面不得有空白）。
- 若不可判定：所有選項行都不加 ⭐。

5.2 對話行（Dialogue）
- 僅在「對話題」語境內啟用（例如 range-intro 後出現多行對話）。
- Speaker 白名單（最小集）：W, M
- Regex：^\s*([WM])\s*:\s*(.+?)\s*$

輸出：
- 預設支援句子切分：若 Utterance 內有多句，則分多行輸出，每行都保留 Speaker。
  - {Speaker}: <span class="tts">{Sentence1}</span>
  - {Speaker}: <span class="tts">{Sentence2}</span>
  （若你不想對話多行，可在實作時關閉此行為，僅對 5.3 啟用句子切分。）

5.3 一般敘述行（Narration / Passage / Question stem）
條件：非空行，且不符合 5.1/5.2。

輸出：
- 先對該行執行「文字轉換流程」（第 6～7 節 + 第 5.5 節），再輸出。
- 若句子切分後得到多句：每句各一行，各自包一個 <span class="tts">…</span>。
  - <span class="tts">{Sentence1}</span>
  - <span class="tts">{Sentence2}</span>

5.4 空行（Blank line）
- 原樣輸出空行（用於分段）

5.5 句子切分（Sentence Splitting）
目的：讓像「Welcome shoppers. To celebrate ...!」這種同一行多句敘述，在輸出時做到「一句一個 span」。

規則：
- 對待輸出的文字字串 text（已完成克漏字回填與可選強調）執行：
  - sentences = split(text, SENTENCE_SPLIT_REGEX)
  - 每個 sentence 做 trim（去掉前後空白）
  - 過濾掉空字串
- 若 sentences 長度 = 1：維持單行輸出
- 若 sentences 長度 ≥ 2：每句輸出成獨立一行

注意（保守）：
- 本規則為啟發式，可能在縮寫（e.g., Mr., Dr.）或小數點（3.14）處產生誤切。
  - 若你想降低誤切，可在實作時加入縮寫白名單或更進階的斷句器。

────────────────────────────────────────────────────────
6) 克漏字回填（Cloze Fill-in）

6.1 適用範圍
- 僅對「題幹/敘述行」（5.3）與（若啟用）「對話內容」（5.2 的 Utterance）套用。
- 不對選項文字做克漏字回填。

6.2 回填規則
- 在待輸出的文字中偵測 CLOZE_TOKEN_REGEX（/-{2,}/）。
- 若某一行偵測到 1 個克漏字 token，且「可判定正解」成立：
  - correct_letter = ANSWER_KEY[current_qid]
  - correct_text = option_map[correct_letter]
  - 將該 token 取代為：^^{correct_text}^^

6.3 保守規則（避免誤填）
- 若不可判定正解：不回填（保留原 token）。
- 若同一行出現多個克漏字 token（>1）：不自動回填（保留原 token）。

────────────────────────────────────────────────────────
7) 額外強調（可選，HIGHLIGHT_MAP）

7.1 適用時機
- 建議在「克漏字回填之後」再套用，避免把 ^^...^^ 結構弄亂。

7.2 規則
- 若 HIGHLIGHT_MAP[current_qid] 存在，對每個片語 phrase：
  - 在題幹/敘述行中，將 phrase 包成 ^^phrase^^。

7.3 保守規則
- 若 phrase 已在某段 ^^...^^ 之內：建議不重複包（避免巢狀）。

────────────────────────────────────────────────────────
8) 版面與空行（Spacing）

8.1 每個 block 標頭（##）後保留 1 空行
8.2 每個子題標頭（###）後保留 1 空行
8.3 題幹/段落與選項群之間建議保留 1 空行（題幹輸出完 → 空行 → 選項群）
8.4 block 結束後保留至少 1 空行

────────────────────────────────────────────────────────
9) 最小可判定條件（"無法分辨就不用加" 的定義）

對每一題（current_qid），只要以下任一不成立，即視為「不可判定」：
- ANSWER_KEY 不存在或不含 current_qid
- ANSWER_KEY[current_qid] 不是 A/B/C/D
- 該題未解析到對應字母的選項文字（option_map 缺值）

不可判定時：
- 不加 ⭐
- 不做克漏字回填（保留 "------" 等 token）

────────────────────────────────────────────────────────
10) 轉換輸出摘要（你可拿來檢查）

- 題號：Q14. → ## 14
- 題組導語：Questions 53 to 55 refer to ... → ## 53-55 + 導語行以 TTS 輸出
- range 內子題：Q53. → ### 53
- 選項：A) foo → A) <span class="tts">foo</span>
- 正解選項：B) bar 且可判定 → ⭐B) <span class="tts">bar</span>
- 克漏字：All tenants ------ to pay ...（可判定正解且該行只有 1 個 token）→
  All tenants ^^<正確選項文字>^^ to pay ...（再進行句子切分與 TTS 包裝）
- 多句同一行（示例）：
  輸入：Welcome shoppers. To celebrate our tenth anniversary, ... deals!
  輸出（示意）：
    <span class="tts">Welcome shoppers.</span>
    <span class="tts">To celebrate our tenth anniversary, ...</span>
    ...
    <span class="tts">... great deals!</span>


」

請依照以上轉換規則，幫我轉換這個檔案，不需要使用腳本，你直接編輯即可。