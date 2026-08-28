import json
import random
import time
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

import matplotlib  # isort: skip

matplotlib.use("TkAgg")  # isort: skip
import matplotlib.pyplot as plt  # isort: skip
import numpy as np
import pandas as pd
import pygame

from ..config.game_config import GameConfig
from ..ui.demo_page import DemoPage
from ..ui.sign_up_page import SignUp
from ..ui.start_actual_task_page import StartActualTask
from ..ui.welcome_page import Welcome
from .task import Task, task_param_based_on_screen
from .task_guiding import TaskGuiding

# Make CWD be the folder this file lives in (handles symlinks, uv, etc.)
# Handles issues that otherwise arise from running via `uv run <path>/main_game.py`
# os.chdir(Path(__file__).resolve().parent)

# Get the base directory for memtest (parent of game/)
MEMTEST_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = MEMTEST_DIR / "assets"


def beep(alert, game_config, wait: bool = False) -> None:
    """Play the alert sound for `alert`.

    Returns as soon as playback starts. `pygame`'s `Sound.play()` is already
    asynchronous; blocking for the sound's duration would delay the protocol by
    several seconds per alert and, worse, make an event timestamp taken after
    the call mean something different from one taken before it.

    Pass `wait=True` only where the process is about to do something that would
    cut playback short, such as shutting down the mixer.
    """
    if not game_config.enable_audio_alerts:
        return
    audio_file = game_config.get_audio_file(alert)
    if audio_file is None:
        print(f"[WARNING] No audio file configured for alert: {alert}")
        return
    # Resolve relative paths against MEMTEST_DIR
    if not audio_file.is_absolute():
        audio_file = MEMTEST_DIR / audio_file
    print(f"Triggering sound at {audio_file}")
    if not audio_file.exists():
        print(f"[ERROR] Audio file not found: {audio_file}")
        return
    sound = pygame.mixer.Sound(file=audio_file)
    sound.set_volume(game_config.volume)
    sound.play()
    if wait:
        time.sleep(sound.get_length())


def dda_rule_based(
    *,
    screen,
    episode_len,
    trials_per_effort,
    wait_breaks,
    user_info,
    save_gameplay_data,
    gameplay_data_file_name,
    num_x,
    num_y,
    is_eye_tracker,
    tracker,
    event_timestamps,
    session_config,
    game_config,
):
    position_init, R_hexagon = task_param_based_on_screen(screen)
    score_list = []
    gameplay_data_list = []
    position_init, R_hexagon = task_param_based_on_screen(screen)
    n_target = 5
    break_tally = 0
    for step in range(episode_len):
        n_target = np.clip(n_target, a_min=4, a_max=14)
        can_be_target_cell = set(range(36)) - {0, 5, 8, 9, 11, 17, 20, 22, 30, 33, 35}
        indices_one = random.sample(sorted(can_be_target_cell), k=n_target)
        task_obj = Task(
            indices_target=indices_one,
            dda_mthd="rule-base",
            user_info=user_info,
            session_config=session_config,
            game_config=game_config,
            difficulty=None,
            num_x=num_x,
            num_y=num_y,
            show_time=2,
            position_init=position_init,
            R_hexagon=R_hexagon,
            is_eye_tracker=is_eye_tracker,
            tracker=tracker,
            task_number=step,
        )
        score = task_obj.run_task(screen)
        gameplay_data_list.append(vars(task_obj))
        print(
            f"[{step + 1}]/[{episode_len}]: {100 * score:1.2f}% of {n_target} targets"
        )
        score_list.append(score)
        if score is not None and 0.9 < score <= 1:
            n_target += 1
        elif score is not None and 0 <= score < 0.7:
            n_target -= 1
        # Check if we need a break, but skip if this is the last task
        if (step + 1) % trials_per_effort == 0 and (step + 1) != episode_len:
            print(
                f"Finished step {step + 1} @ {trials_per_effort} tasks per trial | Taking {wait_breaks}-sec break"
            )
            break_tally += 1
            curr_break = f"break_{break_tally:02}"
            event_timestamps[f"{curr_break}_start"] = datetime.now()
            print(
                f"Starting break {break_tally} at {event_timestamps.get(curr_break + '_start')}"
            )
            beep("start_break", game_config)
            for _ in tqdm(iterable=range(wait_breaks), unit="s"):
                time.sleep(1)
            event_timestamps[f"{curr_break}_end"] = datetime.now()
            beep("end_break", game_config)
            print(
                f"Ending break {break_tally} at {event_timestamps.get(curr_break + '_end')}"
            )
    if save_gameplay_data:
        gameplay_data_df = pd.DataFrame(gameplay_data_list)
        # Output to grandparent's data/memtest/ directory
        output_dir = MEMTEST_DIR.parent.parent / "data" / "memtest"
        output_dir.mkdir(parents=True, exist_ok=True)
        gameplay_data_df.to_csv(output_dir / f"{gameplay_data_file_name}.csv")
        gameplay_data_df.to_pickle(output_dir / f"{gameplay_data_file_name}.pkl")
    return score_list


