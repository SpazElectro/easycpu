MOV R0, 0x50 ; x
MOV R1, 0x50 ; y
MOV R2, 30 ; w
MOV R3, 30 ; h
MOV R4, 0x1  ; color

SEED 1

; randomize position
RND R0
RNDMAP R0, 0x0, 0x100
RND R1
RNDMAP R1, 0x0, 0x100

; randomize color
RND R4
RNDMAP R4, 0x0, 0xF

JMP M        ; go to loop

M:
RECT R0, R1, R2, R3, R4 ; draw rectangle

RENDER ; swap buffers

; infinitely loop
JMP M

