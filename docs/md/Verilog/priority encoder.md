# Priority Encoder

## 一句話先懂

Priority encoder 的重點不是只有「把多個輸入編成編號」，而是：  
當多個 bit 同時為 `1` 時，你到底要保留哪一個優先順序最高的 bit。

## 核心規則

- 先定義清楚 priority 方向：`MSB -> LSB` 還是 `LSB -> MSB`。
- 如果輸出只有 `out`，全 0 時常會和「bit0 命中」混淆。
- 實務上常加 `valid`，把「有命中」和「全 0」分開。
- `if / else if` 與 `casez` 都很常用。
- `casez` 遇到重疊 pattern 時，分支順序就會有 priority 意義。

## 常用模板或例子

### LSB 優先

```verilog
always @(*) begin
    out   = 2'd0;
    valid = 1'b1;

    casez (in)
        4'b???1: out = 2'd0;
        4'b??10: out = 2'd1;
        4'b?100: out = 2'd2;
        4'b1000: out = 2'd3;
        default: begin
            out   = 2'd0;
            valid = 1'b0;
        end
    endcase
end
```

- 第一個匹配到的 pattern 就代表最高 priority。
- `???1` 先出現，所以 bit0 優先。

### MSB 優先

```verilog title="使用?"
always @(*) begin
    out = 2'b00;

    casez (in)
        4'b1???: out = 2'd3;
        4'b01??: out = 2'd2;
        4'b001?: out = 2'd1;
        4'b0001: out = 2'd0;
        default: out = 2'd0;
    endcase
end
```

```verilog title="使用z"
always @(*) begin
    out = 2'b00;

    casez (in)
        4'b1zzz: out = 2'd3;
        4'b01zz: out = 2'd2;
        4'b001z: out = 2'd1;
        4'b0001: out = 2'd0;
        default: out = 2'd0;
    endcase
end
```
用 z 和 ? 是相同意思。

### `if / else if` 版本

```verilog
always @(*) begin
    out   = 2'd0;
    valid = 1'b0;

    if (in[3]) begin
        out   = 2'd3;
        valid = 1'b1;
    end
    else if (in[2]) begin
        out   = 2'd2;
        valid = 1'b1;
    end
    else if (in[1]) begin
        out   = 2'd1;
        valid = 1'b1;
    end
    else if (in[0]) begin
        out   = 2'd0;
        valid = 1'b1;
    end
end
```

## 常見地雷

- 沒寫清楚到底是 LSB 優先還是 MSB 優先。
- 只有 `out` 沒有 `valid`，導致全 0 與 bit0 命中都看起來像 `0`。
- `casez` 分支順序寫反，priority 就跟著反。
- 組合邏輯沒先給預設值，結果推到 latch。

## 相關主題

- [選擇結構](選擇結構.md)
- [always、initial 與事件控制](always、initial 與事件控制.md)
