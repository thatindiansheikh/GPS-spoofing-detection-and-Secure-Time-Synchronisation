"""Independent time references.

The cross-check that catches a coherent spoof needs a clock the attacker does
not control. A local RF attacker can overwhelm a GNSS antenna; reaching a set
of NTP servers across the public internet is a different and much harder
proposition, and that asymmetry is what the check rests on.

The limit of that argument is stated rather than glossed over. Public NTP
servers are themselves frequently GPS-disciplined, so this is not an
independent *technology*, only an independent *location and path*. An attacker
who can also intercept the network path, or who can reach the reference
servers' own antennas, defeats it. That is the gap NTS (RFC 8915) exists to
close, and closing it here is out of scope.

Several servers are queried and the median offset taken, so that one
misbehaving server cannot move the reference. The spread across servers is
carried forward as the reference's uncertainty, which the time-offset detector
uses as its noise floor: nothing can be claimed about a GPS offset smaller than
the uncertainty of the thing it is being compared against.
"""

from __future__ import annotations

import socket
import statistics
import time
from dataclasses import dataclass, field
from typing import Optional, Sequence

try:
    import ntplib
except ImportError:  # pragma: no cover - dependency is declared, this is defensive
    ntplib = None

# Independent operators, so that one organisation's failure does not move the
# median. Not all from one pool for the same reason.
DEFAULT_SERVERS = (
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
    "time.windows.com",
)

DEFAULT_TIMEOUT_S = 3.0
DEFAULT_REFRESH_S = 64.0

# Floor on claimed uncertainty. Network jitter and scheduling delay on a
# general-purpose host make anything below this unmeasurable, whatever the
# servers agree on.
MIN_UNCERTAINTY_S = 0.010


@dataclass
class NtpSample:
    server: str
    offset: float
    delay: float
    stratum: int
    at: float


@dataclass
class NtpReference:
    """Median offset from several NTP servers, applied to the host clock.

    The host clock is read, never written. Steering it would need administrator
    rights, would disturb the machine the experiment runs on, and would make
    results irreproducible.
    """

    servers: Sequence[str] = DEFAULT_SERVERS
    timeout_s: float = DEFAULT_TIMEOUT_S
    refresh_s: float = DEFAULT_REFRESH_S

    _offset: Optional[float] = field(default=None, init=False)
    _uncertainty: float = field(default=float("inf"), init=False)
    _last_poll: float = field(default=0.0, init=False)
    _samples: list[NtpSample] = field(default_factory=list, init=False)
    _failures: int = field(default=0, init=False)

    # -- polling ---------------------------------------------------------

    def poll(self, force: bool = False) -> list[NtpSample]:
        """Query the servers, unless a fresh result is already held."""
        now = time.time()
        if not force and self._offset is not None and now - self._last_poll < self.refresh_s:
            return self._samples

        if ntplib is None:
            self._failures += 1
            return []

        client = ntplib.NTPClient()
        samples: list[NtpSample] = []
        for server in self.servers:
            try:
                r = client.request(server, version=3, timeout=self.timeout_s)
            except (ntplib.NTPException, socket.gaierror, socket.timeout, OSError):
                # One unreachable server is normal and must not break the
                # reference; it simply does not vote.
                continue
            # Stratum 0 is "unspecified" and 16 means unsynchronised. Neither
            # is a usable time source.
            if r.stratum in (0, 16):
                continue
            samples.append(
                NtpSample(
                    server=server,
                    offset=r.offset,
                    delay=r.delay,
                    stratum=r.stratum,
                    at=now,
                )
            )

        self._last_poll = now
        self._samples = samples

        if not samples:
            self._failures += 1
            self._offset = None
            self._uncertainty = float("inf")
            return []

        self._failures = 0
        offsets = [s.offset for s in samples]
        self._offset = statistics.median(offsets)

        # Uncertainty is the worst of: disagreement between servers, half the
        # best round trip, and the measurement floor. Taking the worst avoids
        # claiming more precision than any one contributor supports.
        spread = (max(offsets) - min(offsets)) if len(offsets) > 1 else 0.0
        half_rtt = min(s.delay for s in samples) / 2.0
        self._uncertainty = max(spread, half_rtt, MIN_UNCERTAINTY_S)
        return samples

    # -- TimeReference protocol -------------------------------------------

    def now(self) -> Optional[float]:
        self.poll()
        if self._offset is None:
            return None
        return time.time() + self._offset

    @property
    def uncertainty_s(self) -> float:
        return self._uncertainty

    @property
    def healthy(self) -> bool:
        return self._offset is not None

    @property
    def offset(self) -> Optional[float]:
        return self._offset

    def status(self) -> dict:
        return {
            "healthy": self.healthy,
            "offset_s": self._offset,
            "uncertainty_s": None if self._uncertainty == float("inf") else self._uncertainty,
            "servers_responding": len(self._samples),
            "servers_configured": len(self.servers),
            "consecutive_failures": self._failures,
            "last_poll": self._last_poll,
            "samples": [
                {"server": s.server, "offset_s": round(s.offset, 6),
                 "delay_s": round(s.delay, 6), "stratum": s.stratum}
                for s in self._samples
            ],
        }


@dataclass
class FixedReference:
    """A reference with a known time, for tests and replay.

    Replaying a recorded trace needs a clock that advances with the trace
    rather than with the wall clock, or every epoch would appear to be hours
    out of date.

    It presents the same surface as `NtpReference` - `now`, `uncertainty_s`,
    `healthy`, `status` - so that `TimeSourceManager` treats it as the network
    reference during a replay. Without `status` the manager cannot recognise it
    as a peer at all and failover skips straight to holdover, which makes a
    replay exercise a different path from the live system.
    """

    _now: Optional[float] = None
    uncertainty: float = MIN_UNCERTAINTY_S
    #: Set False to simulate the network reference being unreachable. `now()`
    #: then returns None and the manager falls through to holdover, which is
    #: the only way to exercise the last leg of the chain on recorded data.
    available: bool = True

    def set(self, value: Optional[float]) -> None:
        self._now = value

    def now(self) -> Optional[float]:
        return self._now if self.available else None

    @property
    def uncertainty_s(self) -> float:
        return self.uncertainty if self.available else float("inf")

    @property
    def healthy(self) -> bool:
        return self.available and self._now is not None

    def status(self) -> dict:
        return {
            "healthy": self.healthy,
            "offset_s": None,
            "uncertainty_s": self.uncertainty if self.available else None,
            "servers_responding": 1 if self.healthy else 0,
            "servers_configured": 1,
            "consecutive_failures": 0 if self.available else 1,
            "last_poll": self._now,
            "samples": [],
            "fixed": True,
        }
