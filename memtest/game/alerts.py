"""Alert emission.

`beep()` lives here rather than in `main_game` because it has two callers --
the protocol phase transitions in `main_game`, and per-task completion in
`task` -- and `main_game` imports `task`. Sharing it through this module keeps
every emission on one code path without an import cycle.

That single code path matters. An alert that is played directly at a call site
reaches the recording while the session sidecar has no record of it, which is
exactly the state that makes an audio track unmatchable to protocol time.
"""

import time

import pygame

from ..paths import MEMTEST_DIR


def beep(alert, game_config, wait: bool = False, alert_log=None) -> None:
    """Play the alert sound for `alert`.

    Returns as soon as playback starts. `pygame`'s `Sound.play()` is already
    asynchronous; blocking for the sound's duration would delay the protocol by
    several seconds per alert and, worse, make an event timestamp taken after
    the call mean something different from one taken before it.

    Pass `wait=True` only where the process is about to do something that would
    cut playback short, such as shutting down the mixer.

    When `alert_log` is given, the emission is recorded so the session's sidecar
    carries which alert fired and when. The timestamp is the intended emission
    time -- see `game.session_record` for why, and what that costs.
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
    if alert_log is not None:
        alert_log.record(alert, audio_file)
    sound.play()
    if wait:
        time.sleep(sound.get_length())
