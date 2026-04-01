## 管道化


已啟用教學模式

#### 先抓整體：這幾頁到底在回答什麼問題

這一大段其實在回答兩個核心問題：

1. **為什麼 CPU 要做 pipelining(管道化)**
2. **做了 pipelining 之後，為什麼又會冒出一堆麻煩，例如 hazard(危障)**

最直覺的說法是：
**管道化不是把一個人洗衣服洗得更快，而是讓很多批衣服同時卡在不同步驟裡面一起往前推。**
放到 CPU 上，就是：**不是讓一條 instruction(指令) 瞬間變短，而是讓很多條指令重疊執行，提高 throughput(吞吐量)**。理想上 speedup(加速比) 會接近管線的 stage(階段) 數，但實際上會被各階段不平均、管線填滿/排空成本，以及 hazard 拉低。([cs.umd.edu][1])

```mermaid
flowchart TB
    A[單一指令執行<br>IF → ID → EX → MEM → WB] --> B[多條指令重疊執行]
    B --> C[Throughput(吞吐量)上升]
    B --> D[Hazard(危障)出現]
    D --> E[Structural Hazard(結構危障)]
    D --> F[Data Hazard(數據危障)]
    D --> G[Control Hazard(控制危障)]
```

---

#### 一、4.5 管道化處理概觀：先用洗衣服把直覺建立起來

你的教材從 **洗、烘、摺、收** 這四步驟開始講，這個比喻非常重要。

##### 1. 這段在回答什麼問題

它在回答：
**為什麼把工作拆成多階段重疊做，總完成量會變大？**

##### 2. 核心概念

非管道化(non-pipelined)做法是：

* 第一批衣服：洗完
* 再烘完
* 再摺完
* 再收完
* 然後才做第二批

這樣做的問題不是每一步慢，而是**很多資源在等**。
例如你在摺衣服時，洗衣機和烘衣機是閒著的。

管道化(pipelined)做法是：

* 第一批在烘時，第二批可以開始洗
* 第一批在摺時，第二批在烘、第三批在洗

也就是：

* **不同批次**
* **同時佔據不同階段**
* **彼此重疊(overlap)**

這正是 instruction pipeline(指令管線) 的本質。([cs.umd.edu][1])

##### 3. 生活化例子

像便當店做餐：

* 一個人從頭到尾做完一份便當，再做下一份
  → latency(單份完成時間)看起來簡單，但整體產量低

* 改成分站：

  * A 洗菜
  * B 切菜
  * C 炒
  * D 裝盒

這時一份便當不一定比較早完成，
但**一小時內能出更多份**。

##### 4. 最容易混淆的地方

這裡最重要的一句話是：

**Pipeline 改善的是 throughput(吞吐量)，不是 latency(延遲)。**
也就是說：

* ✅ 單位時間完成更多指令
* ❌ 單一指令一定更快

這是整段最核心、也最常考錯的觀念。教材後面用 800 ps 與 200 ps 的例子，就是在證明這件事。([cs.umd.edu][1])

##### 5. 小結

洗衣服例子不是在說「CPU 真的像洗衣機」，
而是在幫你抓到一個抽象：

> **把工作切成階段，讓多個工作同時處在不同階段，就能提升整體產量。**

---

#### 二、MIPS 的五級管道是什麼

你的頁面接著把洗衣服例子對應到 MIPS 的 5-stage pipeline(五級管線)：

1. **IF, Instruction Fetch(指令擷取)**
2. **ID, Instruction Decode / Register Read(指令解碼 / 暫存器讀取)**
3. **EX, Execute / Address Calculation(執行 / 位址計算)**
4. **MEM, Memory Access(記憶體存取)**
5. **WB, Write Back(寫回)**

這五步是經典 MIPS pipeline 的骨架。([cs.umd.edu][2])

##### 1. 用一條指令來看

例如：

```asm
lw $s1, 100($s0)
```

它在五個階段大致做的是：

