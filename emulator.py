import os
import time
import socket
import threading
import pickle

DISPLAY_WIDTH  = 256
DISPLAY_HEIGHT = 256

def lcg_random(seed: int, a=1664525, c=1013904223, m=2**32):
    """Linear Congruential Generator (LCG) function with seed setting."""
    state = seed
    def set_seed(new_seed):
        nonlocal state
        state = new_seed

    def nextv():
        nonlocal state
        state = (a * state + c) % m
        return state

    return nextv, set_seed

def map_to_range(lcg_value: int, min_val: int, max_val: int, m=2**32):
    """Map LCG value to a specified range [min_val, max_val]."""
    return min_val + (lcg_value / (m - 1)) * (max_val - min_val)

class CPU:
    def __init__(self, rom_filename: str, ips_limit: float = float("inf")) -> None:
        self.memory = bytearray(8192)
        self.display = bytearray(DISPLAY_WIDTH*DISPLAY_HEIGHT)

        # display test
        # for x in range(DISPLAY_WIDTH*DISPLAY_HEIGHT):
        #     self.display[x] = 1
        #     if x >= 32768:
        #         self.display[x] = 2
        
        self.display2 = bytearray(DISPLAY_WIDTH*DISPLAY_HEIGHT) # double buffer
        self.stack = []
        self.pc = 0x1000
        self.registers = {
            "R0": 0, "R1": 0, "R2": 0, "R3": 0,
            "R4": 0, "R5": 0, "R6": 0, "R7": 0,
        }
        self.instructions_executed = 0
        self.start_time = time.time()
        self.halted = False
        self.paused = False
        self.rom_size = 0
        self.stop_requested = False
        self.ips_limit = ips_limit

        self.load_rom(rom_filename)

        self.debug_server_thread = threading.Thread(target=self.debug_server)
        self.debug_server_thread.start()

        self.clear_display()

        self._step_random, self._set_seed = lcg_random(42)

    def load_rom(self, filename: str) -> None:
        with open(filename, "rb") as f:
            self.memory[0x1000:] = f.read()
        self.rom_size = os.path.getsize(filename)
        print(f"Loaded {self.rom_size} bytes for ROM")

    # Display
    def draw_pixel(self, x: int, y: int, color: int) -> None:
        if x < 0 or x >= DISPLAY_WIDTH or y < 0 or y >= DISPLAY_HEIGHT:
            return

        # index = y * DISPLAY_WIDTH + x
        index = x * DISPLAY_WIDTH + y
        self.display2[index] = min(color, 255)
    def draw_rectangle(self, x: int, y: int, width: int, height: int, color: int) -> None:
        for _x in range(x, x+width):
            for _y in range(y, y+height):
                self.draw_pixel(_x, _y, color)
    def clear_display(self):
        self.display2 = bytearray(DISPLAY_WIDTH*DISPLAY_HEIGHT)

    # Fetch
    def bytelist_to_int(self, bytelist: bytearray) -> int:
        return int.from_bytes(bytelist, byteorder="little")
    def fetch(self) -> int:
        self.pc += 1
        return self.memory[self.pc-1]
    def fetch_bytes(self, n) -> bytearray:
        if self.pc + n > len(self.memory):
            raise IndexError("Read beyond memory bounds")

        data = self.memory[self.pc:self.pc + n]
        self.pc += n

        return data
    def fetch_register(self) -> str:
        return f"R{self.fetch()}"
    def fetch_immediate(self) -> int:
        return self.bytelist_to_int(self.fetch_bytes(2))
    def fetch_addr(self) -> int:
        return self.bytelist_to_int(self.fetch_bytes(2))
    def fetch_int(self) -> int:
        return self.bytelist_to_int(self.fetch_bytes(4))

    # Registers
    def set_register(self, name: str, value: int) -> None:
        self.registers[name] = value
    def get_register(self, name: str) -> int:
        return self.registers[name]

    # Memory
    def get_memory(self, addr: int) -> int:
        if 0 <= addr < len(self.memory):
            return self.memory[addr]
        else:
            raise IndexError(f"Address {addr} is out of bounds. Valid range is 0 to {len(self.memory) - 1}.")
    def set_memory(self, addr: int, value: int | bytearray) -> None:
        if not (0 <= addr < len(self.memory)):
            raise IndexError(f"Address {addr} is out of bounds. Valid range is 0 to {len(self.memory) - 1}.")

        if isinstance(value, int):
            self.memory[addr] = value
        elif isinstance(value, (bytes, bytearray)):
            end_addr = addr + len(value)
            if end_addr > len(self.memory):
                raise IndexError(f"Write operation exceeds memory bounds. Valid range is 0 to {len(self.memory) - 1}.")
            self.memory[addr:end_addr] = value

    # Stack
    def push_stack(self, value: int):
        self.stack.append(value)
    def pop_stack(self) -> int:
        return self.stack.pop()
    def pop_stack_into_register(self, into_register: str):
        self.set_register(into_register, self.pop_stack())

    # Random
    def step_random(self) -> int:
        return self._step_random()
    def set_random(self, seed: int):
        self._set_seed(seed)

    # Debug commands
    def set_stack(self, index: int, value: int) -> None:
        if index < len(self.stack):
            self.stack[-(index + 1)] = value
        else:
            raise IndexError("Stack index out of range")
    def get_stack(self) -> list[int]:
        return self.stack
    def set_pc(self, value: int) -> None:
        self.pc = value
    def halt(self, message: str) -> None:
        self.halted = True
        self.traceback(message)
        self.stop()
    def traceback(self, message: str) -> None:
        print("TRACEBACK:")
        print(f"Program Counter (PC): 0x{self.pc:04X}")
        print("Registers:")
        for reg, value in self.registers.items():
            print(f"  {reg}: 0x{value:02X}")
        print("Stack:")
        for i, value in enumerate(reversed(self.stack)):
            print(f"  {i}: 0x{value:02X}")
        print("Memory (showing 16 bytes around PC):")
        start = max(0, self.pc - 8)
        end = min(len(self.memory), self.pc + 8)
        for addr in range(start, end):
            if addr % 16 == 0 and addr != start:
                print()
            print(f"  0x{addr:04X}: 0x{self.memory[addr]:02X}", end="\n")
        print()
        print(f"Message: {message}")

    def cycle(self) -> None:
        if self.halted or self.paused:
            return
        
        if self.pc-0x1000 >= self.rom_size:
            return self.halt(f"Program Counter has exceeded the ROM size {self.pc=} {self.rom_size=}")
        instruction = self.fetch()

        if instruction == 0x00: # NOP
            pass
        elif instruction == 0x01: # MOV R, IMM
            self.set_register(self.fetch_register(), self.fetch_immediate())
        elif instruction == 0x02: # ADD R1, R2
            R1 = self.fetch_register()
            self.set_register(R1, self.get_register(R1) + self.get_register(self.fetch_register()))
        elif instruction == 0x03: # SUB R1, R2
            R1 = self.fetch_register()
            self.set_register(R1, self.get_register(R1) - self.get_register(self.fetch_register()))
        elif instruction == 0x04: # LOAD R, ADDR
            self.set_register(self.fetch_register(), self.get_memory(self.fetch_addr()))
        elif instruction == 0x05: # STORE ADDR, R
            self.set_memory(self.fetch_addr(), self.get_register(self.fetch_register()))
        elif instruction == 0x06: # JMP ADDR
            self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x07: # CALL ADDR
            return_address = self.pc + 3
            self.push_stack(return_address)
            self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x08: # RET
            self.pc = self.pop_stack()
        elif instruction == 0x09: # PUSH R
            self.push_stack(self.get_register(self.fetch_register()))
        elif instruction == 0x0A: # POP R
            self.pop_stack_into_register(self.fetch_register())
        elif instruction == 0x0B: # JZ R1, ADDR
            if self.get_register(self.fetch_register()) == 0:
                self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x0C: # JNZ R1, ADDR
            if self.get_register(self.fetch_register()) != 0:
                self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x0D: # JG R1, ADDR
            if self.get_register(self.fetch_register()) > 0:
                self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x0E: # JL R1, ADDR
            if self.get_register(self.fetch_register()) < 0:
                self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x0F: # JEQ R1, R2
            reg1 = self.fetch_register()
            reg2 = self.fetch_register()
            if self.get_register(reg1) == self.get_register(reg2):
                self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x10: # JNE R1, R2
            reg1 = self.fetch_register()
            reg2 = self.fetch_register()
            if self.get_register(reg1) != self.get_register(reg2):
                self.pc = 0x1000 + self.fetch_addr()
        elif instruction == 0x11: # DRW R1, R2, R3
            self.draw_pixel(self.get_register(self.fetch_register()), self.get_register(self.fetch_register()), self.get_register(self.fetch_register()))
        elif instruction == 0x12: # CLR
            self.clear_display()
        elif instruction == 0x13: # RENDER
            self.display  = self.display2
            self.display2 = bytearray(DISPLAY_WIDTH*DISPLAY_HEIGHT)
        elif instruction == 0x14: # DIV R1, R2
            R1 = self.fetch_register()
            reg2 = self.fetch_register()
            self.set_register(R1, int(self.get_register(R1) / self.get_register(reg2)))
        elif instruction == 0x15: # MUL R1, R2
            R1 = self.fetch_register()
            reg2 = self.fetch_register()
            self.set_register(R1, int(self.get_register(R1) * self.get_register(reg2)))
        elif instruction == 0x16: # RECT R1, R2, R3, R4, R5
            self.draw_rectangle(
                self.get_register(self.fetch_register()),
                self.get_register(self.fetch_register()),
                self.get_register(self.fetch_register()),
                self.get_register(self.fetch_register()),
                self.get_register(self.fetch_register())
            )
        elif instruction == 0x17: # RND
            self.set_register(self.fetch_register(), self.step_random())
        elif instruction == 0x18: # SEED INT
            self.set_random(self.fetch_int())
        elif instruction == 0x19: # RNDMAP R1, IMM, IMM
            R1 = self.fetch_register()
            self.set_register(R1, int(map_to_range(
                self.get_register(R1),
                self.fetch_immediate(),
                self.fetch_immediate()
            )))
        elif instruction == 0xFF: # HLT
            self.halt("HLT by program")
        else:
            self.halt(f"Unknown instruction! {instruction=}")

        self.instructions_executed += 1
        self.print_ips()

        if self.ips_limit != float('inf'):
            elapsed_time = time.time() - self.start_time
            expected_time = self.instructions_executed / self.ips_limit
            if elapsed_time < expected_time:
                time.sleep(expected_time - elapsed_time)

    def print_ips(self) -> None:
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= 1.0:
            ips = self.instructions_executed / elapsed_time
            print(f"Instructions Per Second: {ips:.2f}")
            self.start_time = time.time()
            self.instructions_executed = 0

    def debug_server(self) -> None:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("localhost", 12345))
        server_socket.listen(1)
        server_socket.setblocking(False)
        print("Debug server started on port 12345")

        while not self.stop_requested:
            try:
                client_socket, _ = server_socket.accept()
                with client_socket:
                    while not self.stop_requested:
                        try:
                            data = client_socket.recv(2048)
                            if not data:
                                break
                            command = pickle.loads(data)
                            self.handle_debug_command(command, client_socket)
                        except EOFError:
                            break
                        except Exception as e:
                            print(f"Error while handling command: {e}")
            except OSError:
                if not self.stop_requested:
                    time.sleep(0.5)

        server_socket.close()
        print("Debug server stopped.")

    def handle_debug_command(self, command, client_socket) -> None:
        cmd_type = command["type"]
        response = {}
        
        try:
            if cmd_type == "GET_REGISTERS":
                response["data"] = self.registers
            elif cmd_type == "SET_REGISTER":
                reg = command["register"]
                value = command["value"]
                self.set_register(reg, value)
            elif cmd_type == "GET_MEMORY":
                addr = command["address"]
                response["data"] = self.get_memory(addr)
            elif cmd_type == "SET_MEMORY":
                addr = command["address"]
                value = command["value"]
                self.set_memory(addr, value)
            elif cmd_type == "GET_STACK":
                response["data"] = self.get_stack()
            elif cmd_type == "SET_STACK":
                index = command["index"]
                value = command["value"]
                self.set_stack(index, value)
            elif cmd_type == "PC":
                response["data"] = self.pc
            elif cmd_type == "SET_PC":
                value = command["value"]
                self.set_pc(value)
            elif cmd_type == "PAUSE":
                response["data"] = "OK"
                self.paused = True
            elif cmd_type == "RESUME":
                response["data"] = "OK"
                self.paused = False
            elif cmd_type == "HALT":
                message = command.get("message", "Remote Debugger requested HLT")
                response["data"] = "OK"
                self.halt(message)
            else:
                response["error"] = "Unknown command"
        except BaseException as e:
            response["error"] = str(e)

        client_socket.sendall(pickle.dumps(response))

    def stop(self):
        self.stop_requested = True
        self.debug_server_thread.join()

def main():
    cpu = CPU("test.rom")#, ips_limit=1000)

    try:
        while not cpu.halted:
            cpu.cycle()
    except KeyboardInterrupt:
        print("Interrupt received. Stopping CPU...")
        cpu.stop()
    except Exception as e:
        cpu.halt(str(e))
        print(f"Exception: {e}")
        cpu.stop()

if __name__ == "__main__":
    main()
