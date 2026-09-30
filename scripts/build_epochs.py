"""Build the labelled per-epoch table from the JammerTest dataset.

Output: data/baseline/epochs.parquet, one row per fix cycle per receiver
module, with ground-truth labels from the published transmission plan.

This is the slow step (it reads ~250 MB of CSV), so the result is cached and
everything downstream reads the parquet.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpstrust.datasets import jammertest  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "baseline"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("Loading transmission plan ...")
    plan = jammertest.load_plan(RAW / "jammertest-plan")
    catalog = jammertest.load_catalog(RAW / "jammertest-plan")
    print(f"  {len(plan)} test windows, {len(catalog)} catalogue groups")

    print("Building epochs from gps.csv + constellation.csv ...")
    epochs = jammertest.load_epochs(RAW, module_id=None, with_snr=True)
    print(f"  {len(epochs):,} epochs in {time.time() - t0:.1f}s")

    print("Labelling against the plan ...")
    labelled = jammertest.label_epochs(epochs, plan)

    print()
    print("Label distribution:")
    counts = labelled["label"].value_counts()
    for name, n in counts.items():
        print(f"  {name:22s} {n:>9,}  {n / len(labelled):6.2%}")
    print()
    print(f"  attack epochs      {labelled.is_attack.sum():>9,}")
    print(f"  confidently clean  {labelled.is_clean.sum():>9,}")
    print(f"  contaminated       {labelled.contaminated.sum():>9,}")

    path = OUT / "epochs.parquet"
    labelled.to_parquet(path, index=False)
    plan.to_parquet(OUT / "plan.parquet", index=False)
    catalog.to_parquet(OUT / "catalog.parquet", index=False)
    print()
    print(f"Written {path} ({path.stat().st_size / 1e6:.1f} MB) in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
