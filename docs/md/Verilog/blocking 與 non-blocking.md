# blocking 與 non-blocking

## 一句話先懂

`=` 是 blocking assignment，會立刻更新；`<=` 是 non-blocking assignment，會先排程，稍後一起生效。  
最常見的穩定規則是：組合邏輯常用 `=`，時序邏輯常用 `<=`。

## 核心規則

- `=`：目前這一行先完成，再往下執行下一行。
- `<=`：先記錄右值，等到目前時間步較後面再一起更新左值。
- `always @(*)` 內通常用 `=`
- `always @(posedge clk)` 內通常用 `<=`
- 除非你非常確定語意，否則不要在同一個 `always` block 混用 `=` 和 `<=`

## 常用模板或例子

### 組合邏輯常用 `=`

```verilog
always @(*) begin
    y = a;

    if (sel)
        y = b;
end
```

- 這裡重點是「描述現在這一拍的組合結果」。

### 時序邏輯常用 `<=`

```verilog
always @(posedge clk) begin
    q1 <= d;
    q2 <= q1;
    q3 <= q2;
end
```

- 這種寫法會讓資料一拍一拍往後傳。

### blocking 在 clocked block 的效果

```verilog
always @(posedge clk) begin
    q1 = d;
    q2 = q1;
    q3 = q2;
end
```

- 這和上面的 `<=` 語意不同。
- 因為 `=` 會立刻更新，所以同一個 block 後面的敘述可能看到的是新值。

## 實務判斷

- 想描述 combinational logic：先想 `always @(*)` + `=`
- 想描述 flip-flop / pipeline：先想 `always @(posedge clk)` + `<=`
- 真的要混用時，要先清楚知道哪個訊號是暫時變數、哪個訊號是暫存狀態

## 常見地雷

- 在 clocked block 裡大量用 `=`，結果模擬與心中想像的 pipeline 不一致。
- 在 combinational block 裡用 `<=`，讓閱讀與除錯都變難。
- 同一個 block 混用 `=`、`<=`，卻沒先定義好語意。
- 把 blocking / non-blocking 和 `wire` / `reg` 的概念混在一起。

## 相關主題

- [always、initial 與事件控制](always、initial 與事件控制.md)
- [選擇結構](選擇結構.md)
