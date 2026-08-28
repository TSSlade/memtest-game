"""Session metadata sidecar.

A session's score output records what the participant did. It does not record
how the run was *configured*, and that gap matters because the audio alerts
double as synchronisation markers: sessions are filmed by cameras whose clocks
bear no relation to this machine's, and matching alert sounds in a camera's
audio track is how a recording gets placed on protocol time.

That only works if the analysis knows which sound marked which event. The
mapping lives in code and config files that change independently of the data, so
a recording captured under one mapping can be analysed months later under
another. This module writes the mapping — and the times alerts fired — into a
sidecar file alongside the session's other output, so a recording carries its
own answer.

Assets are recorded with a content hash as well as a path, because a filename
does not guarantee the file's contents.

Known limitation -- intended versus actual emission time
--------------------------------------------------------
`AlertLog.record` stores the moment `beep()` was *called*, not the moment sound
reached the speaker. Those differ by the audio stack's buffer latency, typically
single-digit to low-tens of milliseconds, and that offset is systematic rather
than random.

Intended time is used deliberately: it is simple, it needs no callback from the
mixer, and the residual error is one to two orders of magnitude below the
alignment tolerance these markers exist to serve (RSA epochs are 15 seconds, so
alignment good to roughly 0.1-1 s suffices). Anyone doing sub-100 ms work with
these timestamps should know the bias is there and unmeasured.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

# 2 adds `config_source`, recording which configuration file a session ran from
# and whether it was the smoke-test placeholder.
SCHEMA_VERSION = 2

# Every alert that can actually fire. Validation filters on this, so an alert
# that fires without being listed here gets no collision checking at all --
# which is how `task_complete` went unchecked while firing once per task.
RAISED_ALERTS = (
    "start_baseline",
    "start_game",
    "start_break",
    "end_break",
    "start_endline",
    "end_game",
    "task_complete",
)


def sha256_of(path: Path) -> str | None:
    """Return the SHA-256 of a file, or None if it cannot be read."""
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def resolve_audio_config(game_config, root: Path) -> dict:
    """Describe the audio configuration as it will actually be used.

    Paths are resolved the way `beep()` resolves them, and each asset carries a
    content hash, so the record does not depend on the config file or the asset
    directory staying unchanged.
    """
    alerts = {}
    for alert, configured in game_config.audio_files.items():
        path = Path(configured)
        resolved = path if path.is_absolute() else root / path
        alerts[alert] = {
            "configured_path": str(configured),
            "resolved_path": str(resolved),
            "exists": resolved.exists(),
            "sha256": sha256_of(resolved),
            "raised_by_task": alert in RAISED_ALERTS,
        }
    return {
        "enabled": bool(game_config.enable_audio_alerts),
        "volume": game_config.volume,
        "alerts": alerts,
    }


def find_shared_alert_sounds(game_config) -> dict[str, list[str]]:
    """Return sounds mapped to more than one *raised* alert.

    Two raised alerts sharing a sound cannot be told apart in a recording, which
    makes them useless as distinct synchronisation markers.

    Only alerts in `RAISED_ALERTS` are considered, since a sound that never
    plays cannot be confused with anything. Keep that tuple honest: an alert
    omitted from it while still firing is checked by nothing.
    """
    by_sound: dict[str, list[str]] = {}
    for alert, path in game_config.audio_files.items():
        if alert in RAISED_ALERTS:
            by_sound.setdefault(str(path), []).append(alert)
    return {sound: alerts for sound, alerts in by_sound.items() if len(alerts) > 1}


def warn_on_shared_alert_sounds(game_config) -> bool:
    """Print a warning for any sound shared between raised alerts.

    Returns True when the configuration is clean.
    """
    shared = find_shared_alert_sounds(game_config)
    for sound, alerts in shared.items():
        print(
            f"[WARNING] {' and '.join(alerts)} share the sound {sound}. "
            "They cannot be distinguished in a recording, so they will not work "
            "as separate synchronisation markers."
        )
    return not shared


class AlertLog:
    """Record which alert fired and when.

    Timestamps are intended emission times; see the module docstring.
    """

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def record(self, alert: str, audio_file: Path | None) -> None:
        self._entries.append(
            {
                "alert": alert,
                "intended_at": datetime.now().isoformat(timespec="milliseconds"),
                "audio_file": str(audio_file) if audio_file else None,
            }
        )

    @property
    def entries(self) -> list[dict]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


def check_output_writable(directory: Path) -> str | None:
    """Return a human-readable reason the directory is unusable, or None.

    Called before a session starts, so an unwritable output location is found
    before a participant's time is spent rather than after.
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".memtest_write_probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return None
    except OSError as error:
        return f"{directory}: {error}"


def build_session_metadata(
    *,
    game_config,
    session_config,
    user_info,
    event_timestamps: dict,
    alert_log: AlertLog,
    root: Path,
    config_source: dict | None = None,
) -> dict:
    """Assemble the sidecar payload.

    `config_source` records which configuration file the session ran from and
    whether it was a placeholder, so a smoke-test run is identifiable in a data
    directory instead of looking like a real but oddly short session.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "written_at": datetime.now().isoformat(timespec="milliseconds"),
        "config_source": config_source or {},
        "subject": {
            "name": getattr(user_info, "name", None),
            "last_name": getattr(user_info, "last_name", None),
        },
        "session_config": (
            session_config.to_dict() if hasattr(session_config, "to_dict") else {}
        ),
        "audio": resolve_audio_config(game_config, root),
        "event_timestamps": {
            key: value.isoformat(timespec="milliseconds")
            for key, value in event_timestamps.items()
        },
        "alert_emissions": alert_log.entries,
        "notes": {
            "alert_timestamps": (
                "intended emission times -- the moment beep() was called, not "
                "the moment sound left the speaker; see game/session_record.py"
            )
        },
    }


def write_session_metadata(path: Path, payload: dict) -> Path | None:
    """Write the sidecar as JSON. Returns the path, or None on failure."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
    except OSError as error:
        print(f"[ERROR] Could not write session metadata to {path}: {error}")
        return None
