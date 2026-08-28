"""Shared test setup.

Importing `memtest.game.main_game` pulls in pygame, which will try to open a
window and an audio device. The dummy drivers are selected here -- before any
test module imports anything -- so the suite runs headless and on machines with
no sound card.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest  # noqa: E402

from memtest.paths import MEMTEST_DIR  # noqa: E402

REPO_ROOT = MEMTEST_DIR.parent


@pytest.fixture
def repo_root():
    """The repository root, for checks on files that are not packaged."""
    return REPO_ROOT
