# Modifications

This is a fork of
[masoudrahimi39/visual-working-memory-game](https://github.com/masoudrahimi39/visual-working-memory-game),
taken at commit `646b46e381`. The original is MIT licensed and that licence is
retained unchanged in [LICENSE](LICENSE); all original copyright remains with
the upstream author.

The fork exists because the game is used as a stimulus task in a physiological
research protocol, which imposes requirements the original was never intended to
meet. It has diverged substantially and is not intended to track upstream.

## What changed, and why

### Package structure

The original was a flat directory of scripts. Code now lives under a single
`memtest/` package (`memtest/game/`, `memtest/ui/`, `memtest/config/`,
`memtest/user/`, `memtest/assets/`), installable with a `memtest` console
script.

The single top-level package matters: a flat layout would claim names like
`config`, `game` and `user` in site-packages, which collide with almost anything
installed alongside it. That made the package unusable as a dependency.

Session output is written relative to the working directory (`./data/memtest` by
default, overridable with `--output-dir`). It was previously resolved relative to
the package, which for an installed package would have written outside the
installation entirely.

### Configuration

Session and game parameters were hard-coded. They now load from JSON
(`config/config.json`, with `config/example-config.json` as a template), backed
by dataclasses with defaults. This lets a protocol be specified without editing
source.

### Protocol phases

The original ran a continuous sequence of trials. The task now supports a
structured protocol: a timed baseline, blocks of trials separated by timed
breaks, and a timed endline. Phase boundaries are timestamped.

### Audio alerts

Alerts mark each protocol phase transition. They serve two purposes:

1. telling the participant that a phase has changed;
2. acting as **synchronisation markers**.

The second is the demanding one. Sessions are recorded by cameras whose clocks
have no relationship to the task machine's, and which cannot be started
simultaneously. Matching these sounds in a camera's audio track is how a
recording is placed on protocol time.

That constraint shapes the sound design, which is documented in
[`tools/generate_alerts.py`](tools/generate_alerts.py). In short: every alert
occupies its own frequency band so that no two correlate, and band spacing
avoids octave relationships so that one alert's harmonics do not land on
another's fundamental.

Three registers are provided under `assets/alerts/`, all topping out below
1.9 kHz:

| register | range | worst pairwise correlation |
| --- | --- | --- |
| `warm` (default) | 247–1018 Hz | 0.041 |
| `mid` | 262–1437 Hz | 0.020 |
| `bright` | 330–1810 Hz | 0.008 |

Lower correlation means two alerts are harder to confuse when matching audio.
Switching register is a path change in the configuration.

The sounds are **generated**, not sourced, so the repository carries no
third-party audio licence and the assets are reproducible from source:

```bash
python tools/generate_alerts.py
```

### Session metadata

Each run writes a sidecar `<subject>_<timestamp>_session.json` alongside its
other output, recording:

- the resolved audio mapping, with a SHA-256 of every asset, so the record does
  not depend on the config file or the assets staying unchanged;
- which alert fired and when;
- protocol phase timestamps and the session configuration.

This exists so a recording carries its own answer to "which sound marked which
event" — without it, aligning a camera to protocol time depends on reconstructing
a mapping that may since have changed.

Alert timestamps are *intended* emission times: the moment `beep()` was called,
not the moment sound left the speaker. See `game/session_record.py` for why, and
what that costs.

Configuration is also checked at load: two raised alerts sharing a sound cannot
be told apart in a recording, and that now warns.

## Known gaps

- `tools/generate_alerts.py` is a repository script and is not shipped in the
  installed package.
- The gap between intended and actual emission time is unmeasured.
