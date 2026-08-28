import pygame

from .buttons import NextButton, Title


class Welcome:
    def __init__(self, screen) -> None:
        self.screen = screen

    def handler(self) -> None:
        next_btn = NextButton(self.screen, text_color=(0, 59, 102))
        title_btn = Title(
            self.screen,
            text_color=(0, 59, 102),
            border_color=(211, 211, 211),
            show_up_text="Welcome",
        )
        terminated = False
        while not terminated:
            event = pygame.event.wait()
            # handle QUIT event
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit("Window closed by user")
            # handle MOUSEBUTTONUP
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                terminated = next_btn.handle_click(event)
            next_btn.draw()
            title_btn.draw()
            pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    # width, height = pygame.display.get_desktop_sizes()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    # print(type(screen))
    screen_color = (211, 211, 211)
    screen.fill(screen_color)
    welcome_object = Welcome(screen)
    welcome_object.handler()
    pygame.quit()
