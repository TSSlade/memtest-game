import math
import time

import pygame

from ..ui.buttons import Title
from .hexagon import HexagonTile


class TaskGuiding:
    def __init__(
        self,
        *,
        indices_target,
        num_x=6,
        num_y=6,
        show_time=2,
        position_init=(763, 300),
        R_hexagon=70.0,
    ):
        """
        sequence_response_time: list[float, float, ...]: each float is in second.
                first element : delta_time between start answering and first click
                second element : delta_time between last click and current click
        """
        self.indices_target: list[int] = indices_target
        self.n_target: int = len(indices_target)
        self.num_x: int = num_x
        self.num_y: int = num_y
        self.show_time: int = show_time
        self.position_init: tuple[int, int] = position_init
        self.hexagons: list[HexagonTile] = self.create_task(R_hexagon)
        # based on user answer
        self.indices_answer: list[int] = []

    def run_guiding_task(self, screen):
        title_bnt = Title(
            screen,
            text_color=(0, 59, 102),
            border_color="white",
            show_up_text="guiding trials",
        )
        endTime = time.time() + self.show_time
        terminated = False
        while not terminated:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit("Window closed by user")
            title_bnt.draw()
            self.render_task(screen)
            if time.time() >= endTime:
                break

        # show the white screen to the user in order to get their answer
        terminated = False  # if answering is terminated or not
        clicked_hexagon_id = set()

        pygame.event.clear()
        while not terminated:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit("Window closed by user")
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    pos = pygame.mouse.get_pos()  # position of the mouse clicked; (x, y)
                    # find the hexagon which the user clicked on
                    for hexagon in self.hexagons:
                        if (
                            hexagon.collide_with_point(pos)
                            and id(hexagon) not in clicked_hexagon_id
                        ):
                            clicked_hexagon_id.add(id(hexagon))
                            break

                    if len(clicked_hexagon_id) == len(self.indices_target):
                        terminated = True
            title_bnt.draw()
            self.render_answer(screen)
        time.sleep(2)

    def create_task(self, R_hexagon) -> list[HexagonTile]:
        """Creates a hexagonal tile map of size num_x * num_y"""

        # determine if first cell is yellow or white
        temp = 0 in self.indices_target
        hex_counter = 0
        leftmost_hexagon = HexagonTile(
            is_target_cell=temp,
            position=self.position_init,
            index=hex_counter,
            radius=R_hexagon,
        )
        hexagons = [leftmost_hexagon]
        # iterate over rows
        for x in range(self.num_y):  # x is the row number
            if x:
                # alternate between bottom left and bottom right vertices of hexagon above
                index = 2 if x % 2 == 1 else 4
                position = leftmost_hexagon.vertices[index]
                position = (position[0], position[1])

                # determine if current cell is target or not (yellow or white)
                is_target_cell = hex_counter in self.indices_target
                leftmost_hexagon = HexagonTile(
                    is_target_cell=is_target_cell,
                    position=position,
                    index=hex_counter,
                    radius=R_hexagon,
                )
                hexagons.append(leftmost_hexagon)
                hex_counter += 1
            else:
                hex_counter += 1

            # place hexagons to the left of leftmost hexagon, with equal y-values.
            hexagon = leftmost_hexagon

            # iterate over columns
            for _ in range(1, self.num_x):
                x, y = hexagon.position
                position = (x + hexagon.minimal_radius * 2, y)
                position = (position[0], position[1])

                # determine if current cell is target or not (yellow or white)
                is_target_cell = hex_counter in self.indices_target
                hexagon = HexagonTile(
                    is_target_cell=is_target_cell,
                    position=position,
                    index=hex_counter,
                    radius=R_hexagon,
                )
                hexagons.append(hexagon)
                hex_counter += 1

        return hexagons

    def render_task(self, screen):
        for hexagon in self.hexagons:
            hexagon.render(screen)
            hexagon.render_border(screen)
        pygame.display.flip()

    def render_answer(self, screen):
        for hexagon in self.hexagons:
            hexagon.render_answer(screen)
            hexagon.render_border(screen)
        pygame.display.flip()


def task_param_based_on_screen(screen, num_x=6, num_y=6):
    """Derive hexagon geometry from the screen size.

    input
    -------
            screen: pygame screen object
    output
    -------
            R_hexagon: radius of each hexagon, based on screen size
            position_init: the position of the leftmost hexagon, based on screen
                    size
    """
    screen_width, screen_height = screen.get_size()
    R_hexagon = screen_width / 25
    d_hexagon = 2 * R_hexagon * math.cos(math.radians(30))
    position_init = (
        screen_width / 2 - (num_x - 1.5) / 2 * d_hexagon,
        screen_height / 2 - (num_y - 0.5) * R_hexagon,
    )
    return position_init, R_hexagon


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1919, 1079))
    # get parameters to pass into the Task based on screen size
    position_init, R_hexagon = task_param_based_on_screen(screen)
    screen.fill("white")
    for i in [
        (1, 2, 3, 4),
        (10, 12, 14, 30, 35),
        (0, 5, 8, 9, 11, 17, 20, 30, 31, 35),
    ]:
        task_gd_obj = TaskGuiding(
            indices_target=i,
            num_x=6,
            num_y=6,
            position_init=position_init,
            R_hexagon=R_hexagon,
        )
        task_gd_obj.run_guiding_task(screen)

    pygame.display.quit()
