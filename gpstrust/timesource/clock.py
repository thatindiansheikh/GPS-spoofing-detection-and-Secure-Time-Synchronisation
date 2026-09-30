"""Holdover: what the clock does when no source can be trusted.

Rejecting GPS is only half an answer. A time server that stops serving is as
much an outage as one serving wrong time, so something has to carry the clock
across the interval when neither GPS nor the network reference is usable.

That is holdover: keep running on the local oscillator, extrapolating from the
last time that was trusted, and - this is the part that matters - keep an
honest running estimate of how wrong the answer has become. A holdover clock
that reports a time without reporting its uncertainty is worse than no clock,
because downstream systems cannot tell when to stop believing it.

Drift is modelled as a constant rate with a bounded random walk. Real
oscillators also drift with temperature and age, but a constant-rate model with
an explicit uncertainty envelope is the standard first-order treatment and is
what the datasheet figure describes.

Nothing here sets the host clock. The model is the deliverable; steering a real
clock needs administrator rights, disturbs the machine, and would make the
experiment unrepeatable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

# Frequency stability of common oscillator grades, in parts per million.
# A TCXO is what a modest timing receiver ships with; an OCXO is what a telecom
# or substation clock uses when holdover matters.
OSCILLATOR_PPM = {
    "tcxo": 1.0,      # ~86 ms of error per day
    "ocxo": 0.01,     # ~0.86 ms per day
    "rubidium": 0.001,
}

DEFAULT_OSCILLATOR = "tcxo"


@dataclass
class HoldoverClock:
    """Extrapolates from the last trusted time, tracking accumulated error.

    `uncertainty_s` grows with elapsed holdover. Downstream logic is expected
    to compare it against whatever tolerance it needs - 128 ms before ntpd
    steps, 300 s before Kerberos refuses a ticket - and act before it is
    exceeded, rather than discovering the problem afterwards.
    """

    oscillator: str = DEFAULT_OSCILLATOR
    #: Uncertainty of the time that was handed over, at the moment of handover.
    initial_uncertainty_s: float = 0.010

    _anchor_true: Optional[float] = field(default=None, init=False)
    _anchor_host: Optional[float] = field(default=None, init=False)
    _anchor_uncertainty: float = field(default=0.0, init=False)

    @property
    def drift_ppm(self) -> float:
        return OSCILLATOR_PPM.get(self.oscillator, OSCILLATOR_PPM[DEFAULT_OSCILLATOR])

    def discipline(self, true_time: float, uncertainty_s: float,
                   host_time: Optional[float] = None) -> None:
        """Record a moment when the time was known, and how well."""
        self._anchor_true = true_time
        self._anchor_host = time.time() if host_time is None else host_time
        self._anchor_uncertainty = max(uncertainty_s, 0.0)

    def reset(self) -> None:
        self._anchor_true = None
        self._anchor_host = None
        self._anchor_uncertainty = 0.0

    @property
    def disciplined(self) -> bool:
        return self._anchor_true is not None

    def elapsed_s(self, host_time: Optional[float] = None) -> float:
        if self._anchor_host is None:
            return 0.0
        now = time.time() if host_time is None else host_time
        return max(0.0, now - self._anchor_host)

    def now(self, host_time: Optional[float] = None) -> Optional[float]:
        """Best estimate of true time.

        The host clock supplies the elapsed interval; the anchor supplies the
        offset. The host clock's own drift is precisely what the uncertainty
        envelope accounts for.
        """
        if self._anchor_true is None or self._anchor_host is None:
            return None
        now = time.time() if host_time is None else host_time
        return self._anchor_true + (now - self._anchor_host)

    @property
    def uncertainty_s(self) -> float:
        return self.uncertainty_at()

    def uncertainty_at(self, host_time: Optional[float] = None) -> float:
        """Uncertainty of `now()`, grown from the anchor by oscillator drift."""
        if self._anchor_true is None:
            return float("inf")
        elapsed = self.elapsed_s(host_time)
        return self._anchor_uncertainty + (self.drift_ppm * 1e-6) * elapsed

    def seconds_until(self, tolerance_s: float,
                      host_time: Optional[float] = None) -> Optional[float]:
        """How long holdover can continue before exceeding a tolerance.

        Used to warn before the clock becomes unfit for a purpose, rather than
        after. Returns None if the anchor is missing, 0.0 if already exceeded.
        """
        if self._anchor_true is None:
            return None
        current = self.uncertainty_at(host_time)
        if current >= tolerance_s:
            return 0.0
        rate = (self.drift_ppm * 1e-6)
        if rate <= 0:
            return float("inf")
        return (tolerance_s - current) / rate

    def status(self, host_time: Optional[float] = None) -> dict:
        return {
            "disciplined": self.disciplined,
            "oscillator": self.oscillator,
            "drift_ppm": self.drift_ppm,
            "holdover_s": round(self.elapsed_s(host_time), 3),
            "uncertainty_s": (
                None if not self.disciplined else round(self.uncertainty_at(host_time), 9)
            ),
            "seconds_until_ntp_step": (
                None if not self.disciplined else self.seconds_until(0.128, host_time)
            ),
            "seconds_until_kerberos_skew": (
                None if not self.disciplined else self.seconds_until(300.0, host_time)
            ),
        }