* **IF**：從 instruction memory(指令記憶體) 把 `lw` 抓出來
* **ID**：看懂這是 `lw`，讀 `$s0`
* **EX**：算有效位址 `$s0 + 100`
* **MEM**：去 data memory(資料記憶體) 把內容讀出來
* **WB**：把資料寫回 `$s1`

而像 `add $t0,$t1,$t2` 這種 R-type(暫存器型) 指令：

* IF：抓指令
* ID：讀 `$t1`,`$t2`
* EX：ALU 相加
* MEM：這階段通常沒事做
* WB：把結果寫回 `$t0`

##### 2. 為什麼要切成這五段

因為這樣可以讓不同指令在不同硬體單元上同時前進。
例如當第 1 條在 EX 時，第 2 條可以在 ID，第 3 條可以在 IF。
這就是頁面中一直畫斜斜排開的原因。([cs.umd.edu][2])

##### 3. 小結

五級管道不是隨便切的，
而是把一條指令從「抓、看懂、運算、碰記憶體、寫回」拆成五個可重疊的步驟。

---

#### 三、圖 4.26、4.27：single-cycle(單一時脈週期) 和 pipelined(管道化) 到底差在哪

這幾頁是整章最關鍵的數字例子。

教材給了各功能單元的延遲：

* Instruction memory / fetch：200 ps
* Register read：100 ps
* ALU：200 ps
* Data memory：200 ps
* Register write：100 ps

##### 1. 非管道化 single-cycle 為什麼是 800 ps

如果是 single-cycle design(單一時脈週期設計)，
**每條指令都要在同一個 clock cycle(時脈週期) 裡全部做完**。

所以 clock period(時脈週期長度) 必須容納**最慢的那條指令**。
在教材例子裡，最慢的是 `lw`：

* IF 200
* ID 100
* EX 200
* MEM 200
* WB 100

總共 **800 ps**

所以：

* `lw` 要 800 ps
* `sw` 明明只需要 700 ps，還是得等 800 ps
* R-type 明明只需要 600 ps，也還是得等 800 ps
* `beq` 只要 500 ps，仍然得等 800 ps

這就像全班考試明明有人 30 分鐘能寫完，但規定每個人都要坐滿 2 小時才交卷。
系統設計被最慢者綁住。([cseweb.ucsd.edu][3])

##### 2. 管道化為什麼可以變成 200 ps

管道化後，每個 stage 各佔一個 clock cycle。
所以新的 clock period 只要能容納**最慢的 stage** 就好，不必容納整條指令。

在這例子裡最慢 stage 是 200 ps，
所以 pipeline clock 可以設成 **200 ps**。([cs.umd.edu][1])

##### 3. 但單一指令有變快嗎

沒有，甚至常常更慢。

因為一條 `lw` 現在要走 5 個 stage：

* 5 × 200 ps = 1000 ps

所以你會看到一個很反直覺但很重要的結論：

* single-cycle：一條 `lw` = 800 ps
* pipelined：一條 `lw` ≈ 1000 ps

**單條指令 latency 沒降，甚至上升。**

但如果連續做好多條指令：

* non-pipeline 每條都要再加 800 ps
* pipeline 每多一條通常只要再加 200 ps

這就是「一開始不一定贏，做久了就贏很大」的原因。([cs.umd.edu][1])

##### 4. 為什麼教材算出來不是 5 倍，而是接近 4 倍

因為理想 speedup ≈ stage 數，只在很理想的情況成立：

* 階段長度很平均
* 沒有額外 pipeline register overhead(管線暫存器負擔)
* 指令數很多
* 沒有 hazard

教材這個例子裡並不平均：

* 有的 stage 100 ps
* 有的 stage 200 ps

所以 clock 還是被 200 ps 綁住，
100 ps 的那些 stage 等於有一半時間在閒著。
再加上管線剛開始要 fill(填滿)、最後要 drain(排空)，
因此真實 speedup 會小於 stage 數。([cs.umd.edu][1])

##### 5. 這段最容易考

最常錯的兩句：

* **Pipeline 提升 throughput，不保證降低 latency**
* **理想 speedup ≈ 管線級數，但實際通常比較小**

---

