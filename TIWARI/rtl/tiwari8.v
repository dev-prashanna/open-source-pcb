// SPDX-License-Identifier: MIT
// TIWARI-8: 8-bit data, 12-bit word PC, synchronous program/data memories.
module tiwari8 (
 input wire clk, reset, enable,
 output reg [11:0] pc,
 input wire [15:0] instruction,
 output wire [7:0] data_addr, data_wdata,
 input wire [7:0] data_rdata,
 output wire data_we,
 output wire [7:0] port_addr, port_wdata,
 input wire [7:0] port_rdata,
 output wire port_we,
 output reg [7:0] a, b,
 output reg z, c, halted, fault,
 output wire [7:0] port_read_addr,
 output wire [11:0] program_addr
);
 localparam FETCH=0, EXEC=1, LOAD=2, INPUT=3, ALU=4;
 reg [2:0] state;
 reg [7:0] alu_result;
 reg [7:0] load_addr;
 reg [15:0] ir;
 wire [3:0] op=ir[15:12];
 wire [7:0] imm=ir[7:0];
 wire valid=(op>=10 && op<=12) || op==15 || ir[11:8]==0;
 wire active=enable && !reset && !halted && state==EXEC;
 wire [11:0] next_pc=(op==10 || (op==11 && z) || (op==12 && c) || (op==15 && !z)) ? ir[11:0] : pc+12'd1;
 assign program_addr=reset ? 12'd0 : state==EXEC ? next_pc : pc;
 wire [8:0] sum={1'b0,a}+{1'b0,b};
 assign data_addr=state==LOAD ? load_addr : imm;
 assign data_wdata=a;
 assign data_we=active && ir[15:8]==8'h40;
 assign port_addr=imm;
 assign port_read_addr=load_addr;
 assign port_wdata=a;
 assign port_we=active && ir[15:8]==8'he0;
 reg [7:0] result;
 reg alu_write,carry_write,next_c;
 always @* begin
  result=a;alu_write=0;carry_write=0;next_c=c;
  case(op)
   0: case(imm)
    2:begin result={a[6:0],1'b0};alu_write=1;carry_write=1;next_c=a[7];end
    3:begin result={1'b0,a[7:1]};alu_write=1;carry_write=1;next_c=a[0];end
    4:begin result=b;alu_write=1;end
    6:begin result=~a;alu_write=1;end
   endcase
   1:begin result=imm;alu_write=1;end
   5:begin result=sum[7:0];alu_write=1;carry_write=1;next_c=sum[8];end
   6:begin result=a-b;alu_write=1;carry_write=1;next_c=a>=b;end
   7:begin result=a&b;alu_write=1;end
   8:begin result=a|b;alu_write=1;end
   9:begin result=a^b;alu_write=1;end
  endcase
 end
 wire [7:0] writeback=state==LOAD ? data_rdata : state==INPUT ? port_rdata : state==ALU ? alu_result : imm;
 wire wb_enable=state==LOAD || state==INPUT || state==ALU || (state==EXEC && valid && op==1);
 always @(posedge clk) begin
  if(reset) begin
   pc<=0;a<=0;b<=0;z<=1;c<=0;halted<=0;fault<=0;state<=FETCH;load_addr<=0;ir<=0;alu_result<=0;
  end else if(enable && !halted) begin
   if(state==EXEC && valid && alu_write && op!=1)begin alu_result<=result;state<=ALU;end
   if(wb_enable)begin a<=writeback;z<=writeback==0;end
   if(state==EXEC && valid && carry_write)c<=next_c;
   case(state)
    FETCH:begin ir<=instruction;state<=EXEC;end
    EXEC:begin
     state<=(valid && alu_write && op!=1)?ALU:FETCH;pc<=pc+12'd1;
     if(!valid)begin fault<=1;halted<=1;end
     else case(op)
      0:case(imm)
       0,2,3,4,6:begin end
       1:halted<=1;
       5:b<=a;
       default:begin fault<=1;halted<=1;end
      endcase
      2:b<=imm;
      3:begin state<=LOAD;load_addr<=imm;end
      10:pc<=ir[11:0];
      11:if(z)pc<=ir[11:0];
      12:if(c)pc<=ir[11:0];
      13:begin state<=INPUT;load_addr<=imm;end
      15:if(!z)pc<=ir[11:0];
     endcase
    end
    LOAD,INPUT,ALU:state<=FETCH;
   endcase
  end
 end
endmodule
