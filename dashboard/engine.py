"""Driving the pipeline for the console.

One function does the work: take the operator's settings, replay a capture
through the real pipeline under those settings, and return everything the
display needs. The console never reimplements a detector, a threshold or a
failover rule - it reads them off the same objects the evaluation uses, so
what is on screen is what was measured.

The run is cached on its settings. Playback then scrubs through a finished run
rather than recomputing, which is what makes the board update at frame rate
while still showing real output. Changing any control - a different attack
parameter, a different rejection threshold - invalidates the cache and the
whole capture is reprocessed, so the board always shows one self-consistent
run rather than a mixture of two.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gpstrust.attacks import injector  # noqa: E402
from gpstrust.attacks.injector import assemble_with_flags, inject  # noqa: E402
from gpstrust.calibrate import calibrate_from_epochs  # noqa: E402
from gpstrust.nmea import epochs_from_sentences, sentences_from_file  # noqa: E402
from gpstrust.nmea.epoch import SatelliteView  # noqa: E402
from gpstrust.pipeline import Pipeline  # noqa: E402
from gpstrust.timesource import FixedReference  # noqa: E402
from gpstrust.trust import Fusion, TrustConfig  # noqa: E402

GPSD = ROOT / "data" / "raw" / "gpsd" / "gpsd-master-test-daemon" / "test" / "daemon"

#: Fraction of the capture used to survey in. The remainder is what the
#: operator can attack; the attack window slider is clamped to it, because an
#: attack inside the survey would calibrate the thresholds on the attack.
SURVEY_FRACTION = 0.40


# ---------------------------------------------------------------------------
# Attack vectors, as the admin panel offers them
# ---------------------------------------------------------------------------


VECTORS: dict[str, dict[str, Any]] = {
    "none": dict(
        label="None (clean feed)",
        action="The capture is replayed untouched.",
        expect="No detector should fire. Anything that does is a false alarm on "
               "genuine receiver output.",
        param=None,
        build=lambda m: injector.control(),
    ),
    "position_jump": dict(
        label="Position jump",
        action="Reported position steps to a new point and stays there.",
        expect="position_deviation and trajectory fire. velocity_consistency fires "
               "on the single transition epoch only.",
        param=dict(label="Jump distance", min=100.0, max=20000.0, default=3000.0,
                   step=100.0, unit="m"),
        build=lambda m: injector.position_jump(m),
    ),
    "position_drift": dict(
        label="Position drift (slow walk)",
        action="Position walks away a little on every fix, so no single step looks wrong.",
        expect="position_deviation once the cumulative displacement passes the surveyed "
               "scatter. trajectory should stay quiet - that is the stealth of it.",
        param=dict(label="Drift rate", min=0.2, max=25.0, default=2.0,
                   step=0.2, unit="m/fix"),
        build=lambda m: injector.position_drift(m),
    ),
    "time_step": dict(
        label="Time step",
        action="Receiver clock jumps to a wrong time in one go.",
        expect="time_offset only. Every position check stays silent, which is exactly "
               "why an independent clock is needed.",
        param=dict(label="Time offset", min=-600.0, max=600.0, default=45.0,
                   step=5.0, unit="s"),
        build=lambda m: injector.time_step(m),
    ),
    "time_drift": dict(
        label="Time drift (slow slew)",
        action="Receiver clock slews away by a fraction of a second per fix.",
        expect="time_offset, later than the step case. The delay before it fires is the "
               "headline number for a stealthy time attack.",
        param=dict(label="Slew rate", min=0.01, max=2.0, default=0.25,
                   step=0.01, unit="s/fix"),
        build=lambda m: injector.time_drift(m),
    ),
    "satellite_count": dict(
        label="Satellite count forced",
        action="Reported number of satellites is overwritten.",
        expect="satellite_count fires only if the count falls. Forcing it high is "
               "invisible to a threshold calibrated on the low side - included to show "
               "that gap, not to hide it.",
        param=dict(label="Forced count", min=3.0, max=24.0, default=14.0,
                   step=1.0, unit="sats", integer=True),
        build=lambda m: injector.satellite_count(int(m)),
    ),
    "hdop_anomaly": dict(
        label="HDOP falsified",
        action="Dilution of precision is forced to an implausibly perfect value.",
        expect="Nothing fires, and that is the finding. The dilution check is calibrated "
               "on the high side because real degradation raises HDOP; a suspiciously "
               "good value is invisible to it.",
        param=dict(label="Forced HDOP", min=0.1, max=3.0, default=0.4,
                   step=0.1, unit=""),
        build=lambda m: injector.hdop_anomaly(m),
    ),
    "snr_uniform": dict(
        label="Uniform signal strength",
        action="Every satellite is made to report the same carrier-to-noise level, as a "
               "single spoofing transmitter would.",
        expect="snr_uniformity strongly. snr_power too, if the level sits above the clean "
               "99th percentile.",
        param=dict(label="Forced level", min=18.0, max=55.0, default=44.0,
                   step=1.0, unit="dB-Hz", integer=True),
        build=lambda m: injector.snr_uniform(int(m)),
    ),
    "combined": dict(
        label="Combined spoof",
        action="Position step, clock slew and uniform signal strength at once.",
        expect="Several detectors together. Fused trust should fall further and faster "
               "than for any single mechanism.",
        param=dict(label="Strength", min=0.25, max=3.0, default=1.0,
                   step=0.25, unit="x"),
        # Strength scales the two graded mechanisms. The signal-strength leg is
        # a fixed level because "more uniform" is not a quantity - the level is
        # either forced flat or it is not.
        build=lambda m: injector.combined(
            distance_m=2500.0 * m, rate_s_per_epoch=0.20 * m, snr_level=46
        ),
    ),
}

VECTOR_ORDER = list(VECTORS.keys())


# ---------------------------------------------------------------------------
# Settings and results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    """Everything the operator can change, in one hashable bundle."""

    trace: str
    vector: str = "none"
    magnitude: float = 0.0
    window_start_pct: int = 55
    window_end_pct: int = 70
    armed: bool = False

    ntp_available: bool = True
    ntp_uncertainty_ms: float = 20.0

    fusion: str = "noisy_or"
    reject_below: float = 0.80
    suspect_below: float = 0.90
    recover_above: float = 0.85
    recover_hold_s: float = 20.0

    @property
    def active_vector(self) -> str:
        return self.vector if (self.armed and self.vector != "none") else "none"


@dataclass
class Run:
    """A finished replay, ready to display."""

    frame: pd.DataFrame
    satellites: list[list[SatelliteView]] = field(default_factory=list)
    evidence: list[list[dict]] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    detections: pd.DataFrame = field(default_factory=pd.DataFrame)
    calibration: pd.DataFrame = field(default_factory=pd.DataFrame)
    status: dict = field(default_factory=dict)
    scenario: dict = field(default_factory=dict)
    detector_rationale: dict = field(default_factory=dict)
    reference: tuple[Optional[float], Optional[float]] = (None, None)
    survey_epochs: int = 0
    error: Optional[str] = None

    @property
    def total(self) -> int:
        return len(self.frame)


# ---------------------------------------------------------------------------
# Capture discovery
# ---------------------------------------------------------------------------


#: Survey-in needs 25 positioned epochs out of the first SURVEY_FRACTION of the
#: capture, so a capture shorter than this cannot be used at all.
MIN_EPOCHS = int(25 / SURVEY_FRACTION) + 1


@st.cache_data(show_spinner="Scanning captures...")
def available_traces() -> list[str]:
    """Captures this console can actually replay.

    The cheap text test is not sufficient on its own: a log can carry plenty of
    GGA and GSV sentences and still assemble to too few epochs to survey in
    against. Offering such a capture in the selector and then refusing it is
    worse than not offering it, because the refusal happens mid-script and
    takes the playback controls down with it. So the real check is done here,
    once, and only usable captures are listed.
    """
    if not GPSD.exists():
        return []
    out = []
    for path in sorted(GPSD.glob("*.log")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if text.count("GGA") < 50 or text.count("GSV") < 50:
            continue
        epochs = list(epochs_from_sentences(sentences_from_file(path)))
        if len(epochs) < MIN_EPOCHS:
            continue
        if sum(1 for e in epochs[: int(len(epochs) * SURVEY_FRACTION)] if e.has_position) < 25:
            continue
        out.append(path.name)
    return out


@st.cache_data(show_spinner=False)
def trace_summary(name: str) -> dict:
    """A one-line description of a capture, for the feed selector."""
    epochs = list(epochs_from_sentences(sentences_from_file(GPSD / name)))
    positioned = [e for e in epochs if e.has_position]
    mid = positioned[len(positioned) // 2] if positioned else None
    return {
        "epochs": len(epochs),
        "positioned": len(positioned),
        "lat": mid.lat if mid else None,
        "lon": mid.lon if mid else None,
    }


# ---------------------------------------------------------------------------
# The replay
# ---------------------------------------------------------------------------


def _build_scenario(settings: Settings):
    spec = VECTORS[settings.active_vector]
    scenario = spec["build"](settings.magnitude)
    if settings.active_vector == "none":
        return scenario

    # The survey-in segment must stay clean or the thresholds are derived from
    # the attack itself, so the window is clamped to start after it.
    start = max(settings.window_start_pct / 100.0, SURVEY_FRACTION)
    end = max(settings.window_end_pct / 100.0, start)
    scenario.start_frac = start
    scenario.end_frac = end
    return scenario


# Settings is a frozen dataclass of primitives, but the cache is told how to
# hash it explicitly rather than relying on the fallback pickling path.
@st.cache_data(
    show_spinner="Replaying capture through the pipeline...",
    max_entries=12,
    hash_funcs={Settings: lambda s: repr(s)},
)
def replay(settings: Settings) -> Run:
    """Run one capture through the full pipeline under these settings."""
    path = GPSD / settings.trace
    if not path.exists():
        return Run(frame=pd.DataFrame(), error=f"capture {settings.trace} not found")

    sentences = list(sentences_from_file(path))
    control = list(epochs_from_sentences(sentences))
    split = int(len(control) * SURVEY_FRACTION)
    if split < 25:
        return Run(
            frame=pd.DataFrame(),
            error=f"{len(control)} epochs in this capture; at least {MIN_EPOCHS} are "
                  f"needed so that the first {int(SURVEY_FRACTION * 100)}% can survey in",
        )

    calibration, _ = calibrate_from_epochs(control[:split])

    # The honest clock. Replay has to advance the reference with the capture,
    # not with the wall clock, or every epoch would look hours stale.
    truth = {i: e.utc.timestamp() for i, e in enumerate(control) if e.utc}

    scenario = _build_scenario(settings)
    injected = inject(sentences, scenario)

    reference = FixedReference(
        uncertainty=settings.ntp_uncertainty_ms / 1000.0,
        available=settings.ntp_available,
    )
    trust_config = TrustConfig(
        fusion=Fusion(settings.fusion),
        reject_below=settings.reject_below,
        suspect_below=settings.suspect_below,
        recover_above=settings.recover_above,
        recover_hold_s=settings.recover_hold_s,
    )
    pipeline = Pipeline(
        calibration=calibration, reference=reference, trust_config=trust_config
    )

    # Epoch-indexed attack flags rather than a fraction of the trace. The
    # injector counts fix cycles by GGA sentence; assembly produces fewer
    # epochs than that, so a fraction of each gives two different answers.
    epochs, attacked = assemble_with_flags(
        injected.sentences, injected.attack_flags, pipeline.parse_stats
    )

    rows, sats, evidence, detections = [], [], [], []
    logged_events = 0
    events: list[dict] = []

    for i, epoch in enumerate(epochs):
        host = truth.get(i)
        reference.set(host)
        step = pipeline.step(epoch, host_time=host)

        by_detector = {e.detector: e for e in step.evidence}
        offset_ev = by_detector.get("time_offset")
        offset = offset_ev.value if offset_ev is not None and offset_ev.applicable else None

        tracked = [s for s in epoch.snr if s and s > 0]
        served = step.decision.time_s
        served_error = None if (served is None or host is None) else served - host
        gps_error = None if (epoch.utc is None or host is None) else (
            epoch.utc.timestamp() - host
        )

        rows.append({
            "epoch": i,
            "utc": epoch.utc,
            "attacked": bool(attacked[i]) if i < len(attacked) else False,
            "trust": step.verdict.trust,
            "state": step.verdict.state.value,
            "hold_remaining_s": step.verdict.hold_remaining_s,
            "source": step.decision.source.value,
            "source_reason": step.decision.reason,
            "uncertainty_s": step.decision.uncertainty_s,
            "holdover_s": step.decision.holdover_s,
            "served_time_s": served,
            "host_time_s": host,
            "served_error_s": served_error,
            "gps_error_s": gps_error,
            "lat": epoch.lat,
            "lon": epoch.lon,
            "altitude_m": epoch.altitude_m,
            "deviation_m": step.deviation_m,
            "fix_quality": epoch.fix_quality,
            "sats_in_view": epoch.sats_in_view,
            "sats_used": epoch.num_sats_used,
            "sats_tracked": len(tracked),
            "hdop": epoch.hdop,
            "pdop": epoch.pdop,
            "vdop": epoch.vdop,
            "snr_mean": (sum(tracked) / len(tracked)) if tracked else None,
            "snr_spread": (max(tracked) - min(tracked)) if len(tracked) > 1 else None,
            "speed_mps": epoch.sog_mps,
            "course_deg": epoch.cog_deg,
            "time_offset_s": offset,
            "n_fired": len(step.fired),
            "fired": ", ".join(e.detector for e in step.fired),
        })

        sats.append(epoch.satellites)
        evidence.append([
            {
                "detector": e.detector,
                "score": e.score,
                "applicable": e.applicable,
                "value": e.value,
                "warn": e.warn,
                "alarm": e.alarm,
                "reason": e.reason,
            }
            for e in step.evidence
        ])

        for e in step.fired:
            detections.append({
                "epoch": i,
                "detector": e.detector,
                "score": round(e.score, 3),
                "reason": e.reason,
            })

        # Source switches are attributed to the epoch that caused them, so the
        # event log lines up with the timeline instead of carrying a bare
        # wall-clock stamp the operator has to correlate by hand.
        for ev in pipeline.manager.events[logged_events:]:
            events.append({
                "epoch": i,
                "from": ev.from_source.value,
                "to": ev.to_source.value,
                "step_s": ev.step_s,
                "reason": ev.reason,
            })
        logged_events = len(pipeline.manager.events)

    return Run(
        frame=pd.DataFrame(rows),
        satellites=sats,
        evidence=evidence,
        events=events,
        detections=pd.DataFrame(detections),
        calibration=pd.DataFrame([
            {
                "feature": name,
                "fires when": "above" if f.direction == "high" else "below",
                "warn (p99)": round(f.warn, 4),
                "alarm (p99.99)": round(f.alarm, 4),
            }
            for name, f in sorted(calibration.features.items())
        ]),
        status=pipeline.status(),
        scenario={
            "name": scenario.name,
            "description": scenario.description,
            "expect": scenario.expect,
        },
        detector_rationale={d.name: d.rationale for d in pipeline.detectors},
        reference=(calibration.ref_lat, calibration.ref_lon),
        survey_epochs=split,
    )
