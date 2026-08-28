import math
from dataclasses import dataclass

import pygame


@dataclass
class HexagonTile:
    """source: https://github.com/rbaltrusch/pygame_examples/tree/master/code/hexagonal_tiles"""

    is_target_cell: bool
    position: tuple[float, float]
    index: int
    radius: float
    is_answered_true: bool | None = None
    is_clicked_as_answer: bool = False
    answer_color: tuple[int, int, int] = (255, 255, 255)  # answer color of white

    def __post_init__(self):
        self.hex_color = (
            (255, 255, 255) if self.is_target_cell is False else (255, 215, 0)
        )
        self.vertices = self.compute_vertices()

    def compute_vertices(self) -> list[tuple[float, float]]:
        """Returns a list of the hexagon's vertices as x, y tuples"""
        # pylint: disable=invalid-name
        x, y = self.position
        half_radius = self.radius / 2
        minimal_radius = self.minimal_radius
        return [
            (x, y),
            (x - minimal_radius, y + half_radius),
            (x - minimal_radius, y + 3 * half_radius),
            (x, y + 2 * self.radius),
            (x + minimal_radius, y + 3 * half_radius),
            (x + minimal_radius, y + half_radius),
        ]

    def collide_with_point(self, point: tuple[float, float]) -> bool:
        """Returns True if distance from centre to point is less than horizontal_length"""
        if math.dist(point, self.center) < self.minimal_radius:
            self.is_clicked_as_answer = True
            if self.is_target_cell:  # if this cell is a target cell
                self.is_answered_true = True
                self.answer_color = (0, 255, 0)  # green clr
            else:
                self.is_answered_true = False
                self.answer_color = (255, 0, 0)  # red clr
            return True
        else:
            return False

    def render(self, screen) -> None:
        """Renders the hexagon on the screen"""
        pygame.draw.polygon(screen, (self.highlight_clr), self.vertices)

    def render_answer(self, screen) -> None:
        """Renders the hexagon on the screen"""
        pygame.draw.polygon(screen, (self.answer_color), self.vertices)

    def render_border(self, screen, border_clr=(0, 0, 0)) -> None:
        """Draws a border around the hexagon with the specified clr"""
        pygame.draw.aalines(screen, border_clr, closed=True, points=self.vertices)

    @property
    def center(self) -> tuple[float, float]:
        """Centre of the hexagon"""
        x, y = self.position  # pylint: disable=invalid-name
        return (x, y + self.radius)

    @property
    def minimal_radius(self) -> float:
        """Horizontal length of the hexagon"""
        # https://en.wikipedia.org/wiki/Hexagon#Parameters
        return self.radius * math.cos(math.radians(30))

    @property
    def highlight_clr(self) -> tuple[int, ...]:
        return tuple(x for x in self.hex_color)


## UNUSED/REDUNDANT IMPORTS FLAGGED:
# 'field' from dataclasses is imported but never used
# 'Tuple', 'List' from typing were imported but are not needed in Python 3.12+
# 'from __future__ import annotations' is not needed in Python 3.12+
