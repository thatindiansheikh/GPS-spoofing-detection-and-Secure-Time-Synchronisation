"""Event log.

An incident is investigated after the fact, so what the system recorded at the
time is the only evidence available later. Two things follow from that.

The log keeps the *reasons*, not just the verdicts. "Trust fell to 0.34" is
useless six weeks later; "position 2,840 m from reference, SNR spread 0.02
below clean p1" can be argued with.

Timestamps are stored twice: the receiver's claimed time and the host's
arrival time. During a time-spoofing attack these disagree, and a log that
recorded only the first would be timestamped by the attacker. Ordering the log
by GPS time would then reorder or bury the very entries describing the attack.
Host time is the ordering key for exactly that reason.

SQLite because it needs no server, the file is the artefact, and it can be
queried with standard tools while the system is still running.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

from .detect.base import Evidence
from .trust import TrustVerdict

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    started_host  REAL NOT NULL,
    source        TEXT,
    note          TEXT
);

CREATE TABLE IF NOT EXISTS epochs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES runs(id),
    host_time     REAL NOT NULL,
    gps_time      REAL,
    time_source   TEXT,
    lat           REAL,
    lon           REAL,
    deviation_m   REAL,
    fix_quality   INTEGER,
    sats_in_view  INTEGER,
    hdop          REAL,
    snr_mean      REAL,
    snr_cv        REAL,
    trust         REAL,
    state         TEXT,
    active_source TEXT,
    served_time   REAL,
    uncertainty_s REAL
);

CREATE TABLE IF NOT EXISTS detections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES runs(id),
    epoch_id      INTEGER NOT NULL REFERENCES epochs(id),
    host_time     REAL NOT NULL,
    detector      TEXT NOT NULL,
    score         REAL NOT NULL,
    value         REAL,
    warn          REAL,
    alarm         REAL,
    reason        TEXT
);

CREATE TABLE IF NOT EXISTS source_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES runs(id),
    host_time     REAL NOT NULL,
    from_source   TEXT,
    to_source     TEXT,
    step_s        REAL,
    reason        TEXT
);

-- Ordered by host time, never by GPS time: during a time-spoofing attack the
-- receiver's clock is under the attacker's control and would reorder the log.
CREATE INDEX IF NOT EXISTS idx_epochs_host   ON epochs(run_id, host_time);
CREATE INDEX IF NOT EXISTS idx_detect_host   ON detections(run_id, host_time);
CREATE INDEX IF NOT EXISTS idx_detect_which  ON detections(run_id, detector);
CREATE INDEX IF NOT EXISTS idx_events_host   ON source_events(run_id, host_time);
"""


