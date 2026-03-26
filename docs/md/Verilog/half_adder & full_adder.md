# half_adder 和 full_adder 組成



half_adder 和 full_adder 主要差異就是有沒有 cin


## half_adder
[圖片來源](https://www.build-electronic-circuits.com/half-adder/)
![alt text](<images/half_adder & full_adder-1.png>)


```v
module half_adder (
    input x,y,
    output cout,sum
);
    assign sum = x ^ y;
    assign cout = x & y;
endmodule
```


half_adder 的 sum 是看 x、y 中有奇數的 1，所以用 xor。
cout 則是如果有進位就是 1，何時有進位呢？就是 x==1 && y==1 時。


## full_adder

[圖片來源](https://www.youtube.com/watch?v=VokzmpUJAQw)
![alt text](<images/half_adder & full_adder-4.png>)


如果說 half_adder 本質上就是相加兩個數，得到 1-bit 總和和 1-bit 進位。

那 full_adder 就是再加上一個 cin。

也就是三個數字連加 x+y+cin ，得到進位和總合。

所以 full_adder 有三種寫法：
### 第一種：用 half_adder
```v
module full_adder (
    input x,y,cin,
    output cout,sum
);
    wire cout_1,cout_2,sum_1;
    
    half_adder g1 (
        .x   (x),
        .y   (y),
        .cout(cout_1),
        .sum (sum_1)
    );
    
    half_adder g2 (
        .x   (sum_1),
        .y   (cin),
        .cout(cout_2),
        .sum (sum)
    );
    
    or g3(cout,cout_1,cout_2);
    
endmodule
```
這種是直接像圖中那樣用 half_adder 先 x+y 再加上 cin。
最後如果 cout_1 或 cout_2 任何一個是 1 就代表有進位。基本上 cout 只會有一個是 1 ，因為 cout_i 是 1，代表 sum_i 是 0，另一個就不可能是 1。

### 第二種
```v 
module full_adder (
    input x,y,cin,
    output cout,sum
);
    assign sum = x ^ y ^ cin;
    assign cout = ((x^y)&cin)|(x&y);
endmodule
```

這是直接依照圖中的 gate 推出來的，很難記。


### 第三種
```v 
module full_adder (
    input x,y,cin,
    output cout,sum
);
    assign sum = x ^ y ^ cin;
    assign cout = (x&y)|(y|cin)|(cin&x);
endmodule
```
這個是用規律來思考的，最推薦寫。

sum 看 x、y、cin 中奇數個 1 ，所以用 xor。
cout 是只要 x、y、cin 任意兩個是 1 就是 1 。