#### 四、頁 274–275：為什麼說 MIPS 是「為管道化而設計」的 ISA

這裡教材其實在講一個更深的問題：

> 不是只有硬體要管道化，連 ISA(Instruction Set Architecture，指令集架構) 也會影響管道化容不容易做。

你的教材列了四點，這四點非常重要。

##### 1. 固定長度 instruction

MIPS 指令長度固定。
好處是 IF 和 ID 很單純：

* 每次都抓固定大小
* 不用猜下一條指令到底長幾 byte

可變長度指令會讓前端更複雜，對簡單 pipeline 不友善。([cseweb.ucsd.edu][3])

##### 2. 指令格式少，而且 register 欄位位置一致

這讓 ID 階段更容易：

* 比較容易解碼
* 比較容易同時讀 register file(暫存器檔)

因為硬體不用每次都重新猜「來源暫存器欄位到底藏在哪」。

##### 3. 記憶體運算只出現在 load / store

這是典型 load/store architecture(載入/儲存架構)。
意思是：

* 真正算術邏輯運算主要在 register 之間做
* 只有 `lw`,`sw` 會碰 memory

這很重要，因為如果每種指令都能直接 memory-to-memory，
那 pipeline 的 EX/MEM 會變超級複雜，也更容易出現 hazard。([cseweb.ucsd.edu][3])

##### 4. alignment(對齊)

資料對齊可以讓 memory access(記憶體存取) 比較規律，
避免一筆資料拆成兩次 memory 存取。
這對 pipeline 來說很關鍵，因為你希望 MEM stage 行為固定、可預測。

##### 5. 小結

所以「MIPS 適合管道化」不是口號，
而是因為它的 ISA 幫硬體把事情先整理乾淨了。

---

#### 五、hazard(危障) 是什麼

現在進入第二大主題：
**既然 pipeline 這麼棒，為什麼還會卡住？**

hazard 就是：

> **原本希望下一條指令照時鐘節拍正常往前走，但因為某種衝突或依賴，做不到。**

教材分成三類，這也是標準分類。([cs.umd.edu][1])

##### 1. Structural Hazard(結構危障)

硬體資源撞車。
兩條指令同一時間想用同一個硬體，但只有一份。

##### 2. Data Hazard(數據危障)

後面指令需要前面指令的結果，
但前面那條還沒生出來，或還沒送到可用的位置。

##### 3. Control Hazard(控制危障)

碰到 branch(分支) / jump(跳躍) 時，
下一條到底該抓哪裡，還不知道。

---

#### 六、Structural Hazard(結構危障)：不是資料錯，是硬體不夠

##### 1. 這段在回答什麼問題

如果 pipeline 裡每一級都同時跑，
會不會有兩條指令搶同一台機器？

答案是：會。這就是 structural hazard。([cs.umd.edu][1])

##### 2. 生活化例子

洗衣比喻裡，如果你不是「洗衣機 + 烘衣機」各一台，
而是只有一台機器同時兼任洗和烘，
那某一批在洗時，另一批就不可能同時烘。

##### 3. CPU 版本

最典型例子是：

* 某條 `lw/sw` 在 MEM stage 要用 memory
* 同時另一條指令在 IF stage 也要去抓 instruction memory

如果 instruction 和 data 共用同一個 memory，
這兩個需求會衝突。
所以教材才會說，pipelined datapath 常需要分開的 instruction/data memory 或 cache。([cs.umd.edu][1])

##### 4. 解法

兩種：

* **stall(停滯)**：先讓其中一個等
* **加硬體**：把資源複製開，例如 I-cache / D-cache 分離

##### 5. 易混淆

很多人一看到 hazard 就只想到資料相依，
但 structural hazard 跟資料內容無關，
它是**資源衝突(resource conflict)**。

---

#### 七、Data Hazard(數據危障)：前一條還沒算完，下一條就急著要用

這是最核心、也最常考的部分。

##### 1. 最基本的直覺

看這兩條：

```asm
add $s0, $t0, $t1
sub $t2, $s0, $t3
```

第二條 `sub` 需要 `$s0`，
但 `$s0` 是第一條 `add` 才剛要算出來的。

