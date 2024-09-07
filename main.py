import random
import pygame
import numpy as np
from emulator import CPU
import threading

DISPLAY_WIDTH = 256
DISPLAY_HEIGHT = 256

PALETTE = [
    (0, 0, 0),
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
]

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        pygame.display.set_caption("Emulator")

        self.cpu = CPU("test.rom")

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
            # indexed_data[indexed_data >= len(self.palette_array)] = random.randint(1, 3)
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
