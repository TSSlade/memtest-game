"""The alert sounds are synchronisation markers, so their separability is a
requirement rather than an aesthetic preference. These tests pin the properties
MODIFICATIONS.md claims, so that regenerating or retuning the assets cannot
quietly erode them.
"""

import wave

import pytest

from memtest.paths import ALERTS_DIR
from memtest.tools import generate_alerts as ga

# The worst pairwise correlation documented per register in MODIFICATIONS.md.
DOCUMENTED_WORST = {"warm": 0.041, "mid": 0.020, "bright": 0.008}

# Every register is meant to top out below this, to stay clear of the shrill
# region where hearing sensitivity is already falling away.
MAX_TONE_HZ = 1900


@pytest.mark.parametrize("register", sorted(ga.REGISTERS))
def test_worst_correlation_matches_documented_figure(register):
    """Separability must not regress past what the documentation promises."""
    worst = ga.worst_correlation(register)
    assert worst <= DOCUMENTED_WORST[register] + 0.0005, (
        f"{register} worst pairwise correlation is {worst:.4f}, "
        f"documented as {DOCUMENTED_WORST[register]}"
    )


@pytest.mark.parametrize("register", sorted(ga.REGISTERS))
def test_every_alert_pair_is_distinguishable(register):
    """No two alerts may be near-duplicates of each other.

    A previous asset set had two alerts using literally the same file, which put
    one alignment attempt 34 seconds out.
    """
    for (first, second), value in ga.pairwise_correlations(register).items():
        assert value < 0.2, f"{first} and {second} correlate at {value:.3f}"


@pytest.mark.parametrize("register", sorted(ga.REGISTERS))
def test_step_is_not_an_octave_subdivision(register):
    """The documented invariant: band spacing must not divide an octave evenly.

    Every alert carries energy at 2f. If the geometric step between bands is an
    exact octave subdivision -- 1.26 is 2**(1/3) and does exactly this -- then
    one alert's harmonic sits on another's fundamental however far apart their
    fundamentals look.
    """
    step = ga.REGISTERS[register]["step"]
    for power in range(1, len(ga.SLOTS)):
        ratio = step**power
        for octave in (2.0, 4.0):
            assert abs(ratio - octave) / octave > 0.03, (
                f"{register}: step**{power} = {ratio:.4f}, an octave "
                "subdivision, so harmonics stack across bands"
            )


def _closest_octave_deviation(register: str) -> float:
    """Smallest relative distance from any tone pair to a 2:1 or 4:1 ratio."""
    plan = ga.band_plan(register)
    tones = sorted({tone for pair in plan.values() for tone in pair})
    return min(
        abs(high / low - octave) / octave
        for index, low in enumerate(tones)
        for high in tones[index + 1 :]
        for octave in (2.0, 4.0)
    )


def test_default_register_has_no_near_octave_tone_pair():
    """`warm` is the default, so it is the one that must be clean."""
    assert _closest_octave_deviation("warm") > 0.02


@pytest.mark.parametrize("register", ["mid", "bright"])
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known deviation: step**2 * pair = 1.9803 in both registers, so "
        "end_break's second harmonic lands ~0.9% from end_game's upper tone. "
        "Measured correlation is nonetheless better than `warm`, and retuning "
        "would change already-shipped assets -- tracked, not silently fixed."
    ),
)
def test_alternate_registers_have_no_near_octave_tone_pair(register):
    assert _closest_octave_deviation(register) > 0.02


@pytest.mark.parametrize("register", sorted(ga.REGISTERS))
def test_register_stays_in_the_low_range(register):
    plan = ga.band_plan(register)
    highest = max(tone for pair in plan.values() for tone in pair)
    assert highest < MAX_TONE_HZ


@pytest.mark.parametrize("register", sorted(ga.REGISTERS))
def test_shipped_assets_reproduce_from_source(register, tmp_path):
    """The assets must actually be what the generator produces.

    MODIFICATIONS.md justifies generating the sounds rather than sourcing them
    partly on reproducibility. That claim is only worth anything if it is
    checked: an edited or stale .wav would otherwise be indistinguishable from a
    generated one.
    """
    ga.generate(tmp_path, [register])
    for slot in ga.SLOTS:
        shipped = ALERTS_DIR / register / f"{slot}.wav"
        regenerated = tmp_path / register / f"{slot}.wav"
        assert shipped.exists(), f"{shipped} is missing"
        assert shipped.read_bytes() == regenerated.read_bytes(), (
            f"{shipped} does not match what generate_alerts produces"
        )


@pytest.mark.parametrize("register", sorted(ga.REGISTERS))
def test_shipped_assets_are_mono_16bit_at_declared_rate(register):
    """Format is part of the contract: alignment tooling reads these directly."""
    for slot in ga.SLOTS:
        with wave.open(str(ALERTS_DIR / register / f"{slot}.wav")) as handle:
            assert handle.getnchannels() == 1
            assert handle.getsampwidth() == 2
            assert handle.getframerate() == ga.SAMPLE_RATE


def test_every_raised_alert_has_a_generated_sound():
    """The generator's slots and the alerts that can fire must not drift apart."""
    from memtest.game.session_record import RAISED_ALERTS

    assert set(RAISED_ALERTS) == set(ga.SLOTS)
