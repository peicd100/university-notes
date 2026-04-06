# 1000Hz to 1Hz counter


題目：

https://hdlbits.01xz.net/wiki/Exams/ece241_2014_q7b


![alt text](<images/1000Hz to 1Hz counter.png>)

## 題解

他是要做一個 1000 Hz 轉為 1 Hz 的 counter ，所以每 1000 次 clk 之後要給一次 OneHertz 信號。

BCD 計數器的用途是來執行 0~9 循環。

```v
module top_module (
    input clk,
    input reset,
    output OneHertz,
    output [2:0] c_enable
); //
    
    reg [3:0] q0,q1,q2;                            // 記錄個位、十位、百位數。
    
    assign c_enable[0] = 1;                        // 個位數永遠允許。
    assign c_enable[1] = (q0==9);                  // 當個位數 = 9 時，十位數在下一個 clk 加一。
    assign c_enable[2] = (q1==9)&&(q0==9);         // 99 時百位加一
    assign OneHertz = (q0==9)&&(q1==9)&&(q2==9);   // 999 時，OneHertz 為 1。

    bcdcount counter0 (clk, reset, c_enable[0],q0); // 當 clk 來的時候 q0 會 +1
    bcdcount counter1 (clk, reset, c_enable[1],q1); // 當 clk 來的時候 q1 會 +1
    bcdcount counter2 (clk, reset, c_enable[2],q2); // 當 clk 來的時候 q2 會 +1

endmodule
```

這三顆 BCD counter 串起來，本質上是在數：
```
000, 001, 002, ..., 998, 999, 000, 001, ...
```

所以是 1000 Hz (1000 個數字)，第 999 時輸出 1。