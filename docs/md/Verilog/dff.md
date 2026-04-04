# dff

## 題目

https://hdlbits.01xz.net/wiki/Exams/ece241_2014_q4



![alt text](images/dff.png)


## 解題


題目說初始化為 0 ，這我們不用管，我們只要管如何畫出電路。


```v
module top_module (
    input  clk,
    input  x,
    output z
);

    reg q1, q2, q3;

    always @(posedge clk) begin
        q1 <= x ^ q1;
        q2 <= x & ~q2;
        q3 <= x | ~q3;
    end

    assign z = ~(q1 | q2 | q3);

endmodule
```


