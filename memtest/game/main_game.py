import argparse
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
from ..paths import CONFIG_DIR, MEMTEST_DIR
from ..ui.demo_page import DemoPage
from ..ui.sign_up_page import SignUp
from ..ui.start_actual_task_page import StartActualTask
from ..ui.welcome_page import Welcome
from .alerts import beep
from .session_record import (
    AlertLog,
    build_session_metadata,
    check_output_writable,
    warn_on_shared_alert_sounds,
    write_session_metadata,
)
from .task import Task, task_param_based_on_screen
from .task_guiding import TaskGuiding

# Value of the `_profile` key marking a configuration as a placeholder rather
# than a research protocol. Carried in the file itself so a copy is still
# recognisable.
SMOKE_TEST_PROFILE = "smoke-test"


def default_output_dir() -> Path:
    """Where session output goes.

    Relative to the working directory, not to the package. Once installed as a
    dependency the package lives in site-packages, so anything resolved relative
    to it would write somewhere the operator never looks -- and, before this was
    fixed, somewhere outside the installation entirely.
    """
    return Path.cwd() / "data" / "memtest"


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
    alert_log=None,
    output_dir,
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
        score = task_obj.run_task(screen, alert_log=alert_log)
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
            beep("start_break", game_config, alert_log=alert_log)
            for _ in tqdm(iterable=range(wait_breaks), unit="s"):
                time.sleep(1)
            event_timestamps[f"{curr_break}_end"] = datetime.now()
            beep("end_break", game_config, alert_log=alert_log)
            print(
                f"Ending break {break_tally} at {event_timestamps.get(curr_break + '_end')}"
            )
    if save_gameplay_data:
        gameplay_data_df = pd.DataFrame(gameplay_data_list)
        # The caller's resolved output directory, not a freshly computed default:
        # the behavioural data and the sidecar that timestamps it belong together.
        output_dir.mkdir(parents=True, exist_ok=True)
        gameplay_data_df.to_csv(output_dir / f"{gameplay_data_file_name}.csv")
        gameplay_data_df.to_pickle(output_dir / f"{gameplay_data_file_name}.pkl")
    return score_list


def config_profile(config_path: Path) -> str | None:
    """Return the `_profile` marker from a config file, if it has one.

    Underscore-prefixed keys are metadata: both `from_dict` implementations read
    named keys and ignore the rest, so a marker costs nothing to carry.
    """
    try:
        with open(config_path, encoding="utf-8") as handle:
            return json.load(handle).get("_profile")
    except (OSError, json.JSONDecodeError):
        return None


def warn_if_smoke_test_config(config_path: Path) -> bool:
    """Announce, unmissably, that the protocol being run is a placeholder.

    The packaged default runs two trials with a five-second baseline so a fresh
    install can be verified in seconds. It also loads without complaint, which
    is the problem: a researcher who runs `memtest`, sees it work and starts
    collecting has run a protocol that is not a study, and may not notice until
    analysis. The failure mode is precisely someone who did not read the docs,
    so the signal has to be at run time.
    """
    if config_profile(config_path) != SMOKE_TEST_PROFILE:
        return False
    try:
        with open(config_path, encoding="utf-8") as handle:
            session = json.load(handle).get("session", {})
    except (OSError, json.JSONDecodeError):
        session = {}
    print(
        "=" * 72,
        "[SMOKE TEST] Running a placeholder protocol, NOT a research protocol",
        f"[SMOKE TEST]   config: {config_path}",
        f"[SMOKE TEST]   {session.get('num_trials', '?')} trials, "
        f"{session.get('wait_baseline', '?')}s baseline, "
        f"{session.get('wait_endline', '?')}s endline",
        "[SMOKE TEST] This exists to verify audio, display and output paths.",
        "[SMOKE TEST] For a real session, copy example-config.json, adapt it to",
        "[SMOKE TEST] your design, and run:",
        "[SMOKE TEST]   memtest --config my-protocol.json",
        "=" * 72,
        sep="\n",
    )
    return True


def _load_game_config(config_path: Path | None = None) -> GameConfig:
    """Load game configuration from JSON file or use defaults."""
    if config_path is None:
        config_path = CONFIG_DIR / "config.json"

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


