"""Selection of the active time source.

This is the component that makes the project a resilience mechanism rather than
an anomaly detector. Detection produces a trust score; something then has to
decide what the network is actually told the time is.

The order of preference is GPS, then the network reference, then holdover:

* **GPS** while the trust engine accepts it. It is the only source here with
  sub-microsecond potential and no dependence on network reachability.
* **The NTP reference** when GPS is rejected. Milliseconds rather than
  microseconds, and it depends on the network being up, but it is driven by
  infrastructure a local RF attacker cannot reach.
* **Holdover** when neither is available, with the uncertainty envelope
  growing as it runs, so downstream systems can see the answer decaying rather
  than discover it later.

Two rules exist because of what the corpus showed.

Failing over is immediate; failing back is not. The receiver in the JammerTest
data holds a spoofed position long after the transmission stops, so trust
recovering for one epoch is not evidence that the receiver has recovered. The
trust engine enforces the hold; this manager simply follows its state.

A step in the served time is recorded as an event, never hidden. When the
active source changes, the time being served usually jumps. That discontinuity
is exactly what breaks log ordering and transaction sequencing downstream, so
it is logged with its magnitude rather than smoothed away in silence.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..trust import SourceState, TrustVerdict
from .clock import HoldoverClock
from .ntp import NtpReference


class ActiveSource(str, Enum):
    GPS = "gps"
    NTP = "ntp"
    HOLDOVER = "holdover"
    NONE = "none"


@dataclass
class TimeDecision:
    """What the manager decided, and how good the answer is."""

    source: ActiveSource
    time_s: Optional[float]
    uncertainty_s: float
    reason: str
    stepped_by_s: Optional[float] = None
    holdover_s: float = 0.0

    @property
    def usable(self) -> bool:
        return self.time_s is not None


@dataclass
class SourceEvent:
    at: float
    from_source: ActiveSource
    to_source: ActiveSource
    reason: str
    step_s: Optional[float]


@dataclass
class TimeSourceManager:
    """Chooses the served time source from the trust verdict and what is up."""

    ntp: Optional[NtpReference] = None
    holdover: HoldoverClock = field(default_factory=HoldoverClock)

    #: Uncertainty attributed to GPS-derived time at this layer. NMEA carries
    #: whole or fractional seconds and arrives after unbounded serial latency,
    #: so a second is the honest figure without a PPS input. A receiver's PPS
    #: output would move this to the tens of nanoseconds, and that is the main
    #: thing hardware would buy this project.
    gps_uncertainty_s: float = 1.0

    #: How many trusted epochs must follow a GPS time before it is allowed to
    #: become the holdover anchor.
    #:
    #: This exists because of a failure found in testing. Detection is not
    #: instantaneous: the position detector smooths over 30 epochs and the
    #: time-offset detector over 10, so an attack is accepted for several
    #: epochs before trust falls. Anchoring holdover on every accepted epoch
    #: therefore copies the spoofed time into the fallback, and the system
    #: fails over from a compromised source to a clock it has just set from
    #: that same compromised source. In the test that found it, a receiver
    #: claiming a 600 s offset was correctly rejected and holdover then served
    #: that 600 s error anyway.
    #:
    #: So an anchor is held back until it has been followed by this many
    #: consecutive trusted epochs, and discarded if trust falls in the
    #: meantime. The cost is that the anchor is slightly stale - 30 s at 1 ppm
    #: is 30 microseconds of extra error, which is irrelevant next to serving
    #: an attacker's clock.
    anchor_confirm_epochs: int = 30

    active: ActiveSource = ActiveSource.NONE
    events: list[SourceEvent] = field(default_factory=list)

    _last_served: Optional[float] = field(default=None, init=False)
    _pending_anchors: deque = field(default_factory=deque, init=False)

    def update(
        self,
        verdict: Optional[TrustVerdict],
        gps_time: Optional[float],
        host_time: Optional[float] = None,
    ) -> TimeDecision:
        now_host = time.time() if host_time is None else host_time

        gps_ok = (
            verdict is not None
            and verdict.gps_usable
            and verdict.state is not SourceState.UNKNOWN
            and gps_time is not None
        )

        if gps_ok:
            decision = self._use_gps(gps_time, verdict, now_host)
        else:
            decision = self._use_fallback(verdict, now_host)

        decision.stepped_by_s = self._record(decision, now_host)
        self._last_served = decision.time_s
        return decision

    # -- source choices ---------------------------------------------------

    def _use_gps(self, gps_time: float, verdict: TrustVerdict, now_host: float) -> TimeDecision:
        # GPS time is served immediately but anchors holdover only after it has
        # survived `anchor_confirm_epochs` further trusted epochs. See the
        # field comment: anchoring on acceptance copies a spoofed time into the
        # fallback during the detector's own latency window.
        if verdict.state is SourceState.TRUSTED:
            self._pending_anchors.append((gps_time, now_host))
            while len(self._pending_anchors) > self.anchor_confirm_epochs:
                confirmed_time, confirmed_host = self._pending_anchors.popleft()
                self.holdover.discipline(
                    confirmed_time, self.gps_uncertainty_s, host_time=confirmed_host
                )
        else:
            # Anything short of fully trusted invalidates everything not yet
            # confirmed: a run of suspect epochs is not evidence of health.
            self._pending_anchors.clear()
        trust = "unknown" if verdict.trust is None else f"{verdict.trust:.2f}"
        return TimeDecision(
            source=ActiveSource.GPS,
            time_s=gps_time,
            uncertainty_s=self.gps_uncertainty_s,
            reason=f"GPS trusted (trust {trust}, state {verdict.state.value})",
        )

    def _use_fallback(self, verdict: Optional[TrustVerdict], now_host: float) -> TimeDecision:
        # GPS is not usable, so any anchor still awaiting confirmation came
        # from epochs adjacent to the rejection and must not be committed.
        self._pending_anchors.clear()

        why = "no verdict yet"
        if verdict is not None:
            if verdict.state is SourceState.UNKNOWN:
                why = "insufficient evidence to judge GPS"
            elif not verdict.gps_usable:
                trust = "unknown" if verdict.trust is None else f"{verdict.trust:.2f}"
                top = verdict.reasons[0] if verdict.reasons else "trust below threshold"
                why = f"GPS rejected (trust {trust}): {top}"

        if self.ntp is not None:
            ntp_now = self.ntp.now()
            if ntp_now is not None:
                self.holdover.discipline(ntp_now, self.ntp.uncertainty_s, host_time=now_host)
                return TimeDecision(
                    source=ActiveSource.NTP,
                    time_s=ntp_now,
                    uncertainty_s=self.ntp.uncertainty_s,
                    reason=f"{why}; using network reference",
                )

        held = self.holdover.now(host_time=now_host)
        if held is not None:
            return TimeDecision(
                source=ActiveSource.HOLDOVER,
                time_s=held,
                uncertainty_s=self.holdover.uncertainty_at(now_host),
                reason=f"{why}; no network reference, running on local oscillator",
                holdover_s=self.holdover.elapsed_s(now_host),
            )

        return TimeDecision(
            source=ActiveSource.NONE,
            time_s=None,
            uncertainty_s=float("inf"),
            reason=f"{why}; no fallback available and clock was never disciplined",
        )

    # -- bookkeeping -------------------------------------------------------

    def _record(self, decision: TimeDecision, now_host: float) -> Optional[float]:
        step = None
        if (
            self._last_served is not None
            and decision.time_s is not None
            and decision.source is not self.active
        ):
            step = decision.time_s - self._last_served

        if decision.source is not self.active:
            self.events.append(
                SourceEvent(
                    at=now_host,
                    from_source=self.active,
                    to_source=decision.source,
                    reason=decision.reason,
                    step_s=step,
                )
            )
            self.active = decision.source
        return step

    def status(self, host_time: Optional[float] = None) -> dict:
        return {
            "active": self.active.value,
            "ntp": self.ntp.status() if self.ntp is not None else None,
            "holdover": self.holdover.status(host_time),
            "switches": len(self.events),
            "recent_events": [
                {
                    "at": e.at,
                    "from": e.from_source.value,
                    "to": e.to_source.value,
                    "step_s": None if e.step_s is None else round(e.step_s, 6),
                    "reason": e.reason,
                }
                for e in self.events[-10:]
            ],
        }
