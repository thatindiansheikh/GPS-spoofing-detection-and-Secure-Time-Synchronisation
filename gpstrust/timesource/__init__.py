"""Time reference, holdover and source selection.

Detection decides whether GPS may be believed; this package decides what the
network is actually told the time is, and how good that answer currently is.
"""

from .clock import OSCILLATOR_PPM, HoldoverClock
from .manager import ActiveSource, SourceEvent, TimeDecision, TimeSourceManager
from .ntp import DEFAULT_SERVERS, FixedReference, NtpReference, NtpSample

__all__ = [
    "HoldoverClock",
    "OSCILLATOR_PPM",
    "NtpReference",
    "NtpSample",
    "FixedReference",
    "DEFAULT_SERVERS",
    "TimeSourceManager",
    "TimeDecision",
    "ActiveSource",
    "SourceEvent",
]
