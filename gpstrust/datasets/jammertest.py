"""Adapter for the JammerTest 2025 dataset and its transmission plan.

The dataset is real Sierra 7455 output recorded at Andoya in September 2025
while licensed jamming, spoofing and meaconing transmissions were taking place.
The NPRA transmission plan published alongside the campaign gives the start and
end time of every test, so attack labels come from the schedule of what was
actually transmitted rather than from inspecting the measurements. That keeps
the labels independent of the detector being evaluated.

The dataset is distributed as two CSVs rather than raw NMEA. This module maps
them onto the same `Epoch` record the NMEA parser produces, so the detection
layer is identical whether its input is a live sentence stream or this dataset.
Deliberately no NMEA sentences are synthesised from the CSVs: re-serialising
would mean inventing field values that are not in the source, and the one field
that matters most - the receiver's claimed UTC - is exactly what was dropped
during the dataset's own preprocessing.

Findings from the data that are encoded below rather than left as assumptions:

* Plan times are local (CEST, UTC+2); dataset timestamps are UTC. Established
  empirically: shifting the plan by -2 h separates degraded from clean epochs
  by 2.2x, while 0 h, -1 h and -3 h all give ~1.0x, i.e. no discrimination.
* HDOP 500 is the receiver's invalid sentinel, not a dilution value. It appears
  in ~1.3% of rows and must not enter DOP statistics.
* Position is reported even when the fix is unusable - latitude is non-null in
  100% of rows including during jamming. A spoofed or jammed receiver here
  keeps emitting a plausible-looking position, which is the behaviour this
  project exists to catch.
* Each fix cycle produces several rows a few milliseconds apart (GGA, RMC and
  GSA contribute separately), then a ~1 s gap. Rows are therefore grouped into
  epochs by burst, not by rounding to the second, which would split any burst
  that straddles a second boundary.
* The measurement node correlates with Test Area 1 (2.2x degradation ratio,
  against ~1.2x for Areas 2 and 3), so Area 1 tests are treated as the ones
  affecting it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

import numpy as np
import pandas as pd

from ..nmea.epoch import Epoch

# Plan timestamps are local Norwegian summer time; dataset timestamps are UTC.
PLAN_UTC_OFFSET_HOURS = 2

# The receiver reports this in place of a real HDOP when it has no usable fix.
HDOP_INVALID_SENTINEL = 500.0

# Rows closer together than this belong to the same fix cycle.
BURST_GAP_S = 0.10

# The test area the measurement node responds to (see module docstring).
PRIMARY_LOCATION_ID = 1

# Attack category per "type.group" prefix of the plan's dotted test id.
# Taken from testcatalog2025.json group names; kept explicit here so the
# mapping is reviewable rather than inferred from keyword matching.
CATEGORY_BY_GROUP: dict[str, str] = {
    # Type 0 - supplemental periods
    "0.0": "clean",      # mandatory briefings, no RF expected
    "0.1": "clean",      # grace period between tests
    "0.2": "unknown",    # booking slots: participants may transmit
    "0.3": "unknown",    # ad hoc tests: unspecified transmissions
    # Type 1 - jamming
    **{f"1.{g}": "jamming" for g in range(1, 24)},
    # Type 2 - spoofing, split by what is being spoofed
    "2.1": "spoof_position",
    "2.2": "spoof_position",
    "2.3": "spoof_position",
    "2.4": "spoof_time",
    "2.5": "spoof_time",
    "2.6": "spoof_position_time",
    "2.7": "spoof_time",
    "2.8": "spoof_other",
    "2.9": "spoof_other",
    "2.10": "spoof_position",
    # Type 3 - meaconing
    **{f"3.{g}": "meaconing" for g in range(1, 5)},
}

ATTACK_LABELS = frozenset(
    {"jamming", "meaconing", "spoof_position", "spoof_time",
     "spoof_position_time", "spoof_other"}
)

# When several tests overlap, the label with the highest precedence wins.
# Spoofing outranks jamming because a concurrent spoof is what determines the
# reported position; jamming alone cannot move it.
PRECEDENCE = [
    "spoof_position_time",
    "spoof_time",
    "spoof_position",
    "spoof_other",
    "meaconing",
    "jamming",
    "unknown",
    "clean",
]
_RANK = {name: i for i, name in enumerate(PRECEDENCE)}

PLAN_DAYS = [
    "monday-2025-09-15",
    "tuesday-2025-09-16",
    "wednesday-2025-09-17",
    "thursday-2025-09-18",
    "friday-2025-09-19",
]


# ---------------------------------------------------------------------------
# Transmission plan
# ---------------------------------------------------------------------------


def load_plan(plan_dir: str | Path) -> pd.DataFrame:
    """Read the per-day plan files into one table of UTC test windows."""
    plan_dir = Path(plan_dir)
    rows: list[dict] = []
    for day in PLAN_DAYS:
        path = plan_dir / f"plan-{day}.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        for location in doc.get("locations", []):
            for test in location.get("tests", []):
                test_id = str(test.get("test_id", "")).strip()
                rows.append(
                    {
                        "day": day,
                        "location_id": location.get("location_id"),
                        "location_name": location.get("location_name", ""),
                        "test_id": test_id,
                        "group_key": ".".join(test_id.split(".")[:2]),
                        "start_local": pd.Timestamp(test["start_time"]),
                        "end_local": pd.Timestamp(test["end_time"]),
                        "power_w": test.get("power_w", 0),
                        "comment": test.get("comment", "") or "",
                    }
                )

    plan = pd.DataFrame(rows)
    if plan.empty:
        return plan

    shift = pd.Timedelta(hours=PLAN_UTC_OFFSET_HOURS)
    plan["start_utc"] = plan["start_local"] - shift
    plan["end_utc"] = plan["end_local"] - shift
    plan["category"] = plan["group_key"].map(CATEGORY_BY_GROUP).fillna("unknown")
    plan["rank"] = plan["category"].map(_RANK).fillna(len(PRECEDENCE))
    return plan.sort_values("start_utc").reset_index(drop=True)


def load_catalog(plan_dir: str | Path) -> pd.DataFrame:
    """Read the test catalogue: one row per test group, with its description."""
    path = Path(plan_dir) / "testcatalog2025.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for test_type in doc.get("test_types", []):
        type_id = test_type.get("type_id")
        for group in test_type.get("test_groups", []):
            key = f"{type_id}.{group.get('group_id')}"
            rows.append(
                {
                    "group_key": key,
                    "type_id": type_id,
                    "type_name": test_type.get("type", ""),
                    "group_id": group.get("group_id"),
                    "group_name": group.get("group_name", ""),
                    "n_tests": len(group.get("tests", [])),
                    "category": CATEGORY_BY_GROUP.get(key, "unknown"),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


def _assign_epoch_ids(df: pd.DataFrame) -> pd.Series:
    """Group rows into fix cycles by detecting the gap between bursts."""
    dt = df.groupby("module_id", sort=False)["ts"].diff().dt.total_seconds()
    new_module = df["module_id"].ne(df["module_id"].shift())
    starts = new_module | dt.isna() | (dt > BURST_GAP_S)
    return starts.cumsum()


def _first_valid(series: pd.Series):
    valid = series.dropna()
    return valid.iloc[0] if len(valid) else np.nan


def load_epochs(
    raw_dir: str | Path,
    module_id: Optional[int] = None,
    with_snr: bool = True,
) -> pd.DataFrame:
    """Build the per-epoch table from gps.csv and constellation.csv.

    One row per fix cycle per receiver module. Column names match the fields of
    `Epoch` so the streaming and batch paths describe the same quantities.
    """
    raw_dir = Path(raw_dir)
    gps_path = raw_dir / "jammertest25" / "gps.csv"

    gps = pd.read_csv(
        gps_path,
        parse_dates=["ts"],
        usecols=[
            "ts", "node_id", "module_id", "fix_type", "latitude", "longitude",
            "altitude", "speed_knots", "course", "satellites_visible",
            "hdop", "vdop", "pdop",
        ],
    )
    if module_id is not None:
        gps = gps[gps["module_id"] == module_id].copy()
    gps = gps.sort_values(["module_id", "ts"]).reset_index(drop=True)

    # The invalid sentinel must not be averaged into DOP statistics. Keep the
    # fact that it occurred, since it is itself an indicator.
    dop_invalid = pd.Series(False, index=gps.index)
    for col in ("hdop", "vdop", "pdop"):
        bad = gps[col] >= HDOP_INVALID_SENTINEL
        dop_invalid |= bad.fillna(False)
        gps.loc[bad.fillna(False), col] = np.nan
    gps["dop_invalid"] = dop_invalid

    gps["epoch_id"] = _assign_epoch_ids(gps)

    agg = (
        gps.groupby("epoch_id")
        .agg(
            ts=("ts", "first"),
            node_id=("node_id", "first"),
            module_id=("module_id", "first"),
            fix_quality=("fix_type", _first_valid),
            lat=("latitude", _first_valid),
            lon=("longitude", _first_valid),
            altitude_m=("altitude", _first_valid),
            sog_knots=("speed_knots", _first_valid),
            cog_deg=("course", _first_valid),
            sats_in_view=("satellites_visible", _first_valid),
            hdop=("hdop", _first_valid),
            vdop=("vdop", _first_valid),
            pdop=("pdop", _first_valid),
            dop_invalid=("dop_invalid", "any"),
            n_rows=("ts", "size"),
        )
        .reset_index()
    )

    if with_snr:
        agg = _attach_snr(agg, raw_dir, module_id)

    return agg


def _attach_snr(
    epochs: pd.DataFrame, raw_dir: Path, module_id: Optional[int]
) -> pd.DataFrame:
    """Join GSV-derived per-satellite SNR onto each epoch.

    Constellation rows carry the same timestamp as the fix-cycle burst they
    belong to, but are matched with a nearest-time join rather than an exact one
    so that a GSV group emitted a few milliseconds off the burst is not lost.
    """
    con_path = raw_dir / "jammertest25" / "constellation.csv"
    con = pd.read_csv(
        con_path,
        parse_dates=["ts"],
        usecols=["ts", "module_id", "prn", "elevation", "azimuth", "snr", "system"],
    )
    if module_id is not None:
        con = con[con["module_id"] == module_id].copy()

    keys = epochs[["epoch_id", "ts", "module_id"]].sort_values("ts")
    con = con.sort_values("ts")
    con = pd.merge_asof(
        con,
        keys,
        on="ts",
        by="module_id",
        direction="nearest",
        tolerance=pd.Timedelta("0.5s"),
    )
    con = con.dropna(subset=["epoch_id"])

    snr = con.groupby("epoch_id")["snr"].agg(
        snr_n="count", snr_mean="mean", snr_std="std", snr_min="min", snr_max="max"
    )
    # The per-satellite values are kept, not just their summary. The SNR
    # detectors take a list of tracked satellites, exactly as they would from
    # GSV sentences, so the dataset path and the live NMEA path run the same
    # detector code rather than two implementations that can drift apart.
    snr_values = (
        con.dropna(subset=["snr"])
        .groupby("epoch_id")["snr"]
        .apply(lambda s: [int(v) for v in s])
        .rename("snr_values")
    )
    # Coefficient of variation is the uniformity statistic: a spoofer feeding
    # every channel from one antenna tends to flatten the spread that real sky
    # geometry produces.
    snr["snr_cv"] = snr["snr_std"] / snr["snr_mean"].replace(0, np.nan)
    elev = con.groupby("epoch_id")["elevation"].agg(elev_mean="mean", elev_std="std")
    systems = con.groupby("epoch_id")["system"].nunique().rename("n_systems")

    out = epochs.merge(snr, on="epoch_id", how="left")
    out = out.merge(snr_values, on="epoch_id", how="left")
    out = out.merge(elev, on="epoch_id", how="left")
    out = out.merge(systems, on="epoch_id", how="left")
    return out


# ---------------------------------------------------------------------------
# Labelling
# ---------------------------------------------------------------------------


def label_epochs(
    epochs: pd.DataFrame,
    plan: pd.DataFrame,
    location_id: Optional[int] = PRIMARY_LOCATION_ID,
) -> pd.DataFrame:
    """Attach ground-truth labels from the transmission plan.

    `label` is the highest-precedence category of any test active at that
    instant in the selected test area. `contaminated` marks epochs that fall
    inside a transmission window of some *other* test area: those are neither
    confidently clean nor confidently attacked, and are excluded from headline
    metrics rather than silently counted as clean.
    """
    out = epochs.copy()
    out["label"] = "clean"
    out["test_id"] = ""
    out["contaminated"] = False
    rank = np.full(len(out), _RANK["clean"], dtype=int)

    ts = out["ts"].values.astype("datetime64[ns]")

    if location_id is None:
        local, other = plan, plan.iloc[0:0]
    else:
        local = plan[plan["location_id"] == location_id]
        other = plan[plan["location_id"] != location_id]

    label = out["label"].to_numpy(copy=True)
    test_id = out["test_id"].to_numpy(copy=True)

    for _, w in local.iterrows():
        if w["category"] == "clean":
            continue
        mask = (ts >= w["start_utc"].to_datetime64()) & (ts < w["end_utc"].to_datetime64())
        if not mask.any():
            continue
        better = mask & (int(w["rank"]) < rank)
        label[better] = w["category"]
        test_id[better] = w["test_id"]
        rank[better] = int(w["rank"])

    out["label"] = label
    out["test_id"] = test_id

    contaminated = np.zeros(len(out), dtype=bool)
    for _, w in other.iterrows():
        if w["category"] == "clean":
            continue
        contaminated |= (ts >= w["start_utc"].to_datetime64()) & (
            ts < w["end_utc"].to_datetime64()
        )
    out["contaminated"] = contaminated

    out["is_attack"] = out["label"].isin(ATTACK_LABELS)
    # Confidently clean: no transmission anywhere, in any area.
    out["is_clean"] = (~out["is_attack"]) & (~out["contaminated"]) & (
        out["label"] == "clean"
    )
    return out


# ---------------------------------------------------------------------------
# Bridge to the streaming detection path
# ---------------------------------------------------------------------------


def _snr_list(value) -> list[int]:
    """Normalise a stored SNR column entry to a plain list of ints.

    Parquet returns these as numpy arrays, and a missing entry as NaN rather
    than None, so neither a truthiness test nor `is None` alone is enough.
    """
    if value is None:
        return []
    if isinstance(value, float) and value != value:  # NaN
        return []
    try:
        return [int(v) for v in value]
    except TypeError:
        return []


def iter_epochs(frame: pd.DataFrame) -> Iterator[Epoch]:
    """Yield `Epoch` records so dataset rows and live NMEA share one code path.

    `time_source` is set to "host_receive" because the dataset preserves the
    node's arrival timestamp, not the receiver's claimed UTC. Detectors that
    compare GPS time against a reference must refuse these, and do.
    """
    for row in frame.itertuples(index=False):
        yield Epoch(
            time_key=None,
            utc=row.ts.to_pydatetime() if pd.notna(row.ts) else None,
            time_source="host_receive",
            lat=None if pd.isna(row.lat) else float(row.lat),
            lon=None if pd.isna(row.lon) else float(row.lon),
            altitude_m=None if pd.isna(row.altitude_m) else float(row.altitude_m),
            fix_quality=None if pd.isna(row.fix_quality) else int(row.fix_quality),
            hdop=None if pd.isna(row.hdop) else float(row.hdop),
            pdop=None if pd.isna(row.pdop) else float(row.pdop),
            vdop=None if pd.isna(row.vdop) else float(row.vdop),
            sog_knots=None if pd.isna(row.sog_knots) else float(row.sog_knots),
            cog_deg=None if pd.isna(row.cog_deg) else float(row.cog_deg),
            sats_in_view=None if pd.isna(row.sats_in_view) else int(row.sats_in_view),
            # Explicit None check: the value is a numpy array when present, and
            # `or []` would evaluate its truth value and raise.
            snr=_snr_list(getattr(row, "snr_values", None)),
            n_sentences=int(row.n_rows),
        )
