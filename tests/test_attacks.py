"""Attack injection: the modified stream must stay valid NMEA.

The point of these tests is that an injected attack has to be detected on its
merits. If the injector produced malformed sentences the parser would reject
them, and the evaluation would be measuring checksum validation rather than
spoofing detection.
"""

from __future__ import annotations

import pytest

from gpstrust.attacks import (
    all_scenarios,
    decimal_to_nmea,
    inject,
    nmea_to_decimal,
    position_jump,
    shift_time_field,
    snr_uniform,
    time_step,
)
from gpstrust.nmea import ParseStats, epochs_from_sentences, verify_checksum

from conftest import CLEAN_CYCLE, nmea


def trace(n_cycles: int = 20) -> list[str]:
    """A repeating clean cycle, long enough to have an attack window."""
    out = []
    for i in range(n_cycles):
        t = f"{12:02d}{35:02d}{(19 + i) % 60:02d}.00"
        out.append(nmea(f"GPGGA,{t},4807.0380,N,01131.0000,E,1,08,0.9,545.4,M,46.9,M,,"))
        out.append(nmea("GPGSA,A,3,04,05,09,12,24,,,,,,,,2.5,0.9,2.1"))
        out.append(nmea("GPGSV,2,1,08,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45"))
        out.append(nmea("GPGSV,2,2,08,15,60,058,43,17,10,148,38,18,82,113,47,20,25,033,40"))
        out.append(nmea(f"GPRMC,{t},A,4807.0380,N,01131.0000,E,0.06,84.4,230394,3.1,W"))
    return out


# --- coordinate helpers -----------------------------------------------------


def test_coordinate_roundtrip():
    for decimal, is_lat in [(48.1173, True), (-33.8688, True),
                            (11.51666, False), (-118.2437, False)]:
        value, direction = decimal_to_nmea(decimal, is_lat)
        back = nmea_to_decimal(value, direction)
        assert back == pytest.approx(decimal, abs=1e-6)


def test_latitude_and_longitude_keep_their_field_widths():
    """Degree digits are fixed by the standard; a different width is a different receiver."""
    lat, _ = decimal_to_nmea(8.5, True)
    lon, _ = decimal_to_nmea(8.5, False)
    assert lat.index(".") == 4     # ddmm.
    assert lon.index(".") == 5     # dddmm.


def test_time_shift_wraps_at_midnight():
    assert shift_time_field("235959.00", 2).startswith("000001")
    assert shift_time_field("000000.00", -1).startswith("235959")


def test_time_shift_preserves_fractional_part():
    assert shift_time_field("123519.25", 10) == "123529.25"


# --- injection --------------------------------------------------------------


@pytest.mark.parametrize("scenario", all_scenarios(), ids=lambda s: s.name)
def test_every_scenario_produces_valid_nmea(scenario):
    result = inject(trace(), scenario)
    for sentence in result.sentences:
        assert verify_checksum(sentence) is not False, sentence


@pytest.mark.parametrize("scenario", all_scenarios(), ids=lambda s: s.name)
def test_injection_does_not_reduce_parse_success(scenario):
    """A modified trace must parse as cleanly as the original."""
    clean_stats = ParseStats()
    list(epochs_from_sentences(trace(), clean_stats))

    result = inject(trace(), scenario)
    attacked_stats = ParseStats()
    list(epochs_from_sentences(result.sentences, attacked_stats))

    assert attacked_stats.ok == clean_stats.ok
    assert attacked_stats.bad == clean_stats.bad


def test_control_changes_nothing():
    sentences = trace()
    result = inject(sentences, all_scenarios()[0])
    assert result.sentences == sentences
    assert result.modified == 0
    assert not any(result.attack_flags)


def test_attack_only_touches_its_window():
    sentences = trace()
    result = inject(sentences, position_jump(5000))
    for original, modified, flagged in zip(sentences, result.sentences, result.attack_flags):
        if not flagged:
            assert modified == original


def test_position_jump_moves_the_reported_position():
    result = inject(trace(), position_jump(5000))
    epochs = list(epochs_from_sentences(result.sentences))
    before = [e for e in epochs[:5] if e.has_position]
    after = [e for e in epochs[-5:] if e.has_position]
    assert before and after
    assert abs(after[0].lat - before[0].lat) > 0.01


def test_time_step_shifts_only_the_clock():
    result = inject(trace(), time_step(60))
    epochs = [e for e in epochs_from_sentences(result.sentences) if e.utc]
    early, late = epochs[2], epochs[-2]
    # Position untouched...
    assert late.lat == pytest.approx(early.lat, abs=1e-9)
    # ...while the clock has moved by more than the elapsed cycles.
    elapsed = (late.utc - early.utc).total_seconds()
    assert elapsed > 60


def test_snr_uniform_flattens_the_constellation():
    result = inject(trace(), snr_uniform(44))
    epochs = list(epochs_from_sentences(result.sentences))
    attacked = [e for e in epochs[-3:] if len(e.snr) >= 4]
    assert attacked
    assert len(set(attacked[0].snr)) == 1


def test_attack_flags_mark_a_contiguous_window():
    result = inject(trace(40), position_jump())
    flags = result.attack_flags
    first = flags.index(True)
    last = len(flags) - 1 - flags[::-1].index(True)
    assert all(flags[first:last + 1])


def test_scenarios_declare_expectations():
    """Each scenario states what it should trigger, before results exist."""
    for scenario in all_scenarios():
        assert scenario.expect
        assert scenario.description
