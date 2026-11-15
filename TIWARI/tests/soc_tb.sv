`timescale 1ns/1ps
module soc_tb;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;tri [15:0]gpio;
 assign gpio[15:8]=8'h5a;
 wire tx;wire[1:0]pwm;wire led,halted,fault;
 tiwari_soc #(.CLOCK_HZ(1000000)) dut(clk,reset,gpio,1'b1,tx,pwm,led,halted,fault);
 task tick;begin @(posedge clk);#1;end endtask
 integer i,count0,count1;
 initial begin
  // Install a test program before releasing reset.
  #1;
  dut.rom[0]=16'h10ff;dut.rom[1]=16'he002;
  dut.rom[2]=16'hd001;dut.rom[3]=16'he000;
  dut.rom[4]=16'h1000;dut.rom[5]=16'he022;
  dut.rom[6]=16'h1040;dut.rom[7]=16'he020;
  dut.rom[8]=16'h10c0;dut.rom[9]=16'he021;
  dut.rom[10]=16'h1001;dut.rom[11]=16'he040;dut.rom[12]=1;
  repeat(3)tick;reset=0;
  for(i=0;i<40;i=i+1)tick;
  if(!halted||fault||gpio[7:0]!==8'h5a||!led)$fatal(1,"SoC GPIO and LED");
  count0=0;count1=0;
  for(i=0;i<256;i=i+1)begin tick;if(pwm[0])count0=count0+1;if(pwm[1])count1=count1+1;end
  if(count0!=64||count1!=192)$fatal(1,"PWM duty %0d %0d",count0,count1);
  repeat(2000)tick;
  if(dut.millis<2)$fatal(1,"timer");
  reset=1;tick;
  if(dut.gpio_dir!==0||pwm!==0||led||dut.millis!==0)$fatal(1,"peripheral reset");
  $display("PASS SOC: GPIO direction/input/output, LED, autonomous PWM and timer, reset");$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
