"""Position-based detection for a fixed receiver.

Two independent mechanisms:

`PositionDeviationDetector` compares the reported position against the surveyed
reference. This mirrors what real GNSS timing receivers do in fixed-position
mode: survey in once, then solve only for the clock. A static receiver that
starts reporting a position hundreds of metres away is either broken or lying.

`TrajectoryDetector` ignores the reference entirely and looks only at whether
consecutive positions are connected by physically possible motion. It therefore
still works if the surveyed reference is wrong or unavailable, and it catches a
spoof that walks the position smoothly away from truth, which a pure deviation
check would only notice once the walk had gone far enough.
"""

from __future__ import annotations

from collections import deque
from statistics import median
from typing import Optional

from ..config import Calibration
from ..nmea.epoch import Epoch
from .base import Detector, Evidence, flat_distance_m, haversine_m

# Consecutive epochs further apart than this are a logging discontinuity, not
# motion. No implied speed can be computed across such a gap.
MAX_GAP_S = 10.0


class PositionDeviationDetector(Detector):
    """Sustained displacement from the surveyed antenna position."""

    name = "position_deviation"
    rationale = (
        "A stationary timing receiver should report a position stable to a few "
        "metres. Sustained displacement means the position solution is being "
        "driven by something other than the real constellation."
    )

    def __init__(self, calibration: Calibration, window: int = 30):
        self.cal = calibration
        self.feature = calibration.feature("position_deviation_m")
        # A rolling median rather than the instantaneous value. Single-epoch
        # multipath excursions are common and are not attacks; a spoof holds
        # the position away from truth for as long as it is transmitting. The
        # cost is detection latency of up to half a window, which the
        # evaluation measures rather than assumes away.
        self.window = window
        self._recent: deque[float] = deque(maxlen=window)

    def reset(self) -> None:
        self._recent.clear()

    def update(self, epoch: Epoch) -> Evidence:
        if not epoch.has_position:
            return Evidence.not_applicable(self.name, "no position in epoch")

        instant = flat_distance_m(epoch.lat, epoch.lon, self.cal.ref_lat, self.cal.ref_lon)
        self._recent.append(instant)
        smoothed = median(self._recent)

        score = self.feature.score(smoothed) or 0.0
        return Evidence(
            detector=self.name,
            score=score,
            value=smoothed,
            warn=self.feature.warn,
            alarm=self.feature.alarm,
            reason=(
                f"position {smoothed:.1f} m from reference "
                f"(warn {self.feature.warn:.1f} m)"
                if score > 0
                else "position within surveyed scatter"
            ),
            detail={"instantaneous_m": instant, "window": len(self._recent)},
        )


class TrajectoryDetector(Detector):
    """Motion between consecutive fixes that no real receiver could produce."""

    name = "trajectory"
    rationale = (
        "Consecutive positions must be joined by plausible motion. A position "
        "that teleports, or moves faster than the platform can, indicates the "
        "solution jumped rather than tracked."
    )

    def __init__(self, calibration: Calibration):
        self.cal = calibration
        self.jump = calibration.feature("jump_m")
        self.speed = calibration.feature("implied_speed_mps")
        self._prev: Optional[tuple[float, float, float]] = None  # lat, lon, t

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
                self.name, f"discontinuity of {dt:.1f}s; motion undefined across a gap"
            )

        # Great-circle, not flat: during a spoof the two points can be hundreds
        # of kilometres apart and the flat approximation would misreport speed.
        jump_m = haversine_m(plat, plon, epoch.lat, epoch.lon)
        implied = jump_m / dt

        s_jump = self.jump.score(jump_m) or 0.0
        s_speed = self.speed.score(implied) or 0.0
        score = max(s_jump, s_speed)

        return Evidence(
            detector=self.name,
            score=score,
            value=implied,
            warn=self.speed.warn,
            alarm=self.speed.alarm,
            reason=(
                f"moved {jump_m:.1f} m in {dt:.1f}s ({implied:.1f} m/s)"
                if score > 0
                else "motion between fixes is plausible"
            ),
            detail={"jump_m": jump_m, "dt_s": dt,
                    "score_jump": s_jump, "score_speed": s_speed},
        )
