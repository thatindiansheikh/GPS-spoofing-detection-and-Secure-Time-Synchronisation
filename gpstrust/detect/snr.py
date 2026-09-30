"""Signal-strength checks on the reported satellite view.

These are the two mechanisms that actually separate spoofing from clean
operation in the JammerTest data, and they work for a physical reason. A
spoofer radiates every counterfeit signal from one antenna, so all of them
arrive along the same path at a similar level. The real constellation does not
behave that way: satellites sit at different elevations, travel different path
lengths, and are attenuated differently, so their reported SNR spreads out.

Two consequences, checked separately:

* The spoofer must overpower the genuine signals to capture the receiver, so
  mean SNR rises above anything the real sky produces.
* The spread across satellites collapses, because one transmitter cannot
  reproduce the geometry-driven variation of a real constellation.

Both are measured against the clean distribution rather than against a textbook
number, because the absolute values depend on the receiver and its antenna.
"""

from __future__ import annotations

from statistics import mean, pstdev

from ..config import Calibration
from ..nmea.epoch import Epoch
from .base import Detector, Evidence

# Below this many tracked satellites the spread statistic is noise. Two
# satellites can look uniform by chance; ten cannot.
MIN_SATS = 4


def _snr_values(epoch: Epoch) -> list[int]:
    """Tracked satellites only.

    Satellites in view but untracked report an empty SNR field, which the
    parser drops rather than recording as zero. Including them as zero would
    depress the mean and inflate the spread, pointing both detectors the wrong
    way at exactly the moment the receiver is struggling.
    """
    return [s for s in epoch.snr if s is not None and s > 0]


class SnrPowerDetector(Detector):
    """Mean SNR above what the real constellation delivers."""

    name = "snr_power"
    rationale = (
        "A spoofer has to out-power the genuine signals to capture the "
        "receiver, which lifts mean reported SNR above the clean range."
    )

    def __init__(self, calibration: Calibration):
        self.feature = calibration.feature("snr_mean")

    def update(self, epoch: Epoch) -> Evidence:
        values = _snr_values(epoch)
        if len(values) < MIN_SATS:
            return Evidence.not_applicable(
                self.name, f"only {len(values)} tracked satellites; need {MIN_SATS}"
            )

        m = mean(values)
        score = self.feature.score(m) or 0.0
        return Evidence(
            detector=self.name,
            score=score,
            value=m,
            warn=self.feature.warn,
            alarm=self.feature.alarm,
            reason=(
                f"mean SNR {m:.1f} dB-Hz above clean p99 of {self.feature.warn:.1f}"
                if score > 0
                else f"mean SNR {m:.1f} dB-Hz within clean range"
            ),
            detail={"n_sats": len(values)},
        )


class SnrUniformityDetector(Detector):
    """Spread across satellites too small for a real sky."""

    name = "snr_uniformity"
    rationale = (
        "Real satellites differ in elevation and path length, so their SNR "
        "spreads out. Signals from a single spoofing antenna do not."
    )

    def __init__(self, calibration: Calibration):
        self.feature = calibration.feature("snr_cv")

    def update(self, epoch: Epoch) -> Evidence:
        values = _snr_values(epoch)
        if len(values) < MIN_SATS:
            return Evidence.not_applicable(
                self.name, f"only {len(values)} tracked satellites; need {MIN_SATS}"
            )

        m = mean(values)
        if m <= 0:
            return Evidence.not_applicable(self.name, "mean SNR is zero")

        # Coefficient of variation rather than raw standard deviation: it stays
        # comparable when the whole constellation is attenuated or amplified,
        # which is precisely the situation being judged.
        cv = pstdev(values) / m
        score = self.feature.score(cv) or 0.0
        return Evidence(
            detector=self.name,
            score=score,
            value=cv,
            warn=self.feature.warn,
            alarm=self.feature.alarm,
            reason=(
                f"SNR spread {cv:.3f} below clean p1 of {self.feature.warn:.3f}: "
                "signals are more uniform than real sky geometry produces"
                if score > 0
                else f"SNR spread {cv:.3f} consistent with real sky"
            ),
            detail={"n_sats": len(values), "mean": m},
        )