問題不是「永遠拿不到」，
而是「**當第二條需要時，第一條還沒正式寫回 register file**」。
這就叫 data hazard。([cs.umd.edu][4])

##### 2. forwarding(前饋) / bypassing(繞送) 是什麼

forwarding 的核心思想是：

> **既然結果其實已經在 pipeline 中間某個地方算出來了，就不要傻傻等它一路走到 WB 再回 register file，直接從中途送到下一條指令要用的地方。**

也就是：

* 結果剛在 EX 算好
* 下一條很快就要在 EX 用到
* 那就直接把 EX/MEM pipeline register 裡的值餵回 ALU input

這就是圖 4.29 在畫的事。([cs.umd.edu][4])

##### 3. 為什麼 add → sub 可以靠 forwarding 解掉

因為 `add` 的結果在 **EX 結束** 時就已經有了。
而下一條 `sub` 真正需要它，是在自己的 **EX 開始**。

時間還接得上。
所以可以 forward，通常**不用 stall**。([cs.umd.edu][4])

##### 4. 但為什麼 lw → use 還是要 stall

這是社群上最常卡住的點。

看：

```asm
lw  $s0, 20($t1)
sub $t2, $s0, $t3
```

`lw` 的資料不是在 EX 就算完，
而是要等到 **MEM stage 結束**，從 data memory 讀出來後才真的拿到。

但下一條 `sub` 在自己的 EX 就想用 `$s0`。
時間點太早了。

所以即使有 forwarding，
對標準 5-stage MIPS 來說，**load-use hazard(載入後立即使用危障)** 通常仍需要 **1 個 stall cycle**。
也就是插入一個 bubble(氣泡)。([cs.umd.edu][5])

##### 5. bubble(氣泡) / stall(停滯) 是什麼

bubble 你可以把它想成：

* pipeline 某格本來應該塞一條有效指令
* 但為了等資料，硬塞一個「空操作 NOP」

它看起來像東西還在流動，
但那一格其實沒做有效工作。

##### 6. 為什麼教材說 compiler(編譯器) 也能幫忙

因為有些 stall 可以透過 instruction scheduling(指令重排) 減少。

例如本來：

```asm
lw   $t1, 0($t0)
add  $t3, $t1, $t2
```

如果中間能插進一條與 `$t1` 無關的指令：

```asm
lw   $t1, 0($t0)
addi $s5, $s5, 1
add  $t3, $t1, $t2
```

就可能把原本的 bubble 拿去做別的事。
這就是頁 278 那個「重排程式碼以避免管道停滯」例子的核心。([cs.umd.edu][5])

##### 7. 補充一個很容易被問的點

在這種經典 **5-stage、in-order(循序發射)、單發射** MIPS pipeline 裡，
最主要會碰到的是 **RAW, Read After Write(先寫後讀相依)**。
而 **WAR / WAW** 在這種簡單管線裡通常不會成為問題，因為：

* 讀大多固定在 ID
* 寫大多固定在 WB
* 指令順序不會亂掉

所以時序上不會出現後讀先於前讀、後寫先於前寫這種情況。([cs.umd.edu][1])

---

#### 八、Control Hazard(控制危障)：問題不是資料，而是下一條指令去哪裡抓

##### 1. 這段在回答什麼問題

branch 指令像 `beq`,`bne` 會改變 PC。
但在 branch 條件尚未判定前，CPU 不知道下一條該抓：

* `PC + 4` 的順序下一條？
* 還是 branch target(分支目標)？

這種「下一步路線未定」就是 control hazard。([cs.umd.edu][6])

##### 2. 生活化例子

教材用洗足球制服的例子很不錯。

你必須先觀察洗完/烘完後衣服夠不夠乾淨，
才能決定下一步要不要改設定重洗。
在決定出來前，後面的動作不敢完全確定。

##### 3. 最保守的解法：stall

最簡單做法是：

* branch 進來後
* 先停住
* 等結果確定
* 再決定抓哪條

