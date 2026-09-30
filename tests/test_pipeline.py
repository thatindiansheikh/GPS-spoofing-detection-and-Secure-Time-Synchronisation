"""The assembled system, and the event log.

These are the tests that would catch a demonstration drifting away from the
thing that was evaluated: the dashboard and the command line both drive
Pipeline, so if it behaves differently from the evaluation, it shows here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gpstrust.config import Calibration, FeatureCalibration
from gpstrust.nmea.epoch import Epoch
from gpstrust.pipeline import Pipeline, summarise
from gpstrust.store import EventStore
from gpstrust.timesource import ActiveSource, FixedReference

REF_LAT, REF_LON = 48.1173, 11.5167
T0 = datetime(2025, 9, 15, 12, 0, 0, tzinfo=timezone.utc)


def feat(name, direction, warn, alarm):
    return FeatureCalibration(name=name, direction=direction, warn=warn,
                              alarm=alarm, median=0.0, robust_sigma=1.0)


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
            "hdop": feat("hdop", "high", 2.0, 5.0),
            "pdop": feat("pdop", "high", 3.0, 6.0),
            "sats_in_view": feat("sats_in_view", "low", 6.0, 3.0),
            "snr_mean": feat("snr_mean", "high", 44.0, 54.0),
            "snr_cv": feat("snr_cv", "low", 0.05, 0.02),
        },
        corpus={},
    )


def clean_epoch(i: int, lat=REF_LAT, lon=REF_LON) -> Epoch:
    return Epoch(
        utc=T0 + timedelta(seconds=i), lat=lat, lon=lon, time_source="gps",
        fix_quality=1, sats_in_view=10, hdop=0.9, pdop=1.2, sog_knots=0.0,
        snr=[30, 36, 41, 28, 44, 33],
    )


def test_clean_stream_keeps_gps(cal):
    ref = FixedReference(uncertainty=0.02)
    p = Pipeline(calibration=cal, reference=ref)
    steps = []
    for i in range(30):
        ref.set((T0 + timedelta(seconds=i)).timestamp())
        steps.append(p.step(clean_epoch(i), host_time=(T0 + timedelta(seconds=i)).timestamp()))
    assert all(s.decision.source is ActiveSource.GPS for s in steps)
    assert all(not s.fired for s in steps)
    assert summarise(steps)["min_trust"] == 1.0


def test_spoofed_time_is_not_served(cal):
    """The whole point: a spoofed clock must not reach the output.

    The clean run is long enough for the holdover anchor to be confirmed
    before the attack starts. That matters - an attack arriving before the
    system has earned a trustworthy anchor leaves it with nothing to fall back
    to, which is covered separately in test_timesource.py.
    """
    ref = FixedReference(uncertainty=0.02)
    p = Pipeline(calibration=cal, reference=ref)
    for i in range(60):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        p.step(clean_epoch(i), host_time=host)

    last = None
    for i in range(60, 120):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        spoofed = clean_epoch(i)
        spoofed.utc = T0 + timedelta(seconds=i + 600)   # receiver claims +10 min
        last = p.step(spoofed, host_time=host)

    assert last.decision.source is not ActiveSource.GPS
    # Served time follows real elapsed time, not the receiver's +600 s claim.
    expected = (T0 + timedelta(seconds=119)).timestamp()
    assert abs(last.decision.time_s - expected) < 40


def test_position_spoof_triggers_failover(cal):
    ref = FixedReference(uncertainty=0.02)
    p = Pipeline(calibration=cal, reference=ref)
    for i in range(40):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        p.step(clean_epoch(i), host_time=host)
    last = None
    for i in range(40, 100):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        last = p.step(clean_epoch(i, lat=REF_LAT + 0.02), host_time=host)
    assert last.decision.source is not ActiveSource.GPS
    assert any(e.detector == "position_deviation" for e in last.fired)


def test_pipeline_reports_skipped_detectors(cal):
    """A detector that could not be calibrated is visibly absent, not silently zero."""
    reduced = Calibration(
        ref_lat=REF_LAT, ref_lon=REF_LON, nominal_median_m=2.0,
        nominal_robust_sigma_m=2.0,
        features={k: v for k, v in cal.features.items() if not k.startswith("snr")},
        corpus={},
    )
    p = Pipeline(calibration=reduced)
    names = [d.name for d in p.detectors]
    assert "snr_power" not in names
    assert "snr_uniformity" not in names
    assert set(p.status()["detectors_skipped"]) >= {"snr_power", "snr_uniformity"}


# --- event log --------------------------------------------------------------


def test_store_records_epochs_and_only_firing_detectors(tmp_path, cal):
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.start_run(source="test")
    ref = FixedReference(uncertainty=0.02)
    p = Pipeline(calibration=cal, reference=ref, store=store)
    for i in range(10):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        p.step(clean_epoch(i), host_time=host)
    store.commit()

    assert len(store.recent_epochs()) == 10
    # Nothing fired, so nothing should be in the detections table.
    assert store.recent_detections() == []
    store.close()


def test_store_keeps_both_clocks(tmp_path, cal):
    """A log timestamped only by GPS would be timestamped by the attacker."""
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.start_run()
    ref = FixedReference(uncertainty=0.02)
    p = Pipeline(calibration=cal, reference=ref, store=store)

    host = T0.timestamp()
    ref.set(host)
    spoofed = clean_epoch(0)
    spoofed.utc = T0 + timedelta(days=365)
    p.step(spoofed, host_time=host)
    store.commit()

    row = store.recent_epochs()[0]
    assert row["host_time"] == pytest.approx(host)
    assert row["gps_time"] != pytest.approx(host)
    store.close()


def test_store_records_source_changes(tmp_path, cal):
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.start_run()
    ref = FixedReference(uncertainty=0.02)
    p = Pipeline(calibration=cal, reference=ref, store=store)
    # Shorter confirmation so the test does not need 30 warm-up epochs before
    # it can observe a failover; the window itself is tested in test_timesource.
    p.manager.anchor_confirm_epochs = 3
    for i in range(20):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        p.step(clean_epoch(i), host_time=host)
    for i in range(20, 70):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        p.step(clean_epoch(i, lat=REF_LAT + 0.02), host_time=host)
    store.commit()

    events = store.source_events()
    # The reference is reachable here, so rejecting GPS must hand over to it
    # rather than drop straight to the local oscillator.
    assert any(e["to_source"] == "ntp" for e in events)
    assert all(e["reason"] for e in events)
    store.close()


def test_failover_reaches_holdover_when_reference_is_down(tmp_path, cal):
    """With no reachable reference, the last leg of the chain must be taken."""
    store = EventStore(tmp_path / "events.db")
    store.start_run()
    ref = FixedReference(uncertainty=0.02, available=False)
    p = Pipeline(calibration=cal, reference=ref, store=store)
    p.manager.anchor_confirm_epochs = 3
    for i in range(20):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        p.step(clean_epoch(i), host_time=host)
    for i in range(20, 70):
        host = (T0 + timedelta(seconds=i)).timestamp()
        ref.set(host)
        p.step(clean_epoch(i, lat=REF_LAT + 0.02), host_time=host)
    store.commit()

    events = store.source_events()
    assert any(e["to_source"] == "holdover" for e in events)
    assert not any(e["to_source"] == "ntp" for e in events)
    store.close()
