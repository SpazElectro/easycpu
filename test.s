MOV R0, 0x50 ; x
MOV R1, 0x50 ; y
MOV R2, 0x50 ; w
MOV R3, 0x50 ; h
MOV R4, 0x1  ; color
JMP M        ; go to loop

M:
RECT R0, R1, R2, R3, R4 ; draw rectangle

; randomize position
RND R0
RNDMAP R0, 0x0, 0x100
RND R1
RNDMAP R1, 0x0, 0x100

; randomize color
RND R4
RNDMAP R4, 0x0, 0xF

RENDER ; swap buffers

; infinitely loop
JMP M

