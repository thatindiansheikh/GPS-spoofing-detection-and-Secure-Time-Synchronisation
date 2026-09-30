"""GPSTRUST - Enterprise Time Integrity Monitoring Console.

    streamlit run dashboard/app.py

An operations monitoring console for GNSS time integrity, spoofing detection,
and autonomous time failover.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

import engine
import panels
from engine import SURVEY_FRACTION, VECTORS, VECTOR_ORDER, Settings, replay
from geo import (
    Place, bearing_deg, compass, decimal, dms, reverse_geocode,
    utc_offset_estimate,
)
from theme import AMBER, BLUE, CYAN, GREEN, MUTED, RED, VIOLET, css

REFRESH_S = 10.0

st.set_page_config(
    page_title="GPSTRUST // Time Integrity Monitor",
    page_icon="\U0001f6f0",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(css(), unsafe_allow_html=True)

#: Epochs per second at each playback rate.
RATES = {"0.5x": 0.5, "1x": 1.0, "2x": 2.0, "4x": 4.0, "8x": 8.0}

ss = st.session_state
ss.setdefault("playing", True)
ss.setdefault("rate", "2x")
ss.setdefault("loop", True)
ss.setdefault("_pending_cursor", None)


def group(label: str) -> None:
    st.sidebar.markdown(f'<div class="grp">{label}</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=256)
def resolve_place(lat_key: float, lon_key: float) -> Place:
    """Reverse geocode coordinate via Nominatim, cached per ~10m."""
    return reverse_geocode(lat_key, lon_key)


# Apply programmatic cursor moves prior to slider initialization
if ss["_pending_cursor"] is not None:
    ss["epoch_slider"] = int(ss["_pending_cursor"])
    ss["_pending_cursor"] = None


# ---------------------------------------------------------------------------
# Admin & Operator Controls Sidebar
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    '<div style="font-size:12px;font-weight:700;letter-spacing:.12em;color:#f1f5f9;padding:2px 0 2px 0">'
    'OPERATIONS <span style="color:#0ea5e9">CONSOLE</span></div>'
    '<div style="font-size:10px;color:#64748b;letter-spacing:.04em">'
    'Telecommunications & Aerospace Integrity</div>',
    unsafe_allow_html=True,
)

traces = engine.available_traces()
if not traces:
    st.error(
        "No captures found. Run `python scripts/fetch_data.py`, then extract "
        "`data/raw/gpsd/gpsd-test-daemon.tar.gz`."
    )
    st.stop()

group("Receiver feed")
PREFERRED = "quectel-l76k-dual.log"
default_trace = PREFERRED if PREFERRED in traces else traces[0]
trace = st.sidebar.selectbox(
    "Capture", traces, index=traces.index(default_trace),
    help="Recorded NMEA stream from an operational GNSS receiver.",
)
resolve_address = st.sidebar.toggle(
    "Resolve street address", value=True,
    help="Query OpenStreetMap Nominatim reverse geocode service when paused.",
)

group("Attack injection")
armed = st.sidebar.toggle(
    "Arm injector", value=False,
    help="Off replays clean baseline capture. On injects selected threat profile.",
)
vector = st.sidebar.selectbox(
    "Attack vector", VECTOR_ORDER,
    format_func=lambda k: VECTORS[k]["label"],
    index=VECTOR_ORDER.index("position_jump"),
    disabled=not armed,
)
spec = VECTORS[vector]
param = spec["param"]
if param is not None:
    magnitude = st.sidebar.slider(
        f"{param['label']} ({param['unit']})" if param["unit"] else param["label"],
        float(param["min"]), float(param["max"]), float(param["default"]),
        step=float(param["step"]), disabled=not armed, key=f"magnitude_{vector}",
    )
else:
    magnitude = 0.0

window = st.sidebar.slider(
    "Attack window (% of capture)", int(SURVEY_FRACTION * 100), 100, (55, 70),
    disabled=not armed,
    help="Constrained to begin after survey-in baseline calibration.",
)

st.sidebar.markdown(
    f'<div style="font-size:10.5px;color:{"#f43f5e" if armed and vector != "none" else MUTED};'
    f'border:1px solid {"#f43f5e55" if armed and vector != "none" else "#2d3748"};'
    f'border-radius:5px;padding:7px 9px;margin-top:5px;line-height:1.4">'
    + (
        f'<b style="color:#f43f5e">INJECTION ARMED</b><br>{spec["action"]}'
        if armed and vector != "none"
        else "<b>INJECTION INACTIVE</b><br>Replaying capture baseline untouched."
    )
    + "</div>",
    unsafe_allow_html=True,
)

group("Time reference")
ntp_available = st.sidebar.toggle(
    "Network NTP reference reachable", value=True,
    help="Simulate availability of external Stratum-1/2 network peer.",
)
ntp_uncertainty_ms = st.sidebar.slider(
    "Reference uncertainty (ms)", 1.0, 200.0, 20.0, step=1.0,
    disabled=not ntp_available,
)

group("Trust & failover policy")
fusion = st.sidebar.radio(
    "Fusion logic", ["noisy_or", "mean"], horizontal=True,
    help="noisy_or: any single high-confidence anomaly trips failover. mean: weighted consensus.",
)
reject_below = st.sidebar.slider("Reject GPS below trust", 0.10, 0.99, 0.80, step=0.01)
suspect_below = st.sidebar.slider("Flag suspect below trust", 0.10, 1.00, 0.90, step=0.01)
recover_above = st.sidebar.slider("Allow recovery above trust", 0.10, 1.00, 0.85, step=0.01)
recover_hold_s = st.sidebar.slider(
    "Recovery hold (s)", 0.0, 900.0, 20.0, step=5.0,
    help="Duration clean evidence must persist before re-trusting GNSS.",
)

settings = Settings(
    trace=trace,
    vector=vector,
    magnitude=magnitude,
    window_start_pct=window[0],
    window_end_pct=window[1],
    armed=armed,
    ntp_available=ntp_available,
    ntp_uncertainty_ms=ntp_uncertainty_ms,
    fusion=fusion,
    reject_below=reject_below,
    suspect_below=suspect_below,
    recover_above=recover_above,
    recover_hold_s=recover_hold_s,
)

run = replay(settings)
if run.error:
    st.error(run.error)
    st.stop()

frame = run.frame
total = run.total

if int(ss.get("epoch_slider", 0)) > total - 1:
    ss["epoch_slider"] = total - 1

group("Feed playback")
b1, b2, b3, b4 = st.sidebar.columns(4)


def _jump(target: int) -> None:
    ss["epoch_slider"] = max(0, min(total - 1, int(target)))


def _toggle_playing() -> None:
    ss["playing"] = not ss["playing"]


current = int(ss.get("epoch_slider", 0))
b1.button("⏮", width="stretch", help="Restart from epoch 0",
          on_click=_jump, args=(0,))
b2.button("◀", width="stretch", help="Step back 1 epoch",
          on_click=_jump, args=(current - 1,))
b3.button("⏸" if ss["playing"] else "▶", width="stretch",
          help="Pause or resume feed playback",
          on_click=_toggle_playing)
b4.button("▶❘", width="stretch", help="Step forward 1 epoch",
          on_click=_jump, args=(current + 1,))

ss["rate"] = st.sidebar.select_slider(
    "Playback rate (epochs/s)", list(RATES), value=ss["rate"],
    help=f"Feed updates every {REFRESH_S:g}s advancing by rate x {REFRESH_S:g} epochs.",
)
ss["loop"] = st.sidebar.toggle("Loop at capture end", value=ss["loop"])

cursor = st.sidebar.slider("Epoch scrubber", 0, max(total - 1, 0), key="epoch_slider")

with st.sidebar.expander("Calibration baseline"):
    st.caption(
        f"Calibrated over initial {int(SURVEY_FRACTION * 100)}% of capture "
        f"({run.survey_epochs} epochs). All detector thresholds are measured from baseline."
    )
    st.dataframe(run.calibration, width="stretch")
    skipped = run.status["detectors_skipped"]
    if skipped:
        st.warning("Omitted (insufficient calibration data): " + ", ".join(skipped))


# ---------------------------------------------------------------------------
# Main Executive Monitoring Board
# ---------------------------------------------------------------------------

now = frame.iloc[cursor]
view = frame.iloc[: cursor + 1]
attacking_now = bool(now["attacked"])

served = now["served_time_s"]
served_text = (
    datetime.fromtimestamp(served, tz=timezone.utc).strftime("%H:%M:%S")
    if not panels.isna(served)
    else "--:--:--"
)
attack_label = (
    f"{VECTORS[vector]['label']}"
    + (f" @ {magnitude:g} {VECTORS[vector]['param']['unit']}"
       if VECTORS[vector]["param"] else "")
)

panels.topbar(
    trace=trace,
    served_utc=served_text,
    wall_utc=datetime.now(timezone.utc).strftime("%H:%M:%S"),
    epoch=cursor,
    total=total,
    playing=ss["playing"],
    attacking=attacking_now,
    attack_label=attack_label,
    source=str(now["source"]),
    state=str(now["state"]),
    trust_score=float(now["trust"]) if not panels.isna(now["trust"]) else None,
)

panels.tiles(now, holdover_s=float(now["holdover_s"] or 0.0))

# -- Map and Sky View -------------------------------------------------------

left, right = st.columns([1.35, 1], gap="small")

with left.container(border=True):
    map_header_col, map_nav_col = st.columns([1.1, 1.9])
    with map_header_col:
        panels.panel_open("Position & Trajectory", "Reported fix vs surveyed benchmark")
    with map_nav_col:
        map_view_mode = st.radio(
            "Map Projection",
            ["Local Focus", "Regional View", "Globe View", "Plan View"],
            horizontal=True,
            label_visibility="collapsed",
            key="map_view_selector",
            help="Toggle between earth map projections and local metric Cartesian plan view",
        )

    if map_view_mode == "Plan View":
        plan = panels.plan_view(frame, cursor, run.reference)
        if plan is None:
            st.markdown('<div class="empty">No position coordinates available in this capture.</div>',
                        unsafe_allow_html=True)
        else:
            st.plotly_chart(plan, width="stretch", key="planview",
                            config={"displayModeBar": False})
            st.markdown(
                '<div class="hint">Cartesian displacement in metres from surveyed station benchmark. '
                'Concentric rings denote radial distance. Nominal stationary fixes scatter inside the innermost ring.</div>',
                unsafe_allow_html=True,
            )
    else:
        mode_map = {"Local Focus": "local", "Regional View": "region", "Globe View": "globe"}
        chosen_mode = mode_map.get(map_view_mode, "local")
        st.plotly_chart(
            panels.world_map(frame, cursor, run.reference, chosen_mode),
            width="stretch", key="worldmap",
            config={"displayModeBar": False, "scrollZoom": False},
        )
        st.markdown(
            f'<div class="chips">'
            f'<span class="chip"><i style="background:{GREEN}"></i>Current Fix</span>'
            f'<span class="chip"><i style="background:{VIOLET}"></i>Station Benchmark</span>'
            f'<span class="chip"><i style="background:{CYAN}"></i>Nominal Track</span>'
            f'<span class="chip"><i style="background:{RED}"></i>Injected Track</span>'
            f"</div>"
            '<div class="hint">Geographic position tracking with reference offset line. '
            'Vector coastline and country boundaries render offline or from cached geometry.</div>',
            unsafe_allow_html=True,
        )

    # Coordinate & Geocoding Details
    lat, lon = now["lat"], now["lon"]
    ref_lat, ref_lon = run.reference

    place = None
    pending = False
    if resolve_address and not panels.isna(lat):
        key = (round(float(lat), 3), round(float(lon), 3))
        seen = ss.setdefault("_places", {})
        if key in seen:
            place = seen[key]
        elif not ss["playing"]:
            place = resolve_place(*key)
            seen[key] = place
        else:
            pending = True

    if place is None:
        if not resolve_address:
            address_line = '<span style="color:#64748b">address lookup off</span>'
        elif pending:
            address_line = ('<span style="color:#64748b">new coordinate &mdash; '
                            'pause feed to resolve address</span>')
        else:
            address_line = "--"
    elif not place.ok:
        address_line = f'<span style="color:{AMBER}">{place.line} ({place.detail})</span>'
    else:
        address_line = f"{place.line}" + (
            f'<br><span style="color:#94a3b8">{place.detail}'
            + (f", {place.country}" if place.country else "")
            + "</span>"
            if place.detail else ""
        )

    dev = now["deviation_m"]
    if not panels.isna(dev) and ref_lat is not None and not panels.isna(lat):
        brg = bearing_deg(ref_lat, ref_lon, float(lat), float(lon))
        offset_text = f"{dev:,.0f} m {compass(brg)} ({brg:.0f}°)"
    else:
        offset_text = "--"

    panels.kv_strip([
        ("latitude", decimal(None if panels.isna(lat) else float(lat))),
        ("longitude", decimal(None if panels.isna(lon) else float(lon))),
        ("latitude (dms)", dms(None if panels.isna(lat) else float(lat), True)),
        ("longitude (dms)", dms(None if panels.isna(lon) else float(lon), False)),
        ("altitude", panels.num(
            None if panels.isna(now["altitude_m"]) else float(now["altitude_m"]), ",.1f")
            + " m"),
        ("solar zone (est.)", utc_offset_estimate(
            None if panels.isna(lon) else float(lon))),
        ("station offset", offset_text),
        ("location", address_line),
    ])

with right.container(border=True):
    sats = run.satellites[cursor]
    tracked = sum(1 for s in sats if s.tracked)
    panels.panel_open("Sky View & Constellations", f"{tracked} tracked of {len(sats)} in view")
    st.plotly_chart(panels.skyplot(sats), width="stretch", key="skyplot",
                    config={"displayModeBar": False})
    panels.constellation_chips(sats)
    st.markdown(
        '<div class="hint">Polar projection: zenith at center, perimeter is horizon, north is up. '
        'Color denotes C/N0 (dB-Hz). Hollow icons are in-view untracked satellites. '
        'Dotted ring indicates 10&deg; elevation mask. Uniform power across constellations indicates single-transmitter spoofing.</div>',
        unsafe_allow_html=True,
    )

# -- Grouped Detector Integrity Rail ----------------------------------------

with st.container(border=True):
    panels.panel_open(
        "Detector Integrity Rail",
        "Multi-domain anomaly detection suite · 0.00 indicates nominal baseline",
    )
    panels.detector_rail(run.evidence[cursor], run.detector_rationale)
    st.markdown(
        '<div class="hint" style="margin-top:8px">Detector scores are fused into composite trust score. '
        'Checks marked N/A lack prerequisite telemetry for the current epoch and are excluded from Bayesian fusion.</div>',
        unsafe_allow_html=True,
    )

# -- Detail Telemetry Panels (Tabs) -----------------------------------------

tab_time, tab_signal, tab_sats, tab_events, tab_system = st.tabs([
    "Time Integrity",
    "Signal & Geometry",
    "Satellites",
    "Security Event Log",
    "System Diagnostics",
])

with tab_time:
    c1, c2 = st.columns(2)
    with c1:
        panels.chart_block(
            "Composite Trust Score",
            f"Bayesian multi-detector trust metric. Failover activates when score breaches reject threshold ({reject_below:.2f}). Shaded red zones designate injected attack epochs.",
            panels.timeline(
                view, total, cursor,
                [dict(column="trust", name="trust", colour=CYAN, fill="tozeroy",
                      fillcolor="rgba(14,165,233,0.12)")],
                thresholds=[
                    dict(y=reject_below, colour=RED, label="reject"),
                    dict(y=suspect_below, colour=AMBER, label="suspect"),
                ],
                y_range=[-0.03, 1.03],
            ),
            key="c_trust",
        )
        panels.chart_block(
            "Antenna Station Deviation",
            "Stationary radial drift from surveyed benchmark coordinates. Steps denote coordinate jumps; ramps denote drift attacks.",
            panels.timeline(
                view, total, cursor,
                [dict(column="deviation_m", name="deviation", colour=VIOLET)],
                unit="m",
            ),
            key="c_dev",
        )
    with c2:
        panels.chart_block(
            "Served Clock Error vs Ground Truth",
            "Comparative timing error: served network clock output (green) vs raw unvalidated GNSS receiver input (amber). Divergence reflects absorbed attack displacement.",
            panels.timeline(
                view, total, cursor,
                [
                    dict(column="gps_error_s", name="raw receiver claim", colour=AMBER,
                         dash="dot"),
                    dict(column="served_error_s", name="served to network",
                         colour=GREEN, width=2.2),
                ],
                unit="s",
            ),
            key="c_err",
        )
        panels.chart_block(
            "Served Time Uncertainty (95% CI)",
            "Upper-bound timing dispersion reported to downstream network clients. Increases during local oscillator holdover drift.",
            panels.timeline(
                view, total, cursor,
                [dict(column="uncertainty_s", name="uncertainty", colour=BLUE)],
                unit="s", log_y=True,
            ),
            key="c_unc",
        )

    panels.chart_block(
        "Independent NTP Reference Clock Offset",
        "Direct time-of-week phase offset measured against independent stratum network peer. Detects clock-only timing attacks.",
        panels.timeline(
            view, total, cursor,
            [dict(column="time_offset_s", name="offset", colour=CYAN)],
            unit="s", height=180,
        ),
        key="c_off",
    )

with tab_signal:
    c1, c2 = st.columns(2)
    with c1:
        panels.chart_block(
            "Carrier-to-Noise Density (C/N0)",
            "Carrier-to-noise ratio per visible satellite in constellation order. Uniform levels across all azimuths indicate artificial RF transmitter.",
            panels.snr_bars(run.satellites[cursor]),
            key="c_snrbars",
        )
        panels.chart_block(
            "Satellite Tracking Continuity",
            "Constellation count dynamics. Sudden drops indicate RF jamming; static counts during movement indicate replay.",
            panels.timeline(
                view, total, cursor,
                [
                    dict(column="sats_in_view", name="in view", colour=CYAN),
                    dict(column="sats_used", name="used in fix", colour=GREEN),
                    dict(column="sats_tracked", name="tracked", colour=BLUE,
                         dash="dot"),
                ],
            ),
            key="c_sats",
        )
    with c2:
        panels.chart_block(
            "Signal Strength Mean & Spread",
            "Constellation mean C/N0 and cross-satellite variance. Spread collapse toward zero signifies single-source RF overpower.",
            panels.timeline(
                view, total, cursor,
                [
                    dict(column="snr_mean", name="mean", colour=CYAN),
                    dict(column="snr_spread", name="spread (max-min)", colour=AMBER,
                         dash="dot"),
                ],
                unit="dB-Hz",
            ),
            key="c_snr",
        )
        panels.chart_block(
            "Constellation Dilution of Precision",
            "Geometric Dilution of Precision (HDOP, PDOP, VDOP). Lower values indicate optimal satellite distribution.",
            panels.timeline(
                view, total, cursor,
                [
                    dict(column="hdop", name="HDOP", colour=CYAN),
                    dict(column="pdop", name="PDOP", colour=VIOLET, dash="dot"),
                    dict(column="vdop", name="VDOP", colour=BLUE, dash="dot"),
                ],
            ),
            key="c_dop",
        )

with tab_sats:
    table = panels.satellite_table(run.satellites[cursor])
    if table.empty:
        st.markdown('<div class="empty">No satellite view reported in this epoch.</div>',
                    unsafe_allow_html=True)
    else:
        st.dataframe(table, width="stretch", hide_index=True, height=380)
        st.markdown(
            '<div class="hint">Active epoch satellite telemetry: PRN identifier, constellation source, azimuth, elevation, and C/N0 tracking state.</div>',
            unsafe_allow_html=True,
        )

with tab_events:
    c1, c2 = st.columns(2)
    with c1:
        panels.panel_open("Time Source Transitions", "audit trail · newest first")
        panels.event_log(run.events, cursor)
        st.markdown(
            '<div class="hint">Discontinuity phase steps logged during failover transitions between GNSS, NTP, and local oscillator.</div>',
            unsafe_allow_html=True,
        )
    with c2:
        panels.panel_open("Anomaly Detections", "detector trigger log · newest first")
        panels.detection_log(run.detections, cursor)

with tab_system:
    c1, c2 = st.columns(2)
    with c1:
        panels.panel_open("Scenario Specification", run.scenario["description"])
        st.markdown(
            f'<div class="hint"><b>Expected Threat Profile:</b> '
            f'{panels.esc(run.scenario["expect"])}</div>',
            unsafe_allow_html=True,
        )
        panels.panel_open("NMEA Parse Stream Integrity", "raw sentence validation counters")
        st.json(run.status["parse"], expanded=False)
        st.markdown(
            '<div class="hint">Sentence syntax and checksum validation failures indicate RF interference or transmission corruptions.</div>',
            unsafe_allow_html=True,
        )
    with c2:
        panels.panel_open("Engine Configuration", "runtime operational parameters")
        panels.kv_strip([
            ("detectors running", str(len(run.status["detectors"]))),
            ("fusion mode", fusion),
            ("reject below", f"{reject_below:.2f}"),
            ("recovery hold", f"{recover_hold_s:.0f} s"),
            ("network reference",
             "reachable" if ntp_available else "unreachable (forced)"),
            ("reference uncertainty",
             f"{ntp_uncertainty_ms:.0f} ms" if ntp_available else "n/a"),
            ("surveyed benchmark",
             f"{run.reference[0]:.5f}, {run.reference[1]:.5f}" if run.reference[0] is not None else "--"),
            ("source transitions",
             str(len([e for e in run.events if e["epoch"] <= cursor]))),
        ])
        panels.panel_open("Time Authority State", "end-of-capture synchronization status")
        st.json(run.status["time_source"], expanded=False)


# ---------------------------------------------------------------------------
# Background Playback Timer Fragment
# ---------------------------------------------------------------------------


@st.fragment(run_every=REFRESH_S)
def _playback_tick() -> None:
    """Advance the feed on a timer that runs between script runs."""
    if not ss.get("_tick_primed"):
        ss["_tick_primed"] = True
        return
    cur = int(ss.get("epoch_slider", cursor))
    at_end = cur >= total - 1
    if at_end and not ss["loop"]:
        ss["playing"] = False
    else:
        step = max(1, round(RATES[ss["rate"]] * REFRESH_S))
        ss["_pending_cursor"] = 0 if at_end else min(cur + step, total - 1)
    st.rerun(scope="app")


if ss["playing"]:
    ss["_tick_primed"] = False
    _playback_tick()
