# VHDL


好，我先不照投影片順序講，而是改成**你這個已經會 Verilog 的人，最容易上手的 VHDL 學習順序**。目標很明確：**讓你能直接讀懂 Ch3 p.1~p.62 的程式**，也就是看懂 `process / variable / signal / if / loop / case / wait` 這些行為模型語法；但因為這些語法會用到第 2 章的一些基礎，所以我會把**必要的前置語法一起補上**。 

---

#### 1. 先抓住 VHDL 和 Verilog 最大的差別

你先只記一件事：

* **Verilog**：你很常在想
  `assign`、`always @(*)`、`always @(posedge clk)`
* **VHDL**：你要改成想
  **「architecture 外面是 concurrent，process 裡面是 sequential」**

```mermaid
flowchart TB
A[architecture 裡、process 外<br>Concurrent] --> B[像 Verilog 的 assign<br>或多個 always block 彼此並行]
B --> C[process(...) 裡面<br>Sequential]
C --> D[像 Verilog 的 always block 內部<br>一行一行執行]
D --> E[再加上 VHDL 特有差異<br>signal 與 variable 更新時機不同]
```

這就是整章的核心。 

---

#### 2. VHDL 程式骨架：`entity + architecture`

Verilog 你熟的是：

```verilog
module or_gate(input A, B, output C);
  assign C = A | B;
endmodule
```

VHDL 對應是：

```vhdl
entity OR_gate is
  port(
    A, B : in bit;
    C    : out bit
  );
end OR_gate;

architecture OR2_arch of OR_gate is
begin
  C <= A or B;
end OR2_arch;
```

你可以這樣對照：

* `module` ≈ `entity + architecture`
* `entity` = **外部介面**
* `architecture` = **內部實作**
* `port(...)` = I/O 宣告
* `begin ... end` 之間放真正的電路描述

這個骨架是讀所有 VHDL 的第一步。

---

#### 3. 型別先會這幾個就夠看懂 p.62 前大部分程式

##### 3.1 `bit` / `bit_vector`

```vhdl
signal A : bit;
signal X : bit_vector(3 downto 0);
```

對你來說可先類比成：

* `bit` ≈ 單一 0/1
* `bit_vector(3 downto 0)` ≈ Verilog 的 `[3:0]`

但 VHDL 寫法是**型別放右邊**，而且範圍用括號。

---

##### 3.2 `std_logic` / `std_logic_vector`

這是實務上比 `bit` 更常用的型別，要先引入套件：

```vhdl
library ieee;
use ieee.std_logic_1164.all;
```

`std_logic` 不只 `'0'`、`'1'`，還能表示 `U/X/Z...` 等狀態。你可以先把它理解成：

* `bit` = 比較單純的 2-state
* `std_logic` = 比較像 Verilog 的多狀態邏輯值

你目前最重要只要先認得：

* `'0'`：低
* `'1'`：高
* `'X'`：未知
* `'Z'`：高阻抗
* `'U'`：未初始化



---

##### 3.3 單引號和雙引號

這在 VHDL 很重要：

* `'1'`：**單一 bit / std_logic**
* `"1010"`：**vector**

例如：

```vhdl
clk = '1'
S   = "10"
```

這一點你看程式時一定要立刻分清楚。

---

##### 3.4 `downto` 和 `to`

```vhdl
signal a : bit_vector(7 downto 0);
signal b : bit_vector(0 to 7);
```

* `downto` 比較像你熟的 Verilog `[7:0]`
* `to` 是反方向編號

所以 VHDL 的重點不是只有位元數，**索引方向也算語意的一部分**。

---

#### 4. 你一定要先分清楚：`signal` 和 `variable`

這是 Verilog 轉 VHDL 最容易卡住的地方。

##### 4.1 `signal`

```vhdl
signal A : bit;
A <= B;
```

* `signal` 是 VHDL 最常見的硬體物件
* 賦值符號是 `<=`
* **不會立刻更新**
* 會先安排，然後在一個很小的模擬延遲後更新

這很像 Verilog `always` 裡面的 **nonblocking assignment `<=`** 的味道。

---

##### 4.2 `variable`

```vhdl
variable temp : bit;
temp := A and B;
```

* `variable` 多半宣告在 `process` 裡
* 賦值符號是 `:=`
* **立刻更新**

這很像 Verilog `always` block 裡的**區域變數 / blocking assignment `=`**。

---

##### 4.3 最實用的類比

這段 VHDL：

