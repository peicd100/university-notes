# Testbench 用數學式驗證


## 電路

### half_adder.v
```verilog
module half_adder(
    input A,B,
    output S,C
);

    assign S = A ^ B;
    assign C = A & B;

endmodule
```

### full_adder.v
```verilog
module full_adder (
    input A,B,Cin,
    output S,Cout
);
    wire s1,c1,c2;

    half_adder h1 (
        .A(A),
        .B(B),
        .S(s1),
        .C(c1)
    );

    half_adder h2 (
        .A(s1),
        .B(Cin),
        .S(S),
        .C(c2)
    );

    assign Cout = c1 | c2;

endmodule
```

### ripple_carry_adder.v
```verilog
module ripple_carry_adder (
    input [3:0] A,B,
    input Cin,
    output [3:0]S,
    output Cout
);
    wire c1,c2,c3;

    full_adder f1 (
        .A   (A[0]),
        .B   (B[0]),
        .Cin (Cin),
        .S   (S[0]),
        .Cout(c1)
    );

    full_adder f2 (
        .A   (A[1]),
        .B   (B[1]),
        .Cin (c1),
        .S   (S[1]),
        .Cout(c2)
    );

    full_adder f3 (
        .A   (A[2]),
        .B   (B[2]),
        .Cin (c2),
        .S   (S[2]),
        .Cout(c3)
    );

    full_adder f4 (
        .A   (A[3]),
        .B   (B[3]),
        .Cin (c3),
        .S   (S[3]),
        .Cout(Cout)
    );

endmodule
```

### multiplier.v
```verilog
module multiplier (
    input [2:0] A,
    input [3:0] B,
    output [6:0] S
);

    wire [3:0] a0b = {4{A[0]}} & {B};
    wire [3:0] a1b = {4{A[1]}} & {B};
    wire [3:0] a2b = {4{A[2]}} & {B};
    wire [3:0] w;


    assign S[0] = a0b[0];

    ripple_carry_adder r1 (
        .A  ({1'b0,a0b[3:1]}),
        .B  (a1b),
        .Cin(1'b0),
        .S  ({w[2:0],S[1]}),
        .Cout(w[3])
    );

    ripple_carry_adder r2 (
        .A  (w),
        .B  (a2b),
        .Cin(1'b0),
        .S  (S[5:2]),
        .Cout(S[6])
    );

endmodule
```

### tb_multiplier.v
```verilog
module tb_multiplier();
	
	reg [2:0] A;
	reg [3:0] B;
	wire [6:0] S;
	
	multiplier m1(A,B,S);
	
	integer i,j;
	initial begin
	
		for(i=0;i<8;i=i+1) begin
			for(j=0;j<16;j=j+1)begin
            
				A = i;
				B = j;
                
				#10;
				
				if(A*B!==S)begin
					$display("False!!!!");
					$finish;
				end
			
			end
			
			
		end
		
		$display("True!!!!");
		$finish;
	
	end
	
	initial begin
		$monitor($time," | A: %d | B: %d | S: %d ",A,B,S);
	end
endmodule
```


## 講解

```v
if(A*B!==S)begin
    $display("False!!!!");
    $finish;
end
```

要放在 `#10` 後面，不然電路都還沒有穩定就開始比較 `A * B !== S` 了。
利用 `$finish` 直接中斷程式，像是 `return 0;` 一樣。
