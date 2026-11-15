`timescale 1ns/1ps
module blink_tb;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;tri[15:0]gpio;wire tx,led,halted,fault;wire[1:0]pwm;
 tiwari_soc #(.CLOCK_HZ(1000000)) dut(clk,reset,gpio,1'b1,tx,pwm,led,halted,fault);
 integer cycle=0,edges=0,last=0;
 reg previous=0;
 initial begin
  repeat(3)begin @(posedge clk);#1;end
  reset=0;
  while(edges<3 && cycle<600000)begin
   @(posedge clk);#1;cycle=cycle+1;
   if(led!=previous)begin
    if(edges>0 && (cycle-last<249000 || cycle-last>251000))$fatal(1,"blink interval %0d",cycle-last);
    edges=edges+1;last=cycle;previous=led;
   end
   if(fault||halted)$fatal(1,"blink unexpectedly halted");
  end
  if(edges!=3)$fatal(1,"blink timed out");
  $display("PASS BLINK: actual assembled program toggles LED every 250ms");$finish;
 end
endmodule
