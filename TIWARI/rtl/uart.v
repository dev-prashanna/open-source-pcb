// SPDX-License-Identifier: MIT
module tiwari_uart #(parameter CLOCK_HZ=36000000, BAUD=115200)(
 input wire clk, reset, rx, tx_start, rx_ack,
 input wire [7:0] tx_data,
 output wire tx,
 output reg tx_busy, rx_ready, rx_overrun, rx_frame_error,
 output reg [7:0] rx_data
);
 localparam DIV=(CLOCK_HZ+BAUD/2)/BAUD;
 reg [15:0] tx_count, rx_count;
 reg [9:0] tx_shift;
 reg [3:0] tx_bits;
 (* async_reg="true" *) reg rx_meta=1, rx_sync=1;
 reg [1:0] rx_state;
 reg [2:0] rx_bit;
 reg [7:0] rx_shift;
 assign tx=tx_busy ? tx_shift[0] : 1'b1;
 always @(posedge clk) begin
  rx_meta<=rx; rx_sync<=rx_meta;
  if(reset) begin
   tx_busy<=0; tx_count<=0; tx_bits<=0; tx_shift<=10'h3ff;
   rx_count<=0; rx_state<=0; rx_bit<=0; rx_shift<=0;
   rx_ready<=0; rx_data<=0; rx_overrun<=0; rx_frame_error<=0;
  end else begin
   if(rx_ack) begin rx_ready<=0; rx_overrun<=0; rx_frame_error<=0; end
   if(tx_start && !tx_busy) begin
    tx_shift<={1'b1,tx_data,1'b0}; tx_busy<=1; tx_count<=DIV-1; tx_bits<=10;
   end else if(tx_busy) begin
    if(tx_count!=0) tx_count<=tx_count-1'b1;
    else begin
     tx_count<=DIV-1; tx_shift<={1'b1,tx_shift[9:1]}; tx_bits<=tx_bits-1'b1;
     if(tx_bits==1) tx_busy<=0;
    end
   end
   case(rx_state)
    0: if(!rx_sync) begin rx_count<=DIV/2-1; rx_state<=1; end
    1: if(rx_count!=0) rx_count<=rx_count-1'b1;
       else if(!rx_sync) begin rx_count<=DIV-1; rx_bit<=0; rx_state<=2; end
       else rx_state<=0;
    2: if(rx_count!=0) rx_count<=rx_count-1'b1;
       else begin
        rx_shift[rx_bit]<=rx_sync; rx_count<=DIV-1;
        if(rx_bit==7) rx_state<=3; else rx_bit<=rx_bit+1'b1;
       end
    3: if(rx_count!=0) rx_count<=rx_count-1'b1;
       else begin
        if(!rx_sync) rx_frame_error<=1;
        else if(rx_ready && !rx_ack) rx_overrun<=1;
        else begin rx_data<=rx_shift; rx_ready<=1; end
        rx_state<=0;
       end
   endcase
  end
 end
endmodule
