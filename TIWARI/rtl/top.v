// SPDX-License-Identifier: MIT
module top(input wire clk_12m, reset_n, uart_rx,
 inout wire [15:0] gpio,
 output wire uart_tx, output wire [1:0] pwm,
 output wire user_led, fault_led);
 wire clk,locked;
 SB_PLL40_PAD #(.FEEDBACK_PATH("SIMPLE"),.DIVR(4'd0),.DIVF(7'd47),
  .DIVQ(3'd4),.FILTER_RANGE(3'b001)) pll(
  .PACKAGEPIN(clk_12m),.PLLOUTCORE(clk),.LOCK(locked),.RESETB(1'b1),.BYPASS(1'b0));
 (* async_reg="true" *) reg [1:0] reset_sync=0;
 wire async_reset_n=reset_n && locked;
 always @(posedge clk or negedge async_reset_n)
  if(!async_reset_n) reset_sync<=0; else reset_sync<={reset_sync[0],1'b1};
 wire halted,fault;
 tiwari_soc soc(.clk(clk),.reset(!reset_sync[1]),.gpio(gpio),.uart_rx(uart_rx),
  .uart_tx(uart_tx),.pwm(pwm),.status_led(user_led),.halted(halted),.fault(fault));
 assign fault_led=fault;
endmodule
