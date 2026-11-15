`timescale 1ns/1ps
module cpu_tb;
 reg clk=0; always #5 clk=~clk;
 reg reset=1,enable=1;
 wire [11:0] pc,program_addr;
 reg [15:0] rom[0:4095]; reg [15:0] ins;
 reg [7:0] ram[0:255];reg [7:0] dq;
 wire [7:0] da,dw,pa,pw,a,b,pra;
 wire dwe,pwe,z,c,halted,fault;
 integer stores=0,outs=0;
 tiwari8 dut(clk,reset,enable,pc,ins,da,dw,dq,dwe,pa,pw,8'ha7,pwe,a,b,z,c,halted,fault,pra,program_addr);
 always @(posedge clk) begin
  ins<=rom[program_addr];dq<=ram[da];
  if(dwe) begin ram[da]<=dw;stores<=stores+1;end
  if(pwe) outs<=outs+1;
 end
 task tick;begin @(posedge clk);#1;end endtask
 task boot;begin reset=1;enable=1;tick;reset=0;end endtask
 task step;begin tick;while(dut.state!=0)tick;end endtask
 integer i,j,op,expected,saved;
 initial begin
  for(i=0;i<4096;i=i+1)rom[i]=1;
  for(i=0;i<256;i=i+1)ram[i]=0;
  rom[0]=16'h1000;rom[1]=16'h2000;
  for(op=5;op<=6;op=op+1)begin
   rom[2]=op<<12;
   for(i=0;i<256;i=i+1)for(j=0;j<256;j=j+1)begin
    rom[0]=16'h1000|i;rom[1]=16'h2000|j;boot;repeat(3)step;
    expected=op==5?i+j:i-j;
    if(a!==(expected&255)||z!==((expected&255)==0)||c!==(op==5?expected>255:i>=j))
     $fatal(1,"ALU op %0d a %0d b %0d",op,i,j);
   end
  end
  // Data memory, load latency, I/O, taken and untaken branches.
  rom[0]=16'hd010;rom[1]=16'h40f0;rom[2]=16'h1000;rom[3]=16'h30f0;
  rom[4]=16'h20a7;rom[5]=16'h9000;rom[6]=16'hb008;rom[7]=1;
  rom[8]=16'hf00a;rom[9]=16'h1009;rom[10]=16'he040;rom[11]=16'ha00d;
  rom[12]=1;rom[13]=1;
  boot;step;step;
  if(ram[240]!==8'ha7)$fatal(1,"STA");
  step;step;
  if(a!==8'ha7||z)$fatal(1,"LDA");
  step;step;step;
  if(pc!==8||!z)$fatal(1,"JZ");
  step;if(pc!==9)$fatal(1,"JNZ untaken");
  step;step;if(outs!=1||a!==9)$fatal(1,"OUT");
  step;if(pc!==13)$fatal(1,"JMP");
  step;if(!halted||fault)$fatal(1,"HLT");
  saved=pc;repeat(3)tick;if(pc!=saved||dwe||pwe)$fatal(1,"halt stable");
  // Every logic operation and the six system operations.
  for(op=7;op<=9;op=op+1)begin
   rom[0]=16'h10aa;rom[1]=16'h2055;rom[2]=op<<12;boot;repeat(3)step;
   expected=op==7?0:255;
   if(a!==expected||z!==(expected==0))$fatal(1,"logic");
  end
  rom[0]=16'h1081;rom[1]=2;rom[2]=3;rom[3]=5;rom[4]=16'h1000;rom[5]=4;rom[6]=6;
  boot;step;step;if(a!==2||!c)$fatal(1,"SHL");
  step;if(a!==1||c)$fatal(1,"SHR");
  repeat(3)step;if(a!==1||b!==1)$fatal(1,"MOV");
  step;if(a!==254||z)$fatal(1,"NOT");
  rom[0]=16'h1000;rom[1]=16'hc003;rom[2]=16'hb004;rom[4]=0;
  boot;step;step;if(pc!==2)$fatal(1,"JC untaken");
  step;if(pc!==4)$fatal(1,"JZ taken");step;if(pc!==5)$fatal(1,"NOP");
  // 12-bit PC wrap.
  rom[0]=16'hafff;rom[4095]=16'h1042;boot;step;step;
  if(pc!==0||a!==66)$fatal(1,"PC wrap");
  // Paused EXEC and asserted reset cannot write.
  rom[0]=16'h4000;boot;tick;enable=0;saved=stores;
  repeat(4)tick;if(dwe||stores!=saved||pc!==0)$fatal(1,"pause");
  reset=1;enable=1;tick;if(stores!=saved||pc!==0||a!==0||b!==0||!z||c)$fatal(1,"reset");
  rom[0]=16'h4100;boot;step;
  if(!halted||!fault||stores!=saved)$fatal(1,"fault store gating");
  rom[0]=7;boot;step;if(!fault||!halted)$fatal(1,"unknown SYS");
  // LDA can be paused without losing its address.
  ram[240]=8'h6b;rom[0]=16'h30f0;rom[1]=16'h3001;
  boot;tick;tick;enable=0;repeat(4)tick;enable=1;tick;
  if(a!==8'h6b)$fatal(1,"paused LDA");
  $display("PASS CPU: 131072 ALU cases, logic, flags, branches, RAM, I/O, reset, pause, faults, wrap");$finish;
 end
 initial begin #20000000;$fatal(1,"timeout");end
endmodule
