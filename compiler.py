import re

instruction_sizes = {
    "MOV": 1 + 1 + 2,     # 3 bytes (1 for opcode, 1 for register, 2 for immediate)
    "ADD": 1 + 2,         # 3 bytes (1 for opcode, 2 for registers)
    "SUB": 1 + 2,         # 3 bytes (1 for opcode, 2 for registers)
    "LOAD": 1 + 1 + 2,    # 4 bytes (1 for opcode, 1 for register, 2 for address)
    "STR": 1 + 2 + 1,     # 4 bytes (1 for opcode, 2 for address, 1 for register)
    "JMP": 1 + 2,         # 3 bytes (1 for opcode, 2 for address)
    "CALL": 1 + 2,        # 3 bytes (1 for opcode, 2 for address)
    "RET": 1,             # 1 byte (1 for opcode)
    "PUSH": 1 + 1,        # 2 bytes (1 for opcode, 1 for register)
    "POP": 1 + 1,         # 2 bytes (1 for opcode, 1 for register)
    "HLT": 1,             # 1 byte (1 for opcode)

    "JEQ": 1 + 1 + 2,     # 3 bytes (1 for opcode, 1 for register, 2 for address)
    "JNE": 1 + 1 + 2,     # 3 bytes (1 for opcode, 1 for register, 2 for address)
    "JG": 1 + 1 + 2,      # 3 bytes (1 for opcode, 1 for register, 2 for address)
    "JL": 1 + 1 + 2,      # 3 bytes (1 for opcode, 1 for register, 2 for address)
    "DRW": 1 + 1 + 1 + 1, # 4 bytes (1 for opcode, 1 for xPosition, 1 for yPosition, 1 for color)
    "CLR": 1, # opcode
    "RENDER": 1, # opcode

    "DIV": 1 + 1 + 1, # 4 bytes (1 for opcode, 2 for registers)
    "MUL": 1 + 1 + 1, # 4 bytes (1 for opcode, 2 for registers)
    "RECT": 1 + 1 + 1 + 1 + 1 + 1, # 6 bytes (1 for opcode, 1 for xPosition, 1 for yPosition, 1 for width, 1 for height, 1 for color)

    "RND": 1 + 1,  # 2 bytes (1 for opcode, 1 for register)
    "SEED": 1 + 4, # 5 bytes (1 for opcode, 4 for seed)
    "RNDMAP": 1 + 1 + 2 + 2 # 4 bytes (1 for opcode, 1 for register, 2 for min, max immediates)
}

