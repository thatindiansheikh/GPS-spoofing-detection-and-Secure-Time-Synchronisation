"""Fusion of detector evidence into a trust score and a source decision.

No single check is sufficient. Jamming is loud and shows up in satellite count
and dilution; a coherent spoof is quiet there and shows up in signal strength
and uniformity; a careful spoof that matches position, velocity and geometry
shows up only against an independent clock. Fusing them is what lets the system
respond to all three without a separate rule for each.

Two design points are driven by what the data showed rather than by taste.

**Only applicable evidence counts.** A detector that cannot assess an epoch is
excluded from the weighted mean rather than contributing a zero. Missing GSV is
not evidence of innocence, and scoring it as such would quietly raise trust
during exactly the degraded conditions where the receiver is least reliable.

**Recovery is slower than detection, and deliberately so.** The JammerTest data
shows the receiver sitting on a spoofed position long after the transmission
that put it there has stopped: no guard interval up to two hours removes the
effect, and requiring observed recovery after a logging gap makes it worse
(docs/data-validity.md). A trust engine that restored confidence the moment the
anomaly disappeared would hand the network a receiver that is still wrong. So
leaving the untrusted state requires the evidence to stay clean for a sustained
hold time, not merely to fall below a threshold for one epoch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional, Sequence

from .detect.base import Evidence


class SourceState(str, Enum):
    """Whether GPS may currently be used as a time source."""

    TRUSTED = "trusted"
    SUSPECT = "suspect"        # anomalous, still usable, flagged
    UNTRUSTED = "untrusted"    # rejected, failover active
    RECOVERING = "recovering"  # evidence clean again, serving out the hold
    UNKNOWN = "unknown"        # not enough evidence to judge


# Equal weights are the honest starting point: any other assignment is a claim
# about relative importance that has to be justified. scripts/tune_weights.py
# derives an alternative from per-detector discrimination on a training split,
# and the evaluation reports both so the gain from weighting is visible rather
# than assumed.
DEFAULT_WEIGHTS: dict[str, float] = {
    "position_deviation": 1.0,
    "trajectory": 1.0,
    "velocity_consistency": 1.0,
    "satellite_count": 1.0,
    "dilution": 1.0,
    "snr_power": 1.0,
    "snr_uniformity": 1.0,
    "time_offset": 1.0,
}


class Fusion(str, Enum):
    """How per-detector evidence is combined.

    `MEAN` is a weighted average of the scores. It is the obvious choice and it
    is wrong for this problem: averaging dilutes. With eight detectors, one of
    them firing at full confidence while the rest see nothing produces an
    anomaly of 1/8, so the strongest single piece of evidence available cannot
    on its own push trust past a rejection threshold. Measured on the corpus,
    the position detector alone reaches 84% recall, yet the fused score at
    equal weights rejected only 2% of attack epochs.

    `NOISY_OR` treats each detector as an independent opportunity to notice the
    attack: trust is the probability that every detector is right to stay
    quiet, so trust = product over detectors of (1 - weight * score). One
    reliable detector at full score can then drive trust to zero, while several
    weak detectors still combine. The weight carries the detector's reliability
    rather than its share of a budget, which is also what makes it estimable
    from data: scripts/tune_weights.py sets each weight to the detector's
    precision on the training split.

    Both are retained and both are reported, so the choice rests on measured
    difference rather than on assertion.
    """

    MEAN = "mean"
    NOISY_OR = "noisy_or"


@dataclass
class TrustConfig:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    fusion: Fusion = Fusion.NOISY_OR

    # These four are set from the measured operating point, not chosen by eye.
    # scripts/run_evaluation.py sweeps the decision threshold on the held-out
    # days and reports precision, recall and false alarm rate at each; 0.80 is
    # where F1 peaks (86.9% precision, 88.5% recall) and 0.70 is the
    # higher-precision alternative (94.7% precision, 71.5% recall, 5.0% FPR).
    # Rerunning the evaluation is what justifies changing them.

    #: Trust below this flags the source as suspect but keeps using it.
    suspect_below: float = 0.90
    #: Trust below this rejects GPS and triggers failover.
    reject_below: float = 0.80
    #: Trust must exceed this to begin recovering.
    #: Set above reject_below rather than far above it. An earlier value of
    #: 0.90 left the engine 77% untrusted on the held-out days, because fused
    #: trust rarely climbed that high while the position detector was still
    #: firing on residual displacement: the gate was never reached and the
    #: state machine latched.
    recover_above: float = 0.85
    #: ...and stay there for this long before GPS is trusted again.
    #: The receiver in this corpus holds a spoofed position long after the
    #: transmission stops, so recovery is deliberately slower than detection.
    #: The cost of this hold is measured in the evaluation rather than assumed.
    recover_hold_s: float = 300.0

    #: Minimum number of applicable detectors before a verdict is issued at all.
    #: One detector agreeing with itself is not a consensus, and renormalising
    #: over a single applicable detector would let it swing trust on its own.
    min_applicable: int = 3


@dataclass
class TrustVerdict:
    trust: Optional[float]
    state: SourceState
    anomaly: Optional[float]
    contributions: dict[str, float]
    applicable: list[str]
    inapplicable: dict[str, str]
    reasons: list[str]
    time_s: Optional[float] = None
    #: Seconds of clean evidence still owed before GPS may be trusted again,
    #: or None when no hold is running. An operator watching a failover needs
    #: to know whether the system is stuck or simply counting down, and the
    #: state name alone does not distinguish those.
    hold_remaining_s: Optional[float] = None

    @property
    def gps_usable(self) -> bool:
        return self.state in (SourceState.TRUSTED, SourceState.SUSPECT)


class TrustEngine:
    """Turns a stream of evidence into a trust score and a source state."""

    def __init__(self, config: Optional[TrustConfig] = None):
        self.config = config or TrustConfig()
        self.state = SourceState.UNKNOWN
        self._clean_since: Optional[float] = None
        self._last_time: Optional[float] = None
        self._hold_remaining: Optional[float] = None

    def reset(self) -> None:
        self.state = SourceState.UNKNOWN
        self._clean_since = None
        self._last_time = None
        self._hold_remaining = None

    def evaluate(
        self, evidence: Sequence[Evidence], now: Optional[float] = None
    ) -> TrustVerdict:
        applicable = [e for e in evidence if e.applicable]
        inapplicable = {e.detector: e.reason for e in evidence if not e.applicable}

        if len(applicable) < self.config.min_applicable:
            self.state = SourceState.UNKNOWN
            return TrustVerdict(
                trust=None,
                state=self.state,
                anomaly=None,
                contributions={},
                applicable=[e.detector for e in applicable],
                inapplicable=inapplicable,
                reasons=[
                    f"only {len(applicable)} detectors applicable; "
                    f"need {self.config.min_applicable}"
                ],
                time_s=now,
            )

        weights = self.config.weights
        contributions = {
            e.detector: weights.get(e.detector, 1.0) * e.score for e in applicable
        }

        if self.config.fusion is Fusion.NOISY_OR:
            # Probability that every applicable detector is right to stay quiet.
            survival = 1.0
            for e in applicable:
                w = min(1.0, max(0.0, weights.get(e.detector, 1.0)))
                survival *= 1.0 - w * e.score
            trust = max(0.0, min(1.0, survival))
            anomaly = 1.0 - trust
        else:
            total_w = sum(weights.get(e.detector, 1.0) for e in applicable)
            anomaly = sum(contributions.values()) / total_w if total_w else 0.0
            trust = max(0.0, min(1.0, 1.0 - anomaly))

        reasons = [e.reason for e in sorted(applicable, key=lambda x: -x.score) if e.score > 0]

        self._advance_state(trust, now)

        return TrustVerdict(
            trust=trust,
            state=self.state,
            anomaly=anomaly,
            contributions=contributions,
            applicable=[e.detector for e in applicable],
            inapplicable=inapplicable,
            reasons=reasons,
            time_s=now,
            hold_remaining_s=self._hold_remaining,
        )

    # -- state machine ---------------------------------------------------

    def _advance_state(self, trust: float, now: Optional[float]) -> None:
        cfg = self.config
        if now is not None:
            self._last_time = now

        if trust < cfg.reject_below:
            # Any rejection-level evidence restarts the hold from zero. An
            # attack that flickers must not accumulate credit for the quiet
            # moments between its own bursts.
            self.state = SourceState.UNTRUSTED
            self._clean_since = None
            self._hold_remaining = cfg.recover_hold_s
            return

        if self.state is SourceState.UNTRUSTED or self.state is SourceState.RECOVERING:
            if trust < cfg.recover_above:
                self.state = SourceState.UNTRUSTED
                self._clean_since = None
                self._hold_remaining = cfg.recover_hold_s
                return
            if self._clean_since is None:
                self._clean_since = now if now is not None else 0.0
                self.state = SourceState.RECOVERING
                self._hold_remaining = cfg.recover_hold_s
                return
            elapsed = (now - self._clean_since) if now is not None else 0.0
            if elapsed >= cfg.recover_hold_s:
                self.state = SourceState.TRUSTED
                self._clean_since = None
                self._hold_remaining = None
            else:
                self.state = SourceState.RECOVERING
                self._hold_remaining = max(0.0, cfg.recover_hold_s - elapsed)
            return

        if trust < cfg.suspect_below:
            self.state = SourceState.SUSPECT
        else:
            self.state = SourceState.TRUSTED
        self._clean_since = None
        self._hold_remaining = None


def run_stream(
    epochs: Iterable,
    detectors: Sequence,
    engine: Optional[TrustEngine] = None,
):
    """Drive detectors and the trust engine over an epoch stream.

    Yields (epoch, evidence, verdict) so callers can evaluate, log or display
    without each re-implementing the loop.
    """
    engine = engine or TrustEngine()
    for epoch in epochs:
        evidence = [d.update(epoch) for d in detectors]
        now = epoch.utc.timestamp() if epoch.utc is not None else None
        verdict = engine.evaluate(evidence, now=now)
        yield epoch, evidence, verdict
