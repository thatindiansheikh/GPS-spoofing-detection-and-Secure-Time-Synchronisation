"""Detector behaviour, against a synthetic calibration.

The calibration here is fabricated on purpose: these tests check the detection
logic, not the real thresholds. Whether the measured thresholds are sensible is
a question for the evaluation, not for a unit test.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gpstrust.config import Calibration, FeatureCalibration
from gpstrust.detect import (
    DilutionDetector,
    PositionDeviationDetector,
    SatelliteCountDetector,
    SnrPowerDetector,
    SnrUniformityDetector,
    TimeOffsetDetector,
    TrajectoryDetector,
    VelocityConsistencyDetector,
)
from gpstrust.nmea.epoch import Epoch

REF_LAT, REF_LON = 69.275374, 15.967894


def feat(name, direction, warn, alarm):
    return FeatureCalibration(
        name=name, direction=direction, warn=warn, alarm=alarm,
        median=0.0, robust_sigma=1.0,
    )


@pytest.fixture
def cal():
    return Calibration(
        ref_lat=REF_LAT, ref_lon=REF_LON,
        nominal_median_m=2.0, nominal_robust_sigma_m=2.0,
        features={
            "position_deviation_m": feat("position_deviation_m", "high", 10.0, 20.0),
            "jump_m": feat("jump_m", "high", 5.0, 50.0),
            "implied_speed_mps": feat("implied_speed_mps", "high", 5.0, 50.0),
            "speed_excess_mps": feat("speed_excess_mps", "high", 1.0, 10.0),
            "hdop": feat("hdop", "high", 1.0, 3.0),
            "pdop": feat("pdop", "high", 1.5, 4.0),
            "sats_in_view": feat("sats_in_view", "low", 9.0, 5.0),
            "snr_mean": feat("snr_mean", "high", 44.0, 54.0),
            "snr_cv": feat("snr_cv", "low", 0.05, 0.02),
        },
        corpus={},
    )


def ep(lat=REF_LAT, lon=REF_LON, t=0.0, **kw):
    base = datetime(2025, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    kw.setdefault("time_source", "gps")
    return Epoch(utc=base + timedelta(seconds=t), lat=lat, lon=lon, **kw)


# --- position ---------------------------------------------------------------


def test_position_quiet_at_reference(cal):
    d = PositionDeviationDetector(cal, window=5)
    for i in range(10):
        e = d.update(ep(t=i))
    assert e.score == 0.0
    assert e.applicable


def test_position_fires_on_sustained_displacement(cal):
    d = PositionDeviationDetector(cal, window=5)
    # ~0.001 deg latitude is about 111 m, far beyond the 20 m alarm point.
    for i in range(10):
        e = d.update(ep(lat=REF_LAT + 0.001, t=i))
    assert e.score == 1.0


def test_position_ignores_a_single_outlier(cal):
    """A one-epoch multipath excursion is not an attack.

    This is the whole reason the detector uses a rolling median rather than the
    instantaneous value.
    """
    d = PositionDeviationDetector(cal, window=5)
    for i in range(5):
        d.update(ep(t=i))
    e = d.update(ep(lat=REF_LAT + 0.01, t=5))  # single ~1.1 km spike
    assert e.score == 0.0
    assert e.detail["instantaneous_m"] > 1000


def test_position_not_applicable_without_a_fix(cal):
    d = PositionDeviationDetector(cal)
    e = d.update(Epoch(utc=datetime.now(timezone.utc)))
    assert not e.applicable


# --- trajectory and velocity ------------------------------------------------


def test_trajectory_needs_a_previous_fix(cal):
    d = TrajectoryDetector(cal)
    assert not d.update(ep(t=0)).applicable


def test_trajectory_fires_on_teleport(cal):
    d = TrajectoryDetector(cal)
    d.update(ep(t=0))
    e = d.update(ep(lat=REF_LAT + 0.05, t=1))  # ~5.5 km in one second
    assert e.score == 1.0


def test_trajectory_refuses_across_a_logging_gap(cal):
    """A gap is a discontinuity, not motion."""
    d = TrajectoryDetector(cal)
    d.update(ep(t=0))
    e = d.update(ep(lat=REF_LAT + 0.05, t=3600))
    assert not e.applicable
    assert "discontinuity" in e.reason


def test_velocity_flags_movement_the_receiver_denies(cal):
    d = VelocityConsistencyDetector(cal)
    d.update(ep(t=0, sog_knots=0.0))
    e = d.update(ep(lat=REF_LAT + 0.001, t=1, sog_knots=0.0))  # ~111 m/s claimed still
    assert e.score == 1.0


def test_velocity_quiet_when_speed_matches_motion(cal):
    d = VelocityConsistencyDetector(cal)
    d.update(ep(t=0, sog_knots=20.0))
    # 20 kn is ~10.3 m/s; move roughly that far in one second.
    e = d.update(ep(lat=REF_LAT + 0.0000925, t=1, sog_knots=20.0))
    assert e.score == 0.0


# --- satellites and dilution ------------------------------------------------


def test_satellite_count_fires_when_satellites_vanish(cal):
    d = SatelliteCountDetector(cal)
    assert d.update(ep(sats_in_view=11)).score == 0.0
    assert d.update(ep(sats_in_view=4)).score == 1.0


def test_dilution_sentinel_is_maximum_evidence_not_a_large_dop(cal):
    d = DilutionDetector(cal)
    e = d.update(ep(hdop=500.0))
    assert e.score == 1.0
    assert e.detail.get("sentinel") is True


def test_dilution_quiet_in_normal_range(cal):
    d = DilutionDetector(cal)
    assert d.update(ep(hdop=0.8, pdop=1.1)).score == 0.0


# --- SNR --------------------------------------------------------------------


def test_snr_power_fires_when_spoofer_outshouts_the_sky(cal):
    d = SnrPowerDetector(cal)
    assert d.update(ep(snr=[36, 38, 40, 35, 37])).score == 0.0
    assert d.update(ep(snr=[54, 55, 56, 54, 55])).score == 1.0


def test_snr_uniformity_fires_on_a_flat_constellation(cal):
    d = SnrUniformityDetector(cal)
    varied = d.update(ep(snr=[22, 31, 38, 45, 29, 41]))
    flat = d.update(ep(snr=[44, 44, 45, 44, 45, 44]))
    assert varied.score == 0.0
    assert flat.score == 1.0


def test_snr_detectors_abstain_on_too_few_satellites(cal):
    """Two satellites can look uniform by chance; that is not evidence."""
    for det in (SnrPowerDetector(cal), SnrUniformityDetector(cal)):
        e = det.update(ep(snr=[40, 40]))
        assert not e.applicable


def test_untracked_satellites_do_not_drag_the_statistics(cal):
    """Zero-SNR entries are absent, not zero: including them would invert the signal."""
    d = SnrUniformityDetector(cal)
    e = d.update(ep(snr=[44, 44, 45, 44, 45, 44, 0, 0]))
    assert e.score == 1.0


# --- time offset ------------------------------------------------------------


class FakeReference:
    def __init__(self, t, uncertainty=0.05):
        self._t = t
        self._u = uncertainty

    def now(self):
        return self._t

    @property
    def uncertainty_s(self):
        return self._u


def test_time_offset_refuses_host_receive_timestamps():
    """The limitation is enforced in code, not only documented."""
    base = datetime(2025, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    d = TimeOffsetDetector(FakeReference(base.timestamp()))
    e = d.update(Epoch(utc=base, lat=REF_LAT, lon=REF_LON, time_source="host_receive"))
    assert not e.applicable
    assert "host_receive" in e.reason


def test_time_offset_quiet_when_clocks_agree():
    base = datetime(2025, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    d = TimeOffsetDetector(FakeReference(base.timestamp()))
    e = d.update(ep(t=0))
    assert e.applicable and e.score == 0.0


def test_time_offset_fires_on_a_large_shift():
    base = datetime(2025, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    d = TimeOffsetDetector(FakeReference(base.timestamp()))
    for i in range(10):
        e = d.update(ep(t=30))  # receiver claims 30 s ahead of reference
    assert e.score == 1.0
    assert e.value == pytest.approx(30.0, abs=0.5)


def test_time_offset_respects_reference_uncertainty():
    """Nothing can be claimed below the reference's own accuracy."""
    base = datetime(2025, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    d = TimeOffsetDetector(FakeReference(base.timestamp(), uncertainty=5.0))
    for i in range(10):
        e = d.update(ep(t=3))
    assert e.score == 0.0


def test_time_offset_not_applicable_without_a_reference():
    d = TimeOffsetDetector(FakeReference(None))
    e = d.update(ep(t=0))
    assert not e.applicable
