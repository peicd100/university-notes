## code


```v
module full_adder(
    input a, b,
    input cin,
    output cout,
    output sum
);
    assign sum = a ^ b ^ cin;
    assign cout = (a & b) | (a & cin) | (b & cin) ;
    
endmodule
```

## 裡面的 sum 和 cout 為何這樣寫 ?

sum 何時會是 1 呢，就是 a+b+cin 相加結果是奇數時 sum 會是 1，所以看 a、b、cin 裡面有奇數個 1 可以用 xor 來看。

cout 何時會進位，當 a、b、cin 裡面有 2 個以上的 1 時，就會進位，所以兩配對，如果有兩個都是 1 那 cout 就是 1。