def _load_game_config(config_path: Path | None = None) -> GameConfig:
    """Load game configuration from JSON file or use defaults."""
    if config_path is None:
        config_path = MEMTEST_DIR / "config" / "config.json"

    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)
            game_data = config_data.get("game", {})
            if game_data:
                print(f"[INFO] Loading game configuration from {config_path}")
                return GameConfig.from_dict(game_data)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[WARNING] Failed to load game config from {config_path}: {e}")
    else:
        print("[INFO] Using default game configuration")

    return GameConfig()


def game_provider_rule_based(*args):
    event_timestamps = {}
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1920, 1080))
    screen_color = (211, 211, 211)
    screen.fill(screen_color)
    welcome_obj = Welcome(screen)
    welcome_obj.handler()
    screen.fill(screen_color)
    # Use default config path (can be overridden via args if needed)
    config_path = MEMTEST_DIR / "config" / "config.json"
    signup_page_obj = SignUp(screen, screen_color=screen_color, config_path=config_path)
    user_info, session_config = signup_page_obj.handler()
    game_config = _load_game_config(config_path)
    episode_len = session_config.num_trials
    trials_per_effort = session_config.trials_per_effort
    wait_baseline = session_config.wait_baseline
    wait_breaks = session_config.wait_breaks
    wait_endline = session_config.wait_endline
    screen.fill("white")
    guid_obj = DemoPage()
    guid_obj.provide_demo(screen)
    position_init, R_hexagon = task_param_based_on_screen(screen=screen)
    for indices in ((1, 4, 13), (9, 12, 17, 21, 23), (3, 4, 9, 10, 15, 16, 20)):
        screen.fill("white")
        task_obj = TaskGuiding(
            indices_target=indices,
            position_init=position_init,
            R_hexagon=R_hexagon,
            show_time=2,
            num_x=6,
            num_y=6,
        )
        task_obj.run_guiding_task(screen)
        break
    screen.fill("white")
    setter_actual_pg_obj = StartActualTask()
    setter_actual_pg_obj.handler(screen)
    # Start baseline sound
    # Timestamp immediately before the alert, matching every other event here,
    # so a recorded time always denotes the moment its sound began.
    print("Starting baseline - playing start_baseline sound")
    event_timestamps["baseline_start"] = datetime.now()
    beep("start_baseline", game_config)
    print(
        f"Starting {wait_baseline}-sec. baseline at {event_timestamps.get('baseline_start')}"
    )
    for _ in tqdm(range(wait_baseline), unit="s"):
        time.sleep(1)
    event_timestamps["baseline_end"] = datetime.now()
    print(f"Ending baseline at {event_timestamps.get('baseline_end')}")
    # Start game sound (before tasks begin)
    beep("start_game", game_config)
    screen.fill("white")
    score_list = dda_rule_based(
        screen=screen,
        episode_len=episode_len,
        trials_per_effort=trials_per_effort,
        wait_breaks=wait_breaks,
        user_info=user_info,
        save_gameplay_data=True,
        gameplay_data_file_name="memtest_output",
        num_x=game_config.num_hexagons // 6,
        num_y=6,
        is_eye_tracker=False,
        tracker=None,
        event_timestamps=event_timestamps,
        session_config=session_config,
        game_config=game_config,
    )
    event_timestamps["endline_start"] = datetime.now()
    print(f"Starting endline at {event_timestamps.get('endline_start')}")
    beep("start_endline", game_config)
    for _ in tqdm(range(wait_endline), unit="s"):
        time.sleep(1)
    event_timestamps["endline_end"] = datetime.now()
    print(f"Ending endline at {event_timestamps.get('endline_end')}")
    # The only alert that must block: pygame.quit() below tears down the mixer
    # and would truncate playback.
    beep("end_game", game_config, wait=True)
    pygame.display.quit()
    pygame.quit()
    print(
        "\n".join(
            f"{k:<20}: {v.isoformat(sep=' ', timespec='milliseconds')}"
            for k, v in event_timestamps.items()
        )
    )
    return score_list, user_info


def main():
    score_list, user_info = game_provider_rule_based()
    last = getattr(user_info, "last_name", "anon").strip().replace(" ", "_") or "anon"
    first = getattr(user_info, "name", "anon").strip().replace(" ", "_") or "anon"
    timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")

    # Output to grandparent's data/memtest/ directory
    output_dir = MEMTEST_DIR.parent.parent / "data" / "memtest"
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.plot(score_list)
    plt.title("your score graph")
    plt.xlabel("step")
    plt.ylabel("score")
    plt.savefig(output_dir / f"{last}_{first}_{timestamp}.png")
    plt.show()


if __name__ == "__main__":
    main()
