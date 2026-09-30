"""Position and satellite presentation helpers.

Everything here turns a number the receiver reported into something a person
can read: degrees into degrees-minutes-seconds, a PRN into the name of the
constellation that owns it, a coordinate pair into a street address.

The address lookup is the only part of this project that talks to the network
at display time, and it is deliberately the only part: it is off unless the
operator turns it on, it never runs during clean playback more than once per
distinct location, and nothing downstream of it feeds a detector. Detection
must not depend on a third party being reachable.
"""

from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional

NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "gpstrust-monitor/1.0 (GNSS spoofing research dashboard)"

#: Minimum seconds between calls. Nominatim's usage policy allows one request
#: per second; the cache means we rarely come close, but a slider dragged
#: across a drifting track could, so the floor is enforced here as well.
MIN_INTERVAL_S = 1.1
_last_call = 0.0


# ---------------------------------------------------------------------------
# Constellations
# ---------------------------------------------------------------------------

#: NMEA talker id -> constellation. The talker is authoritative; PRN ranges are
#: only a fallback, because the same PRN number means different satellites on
#: different systems and a receiver that reports BeiDou PRN 13 on the $BD
#: talker is not reporting GPS 13.
TALKERS = {
    "GP": ("GPS", "#10b981"),
    "GL": ("GLONASS", "#3b82f6"),
    "GA": ("Galileo", "#8b5cf6"),
    "GB": ("BeiDou", "#f59e0b"),
    "BD": ("BeiDou", "#f59e0b"),
    "GQ": ("QZSS", "#ec4899"),
    "QZ": ("QZSS", "#ec4899"),
    "GI": ("NavIC", "#0ea5e9"),
    "GN": ("multi-GNSS", "#94a3b8"),
}

UNKNOWN_CONSTELLATION = ("unknown", "#64748b")


def constellation(talker: Optional[str], prn: str) -> tuple[str, str]:
    """Name and colour for a satellite, preferring the talker id."""
    if talker:
        hit = TALKERS.get(talker.upper())
        if hit and hit[0] != "multi-GNSS":
            return hit

    # Fallback on the NMEA 0183 PRN allocation, which is only meaningful for a
    # mixed "GN" talker or a log with the talker stripped.
    try:
        n = int(prn)
    except (TypeError, ValueError):
        return UNKNOWN_CONSTELLATION
    if 1 <= n <= 32:
        return TALKERS["GP"]
    if 33 <= n <= 64:
        return ("SBAS", "#f43f5e")
    if 65 <= n <= 96:
        return TALKERS["GL"]
    if 193 <= n <= 202:
        return TALKERS["GQ"]
    if 301 <= n <= 336:
        return TALKERS["GA"]
    return UNKNOWN_CONSTELLATION


# ---------------------------------------------------------------------------
# Coordinate formatting
# ---------------------------------------------------------------------------


def dms(value: Optional[float], is_lat: bool) -> str:
    """Decimal degrees as degrees, minutes and seconds with a hemisphere."""
    if value is None:
        return "--"
    hemi = ("N" if value >= 0 else "S") if is_lat else ("E" if value >= 0 else "W")
    v = abs(value)
    d = int(v)
    m_full = (v - d) * 60
    m = int(m_full)
    s = (m_full - m) * 60
    return f"{d:d}° {m:02d}' {s:05.2f}\" {hemi}"


def decimal(value: Optional[float], places: int = 6) -> str:
    return "--" if value is None else f"{value:.{places}f}°"


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from point one to point two, degrees from true north."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def compass(bearing: float) -> str:
    points = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return points[int((bearing + 11.25) % 360 / 22.5)]


def utc_offset_estimate(lon: Optional[float]) -> str:
    """Solar time zone from longitude.

    Labelled as an estimate everywhere it is shown, because it is geometry, not
    a time zone database: it ignores political boundaries and daylight saving.
    It is here because a receiver's longitude drifting into a different offset
    is a quick sanity check on a spoofed position.
    """
    if lon is None:
        return "--"
    hours = round(lon / 15.0)
    return f"UTC{hours:+d}"


# ---------------------------------------------------------------------------
# Reverse geocoding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Place:
    line: str
    detail: str
    country: str
    ok: bool = True


def _compose(address: dict, display: str) -> Place:
    """Pick the useful parts out of Nominatim's address breakdown."""
    road = address.get("road") or address.get("pedestrian") or address.get("neighbourhood")
    number = address.get("house_number")
    locality = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or address.get("suburb")
        or address.get("county")
    )
    region = address.get("state") or address.get("region") or ""
    country = address.get("country") or ""
    postcode = address.get("postcode") or ""

    street = " ".join(x for x in (number, road) if x)
    line = street or locality or display.split(",")[0]
    detail = ", ".join(x for x in (locality if street else None, region, postcode) if x)
    return Place(line=line, detail=detail or display, country=country)


def reverse_geocode(lat: float, lon: float, timeout: float = 6.0) -> Place:
    """Street-level address for a coordinate, or a stated failure.

    Never raises. A failed lookup is reported as a failed lookup rather than
    silently blanked, so an operator can tell "no network" from "middle of the
    ocean".
    """
    global _last_call

    wait = MIN_INTERVAL_S - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()

    query = urllib.parse.urlencode(
        {"format": "jsonv2", "lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "zoom": "16"}
    )
    request = urllib.request.Request(
        f"{NOMINATIM}?{query}", headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # network, DNS, rate limit, malformed JSON
        return Place(
            line="lookup unavailable",
            detail=f"{type(exc).__name__}",
            country="",
            ok=False,
        )

    if "error" in payload:
        return Place(line="no address at this coordinate", detail="open water or unmapped",
                     country="", ok=True)

    return _compose(payload.get("address", {}) or {}, payload.get("display_name", ""))