def game_provider_rule_based(config_path=None, output_dir=None):
    """Run one session.

    `config_path` and `output_dir` come from the command line. They are real
    parameters rather than the `*args` this used to take, because a signature
    that accepted anything and used nothing is how `--output-dir` came to be
    honoured for the sidecar and ignored for the behavioural data.
    """
    if config_path is None:
        config_path = CONFIG_DIR / "config.json"
    if output_dir is None:
        output_dir = default_output_dir()

    event_timestamps = {}
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1920, 1080))
    screen_color = (211, 211, 211)
    screen.fill(screen_color)
    welcome_obj = Welcome(screen)
    welcome_obj.handler()
    screen.fill(screen_color)
    signup_page_obj = SignUp(screen, screen_color=screen_color, config_path=config_path)
    user_info, session_config = signup_page_obj.handler()
    game_config = _load_game_config(config_path)
    # Alerts double as synchronisation markers, so two raised alerts sharing a
    # sound would be indistinguishable in a recording. Surface that at load.
    warn_on_shared_alert_sounds(game_config)
    alert_log = AlertLog()
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
    beep("start_baseline", game_config, alert_log=alert_log)
    print(
        f"Starting {wait_baseline}-sec. baseline at {event_timestamps.get('baseline_start')}"
    )
    for _ in tqdm(range(wait_baseline), unit="s"):
        time.sleep(1)
    event_timestamps["baseline_end"] = datetime.now()
    print(f"Ending baseline at {event_timestamps.get('baseline_end')}")
    # Start game sound (before tasks begin)
    beep("start_game", game_config, alert_log=alert_log)
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
        alert_log=alert_log,
        output_dir=output_dir,
        session_config=session_config,
        game_config=game_config,
    )
    event_timestamps["endline_start"] = datetime.now()
    print(f"Starting endline at {event_timestamps.get('endline_start')}")
    beep("start_endline", game_config, alert_log=alert_log)
    for _ in tqdm(range(wait_endline), unit="s"):
        time.sleep(1)
    event_timestamps["endline_end"] = datetime.now()
    print(f"Ending endline at {event_timestamps.get('endline_end')}")
    # The only alert that must block: pygame.quit() below tears down the mixer
    # and would truncate playback.
    beep("end_game", game_config, wait=True, alert_log=alert_log)
    pygame.display.quit()
    pygame.quit()
    print(
        "\n".join(
            f"{k:<20}: {v.isoformat(sep=' ', timespec='milliseconds')}"
            for k, v in event_timestamps.items()
        )
    )
    return (
        score_list,
        user_info,
        session_config,
        game_config,
        event_timestamps,
        alert_log,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="memtest",
        description="Run a visual working memory session.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Protocol configuration file. Defaults to the packaged "
            "config.json, which is a smoke-test protocol, not a research one. "
            "Copy example-config.json, adapt it, and pass it here."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write session output. Defaults to ./data/memtest.",
    )
    parser.add_argument(
        "--allow-unwritable-output",
        action="store_true",
        help=(
            "Run even if the session metadata sidecar cannot be written. "
            "Recordings of the session will not be alignable to protocol time."
        ),
    )
    args = parser.parse_args(argv)

    # A typo'd --config must not silently fall back to the packaged default: that
    # would run the smoke-test protocol in place of the intended one, which looks
    # like a successful session and is not noticeable until analysis.
    if args.config is not None:
        config_path = Path(args.config)
        if not config_path.is_file():
            parser.exit(
                2,
                f"[ERROR] Configuration file not found: {config_path}\n"
                "Refusing to fall back to the packaged default, which is a "
                "smoke-test protocol rather than a research one.\n",
            )
    else:
        config_path = CONFIG_DIR / "config.json"

    # Keyed on the file's own `_profile` marker rather than on whether --config
    # was passed, so a copy of the smoke-test config is still flagged.
    is_smoke_test = warn_if_smoke_test_config(config_path)

    # Checked before a participant's time is spent, so an unusable output
    # location costs seconds rather than a whole session. Without the sidecar a
    # recording cannot be placed on protocol time, which usually makes the
    # session worthless for synchronised analysis -- so this blocks by default.
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    problem = check_output_writable(output_dir)
    if problem:
        if not args.allow_unwritable_output:
            parser.exit(
                2,
                f"[ERROR] Session metadata cannot be written ({problem}).\n"
                "Without it, recordings of this session cannot be aligned to "
                "protocol time.\nFix the output location, or re-run with "
                "--allow-unwritable-output to proceed anyway.\n",
            )
        print(
            "=" * 72,
            "[OVERRIDE] Running WITHOUT session metadata, by explicit request",
            "[OVERRIDE]   --allow-unwritable-output was passed",
            f"[OVERRIDE]   reason: {problem}",
            "[OVERRIDE] Recordings of this session will NOT be alignable to",
            "[OVERRIDE] protocol time. The audio configuration and alert",
            "[OVERRIDE] emission times will be lost when this process exits.",
            "=" * 72,
            sep="\n",
        )

    (
        score_list,
        user_info,
        session_config,
        game_config,
        event_timestamps,
        alert_log,
    ) = game_provider_rule_based(config_path=config_path, output_dir=output_dir)
    last = getattr(user_info, "last_name", "anon").strip().replace(" ", "_") or "anon"
    first = getattr(user_info, "name", "anon").strip().replace(" ", "_") or "anon"
    timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")

    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / f"{last}_{first}_{timestamp}_session.json"
    written = write_session_metadata(
        metadata_path,
        build_session_metadata(
            game_config=game_config,
            session_config=session_config,
            user_info=user_info,
            event_timestamps=event_timestamps,
            alert_log=alert_log,
            root=MEMTEST_DIR,
            config_source={
                "path": str(config_path),
                "profile": config_profile(config_path),
                "is_smoke_test": is_smoke_test,
            },
        ),
    )
    if written:
        print(f"[OK] Session metadata written to {written} ({len(alert_log)} alerts)")

    plt.plot(score_list)
    plt.title("your score graph")
    plt.xlabel("step")
    plt.ylabel("score")
    plt.savefig(output_dir / f"{last}_{first}_{timestamp}.png")
    plt.show()


if __name__ == "__main__":
    main()
