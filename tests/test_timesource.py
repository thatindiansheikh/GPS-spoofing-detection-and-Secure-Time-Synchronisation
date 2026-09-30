"""Holdover and source selection.

No test here touches the network. NTP behaviour is exercised through injected
state rather than live queries, so the suite stays deterministic and runs
offline.
"""

from __future__ import annotations

import pytest

from gpstrust.timesource import ActiveSource, HoldoverClock, TimeSourceManager
from gpstrust.timesource.ntp import MIN_UNCERTAINTY_S
from gpstrust.trust import SourceState, TrustVerdict

T0 = 1_700_000_000.0


def verdict(state: SourceState, trust: float = 1.0) -> TrustVerdict:
    return TrustVerdict(
        trust=trust, state=state, anomaly=1 - trust,
        contributions={}, applicable=["position_deviation"],
        inapplicable={}, reasons=[],
    )


# --- holdover ---------------------------------------------------------------


def test_undisciplined_clock_reports_nothing():
    clock = HoldoverClock()
    assert clock.now() is None
    assert clock.uncertainty_s == float("inf")
    assert not clock.disciplined


def test_holdover_extrapolates_from_the_anchor():
    clock = HoldoverClock()
    clock.discipline(T0, 0.01, host_time=1000.0)
    assert clock.now(host_time=1060.0) == pytest.approx(T0 + 60.0)


def test_uncertainty_grows_with_elapsed_holdover():
    clock = HoldoverClock(oscillator="tcxo")  # 1 ppm
    clock.discipline(T0, 0.0, host_time=0.0)
    # 1 ppm over one day is about 86 ms.
    assert clock.uncertainty_at(86400.0) == pytest.approx(0.0864, abs=1e-4)


def test_better_oscillator_holds_longer():
    tcxo, ocxo = HoldoverClock("tcxo"), HoldoverClock("ocxo")
    for c in (tcxo, ocxo):
        c.discipline(T0, 0.0, host_time=0.0)
    assert ocxo.uncertainty_at(3600.0) < tcxo.uncertainty_at(3600.0)


def test_time_until_a_tolerance_is_exceeded():
    clock = HoldoverClock(oscillator="tcxo")
    clock.discipline(T0, 0.0, host_time=0.0)
    # 128 ms at 1 ppm is 128,000 seconds.
    assert clock.seconds_until(0.128, host_time=0.0) == pytest.approx(128_000, rel=1e-3)


def test_already_exceeded_tolerance_reports_zero():
    clock = HoldoverClock()
    clock.discipline(T0, 1.0, host_time=0.0)
    assert clock.seconds_until(0.128, host_time=0.0) == 0.0


# --- source selection -------------------------------------------------------


def test_gps_used_while_trusted():
    mgr = TimeSourceManager()
    d = mgr.update(verdict(SourceState.TRUSTED), gps_time=T0, host_time=1000.0)
    assert d.source is ActiveSource.GPS
    assert d.time_s == T0


def test_suspect_still_serves_gps_but_is_flagged():
    """Suspect means degraded, not rejected; dropping a source too eagerly is its own outage."""
    mgr = TimeSourceManager()
    d = mgr.update(verdict(SourceState.SUSPECT, 0.85), gps_time=T0, host_time=1000.0)
    assert d.source is ActiveSource.GPS


def test_untrusted_gps_falls_back_to_holdover_without_ntp():
    mgr = TimeSourceManager(anchor_confirm_epochs=3)
    for i in range(10):
        mgr.update(verdict(SourceState.TRUSTED), gps_time=T0 + i, host_time=1000.0 + i)
    d = mgr.update(verdict(SourceState.UNTRUSTED, 0.2), gps_time=T0 + 500, host_time=1010.0)
    assert d.source is ActiveSource.HOLDOVER
    # The spoofed GPS time is not served.
    assert d.time_s == pytest.approx(T0 + 10.0, abs=1.0)


def test_holdover_ignores_the_spoofed_time_entirely():
    mgr = TimeSourceManager(anchor_confirm_epochs=3)
    for i in range(10):
        mgr.update(verdict(SourceState.TRUSTED), gps_time=T0 + i, host_time=float(i))
    d = mgr.update(verdict(SourceState.UNTRUSTED, 0.1), gps_time=T0 + 86400, host_time=60.0)
    assert abs(d.time_s - (T0 + 60)) < 2.0