這很安全，但效能差。
教材頁 280 用「若 17% 指令是 branch，且每次多 1 個 cycle」算到 CPI 變成 1.17，重點不是 17 這個數字本身，而是要你理解：

> **branch 很常見，所以每次都停，代價很大。**

這也是為什麼控制危障非常麻煩。([cs.umd.edu][7])

##### 4. 第二種解法：prediction(預測)

既然等太慢，那就先猜。

最簡單的 static prediction(靜態預測) 是：

* **predict not taken(預測不分支)**
  先抓 `PC+4` 那條

如果猜對：

* 幾乎沒損失

如果猜錯：

* 把已經抓錯的指令 flush(清空)
* 插入 bubble
* 改抓正確目標

這就是你圖 4.32 的主軸。([cs.umd.edu][7])

##### 5. 第三種解法：delayed branch(延遲分支)

這是歷史上經典 MIPS 很有名的作法。

概念是：

* branch 後面那一格 delay slot(延遲槽)
* 不管 branch 成不成立，這一格都先執行

於是 compiler 嘗試把一條「不管跳不跳都安全」的指令塞進去，
把原本浪費的 bubble 變有用。

這在短而簡單的 in-order pipeline 很實用。([cs.umd.edu][6])

##### 6. 但現在還常用 delayed branch 嗎

你的教材把 delayed branch 當作重要概念，是對的，因為它是理解 control hazard 的經典方法。
但如果從現代 CPU 角度補充一句：

**新一代高效能處理器通常更依賴 branch prediction，而不是 branch delay slot。**
原因是 delay slot 對 superscalar(超純量)、out-of-order(亂序執行) 等高效能設計不太友善，控制更複雜、收益也變差。([Stack Overflow][8])

---

#### 九、頁 283 的自我檢查：三個序列怎麼判斷要不要 stall / forwarding

這頁其實很值得講，因為它是在訓練你「看相依性」。

##### 序列 1

```asm
lw   $t0, 0($t0)
add  $t1, $t0, $t0
```

這是 **load-use hazard**。
`add` 立刻要用 `lw` 載入的 `$t0`。
即使有 forwarding，對經典 5-stage pipeline 通常仍要 **stall 1 cycle**。([cs.umd.edu][5])

##### 序列 2

```asm
add   $t1, $t0, $t0
addi  $t2, $t0, #5
addi  $t4, $t1, #5
```

這裡第三條依賴第一條的 `$t1`，
但中間隔了一條不相依的 `addi $t2,...`。

所以這通常可以靠 forwarding 解決，
**不一定需要 stall**。
重點是：**有相依，不代表一定 stall；要看資料何時產生、何時被使用。**([cs.umd.edu][4])

##### 序列 3

```asm
addi  $t1, $t0, #1
addi  $t2, $t0, #2
addi  $t3, $t0, #2
addi  $t3, $t0, #4
addi  $t5, $t0, #5
```

這串幾乎都只是讀 `$t0`，
沒有「下一條急著讀前一條剛算出的結果」那種 RAW hazard。
雖然 `$t3` 被連續寫兩次，但在這種簡單 5-stage in-order pipeline 中，這不會形成你這章主講的那種 data stall。
所以大致可視為：

* **不用 stall**
* **也不特別需要 forwarding**

##### 這頁想考你的不是背答案

而是問你：

> **這條指令真正使用來源操作數，是在哪個 stage？前一條的結果又是在哪個 stage 才可用？**

只要你抓住這個判斷法，題目換一組寄存器名稱你也會做。

---

#### 十、頁 284 開頭：4.6 管道化數據通道及控制，在鋪什麼梗

這一頁是在告訴你：

前面 4.5 還是在講**概念與效能直覺**，
接下來 4.6 要開始進入真正硬體結構，也就是 datapath(數據通道) 和 control(控制)。

它把單週期 datapath 拆成 5 個部分：

1. IF
2. ID
3. EX
4. MEM
5. WB

並提醒你：
資料與指令大致從左到右流，
但有兩個重要「回頭」現象：

* **WB** 會把結果寫回中間的 register file
* **next PC selection** 會依 branch 結果改變之後從哪抓指令

