"""Configuration failures are the cheap ones to catch and the expensive ones to
miss: they cost a whole session, and the session looks fine while it happens.
"""

import json

import pytest

from memtest.config.game_config import GameConfig
from memtest.config.session_config import SessionConfig
from memtest.game.main_game import (
    SMOKE_TEST_PROFILE,
    _load_game_config,
    config_profile,
    main,
)
from memtest.game.session_record import (
    RAISED_ALERTS,
    find_shared_alert_sounds,
    warn_on_shared_alert_sounds,
)
from memtest.paths import CONFIG_DIR, MEMTEST_DIR

SHIPPED_CONFIGS = ("config.json", "example-config.json")


@pytest.mark.parametrize("name", SHIPPED_CONFIGS)
def test_shipped_config_alert_paths_resolve(name):
    """Every configured sound must exist, in both shipped configurations."""
    data = json.loads((CONFIG_DIR / name).read_text(encoding="utf-8"))
    audio_files = data["game"]["audio_files"]
    assert audio_files, f"{name} declares no alert sounds"
    for alert, relative in audio_files.items():
        assert (MEMTEST_DIR / relative).is_file(), f"{name}: {alert} -> {relative}"


@pytest.mark.parametrize("name", SHIPPED_CONFIGS)
def test_shipped_config_covers_every_raised_alert(name):
    data = json.loads((CONFIG_DIR / name).read_text(encoding="utf-8"))
    assert set(data["game"]["audio_files"]) >= set(RAISED_ALERTS)


@pytest.mark.parametrize("name", SHIPPED_CONFIGS)
def test_shipped_config_has_no_shared_alert_sounds(name):
    config = _load_game_config(CONFIG_DIR / name)
    assert find_shared_alert_sounds(config) == {}


def test_collision_between_raised_alerts_is_detected():
    """Two raised alerts on one sound are indistinguishable in a recording."""
    config = GameConfig()
    config.audio_files = dict(config.audio_files)
    config.audio_files["start_break"] = config.audio_files["end_break"]

    shared = find_shared_alert_sounds(config)
    assert shared, "a shared sound between two raised alerts was not reported"
    assert sorted(next(iter(shared.values()))) == ["end_break", "start_break"]
    assert warn_on_shared_alert_sounds(config) is False


def test_task_complete_collision_is_detected():
    """Regression: task_complete fires, so it must be collision-checked.

    While it was absent from RAISED_ALERTS, a config pointing it at a phase
    marker's sound passed validation silently and then fired on the recording.
    """
    config = GameConfig()
    config.audio_files = dict(config.audio_files)
    config.audio_files["task_complete"] = config.audio_files["end_game"]

    shared = find_shared_alert_sounds(config)
    assert "task_complete" in next(iter(shared.values()))


def test_from_dict_uses_defaults_for_missing_keys():
    game = GameConfig.from_dict({})
    session = SessionConfig.from_dict({})
    assert game.num_hexagons == GameConfig().num_hexagons
    assert session.num_trials == SessionConfig().num_trials


def test_from_dict_ignores_unknown_keys():
    """The smoke-test marker relies on unknown keys being harmless."""
    game = GameConfig.from_dict({"_comment": "hi", "volume": 0.25})
    session = SessionConfig.from_dict({"_profile": "x", "num_trials": 7})
    assert game.volume == 0.25
    assert session.num_trials == 7


def test_custom_config_file_is_honoured(tmp_path):
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps({"game": {"num_hexagons": 24, "volume": 0.9}}), encoding="utf-8")
    config = _load_game_config(path)
    assert (config.num_hexagons, config.volume) == (24, 0.9)


def test_missing_config_aborts_rather_than_falling_back(tmp_path):
    """A typo'd --config must not silently run the smoke-test protocol.

    Falling back would look like a successful session and go unnoticed until
    analysis.
    """
    with pytest.raises(SystemExit) as excinfo:
        main(["--config", str(tmp_path / "nope.json")])
    assert excinfo.value.code == 2


def test_packaged_default_is_marked_as_a_smoke_test():
    assert config_profile(CONFIG_DIR / "config.json") == SMOKE_TEST_PROFILE


def test_example_config_is_not_marked_as_a_smoke_test():
    """The template a researcher copies must not carry the placeholder marker."""
    assert config_profile(CONFIG_DIR / "example-config.json") is None


def test_smoke_test_marker_does_not_reach_signup_defaults():
    """Session defaults become text boxes, so a stray key would show up as one."""
    from memtest.ui.sign_up_page import SignUp

    defaults = SignUp._load_session_defaults(SignUp.__new__(SignUp), CONFIG_DIR / "config.json")
    assert not any(key.startswith("_") for key in defaults)
    assert set(defaults) == set(SessionConfig().to_dict())
