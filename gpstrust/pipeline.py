"""The assembled system.

Wires the layers into one object so the dashboard, the command line and the
tests all drive identical code. The alternative - each entry point assembling
its own chain - is how a demonstration ends up behaving differently from the
thing that was evaluated.

    NMEA in -> parse -> epoch -> detectors -> trust -> time source -> log

Input can be a file, a replayed capture, or an injected attack stream. The
pipeline does not know or care which, because the detectors only ever see
assembled epochs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Sequence

from .config import Calibration
from .detect import build_default_suite
from .detect.base import Evidence, flat_distance_m
from .nmea import ParseStats, epochs_from_sentences
from .nmea.epoch import Epoch
from .store import EventStore
from .timesource import TimeDecision, TimeSourceManager
from .trust import TrustConfig, TrustEngine, TrustVerdict


@dataclass
class Step:
    """Everything the system concluded about one epoch."""

    index: int
    epoch: Epoch
    evidence: list[Evidence]
    verdict: TrustVerdict
    decision: TimeDecision
    deviation_m: Optional[float] = None

    @property
    def fired(self) -> list[Evidence]:
        return [e for e in self.evidence if e.applicable and e.score > 0]


@dataclass
class Pipeline:
    """Detection, trust and time-source selection over an epoch stream."""

    calibration: Calibration
    reference: Optional[object] = None
    trust_config: TrustConfig = field(default_factory=TrustConfig)
    store: Optional[EventStore] = None

    detectors: list = field(init=False)
    engine: TrustEngine = field(init=False)
    manager: TimeSourceManager = field(init=False)
    parse_stats: ParseStats = field(default_factory=ParseStats)
    skipped_detectors: list = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.detectors = build_default_suite(self.calibration, reference=self.reference)
        self.skipped_detectors = list(getattr(build_default_suite, "last_skipped", []))
        self.engine = TrustEngine(self.trust_config)
        self.manager = TimeSourceManager(
            ntp=self.reference if hasattr(self.reference, "status") else None
        )
        self._index = 0
        self._logged_events = 0

    def reset(self) -> None:
        for d in self.detectors:
            d.reset()
        self.engine.reset()
        self._index = 0

    # -- driving -----------------------------------------------------------

    def step(self, epoch: Epoch, host_time: Optional[float] = None) -> Step:
        """Process one epoch through every layer."""
        evidence = [d.update(epoch) for d in self.detectors]
        gps_time = epoch.utc.timestamp() if epoch.utc is not None else None

        # The trust engine is clocked on GPS time when it is the only clock
        # available, which is a real limitation: an attacker who freezes the
        # reported time also freezes the recovery hold. Host time is passed
        # when a caller has it, and the dashboard and live paths always do.
        verdict = self.engine.evaluate(evidence, now=host_time or gps_time)
        decision = self.manager.update(verdict, gps_time, host_time=host_time)

        deviation = None
        if epoch.has_position:
            deviation = flat_distance_m(
                epoch.lat, epoch.lon, self.calibration.ref_lat, self.calibration.ref_lon
            )

        step = Step(
            index=self._index,
            epoch=epoch,
            evidence=evidence,
            verdict=verdict,
            decision=decision,
            deviation_m=deviation,
        )
        self._index += 1

        if self.store is not None:
            self.store.record(
                epoch, evidence, verdict, decision,
                host_time=host_time, deviation_m=deviation,
            )
            new_events = self.manager.events[self._logged_events:]
            if new_events:
                self.store.record_source_events(new_events)
                self._logged_events = len(self.manager.events)

        return step

    def run(self, epochs: Iterable[Epoch]) -> Iterator[Step]:
        for epoch in epochs:
            yield self.step(epoch)

    def run_sentences(self, sentences: Iterable[str]) -> Iterator[Step]:
        """Drive the pipeline from raw NMEA, counting parse failures as it goes."""
        yield from self.run(epochs_from_sentences(sentences, self.parse_stats))

    # -- reporting ---------------------------------------------------------

    def status(self) -> dict:
        return {
            "detectors": [d.name for d in self.detectors],
            "detectors_skipped": [name for name, _ in self.skipped_detectors],
            "epochs_processed": self._index,
            "parse": self.parse_stats.as_dict(),
            "trust_state": self.engine.state.value,
            "time_source": self.manager.status(),
            "reference_position": {
                "lat": self.calibration.ref_lat,
                "lon": self.calibration.ref_lon,
            },
        }


def summarise(steps: Sequence[Step]) -> dict:
    """Aggregate a completed run, for a report or a test."""
    if not steps:
        return {"epochs": 0}

    trusts = [s.verdict.trust for s in steps if s.verdict.trust is not None]
    states: dict[str, int] = {}
    sources: dict[str, int] = {}
    firings: dict[str, int] = {}

    for s in steps:
        states[s.verdict.state.value] = states.get(s.verdict.state.value, 0) + 1
        sources[s.decision.source.value] = sources.get(s.decision.source.value, 0) + 1
        for e in s.fired:
            firings[e.detector] = firings.get(e.detector, 0) + 1

    return {
        "epochs": len(steps),
        "mean_trust": sum(trusts) / len(trusts) if trusts else None,
        "min_trust": min(trusts) if trusts else None,
        "states": states,
        "active_sources": sources,
        "detector_firings": firings,
    }
