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

The original was a flat directory of scripts. Code is now organised into
`game/`, `ui/`, `config/`, `user/` and `assets/`, with a `setup.py` so the task
can be installed and launched as a package rather than run from its own
directory.

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

## Known gaps

- The effective audio configuration is not yet written into session output, so a
  recording does not carry a record of which sounds marked its phases. Alert
  emission times are printed to the console but not persisted.
- `task_complete` has a configured sound but is not raised by any call site.
- Nothing validates that a configuration maps each alert to a distinct sound.
