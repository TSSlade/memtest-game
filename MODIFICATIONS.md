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
`memtest/user/`, `memtest/assets/`, `memtest/tools/`), installable with a
`memtest` console script.

The single top-level package matters: a flat layout would claim names like
`config`, `game` and `user` in site-packages, which collide with almost anything
installed alongside it. That made the package unusable as a dependency.

Package-relative locations are defined once, in `memtest/paths.py`, and are for
reading only — bundled assets and config. Three modules had each grown their own
copy of the same `Path(__file__).parent.parent` expression, which is how the
participant guide image came to be loaded from a directory it had never been in.

Session output is written relative to the working directory (`./data/memtest` by
default, overridable with `--output-dir`). It was previously resolved relative to
the package, which for an installed package would have written outside the
installation entirely. All of a session's output goes to that one directory: the
behavioural data and the sidecar that timestamps it are of little use apart.

### Configuration

Session and game parameters were hard-coded. They now load from JSON, backed by
dataclasses with defaults, and a protocol is selected with `--config` so that
specifying one never means editing source — or, for an installed copy, editing
site-packages.

`memtest/config/example-config.json` is the template to copy. The packaged
`memtest/config/config.json` is deliberately a **smoke-test** protocol: two
trials and a five-second baseline, so a fresh install can be verified in seconds
rather than making the first run a ten-minute commitment. Because a placeholder
that loads without complaint is easy to collect data against by accident, it
carries a `_profile` marker, announces itself with a banner at startup, and is
flagged in the session sidecar. Keys beginning with an underscore are metadata
and are ignored by the loaders.

A `--config` path that does not exist is an error rather than a fallback:
silently running the smoke-test protocol in place of the intended one looks like
a successful session and would not be noticed until analysis.

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
[`memtest/tools/generate_alerts.py`](memtest/tools/generate_alerts.py). In short:
every alert occupies its own frequency band so that no two correlate, and band
spacing avoids octave relationships so that one alert's harmonics do not land on
another's fundamental.

Three registers are provided under `memtest/assets/alerts/`, all topping out
below 1.9 kHz:

| register | range | worst pairwise correlation | clearance from nearest octave |
| --- | --- | --- | --- |
| `warm` (default) | 247–1029 Hz | 0.0265 | 4.05% |
| `mid` | 262–1422 Hz | 0.0191 | 3.99% |
| `bright` | 330–1791 Hz | 0.0129 | 4.05% |

Lower correlation means two alerts are harder to confuse when matching audio.
Switching register is a path change in the configuration.

The clearance column is the distance from the nearest 2:1 or 4:1 tone pair to
that exact ratio, and it exists because the first version of these registers got
it wrong. `mid` and `bright` originally sat 0.9% from a 2:1 relationship —
`step**2 * pair` came to 1.9803, a route to octave stacking the original spacing
rule did not consider — so one alert's second harmonic landed about 10 Hz from
another's upper tone. All three registers were retuned; nothing had yet been
recorded against the old assets.

Perfect avoidance is not achievable: 14 tones inside a 7.7x span leave a mean
neighbouring ratio near 1.17, so every tone's double falls close to some other
tone. About 4% is the practical optimum under these range constraints, against
roughly 4.8% if the spread between registers were given up. The parameters were
chosen by search, and the test suite pins both this clearance and the
correlations above.

The sounds are **generated**, not sourced, so the repository carries no
third-party audio licence and the assets are reproducible from source:

```bash
python -m memtest.tools.generate_alerts
```

The generator ships with the package, so an installed copy can be checked
against its own source rather than the reproducibility claim above holding only
for a checkout. The test suite asserts that the shipped assets are byte-for-byte
what it produces. Writing into the package needs a source checkout; elsewhere,
pass `--out`.

### Session metadata

Each run writes a sidecar `<subject>_<timestamp>_session.json` alongside its
other output, recording:

- the resolved audio mapping, with a SHA-256 of every asset, so the record does
  not depend on the config file or the assets staying unchanged;
- which alert fired and when;
- protocol phase timestamps and the session configuration;
- which configuration file the session ran from, and whether it was the
  smoke-test placeholder, so such a run is identifiable in a data directory
  instead of looking like a real but oddly short session.

This exists so a recording carries its own answer to "which sound marked which
event" — without it, aligning a camera to protocol time depends on reconstructing
a mapping that may since have changed.

Alert timestamps are *intended* emission times: the moment `beep()` was called,
not the moment sound left the speaker. See `memtest/game/session_record.py` for
why, and what that costs.

Every alert is emitted through `beep()`, which is the only place an emission gets
recorded. An alert played directly at a call site reaches the recording while the
sidecar has no record of it — which is precisely the state that makes an audio
track unmatchable — so `memtest/game/alerts.py` holds `beep()` for both its
callers rather than either one having its own copy.

Configuration is also checked at load: two raised alerts sharing a sound cannot
be told apart in a recording, and that now warns. The check covers every alert
that can fire, including `task_complete`, which fires after every task and is
therefore the most frequent sound in a session.

## Known gaps

- The gap between intended and actual emission time is unmeasured. This bounds
  the achievable alignment accuracy and is the most consequential item here.
- The task supports an eye tracker, but `is_eye_tracker` is hard-coded to
  `False` at the call site, so that path is never exercised.
