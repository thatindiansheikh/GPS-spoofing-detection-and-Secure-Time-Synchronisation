"""Comparison of receiver-claimed time against an independent reference.

This is the detector closest to the project's purpose, and the only one whose
thresholds are not derived from the JammerTest corpus. That dataset retained
the measurement node's arrival timestamp and discarded the receiver's claimed
UTC, so the quantity this detector exists to measure is simply absent from it.
Rather than paper over that, the detector refuses any epoch whose timestamp is
host receive time. See docs/data-validity.md.

Its thresholds therefore come from standards and from the resolution of the
NMEA interface itself, and are labelled as such:

* **warn at 1 s.** GGA and RMC carry time to whole or fractional seconds and
  arrive after unbounded serial latency, so sub-second offsets are not
  measurable at this layer at all. One second is the smallest offset that can
  be distinguished from interface quantisation. Detecting below this needs the
  PPS signal, which is out of scope.
* **alarm at 10 s.** Not a consequence threshold but an evidence one: a
  GPS-disciplined receiver does not drift by ten seconds. An offset of that
  size is not a degraded clock, it is a wrong one.

The consequence thresholds are recorded separately because they describe what
breaks downstream, not what constitutes evidence:

| Offset | Consequence |
|---|---|
| 128 ms | ntpd steps rather than slews the system clock (RFC 5905) |
| 300 s | Kerberos rejects the ticket by default (RFC 4120) |
| hours+ | TLS certificate validity windows misjudged |
"""

from __future__ import annotations

from collections import deque
from typing import Optional, Protocol

from ..nmea.epoch import Epoch
from .base import Detector, Evidence

# Provenance: interface resolution and standards, not the measured corpus.
WARN_OFFSET_S = 1.0
ALARM_OFFSET_S = 10.0

THRESHOLD_PROVENANCE = (
    "standards and NMEA interface resolution; not derived from the JammerTest "
    "corpus, which does not retain receiver-claimed UTC"
)

CONSEQUENCE_THRESHOLDS_S = {
    "ntp_step": 0.128,
    "kerberos_default_skew": 300.0,
}


class TimeReference(Protocol):
    """Anything that can state the current true time, in POSIX seconds."""

    def now(self) -> Optional[float]:
        ...

    @property
    def uncertainty_s(self) -> float:
        ...


class TimeOffsetDetector(Detector):
    """Receiver-claimed UTC against an independent reference clock."""

    name = "time_offset"
    rationale = (
        "The last line of defence. A spoofer that keeps position, velocity and "
        "satellite geometry mutually consistent defeats every other check here, "
        "but it cannot also match an independent clock the attacker does not "
        "control."
    )

    def __init__(self, reference: TimeReference, window: int = 10):
        self.reference = reference
        # A short median filter. One epoch's offset is contaminated by serial
        # and scheduling latency; a sustained offset is not.
        self._recent: deque[float] = deque(maxlen=window)

    def reset(self) -> None:
        self._recent.clear()

    def update(self, epoch: Epoch) -> Evidence:
        # The refusal that keeps the limitation honest in code rather than only
        # in prose. An epoch timestamped on arrival tells us when the sentence
        # reached the host, which is not what the receiver claimed, and a
        # spoofed receiver's claim is the entire point.
        if epoch.time_source != "gps":
            return Evidence.not_applicable(
                self.name,
                f"timestamp provenance is {epoch.time_source!r}, not receiver-reported "
                "UTC; a time-spoofing attack is not observable in this data",
            )

        if epoch.utc is None:
            return Evidence.not_applicable(self.name, "no UTC in epoch")

        ref_now = self.reference.now()
        if ref_now is None:
            return Evidence.not_applicable(
                self.name, "no reference time available; cannot cross-check"
            )

        offset = epoch.utc.timestamp() - ref_now
        self._recent.append(offset)
        sorted_recent = sorted(self._recent)
        smoothed = sorted_recent[len(sorted_recent) // 2]
        magnitude = abs(smoothed)

        # Below the reference's own uncertainty there is nothing to say.
        floor = max(WARN_OFFSET_S, self.reference.uncertainty_s)
        if magnitude <= floor:
            score = 0.0
        elif ALARM_OFFSET_S <= floor:
            score = 1.0
        else:
            score = min(1.0, (magnitude - floor) / (ALARM_OFFSET_S - floor))

        return Evidence(
            detector=self.name,
            score=score,
            value=smoothed,
            warn=floor,
            alarm=ALARM_OFFSET_S,
            reason=(
                f"GPS time differs from reference by {smoothed:+.2f} s"
                if score > 0
                else f"GPS time agrees with reference to {smoothed:+.2f} s"
            ),
            detail={
                "reference_uncertainty_s": self.reference.uncertainty_s,
                "provenance": THRESHOLD_PROVENANCE,
                "samples": len(self._recent),
            },
        )
