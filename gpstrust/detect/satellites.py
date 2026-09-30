"""Satellite health and geometry checks.

These are the cheapest indicators available and they catch the loud attacks.
Jamming shows up as satellites disappearing and dilution of precision
collapsing; a receiver that has lost the constellation says so in GGA and GSA
long before anything subtler is measurable.

Neither check is sufficient alone. A competent spoofer supplies a full, healthy
looking constellation, so these will stay quiet during exactly the attacks that
matter most for time integrity. They are included because they are nearly free
and because their silence during a coherent spoof is itself a reported result.
"""

from __future__ import annotations

from ..config import Calibration
from ..nmea.epoch import Epoch
from .base import Detector, Evidence


class SatelliteCountDetector(Detector):
    """Loss of satellites in view."""

    name = "satellite_count"
    rationale = (
        "Jamming raises the noise floor until the receiver can no longer track "
        "satellites, so the count in view falls away."
    )

    def __init__(self, calibration: Calibration):
        self.feature = calibration.feature("sats_in_view")

    def update(self, epoch: Epoch) -> Evidence:
        n = epoch.sats_in_view
        if n is None:
            return Evidence.not_applicable(self.name, "no GSV data in epoch")

        score = self.feature.score(n) or 0.0
        return Evidence(
            detector=self.name,
            score=score,
            value=float(n),
            warn=self.feature.warn,
            alarm=self.feature.alarm,
            reason=(
                f"{n} satellites in view (warn below {self.feature.warn:.0f})"
                if score > 0
                else f"{n} satellites in view"
            ),
        )


class DilutionDetector(Detector):
    """Degraded geometry, or a receiver reporting no usable solution at all."""

    name = "dilution"
    rationale = (
        "HDOP describes the geometry the solution rests on. It degrades when "
        "satellites are lost, and the receiver substitutes an invalid sentinel "
        "when it has no usable fix at all."
    )

    #: Value the Sierra 7455 reports in place of a real DOP when it has no fix.
    #: Treated as a separate signal rather than as a very large DOP, because it
    #: is a flag, not a measurement, and averaging it would be meaningless.
    INVALID_SENTINEL = 500.0

    def __init__(self, calibration: Calibration):
        self.hdop = calibration.feature("hdop")
        self.pdop = calibration.feature("pdop") if calibration.has("pdop") else None

    def update(self, epoch: Epoch) -> Evidence:
        if epoch.hdop is None and epoch.pdop is None:
            return Evidence.not_applicable(self.name, "no DOP reported")

        # The sentinel means "no fix", which is maximum evidence of a problem
        # and must not be scored as though it were a numeric DOP.
        for value in (epoch.hdop, epoch.pdop, epoch.vdop):
            if value is not None and value >= self.INVALID_SENTINEL:
                return Evidence(
                    detector=self.name,
                    score=1.0,
                    value=value,
                    warn=self.hdop.warn,
                    alarm=self.hdop.alarm,
                    reason="receiver reported the invalid-DOP sentinel: no usable fix",
                    detail={"sentinel": True},
                )

        scores = []
        if epoch.hdop is not None:
            scores.append(("hdop", epoch.hdop, self.hdop.score(epoch.hdop) or 0.0))
        if self.pdop is not None and epoch.pdop is not None:
            scores.append(("pdop", epoch.pdop, self.pdop.score(epoch.pdop) or 0.0))

        if not scores:
            return Evidence.not_applicable(self.name, "no usable DOP value")

        which, value, score = max(scores, key=lambda t: t[2])
        return Evidence(
            detector=self.name,
            score=score,
            value=value,
            warn=self.hdop.warn,
            alarm=self.hdop.alarm,
            reason=(
                f"{which} {value:.2f} exceeds clean p99 of {self.hdop.warn:.2f}"
                if score > 0
                else f"{which} {value:.2f} within clean range"
            ),
            detail={"scores": {k: s for k, _, s in scores}},
        )
