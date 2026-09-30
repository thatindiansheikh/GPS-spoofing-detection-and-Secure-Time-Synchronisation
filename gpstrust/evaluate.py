"""Scoring and metric helpers shared by the tuning and evaluation scripts.

Detector scores do not depend on how they are later fused, so they are computed
once and cached. Fusion variants are then replayed over the cached scores. That
keeps a four-way comparison of combiner and weighting honest - every variant
sees byte-identical detector output - and fast enough to iterate on.

The trust engine is stateful, so fusion is genuinely replayed rather than
recomputed as a column expression: the hysteresis in the source-state machine
depends on the order epochs arrive in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Calibration
from .datasets import jammertest
from .detect import build_default_suite
from .trust import TrustConfig, TrustEngine

MIN_HOURLY_DENSITY = 0.80

# Deviation above which a scheduled-clean epoch is the residue documented in
# docs/data-validity.md: a discrete spoofed position, not receiver scatter.
RESIDUE_DEVIATION_M = 1000.0


def densely_logged(epochs: pd.DataFrame) -> pd.DataFrame:
    """Drop hours where logging was sparse enough that a gap could mimic an event."""
    epochs = epochs.sort_values("ts")
    hour = epochs["ts"].dt.floor("h")
    counts = epochs.groupby([hour, "module_id"]).size().rename("n").reset_index()
    counts["density"] = counts["n"] / 3600.0
    keep = set(
        map(tuple, counts.loc[counts["density"] >= MIN_HOURLY_DENSITY, ["ts", "module_id"]].values)
    )
    mask = [(h, m) in keep for h, m in zip(hour, epochs["module_id"])]
    return epochs[mask]


def score_epochs(frame: pd.DataFrame, calibration: Calibration) -> pd.DataFrame:
    """Run every detector over the frame and return one row of scores per epoch.

    Modules are streamed separately. They are independent receivers, and running
    them as one sequence would invent a position jump at every module boundary.
    """
    out = []
    for module_id, sub in frame.groupby("module_id", sort=True):
        detectors = build_default_suite(calibration, reference=None)
        meta = sub[["ts", "label", "is_attack", "is_clean", "position_deviation_m"]]
        for epoch, row in zip(jammertest.iter_epochs(sub), meta.itertuples(index=False)):
            rec = {
                "module_id": module_id,
                "ts": row.ts,
                "label": row.label,
                "is_attack": bool(row.is_attack),
                "is_clean": bool(row.is_clean),
                "deviation_m": row.position_deviation_m,
            }
            for det in detectors:
                ev = det.update(epoch)
                rec[f"s_{ev.detector}"] = ev.score if ev.applicable else np.nan
            out.append(rec)
    return pd.DataFrame.from_records(out)


def replay_fusion(scores: pd.DataFrame, config: TrustConfig) -> pd.DataFrame:
    """Replay the trust engine over cached detector scores, in time order."""
    from .detect.base import Evidence

    detector_cols = [c for c in scores.columns if c.startswith("s_")]
    trust_out = np.full(len(scores), np.nan)
    state_out = np.empty(len(scores), dtype=object)

    position = 0
    for _, sub in scores.groupby("module_id", sort=True):
        engine = TrustEngine(config)
        sub = sub.sort_values("ts")
        for idx, row in zip(sub.index, sub.itertuples(index=False)):
            evidence = []
            for col in detector_cols:
                value = getattr(row, col)
                name = col[2:]
                if value is None or (isinstance(value, float) and np.isnan(value)):
                    evidence.append(Evidence.not_applicable(name, "not applicable"))
                else:
                    evidence.append(Evidence(detector=name, score=float(value)))
            verdict = engine.evaluate(evidence, now=row.ts.timestamp())
            loc = scores.index.get_loc(idx)
            trust_out[loc] = np.nan if verdict.trust is None else verdict.trust
            state_out[loc] = verdict.state.value
        position += len(sub)

    result = scores.copy()
    result["trust"] = trust_out
    result["state"] = state_out
    return result


def negative_classes(scores: pd.DataFrame):
    """The two negative classes reported side by side.

    `as_labelled` is every epoch the plan calls clean: independent, pessimistic.
    `nominal` removes the demonstrably spoofed residue: optimistic, because the
    removal consults the measurements.
    """
    as_labelled = scores["is_clean"].to_numpy()
    residue = as_labelled & (scores["deviation_m"].to_numpy() > RESIDUE_DEVIATION_M)
    return as_labelled, as_labelled & ~residue, residue


def confusion(pred: np.ndarray, actual: np.ndarray) -> dict:
    tp = int(np.sum(pred & actual))
    fp = int(np.sum(pred & ~actual))
    fn = int(np.sum(~pred & actual))
    tn = int(np.sum(~pred & ~actual))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fp / (fp + tn), 6) if fp + tn else 0.0,
    }
