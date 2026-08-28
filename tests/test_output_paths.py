"""Output must land where the operator expects, all of it in one place.

These are pure path checks, deliberately free of pygame.
"""

import inspect
import os
from pathlib import Path

from memtest.game import main_game
from memtest.game.session_record import check_output_writable
from memtest.paths import ASSETS_DIR, CONFIG_DIR, MEMTEST_DIR


def test_default_output_dir_is_relative_to_the_working_directory(tmp_path, monkeypatch):
    """Never package-relative: an installed package lives in site-packages."""
    monkeypatch.chdir(tmp_path)
    assert main_game.default_output_dir() == tmp_path / "data" / "memtest"


def test_default_output_dir_is_never_inside_the_package(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert MEMTEST_DIR not in main_game.default_output_dir().parents


def test_gameplay_data_uses_the_caller_supplied_output_dir():
    """Regression: the gameplay CSV/PKL once ignored --output-dir.

    It called default_output_dir() at the write site, so passing --output-dir
    split one session's data across two directories -- separating the
    behavioural data from the sidecar that timestamps it.
    """
    signature = inspect.signature(main_game.dda_rule_based)
    assert "output_dir" in signature.parameters

    source = inspect.getsource(main_game.dda_rule_based)
    assert "default_output_dir()" not in source


def test_session_provider_takes_config_and_output_dir():
    """It used to take *args and use none of them."""
    parameters = inspect.signature(main_game.game_provider_rule_based).parameters
    assert set(parameters) == {"config_path", "output_dir"}


def test_check_output_writable_accepts_a_usable_directory(tmp_path):
    assert check_output_writable(tmp_path / "fresh") is None


def test_check_output_writable_rejects_an_unusable_directory(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    assert check_output_writable(blocker / "under-a-file") is not None


def test_check_output_writable_leaves_no_probe_behind(tmp_path):
    target = tmp_path / "clean"
    assert check_output_writable(target) is None
    assert list(target.iterdir()) == []


def test_package_paths_point_inside_the_package():
    for path in (ASSETS_DIR, CONFIG_DIR):
        assert MEMTEST_DIR in path.parents or path.parent == MEMTEST_DIR
        assert path.is_dir()


def test_package_read_locations_are_not_write_targets(tmp_path, monkeypatch):
    """The package is read from; output goes to the working directory."""
    monkeypatch.chdir(tmp_path)
    output = main_game.default_output_dir()
    assert os.path.commonpath([str(output), str(MEMTEST_DIR)]) != str(MEMTEST_DIR)


def test_guide_asset_is_where_the_ui_loads_it_from():
    """Regression: the guide was loaded from a directory it had never been in."""
    from memtest.ui import demo_page

    source = inspect.getsource(demo_page)
    assert "guide_en.png" in source
    assert (ASSETS_DIR / "guide_en.png").is_file()


def test_alert_paths_in_defaults_resolve_against_the_package():
    from memtest.config.game_config import GameConfig

    for alert, relative in GameConfig().audio_files.items():
        assert not Path(relative).is_absolute(), f"{alert} is absolute"
        assert (MEMTEST_DIR / relative).is_file(), f"{alert} -> {relative}"
