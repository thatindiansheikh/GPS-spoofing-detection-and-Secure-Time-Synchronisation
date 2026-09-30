"""Assembly of NMEA sentences into per-second epochs.

A receiver emits a burst of sentences per fix cycle, typically GGA, GSA, several
GSV, RMC and VTG, all describing the same instant. The detection layer wants one
record per instant, not a stream of partial views, so sentences are accumulated
until the reported time changes.

Cycle boundaries are keyed on the timestamp field rather than on a particular
sentence type, because sentence ordering varies between receivers and a log may
start mid-cycle. GSV carries no timestamp and is therefore attributed to the
cycle in progress when it arrives; for receivers that emit GSV ahead of GGA this
shifts satellite-view data by one epoch, which is noted as a known limitation
and does not affect the per-epoch statistics used downstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date, datetime, time as _time, timezone
from typing import Any, Iterable, Iterator, Optional

from .parser import ParsedLine, ParseStats, parse_line, to_float, to_int

KNOTS_TO_MPS = 0.514444


@dataclass(frozen=True)
class SatelliteView:
    """One satellite as the receiver reported it in GSV.

    `snr` is None when the satellite is in view but not being tracked, which is
    a meaningful state and not the same as a weak signal.
    """

    prn: str
    talker: Optional[str] = None
    elevation_deg: Optional[int] = None
    azimuth_deg: Optional[int] = None
    snr: Optional[int] = None

    @property
    def tracked(self) -> bool:
        return self.snr is not None and self.snr > 0

    @property
    def has_sky_position(self) -> bool:
        return self.elevation_deg is not None and self.azimuth_deg is not None


@dataclass
class Epoch:
    """One fix cycle, assembled from every sentence that described it."""

    time_key: Optional[str] = None
    utc: Optional[datetime] = None

    # Position (GGA)
    lat: Optional[float] = None
    lon: Optional[float] = None
    altitude_m: Optional[float] = None
    fix_quality: Optional[int] = None
    num_sats_used: Optional[int] = None
    hdop: Optional[float] = None

    # Dilution of precision (GSA)
    pdop: Optional[float] = None
    vdop: Optional[float] = None

    # Velocity (RMC / VTG)
    sog_knots: Optional[float] = None
    cog_deg: Optional[float] = None
    rmc_valid: Optional[bool] = None

    # Satellites in view (GSV)
    sats_in_view: Optional[int] = None
    #: SNR of tracked satellites only. Entries are dropped for satellites that
    #: report no SNR, so this list is *not* index-aligned with `prn`. The
    #: detectors want exactly that: an untracked satellite has no signal
    #: strength to average, and scoring it as zero would bias the uniformity
    #: statistic. Anything that needs SNR per satellite wants `sat_snr`.
    snr: list[int] = field(default_factory=list)
    elevation: list[Optional[int]] = field(default_factory=list)
    azimuth: list[Optional[int]] = field(default_factory=list)
    prn: list[str] = field(default_factory=list)
    #: SNR aligned one-to-one with `prn`, keeping None where the receiver
    #: reported a satellite in view but was not tracking it. This is the view a
    #: sky plot needs; `snr` above is the view the detectors need.
    sat_snr: list[Optional[int]] = field(default_factory=list)
    #: Talker id per satellite ("GP", "GL", "GA", "GB", ...). PRN alone is
    #: ambiguous across constellations, so the talker that carried the GSV is
    #: kept in order to name the constellation correctly.
    sat_talker: list[Optional[str]] = field(default_factory=list)

    # Assembly bookkeeping
    types_seen: set[str] = field(default_factory=set)
    n_sentences: int = 0
    wall_time: Optional[float] = None

    # Provenance of `utc`. "gps" means the receiver reported this time in RMC
    # or GGA. "host_receive" means it is the host's clock at the moment the
    # sentence arrived, which is a different quantity entirely: it cannot be
    # used to detect a time-spoofing attack, because a spoofed receiver's
    # claimed time is precisely what is missing from it. Detectors that compare
    # GPS time against a reference must refuse anything but "gps".
    time_source: str = "gps"

    @property
    def sog_mps(self) -> Optional[float]:
        return None if self.sog_knots is None else self.sog_knots * KNOTS_TO_MPS

    @property
    def has_fix(self) -> bool:
        """A usable position fix.

        fix_quality 0 means no fix; RMC status 'V' means the data is flagged
        invalid by the receiver. Either one disqualifies the epoch.
        """
        if self.fix_quality is not None and self.fix_quality == 0:
            return False
        if self.rmc_valid is False:
            return False
        return self.lat is not None and self.lon is not None

    @property
    def has_position(self) -> bool:
        return self.lat is not None and self.lon is not None

    @property
    def satellites(self) -> list[SatelliteView]:
        """The satellite view as one record per satellite.

        PRN "0" is a padding entry some receivers emit to fill out a GSV
        sentence; it names no satellite and is dropped. Duplicates are dropped
        too, keeping the first report, because a cycle that repeats a GSV set
        would otherwise show the same satellite twice in the sky.
        """
        out: list[SatelliteView] = []
        seen: set[tuple[Optional[str], str]] = set()
        for i, prn in enumerate(self.prn):
            if not prn or prn.strip("0") == "":
                continue
            talker = self.sat_talker[i] if i < len(self.sat_talker) else None
            key = (talker, prn)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                SatelliteView(
                    prn=prn,
                    talker=talker,
                    elevation_deg=self.elevation[i] if i < len(self.elevation) else None,
                    azimuth_deg=self.azimuth[i] if i < len(self.azimuth) else None,
                    snr=self.sat_snr[i] if i < len(self.sat_snr) else None,
                )
            )
        return out


def _combine(d: Optional[_date], t: Optional[_time]) -> Optional[datetime]:
    if t is None:
        return None
    if d is None:
        return None
    return datetime.combine(d, t).replace(tzinfo=timezone.utc)


class EpochAssembler:
    """Feeds on ParsedLine objects and emits completed Epochs."""

    def __init__(self) -> None:
        self._current: Optional[Epoch] = None
        self._last_date: Optional[_date] = None

    def push(self, parsed: ParsedLine, wall_time: Optional[float] = None) -> Optional[Epoch]:
        """Add one sentence. Returns a completed Epoch when a cycle closes."""
        if not parsed.used:
            return None

        msg = parsed.msg
        stype = parsed.sentence_type
        completed: Optional[Epoch] = None

        time_key = self._time_key(msg, stype)

        if time_key is not None:
            if self._current is None:
                self._current = Epoch(time_key=time_key, wall_time=wall_time)
            elif self._current.time_key is None:
                self._current.time_key = time_key
            elif time_key != self._current.time_key:
                completed = self._finish(self._current)
                self._current = Epoch(time_key=time_key, wall_time=wall_time)
        elif self._current is None:
            # GSV arriving before any timestamped sentence: open an epoch
            # anyway so the satellite view is not lost.
            self._current = Epoch(wall_time=wall_time)

        self._apply(self._current, msg, stype)
        self._current.n_sentences += 1
        self._current.types_seen.add(stype)
        if self._current.wall_time is None:
            self._current.wall_time = wall_time

        return completed

    def flush(self) -> Optional[Epoch]:
        """Close any cycle still in progress; call at end of stream."""
        if self._current is None:
            return None
        done = self._finish(self._current)
        self._current = None
        return done

    # -- internals -------------------------------------------------------

    @staticmethod
    def _time_key(msg: Any, stype: Optional[str]) -> Optional[str]:
        if stype not in ("GGA", "RMC", "VTG"):
            return None
        ts = getattr(msg, "timestamp", None)
        if ts is None:
            return None
        return ts.isoformat()

    def _apply(self, ep: Epoch, msg: Any, stype: Optional[str]) -> None:
        if stype == "GGA":
            ep.lat = _safe_coord(msg, "latitude")
            ep.lon = _safe_coord(msg, "longitude")
            ep.altitude_m = to_float(getattr(msg, "altitude", None))
            ep.fix_quality = to_int(getattr(msg, "gps_qual", None))
            ep.num_sats_used = to_int(getattr(msg, "num_sats", None))
            ep.hdop = to_float(getattr(msg, "horizontal_dil", None))

        elif stype == "RMC":
            status = getattr(msg, "status", None)
            ep.rmc_valid = (status == "A") if status else None
            if ep.lat is None:
                ep.lat = _safe_coord(msg, "latitude")
                ep.lon = _safe_coord(msg, "longitude")
            spd = to_float(getattr(msg, "spd_over_grnd", None))
            if spd is not None:
                ep.sog_knots = spd
            crs = to_float(getattr(msg, "true_course", None))
            if crs is not None:
                ep.cog_deg = crs
            d = getattr(msg, "datestamp", None)
            if isinstance(d, _date):
                self._last_date = d

        elif stype == "GSA":
            ep.pdop = to_float(getattr(msg, "pdop", None))
            if ep.hdop is None:
                ep.hdop = to_float(getattr(msg, "hdop", None))
            ep.vdop = to_float(getattr(msg, "vdop", None))

        elif stype == "VTG":
            spd = to_float(getattr(msg, "spd_over_grnd_kts", None))
            if spd is not None and ep.sog_knots is None:
                ep.sog_knots = spd
            crs = to_float(getattr(msg, "true_track", None))
            if crs is not None and ep.cog_deg is None:
                ep.cog_deg = crs

        elif stype == "GSV":
            n_view = to_int(getattr(msg, "num_sv_in_view", None))
            if n_view is not None:
                ep.sats_in_view = n_view
            # Each GSV sentence carries up to four satellites; a full view is
            # split across num_messages sentences which we accumulate.
            talker = getattr(msg, "talker", None)
            for i in range(1, 5):
                prn = getattr(msg, f"sv_prn_num_{i}", None)
                if prn is None or str(prn).strip() == "":
                    continue
                ep.prn.append(str(prn).strip())
                ep.elevation.append(to_int(getattr(msg, f"elevation_deg_{i}", None)))
                ep.azimuth.append(to_int(getattr(msg, f"azimuth_{i}", None)))
                snr = to_int(getattr(msg, f"snr_{i}", None))
                ep.sat_snr.append(snr)
                ep.sat_talker.append(str(talker) if talker else None)
                # An empty SNR field means the satellite is visible but not
                # tracked. Dropping it is correct: including it as zero would
                # bias the uniformity statistic.
                if snr is not None:
                    ep.snr.append(snr)

    def _finish(self, ep: Epoch) -> Epoch:
        if ep.time_key is not None and self._last_date is not None:
            try:
                ep.utc = _combine(self._last_date, _time.fromisoformat(ep.time_key))
            except ValueError:
                ep.utc = None
        return ep


def _safe_coord(msg: Any, attr: str) -> Optional[float]:
    """pynmea2 raises on malformed coordinate fields rather than returning None."""
    try:
        value = getattr(msg, attr, None)
    except Exception:
        return None
    value = to_float(value)
    if value is None or value == 0.0:
        # Exactly zero is what an unset field decodes to; a receiver genuinely
        # at 0.000000 in the Gulf of Guinea is not a case worth supporting.
        return None
    return value


def epochs_from_sentences(
    sentences: Iterable[str],
    stats: Optional[ParseStats] = None,
) -> Iterator[Epoch]:
    """Parse and assemble in one pass."""
    assembler = EpochAssembler()
    for sentence in sentences:
        parsed = parse_line(sentence, stats)
        done = assembler.push(parsed)
        if done is not None:
            yield done
    tail = assembler.flush()
    if tail is not None:
        yield tail