```vhdl
process(A,B,C,D)
  variable TEMP1, TEMP2 : bit;
begin
  TEMP1 := A and B;
  TEMP2 := C and D;
  TEMP1 := TEMP1 or TEMP2;
  Z <= not TEMP1;
end process;
```

你可以直接類比成 Verilog：

```verilog
always @(*) begin
  temp1 = A & B;
  temp2 = C & D;
  temp1 = temp1 | temp2;
  Z = ~temp1;
end
```

重點是：

* `TEMP1 := ...` 是**立即改**
* `Z <= ...` 是**排程後更新**

所以 **VHDL 裡面拿 intermediate result，通常用 variable，不要用 signal**。教材也特別強調這點。

---

#### 5. `process`：就是 VHDL 版的 `always`

基本型態：

```vhdl
process(A, B, C)
begin
  -- sequential statements
end process;
```

你可以先把它當成：

```verilog
always @(A or B or C) begin
  ...
end
```

或在組合邏輯語意上接近：

```verilog
always @(*) begin
  ...
end
```

但教材是用**明確 sensitivity list** 寫法。它的意思是：

* `A/B/C` 其中任何一個變化
* 就重新執行一次 process 內的程式
* 裡面是**照順序執行**
* 不同 process 彼此之間仍然是**並行**

這個觀念非常重要。

---

#### 6. concurrent 與 sequential 的差別，你一定要真的懂

這是 p.16~25 最核心的地方。

##### 6.1 在 `process` 內的 signal assignment

```vhdl
process(B)
begin
  A <= B;
  Z <= A;
end process;
```

這裡 `Z <= A` 看到的是**舊的 A**，不是剛剛那行更新後的新 A。

對你來說，它很像：

```verilog
always @(B) begin
  A <= B;
  Z <= A;   // 看到舊 A
end
```

---

##### 6.2 在 `process` 外的 concurrent assignment

```vhdl
A <= B;
Z <= A;
```

這像兩條獨立的 `assign`：

```verilog
assign A = B;
assign Z = A;
```

所以：

* `B` 變了，先影響 `A`
* `A` 再變，接著才影響 `Z`

因此教材才說 concurrent 版本的 `Z` 會比 `A` 再晚一個 Δ。

---

#### 7. `if`：最重要的控制語法

VHDL 寫法：

```vhdl
if 條件 then
  ...
elsif 條件 then
  ...
else
  ...
end if;
```

對照 Verilog：

```verilog
if (...) begin
  ...
end
else if (...) begin
  ...
end
else begin
  ...
end
```

注意兩個 VHDL 特徵：

* `then`
* 結尾是 `end if;`

---

##### 7.1 沒有 `else`，可能推導出記憶元件

這段：

```vhdl
if en = '1' then
  Qout <= Qin;
end if;
```

等價概念就是：

```verilog
always @(*) begin
  if (en)
    Qout = Qin;
end
```

因為 `en=0` 時你**沒指定 Qout**，所以它要「保持原值」，這就會導致 **latch**。教材用這點來做 latch 範例。

---

##### 7.2 檢查上升沿：`clk'EVENT and clk='1'`

這就是舊式 VHDL 的 rising edge 寫法：

```vhdl
if (clk'EVENT and clk = '1') then
  Qout <= Qin;
end if;
```

你直接把它看成：

```verilog
always @(posedge clk) begin
  Qout <= Qin;
end
```

就可以了。

`'EVENT` 是 VHDL attribute，表示該 signal 在這個模擬時刻有事件發生。 

---

##### 7.3 非同步 reset

```vhdl
process(Qin, clk, clr)
begin
  if clr = '1' then
    Qout <= '0';
  elsif (clk'EVENT and clk='1') then
    Qout <= Qin;
  end if;
end process;
```

對照 Verilog：

```verilog
always @(posedge clk or posedge clr) begin
  if (clr)
    Qout <= 1'b0;
  else
    Qout <= Qin;
end
```

因為 `clr` 不用等 clock edge 就能生效，所以是 **asynchronous reset**。

---

#### 8. `case`：多路選擇很好用

VHDL：

```vhdl
case S is
  when "00" => Y <= X(0);
  when "01" => Y <= X(1);
  when "10" => Y <= X(2);
  when others => Y <= X(3);
end case;
```

Verilog：

```verilog
case (S)
  2'b00: Y = X[0];
  2'b01: Y = X[1];
  2'b10: Y = X[2];
  default: Y = X[3];
endcase
```

重點只要記：

* `case S is`
* 每支分支用 `when ... =>`
* 預設分支常寫 `when others =>`

