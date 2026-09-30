"""Derived per-epoch quantities.

The detectors need a few things the receiver does not report directly: how far
the position sits from the surveyed reference, how fast the position appears to
be moving between consecutive epochs, and whether that implied motion agrees
with the speed the receiver claims.

This module computes them over a DataFrame so the same definitions calibrate
the thresholds and drive the evaluation. The streaming detectors recompute the
same formulas incrementally; tests/test_features.py checks the two paths agree,
because a drift between them would mean the thresholds no longer describe what
the detectors measure.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

EARTH_M_PER_DEG = 111320.0
EARTH_RADIUS_M = 6371008.8
KNOTS_TO_MPS = 0.514444

# Consecutive epochs further apart than this are treated as a discontinuity
# rather than motion: the receiver stopped logging, so no implied speed can be
# computed across the gap.
MAX_GAP_S = 10.0


def flat_distance_m(lat, lon, ref_lat, ref_lon):
    """Deviation from a fixed reference. Curvature error is negligible here."""
    dlat = (lat - ref_lat) * EARTH_M_PER_DEG
    dlon = (lon - ref_lon) * EARTH_M_PER_DEG * np.cos(np.radians(ref_lat))
    return np.hypot(dlat, dlon)


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance, used where the two points may be far apart.

    During a spoof, consecutive positions can be hundreds of kilometres apart,
    and the flat approximation would misreport the implied speed by enough to
    change the verdict.
    """
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * np.arcsin(np.clip(np.sqrt(a), 0, 1))


def derive(frame: pd.DataFrame, ref_lat: float, ref_lon: float) -> pd.DataFrame:
    """Add derived columns, grouped by receiver module.

    Grouping matters: the two modules are independent receivers, and computing
    an implied speed across a module boundary would invent a jump.
    """
    out = frame.sort_values(["module_id", "ts"]).copy()

    out["position_deviation_m"] = flat_distance_m(out["lat"], out["lon"], ref_lat, ref_lon)

    g = out.groupby("module_id", sort=False)
    prev_lat = g["lat"].shift()
    prev_lon = g["lon"].shift()
    dt = g["ts"].diff().dt.total_seconds()

    jump = haversine_m(prev_lat, prev_lon, out["lat"], out["lon"])
    valid = dt.notna() & (dt > 0) & (dt <= MAX_GAP_S) & prev_lat.notna() & out["lat"].notna()

    out["dt_s"] = dt.where(valid)
    out["jump_m"] = jump.where(valid)
    out["implied_speed_mps"] = (jump / dt).where(valid)

    reported = out["sog_knots"] * KNOTS_TO_MPS
    out["reported_speed_mps"] = reported
    # Positive when the position moves faster than the receiver admits to
    # moving. A spoof that teleports the position while still reporting a
    # stationary receiver shows up here and nowhere else.
    out["speed_excess_mps"] = (out["implied_speed_mps"] - reported.fillna(0.0)).clip(lower=0)

    return out
