# GPS Spoofing Detection and Secure Time Synchronization

UG Honours Project (EC22060).

**Student:** Yajnesh Juttu Sundaram (2127230701171)
**Supervisor:** Dr. T. J. Jeyaprabha, Associate Professor, ECE Department

## What this is

Network infrastructure commonly takes its time from a GPS receiver acting as a
Stratum-0 source and redistributes it over NTP or PTP. Civil GPS is
unauthenticated, so a spoofed receiver reports a false time while otherwise
looking healthy, and that false time propagates into certificate validation,
Kerberos authentication, log ordering and transaction sequencing.

This project puts a trust layer between the receiver and the time distribution
stack. It parses NMEA, runs eight independent plausibility checks, fuses them
into a trust score, and withdraws GPS when that score falls, failing over to an
independent network reference or to holdover that reports its own growing
uncertainty.

```text
NMEA in -> parse -> epoch -> detectors -> trust -> time source -> served time
                                  ^                     ^
                                  +---- NTP reference --+
```

## Headline results

Measured on 110,070 held-out epochs (17-18 September) after calibrating on
15-16 September only.

| | |
|---|---|
| Blind trust would accept compromised time | **66.5%** of epochs |
| System accepts GPS for | 15.3% of epochs |
| ...of which actually compromised | **4.2%** |
| Residual risk reduction | **15.7x** |
| Cost: unnecessary rejections | 22.2% |

Detection F1 at the chosen operating point is 87.7% (precision 86.9%, recall
88.5%). A higher-precision point is available at 94.7% precision, 71.5% recall,
5.0% false alarm rate.

Against injected attacks on five real captures: a +45 s time step is caught in
4 epochs, a 0.25 s/epoch slew in 16, and the unmodified control produced 2 false
alarms in 671 epochs.

## Reading order

Three documents carry the reasoning, and they are worth reading before the code.

- `report/main.pdf` - the report, IEEE format, 10 pages.
- `docs/data-validity.md` - why the corpus's clean labels cannot be used as a
  literal negative class, and the three explanations that were tested.
- `docs/decisions.md` - the six design decisions and what forced each.

## Scope and constraints

- **No RF transmission.** Real GPS spoofing transmission is illegal. Attacks are
  either observed in a licensed national test range or injected at the NMEA data
  layer.
- **Real baseline, synthetic attacks only.** Normal-operation data is real
  receiver output throughout.
- **Stationary receiver.** The target is a fixed timing receiver, which is how
  real GNSS timing receivers are operated.
- **Windows, pure Python.** No chrony. The host clock is read, never written.

## Setup

Requires Python 3.13 and Git.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Reproducing everything

Each stage is one script, and each writes an artefact the next one reads.

```powershell
python scripts/fetch_data.py        # download public datasets, pin SHA-256
#   then extract data/raw/gpsd/gpsd-test-daemon.tar.gz in place
python scripts/build_epochs.py      # 302,158 labelled epochs   (~4 min)
python scripts/build_baseline.py    # thresholds from training days
python scripts/tune_weights.py      # detector weights from training days
python scripts/run_evaluation.py    # held-out evaluation
python scripts/run_scenarios.py     # injected attack scenarios
python scripts/make_figures.py      # figures for the report
```

Then the dashboard, or a single replay:

```powershell
streamlit run dashboard/app.py
python scripts/run_pipeline.py --trace telit-he910.log --scenario time_step
python scripts/run_pipeline.py --list
```

### The monitoring console

`streamlit run dashboard/app.py` opens a live console on
http://localhost:8501. It replays a recorded capture through the same pipeline
objects the evaluation uses, so nothing on screen is reimplemented for display.

- **Board:** served time source and uncertainty, trust state with the remaining
  recovery hold, map of claimed vs surveyed position (LOCAL / REGION / GLOBE,
  plus a plan view in metres), satellite sky plot by constellation, one card
  per detector, and detail panels for time integrity, signal and geometry,
  satellites, the event log and system status.
- **Admin rail:** capture selection; attack injection (vector, magnitude,
  window); network reference on/off and its uncertainty; fusion rule and the
  reject, suspect and recovery thresholds and the recovery hold; playback
  (play/pause, step, rate, loop, epoch slider); the calibration in force.
- **Defaults differ from the evaluation on purpose.** The console uses a 20 s
  recovery hold (evaluation: 300 s) because most gpsd captures are about two
  minutes long, and noisy-OR fusion so a single detector can drive the
  response visibly. The attack window defaults to 55-70 % of the capture so
  the return to GPS is visible.
- The board redraws every 10 s and advances a batch of epochs per redraw.
- "Resolve street address" calls OpenStreetMap Nominatim. It is the only
  network access at display time, is cached per location, and nothing in the
  detection path depends on it. Turn it off to run fully offline.

Requires Streamlit 1.50 or later (timed fragments, app-scoped reruns).

Tests:

```powershell
python -m pytest tests/ -q          # 100 tests
```

Building the report needs a LaTeX engine. Tectonic is convenient because it is a
single binary and fetches what it needs:

```powershell
cd report
tectonic -X compile main.tex
```

## Data

All datasets are public and openly licensed. Provenance, licences and the
sources that were considered and rejected are recorded in `data/SOURCES.md`.

| Source | Licence | Used for |
|---|---|---|
| JammerTest 2025 (SimulaMet) | CC-BY-4.0 | baseline and real-attack evaluation |
| JammerTest transmission plan (NPRA) | MIT | ground-truth attack labels |
| gpsd test corpus | BSD-2-Clause | parser robustness, attack substrate |

Nothing under `data/raw/` is committed; `scripts/fetch_data.py` reproduces it
and pins the exact bytes by SHA-256.

## Layout

```text
src/gpstrust/
  nmea/          framing, robust parsing, epoch assembly
  datasets/      JammerTest adapter and label construction
  detect/        the eight detectors
  timesource/    NTP reference, holdover clock, source manager
  attacks/       NMEA-layer attack injection
  config.py      calibration loading; refuses invented thresholds
  calibrate.py   survey-in from a short clean segment
  features.py    derived per-epoch quantities
  trust.py       fusion and the source state machine
  pipeline.py    the assembled system
  store.py       SQLite event log
dashboard/       live monitoring console (app, engine, panels, geo, theme)
scripts/         one per stage, listed above
report/          IEEE-format report and bibliography
docs/            decisions, data validity
tests/           100 tests
```

## Notes on a few design choices

Some of these are unusual enough to be worth stating plainly.

**Detectors abstain rather than score zero.** A detector that cannot assess an
epoch returns *not applicable*. Missing GSV is not evidence of innocence, and
scoring it as such would raise trust during exactly the degraded conditions
where the receiver is least reliable.

**The time-offset detector refuses host timestamps.** The JammerTest corpus
kept the node's arrival time, not the receiver's claimed UTC. The detector
rejects such epochs in code rather than silently comparing the wrong quantity.

**Holdover anchors are withheld until confirmed.** Detection is not
instantaneous, so anchoring holdover on every accepted epoch copies the
attacker's clock into the fallback during the detector's own latency window.
This was a real bug, found by a test; see the discussion in the report.

**Parse failures are counted, not repaired.** A rise in checksum failures is
itself evidence of interference.

**The event log stores both clocks and orders by host time.** A log timestamped
only by GPS is timestamped by the attacker.
