"""Consistency between reported velocity and observed movement.

The receiver reports speed over ground in RMC and VTG. It also reports a
sequence of positions. Those two are derived differently inside the receiver -
speed from Doppler, position from pseudorange - so a spoofer that does not take
care to keep them consistent leaves a gap between them.

This is the check that catches a lazy spoof: the position is dragged to a new
location while the receiver continues to report that it is standing still.
"""

from __future__ import annotations

from typing import Optional

from ..config import Calibration
from ..nmea.epoch import Epoch
from .base import Detector, Evidence, haversine_m

KNOTS_TO_MPS = 0.514444
MAX_GAP_S = 10.0


class VelocityConsistencyDetector(Detector):
    """Position moves faster than the receiver admits to moving."""

    name = "velocity_consistency"
    rationale = (
        "Reported speed and the speed implied by successive positions come "
        "from different measurements inside the receiver. A spoof that moves "
        "the position without matching the Doppler solution separates them."
    )

    def __init__(self, calibration: Calibration):
        self.feature = calibration.feature("speed_excess_mps")
        self._prev: Optional[tuple[float, float, float]] = None

    def reset(self) -> None:
        self._prev = None

    def update(self, epoch: Epoch) -> Evidence:
        if not epoch.has_position or epoch.utc is None:
            return Evidence.not_applicable(self.name, "no position or timestamp")

        now = epoch.utc.timestamp()
        if self._prev is None:
            self._prev = (epoch.lat, epoch.lon, now)
            return Evidence.not_applicable(self.name, "no previous fix yet")

        plat, plon, ptime = self._prev
        dt = now - ptime
        self._prev = (epoch.lat, epoch.lon, now)

        if dt <= 0 or dt > MAX_GAP_S:
            return Evidence.not_applicable(
                self.name, f"discontinuity of {dt:.1f}s; implied speed undefined"
            )

        implied = haversine_m(plat, plon, epoch.lat, epoch.lon) / dt
        reported = (epoch.sog_knots or 0.0) * KNOTS_TO_MPS

        # Only an excess counts. Reported speed exceeding implied movement is
        # ordinary Doppler noise around zero on a stationary receiver, not
        # evidence of anything.
        excess = max(0.0, implied - reported)
        score = self.feature.score(excess) or 0.0

        return Evidence(
            detector=self.name,
            score=score,
            value=excess,
            warn=self.feature.warn,
            alarm=self.feature.alarm,
            reason=(
                f"position implies {implied:.1f} m/s but receiver reports "
                f"{reported:.1f} m/s"
                if score > 0
                else "reported and implied speed agree"
            ),
            detail={"implied_mps": implied, "reported_mps": reported, "dt_s": dt},
        )
