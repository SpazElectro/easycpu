HELP_MESSAGE = """
EasyCPU Debugger Commands:
r   - Get registers
sr  $r $v - Set register $r to $v
m   $a - Get memory at $a
sm  $a $v - Set memory at $a to $v
s   - Get stack
ss  $i $v - Set stack at $i to $v
pc  - Get PC
spc $v - Set PC to $v
p   - Pause
rs  - Resume
h   - Halt
help - Show this help message
exit - Exit the debugger
"""

import socket
import pickle
import inspect

def send_command(command):
    if command["type"] == "SET_REGISTER":
        command["register"] = str(command["register"]).upper()
        if not command["register"].startswith("R"):
            command["register"] = f"R{command['register']}"
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 12345))
        s.sendall(pickle.dumps(command))
        response = s.recv(1024)
        return pickle.loads(response)

GET_REGISTERS = lambda: send_command({"type": "GET_REGISTERS"})
SET_REGISTER = lambda r, v: send_command({"type": "SET_REGISTER", "register": r, "value": v})
GET_MEMORY = lambda a: send_command({"type": "GET_MEMORY", "address": a})
SET_MEMORY = lambda a, v: send_command({"type": "SET_MEMORY", "address": a, "value": v})
GET_STACK = lambda: send_command({"type": "GET_STACK"})
SET_STACK = lambda i, v: send_command({"type": "SET_STACK", "index": i, "value": v})
GET_PC = lambda: send_command({"type": "PC"})
SET_PC = lambda v: send_command({"type": "SET_PC", "value": v})
PAUSE = lambda: send_command({"type": "PAUSE"})
RESUME = lambda: send_command({"type": "RESUME"})
HALT = lambda: send_command({"type": "HALT"})

commands = {
    "r": GET_REGISTERS,
    "sr": SET_REGISTER,
    "m": GET_MEMORY,
    "sm": SET_MEMORY,
    "s": GET_STACK,
    "ss": SET_STACK,
    "pc": GET_PC,
    "spc": SET_PC,
    "p": PAUSE,
    "rs": RESUME,
    "h": HALT,
    "help": lambda: print(HELP_MESSAGE),
    "exit": lambda: exit(0)
}

def parse_args(func, args):
    sig = inspect.signature(func)
    params = sig.parameters
    if len(params) != len(args):
        raise ValueError(f"Command expects {len(params)} arguments but got {len(args)}")
    
    parsed_args = []
    for param, arg in zip(params.values(), args):
        if arg.startswith('0x'):
            arg = int(arg, 16)
        else:
            try:
                arg = int(arg)
            except ValueError:
                pass
        
        if param.annotation != inspect.Parameter.empty:
            parsed_args.append(param.annotation(arg))
        else:
            parsed_args.append(arg)
    
    return parsed_args

import json

def main():
    while True:
        user_input = input("Enter command: ")
        parts = user_input.split()
        if len(parts) == 0:
            continue
        cmd = parts[0]
        args = parts[1:]

        if cmd in commands:
            func = commands[cmd]
            try:
                parsed_args = parse_args(func, args)
                result = func(*parsed_args)
                if result:
                    data = result.get("data", None)
                    if isinstance(data, (int, float)):
                        print(f"{data} (0x{data:x})")
                    elif isinstance(data, (dict, list)):
                        print(json.dumps(data, indent=4))
                    elif result.get("error", None):
                        print(result.get("error"))
                    else:
                        print(f"{data}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Unknown command")

if __name__ == "__main__":
    main()
