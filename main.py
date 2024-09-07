import pygame
import numpy as np
from emulator import CPU
import threading

from cpuio.test import TestDevice

DISPLAY_WIDTH = 256
DISPLAY_HEIGHT = 256

PALETTE = [
    (0, 0, 0),       # 00: Black
    (29, 43, 83),    # 01: Dark Blue
    (126, 37, 83),   # 02: Purple
    (0, 135, 81),    # 03: Green
    (171, 82, 54),   # 04: Brown
    (95, 87, 79),    # 05: Dark Gray
    (194, 195, 199), # 06: Light Gray
    (255, 241, 232), # 07: White
    (255, 0, 77),    # 08: Red
    (255, 163, 0),   # 09: Orange
    (255, 236, 39),  # 10: Yellow
    (0, 228, 54),    # 11: Light Green
    (41, 173, 255),  # 12: Light Blue
    (131, 118, 156), # 13: Light Purple
    (255, 119, 168), # 14: Pink
    (255, 204, 170)  # 15: Peach
]

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        pygame.display.set_caption("Emulator")

        self.cpu = CPU("test.rom", [TestDevice])

        self.clock = pygame.time.Clock()
        self.running = True

        self.surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.palette_array = np.array(PALETTE, dtype=np.uint8)

        self.cpu_thread = threading.Thread(target=self.cpu_cycle_thread, daemon=True)
        self.cpu_thread.start()

    def cpu_cycle_thread(self):
        while not self.cpu.halted:
            self.cpu.cycle()

    def update_display(self):
        indexed_data = np.array(self.cpu.display, dtype=np.uint8).reshape((DISPLAY_HEIGHT, DISPLAY_WIDTH))
        if np.any(indexed_data >= len(self.palette_array)):
            print("Color doesn't fit in the palette!")
            indexed_data[indexed_data >= len(self.palette_array)] = 15
        rgb_array = self.palette_array[indexed_data]

        pygame.surfarray.blit_array(self.surface, rgb_array)

    def run(self):
        while self.running and not self.cpu.halted:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.update_display()

            self.screen.blit(self.surface, (0, 0))
            pygame.display.flip()

            self.clock.tick(60)

        self.cpu.halt("Window exit")
        self.cpu_thread.join()
        pygame.quit()

if __name__ == "__main__":
    main = Main()
    main.run()
