"""Detection modules.

Each examines one aspect of receiver output and returns graded evidence.
Fusion is the trust engine's job; keeping them independent is what lets the
evaluation report which mechanisms actually carry the load and which stay
silent during the attacks that matter most.
"""

from .base import Detector, Evidence, flat_distance_m, haversine_m
from .motion import VelocityConsistencyDetector
from .position import PositionDeviationDetector, TrajectoryDetector
from .satellites import DilutionDetector, SatelliteCountDetector
from .snr import SnrPowerDetector, SnrUniformityDetector
from .timeoffset import TimeOffsetDetector, TimeReference

__all__ = [
    "Detector",
    "Evidence",
    "flat_distance_m",
    "haversine_m",
    "PositionDeviationDetector",
    "TrajectoryDetector",
    "SatelliteCountDetector",
    "DilutionDetector",
    "SnrPowerDetector",
    "SnrUniformityDetector",
    "VelocityConsistencyDetector",
    "TimeOffsetDetector",
    "TimeReference",
    "build_default_suite",
]


def build_default_suite(calibration, reference=None, strict=False):
    """The detectors used in the standard configuration.

    `reference` is an independent clock. Without one the time-offset detector
    is omitted rather than included in a state where it can never fire, so that
    its absence is visible in the results instead of looking like a detector
    that simply never triggered.

    A detector whose features were not calibrated is likewise omitted. A short
    capture may not contain enough GSV sentences to estimate an SNR
    distribution, and the alternative - running it on a default threshold -
    would violate the rule that no threshold in this project is invented. Pass
    `strict=True` to raise instead, which is what a deployment wants: silently
    losing a detector in production is worse than refusing to start.
    """
    from ..config import CalibrationMissing

    candidates = [
        PositionDeviationDetector,
        TrajectoryDetector,
        VelocityConsistencyDetector,
        SatelliteCountDetector,
        DilutionDetector,
        SnrPowerDetector,
        SnrUniformityDetector,
    ]

    detectors, skipped = [], []
    for cls in candidates:
        try:
            detectors.append(cls(calibration))
        except CalibrationMissing as exc:
            if strict:
                raise
            skipped.append((cls.name, str(exc)))

    if reference is not None:
        detectors.append(TimeOffsetDetector(reference))

    # Recorded on the suite so callers can report what was unavailable rather
    # than quietly presenting a partial suite as a complete one.
    build_default_suite.last_skipped = skipped
    return detectors
