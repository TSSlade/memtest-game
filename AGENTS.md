# Agent instructions

Read and follow [`CONSTITUTION.md`](CONSTITUTION.md) (Clanker Constitution
v2026.08.11) as the baseline for how to work in this repository. It is an
unchanged mirror of an upstream release, pinned to a tag — do not edit it in
place. To adopt a newer release, copy the new tag's file wholesale and update
the version reference here.

The instructions below are specific to this project and override the
Constitution where they conflict.

## What this repository is

A fork of
[masoudrahimi39/visual-working-memory-game](https://github.com/masoudrahimi39/visual-working-memory-game)
adapted to serve as a stimulus task in a physiological research protocol.
[`MODIFICATIONS.md`](MODIFICATIONS.md) explains what diverged from upstream and
why — **read it before changing anything under `memtest/game/` or
`memtest/assets/`.** It records reasoning that is not recoverable from the code.

Two consequences worth stating plainly:

- **The fork does not track upstream, and is not trying to.** Do not "restore"
  upstream behaviour, re-add upstream files, or treat divergence as drift to be
  corrected.
- **A ruined session cannot be re-run.** Participants are scheduled, wired to
  instruments, and recorded once. A bug that silently produces unusable data is
  far more costly here than a crash, which is at least visible. Prefer failing
  loudly and early over degrading quietly.

## Invariants

These encode the reasons the fork exists. Breaking one produces data that looks
fine and is not.

### Alerts are synchronisation markers, not UI feedback

Sessions are recorded by cameras whose clocks have no relationship to the task
machine's. Matching the alert sounds in a camera's audio track is how a
recording is placed on protocol time. That is the entire reason the sounds are
designed rather than chosen.

- Every alert occupies its own frequency band, and band spacing avoids octave
  relationships so one alert's harmonics do not land on another's fundamental.
- Do not add, re-map, re-order, or regenerate alert sounds without re-checking
  pairwise correlation. `memtest/tools/generate_alerts.py` is the source of
  truth for the sound design and computes those figures.
- Assets are **generated, not sourced**, so the repository carries no
  third-party audio licence and the sounds are reproducible from source. Do not
  introduce a downloaded or bundled third-party sound.

### Every raised alert goes through `beep()`, with `alert_log` passed

`beep()` in `memtest/game/alerts.py` is the only sanctioned way to emit an
alert. It resolves the path, honours the volume and enable flags, and — given
`alert_log` — records the emission so it reaches the session sidecar. It lives in
its own module because both `main_game` and `task` call it and `main_game`
imports `task`; that is what keeps every emission on one code path.

An inline `pygame.mixer.Sound(...).play()` at a call site is a bug, not a
shortcut: the sound reaches the recording while the sidecar has no record of
it, which is precisely the state that makes an audio track unmatchable.

Any alert that can fire must also appear in `RAISED_ALERTS`
(`memtest/game/session_record.py`), because the shared-sound collision check
filters on it. An alert that fires but is absent from that tuple gets no
collision checking at all.

`beep()` does not block by default, and that is deliberate — blocking would
delay the protocol and make a timestamp taken after the call mean something
different from one taken before it. Use `wait=True` only where the process is
about to cut playback short, such as mixer shutdown.

### The session sidecar is required output, not telemetry

`<subject>_<timestamp>_session.json` is what lets a recording be aligned to
protocol time. Without it the session is generally worthless for synchronised
analysis, which is why a missing or unwritable sidecar aborts the run unless
`--allow-unwritable-output` is passed explicitly.

Treat its schema as a contract. Alert timestamps in it are *intended* emission
times — the moment `beep()` was called, not the moment sound left the speaker.
`memtest/game/session_record.py` documents why and what that costs; preserve
that distinction rather than quietly implying more precision than exists.

### Package reads from the package; writes go to the working directory

- Config and assets are read from inside the `memtest` package.
- Session output resolves relative to the **working directory** (`./data/memtest`
  by default, overridable with `--output-dir`). Nothing is ever written into the
  package — for an installed copy that would mean writing into site-packages.
- A protocol is specified with `--config`, never by editing a file inside the
  package.
- All of a session's outputs belong in one directory. If you add an output file,
  route it through the resolved `output_dir` rather than recomputing a default
  at the write site.

### One top-level package

Everything lives under `memtest/`. A flat layout would claim top-level names
like `config`, `game` and `user` in site-packages, colliding with almost
anything installed alongside it and making the package unusable as a
dependency. Do not reintroduce top-level modules, and use relative imports
(`..config.game_config`) within the package — including inside
`TYPE_CHECKING` blocks, which type checkers do resolve.

## Working in this repository

### Environment

Use `uv` — not `python -m venv` and `pip`. The project requires **Python 3.14**
and installs editable with its dev extras:

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -e . --group dev
```

The dependency is **`pygame-ce`**, not `pygame`: only pygame-ce publishes CPython
3.14 wheels. The two provide the same `pygame` module and cannot coexist, so do
not add `pygame` to any requirement list, and uninstall it if an environment
already has it.

Because the floor is 3.14, PEP 649 deferred annotation evaluation is available:
a class may refer to itself in its own method annotations without quoting. Do not
reintroduce string forward references.

### Checks

Run all of these before reporting a change complete:

```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check . \
  && .venv/bin/codespell && .venv/bin/pytest
```

Note `ruff format --check`, not a bare `ruff format`. The rewriting form cannot
fail, so using it as a gate enforces nothing — in CI its edits are discarded with
the runner. Run `ruff format .` to fix, `--check` to verify.

All configuration — packaging, dependencies, `ruff` and `pytest` — lives in
`pyproject.toml`. There is no `setup.py`, `pytest.ini` or `ruff.toml`; do not
reintroduce them. Dev tooling is a PEP 735 dependency group, not an extra, so it
is installed with `--group dev` rather than `.[dev]`.

`uv.lock` is committed. The install command above does not consume it, so CI runs
`uv lock --check` to stop it drifting; if you change dependencies, run `uv lock`
in the same change. To reproduce the exact locked environment instead of
resolving fresh:

```bash
uv sync --group dev
```

The same two checks run in GitHub Actions on every push, alongside a job
asserting that the built wheel actually contains the alert sounds, the guide
image and the config files — each of those has silently gone missing from a
build before.

A pre-push hook is available for the same checks locally. It is opt-in per
clone:

```bash
git config core.hooksPath .githooks
```

### Tests

`tests/` covers the properties above — alert signal separation, config
integrity, sidecar schema, and output-path resolution. Driving the pygame UI is
deliberately out of scope.

Note that `test_rule_base.csv` / `test_rule_base.pkl` at the repository root are
**not tests** — they are DDA rule-base data inherited from upstream. The name is
misleading; leave them alone.

### Documentation

`README.md` retains upstream's text below a marked line **for attribution
only**. It is not maintained as a description of current behaviour. Do not
treat it as a specification, and do not leave content in it that contradicts
the code — fork-current usage belongs in the fork's own section above that
line.

When you change a path, a flag, or an output file, update `MODIFICATIONS.md` in
the same change. Its accuracy is load-bearing: it is the only record of *why*
the design is what it is.