@dataclass
class EventStore:
    """Append-only log of what the system saw and what it decided."""

    path: str | Path = "gpstrust.db"
    run_id: Optional[int] = None

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # -- lifecycle ---------------------------------------------------------

    def start_run(self, source: str = "", note: str = "") -> int:
        cur = self._conn.execute(
            "INSERT INTO runs (started_host, source, note) VALUES (?, ?, ?)",
            (time.time(), source, note),
        )
        self._conn.commit()
        self.run_id = int(cur.lastrowid)
        return self.run_id

    def close(self) -> None:
        self._conn.commit()
        self._conn.close()

    # -- writing -----------------------------------------------------------

    def record(
        self,
        epoch,
        evidence: Sequence[Evidence],
        verdict: Optional[TrustVerdict],
        decision=None,
        host_time: Optional[float] = None,
        deviation_m: Optional[float] = None,
    ) -> int:
        """Log one epoch, and every detector that had something to say about it.

        Only firing detectors are written to `detections`. A quiet detector
        produces one row per epoch per detector otherwise, which at 1 Hz across
        eight detectors is nearly seven hundred thousand rows a day of nothing. The
        per-epoch trust score already records that nothing fired.
        """
        if self.run_id is None:
            self.start_run()

        now = time.time() if host_time is None else host_time
        tracked = [s for s in getattr(epoch, "snr", []) if s and s > 0]
        snr_mean = sum(tracked) / len(tracked) if tracked else None
        snr_cv = None
        if snr_mean and len(tracked) >= 4:
            var = sum((s - snr_mean) ** 2 for s in tracked) / len(tracked)
            snr_cv = (var ** 0.5) / snr_mean

        cur = self._conn.execute(
            """INSERT INTO epochs (
                   run_id, host_time, gps_time, time_source, lat, lon,
                   deviation_m, fix_quality, sats_in_view, hdop, snr_mean,
                   snr_cv, trust, state, active_source, served_time, uncertainty_s
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                self.run_id,
                now,
                epoch.utc.timestamp() if getattr(epoch, "utc", None) else None,
                getattr(epoch, "time_source", None),
                epoch.lat,
                epoch.lon,
                deviation_m,
                epoch.fix_quality,
                epoch.sats_in_view,
                epoch.hdop,
                snr_mean,
                snr_cv,
                None if verdict is None else verdict.trust,
                None if verdict is None else verdict.state.value,
                None if decision is None else decision.source.value,
                None if decision is None else decision.time_s,
                None if decision is None else decision.uncertainty_s,
            ),
        )
        epoch_id = int(cur.lastrowid)

        rows = [
            (self.run_id, epoch_id, now, e.detector, e.score,
             e.value, e.warn, e.alarm, e.reason)
            for e in evidence
            if e.applicable and e.score > 0
        ]
        if rows:
            self._conn.executemany(
                """INSERT INTO detections (
                       run_id, epoch_id, host_time, detector, score,
                       value, warn, alarm, reason
                   ) VALUES (?,?,?,?,?,?,?,?,?)""",
                rows,
            )
        return epoch_id

    def record_source_events(self, events: Iterable) -> int:
        """Persist source switches that the manager has accumulated."""
        if self.run_id is None:
            self.start_run()
        rows = [
            (self.run_id, e.at, e.from_source.value, e.to_source.value,
             e.step_s, e.reason)
            for e in events
        ]
        if not rows:
            return 0
        self._conn.executemany(
            """INSERT INTO source_events (
                   run_id, host_time, from_source, to_source, step_s, reason
               ) VALUES (?,?,?,?,?,?)""",
            rows,
        )
        self._conn.commit()
        return len(rows)

    def commit(self) -> None:
        self._conn.commit()

    # -- reading -----------------------------------------------------------

    def recent_epochs(self, limit: int = 600, run_id: Optional[int] = None):
        rid = run_id if run_id is not None else self.run_id
        cur = self._conn.execute(
            "SELECT * FROM epochs WHERE run_id = ? ORDER BY host_time DESC LIMIT ?",
            (rid, limit),
        )
        return [dict(r) for r in cur.fetchall()][::-1]

    def recent_detections(self, limit: int = 200, run_id: Optional[int] = None):
        rid = run_id if run_id is not None else self.run_id
        cur = self._conn.execute(
            "SELECT * FROM detections WHERE run_id = ? ORDER BY host_time DESC LIMIT ?",
            (rid, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def source_events(self, run_id: Optional[int] = None):
        rid = run_id if run_id is not None else self.run_id
        cur = self._conn.execute(
            "SELECT * FROM source_events WHERE run_id = ? ORDER BY host_time",
            (rid,),
        )
        return [dict(r) for r in cur.fetchall()]

    def runs(self):
        cur = self._conn.execute("SELECT * FROM runs ORDER BY started_host DESC")
        return [dict(r) for r in cur.fetchall()]

    def detector_summary(self, run_id: Optional[int] = None):
        rid = run_id if run_id is not None else self.run_id
        cur = self._conn.execute(
            """SELECT detector, COUNT(*) AS firings, AVG(score) AS mean_score,
                      MAX(score) AS max_score
               FROM detections WHERE run_id = ?
               GROUP BY detector ORDER BY firings DESC""",
            (rid,),
        )
        return [dict(r) for r in cur.fetchall()]