`others` 幾乎就等於 Verilog `default`。

---

#### 9. `for ... loop`：VHDL 的迴圈

```vhdl
for i in 2 downto 0 loop
  if d(i) = '1' then
    num_bits := num_bits + 1;
  end if;
end loop;
```

對照 Verilog：

```verilog
for (i=2; i>=0; i=i-1) begin
  if (d[i] == 1'b1)
    num_bits = num_bits + 1;
end
```

VHDL 還很常看到：

```vhdl
for i in d'RANGE loop
```

意思是：

* 不自己手寫範圍
* 直接用 `d` 這個向量本身的索引範圍

如果 `d` 是 `(2 downto 0)`，那 `d'RANGE` 就是 `2 downto 0`。
這很好用，也比較不容易寫錯。 

---

#### 10. `wait`：另一種寫時序 process 的方法

VHDL：

```vhdl
process
begin
  wait until (clk'EVENT and clk = '1');
  Qout <= Qin;
end process;
```

可直接類比成：

```verilog
always begin
  @(posedge clk);
  Qout <= Qin;
end
```

你可以把 `wait until ...` 想成「卡在這裡，等條件成立才往下跑」。

教材強調兩件事：

1. **沒有 sensitivity list 的 process，至少要有一個 wait**
2. **同一個 process 不能同時有 sensitivity list 又有 wait**

這是讀 code 時要立刻檢查的。

---

#### 11. 你看 p.62 前程式時，最常遇到的 3 個坑

##### 11.1 把 `signal <=` 當成立刻更新

這是錯的。

`signal <=` 在 process 內通常像 Verilog nonblocking，**不是馬上改值**。
如果你要在同一個 process 裡存中間結果，通常用 `variable :=`。

---

##### 11.2 忘記「process 外面全部是並行」

這也是常錯點。

```vhdl
agtb <= compare(2);
aeqb <= compare(1);
altb <= compare(0);
```

這三行不是一行做完才做下一行，
它們是**三個 concurrent statement**，同時存在。

---

##### 11.3 `if` 少了 `else`，不一定只是「少寫一點」

在硬體裡，這常常代表：

* 保留舊值
* 推導出 latch / flip-flop / memory behavior

所以 VHDL 裡的 `else` 不是可有可無。

---

#### 12. 最後給你一份 Verilog → VHDL 速查表

* `module` → `entity + architecture`
* `input/output` → `port(... : in/out ...)`
* `wire/reg` 的思維 → 先改成 `signal / variable`
* `assign Y = ...` → process 外的 `Y <= ...`
* `always @(*)` → `process(a,b,c,...)`
* `always @(posedge clk)` → `process(clk)` 搭配 `if clk'EVENT and clk='1' then`
* blocking `=` → `:=`（variable）
* nonblocking `<=` → `<=`（signal，語意最接近）
* `case/default` → `case/when others`
* `{a,b}` → `a & b`

---

#### 13. 你現在只要能讀懂這種程式，就表示 p.62 前大致打通了

```vhdl
architecture behavior of mux4_proc is
begin
  process(X,S)
  begin
    case S is
      when "00" => Y <= X(0);
      when "01" => Y <= X(1);
      when "10" => Y <= X(2);
      when others => Y <= X(3);
    end case;
  end process;
end behavior;
```

你的腦中應該自動翻成：

1. 這是一個 `always @(*)`
2. `S` 決定選哪個輸入
3. `case` 的 `others` 就是 `default`
4. `Y <= ...` 是 signal assignment
5. 這段在硬體上是 combinational mux

如果你可以這樣讀，那你已經不是「逐字看 VHDL」，而是在**直接看硬體**了。

---

#### 14. 小結：你現在最該先背住的是這 6 句

1. **entity 是外部介面，architecture 是內部實作。**
2. **process 外面是 concurrent，process 裡面是 sequential。**
3. **signal 用 `<=`，variable 用 `:=`。**
4. **variable 立即更新，signal 不是立即更新。**
5. **`clk'EVENT and clk='1'` 就是 `posedge clk`。**
6. **`if` 少 `else` 可能會生出 latch。**

如果你要，我下一則可以直接做一份
**「VHDL 對照 Verilog 的最小語法手冊」**，只保留你在這堂課前半最常看到的寫法。教材檔案句尾：[Ch2](sandbox:/mnt/data/Ch2.%20VHDL-Basic%20Elements%20and%20Dataflow.pdf)、[Ch3](sandbox:/mnt/data/Ch3.%20VHDL-Behavior%20and%20Structural.pdf)
