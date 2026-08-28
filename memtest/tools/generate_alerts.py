"""Generate the protocol alert sounds.

The alerts serve two purposes. The obvious one is telling the participant that
a phase of the protocol has changed. The less obvious one is that each alert is
a *synchronisation marker*: sessions are recorded by cameras whose clocks have
no relationship to the task laptop's, and matching these sounds in a camera's
audio track is how a recording gets placed on protocol time.

That second role drives the design:

* **Every alert gets its own frequency band.** Two alerts that share frequency
  content correlate with each other, and an analysis matching audio against
  them cannot tell which one it found. A previous asset set had two alerts using
  literally the same file, which put one alignment attempt 34 seconds out.
* **Bands avoid octave relationships.** Each tone carries a second harmonic at
  2f, so if band spacing is an exact octave subdivision the harmonic of one
  alert lands on the fundamental of another. A geometric step of 1.26 is
  2**(1/3) and does exactly this; the steps below are chosen to miss it.
* **The range stays low.** Stacking seven separable bands naively pushes the
  last ones past 5 kHz, which is shrill and sits where hearing sensitivity is
  already falling away. All three registers here top out below 1.9 kHz.

Sounds are generated rather than sourced so that the repository carries no
third-party audio licence, and so the exact assets are reproducible from source
rather than being opaque binaries.

Usage::

    python -m memtest.tools.generate_alerts                 # all registers
    python -m memtest.tools.generate_alerts --register warm # just one

Writes into the package's own asset directory by default, which is what
regenerating in a source checkout wants. An installed copy is normally not
writable, so `--out` is required there; the error says so.
"""

import argparse
import os
import wave
from pathlib import Path

import numpy as np

from ..paths import ALERTS_DIR

SAMPLE_RATE = 48_000
DURATION_S = 0.45

# Order matters: bands are assigned in sequence, so this is also the pitch order
# a listener hears across a session.
SLOTS = (
    "start_baseline",
    "start_game",
    "start_break",
    "end_break",
    "start_endline",
    "end_game",
    "task_complete",
)

# base: fundamental of the first alert, in Hz
# step: geometric ratio between consecutive alerts' bands
# pair: ratio between the two tones within one alert
REGISTERS = {
    "warm": {"base": 247, "step": 1.22, "pair": 1.25},
    "mid": {"base": 262, "step": 1.29, "pair": 1.19},
    "bright": {"base": 330, "step": 1.29, "pair": 1.19},
}


def band_plan(register: str) -> dict[str, tuple[int, int]]:
    """Return the (low, high) tone pair for each alert in `register`."""
    cfg = REGISTERS[register]
    plan = {}
    for index, slot in enumerate(SLOTS):
        low = cfg["base"] * cfg["step"] ** index
        plan[slot] = (round(low), round(low * cfg["pair"]))
    return plan


def _envelope(length: int, attack_s: float = 0.005, release_s: float = 0.30):
    """Fast attack, long decaying release, so the onset is sharp in time."""
    attack = int(attack_s * SAMPLE_RATE)
    release = int(release_s * SAMPLE_RATE)
    env = np.ones(length)
    env[:attack] = np.linspace(0, 1, attack)
    env[-release:] = np.linspace(1, 0, release) ** 2.2
    return env


def render(low_hz: float, high_hz: float, duration_s: float = DURATION_S):
    """Render one alert: two struck tones, the second entering halfway."""
    length = int(SAMPLE_RATE * duration_s)
    time = np.linspace(0, duration_s, length, endpoint=False)
    offset = length // 2
    out = np.zeros(length)
    for index, freq in enumerate((low_hz, high_hz)):
        start = index * offset
        tail = time[: length - start]
        tone = np.sin(2 * np.pi * freq * tail) + 0.25 * np.sin(
            2 * np.pi * 2 * freq * tail
        )
        voice = np.zeros(length)
        voice[start:] = tone * np.exp(-6 * tail)
        out += voice
    return out * _envelope(length)


def write_wav(path: Path, samples) -> None:
    """Write mono 16-bit PCM, peak-normalised with headroom."""
    peak = np.abs(samples).max()
    scaled = samples / peak * 0.85 if peak else samples
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes((scaled * 32767).astype("<i2").tobytes())


def generate(out_root: Path, registers: list[str]) -> None:
    for register in registers:
        plan = band_plan(register)
        for slot, (low, high) in plan.items():
            write_wav(out_root / register / f"{slot}.wav", render(low, high))
        tones = sorted({f for pair in plan.values() for f in pair})
        print(f"{register:7s} {len(plan)} alerts  {tones[0]}-{tones[-1]} Hz")


def unwritable_reason(out_root: Path) -> str | None:
    """Return why `out_root` cannot be written to, or None if it can.

    Checked up front so an installed, read-only copy fails with an instruction
    rather than part-way through writing a register.
    """
    probe = out_root
    while not probe.exists():
        if probe.parent == probe:
            return f"no existing parent directory for {out_root}"
        probe = probe.parent
    if not probe.is_dir():
        return f"{probe} is not a directory"
    if not os.access(probe, os.W_OK):
        return f"{probe} is not writable"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--register",
        choices=sorted(REGISTERS),
        action="append",
        help="Register to generate; repeatable. Defaults to all.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ALERTS_DIR,
        help=(
            "Output root; one subdirectory per register. Defaults to the "
            "package's own asset directory, which is only writable in a "
            "source checkout."
        ),
    )
    args = parser.parse_args()
    problem = unwritable_reason(args.out)
    if problem:
        parser.exit(
            2,
            f"[ERROR] Cannot write alerts to {args.out} ({problem}).\n"
            "Pass --out with a writable directory, then point the alert paths "
            "in your config file at it.\n",
        )
    generate(args.out, args.register or sorted(REGISTERS))


if __name__ == "__main__":
    main()
