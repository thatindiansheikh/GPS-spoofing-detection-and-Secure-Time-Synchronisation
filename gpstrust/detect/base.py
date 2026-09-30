"""Detector interface.

Each detector examines one aspect of receiver output and returns graded
evidence rather than a verdict. Fusion is the trust engine's job; keeping the
detectors independent is what lets the evaluation report per-detector
performance and show which mechanisms actually carry the load.

Two properties matter for honesty in the results:

* A detector that cannot assess an epoch returns `applicable=False` rather than
  a score of zero. Missing GSV data is not evidence of innocence, and counting
  it as such would quietly inflate the clean-side numbers.
* A detector whose preconditions are violated refuses outright. The time-offset
  detector refuses an epoch whose timestamp is host receive time, because the
  quantity it exists to measure is absent from such an epoch.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from ..nmea.epoch import Epoch

EARTH_M_PER_DEG = 111320.0


@dataclass
class Evidence:
    """One detector's reading of one epoch."""

    detector: str
    score: float = 0.0
    applicable: bool = True
    value: Optional[float] = None
    warn: Optional[float] = None
    alarm: Optional[float] = None
    reason: str = ""
    detail: dict = field(default_factory=dict)

    @property
    def fired(self) -> bool:
        return self.applicable and self.score > 0.0

    @classmethod
    def not_applicable(cls, detector: str, reason: str) -> "Evidence":
        return cls(detector=detector, score=0.0, applicable=False, reason=reason)


class Detector(ABC):
    """Stateful examiner of an epoch stream."""

    name: str = "detector"
    #: Human-readable statement of what this detector would catch, used in the
    #: report so each mechanism's purpose is recorded next to its results.
    rationale: str = ""

    @abstractmethod
    def update(self, epoch: Epoch) -> Evidence:
        """Consume one epoch and return evidence about it."""

    def reset(self) -> None:
        """Clear any rolling state. Called when a stream restarts."""


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres.

    Used for the trajectory and velocity checks, where the two points can be far
    apart during a spoof and the flat-earth approximation would misreport the
    implied speed by enough to matter.
    """
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def flat_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Local flat-earth distance, adequate for deviation from a fixed reference."""
    dlat = (lat1 - lat2) * EARTH_M_PER_DEG
    dlon = (lon1 - lon2) * EARTH_M_PER_DEG * math.cos(math.radians(lat2))
    return math.hypot(dlat, dlon)
