"""Robust NMEA 0183 sentence parsing.

Real receiver output is dirty. Serial buffer overruns truncate lines, the first
line of a capture is usually a fragment, receivers emit proprietary sentences,
fields go empty when there is no fix, and occasional binary noise appears on the
wire. Nothing here raises on bad input: failures are categorised and counted, so
that parse quality becomes an observable signal in its own right rather than a
crash.

Field extraction is delegated to pynmea2. Framing and checksum validation are
done here, because pynmea2 is deliberately lenient about both and we need to
know precisely which lines were rejected and why.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pynmea2

# Sentence types the pipeline consumes. Anything else valid is counted as
# "unused" rather than an error; receivers emit plenty of well-formed sentences
# this project has no use for.
USED_TYPES = frozenset({"GGA", "RMC", "GSV", "GSA", "VTG"})

# NMEA 0183 start delimiters. '!' is used by AIS-style encapsulated sentences,
# which appear in mixed logs and must be framed correctly even though we ignore
# their contents.
START_DELIMITERS = ("$", "!")


@dataclass
class ParseStats:
    """Running tally of line outcomes.

    The ratio of bad lines to total is itself useful: a sharp rise in checksum
    failures can indicate interference or a failing link, which is context the
    detection layer should see rather than have silently repaired.
    """

    total: int = 0
    ok: int = 0
    unused: int = 0
    empty: int = 0
    no_frame: int = 0
    checksum_missing: int = 0
    checksum_bad: int = 0
    malformed: int = 0

    @property
    def bad(self) -> int:
        return self.no_frame + self.checksum_bad + self.malformed

    @property
    def error_rate(self) -> float:
        return self.bad / self.total if self.total else 0.0

    def as_dict(self) -> dict[str, Any]:
        d = {
            "total": self.total,
            "ok": self.ok,
            "unused": self.unused,
            "empty": self.empty,
            "no_frame": self.no_frame,
            "checksum_missing": self.checksum_missing,
            "checksum_bad": self.checksum_bad,
            "malformed": self.malformed,
        }
        d["bad"] = self.bad
        d["error_rate"] = round(self.error_rate, 6)
        return d


@dataclass
class ParsedLine:
    """Outcome of attempting to parse one candidate sentence."""

    raw: str
    msg: Optional[Any] = None
    sentence_type: Optional[str] = None
    talker: Optional[str] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.msg is not None and self.error is None

    @property
    def used(self) -> bool:
        return self.ok and self.sentence_type in USED_TYPES


def compute_checksum(payload: str) -> int:
    """XOR of every character between the start delimiter and the '*'."""
    checksum = 0
    for ch in payload:
        checksum ^= ord(ch) & 0xFF
    return checksum


def verify_checksum(sentence: str) -> Optional[bool]:
    """Validate a framed sentence's checksum.

    Returns True/False, or None when the sentence carries no checksum at all.
    Some logging tools strip checksums, so a missing one is tolerated and
    counted separately from a wrong one.
    """
    star = sentence.rfind("*")
    if star == -1 or star + 3 > len(sentence):
        return None
    payload = sentence[1:star]
    given = sentence[star + 1 : star + 3]
    try:
        return compute_checksum(payload) == int(given, 16)
    except ValueError:
        return False


def parse_line(line: str, stats: Optional[ParseStats] = None) -> ParsedLine:
    """Parse one candidate sentence, never raising.

    The caller is expected to have already split a raw chunk into individual
    candidate sentences (see reader.iter_sentences); this function assumes at
    most one sentence per call and ignores anything after a trailing delimiter.
    """
    if stats is not None:
        stats.total += 1

    # Strip whitespace and the NUL bytes that show up when a serial line is cut
    # mid-write.
    text = line.strip().replace("\x00", "")
    if not text:
        if stats is not None:
            stats.empty += 1
        return ParsedLine(raw=line, error="empty")

    start = min((text.find(d) for d in START_DELIMITERS if d in text), default=-1)
    if start == -1:
        if stats is not None:
            stats.no_frame += 1
        return ParsedLine(raw=line, error="no_frame")
    sentence = text[start:]

    checksum_state = verify_checksum(sentence)
    if checksum_state is False:
        if stats is not None:
            stats.checksum_bad += 1
        return ParsedLine(raw=line, error="checksum_bad")
    if checksum_state is None and stats is not None:
        stats.checksum_missing += 1

    try:
        # check=False because we have already validated the checksum ourselves
        # and want pynmea2 to attempt extraction even on short field counts.
        msg = pynmea2.parse(sentence, check=False)
    except Exception as exc:  # pynmea2 raises several unrelated exception types
        if stats is not None:
            stats.malformed += 1
        return ParsedLine(raw=line, error=f"malformed: {type(exc).__name__}")

    sentence_type = getattr(msg, "sentence_type", None)
    talker = getattr(msg, "talker", None)

    if sentence_type is None:
        # Proprietary sentences (PUBX, PGRMC, ...) have no sentence_type.
        sentence_type = getattr(msg, "identifier", lambda: "PROP")().strip(",")

    if stats is not None:
        if sentence_type in USED_TYPES:
            stats.ok += 1
        else:
            stats.unused += 1

    return ParsedLine(raw=line, msg=msg, sentence_type=sentence_type, talker=talker)


def to_int(value: Any) -> Optional[int]:
    """Field conversion that tolerates empty strings and padded numbers."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        try:
            return int(float(text))
        except ValueError:
            return None


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
