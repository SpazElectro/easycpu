from emulator import IODevice

class TestDevice(IODevice):
    def _in(self, addr: int) -> None:
        self.cpu.set_memory(addr, bytearray([
            69, 42, 69, 42
        ]))
    
    def _out(self, addr: int) -> None:
        self.cpu.set_memory(addr, bytearray([
            42, 69, 42, 69
        ]))
