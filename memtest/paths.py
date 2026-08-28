"""Locations inside the installed package.

These resolve relative to the package, and are for **reading** only -- config
and bundled assets. Session output must never be resolved this way: once
installed, the package lives in site-packages, so anything written here lands
somewhere the operator never looks. See `game.main_game.default_output_dir` for
where output goes.

Defined in one place because three modules had grown their own copy of the same
`Path(__file__).parent.parent` expression, which is how `guide_en.png` came to
be loaded from a directory it had never been in.
"""

from pathlib import Path

# The `memtest` package root.
MEMTEST_DIR = Path(__file__).resolve().parent

ASSETS_DIR = MEMTEST_DIR / "assets"
ALERTS_DIR = ASSETS_DIR / "alerts"
CONFIG_DIR = MEMTEST_DIR / "config"
