import pygame

from .buttons import NextButton, Title


class StartActualTask:
    def handler(self, screen) -> None:
        next_btn = NextButton(screen, text_color=(0, 59, 102), border_color="white")
        title_bnt = Title(
            screen,
            text_color=(0, 59, 102),
            border_color="white",
            show_up_text="Click to start!",
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
            title_bnt.draw()
            pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_color = "white"
    screen.fill(screen_color)
    setter_actual_page_object = StartActualTask()
    setter_actual_page_object.handler(screen)
    pygame.quit()
