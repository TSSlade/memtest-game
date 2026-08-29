import datetime
import math
import time
from typing import TYPE_CHECKING

import pygame

from .alerts import beep
from .hexagon import HexagonTile

if TYPE_CHECKING:
    from ..config.game_config import GameConfig
    from ..config.session_config import SessionConfig
    from ..user.user_info import UserInfo


class Task:
    def __init__(
        self,
        *,
        indices_target,
        dda_mthd,
        user_info: UserInfo,
        session_config: SessionConfig,
        game_config: GameConfig,
        num_x,
        num_y,
        show_time,
        position_init,
        R_hexagon,
        tracker,
        is_eye_tracker,
        task_number,
    ):
        """Set up one task: a hexagonal grid with a set of cells to memorise.

        Parameters are listed in signature order.

        indices_target: tuple: indices of the cells that should be target cells.
                Indexing runs from the upper left, along each row, then down.
        dda_mthd: str: which method is used for dynamic difficulty adjustment.
        user_info: dict: the participant data. Every element of user_info is
                added to this object's __dict__.
        session_config: SessionConfig: the protocol's session parameters.
        game_config: GameConfig: the game parameters, including the alert sounds
                that double as camera synchronisation markers.
        num_x: number of columns in the task table.
        num_y: number of rows in the task table.
        show_time: int: how many seconds the task is shown for, for the
                participant to memorise.
        position_init: the position of the upper-leftmost hexagon in the task;
                passed through to the HexagonTile.
        R_hexagon: float: the radius of each hexagon; passed through to the
                HexagonTile.
        tracker: eye tracker object. Used when is_eye_tracker is True and
                ignored otherwise; never exercised in this fork, see
                MODIFICATIONS.md.
        is_eye_tracker: bool: True when an eye tracker device is present.
        task_number: int: used when is_eye_tracker is True. This task's position
                within its trial: 0 is the first, 1 the second.
        """
        self.user_info = user_info
        self.session_config = session_config
        self.game_config = game_config
        self.is_eye_tracker = is_eye_tracker
        self.tracker = tracker
        self.indices_target: list[int] = indices_target
        self.dda_mthd = dda_mthd
        self.num_x: int = num_x
        self.num_y: int = num_y
        self.show_time: int = show_time
        self.position_init: tuple[int, int] = position_init
        self.R_hexagon = R_hexagon
        self.n_target: int = len(indices_target)
        self.hexagons: list[HexagonTile] = self.create_task(R_hexagon)

        # based on user answer
        self.start_showing_task_ts: datetime.datetime
        self.end_showing_task_ts: datetime.datetime
        self.start_answering_ts: datetime.datetime
        self.indices_answer: list[int] = []
        self.sequence_answer: list[int] = []
        # Timedeltas, not floats. Gaps rather than absolute times: the first
        # element is measured from the start of answering, each later one from
        # the previous click.
        self.sequence_response_time: list[datetime.timedelta] = []
        self.num_true: int
        self.num_false: int
        self.nailed_it: bool = False
        self.score: float
        self.end_answering_ts: datetime.datetime
        self.task_number = task_number

    def run_task(self, screen, alert_log=None):
        """Run one task and return its score.

        `alert_log` is passed rather than stored on the instance because
        `main_game` serialises the task with `vars(task_obj)` into the gameplay
        data; an accumulating log held as an attribute would be written into
        every row.
        """
        endTime = datetime.datetime.now() + datetime.timedelta(seconds=self.show_time)
        self.start_showing_task_ts = datetime.datetime.now()
        terminated = False

        # send trigger to eye tracker; start memorization
        if self.is_eye_tracker:
            event_tag_ET = str(self.task_number) + "_MEMO_ST"
            self.tracker.user_data(event_tag_ET)  # send event to eye tracker

        # Clear screen to white before showing the task
        screen.fill("white")

        # memorization mode
        while not terminated:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit("Window closed by user")
            self.render_task(screen)
            if datetime.datetime.now() >= endTime:
                self.end_showing_task_ts = datetime.datetime.now()
                break

        # send trigger to eye tracker; end memorization
        if self.is_eye_tracker:
            event_tag_ET = str(self.task_number) + "_MEMO_END"
            self.tracker.user_data(event_tag_ET)  # send event to eye tracker

        # recall mode
        # show the white screen to the user in order to get their answer
        terminated = False  # if answering is terminated or not
        clicked_hexagon_id = set()
        count = 0
        pygame.event.clear()
        t_last_click: datetime.datetime | None = None
        while not terminated:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit("Window closed by user")
                if (event.type == pygame.MOUSEBUTTONUP) and (event.button == 1):
                    t_current_click = datetime.datetime.now()  # the current click time
                    pos = pygame.mouse.get_pos()  # position of the mouse click; (x, y)

                    # find the hexagon which the user clicked on
                    for hexagon in self.hexagons:
                        if (
                            hexagon.collide_with_point(pos)
                            and id(hexagon) not in clicked_hexagon_id
                        ):
                            # append response time to sequence_response_time
                            if len(clicked_hexagon_id) == 0:  # if it is the first click of the user
                                self.sequence_response_time.append(
                                    t_current_click - self.start_answering_ts
                                )
                                t_last_click = t_current_click
                            else:  # if it is not the first click of the user
                                if t_last_click is not None:
                                    self.sequence_response_time.append(
                                        t_current_click - t_last_click
                                    )
                                t_last_click = t_current_click

                            # append index of the clicked hexagon to indices_answer
                            self.indices_answer.append(hexagon.index)
                            clicked_hexagon_id.add(id(hexagon))

                            # append this click data into sequence_answer
                            if hexagon.is_answered_true:
                                self.sequence_answer.append(1)
                            elif hexagon.is_answered_true is False:
                                self.sequence_answer.append(0)
                            break

                    if len(clicked_hexagon_id) == len(self.indices_target):
                        terminated = True

            self.render_answer(screen)
            if count == 0:  # at the moment that answering screen is shown
                # send trigger to eye tracker; start recall
                if self.is_eye_tracker:
                    # send event to eye tracker
                    event_tag_ET = str(self.task_number) + "_RECALL_ST"
                    self.tracker.user_data(event_tag_ET)
                count += 1
                self.start_answering_ts = datetime.datetime.now()

        # send trigger to eye tracker; end recall
        if self.is_eye_tracker:
            # send event to eye tracker
            event_tag_ET = str(self.task_number) + "_RECALL_END"
            self.tracker.user_data(event_tag_ET)

        # end of answering to current task
        self.end_of_task()

        # Emitted through `beep()` so it lands in the session sidecar like every
        # other alert. This fires once per task, making it the most frequent
        # sound in a session and the one most likely to be encountered when
        # matching a recording's audio track.
        if self.game_config:
            beep("task_complete", self.game_config, alert_log=alert_log)

        time.sleep(2)

        return self.score

    def create_task(self, R_hexagon) -> list[HexagonTile]:
        """Create a hexagonal tile map of num_x * num_y cells.

        Cells whose index appears in indices_target are targets. Returns the
        hexagons as a list.
        """

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
            for _ in range(1, self.num_x):  # i is the column number
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

    def end_of_task(self):
        """set some attributes value. delete some useless attributes"""
        self.end_answering_ts = datetime.datetime.now()
        self.num_true = self.sequence_answer.count(1)
        self.num_false = self.sequence_answer.count(0)
        self.nailed_it = self.num_true == self.n_target
        self.score = self.num_true / self.n_target
        # main_game serialises this object with vars(task_obj) into the
        # gameplay data, so anything that is not a value has to go first: a list
        # of HexagonTile objects and a tracker handle are not columns.
        delattr(self, "hexagons")
        delattr(self, "tracker")


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
        (1, 2, 3, 4, 33),
        (1, 3, 5, 9),
        (18, 17, 31),
        (0, 5, 8, 9, 11, 17, 20, 22, 30, 33, 35),
    ]:
        task_obj = Task(
            indices_target=i,
            dda_mthd="nothing",
            user_info={},
            session_config=None,
            game_config=None,
            num_x=6,
            num_y=6,
            show_time=2,
            position_init=position_init,
            R_hexagon=R_hexagon,
            tracker=None,
            is_eye_tracker=False,
            task_number=None,
        )
        task_obj.run_task(screen)
    pygame.display.quit()
