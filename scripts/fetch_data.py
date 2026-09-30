"""Download the public datasets this project is built on.

Everything here is read-only retrieval of public data. Nothing is uploaded.
Re-running is safe: a file whose size already matches is left alone.

A manifest with SHA-256 and retrieval time is written alongside the data so the
exact bytes used in the evaluation can be identified later. This matters because
two of these sources are live repositories that may change.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

HF = "https://huggingface.co/datasets/SimulaMet/gnss-nmea-jammertest25/resolve/main"
PLAN = "https://raw.githubusercontent.com/NPRA/jammertest-plan/main"
GPSD = "https://gitlab.com/gpsd/gpsd/-/archive/master/gpsd-master.tar.gz?path=test/daemon"


@dataclass
class Item:
    dest: str
    url: str
    source: str
    licence: str
    note: str
    optional: bool = False


ITEMS: list[Item] = [
    # --- Real receiver telemetry under real jamming/spoofing -------------
    Item(
        "jammertest25/gps.csv",
        f"{HF}/gps.csv",
        "SimulaMet/gnss-nmea-jammertest25 (HuggingFace)",
        "CC-BY-4.0",
        "RMC/GGA-derived. Stationary Sierra 7455 modules, Andoya, Sept 2025.",
    ),
    Item(
        "jammertest25/constellation.csv",
        f"{HF}/constellation.csv",
        "SimulaMet/gnss-nmea-jammertest25 (HuggingFace)",
        "CC-BY-4.0",
        "GSV-derived per-satellite elevation/azimuth/SNR.",
    ),
    Item(
        "jammertest25/README.md",
        f"{HF}/README.md",
        "SimulaMet/gnss-nmea-jammertest25 (HuggingFace)",
        "CC-BY-4.0",
        "Dataset card, including the citation to record in the report.",
    ),
    # --- Ground-truth attack schedule ------------------------------------
    Item(
        "jammertest-plan/testcatalog2025.json",
        f"{PLAN}/testcatalog2025.json",
        "NPRA/jammertest-plan (GitHub)",
        "MIT",
        "Maps test ids to attack type, equipment, band and power.",
    ),
    *[
        Item(
            f"jammertest-plan/plan-{day}.json",
            f"{PLAN}/plan-{day}.json",
            "NPRA/jammertest-plan (GitHub)",
            "MIT",
            "Per-test start/end times: the label source.",
        )
        for day in (
            "monday-2025-09-15",
            "tuesday-2025-09-16",
            "wednesday-2025-09-17",
            "thursday-2025-09-18",
            "friday-2025-09-19",
        )
    ],
    Item(
        "jammertest-plan/LICENSE",
        f"{PLAN}/LICENSE",
        "NPRA/jammertest-plan (GitHub)",
        "MIT",
        "Licence text retained with the data.",
    ),
    # --- Dirty real NMEA for parser robustness ---------------------------
    Item(
        "gpsd/gpsd-test-daemon.tar.gz",
        GPSD,
        "gpsd project (GitLab)",
        "BSD-2-Clause",
        "199 real captures across ~50 receiver models; the dirty-data corpus.",
    ),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def remote_size(url: str) -> int | None:
    try:
        r = requests.head(url, allow_redirects=True, timeout=30)
        n = r.headers.get("content-length")
        return int(n) if n else None
    except requests.RequestException:
        return None


def fetch(item: Item) -> dict:
    dest = RAW / item.dest
    dest.parent.mkdir(parents=True, exist_ok=True)

    expected = remote_size(item.url)
    if dest.exists() and expected is not None and dest.stat().st_size == expected:
        print(f"  [skip] {item.dest} ({expected:,} bytes, already present)")
    else:
        print(f"  [get ] {item.dest} ...", end="", flush=True)
        with requests.get(item.url, stream=True, timeout=120) as r:
            r.raise_for_status()
            tmp = dest.with_suffix(dest.suffix + ".part")
            written = 0
            with tmp.open("wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
                    written += len(chunk)
            tmp.replace(dest)
        print(f" {written:,} bytes")

    return {
        "path": item.dest,
        "url": item.url,
        "source": item.source,
        "licence": item.licence,
        "note": item.note,
        "bytes": dest.stat().st_size,
        "sha256": sha256(dest),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    print(f"Fetching into {RAW}")
    records = []
    failures = []
    for item in ITEMS:
        try:
            records.append(fetch(item))
        except Exception as exc:
            failures.append((item.dest, str(exc)))
            print(f"  [FAIL] {item.dest}: {exc}")

    manifest = RAW / "manifest.json"
    manifest.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nManifest written: {manifest}")
    print(f"{len(records)} ok, {len(failures)} failed")
    for name, err in failures:
        print(f"  FAILED {name}: {err}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
