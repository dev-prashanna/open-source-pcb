`timescale 1ns/1ps
module uart_tb;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,start=0,ack=0;reg[7:0]data=0;
 wire tx,busy,ready,overrun,frame_error;wire[7:0]received;
 tiwari_uart #(.CLOCK_HZ(1000000),.BAUD(100000)) dut(clk,reset,tx,start,ack,data,tx,busy,ready,overrun,frame_error,received);
 task tick;begin @(posedge clk);#1;end endtask
 task send(input[7:0]v);begin data=v;start=1;tick;start=0;while(busy)tick;repeat(5)tick;end endtask
 integer i;
 initial begin
  repeat(3)tick;reset=0;
  for(i=0;i<256;i=i+1)begin
   send(i);if(!ready||received!==i||frame_error||overrun)$fatal(1,"loopback %0d",i);
   ack=1;tick;ack=0;tick;if(ready)$fatal(1,"RX ack");
  end
  send(8'h12);send(8'h34);
  if(!overrun||received!==8'h12)$fatal(1,"overrun retains first byte");
  $display("PASS UART: all 256 byte values, acknowledgement, overrun");$finish;
 end
 initial begin #1000000;$fatal(1,"timeout");end
endmodule
