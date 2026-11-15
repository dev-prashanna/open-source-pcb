; Independent hardware PWM continues while the CPU is halted.
       LDI 140
       OUT 0x22
       LDI 64
       OUT 0x20
       LDI 192
       OUT 0x21
       HLT
