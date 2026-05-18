
![alt text](<images/Finite State Machine(有限狀態機).png>)



!!! danger "重點"
    
    注意下列的 18-26 ，要注意的只有這邊。
    
    只有這邊是跟著 clk 變動，其他都是直接改，反正 clk 來才會跟著 18-26 更新。
    
    然後同一個 reg 只能在同一個 always 中更新，所以 20-22 的 reset 也要寫在

```v  linenums="1" hl_lines="18-26" 
`timescale 1ns / 1ps

module FSM_image(
    input clk,
    input reset,
    input x,
    output reg z,
    output [1:0] state
);

    parameter S00 = 2'b00, S01 = 2'b01, S10 = 2'b10, S11 = 2'b11;

    reg [1:0] present_state = S00;
    reg [1:0] next_state;

    assign state = present_state;

    // state register
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            present_state <= S00;
        end
        else begin
            present_state <= next_state;
        end
    end

    // next state logic and output logic
    always @(*) begin
        next_state = present_state;
        z = 1'b0;

        case (present_state)
            S00: begin
                if (x == 1'b0) begin
                    next_state = S00;
                    z = 1'b0;
                end
                else begin
                    next_state = S01;
                    z = 1'b0;
                end
            end

            S01: begin
                if (x == 1'b0) begin
                    next_state = S00;
                    z = 1'b1;
                end
                else begin
                    next_state = S11;
                    z = 1'b0;
                end
            end

            S10: begin
                if (x == 1'b0) begin
                    next_state = S00;
                    z = 1'b1;
                end
                else begin
                    next_state = S10;
                    z = 1'b0;
                end
            end

            S11: begin
                if (x == 1'b0) begin
                    next_state = S00;
                    z = 1'b1;
                end
                else begin
                    next_state = S10;
                    z = 1'b0;
                end
            end

            default: begin
                next_state = S00;
                z = 1'b0;
            end
        endcase
    end

endmodule
```