def test_holdover_anchor_is_withheld_until_confirmed():
    """No anchor exists until GPS has been trusted for the confirmation window.

    Serving nothing is the correct answer here. The system has not yet observed
    enough trusted operation to know that the time it was given was genuine.
    """
    mgr = TimeSourceManager(anchor_confirm_epochs=30)
    for i in range(5):
        mgr.update(verdict(SourceState.TRUSTED), gps_time=T0 + i, host_time=float(i))
    d = mgr.update(verdict(SourceState.UNTRUSTED, 0.1), gps_time=None, host_time=5.0)
    assert d.source is ActiveSource.NONE
    assert not d.usable


def test_anchor_is_not_poisoned_during_detection_latency():
    """The failure this whole mechanism exists to prevent.

    Detection is not instantaneous. If holdover anchored on every accepted
    epoch, the epochs accepted while the detector was still smoothing would
    copy the attacker's clock into the fallback, and rejecting GPS would
    achieve nothing.
    """
    mgr = TimeSourceManager(anchor_confirm_epochs=10)
    for i in range(40):
        mgr.update(verdict(SourceState.TRUSTED), gps_time=T0 + i, host_time=float(i))

    # Attack begins: the receiver claims a large offset but the detector has
    # not reacted yet, so these epochs are still accepted.
    for i in range(40, 45):
        mgr.update(verdict(SourceState.TRUSTED), gps_time=T0 + i + 600, host_time=float(i))
    # Detector reacts.
    d = mgr.update(verdict(SourceState.UNTRUSTED, 0.0), gps_time=T0 + 645, host_time=45.0)

    assert d.source is ActiveSource.HOLDOVER
    # Served time must follow the pre-attack anchor, not the +600 s claim.
    assert abs(d.time_s - (T0 + 45)) < 15.0


def test_ntp_preferred_over_holdover_when_available():
    class Ref:
        def now(self):
            return T0 + 5.0

        @property
        def uncertainty_s(self):
            return MIN_UNCERTAINTY_S

    mgr = TimeSourceManager(ntp=Ref())
    mgr.update(verdict(SourceState.TRUSTED), gps_time=T0, host_time=0.0)
    d = mgr.update(verdict(SourceState.UNTRUSTED, 0.1), gps_time=T0, host_time=1.0)
    assert d.source is ActiveSource.NTP
    assert d.time_s == pytest.approx(T0 + 5.0)


def test_unusable_when_nothing_was_ever_disciplined():
    mgr = TimeSourceManager()
    d = mgr.update(verdict(SourceState.UNTRUSTED, 0.1), gps_time=None, host_time=0.0)
    assert d.source is ActiveSource.NONE
    assert not d.usable


def test_source_changes_are_recorded_with_their_step():
    """A step in served time is what breaks log ordering downstream; it is logged, not smoothed."""
    mgr = TimeSourceManager(anchor_confirm_epochs=3)
    for i in range(8):
        mgr.update(verdict(SourceState.TRUSTED), gps_time=T0 + i, host_time=float(i))
    mgr.update(verdict(SourceState.UNTRUSTED, 0.1), gps_time=T0, host_time=9.0)
    assert len(mgr.events) == 2
    assert mgr.events[-1].to_source is ActiveSource.HOLDOVER


def test_confirmed_gps_keeps_re_anchoring_holdover():
    """Once past the confirmation window, the anchor tracks trusted GPS."""
    mgr = TimeSourceManager(anchor_confirm_epochs=3)
    for i in range(20):
        mgr.update(verdict(SourceState.TRUSTED), gps_time=T0 + i, host_time=float(i))
    d = mgr.update(verdict(SourceState.UNTRUSTED, 0.1), gps_time=None, host_time=20.0)
    assert d.time_s == pytest.approx(T0 + 20.0, abs=4.0)


def test_unknown_state_does_not_serve_gps():
    """Not enough evidence is not the same as evidence of correctness."""
    mgr = TimeSourceManager()
    mgr.update(verdict(SourceState.TRUSTED), gps_time=T0, host_time=0.0)
    d = mgr.update(verdict(SourceState.UNKNOWN, 1.0), gps_time=T0 + 99, host_time=1.0)
    assert d.source is not ActiveSource.GPS
