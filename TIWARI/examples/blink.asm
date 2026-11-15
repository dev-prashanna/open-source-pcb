; TIWARI heartbeat: blink built-in LED every 250 ms using hardware timer.
.equ LED 0x40
.equ TIMER_LOW 0x30
.equ TIMER_HIGH 0x31
start: LDI 1
       OUT LED
       OUT TIMER_LOW
       IN TIMER_LOW
       STA 0
on_wait: OUT TIMER_LOW
       IN TIMER_LOW
       MOVBA
       LDA 0
       SUB
       LDB 250
       ADD
       JNZ on_wait
; This short demo waits 250 modulo-256 milliseconds (start - now + 250 = 0).
       LDI 0
       OUT LED
       OUT TIMER_LOW
       IN TIMER_LOW
       STA 0
off_wait: OUT TIMER_LOW
       IN TIMER_LOW
       MOVBA
       LDA 0
       SUB
       LDB 250
       ADD
       JNZ off_wait
       JMP start
