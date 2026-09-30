"""Derive baseline statistics and detection thresholds from clean data.

Rule for this project: no threshold is a constant chosen by hand. Each one is a
quantile of the distribution measured over epochs the transmission plan says
were free of any transmission.

That rule survives contact with the data only with a correction, and the
correction is documented in docs/data-validity.md. About 20% of the epochs the
schedule calls clean show the receiver parked at a discrete spoofed position
(6.03 km, 8.09 km, 3.25 km). No guard interval removes them, both receiver
modules see them equally, and demanding observed recovery after the overnight
gap makes the fraction worse. The campaign transmitted outside its published
schedule. So the clean labels are usable as *nominal operating conditions*
after the far-displaced residue is separated out, but not as a literal negative
class.

Both views are therefore written to the output: statistics over the nominal
mode, which the thresholds use, and statistics over the clean set exactly as
labelled, so the gap between them stays visible.

Output: data/baseline/baseline_stats.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

BASE = ROOT / "data" / "baseline"

# An hour must be at least this fraction of full 1 Hz logging to be used, so a
# logging gap cannot masquerade as receiver behaviour.
MIN_HOURLY_DENSITY = 0.80
NOMINAL_RATE_HZ = 1.0

# Quantile grid stored for every feature, so a detector can place an observed
# value in the clean distribution without re-reading the corpus.
GRID = [0.001, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 0.999, 0.9999]

# Features and the direction in which they indicate an anomaly.
FEATURES: dict[str, str] = {
    "implied_speed_mps": "high",
    "speed_excess_mps": "high",
    "jump_m": "high",
    "position_deviation_m": "high",
    "hdop": "high",
    "pdop": "high",
    "sats_in_view": "low",
    "snr_mean": "high",   # a spoofer transmits hotter than the real constellation
    "snr_cv": "low",      # one antenna flattens the spread real sky geometry gives
    "snr_n": "low",
}

# The SNR spread statistic is meaningless on a handful of satellites.
MIN_SNR_SATS = 4


def geo_distance_m(lat, lon, ref_lat, ref_lon):
    """Local flat-earth approximation.

    Adequate here: the reference is fixed, the quantities of interest run from
    metres to a few hundred kilometres at one latitude, and the curvature error
    is far below the position scatter being measured.
    """
    dlat = (lat - ref_lat) * 111320.0
    dlon = (lon - ref_lon) * 111320.0 * np.cos(np.radians(ref_lat))
    return np.sqrt(dlat**2 + dlon**2)


def quantiles(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {}
    return {f"p{qq * 100:g}": float(s.quantile(qq)) for qq in GRID}


def sigma_clip(values: pd.Series, k: float = 5.0, iters: int = 10):
    """Isolate the nominal mode of a contaminated distribution.

    MAD tolerates up to 50% contamination, which is why it is used here rather
    than a standard deviation: the observed contamination is around 20%, well
    inside that, but far too large for a mean and sigma to survive.

    Returns (kept_mask, centre, robust_sigma, contamination_fraction).
    """
    v = pd.to_numeric(values, errors="coerce").dropna()
    if v.empty:
        return pd.Series(dtype=bool), float("nan"), float("nan"), float("nan")

    keep = pd.Series(True, index=v.index)
    centre, sigma = float(v.median()), float("nan")
    for _ in range(iters):
        sub = v[keep]
        centre = float(sub.median())
        sigma = 1.4826 * float((sub - centre).abs().median())
        if not np.isfinite(sigma) or sigma <= 0:
            break
        new_keep = (v - centre).abs() <= k * sigma
        if new_keep.equals(keep):
            break
        keep = new_keep
    return keep, centre, sigma, float(1.0 - keep.sum() / len(v))


def feature_block(nominal: pd.Series, as_labelled: pd.Series, direction: str) -> dict:
    """Warn and alarm points for one feature, plus the evidence behind them.

    warn  = p99   of the nominal distribution
    alarm = p99.99 of the nominal distribution
    (mirrored to p1 / p0.01 for features that are anomalous when low)

    A detector scores 0 below warn, ramps linearly to 1 at alarm, and saturates.
    The ramp keeps the fused trust score graded rather than a step function,
    which matters because the failover logic needs to distinguish "degrading"
    from "gone".
    """
    nom = pd.to_numeric(nominal, errors="coerce").dropna()
    lab = pd.to_numeric(as_labelled, errors="coerce").dropna()
    if nom.empty:
        return {}

    if direction == "high":
        warn, alarm = float(nom.quantile(0.99)), float(nom.quantile(0.9999))
        fpr_labelled = float((lab > warn).mean()) if len(lab) else None
    else:
        warn, alarm = float(nom.quantile(0.01)), float(nom.quantile(0.0001))
        fpr_labelled = float((lab < warn).mean()) if len(lab) else None

    return {
        "direction": direction,
        "warn": round(warn, 6),
        "alarm": round(alarm, 6),
        "median": round(float(nom.median()), 6),
        "robust_sigma": round(1.4826 * float((nom - nom.median()).abs().median()), 6),
        "quantiles_nominal": {k: round(v, 6) for k, v in quantiles(nom).items()},
        "quantiles_as_labelled": {k: round(v, 6) for k, v in quantiles(lab).items()},
        "n_nominal": int(len(nom)),
        "n_as_labelled": int(len(lab)),
        # Rate at which `warn` fires across the clean set exactly as the plan
        # labels it. For position this is large by construction, because that
        # set contains the spoofed residue; recorded so the number is never
        # quoted as a false alarm rate without its context.
        "warn_rate_on_labelled_clean": (
            None if fpr_labelled is None else round(fpr_labelled, 6)
        ),
    }


def main() -> int:
    epochs = pd.read_parquet(BASE / "epochs.parquet")
    print(f"Loaded {len(epochs):,} epochs")

    epochs = epochs.sort_values("ts")
    hour = epochs["ts"].dt.floor("h")
    counts = epochs.groupby([hour, "module_id"]).size().rename("n").reset_index()
    counts["density"] = counts["n"] / (3600 * NOMINAL_RATE_HZ)
    dense_keys = set(
        map(tuple, counts.loc[counts["density"] >= MIN_HOURLY_DENSITY, ["ts", "module_id"]].values)
    )
    dense = epochs[[(h, m) in dense_keys for h, m in zip(hour, epochs["module_id"])]].copy()
    print(f"  {len(dense):,} epochs in densely logged hours ({len(dense) / len(epochs):.1%})")

    # Calibration sees the training days only. Deriving thresholds from the
    # same epochs used to report results would make every number here a
    # statement about memorisation rather than detection.
    from gpstrust import splits

    print(f"  {splits.describe(dense)}")
    dense = splits.train(dense)
    print(f"  calibrating on {len(dense):,} training-day epochs")

    n_clean = int(dense["is_clean"].sum())
    print(f"  {n_clean:,} epochs labelled clean by the plan")
    if n_clean < 10_000:
        print("REFUSING: too few clean epochs to derive thresholds from")
        return 1

    # Survey-in. Median, not mean: the displaced residue must not drag the
    # reference away from the true antenna position.
    ref_lat = float(dense.loc[dense["is_clean"], "lat"].median())
    ref_lon = float(dense.loc[dense["is_clean"], "lon"].median())

    # Derived motion features must be computed over the continuous stream, not
    # over the clean subset. Differencing a subset would treat the gap left by
    # a removed attack period as real movement and invent a jump at every
    # boundary.
    from gpstrust.features import derive as derive_features

    dense = derive_features(dense, ref_lat, ref_lon)
    clean = dense[dense["is_clean"]].copy()

    keep, centre, sigma, contamination = sigma_clip(clean["position_deviation_m"])
    nominal_idx = keep.index[keep]
    nominal = clean.loc[nominal_idx]

    print(f"\nSurvey-in reference: {ref_lat:.7f}, {ref_lon:.7f}")
    print(f"  nominal mode: median {centre:.2f} m, robust sigma {sigma:.2f} m")
    print(f"  residue excluded from the nominal mode: {contamination:.1%} "
          f"({len(clean) - len(nominal):,} epochs)")
    print(f"  -> see docs/data-validity.md; this residue is spoofed, not scatter")

    # The SNR spread statistic needs enough satellites to mean anything.
    snr_ok = nominal["snr_n"] >= MIN_SNR_SATS
    snr_ok_lab = clean["snr_n"] >= MIN_SNR_SATS

    features = {}
    for name, direction in FEATURES.items():
        if name not in nominal.columns:
            continue
        if name.startswith("snr_") and name != "snr_n":
            block = feature_block(nominal.loc[snr_ok, name], clean.loc[snr_ok_lab, name], direction)
        else:
            block = feature_block(nominal[name], clean[name], direction)
        if block:
            features[name] = block

    stats = {
        "corpus": {
            "source": "JammerTest 2025 (SimulaMet, CC-BY-4.0)",
            "labels": "NPRA transmission plan (MIT), test area 1, plan times -2 h to UTC",
            "split": "train days only: " + ", ".join(str(d) for d in __import__(
                "gpstrust.splits", fromlist=["TRAIN_DAYS"]).TRAIN_DAYS),
            "epochs_total": int(len(epochs)),
            "epochs_dense": int(len(dense)),
            "epochs_labelled_clean": int(len(clean)),
            "epochs_nominal": int(len(nominal)),
            "nominal_contamination_excluded": round(contamination, 6),
            "min_hourly_density": MIN_HOURLY_DENSITY,
            "min_snr_sats": MIN_SNR_SATS,
            "caveat": "Clean labels are not a literal negative class; see "
                      "docs/data-validity.md. Thresholds use the nominal mode.",
        },
        "reference_position": {
            "lat": ref_lat,
            "lon": ref_lon,
            "method": "median of plan-clean epochs (survey-in)",
            "nominal_median_m": round(centre, 4),
            "nominal_robust_sigma_m": round(sigma, 4),
        },
        "features": features,
    }

    out = BASE / "baseline_stats.json"
    out.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print("\nCalibrated detector points (warn -> alarm):")
    for name, block in features.items():
        arrow = "high" if block["direction"] == "high" else "low "
        rate = block["warn_rate_on_labelled_clean"]
        rate_s = "n/a" if rate is None else f"{rate:.2%}"
        print(f"  {name:22s} {arrow}  {block['warn']:>10.4f} -> {block['alarm']:<10.4f}"
              f"  (warn fires on {rate_s} of as-labelled clean)")
    print(f"\nWritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
