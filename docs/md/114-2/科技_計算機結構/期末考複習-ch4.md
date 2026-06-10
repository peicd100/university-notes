


## ⭐Processor Design Overview — CPU 設計為什麼要先從「指令需求」開始？

講義位置：PDF viewer page 1 ~ 12

### 1. 這一章在解決什麼問題？

前面 Chapter 3 主要在看 arithmetic(算術)：加、減、乘、除、浮點數怎麼表示與計算。
Chapter 4 開始換成 processor(處理器)：CPU 要怎麼真的執行指令？

這章的核心問題不是「某一條指令語法是什麼」，而是：

CPU 裡面要有哪些硬體元件、這些元件要怎麼連起來、控制訊號要怎麼決定，才能讓 MIPS 指令真的被執行？

所以 Chapter 4 會把指令變成硬體設計問題。

### 2. 處理器設計的五個主要步驟

講義 PDF viewer page 3 給出五個步驟：

| 步驟                  | 意義                         |
| ------------------- | -------------------------- |
| ① 分析指令系統，得出對數據通路的需求 | 先看指令需要做什麼                  |
| ② 為數據通路選擇合適的元件      | 決定需要哪些硬體，例如 ALU、暫存器、記憶體    |
| ③ 連接元件建立數據通路        | 把硬體接起來，讓資料能流動              |
| ④ 分析每條指令的實現，以確定控制訊號 | 每條指令需要哪些 mux 選擇、寫入、讀記憶體等控制 |
| ⑤ 集成控制訊號，形成完整控制邏輯   | 把控制訊號整理成完整 controller      |

本輪 PDF viewer page 1 ~ 12 主要處理前兩步：

第一步：指令到底需要 CPU 做哪些事？
第二步：為了滿足這些需求，需要哪些元件？

### 3. 本段講義選用的 MIPS 指令

PDF viewer page 4 列出這一段要支援的指令。這不是完整 MIPS，而是設計處理器時先選一組代表性指令來建 datapath(數據通路)。

| 指令類型              | 指令                  | 功能直覺                         |
| ----------------- | ------------------- | ---------------------------- |
| R-type arithmetic | `addu rd, rs, rt`   | `rd = rs + rt`               |
| R-type arithmetic | `subu rd, rs, rt`   | `rd = rs - rt`               |
| Immediate logic   | `ori rt, rs, imm16` | `rt = rs OR zero_ext(imm16)` |
| Load              | `lw rt, imm16(rs)`  | 從記憶體讀一個 word 到 `rt`          |
| Store             | `sw rt, imm16(rs)`  | 把 `rt` 的資料寫到記憶體              |
| Branch            | `beq rs, rt, imm16` | 如果 `rs == rt`，就改變 PC         |

這些指令剛好涵蓋幾種 CPU 必須會做的事：

* 從 instruction memory(指令記憶體)取指令。
* 從 register file(暫存器堆)讀兩個暫存器。
* 用 ALU 做加法、減法、OR、比較相等。
* 對 16-bit immediate(立即數)做 zero extension(零擴展)或 sign extension(符號擴展)。
* 讀寫 data memory(資料記憶體)。
* 更新 PC(program counter，程式計數器)。

### 4. 從指令格式推導第一批硬體需求

PDF viewer page 5 先看 instruction bit fields(指令位元欄位)。

R-type 指令格式：

`{op, rs, rt, rd, shamt, funct}`

I-type 指令格式：

`{op, rs, rt, Imm16}`

這馬上推出兩個需求：

| 需求                           | 為什麼                            |
| ---------------------------- | ------------------------------ |
| 需要 PC(program counter，程式計數器) | CPU 要知道下一條指令在哪裡                |
| 需要 instruction memory(指令記憶體) | CPU 要用 PC 當地址去取出指令 bit pattern |

最短理解：

CPU 執行任何指令以前，都要先知道「去哪裡拿指令」，所以一定需要 PC 和 instruction memory。

### 5. 從運算指令推導 ALU 與 register file

PDF viewer page 6 看 `addu`、`subu`、`ori`。

例如：

`ADDU R[rd] ← R[rs] + R[rt]; PC ← PC + 4`

這行其實已經告訴你很多硬體需求：

| 指令語意          | 推出硬體需求                               |
| ------------- | ------------------------------------ |
| `R[rs]`       | 需要讀 register file 的 `rs`             |
| `R[rt]`       | 需要讀 register file 的 `rt`             |
| `R[rd] ← ...` | 需要把結果寫回 register file                |
| `+`、`-`、`OR`  | 需要 ALU                               |
| `imm16`       | 需要 immediate extension unit(立即數擴展元件) |
| `PC ← PC + 4` | 需要能讓 PC 加 4                          |

