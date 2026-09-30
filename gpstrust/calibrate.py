"""Calibration from a short clean segment.

The JammerTest calibration describes one Sierra 7455 on one antenna at one
site. It does not transfer to a different receiver in a different place: mean
SNR, position scatter and DOP all depend on the hardware and the sky view. A
scenario run against a gpsd capture therefore has to calibrate against that
capture's own quiet period, which is also what a real deployment does when it
surveys in.

The estimator differs from the one used for the large corpus, and deliberately.
With ninety thousand clean epochs an empirical p99.99 is meaningful. With
ninety, it is the largest sample and nothing more, so the warn and alarm points
here come from a robust location and scale estimate - median and scaled median
absolute deviation - rather than from extreme order statistics. The MAD is used
rather than a standard deviation because a short segment can still contain an
outlier, and one outlier moves a standard deviation enough to hide the very
excursion the threshold exists to catch.

Multipliers of 4 and 8 sigma are conventional for outlier work. They are
recorded as such rather than tuned, since tuning them against the scenarios
would make the scenario results a measure of the tuning.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Optional, Sequence

from .config import Calibration, FeatureCalibration
from .nmea.epoch import Epoch
from .detect.base import flat_distance_m, haversine_m

WARN_SIGMA = 4.0
ALARM_SIGMA = 8.0

# Below this many samples the estimate is not trustworthy and calibration is
# refused rather than guessed.
MIN_SAMPLES = 20

# Floors, so that a receiver reporting suspiciously little variation during the
# quiet segment cannot produce a threshold tight enough to fire on rounding.
MIN_SIGMA = {
    "position_deviation_m": 1.0,   # metres
    "jump_m": 1.0,
    "implied_speed_mps": 0.5,
    "speed_excess_mps": 0.5,
    "hdop": 0.1,
    "pdop": 0.1,
    "snr_mean": 1.0,               # dB-Hz
    "snr_cv": 0.01,
    "sats_in_view": 1.0,
}

# Dilution of precision is handled separately from everything else, for two
# reasons found while testing scenarios against real captures.
#
# First, MAD fails on it. Receivers report DOP to one or two decimals and the
# values cluster heavily - on one capture more than half of all PDOP readings
# were exactly 2.50 - so the median absolute deviation collapses to zero and
# the scale estimate falls to whatever floor is set. The derived threshold then
# sat at 2.9 while the trace's own clean PDOP ranged to 4.0, and the detector
# fired on 37% of unmodified epochs. MAD assumes a continuous distribution;
# quantised readings violate that.
#
# Second, DOP is dimensionless and comparable between receivers in a way that
# SNR and position scatter are not, so it does not need per-trace calibration
# in the first place. The conventional interpretation - below 2 excellent, 2 to
# 5 good, 5 to 10 moderate, above 10 poor - applies to any receiver.
#
# So the threshold is the looser of a relative rise above this receiver's own
# median and an absolute point on that published scale.
DOP_FEATURES = ("hdop", "pdop")
DOP_WARN_RATIO = 2.0
DOP_ALARM_RATIO = 4.0
DOP_WARN_FLOOR = 5.0    # leaving "good" geometry
DOP_ALARM_FLOOR = 10.0  # leaving "moderate" geometry

DIRECTIONS = {
    "position_deviation_m": "high",
    "jump_m": "high",
    "implied_speed_mps": "high",
    "speed_excess_mps": "high",
    "hdop": "high",
    "pdop": "high",
    "snr_mean": "high",
    "snr_cv": "low",
    "sats_in_view": "low",
}


def robust_scale(values: Sequence[float]) -> tuple[float, float]:
    """Median and MAD-derived sigma."""
    if not values:
        return float("nan"), float("nan")
    centre = median(values)
    mad = median([abs(v - centre) for v in values])
    return centre, 1.4826 * mad


def _feature(name: str, values: list[float]) -> Optional[FeatureCalibration]:
    clean = [v for v in values if v is not None and v == v]
    if len(clean) < MIN_SAMPLES:
        return None

    centre, sigma = robust_scale(clean)
    sigma = max(sigma, MIN_SIGMA.get(name, 0.0))
    direction = DIRECTIONS[name]

    if name in DOP_FEATURES:
        return FeatureCalibration(
            name=name,
            direction="high",
            warn=max(centre * DOP_WARN_RATIO, DOP_WARN_FLOOR),
            alarm=max(centre * DOP_ALARM_RATIO, DOP_ALARM_FLOOR),
            median=centre,
            robust_sigma=sigma,
        )

    if direction == "high":
        warn = centre + WARN_SIGMA * sigma
        alarm = centre + ALARM_SIGMA * sigma
    else:
        warn = centre - WARN_SIGMA * sigma
        alarm = centre - ALARM_SIGMA * sigma

    return FeatureCalibration(
        name=name, direction=direction, warn=warn, alarm=alarm,
        median=centre, robust_sigma=sigma,
    )


@dataclass
class SegmentStats:
    epochs: int
    features: dict[str, int]


def calibrate_from_epochs(epochs: Sequence[Epoch]) -> tuple[Calibration, SegmentStats]:
    """Survey in against a clean segment and derive thresholds from it."""
    positioned = [e for e in epochs if e.has_position]
    if len(positioned) < MIN_SAMPLES:
        raise ValueError(
            f"only {len(positioned)} positioned epochs; need {MIN_SAMPLES} to survey in"
        )

    ref_lat = median([e.lat for e in positioned])
    ref_lon = median([e.lon for e in positioned])

    samples: dict[str, list[float]] = {name: [] for name in DIRECTIONS}
    previous: Optional[tuple[float, float, float]] = None

    for e in epochs:
        if e.has_position:
            samples["position_deviation_m"].append(
                flat_distance_m(e.lat, e.lon, ref_lat, ref_lon)
            )
            t = e.utc.timestamp() if e.utc is not None else None
            if previous is not None and t is not None:
                plat, plon, pt = previous
                dt = t - pt
                if 0 < dt <= 10.0:
                    jump = haversine_m(plat, plon, e.lat, e.lon)
                    samples["jump_m"].append(jump)
                    samples["implied_speed_mps"].append(jump / dt)
                    reported = (e.sog_knots or 0.0) * 0.514444
                    samples["speed_excess_mps"].append(max(0.0, jump / dt - reported))
            if t is not None:
                previous = (e.lat, e.lon, t)

        if e.hdop is not None:
            samples["hdop"].append(e.hdop)
        if e.pdop is not None:
            samples["pdop"].append(e.pdop)
        if e.sats_in_view is not None:
            samples["sats_in_view"].append(float(e.sats_in_view))

        tracked = [s for s in e.snr if s and s > 0]
        if len(tracked) >= 4:
            m = sum(tracked) / len(tracked)
            samples["snr_mean"].append(m)
            if m > 0:
                var = sum((s - m) ** 2 for s in tracked) / len(tracked)
                samples["snr_cv"].append((var ** 0.5) / m)

    features = {}
    for name, values in samples.items():
        fc = _feature(name, values)
        if fc is not None:
            features[name] = fc

    centre, sigma = robust_scale(samples["position_deviation_m"] or [0.0])
    calibration = Calibration(
        ref_lat=ref_lat,
        ref_lon=ref_lon,
        nominal_median_m=centre,
        nominal_robust_sigma_m=max(sigma, MIN_SIGMA["position_deviation_m"]),
        features=features,
        corpus={
            "method": "survey-in over a clean segment",
            "estimator": f"median +/- {WARN_SIGMA}/{ALARM_SIGMA} robust sigma (MAD)",
            "epochs": len(epochs),
        },
    )
    return calibration, SegmentStats(
        epochs=len(epochs),
        features={k: len(v) for k, v in samples.items()},
    )
