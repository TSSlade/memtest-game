import pygame


class NextButton:
    def __init__(
        self,
        screen,
        text_color=(0, 59, 102),
        border_color=(211, 211, 211),
        w=280,
        h=70,
        show_up_text="Next",
    ):
        self.screen = screen
        # get the screen based parameters; x, y, w, font size are determined based on screen size
        screen_width, screen_height = screen.get_size()
        FONT = pygame.font.Font(None, screen_width // 24)
        text_width, text_height = FONT.size(show_up_text)
        w = text_width * 1.14
        x = 5 * screen_width / 6 - w / 2
        y = 3 * screen_height / 4
        self.rect = pygame.Rect(x, y, w, h)
        self.border_color = border_color

        self.text_surface = FONT.render(show_up_text, True, text_color)
        self.go_next_page = False
        # self.border_color = 'black'

    def handle_click(self, click_event):
        if self.rect.collidepoint(click_event.pos):
            self.go_next_page = True
        else:
            self.go_next_page = False
        return self.go_next_page

    def draw(self):
        self.screen.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(self.screen, self.border_color, self.rect, 2)


class Title:
    def __init__(
        self,
        screen,
        font_ratio_to_screen=20,
        text_color=(0, 59, 102),
        border_color=(211, 211, 211),
        h=90,
        show_up_text="",
    ):
        self.screen = screen
        screen_width, screen_height = screen.get_size()
        self.FONT = pygame.font.Font(None, screen_width // font_ratio_to_screen)
        text_width, text_height = self.FONT.size(show_up_text)
        w = text_width * 1.08
        x = screen_width / 2 - w / 2
        y = screen_height / 30

        self.rect = pygame.Rect(x, y, w, h)

        self.text_surface = self.FONT.render(show_up_text, True, text_color)
        self.border_color = border_color
        # self.border_color = 'black'

    def draw(self):
        self.screen.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(self.screen, self.border_color, self.rect, 2)
        # pygame.display.flip()


class TitleOfInputBox:
    def __init__(
        self,
        screen,
        title_text,
        x,
        y,
        w=280,
        color_border_inactive=(192, 192, 192),
        text_color=(0, 59, 102),
    ):
        self.title_text = title_text
        # get the screen based parameters; x, y, w, font size are determined based on screen size
        screen_width, screen_height = screen.get_size()
        self.FONT = pygame.font.Font(None, screen_width // 48)
        w = screen_width // 7
        h = screen_height // 27
        self.rect = pygame.Rect(x, y, w, h)
        self.color_border_inactive = color_border_inactive
        self.text_surface = self.FONT.render(
            self.title_text.capitalize(), True, text_color
        )

    def draw(self, screen):
        screen.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color_border_inactive, self.rect, 2)


class InputBox:
    """https://stackoverflow.com/questions/46390231/how-can-i-create-a-text-input-box-with-pygame"""

    def __init__(
        self,
        screen,
        type_text,
        x,
        y,
        color_border_inactive=(192, 192, 192),
        border_color_active=(105, 105, 105),
        text_color=(0, 59, 102),
        initial_text: str = "",
    ):
        self.type_text = type_text
        self.text = initial_text
        # rect paramters based on screen size
        screen_width, screen_height = screen.get_size()
        self.FONT = pygame.font.Font(None, screen_width // 48)
        w = screen_width // 7
        h = screen_height // 18
        self.rect = pygame.Rect(x, y, w, h)
        self.text_color = text_color
        self.border_color = color_border_inactive
        self.color_border_inactive = color_border_inactive
        self.border_color_active = border_color_active
        self.txt_surface = self.FONT.render(self.text, True, text_color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.border_color = (
                    self.border_color_active
                )  # Change the current color of the input box.
            else:
                self.active = False
                self.border_color = (
                    self.color_border_inactive
                )  # Change the current color of the input box.

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = self.FONT.render(self.text, True, self.text_color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