所以 register file 必須至少支援：

* 同時讀兩個暫存器：`rs` 和 `rt`。
* 寫回一個暫存器：可能是 `rd` 或 `rt`。

這就是 PDF viewer page 9 說的「兩讀一寫」register file。

### 6. 從 load/store 推導 data memory 與 sign extension

PDF viewer page 7 看 `lw` 和 `sw`。

`LOAD R[rt] ← MEM[R[rs] + sign_ext(Imm16)]; PC ← PC + 4`

這行可以拆成：

| 指令語意                      | 推出硬體需求                                 |
| ------------------------- | -------------------------------------- |
| `R[rs] + sign_ext(Imm16)` | ALU 要能算 memory address(記憶體位址)          |
| `sign_ext(Imm16)`         | 需要 sign extension(符號擴展)                |
| `MEM[...]`                | 需要 data memory(資料記憶體)                  |
| `R[rt] ← MEM[...]`        | load 要把 memory output 寫回 register file |

`STORE MEM[R[rs] + sign_ext(Imm16)] ← R[rt]`

則多了一個重點：

store 不寫 register file，而是寫 data memory。

所以之後控制訊號會需要分清楚：

* 這條指令要不要寫 register？
* 這條指令要不要寫 memory？
* 寫回 register 的資料是 ALU 結果，還是 memory 讀出的資料？

### 7. 從 beq 推導比較器與 PC 選擇

PDF viewer page 7 的 branch 指令是：

`BEQ if (R[rs] == R[rt]) then PC ← PC + 4 + (sign_ext(Imm16)||00) else PC ← PC + 4`

這裡有三個硬體需求：

| 需求                               | 原因                            |
| -------------------------------- | ----------------------------- |
| 比較 `R[rs]` 和 `R[rt]` 是否相等        | `beq` 要判斷 branch 是否成立         |
| 計算 branch target address(分支目標位址) | 成立時 PC 不是單純 `PC+4`            |
| PC 需要能在兩個來源中選一個                  | 不成立選 `PC+4`，成立選 branch target |

這會導向後面很重要的 multiplexer(mux，多工器)概念：當資料來源有多種可能時，需要 mux 由控制訊號決定選哪一路。

### 8. 本輪整理：目前已推出哪些元件？

PDF viewer page 8 ~ 11 把需求整理成元件。

| 元件                       | 功能                                                                |
| ------------------------ | ----------------------------------------------------------------- |
| ALU                      | 做加、減、OR、比較相等                                                      |
| Immediate extension unit | 把 16-bit immediate 擴展成 32-bit，可能是 zero extension 或 sign extension |
| PC                       | 存目前指令位址，並支援 `PC+4` 或 branch target                                |
| Register file            | 32 個 32-bit 暫存器，支援兩讀一寫                                            |
| Instruction memory       | 用 PC 當地址讀出指令                                                      |
| Data memory              | load/store 用，支援讀寫資料                                               |

其中 PDF viewer page 10 特別說 register file：

* 有 32 個 32-bit 暫存器。
* `busA`、`busB` 是兩個 32-bit 輸出。
* `busW` 是一個 32-bit 輸入。
* `Ra`、`Rb` 選擇要讀哪兩個暫存器。
* `Rw` 選擇要寫哪個暫存器。
* `WriteEnable == 1` 且 clock 上升沿到來時，才會寫入。
* 讀操作不受時脈控制。

PDF viewer page 11 則說 memory：

* `Address` 指定位置。
* `Data In` 是要寫入的資料。
* `Data Out` 是讀出的資料。
* `Write Enable` 有效且 clock 上升沿到來時，才會寫入。
* 讀操作不受時脈控制。

### 9. 最短記法

這段的核心不是背元件名字，而是建立一個推導方式：

先看指令語意，再問「為了完成這句語意，硬體要能做什麼？」

例如：

`R[rd] ← R[rs] + R[rt]`

推出：

讀 `rs`、讀 `rt`、ALU 加法、寫 `rd`。

`R[rt] ← MEM[R[rs] + sign_ext(Imm16)]`

推出：

讀 `rs`、sign extension、ALU 算地址、data memory 讀資料、寫 `rt`。

`if R[rs] == R[rt] then PC ← branch target`

推出：

讀 `rs`、讀 `rt`、比較相等、計算 branch target、選擇下一個 PC。

你之後看到 datapath 圖時，不要先背線路；要先問：這條線是在滿足哪一條指令需求？







