"""Calibration loaded from measured data.

No detector in this project carries a hard-coded threshold. Every decision
point is read from data/baseline/baseline_stats.json, which is produced by
scripts/build_baseline.py from epochs the transmission plan says were free of
any transmission. If that file is missing the detectors refuse to run rather
than fall back on invented constants, because a plausible-looking default is
exactly the thing this project should not contain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "baseline" / "baseline_stats.json"


class CalibrationMissing(RuntimeError):
    """Raised when baseline statistics have not been built."""


@dataclass(frozen=True)
class FeatureCalibration:
    """Where one feature's warn and alarm points sit in the clean distribution.

    `warn` is the p99 of the clean distribution and `alarm` the p99.99 (mirrored
    for features that are anomalous when low). A detector returns 0 below warn,
    ramps linearly to 1 at alarm, and saturates there.

    The ramp matters: a step function would make the fused trust score jump
    between two values, and the failover logic needs to tell "degrading" from
    "gone" in order to hold off on switching time sources for a transient.
    """

    name: str
    direction: str
    warn: float
    alarm: float
    median: float
    robust_sigma: float
    warn_rate_on_labelled_clean: Optional[float] = None

    def score(self, value: Optional[float]) -> Optional[float]:
        """Map an observed value to 0..1. None means "cannot assess"."""
        if value is None:
            return None
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        if v != v:  # NaN
            return None

        span = self.alarm - self.warn
        if self.direction == "high":
            if v <= self.warn:
                return 0.0
            if span <= 0:
                return 1.0
            return min(1.0, (v - self.warn) / span)

        # direction == "low": alarm sits below warn
        if v >= self.warn:
            return 0.0
        if span >= 0:
            return 1.0
        return min(1.0, (v - self.warn) / span)


@dataclass(frozen=True)
class Calibration:
    """The full calibration set, plus the surveyed reference position."""

    ref_lat: float
    ref_lon: float
    nominal_median_m: float
    nominal_robust_sigma_m: float
    features: dict[str, FeatureCalibration]
    corpus: dict
    source_path: Optional[Path] = None

    def feature(self, name: str) -> FeatureCalibration:
        try:
            return self.features[name]
        except KeyError:
            raise CalibrationMissing(
                f"feature {name!r} was not calibrated; rerun scripts/build_baseline.py"
            ) from None

    def has(self, name: str) -> bool:
        return name in self.features


def load(path: str | Path | None = None) -> Calibration:
    """Read baseline_stats.json into a Calibration."""
    p = Path(path) if path is not None else DEFAULT_PATH
    if not p.exists():
        raise CalibrationMissing(
            f"{p} not found. Run scripts/fetch_data.py, scripts/build_epochs.py "
            "and scripts/build_baseline.py first. Detectors will not run on "
            "invented thresholds."
        )

    doc = json.loads(p.read_text(encoding="utf-8"))
    ref = doc["reference_position"]

    features = {}
    for name, block in doc.get("features", {}).items():
        features[name] = FeatureCalibration(
            name=name,
            direction=block["direction"],
            warn=float(block["warn"]),
            alarm=float(block["alarm"]),
            median=float(block.get("median", 0.0)),
            robust_sigma=float(block.get("robust_sigma", 0.0)),
            warn_rate_on_labelled_clean=block.get("warn_rate_on_labelled_clean"),
        )

    return Calibration(
        ref_lat=float(ref["lat"]),
        ref_lon=float(ref["lon"]),
        nominal_median_m=float(ref.get("nominal_median_m", 0.0)),
        nominal_robust_sigma_m=float(ref.get("nominal_robust_sigma_m", 1.0)),
        features=features,
        corpus=doc.get("corpus", {}),
        source_path=p,
    )
