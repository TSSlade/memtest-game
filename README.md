# memtest-game

> **A fork of [masoudrahimi39/visual-working-memory-game](https://github.com/masoudrahimi39/visual-working-memory-game)**,
> taken at commit `646b46e381` and MIT licensed by the original author.
>
> This fork adapts the task for use as a stimulus in a physiological research
> protocol: structured baseline / block / break / endline phases, JSON-driven
> configuration, and audio alerts that double as camera synchronisation markers.
> It has diverged substantially and does not track upstream.
>
> See **[MODIFICATIONS.md](MODIFICATIONS.md)** for what changed and why.

A visual working memory task. A hexagonal grid briefly highlights a set of
target cells; the participant then recalls and clicks them. Difficulty adapts to
performance. This fork wraps that task in a timed protocol and emits audio
alerts at each phase boundary so a session can be aligned to camera recordings
afterwards.

## Installation

Requires **Python 3.14 or newer**.

```bash
pip install .
```

For development, using [uv](https://docs.astral.sh/uv/):

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -e . --group dev
```

### A note on pygame

This depends on **`pygame-ce`**, not `pygame`. They are a fork and its upstream,
they both provide the `pygame` module, and **they cannot coexist in one
environment** — if upstream `pygame` is already installed, uninstall it first or
which module wins is undefined:

```bash
pip uninstall pygame
```

The reason is Python 3.14: upstream `pygame` publishes wheels only up to CPython
3.13, so installing it on 3.14 falls back to building from source and needs SDL
development headers. `pygame-ce` ships 3.14 wheels. Nothing in the code changes —
`import pygame` still works.

## Running a session

```bash
memtest
```

That runs the **packaged smoke-test protocol** — two trials, a five-second
baseline — which exists so you can confirm audio, display and output paths work
before a participant is in the chair. It is not a research protocol, and it
announces itself as such at startup.

To run a real protocol, copy the template, adapt it to your design, and pass it
in:

```bash
cp memtest/config/example-config.json my-protocol.json
memtest --config my-protocol.json
```

Do not edit `memtest/config/config.json` instead. Once installed, that file
lives inside the package, so edits are lost on reinstall and are invisible to
anyone reading your protocol.

### Options

| flag | effect |
| --- | --- |
| `--config PATH` | Protocol configuration file. Defaults to the packaged smoke-test config. A path that does not exist is an error, not a fallback. |
| `--output-dir PATH` | Where session output goes. Defaults to `./data/memtest`, relative to the working directory. |
| `--allow-unwritable-output` | Run even if the session metadata sidecar cannot be written. See the warning below. |

### What a session writes

All of it into one directory:

| file | contents |
| --- | --- |
| `<subject>_<timestamp>_session.json` | Session metadata sidecar: resolved audio mapping with per-asset hashes, alert emission times, protocol phase timestamps, configuration, and which config file was used |
| `memtest_output.csv` / `.pkl` | Trial-level behavioural data |
| `<subject>_<timestamp>.png` | Score graph |

**The sidecar is required output, not telemetry.** It is what lets a recording
be placed on protocol time; without it a session is generally unusable for
synchronised analysis. That is why a missing or unwritable sidecar aborts the
run, and why overriding it with `--allow-unwritable-output` prints a warning
rather than proceeding quietly.

## Alert sounds

Three registers ship under `memtest/assets/alerts/` — `warm` (default), `mid`
and `bright`. Switching register is a path change in the configuration file.

The sounds are generated rather than sourced, so the repository carries no
third-party audio licence and the assets are reproducible from source:

```bash
python -m memtest.tools.generate_alerts
```

Their frequency separation is a requirement rather than a preference — see
[MODIFICATIONS.md](MODIFICATIONS.md) before changing any of it.

## Development

```bash
.venv/bin/ruff check . && .venv/bin/pytest
```

Both run in CI on every push, along with a check that the built wheel contains
the alert sounds, the guide image and the config files. To run them locally
before each push as well:

```bash
git config core.hooksPath .githooks
```

[AGENTS.md](AGENTS.md) records the invariants this code has to preserve, and is
worth reading before changing the protocol, the alerts or the sidecar.

## Licence

MIT, retained from upstream — see [LICENSE](LICENSE). All original copyright
remains with the upstream author.

---

## Upstream README

Retained for attribution, to signal the original author's intent for the
project. It is **not** documentation for this fork.

Sections covering installation, module layout, imports and configuration have
been removed rather than preserved verbatim, because they describe the
pre-fork code and would actively mislead: the paths, the run command and the
configuration mechanism have all changed. What remains is the original
description of the task itself.

> ### Visual working memory game
>
> If you find this repo helpful, please consider giving it a ⭐ to show your support.
>
> #### Demo
>
> https://user-images.githubusercontent.com/65596290/178737195-80565633-60ce-4d58-8590-a0c315346da4.mp4
>
> #### Usage
>
> This project serves multiple purposes:
>
> 1. **Entertainment**: Play the game for fun and test your visual working memory abilities.
> 2. **Gameplay and Eye Tracker Data Collection**: The game collects and saves the player's gameplay data, along with eye tracker data when enabled, providing valuable insights for research and analysis.
>
> #### Features
>
> - **Rule-Based Difficulty Adjustment**: The game incorporates a rule-based difficulty adjustment system, ensuring that players are appropriately challenged as they progress through the tasks.
> - **Data Storage**: The player's gameplay data is saved in CSV and plk (Pandas DataFrames) files, facilitating data analysis and post-game insights.
> - **Structured User Journey**: The task follows a well-structured user journey, guiding players through different pages, including "Welcome," "Sign Up," "Guiding," "Guiding trials," and "Actual Trials."
>
> #### About the memory game?
>
> - At the beginning, a 6*6 hexagonal grid is displayed for two seconds, with certain hexagons simultaneously highlighted in yellow (known as "targets") while the rest are white.
> - After two seconds, all the hexagons become white, and the player must recall and click on the exact locations of the targets.
> - Correct and incorrect clicks instantly become green and red, respectively.
> - The player's score is the number of correct clicks divided by the total number of targets in the task.
> - A score 1 represents a win, whereas other scores represent a loss.