## ⭐數據通路的建立：所有指令共同需求 — 這個概念在解決什麼問題？

講義位置：PDF viewer page 13 ~ PDF viewer page 20／輔助：Chapter 4 — The Processor — 13 ~ 20

### 1. 這一段在解決什麼問題？

前面我們已經知道：MIPS 指令會要求 CPU 具備很多元件，例如 `PC`、`Instruction Memory`、`Register File`、`ALU`、`Extender`、`Data Memory`。但知道「需要哪些元件」還不夠，CPU 真正要能執行指令，還要把這些元件接起來，讓資料可以照指令需求流動。

所以 `Datapath(數據通路)` 的核心問題是：

**一條指令進來之後，資料要從哪裡來、經過哪些元件、最後到哪裡去？**

講義在 PDF viewer page 14 ~ 15 給的基本原則是：根據指令需求，連接元件，建立數據通路。需求又分成兩類：所有指令的共同需求，以及不同指令的不同需求。

### 2. 所有指令的共同需求 1：Fetch(取指令)

不管是 `addu`、`ori`、`lw`、`sw` 還是 `beq`，CPU 第一件事都一定是：**把目前要執行的指令抓出來。**

這件事需要兩個核心元件：

| 元件                           | 功能                                  |
| ---------------------------- | ----------------------------------- |
| `PC(Program Counter, 程式計數器)` | 存放目前指令的位址                           |
| `Instruction Memory(指令記憶體)`  | 根據 PC 給的位址，輸出該位址中的 instruction word |

所以流程是：

`PC` 內的值是一個指令位址 → 用這個位址去讀 `Instruction Memory` → 得到 32-bit 的 instruction word。

這裡要特別修正一個常見說法：`PC` 不只是「找下一個指令」。更精準地說，`PC` 先提供**目前要取出的指令位址**，然後在取指令後被更新成下一個 PC。講義在 PDF viewer page 16 ~ 17 就是用這個順序建立共同需求。

### 3. 所有指令的共同需求 2：更新 PC

取完指令後，CPU 不能停在原地。它必須決定下一個 `PC` 是什麼。

在這份講義目前的範圍，下一個 PC 有兩種基本情況：

| 情況   | 下一個 PC                       |
| ---- | ---------------------------- |
| 循序執行 | `PC ← PC + 4`                |
| 發生分支 | `PC ← branch target address` |

為什麼是 `PC+4`？因為 MIPS 一條指令是 32-bit，也就是 4 bytes。若目前指令在位址 `PC`，下一條循序指令就在 `PC+4`。

所以 CPU 需要一個 `Adder(加法器)` 幫 PC 加 4。這就是 PDF viewer page 18 開始畫出 adder 的原因。

### 4. IFU(Instruction Fetch Unit) 是把取指令與 PC 更新包起來

PDF viewer page 19 把這一塊整理成 `Instruction Fetch Unit, IFU`。它大致包含：

| IFU 內部元件             | 負責的事                                   |
| -------------------- | -------------------------------------- |
| `PC`                 | 存目前指令位址                                |
| `Instruction Memory` | 用 PC 讀出 instruction word               |
| `Adder`              | 算出 `PC+4`                              |
| `MUX(多工器)`           | 在 `PC+4` 和 branch target address 之間選一個 |
| `nPC_sel`            | 控制 MUX 要選哪個 next PC                    |

你可以把 IFU 想成 CPU 的「取指令與決定下一站」模組。

每條指令都要經過 IFU，因為每條指令都必須被抓出來，也都必須讓 CPU 知道下一個要去哪裡。差別只是：大多數普通指令走 `PC+4`，branch 類指令可能走 branch target。

### 5. 最短記法與常見錯法

最短記法：

**所有指令共同需求 = 取指令 + 更新 PC。**
取指令需要 `PC → Instruction Memory → Instruction Word`。
更新 PC 需要在 `PC+4` 與 `branch target` 之間選擇。

常見錯法：

第一，說「PC 是找下一個指令」不夠精準。PC 先是目前指令的 address，更新後才變成下一個指令的 address。

第二，把 `Register File`、`ALU`、`Data Memory` 都說成「所有指令共同需求」會太粗。它們是很多指令會用，但不是所有指令都一定用。真正所有指令都一定需要的是 `Fetch` 和 `PC update`。

第三，branch target 不是單純等於 immediate。後面講 `beq` 細節時會正式算，但現在先記：branch target 會跟 `PC+4` 和 sign-extended immediate 有關。







## ⭐加法和減法指令的 Datapath — R-type 指令怎麼用 RegFile 和 ALU 完成運算？

