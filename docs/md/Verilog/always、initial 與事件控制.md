# always、initial 與事件控制

## 一句話先懂

`always` 是重複觸發的程序區塊，`initial` 是模擬開始時只跑一次的程序區塊；你在 `@(...)` 裡怎麼寫，決定它描述的是組合邏輯、時序邏輯，還是 testbench 行為。

## 核心規則

- `always @(*)` 常用來描述組合邏輯。
- `always @(posedge clk)` 常用來描述 flip-flop 等時序邏輯。
- `always @(posedge clk or negedge rst_n)` 常用來描述含非同步 reset 的時序邏輯。
- `initial` 主要用在模擬與 testbench；是否可綜合，要看工具與目標平台。
- `@*` 代表把 block 內被讀取到的訊號都放進 sensitivity list。
- 組合邏輯 block 內如果不是每條路徑都有賦值，就可能推到 latch。

## 常用模板或例子

### 組合邏輯

```verilog
always @(*) begin
    y = 1'b0;

    if (en)
        y = a & b;
end
```

- `always @(*)` 重點是「輸出只看現在輸入」。
- 先給 default assignment，是避免 latch 的穩定寫法。

### 時序邏輯

```verilog
always @(posedge clk) begin
    q <= d;
end
```

- 這種寫法是在上升沿取樣。
- 如果你要描述一般 D flip-flop，通常不會寫成 `@(clk)`。

### 非同步 reset

```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        q <= 1'b0;
    else
        q <= d;
end
```

### `initial`

```verilog
initial begin
    clk = 1'b0;
    rst_n = 1'b0;
    #10 rst_n = 1'b1;
end
```

- 最常見在 testbench 做初始化與刺激流程。

### `@*` 的意思

```verilog
always @(*) begin
    shut_off = cpu_overheated | shut_off;
end
```

- 語意上可理解成把 block 裡所有「被讀取的訊號」都放進 sensitivity list。
- 這能降低手寫 sensitivity list 漏訊號的風險。

## 組合 vs 時序，怎麼判斷

- `always @(*)`：組合邏輯
- `always @(posedge clk)` / `@(negedge clk)`：時序邏輯
- `initial`：模擬初始化或 testbench 流程

如果你的輸出必須記住上一拍狀態，那通常是時序邏輯。  
如果你的輸出只看現在輸入，那通常是組合邏輯。

## 常見地雷

- 在組合邏輯中漏掉 default assignment 或 `else`，結果推到 latch。
- 寫 flip-flop 時用 `@(clk)` 而不是 `@(posedge clk)` / `@(negedge clk)`。
- `always` 沒有事件控制或 delay，造成 zero-delay infinite loop。
- 把 `initial` 當成一般可綜合 RTL 主力。

## 相關主題

- [blocking 與 non-blocking](blocking 與 non-blocking.md)
- [選擇結構](選擇結構.md)
- [模擬控制與 System Tasks](system tasks.md)
