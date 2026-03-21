從低位元到高位元，哪個位元先看到1，就輸出幾。

如果輸入是 8'b10010000，那麼輸出會是 3'd4

## 範例

輸出 in 的最低是 1 的位元 ，如果都是 0 就輸出 0 。

```v
always @(*) begin
    casez (in)
        4'b1???: out = 2'd3;
        4'b01??: out = 2'd2;
        4'b001?: out = 2'd1;
        4'b0001: out = 2'd0;
        default: out = 2'd0;
    endcase
end
```

