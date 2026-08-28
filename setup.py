from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="memtest-game",
    version="0.2.0",
    description=(
        "Visual working memory task adapted for physiological research: "
        "structured protocol phases, and audio alerts usable as camera "
        "synchronisation markers."
    ),
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/TSSlade/memtest-game",
    # Everything lives under the single `memtest` package. A flat layout would
    # claim top-level names like `config`, `game` and `user` in site-packages,
    # which collide with almost anything else installed alongside it.
    packages=find_packages(include=["memtest", "memtest.*"]),
    include_package_data=True,
    package_data={
        "memtest": ["assets/alerts/*/*.wav", "assets/*.png", "config/*.json"]
    },
    python_requires=">=3.9",
    install_requires=[
        "pygame>=2.1.2",
        "pandas",
        "numpy",
        "matplotlib",
        "tqdm",
    ],
    # Declared so lint and test tooling is shared rather than per-machine.
    # Install with: uv pip install -e ".[dev]"
    extras_require={"dev": ["pytest", "ruff"]},
    entry_points={"console_scripts": ["memtest = memtest.game.main_game:main"]},
    # Forked from masoudrahimi39/visual-working-memory-game at 646b46e381.
    # Original copyright retained in LICENSE; see MODIFICATIONS.md for the
    # nature and extent of the divergence.
    author="Timothy Slade",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research",
    ],
)
