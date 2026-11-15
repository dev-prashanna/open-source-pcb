; Read eight digital inputs D8..D15 and mirror them to outputs D0..D7.
       LDI 255
       OUT 2
loop:  IN 1
       OUT 0
       JMP loop
