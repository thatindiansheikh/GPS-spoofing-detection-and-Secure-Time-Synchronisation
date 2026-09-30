"""Attack injection at the NMEA layer.

Transmitting counterfeit GNSS signals is illegal, so attacks here are injected
into the sentence stream instead. The system under test sits after the
receiver and its only input is NMEA, so a receiver under a real spoof and a
real capture with modified sentences present the same interface. What this does
not reproduce is signal-level evidence - correlator distortion, AGC behaviour,
carrier phase - which a real attack would also leave. That limit is stated in
docs/decisions.md and is why the project targets receivers that do not expose
those quantities anyway.

Sentences are modified as text and re-checksummed, not rebuilt from a parsed
object. Two reasons. Field-level editing preserves every quirk of the original
capture - spacing, precision, talker id, trailing empty fields - so the trace
stays as dirty as it started. And because the checksum is recomputed, the
modified sentence is accepted by the parser on its merits; if the injector
produced malformed output the evaluation would be measuring checksum rejection
rather than detection.

The substrate is always a real capture. Only the attack is synthetic. Writing
both the normal data and the attack would make the evaluation circular, which
is the failure mode docs/data-validity.md exists to avoid.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, Optional

from ..nmea.parser import compute_checksum

# Field positions within each sentence type, counting the talker+type token as 0.
GGA_TIME, GGA_LAT, GGA_LAT_DIR, GGA_LON, GGA_LON_DIR = 1, 2, 3, 4, 5
GGA_QUALITY, GGA_NUM_SATS, GGA_HDOP = 6, 7, 8
RMC_TIME, RMC_STATUS, RMC_LAT, RMC_LAT_DIR, RMC_LON, RMC_LON_DIR = 1, 2, 3, 4, 5, 6
RMC_SPEED, RMC_COURSE, RMC_DATE = 7, 8, 9
GSA_PDOP, GSA_HDOP, GSA_VDOP = 15, 16, 17
GSV_NUM_MSGS, GSV_MSG_NUM, GSV_NUM_SV = 1, 2, 3
GSV_FIRST_PRN = 4  # then repeating groups of (prn, elevation, azimuth, snr)

EARTH_M_PER_DEG = 111320.0


# ---------------------------------------------------------------------------
# NMEA coordinate helpers
# ---------------------------------------------------------------------------


def nmea_to_decimal(value: str, direction: str) -> Optional[float]:
    """ddmm.mmmm plus hemisphere to signed decimal degrees."""
    if not value:
        return None
    try:
        raw = float(value)
    except ValueError:
        return None
    degrees = int(raw // 100)
    minutes = raw - degrees * 100
    result = degrees + minutes / 60.0
    if direction in ("S", "W"):
        result = -result
    return result


def decimal_to_nmea(value: float, is_latitude: bool) -> tuple[str, str]:
    """Signed decimal degrees back to ddmm.mmmm plus hemisphere.

    Width is preserved as the standard expects - two degree digits for
    latitude, three for longitude - because a receiver that emitted a
    differently shaped field would be a different receiver.
    """
    direction = ("N" if value >= 0 else "S") if is_latitude else ("E" if value >= 0 else "W")
    magnitude = abs(value)
    degrees = int(magnitude)
    minutes = (magnitude - degrees) * 60.0
    width = 2 if is_latitude else 3
    return f"{degrees:0{width}d}{minutes:07.4f}", direction


def shift_time_field(value: str, seconds: float) -> str:
    """Advance or retard an hhmmss[.sss] field, wrapping at a day."""
    if not value:
        return value
    try:
        whole, _, frac = value.partition(".")
        hours, minutes = int(whole[0:2]), int(whole[2:4])
        secs = int(whole[4:6])
    except (ValueError, IndexError):
        return value
    total = hours * 3600 + minutes * 60 + secs + seconds
    total %= 86400
    if total < 0:
        total += 86400
    h, rem = divmod(int(total), 3600)
    m, s = divmod(rem, 60)
    out = f"{h:02d}{m:02d}{s:02d}"
    return f"{out}.{frac}" if frac else out


# ---------------------------------------------------------------------------
# Scenario definition
# ---------------------------------------------------------------------------


@dataclass
class Context:
    """State passed to a scenario for each sentence."""

    epoch: int          # fix cycles seen so far
    total_epochs: int   # total in the trace, for placing the attack window
    attacking: bool
    elapsed: int        # fix cycles since the attack began


@dataclass
class Scenario:
    """One attack, as a set of per-sentence field edits."""

    name: str
    description: str
    #: What this should trigger, written before the evaluation is run so that
    #: the expected outcome is a hypothesis rather than a description of
    #: whatever happened.
    expect: str
    start_frac: float = 0.40
    end_frac: float = 1.00
    edit: Optional[Callable[[str, list[str], Context], list[str]]] = None

    def window(self, total: int) -> tuple[int, int]:
        return int(total * self.start_frac), int(total * self.end_frac)


def _split(sentence: str) -> tuple[list[str], bool]:
    """Split a framed sentence into fields, dropping any checksum."""
    body = sentence[1:] if sentence[:1] in "$!" else sentence
    star = body.rfind("*")
    had_checksum = star != -1
    if had_checksum:
        body = body[:star]
    return body.split(","), had_checksum


def _join(fields: list[str], had_checksum: bool) -> str:
    body = ",".join(fields)
    if not had_checksum:
        return f"${body}"
    return f"${body}*{compute_checksum(body):02X}"


def _kind(fields: list[str]) -> str:
    head = fields[0] if fields else ""
    return head[2:5] if len(head) >= 5 else head


# ---------------------------------------------------------------------------
# Scenario library
# ---------------------------------------------------------------------------


def _offset_position(fields: list[str], kind: str, north_m: float, east_m: float) -> list[str]:
    if kind == "GGA":
        lat_i, lat_d, lon_i, lon_d = GGA_LAT, GGA_LAT_DIR, GGA_LON, GGA_LON_DIR
    elif kind == "RMC":
        lat_i, lat_d, lon_i, lon_d = RMC_LAT, RMC_LAT_DIR, RMC_LON, RMC_LON_DIR
    else:
        return fields
    if len(fields) <= lon_d:
        return fields

    lat = nmea_to_decimal(fields[lat_i], fields[lat_d])
    lon = nmea_to_decimal(fields[lon_i], fields[lon_d])
    if lat is None or lon is None:
        return fields

    new_lat = lat + north_m / EARTH_M_PER_DEG
    denom = EARTH_M_PER_DEG * math.cos(math.radians(lat))
    new_lon = lon + (east_m / denom if abs(denom) > 1e-9 else 0.0)

    fields[lat_i], fields[lat_d] = decimal_to_nmea(new_lat, True)
    fields[lon_i], fields[lon_d] = decimal_to_nmea(new_lon, False)
    return fields


def _shift_time(fields: list[str], kind: str, seconds: float) -> list[str]:
    idx = {"GGA": GGA_TIME, "RMC": RMC_TIME}.get(kind)
    if idx is None or len(fields) <= idx:
        return fields
    fields[idx] = shift_time_field(fields[idx], seconds)
    return fields


def position_jump(distance_m: float = 3000.0) -> Scenario:
    def edit(sentence, fields, ctx):
        if not ctx.attacking:
            return fields
        return _offset_position(fields, _kind(fields), distance_m, distance_m * 0.5)

    return Scenario(
        name="position_jump",
        description=f"Position steps {distance_m:.0f} m and stays there",
        expect="position_deviation and trajectory; velocity_consistency on the "
               "single transition epoch only",
        edit=edit,
    )


def position_drift(rate_m_per_epoch: float = 2.0) -> Scenario:
    def edit(sentence, fields, ctx):
        if not ctx.attacking:
            return fields
        d = rate_m_per_epoch * ctx.elapsed
        return _offset_position(fields, _kind(fields), d, 0.0)

    return Scenario(
        name="position_drift",
        description=f"Position walks away at {rate_m_per_epoch:.1f} m per fix",
        expect="position_deviation once cumulative displacement passes the "
               "surveyed scatter; trajectory should stay quiet because each "
               "step is individually plausible",
        edit=edit,
    )


def time_step(offset_s: float = 45.0) -> Scenario:
    def edit(sentence, fields, ctx):
        if not ctx.attacking:
            return fields
        return _shift_time(fields, _kind(fields), offset_s)

    return Scenario(
        name="time_step",
        description=f"Receiver time jumps {offset_s:+.0f} s",
        expect="time_offset only. Every position-based check should stay "
               "silent, which is the point of including it",
        edit=edit,
    )


def time_drift(rate_s_per_epoch: float = 0.25) -> Scenario:
    def edit(sentence, fields, ctx):
        if not ctx.attacking:
            return fields
        return _shift_time(fields, _kind(fields), rate_s_per_epoch * ctx.elapsed)

    return Scenario(
        name="time_drift",
        description=f"Receiver time slews at {rate_s_per_epoch:.2f} s per fix",
        expect="time_offset, later than the step case; detection latency here "
               "is the headline number for a stealthy time attack",
        edit=edit,
    )


def satellite_count(target: int = 14) -> Scenario:
    def edit(sentence, fields, ctx):
        if not ctx.attacking:
            return fields
        kind = _kind(fields)
        if kind == "GGA" and len(fields) > GGA_NUM_SATS:
            fields[GGA_NUM_SATS] = f"{target:02d}"
        elif kind == "GSV" and len(fields) > GSV_NUM_SV:
            fields[GSV_NUM_SV] = f"{target:02d}"
        return fields

    return Scenario(
        name="satellite_count",
        description=f"Reported satellite count forced to {target}",
        expect="satellite_count only if the count falls; a rise is not "
               "something the calibrated low-side threshold looks for, and "
               "this scenario is included to show that gap",
        edit=edit,
    )


def hdop_anomaly(value: float = 0.4) -> Scenario:
    def edit(sentence, fields, ctx):
        if not ctx.attacking:
            return fields
        kind = _kind(fields)
        if kind == "GGA" and len(fields) > GGA_HDOP:
            fields[GGA_HDOP] = f"{value:.1f}"
        elif kind == "GSA" and len(fields) > GSA_VDOP:
            fields[GSA_HDOP] = f"{value:.1f}"
            fields[GSA_PDOP] = f"{value * 1.4:.1f}"
        return fields

    return Scenario(
        name="hdop_anomaly",
        description=f"HDOP forced to an implausibly perfect {value}",
        expect="nothing, and that is the finding. The dilution detector is "
               "calibrated on the high side because real degradation raises "
               "HDOP; a suspiciously good value is invisible to it",
        edit=edit,
    )


def snr_uniform(level: int = 44) -> Scenario:
    def edit(sentence, fields, ctx):
        if not ctx.attacking or _kind(fields) != "GSV":
            return fields
        i = GSV_FIRST_PRN + 3
        while i < len(fields):
            if fields[i]:
                fields[i] = f"{level:02d}"
            i += 4
        return fields

    return Scenario(
        name="snr_uniform",
        description=f"Every satellite reports {level} dB-Hz",
        expect="snr_uniformity strongly; snr_power depending on whether the "
               "level sits above the clean p99",
        edit=edit,
    )


def combined(
    distance_m: float = 2500.0,
    rate_s_per_epoch: float = 0.20,
    snr_level: int = 46,
) -> Scenario:
    """Three mechanisms at once.

    Parameterised so the dashboard can drive its strength, with the defaults
    fixed at the values the evaluation was run against.
    """
    jump = position_jump(distance_m).edit
    drift = time_drift(rate_s_per_epoch).edit
    snr = snr_uniform(snr_level).edit

    def edit(sentence, fields, ctx):
        if not ctx.attacking:
            return fields
        fields = jump(sentence, fields, ctx)
        fields = drift(sentence, fields, ctx)
        fields = snr(sentence, fields, ctx)
        return fields

    return Scenario(
        name="combined",
        description="Position step, time slew and uniform SNR together",
        expect="several detectors at once; the fused trust score should fall "
               "further and faster than for any single mechanism",
        edit=edit,
    )


def control() -> Scenario:
    return Scenario(
        name="control",
        description="Unmodified trace",
        expect="no detections. Anything that fires here is a false alarm on "
               "genuine receiver output and is counted as such",
        start_frac=1.0,
        end_frac=1.0,
        edit=None,
    )


def all_scenarios() -> list[Scenario]:
    return [
        control(),
        position_jump(),
        position_drift(),
        time_step(),
        time_drift(),
        satellite_count(),
        hdop_anomaly(),
        snr_uniform(),
        combined(),
    ]


# ---------------------------------------------------------------------------
# Applying a scenario
# ---------------------------------------------------------------------------


@dataclass
class InjectionResult:
    sentences: list[str] = field(default_factory=list)
    attack_flags: list[bool] = field(default_factory=list)
    total_epochs: int = 0
    attack_start_epoch: int = 0
    modified: int = 0


def count_epochs(sentences: Iterable[str]) -> int:
    """A fix cycle is counted at each GGA, the once-per-cycle sentence."""
    return sum(1 for s in sentences if _kind(_split(s)[0]) == "GGA")


def assemble_with_flags(sentences, flags, stats=None):
    """Assemble epochs while tracking which of them contain attacked sentences.

    Lives here rather than in a script because the alternative caused a real
    error. The injector counts fix cycles by GGA sentences; epoch assembly
    produces fewer epochs than that, since some cycles are malformed or
    duplicated. One capture has 224 GGA sentences and assembles to 187 epochs,
    so taking the same fraction of each gives two different attack-start
    indices. Any measurement or figure that derives the attack window from a
    fraction rather than from these flags is describing the wrong epoch.

    An epoch counts as attacked if any sentence describing it was modified:
    the detectors see the assembled record, so if part of it was tampered with
    then that record is tampered with.
    """
    from ..nmea import EpochAssembler, parse_line

    assembler = EpochAssembler()
    epochs: list = []
    attacked: list[bool] = []
    pending = False

    for sentence, flag in zip(sentences, flags):
        parsed = parse_line(sentence, stats)
        done = assembler.push(parsed)
        if done is not None:
            epochs.append(done)
            attacked.append(pending)
            pending = False
        if parsed.used and flag:
            pending = True

    tail = assembler.flush()
    if tail is not None:
        epochs.append(tail)
        attacked.append(pending)
    return epochs, attacked


def inject(sentences: list[str], scenario: Scenario) -> InjectionResult:
    """Apply a scenario to a real trace.

    Returns the modified sentences alongside a per-sentence flag saying whether
    the attack was active, which is the ground truth the evaluation scores
    against. Because the flag is produced by the injector rather than inferred
    from the output, it is exact - unlike the plan-derived labels on the
    JammerTest corpus.
    """
    total = count_epochs(sentences)
    start, end = scenario.window(total)

    out = InjectionResult(total_epochs=total, attack_start_epoch=start)
    epoch = -1
    for sentence in sentences:
        fields, had_checksum = _split(sentence)
        if _kind(fields) == "GGA":
            epoch += 1

        attacking = scenario.edit is not None and start <= epoch < end
        ctx = Context(
            epoch=max(epoch, 0),
            total_epochs=total,
            attacking=attacking,
            elapsed=max(0, epoch - start),
        )

        if attacking:
            new_fields = scenario.edit(sentence, list(fields), ctx)
            rendered = _join(new_fields, had_checksum)
            if rendered != sentence:
                out.modified += 1
            out.sentences.append(rendered)
        else:
            out.sentences.append(sentence)
        out.attack_flags.append(attacking)

    return out
