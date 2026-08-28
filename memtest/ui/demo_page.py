import pygame

from ..paths import ASSETS_DIR
from .buttons import NextButton


class DemoPage:
    # def __init__(self) -> None:
    # self.screen = screen

    def provide_demo(self, screen):
        img1 = pygame.image.load(ASSETS_DIR / "guide_en.png")
        next_obj = NextButton(screen, border_color=(255, 255, 255))
        terminated = False
        while not terminated:
            event = pygame.event.wait()
            # for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit("Window closed by user")
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                terminated = next_obj.handle_click(event)

            screen.blit(img1, (650, 50))
            next_obj.draw()
            pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_color = "white"
    screen.fill(screen_color)
    obj = DemoPage()
    obj.provide_demo(screen)
    pygame.quit()
