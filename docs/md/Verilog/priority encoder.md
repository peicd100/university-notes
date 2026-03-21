## Priority Encoder

### 一句話

- 多個輸入同時為 `1` 時，只輸出「優先順序最高」那一個 bit 的編號。
- priority 必須先定義清楚，可以是 `MSB -> LSB`，也可以是 `LSB -> MSB`。
- 這頁以下先用 `LSB 優先` 當範例，也就是從低位元往高位元找第一個 `1`。

### 速查

- `8'b10010000` -> `3'd4`
- `8'b00001001` -> `3'd0`
- `8'b00000000` -> 若只有 `out`，通常先約定輸出 `0`
- 實務上常加 `valid`，避免「全 0」和「bit0 = 1」都得到 `0`

### 最常見寫法

- `if / else if`：最直觀，從上到下就是優先順序。
- `casez`：適合用 `?` 表示 don't care。
- `default`：組合邏輯通常要補預設值，避免漏分支。
- `casex`：不建議在可綜合 RTL 亂用，因為 `X` 也會被當成 wildcard。

### 4-bit LSB 優先

```verilog
always @(*) begin
    out = 2'd0;
    valid = 1'b1;

    casez (in)
        4'b???1: out = 2'd0;
        4'b??10: out = 2'd1;
        4'b?100: out = 2'd2;
        4'b1000: out = 2'd3;
        default: begin
            out = 2'd0;
            valid = 1'b0;
        end
    endcase
end
```

- `???1` 先匹配到，所以 bit0 的優先權最高。

### 如果你要改成 MSB 優先

```verilog
always @(*) begin
    out = 2'd0;

    casez (in)
        4'b1???: out = 2'd3;
        4'b01??: out = 2'd2;
        4'b001?: out = 2'd1;
        4'b0001: out = 2'd0;
        default: out = 2'd0;
    endcase
end
```

- `casez` 會執行第一個匹配到的分支，所以 pattern 順序就是 priority。

### 常見地雷

- 沒寫清楚到底是 `LSB 優先` 還是 `MSB 優先`。
- 只有 `out` 沒有 `valid`，就分不出「全 0」和「bit0 命中」。
- `casez` 的分支順序寫反，整個 priority 方向就會反過來。
- 組合邏輯沒有先給預設值，容易推到 latch。

### 你可以直接這樣記

- priority encoder = 多個 `1` 同時出現時，只保留一個順位最高的輸出
- `???1 -> 0` 代表 `LSB 優先`
- `1??? -> 3` 代表 `MSB 優先`

