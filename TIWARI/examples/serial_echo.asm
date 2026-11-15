; Echo bytes at 115200 baud, 8N1, using the second USB serial interface.
.equ DATA 0x10
.equ STATUS 0x11
.equ ACK 0x12
wait_rx: IN STATUS
         LDB 2
         AND
         JZ wait_rx
         IN DATA
         STA 0
         LDI 1
         OUT ACK
wait_tx: IN STATUS
         LDB 1
         AND
         JNZ wait_tx
         LDA 0
         OUT DATA
         JMP wait_rx
