"""Train and test split for the JammerTest corpus.

The split is **by day**, not at random.

A random split would be indefensible here. Epochs arrive at 1 Hz and adjacent
ones are almost identical, so shuffling would put near-duplicates of the same
second on both sides and every threshold would look excellent for a reason that
has nothing to do with generalisation. Splitting by whole days keeps a test
attack entirely unseen during calibration.

Days 15 and 16 September calibrate; 17 and 18 evaluate. The division is by
calendar rather than by attack type, so the test days contain their own mix of
jamming, spoofing and meaconing rather than a class the calibration never met.

19 September is absent from the dataset despite appearing in the transmission
plan, so only four days exist.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

TRAIN_DAYS: tuple[date, ...] = (date(2025, 9, 15), date(2025, 9, 16))
TEST_DAYS: tuple[date, ...] = (date(2025, 9, 17), date(2025, 9, 18))


def _mask(frame: pd.DataFrame, days: Iterable[date]) -> pd.Series:
    wanted = set(days)
    return frame["ts"].dt.date.isin(wanted)


def train(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[_mask(frame, TRAIN_DAYS)].copy()


def test(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[_mask(frame, TEST_DAYS)].copy()


def describe(frame: pd.DataFrame) -> str:
    tr, te = train(frame), test(frame)
    other = len(frame) - len(tr) - len(te)
    return (
        f"train {len(tr):,} epochs ({', '.join(str(d) for d in TRAIN_DAYS)}), "
        f"test {len(te):,} epochs ({', '.join(str(d) for d in TEST_DAYS)})"
        + (f", {other:,} outside both" if other else "")
    )