這兩個「不是單純一路往右走」的地方，
正是後面控制邏輯最麻煩的來源。

---

#### 十一、把整段觀念串成一條線

你可以把頁 270–284 壓成下面這條主線：

1. **把指令執行切成 5 個 stage**
2. **讓多條指令同時卡在不同 stage**
3. **因此 throughput 變高**
4. **但重疊之後就會撞到**

   * 資源衝突 → structural hazard
   * 資料相依 → data hazard
   * 分支不確定 → control hazard
5. **所以要靠**

   * stall / bubble
   * forwarding
   * instruction scheduling
   * branch prediction
   * delayed branch（歷史/教材重點）

這就是這幾頁真正的大架構。([cs.umd.edu][1])

---

#### 十二、這段最容易考、也最容易混淆的地方

1. **Pipeline 提升 throughput，不保證降低 latency。**
2. **single-cycle 的 clock period 由最慢指令決定；pipeline 的 clock period 由最慢 stage 決定。**
3. **理想 speedup 接近 stage 數，不一定等於 stage 數。**
4. **forwarding 不是寫回暫存器後再讀，而是中途直接送到需要的位置。**
5. **add-use 常可靠 forwarding 解；load-use 通常還要 1 個 stall。**
6. **control hazard 是因為 next PC 不確定，不是因為資料值錯。**
7. **MIPS 適合管道化，和它的 ISA 設計有很大關係：固定長度、少格式、load/store、對齊。** ([cseweb.ucsd.edu][3])

---

#### 十三、小結

這幾頁你如果只記一句話，請記這句：

> **管道化的本質是用重疊執行換吞吐量；而所有 hazard，都是這個「重疊」帶來的副作用。**

再精簡成考前版：

* **Pipeline 是 overlap(重疊)**
* **好處是 throughput 上升**
* **代價是 hazard**
* **Data hazard 靠 forwarding / stall**
* **Control hazard 靠 stall / predict / delayed branch**

如果你要，我下一則可以直接接著幫你做一份：

**「頁 270–284 的考前背誦版重點整理」**
或是
**「把圖 4.28～4.32 一張一張重新畫成更好懂的時間線」**

[1]: https://www.cs.umd.edu/~meesh/411/CA-online/chapter/pipeline-hazards/index.html "https://www.cs.umd.edu/~meesh/411/CA-online/chapter/pipeline-hazards/index.html"
[2]: https://www.cs.umd.edu/users/meesh/411/Pipelining_Lecture.pdf "https://www.cs.umd.edu/users/meesh/411/Pipelining_Lecture.pdf"
[3]: https://cseweb.ucsd.edu/classes/wi12/cse141-a/Slides/03_ImplementingMIPS-e.pdf "https://cseweb.ucsd.edu/classes/wi12/cse141-a/Slides/03_ImplementingMIPS-e.pdf"
[4]: https://www.cs.umd.edu/~meesh/cmsc411/website/proj01/dlx/forwarding.html "https://www.cs.umd.edu/~meesh/cmsc411/website/proj01/dlx/forwarding.html"
[5]: https://www.cs.umd.edu/~meesh/411/mips-pipe/proj-fall11/mips-doc/node7.html "https://www.cs.umd.edu/~meesh/411/mips-pipe/proj-fall11/mips-doc/node7.html"
[6]: https://www.cs.umd.edu/~meesh/cmsc411/CourseResources/CA-online/chapter/handling-control-hazards/index.html "https://www.cs.umd.edu/~meesh/cmsc411/CourseResources/CA-online/chapter/handling-control-hazards/index.html"
[7]: https://www.cs.umd.edu/~meesh/411/CA-online/chapter/handling-control-hazards/index.html "https://www.cs.umd.edu/~meesh/411/CA-online/chapter/handling-control-hazards/index.html"
[8]: https://stackoverflow.com/questions/54724410/why-is-the-branch-delay-slot-deprecated-or-obsolete "https://stackoverflow.com/questions/54724410/why-is-the-branch-delay-slot-deprecated-or-obsolete"
