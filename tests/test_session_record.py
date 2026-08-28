"""The sidecar is what makes a recording alignable to protocol time, so its
shape is a contract rather than incidental telemetry.
"""

import json
from datetime import datetime

from memtest.config.game_config import GameConfig
from memtest.config.session_config import SessionConfig
from memtest.game.session_record import (
    RAISED_ALERTS,
    SCHEMA_VERSION,
    AlertLog,
    build_session_metadata,
    resolve_audio_config,
    sha256_of,
    write_session_metadata,
)
from memtest.paths import ALERTS_DIR, MEMTEST_DIR


class _Subject:
    name = "Ada"
    last_name = "Lovelace"


def _payload(alert_log=None, config_source=None):
    return build_session_metadata(
        game_config=GameConfig(),
        session_config=SessionConfig(),
        user_info=_Subject(),
        event_timestamps={"baseline_start": datetime.now()},
        alert_log=alert_log or AlertLog(),
        root=MEMTEST_DIR,
        config_source=config_source,
    )


def test_payload_carries_the_expected_top_level_keys():
    expected = {
        "schema_version",
        "written_at",
        "config_source",
        "subject",
        "session_config",
        "audio",
        "event_timestamps",
        "alert_emissions",
        "notes",
    }
    assert set(_payload()) == expected


def test_schema_version_is_recorded():
    assert _payload()["schema_version"] == SCHEMA_VERSION


def test_every_alert_asset_carries_a_hash():
    """The record must not depend on the config file or assets staying put."""
    audio = resolve_audio_config(GameConfig(), MEMTEST_DIR)
    assert set(audio["alerts"]) >= set(RAISED_ALERTS)
    for alert, entry in audio["alerts"].items():
        assert entry["exists"] is True, f"{alert} resolves to a missing file"
        assert entry["sha256"], f"{alert} has no content hash"
        assert entry["raised_by_task"] is True


def test_sha256_of_missing_file_returns_none(tmp_path):
    """A missing asset must degrade to None rather than aborting the write."""
    assert sha256_of(tmp_path / "absent.wav") is None


def test_sha256_matches_the_shipped_asset():
    import hashlib

    path = ALERTS_DIR / "warm" / "start_game.wav"
    assert sha256_of(path) == hashlib.sha256(path.read_bytes()).hexdigest()


def test_recorded_alerts_appear_in_the_payload():
    log = AlertLog()
    log.record("start_baseline", ALERTS_DIR / "warm" / "start_baseline.wav")
    log.record("end_game", ALERTS_DIR / "warm" / "end_game.wav")

    emissions = _payload(alert_log=log)["alert_emissions"]
    assert [entry["alert"] for entry in emissions] == ["start_baseline", "end_game"]
    for entry in emissions:
        assert entry["intended_at"]
        assert entry["audio_file"]


def test_task_complete_emissions_are_recorded():
    """Regression: task_complete used to play without reaching the sidecar.

    It fires after every task, making it the most frequent sound in a session
    and the one most likely to be met when matching a recording's audio track.
    """
    log = AlertLog()
    log.record("task_complete", ALERTS_DIR / "warm" / "task_complete.wav")

    emissions = _payload(alert_log=log)["alert_emissions"]
    assert [entry["alert"] for entry in emissions] == ["task_complete"]


def test_notes_preserve_the_intended_emission_caveat():
    """Timestamps are when beep() was called, not when sound left the speaker.

    Losing this note would imply a precision the data does not have.
    """
    assert "intended emission times" in _payload()["notes"]["alert_timestamps"]


def test_config_source_records_the_protocol_that_ran():
    source = {"path": "/tmp/protocol.json", "profile": None, "is_smoke_test": False}
    assert _payload(config_source=source)["config_source"] == source


def test_config_source_defaults_to_empty_rather_than_missing():
    assert _payload()["config_source"] == {}


def test_write_session_metadata_round_trips(tmp_path):
    path = write_session_metadata(tmp_path / "nested" / "session.json", _payload())
    assert path is not None
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == (
        SCHEMA_VERSION
    )


def test_write_session_metadata_reports_failure_rather_than_raising(tmp_path):
    """Failure is reported so the caller can decide; it must not raise."""
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    assert write_session_metadata(blocker / "session.json", _payload()) is None
