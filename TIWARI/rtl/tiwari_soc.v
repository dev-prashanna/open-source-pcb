// SPDX-License-Identifier: MIT
module tiwari_soc #(parameter PROGRAM="build/blink.hex", CLOCK_HZ=36000000)(
 input wire clk, reset,
 inout wire [15:0] gpio,
 input wire uart_rx,
 output wire uart_tx,
 output wire [1:0] pwm,
 output wire status_led,
 output wire halted, fault
);
 reg [15:0] rom[0:4095];
 reg [7:0] ram[0:255];
 reg [15:0] instr;
 reg [7:0] ram_q;
 wire [11:0] pc,program_addr;
 wire [7:0] da,dw,pa,pw,pra;
 reg [7:0] pr;
 wire dwe,pwe;
 integer k;
 initial begin
  for(k=0;k<4096;k=k+1) rom[k]=16'h0001;
  $readmemh(PROGRAM,rom);
 end
 always @(posedge clk) begin
  instr<=rom[program_addr];
  ram_q<=ram[da];
  if(dwe) ram[da]<=dw;
 end
 wire [7:0] a,b;
 wire z,c;
 tiwari8 cpu(.clk(clk),.reset(reset),.enable(1'b1),.pc(pc),.instruction(instr),
  .data_addr(da),.data_wdata(dw),.data_rdata(ram_q),.data_we(dwe),
  .port_addr(pa),.port_wdata(pw),.port_rdata(pr),.port_we(pwe),
  .a(a),.b(b),.z(z),.c(c),.halted(halted),.fault(fault),.port_read_addr(pra),.program_addr(program_addr));
 reg [15:0] gpio_out,gpio_dir;
 (* async_reg="true" *) reg [15:0] gpio_meta,gpio_sync;
 genvar bitno;
 generate for(bitno=0;bitno<16;bitno=bitno+1) begin: pins
  assign gpio[bitno]=gpio_dir[bitno] ? gpio_out[bitno] : 1'bz;
 end endgenerate
 reg [7:0] duty0,duty1,pwm_div,pwm_prescale,pwm_count;
 assign pwm[0]=pwm_count<duty0;
 assign pwm[1]=pwm_count<duty1;
 reg led;
 assign status_led=led;
 localparam MS_DIV=CLOCK_HZ/1000;
 reg [15:0] ms_prescale;
 reg [15:0] millis,millis_latch;
 wire [7:0] rx_data;
 wire tx_busy,rx_ready,rx_overrun,rx_frame_error;
 reg rx_ack=0,tx_start=0;
 reg [7:0] tx_data=0;
 always @(posedge clk) begin
  if(reset) begin rx_ack<=0;tx_start<=0;tx_data<=0;end
  else begin rx_ack<=pwe && pa==8'h12;tx_start<=pwe && pa==8'h10;tx_data<=pw;end
 end
 tiwari_uart #(.CLOCK_HZ(CLOCK_HZ)) uart(.clk(clk),.reset(reset),.rx(uart_rx),
  .tx_start(tx_start),.tx_data(tx_data),.rx_ack(rx_ack),.tx(uart_tx),
  .tx_busy(tx_busy),.rx_ready(rx_ready),.rx_overrun(rx_overrun),
  .rx_frame_error(rx_frame_error),.rx_data(rx_data));
 always @* begin
  case(pra)
   8'h00: pr=gpio_sync[7:0];
   8'h01: pr=gpio_sync[15:8];
   8'h02: pr=gpio_dir[7:0];
   8'h03: pr=gpio_dir[15:8];
   8'h04: pr=gpio_out[7:0];
   8'h05: pr=gpio_out[15:8];
   8'h10: pr=rx_data;
   8'h11: pr={4'b0,rx_frame_error,rx_overrun,rx_ready,tx_busy};
   8'h20: pr=duty0;
   8'h21: pr=duty1;
   8'h22: pr=pwm_div;
   8'h30: pr=millis_latch[7:0];
   8'h31: pr=millis_latch[15:8];
   8'h40: pr={7'b0,led};
   8'h7f: pr=8'h81;
   default: pr=0;
  endcase
 end
 always @(posedge clk) begin
  gpio_meta<=gpio; gpio_sync<=gpio_meta;
  if(reset) begin
   gpio_out<=0; gpio_dir<=0; duty0<=0; duty1<=0; pwm_div<=140;
   pwm_prescale<=0; pwm_count<=0; ms_prescale<=0; millis<=0;
   millis_latch<=0; led<=0;
  end else begin
   if(ms_prescale==MS_DIV-1) begin ms_prescale<=0; millis<=millis+1'b1; end
   else ms_prescale<=ms_prescale+1'b1;
   if(pwm_prescale>=pwm_div) begin pwm_prescale<=0; pwm_count<=pwm_count+1'b1; end
   else pwm_prescale<=pwm_prescale+1'b1;
   if(pwe) case(pa)
    8'h00: gpio_out[7:0]<=pw;
    8'h01: gpio_out[15:8]<=pw;
    8'h02: gpio_dir[7:0]<=pw;
    8'h03: gpio_dir[15:8]<=pw;
    8'h20: duty0<=pw;
    8'h21: duty1<=pw;
    8'h22: pwm_div<=pw;
    8'h30: millis_latch<=millis;
    8'h40: led<=pw[0];
   endcase
  end
 end
endmodule