class Compiler:
    def __init__(self):
        self.registers = {
            "R0": 0, "R1": 1, "R2": 2, "R3": 3,
            "R4": 4, "R5": 5, "R6": 6, "R7": 7
        }
        self.labels = {}
        self.instructions = []
        self.bytecode = []

    def compile(self, code):
        lines = code.strip().split("\n")
        position = 0  # Initialize position at 0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            if ":" in line:
                label = line.split(":")[0].strip()
                self.labels[label] = position
                line = line.split(":")[1].strip()
                # print(f"{label=} estimation is 0x{position:02X}")
            
            if line:
                instruction = line.split(" ")[0]
                if instruction in instruction_sizes:
                    position += instruction_sizes[instruction]
                    self.instructions.append(line)
                    # print(f"Added {instruction_sizes[instruction]} from '{line}'")
                else:
                    print(f"idk this instruction {instruction=}")
        
        for line in self.instructions:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            
            tokens = re.split(r"\s+", line)
            instruction = tokens[0].upper()
            args = [arg.strip(",") for arg in tokens[1:]]
            
            if instruction == "MOV":
                self.bytecode.append(0x01)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.extend(self.encode_immediate(self.parse_immediate(args[1])))
            elif instruction == "ADD":
                self.bytecode.append(0x02)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.append(self.get_register_code(args[1]))
            elif instruction == "SUB":
                self.bytecode.append(0x03)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.append(self.get_register_code(args[1]))
            elif instruction == "LOAD":
                self.bytecode.append(0x04)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.extend(self.encode_address(self.parse_address(args[1])))
            elif instruction == "STR":
                self.bytecode.append(0x05)
                self.bytecode.extend(self.encode_address(self.parse_address(args[0])))
                self.bytecode.append(self.get_register_code(args[1]))
            elif instruction == "JMP":
                self.bytecode.append(0x06)
                self.bytecode.extend(self.encode_address(self.parse_label(args[0])))
            elif instruction == "CALL":
                self.bytecode.append(0x07)
                self.bytecode.extend(self.encode_address(self.parse_label(args[0])))
            elif instruction == "RET":
                self.bytecode.append(0x08)
            elif instruction == "PUSH":
                self.bytecode.append(0x09)
                self.bytecode.append(self.get_register_code(args[0]))
            elif instruction == "POP":
                self.bytecode.append(0x0A)
                self.bytecode.append(self.get_register_code(args[0]))
            elif instruction == "JZ":
                self.bytecode.append(0x0B)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.extend(self.encode_address(self.parse_address(args[1])))
            elif instruction == "JNZ":
                self.bytecode.append(0x0C)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.extend(self.encode_address(self.parse_address(args[1])))
            elif instruction == "JG":
                self.bytecode.append(0x0D)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.extend(self.encode_address(self.parse_address(args[1])))
            elif instruction == "JL":
                self.bytecode.append(0x0E)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.extend(self.encode_address(self.parse_address(args[1])))
            elif instruction == "JEQ":
                self.bytecode.append(0x0F)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.append(self.get_register_code(args[1]))
                self.bytecode.extend(self.encode_address(self.parse_label(args[2])))
            elif instruction == "JNE":
                self.bytecode.append(0x10)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.append(self.get_register_code(args[1]))
                self.bytecode.extend(self.encode_address(self.parse_label(args[2])))
            elif instruction == "DRW":
                self.bytecode.append(0x11)
                self.bytecode.append(self.get_register_code(args[0])) # x
                self.bytecode.append(self.get_register_code(args[1])) # y
                self.bytecode.append(self.get_register_code(args[2])) # color
            elif instruction == "CLR":
                self.bytecode.append(0x12)
            elif instruction == "RENDER":
                self.bytecode.append(0x13)
            elif instruction == "DIV":
                self.bytecode.append(0x14)
                self.bytecode.append(self.get_register_code(args[0])) # a
                self.bytecode.append(self.get_register_code(args[1])) # b
            elif instruction == "MUL":
                self.bytecode.append(0x15)
                self.bytecode.append(self.get_register_code(args[0])) # a
                self.bytecode.append(self.get_register_code(args[1])) # b
            elif instruction == "RECT":
                self.bytecode.append(0x16)
                self.bytecode.append(self.get_register_code(args[0])) # x
                self.bytecode.append(self.get_register_code(args[1])) # y
                self.bytecode.append(self.get_register_code(args[2])) # w
                self.bytecode.append(self.get_register_code(args[3])) # h
                self.bytecode.append(self.get_register_code(args[4])) # color
            elif instruction == "RND":
                self.bytecode.append(0x17)
                self.bytecode.append(self.get_register_code(args[0]))
            elif instruction == "SEED":
                self.bytecode.append(0x18)
                self.bytecode.append(self.encode_int(self.parse_int(args[0])))
            elif instruction == "RNDMAP":
                self.bytecode.append(0x19)
                self.bytecode.append(self.get_register_code(args[0]))
                self.bytecode.extend(self.encode_immediate(self.parse_immediate(args[1])))
                self.bytecode.extend(self.encode_immediate(self.parse_immediate(args[2])))
            elif instruction == "HLT":
                self.bytecode.append(0xFF)
            else:
                raise ValueError(f"Unknown instruction: {instruction}")

        if len(self.bytecode) != position:
            print(f"[FATAL] Expected bytecode length to be {position} bytes but instead got {len(self.bytecode)} bytes!")
            print(self.bytecode)
        

        return bytearray(self.bytecode)

    def get_register_code(self, reg_name):
        reg_name = reg_name.strip(",")
        if reg_name in self.registers:
            return self.registers[reg_name]
        raise ValueError(f"Unknown register: {reg_name}")

    def parse_immediate(self, value):
        return int(value, 0)
    def parse_address(self, addr):
        return int(addr, 0)
    def parse_int(self, addr):
        return int(addr, 0)

    def encode_immediate(self, value):
        return [value & 0xFF, (value >> 8) & 0xFF]
    def encode_address(self, value):
        return [value & 0xFF, (value >> 8) & 0xFF]
    def encode_int(self, value):
        return [value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF]

    def parse_label(self, label):
        label = label.strip()
        if label in self.labels:
            return self.labels[label]  # Return the bytecode position as an integer
        else:
            raise ValueError(f"Unknown label: {label}")

# Example usage
assembly_code = open("test.s").read()

compiler = Compiler()
bytecode = compiler.compile(assembly_code)
open("test.rom", "wb").write(bytecode)
print(f"Wrote {len(bytecode)} bytes!")