講義位置：PDF viewer page 20 ~ 21

### 1. 這一頁在解決什麼問題？

前面 p16~19 講的是「所有指令共同需要什麼」：都要取指令、都要更新 PC。

現在 p20~21 開始問另一個問題：

**不同指令本身要做的事情不同，那 Datapath(資料通路) 要怎麼接，才能讓這些指令真的完成？**

本頁先處理最基本的 R-type arithmetic instruction(算術 R 型指令)：

`addu rd, rs, rt`
`subu rd, rs, rt`

它們共同的語意是：

`R[rd] = R[rs] op R[rt]`

其中 `op` 可能是加法，也可能是減法。

### 2. `rs`、`rt`、`rd` 各自扮演什麼角色？

對 `addu rd, rs, rt` 或 `subu rd, rs, rt` 來說：

| 欄位   | 角色       | 接到哪裡                      |
| ---- | -------- | ------------------------- |
| `rs` | 第一個來源暫存器 | RegFile 的 `Ra`，輸出到 `busA` |
| `rt` | 第二個來源暫存器 | RegFile 的 `Rb`，輸出到 `busB` |
| `rd` | 目的暫存器    | RegFile 的 `Rw`，最後寫回結果     |

所以資料流是：

| 步驟 | 發生的事                                                    |
| -- | ------------------------------------------------------- |
| 1  | instruction encoding(指令編碼) 裡的 `rs`、`rt`、`rd` 被拆出來       |
| 2  | `rs` 接到 `Ra`，RegFile 把 `R[rs]` 放到 `busA`                |
| 3  | `rt` 接到 `Rb`，RegFile 把 `R[rt]` 放到 `busB`                |
| 4  | `busA`、`busB` 進入 ALU                                    |
| 5  | ALU 根據 `ALUCtr` 做加法或減法                                  |
| 6  | ALU result(結果) 經由 `busW` 回到 RegFile                     |
| 7  | 若 `RegWr = 1`，在 clock rising edge(時脈上升沿) 寫入 `rd` 指定的暫存器 |

關鍵句：
**R-type add/sub 是「讀 rs、讀 rt、算 ALU、寫 rd」。**

### 3. 為什麼需要 `ALUCtr` 和 `RegWr`？

講義特別用紅色標出兩個 control signals(控制訊號)：`ALUCtr` 和 `RegWr`。

`ALUCtr` 控制 ALU 要做什麼：
對 `addu`，ALU 做 addition(加法)。
對 `subu`，ALU 做 subtraction(減法)。

`RegWr` 控制 RegFile 要不要寫回：
對 `addu` 和 `subu`，都需要把 ALU 結果寫進 `rd`，所以 `RegWr = 1`。
如果 `RegWr = 0`，ALU 可能算出結果，但結果不會被寫回 RegFile，這條加法／減法指令就沒有真正更新暫存器。

這就是 control signal(控制訊號) 的核心作用：
**Datapath 提供路，control signal 決定這條路現在怎麼用。**

### 4. 用一個例子追一次

假設指令是：

`addu $t0, $t1, $t2`

意思是：

`R[$t0] = R[$t1] + R[$t2]`

Datapath 走法如下：

| 欄位       | 值     | 動作                        |
| -------- | ----- | ------------------------- |
| `rs`     | `$t1` | 接到 `Ra`，讀出 `$t1` 到 `busA` |
| `rt`     | `$t2` | 接到 `Rb`，讀出 `$t2` 到 `busB` |
| `rd`     | `$t0` | 接到 `Rw`，準備寫回 `$t0`        |
| `ALUCtr` | add   | ALU 做加法                   |
| `RegWr`  | 1     | 允許寫回 RegFile              |

如果 `$t1 = 7`，`$t2 = 5`，ALU 輸出 `12`。
下一個時脈上升沿，如果 `RegWr = 1`，RegFile 會把 `12` 寫入 `$t0`。



### 5. 常見錯法

最常見錯法是把 `rt` 當成目的暫存器。

這在 `lw`、`ori` 這些 I-type instruction(立即數型指令) 裡常常會發生，但在 R-type add/sub 裡不是這樣。

對 `addu rd, rs, rt`、`subu rd, rs, rt`：

| 指令類型           | 目的暫存器 |
| -------------- | ----- |
| R-type add/sub | `rd`  |
| `ori`、`lw`     | `rt`  |

所以本頁 p21 的 add/sub Datapath 裡，RegFile 的 write address(寫入位址) 應該接 `rd`，也就是 `rd → Rw`。


