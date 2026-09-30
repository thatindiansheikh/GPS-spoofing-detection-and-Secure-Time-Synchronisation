"""Enterprise monitoring console visualization panels and components.

Modular display elements designed for high operational clarity:
- Executive status header bar with active authority, clocks, and threat indicators
- Telemetry metric status cards with visual status pills
- Grouped functional domain detector rail (Time, Spatial, RF)
- Map, plan view, polar skyplot, and timeline charts
"""

from __future__ import annotations

import html
import math
from typing import Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from geo import compass, constellation
from theme import (
    AXIS, AMBER, BLUE, BORDER, CYAN, DIM, GREEN, GRID, MUTED,
    PLOT_LAYOUT, RED, SNR_SCALE, SOURCE_COLOUR, SOURCE_LABEL, STATE_COLOUR,
    STATE_MEANING, TEXT, VIOLET,
)

EARTH_M_PER_DEG = 111320.0


def _axis(**overrides) -> dict:
    """The shared axis style with per-chart overrides applied."""
    axis = {k: dict(v) if isinstance(v, dict) else v for k, v in AXIS.items()}
    axis.update(overrides)
    return axis


def _axis_title(text: str) -> dict:
    return dict(text=text, font=dict(size=9.5, color=MUTED))


def esc(value) -> str:
    return html.escape(str(value))


def num(value, fmt: str, dash: str = "--") -> str:
    if value is None:
        return dash
    try:
        if isinstance(value, float) and (value != value or value == float("inf")):
            return "∞" if value == float("inf") else dash
    except TypeError:
        return dash
    try:
        return format(value, fmt)
    except (TypeError, ValueError):
        return dash


def isna(value) -> bool:
    return value is None or (isinstance(value, float) and value != value) or pd.isna(value)


# ---------------------------------------------------------------------------
# Executive Status Bar (Topbar)
# ---------------------------------------------------------------------------


def topbar(
    trace: str,
    served_utc: str,
    wall_utc: str,
    epoch: int,
    total: int,
    playing: bool,
    attacking: bool,
    attack_label: str,
    source: str = "gps",
    state: str = "trusted",
    trust_score: Optional[float] = None,
) -> None:
    """Executive NOC Status Bar with primary time authority, integrity, and feed status."""
    src = (source or "gps").lower()
    src_badge_class = {
        "gps": "badge-emerald",
        "ntp": "badge-blue",
        "holdover": "badge-amber",
    }.get(src, "badge-rose")
    src_label = SOURCE_LABEL.get(src, src.upper())

    stt = (state or "trusted").lower()
    if attacking:
        threat_cls = "attack"
        threat_text = f"&#9888; SPOOFING ATTACK DETECTED &mdash; {esc(attack_label.upper())}"
    elif stt == "untrusted":
        threat_cls = "attack"
        threat_text = "&#9888; UNTRUSTED FEED &mdash; FAILOVER ACTIVE"
    elif stt == "suspect":
        threat_cls = "suspect"
        threat_text = "&#9888; SUSPECT ANOMALY &mdash; DEGRADED"
    elif stt == "recovering":
        threat_cls = "recovering"
        threat_text = "&#8634; RECOVERY VALIDATION &mdash; HOLDOVER"
    else:
        threat_cls = "nominal"
        threat_text = "&#10003; NOMINAL / VERIFIED"

    trust_val_str = (
        f"{trust_score:.3f}"
        if (trust_score is not None and not isna(trust_score))
        else "--"
    )

    live = (
        '<div class="live-pill on"><i class="dot"></i>LIVE FEED</div>'
        if playing
        else '<div class="live-pill off"><i class="dot"></i>FEED PAUSED</div>'
    )

    st.markdown(
        f"""
<div class="topbar">
  <div class="brand-group">
    <div class="brand">GPSTRUST</div>
    <div class="brand-badge">NOC CONSOLE</div>
  </div>
  <div class="sep"></div>
  <div class="tb">
    <div class="k">Active Authority</div>
    <div class="badge-pill {src_badge_class}"><span class="pill-dot"></span>{esc(src_label)}</div>
  </div>
  <div class="tb">
    <div class="k">Trust Score</div>
    <div class="v" style="color:{STATE_COLOUR.get(stt, TEXT)}">{trust_val_str}</div>
  </div>
  <div class="tb">
    <div class="k">Served Time (UTC)</div>
    <div class="v">{esc(served_utc)}</div>
  </div>
  <div class="tb">
    <div class="k">Console Clock</div>
    <div class="v">{esc(wall_utc)}</div>
  </div>
  <div class="sep"></div>
  <div class="tb">
    <div class="k">Receiver Stream</div>
    <div class="v" style="font-size:12px;color:var(--dim)">{esc(trace)}</div>
  </div>
  <div class="tb">
    <div class="k">Epoch</div>
    <div class="v">{epoch + 1} / {total}</div>
  </div>
  <div class="spacer"></div>
  <div class="threat-badge {threat_cls}">{threat_text}</div>
  {live}
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Status Cards (Tiles)
# ---------------------------------------------------------------------------


def tiles(now: pd.Series, holdover_s: float) -> None:
    """The eight core telemetry indicators answering whether served time is safe."""
    state = str(now.get("state", "trusted"))
    source = str(now.get("source", "gps"))
    state_colour = STATE_COLOUR.get(state, MUTED)
    source_colour = SOURCE_COLOUR.get(source, MUTED)

    unc = now.get("uncertainty_s")
    if isna(unc) or unc == float("inf"):
        unc_text, unc_unit = "unbounded", "no disciplined clock"
        unc_badge = '<span class="badge-pill badge-rose"><span class="pill-dot"></span>UNBOUNDED</span>'
    elif unc < 0.05:
        unc_text, unc_unit = f"{unc * 1000:.0f}", "ms (95%)"
        unc_badge = '<span class="badge-pill badge-emerald"><span class="pill-dot"></span>PRECISE</span>'
    elif unc < 1.0:
        unc_text, unc_unit = f"{unc * 1000:.0f}", "ms (95%)"
        unc_badge = '<span class="badge-pill badge-blue"><span class="pill-dot"></span>LOCKED</span>'
    else:
        unc_text, unc_unit = f"{unc:.2f}", "s (95%)"
        unc_badge = '<span class="badge-pill badge-amber"><span class="pill-dot"></span>COARSE</span>'

    served_err = now.get("served_error_s")
    if isna(served_err):
        err_text, err_unit, err_colour = "--", "no reference", MUTED
        err_badge = '<span class="badge-pill badge-slate"><span class="pill-dot"></span>UNSYNC</span>'
    else:
        err_text = f"{served_err * 1000:+.0f}" if abs(served_err) < 10 else f"{served_err:+.1f}"
        err_unit = "ms vs truth" if abs(served_err) < 10 else "s vs truth"
        if abs(served_err) < 0.5:
            err_colour = GREEN
            err_badge = '<span class="badge-pill badge-emerald"><span class="pill-dot"></span>IN-SPEC</span>'
        elif abs(served_err) < 5.0:
            err_colour = AMBER
            err_badge = '<span class="badge-pill badge-amber"><span class="pill-dot"></span>DRIFT</span>'
        else:
            err_colour = RED
            err_badge = '<span class="badge-pill badge-rose"><span class="pill-dot"></span>ALARM</span>'

    trust = now.get("trust")
    trust_val = float(trust) if not isna(trust) else 0.0
    if trust_val >= 0.90:
        trust_badge = '<span class="badge-pill badge-emerald"><span class="pill-dot"></span>NOMINAL</span>'
    elif trust_val >= 0.80:
        trust_badge = '<span class="badge-pill badge-amber"><span class="pill-dot"></span>SUSPECT</span>'
    else:
        trust_badge = '<span class="badge-pill badge-rose"><span class="pill-dot"></span>REJECTED</span>'

    dev = now.get("deviation_m")
    if isna(dev):
        dev_colour = MUTED
        dev_badge = '<span class="badge-pill badge-slate"><span class="pill-dot"></span>N/A</span>'
    elif dev < 50:
        dev_colour = GREEN
        dev_badge = '<span class="badge-pill badge-emerald"><span class="pill-dot"></span>ON-STATION</span>'
    elif dev < 500:
        dev_colour = AMBER
        dev_badge = '<span class="badge-pill badge-amber"><span class="pill-dot"></span>DRIFT</span>'
    else:
        dev_colour = RED
        dev_badge = '<span class="badge-pill badge-rose"><span class="pill-dot"></span>SPOOFED</span>'

    hdop = now.get("hdop")
    if isna(hdop):
        hdop_colour = MUTED
        hdop_badge = '<span class="badge-pill badge-slate"><span class="pill-dot"></span>NO FIX</span>'
    elif hdop <= 2.0:
        hdop_colour = GREEN
        hdop_badge = '<span class="badge-pill badge-emerald"><span class="pill-dot"></span>IDEAL</span>'
    elif hdop <= 5.0:
        hdop_colour = AMBER
        hdop_badge = '<span class="badge-pill badge-amber"><span class="pill-dot"></span>FAIR</span>'
    else:
        hdop_colour = RED
        hdop_badge = '<span class="badge-pill badge-rose"><span class="pill-dot"></span>POOR</span>'

    in_view = now.get("sats_in_view")
    used = now.get("sats_used")
    tracked = now.get("sats_tracked")
    tracked_val = int(tracked) if not isna(tracked) else 0
    if tracked_val >= 8:
        sat_badge = '<span class="badge-pill badge-emerald"><span class="pill-dot"></span>ROBUST</span>'
    elif tracked_val >= 4:
        sat_badge = '<span class="badge-pill badge-blue"><span class="pill-dot"></span>FIX OK</span>'
    else:
        sat_badge = '<span class="badge-pill badge-rose"><span class="pill-dot"></span>POOR</span>'

    fix = now.get("fix_quality")
    fix_names = {0: "no fix", 1: "GPS 3D", 2: "DGPS", 3: "PPS",
                 4: "RTK fixed", 5: "RTK float", 6: "estimated"}
    try:
        fix_int = int(fix)
        fix_text = fix_names.get(fix_int, f"mode {fix_int}")
    except (TypeError, ValueError):
        fix_text = str(fix) if not isna(fix) else "unknown"

    source_pill_cls = {
        "gps": "badge-emerald",
        "ntp": "badge-blue",
        "holdover": "badge-amber",
    }.get(source, "badge-rose")

    state_pill_cls = {
        "trusted": "badge-emerald",
        "suspect": "badge-amber",
        "untrusted": "badge-rose",
        "recovering": "badge-blue",
    }.get(state, "badge-slate")

    source_note = (
        f"Oscillator holdover: {holdover_s / 60:.1f} min"
        if source == "holdover" and holdover_s
        else ("Stratum-0 GNSS disciplined" if source == "gps" else "Stratum-2 network synchronization")
    )

    state_note = STATE_MEANING.get(state, "")
    hold = now.get("hold_remaining_s")
    if state == "recovering" and not isna(hold):
        state_note = f"Stability countdown: {float(hold):.0f}s"

    state_pill_text = (
        "VERIFIED" if state == "trusted"
        else ("DEGRADED" if state == "suspect"
              else ("RECOVERING" if state == "recovering" else "REJECTED"))
    )

    cards_html = [
        # 1. Time Authority
        f'<div class="tile" style="--accent:{source_colour}">'
        f'<div class="k">Time Authority</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<span class="v" style="color:{source_colour};font-size:16px">{esc(source.upper())}</span>'
        f'<span class="badge-pill {source_pill_cls}"><span class="pill-dot"></span>{esc(SOURCE_LABEL.get(source, source.upper()))}</span></div>'
        f'<div class="n">{esc(source_note)}</div></div>',

        # 2. GNSS Integrity State
        f'<div class="tile" style="--accent:{state_colour}">'
        f'<div class="k">GNSS State</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<span class="v" style="color:{state_colour};font-size:16px">{esc(state.upper())}</span>'
        f'<span class="badge-pill {state_pill_cls}"><span class="pill-dot"></span>{esc(state_pill_text)}</span></div>'
        f'<div class="n">{esc(state_note)}</div></div>',

        # 3. Composite Trust Score
        f'<div class="tile" style="--accent:{state_colour}">'
        f'<div class="k">Composite Trust</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<span class="v" style="color:{state_colour}">{num(trust, ".3f")}</span>'
        f'{trust_badge}</div>'
        f'<div class="n">Multi-detector Bayesian fusion</div></div>',

        # 4. Served Time Error
        f'<div class="tile" style="--accent:{err_colour}">'
        f'<div class="k">Served Time Error</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<div><span class="v" style="color:{err_colour}">{err_text}</span> <span class="u">{err_unit}</span></div>'
        f'{err_badge}</div>'
        f'<div class="n">Delivered downstream offset</div></div>',

        # 5. Time Uncertainty
        f'<div class="tile" style="--accent:{CYAN}">'
        f'<div class="k">Time Uncertainty</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<div><span class="v" style="color:var(--text)">{unc_text}</span> <span class="u">{unc_unit}</span></div>'
        f'{unc_badge}</div>'
        f'<div class="n">Disciplined bound (95% CI)</div></div>',

        # 6. Station Deviation
        f'<div class="tile" style="--accent:{dev_colour}">'
        f'<div class="k">Station Deviation</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<div><span class="v" style="color:{dev_colour}">{num(dev, ".0f")}</span> <span class="u">m</span></div>'
        f'{dev_badge}</div>'
        f'<div class="n">From surveyed benchmark</div></div>',

        # 7. Constellation Satellites
        f'<div class="tile" style="--accent:{CYAN}">'
        f'<div class="k">Constellation</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<div><span class="v" style="color:var(--text)">{num(used, ".0f")}/{num(in_view, ".0f")}</span> <span class="u">used/view</span></div>'
        f'{sat_badge}</div>'
        f'<div class="n">{num(tracked, ".0f")} tracked in solution</div></div>',

        # 8. Geometry & Fix
        f'<div class="tile" style="--accent:{hdop_colour}">'
        f'<div class="k">Geometry & Fix</div>'
        f'<div class="v-box" style="display:flex;align-items:center;justify-content:space-between">'
        f'<div><span class="v" style="color:{hdop_colour}">HDOP {num(hdop, ".2f")}</span></div>'
        f'{hdop_badge}</div>'
        f'<div class="n">Fix mode: {fix_text}</div></div>',
    ]

    st.markdown(f'<div class="tiles">{"".join(cards_html)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Maps & Plan Views
# ---------------------------------------------------------------------------


def _geo_style(projection: str) -> dict:
    return dict(
        projection_type=projection,
        showland=True, landcolor="#111827",
        showocean=True, oceancolor="#0b0f19",
        showcoastlines=True, coastlinecolor="#334155", coastlinewidth=0.8,
        showcountries=True, countrycolor="#1e293b", countrywidth=0.6,
        showlakes=True, lakecolor="#0b0f19",
        showrivers=False,
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
        lonaxis=dict(showgrid=True, gridcolor="#1e293b", gridwidth=0.5, dtick=15),
        lataxis=dict(showgrid=True, gridcolor="#1e293b", gridwidth=0.5, dtick=15),
    )


def world_map(
    frame: pd.DataFrame,
    cursor: int,
    reference: tuple[Optional[float], Optional[float]],
    mode: str,
    height: int = 430,
) -> go.Figure:
    """Geographic display of the reported receiver position vs surveyed station benchmark."""
    view = frame.iloc[: cursor + 1]
    track = view.dropna(subset=["lat", "lon"])
    now = frame.iloc[cursor]
    ref_lat, ref_lon = reference

    fig = go.Figure()

    if not track.empty:
        clean = track[~track["attacked"]]
        spoofed = track[track["attacked"]]

        if len(clean) > 1:
            fig.add_trace(go.Scattergeo(
                lat=clean["lat"], lon=clean["lon"], mode="lines",
                line=dict(width=1.6, color=CYAN), opacity=0.65,
                name="track (clean)", hoverinfo="skip",
            ))
        if len(spoofed) > 1:
            fig.add_trace(go.Scattergeo(
                lat=spoofed["lat"], lon=spoofed["lon"], mode="lines",
                line=dict(width=2.2, color=RED), opacity=0.85,
                name="track (injected)", hoverinfo="skip",
            ))

    if ref_lat is not None and ref_lon is not None:
        fig.add_trace(go.Scattergeo(
            lat=[ref_lat], lon=[ref_lon], mode="markers",
            marker=dict(size=12, color=VIOLET, symbol="x-thin",
                        line=dict(width=2.2, color=VIOLET)),
            name="surveyed reference",
            hovertemplate=f"surveyed reference<br>{ref_lat:.5f}, {ref_lon:.5f}<extra></extra>",
        ))

    lat, lon = now["lat"], now["lon"]
    if not isna(lat) and not isna(lon):
        colour = STATE_COLOUR.get(str(now["state"]), MUTED)

        if ref_lat is not None and not isna(now["deviation_m"]) and now["deviation_m"] > 30:
            fig.add_trace(go.Scattergeo(
                lat=[ref_lat, lat], lon=[ref_lon, lon], mode="lines",
                line=dict(width=1.3, color=RED, dash="dot"),
                name="displacement", hoverinfo="skip",
            ))

        fig.add_trace(go.Scattergeo(
            lat=[lat], lon=[lon], mode="markers",
            marker=dict(size=26, color=colour, opacity=0.2),
            hoverinfo="skip", showlegend=False,
        ))
        fig.add_trace(go.Scattergeo(
            lat=[lat], lon=[lon], mode="markers",
            marker=dict(size=12, color=colour, line=dict(width=2, color="#0b0f19")),
            name="reported position",
            hovertemplate=(
                f"reported position<br>{lat:.6f}, {lon:.6f}"
                f"<br>state: {now['state']}<extra></extra>"
            ),
        ))

    geo = _geo_style("orthographic" if mode == "globe" else "equirectangular")

    if mode == "globe":
        geo["projection_rotation"] = dict(
            lon=float(lon) if not isna(lon) else 0.0,
            lat=float(lat) if not isna(lat) else 0.0,
            roll=0,
        )
        geo["projection_scale"] = 1.0
    elif mode == "region":
        if not isna(lat):
            geo["lataxis"]["range"] = [float(lat) - 9, float(lat) + 9]
            geo["lonaxis"]["range"] = [float(lon) - 14, float(lon) + 14]
        geo["lonaxis"]["dtick"] = 5
        geo["lataxis"]["dtick"] = 5
    else:  # local focus
        lats = [float(v) for v in list(track["lat"]) + [ref_lat] if not isna(v) and math.isfinite(float(v))]
        lons = [float(v) for v in list(track["lon"]) + [ref_lon] if not isna(v) and math.isfinite(float(v))]
        if lats and lons:
            pad = max(0.012, (max(lats) - min(lats)) * 0.45, (max(lons) - min(lons)) * 0.25)
            geo["lataxis"]["range"] = [min(lats) - pad, max(lats) + pad]
            geo["lonaxis"]["range"] = [min(lons) - pad * 1.6, max(lons) + pad * 1.6]
        else:
            geo["lataxis"]["range"] = [-90, 90]
            geo["lonaxis"]["range"] = [-180, 180]
        geo["lonaxis"]["dtick"] = 0.05
        geo["lataxis"]["dtick"] = 0.05
        geo["showcountries"] = True
        geo["resolution"] = 50

    fig.update_layout(
        **PLOT_LAYOUT,
        geo=geo,
        height=height,
        showlegend=False,
        dragmode=False,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return fig


def plan_view(
    frame: pd.DataFrame,
    cursor: int,
    reference: tuple[Optional[float], Optional[float]],
    height: int = 430,
) -> Optional[go.Figure]:
    """Cartesian metric plan view showing displacement from surveyed benchmark in metres."""
    ref_lat, ref_lon = reference
    if isna(ref_lat) or isna(ref_lon):
        return None

    try:
        ref_lat = float(ref_lat)
        ref_lon = float(ref_lon)
        if not math.isfinite(ref_lat) or not math.isfinite(ref_lon):
            return None
    except (TypeError, ValueError):
        return None

    view = frame.iloc[: cursor + 1].dropna(subset=["lat", "lon"])
    if view.empty:
        return None

    scale_lon = EARTH_M_PER_DEG * math.cos(math.radians(ref_lat))
    east = (view["lon"] - ref_lon) * scale_lon
    north = (view["lat"] - ref_lat) * EARTH_M_PER_DEG

    max_dist = max(east.abs().max(), north.abs().max())
    if isna(max_dist) or not math.isfinite(max_dist):
        max_dist = 60.0
    reach = max(60.0, min(10_000_000.0, float(max_dist) * 1.25))

    fig = go.Figure()

    step = 10 ** math.floor(math.log10(reach / 2.2))
    for mult in (1, 2, 5, 10):
        if reach / (step * mult) <= 4:
            step = step * mult
            break
    ring = step
    ring_count = 0
    while ring <= reach and ring_count < 25:
        angle = [i * math.pi / 60 for i in range(121)]
        fig.add_trace(go.Scatter(
            x=[ring * math.sin(a) for a in angle],
            y=[ring * math.cos(a) for a in angle],
            mode="lines", line=dict(width=0.7, color="#1e293b"),
            hoverinfo="skip", showlegend=False,
        ))
        label = f"{ring:.0f} m" if ring < 1000 else f"{ring / 1000:.1f} km"
        fig.add_annotation(x=0, y=ring, text=label, showarrow=False,
                           font=dict(size=8.5, color=MUTED, family=PLOT_LAYOUT["font"]["family"]),
                           yshift=7)
        ring += step
        ring_count += 1

    for angle_deg, label in ((0, "N"), (90, "E"), (180, "S"), (270, "W")):
        a = math.radians(angle_deg)
        fig.add_trace(go.Scatter(
            x=[0, reach * math.sin(a)], y=[0, reach * math.cos(a)],
            mode="lines", line=dict(width=0.7, color="#2d3748"),
            hoverinfo="skip", showlegend=False,
        ))
        fig.add_annotation(x=reach * 0.97 * math.sin(a), y=reach * 0.97 * math.cos(a),
                           text=label, showarrow=False,
                           font=dict(size=10, color=DIM, family=PLOT_LAYOUT["font"]["family"]))

    attacked = view["attacked"].to_numpy()
    fig.add_trace(go.Scatter(
        x=east[~attacked], y=north[~attacked], mode="markers",
        marker=dict(size=4.5, color=CYAN, opacity=0.55),
        name="clean fixes",
        hovertemplate="%{x:.0f} m E, %{y:.0f} m N<extra>clean</extra>",
    ))
    if attacked.any():
        fig.add_trace(go.Scatter(
            x=east[attacked], y=north[attacked], mode="markers",
            marker=dict(size=5.5, color=RED, opacity=0.75),
            name="injected fixes",
            hovertemplate="%{x:.0f} m E, %{y:.0f} m N<extra>injected</extra>",
        ))

    now = frame.iloc[cursor]
    if not isna(now["lat"]):
        cx = (now["lon"] - ref_lon) * scale_lon
        cy = (now["lat"] - ref_lat) * EARTH_M_PER_DEG
        colour = STATE_COLOUR.get(str(now["state"]), MUTED)
        fig.add_trace(go.Scatter(
            x=[0, cx], y=[0, cy], mode="lines",
            line=dict(width=1.3, color=colour, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy], mode="markers",
            marker=dict(size=14, color=colour, line=dict(width=2, color="#0b0f19")),
            name="current fix",
            hovertemplate="%{x:.0f} m E, %{y:.0f} m N<extra>current fix</extra>",
        ))

    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=dict(size=11, color=VIOLET, symbol="x-thin",
                    line=dict(width=2.2, color=VIOLET)),
        name="surveyed reference",
        hovertemplate="surveyed reference<extra></extra>",
    ))

    fig.update_layout(
        **PLOT_LAYOUT, height=height, showlegend=False,
        xaxis=_axis(range=[-reach, reach], visible=False,
                    scaleanchor="y", scaleratio=1),
        yaxis=_axis(range=[-reach, reach], visible=False),
    )
    fig.update_layout(margin=dict(l=4, r=4, t=4, b=4))
    return fig


# ---------------------------------------------------------------------------
# Sky View & Satellites
# ---------------------------------------------------------------------------


def skyplot(satellites: Sequence, height: int = 360) -> go.Figure:
    """Polar projection of visible satellites across azimuth and elevation."""
    fig = go.Figure()

    # Elevation mask at 10 degrees
    theta = list(range(0, 361, 3))
    fig.add_trace(go.Scatterpolar(
        r=[80] * len(theta), theta=theta, mode="lines",
        line=dict(width=0.8, color=AMBER, dash="dot"), opacity=0.4,
        hoverinfo="skip", showlegend=False,
    ))

    plotted = [s for s in satellites if s.has_sky_position]
    tracked = [s for s in plotted if s.tracked]
    idle = [s for s in plotted if not s.tracked]

    if idle:
        fig.add_trace(go.Scatterpolar(
            r=[90 - s.elevation_deg for s in idle],
            theta=[s.azimuth_deg for s in idle],
            mode="markers+text",
            marker=dict(size=17, color="rgba(0,0,0,0)",
                        line=dict(width=1.2, color=MUTED)),
            text=[s.prn for s in idle],
            textfont=dict(size=7.5, color=MUTED),
            textposition="middle center",
            hovertemplate=(
                "PRN %{text}<br>elevation %{customdata[0]}°"
                "<br>azimuth %{theta}°<br>not tracked<extra>%{customdata[1]}</extra>"
            ),
            customdata=[[s.elevation_deg, constellation(s.talker, s.prn)[0]] for s in idle],
            showlegend=False,
        ))

    if tracked:
        fig.add_trace(go.Scatterpolar(
            r=[90 - s.elevation_deg for s in tracked],
            theta=[s.azimuth_deg for s in tracked],
            mode="markers+text",
            marker=dict(
                size=19,
                color=[s.snr for s in tracked],
                colorscale=SNR_SCALE, cmin=10, cmax=50,
                line=dict(width=1, color="#0b0f19"),
                colorbar=dict(
                    title=dict(text="dB-Hz", font=dict(size=9.5, color=MUTED)),
                    thickness=8, len=0.65, x=1.02,
                    tickfont=dict(size=8.5, color=MUTED),
                    outlinewidth=0,
                ),
            ),
            text=[s.prn for s in tracked],
            textfont=dict(size=7.5, color="#0b0f19"),
            textposition="middle center",
            hovertemplate=(
                "PRN %{text}<br>elevation %{customdata[0]}°"
                "<br>azimuth %{theta}°<br>%{customdata[1]} dB-Hz"
                "<extra>%{customdata[2]}</extra>"
            ),
            customdata=[
                [s.elevation_deg, s.snr, constellation(s.talker, s.prn)[0]] for s in tracked
            ],
            showlegend=False,
        ))

    fig.update_layout(
        **PLOT_LAYOUT,
        height=height,
        polar=dict(
            bgcolor="rgba(17, 24, 39, 0.7)",
            radialaxis=dict(
                range=[0, 90], tickvals=[0, 30, 60, 90],
                ticktext=["90°", "60°", "30°", "0°"],
                angle=90, tickangle=90,
                gridcolor=GRID, linecolor=BORDER,
                tickfont=dict(size=8, color=MUTED),
            ),
            angularaxis=dict(
                direction="clockwise", rotation=90,
                tickmode="array",
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                gridcolor=GRID, linecolor=BORDER,
                tickfont=dict(size=9, color=DIM),
            ),
        ),
    )
    fig.update_layout(margin=dict(l=24, r=36, t=16, b=16))
    return fig


def snr_bars(satellites: Sequence, height: int = 220) -> Optional[go.Figure]:
    """Carrier-to-noise ratio per satellite sorted by constellation."""
    sats = sorted(
        satellites,
        key=lambda s: (constellation(s.talker, s.prn)[0], s.prn),
    )
    if not sats:
        return None

    labels = [s.prn for s in sats]
    values = [float(s.snr) if (s.tracked and not isna(s.snr)) else 0.0 for s in sats]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=values,
        marker=dict(
            color=values,
            colorscale=SNR_SCALE, cmin=10, cmax=50,
            line=dict(width=0),
        ),
        customdata=[[constellation(s.talker, s.prn)[0],
                     "tracked" if s.tracked else "in view, not tracked"] for s in sats],
        hovertemplate="PRN %{x}<br>%{y} dB-Hz<br>%{customdata[1]}<extra>%{customdata[0]}</extra>",
        showlegend=False,
    ))

    fig.update_layout(
        **PLOT_LAYOUT, height=height, bargap=0.28,
        xaxis=_axis(title=_axis_title("PRN"), type="category",
                    tickfont=dict(size=8.5, color=MUTED)),
        yaxis=_axis(title=_axis_title("C/N0 (dB-Hz)"), range=[0, 55]),
    )
    fig.update_layout(margin=dict(l=36, r=8, t=6, b=28))
    return fig


def constellation_chips(satellites: Sequence) -> None:
    counts: dict[str, list] = {}
    for s in satellites:
        name, colour = constellation(s.talker, s.prn)
        entry = counts.setdefault(name, [0, 0, colour])
        entry[0] += 1
        if s.tracked:
            entry[1] += 1

    if not counts:
        st.markdown('<div class="empty">No satellite telemetry available in this epoch.</div>',
                    unsafe_allow_html=True)
        return

    chips = "".join(
        f'<span class="chip"><i style="background:{colour}"></i>'
        f'{esc(name)} <b>{tracked}/{total}</b></span>'
        for name, (total, tracked, colour) in sorted(counts.items())
    )
    st.markdown(
        f'<div class="chips">{chips}'
        f'<span class="chip" style="color:{MUTED}">tracked / in view</span></div>',
        unsafe_allow_html=True,
    )


def satellite_table(satellites: Sequence) -> pd.DataFrame:
    rows = []
    for s in satellites:
        name, _ = constellation(s.talker, s.prn)
        rows.append({
            "PRN": s.prn,
            "Constellation": name,
            "Elevation": s.elevation_deg,
            "Azimuth": s.azimuth_deg,
            "Bearing": compass(s.azimuth_deg) if s.azimuth_deg is not None else None,
            "C/N0 (dB-Hz)": s.snr,
            "Status": "tracked" if s.tracked else "in view",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Grouped Functional Domain Detector Rail
# ---------------------------------------------------------------------------

DETECTOR_META = {
    "time_offset": {
        "name": "Network Reference Offset",
        "domain": "time",
        "domain_title": "Time Domain Integrity",
        "domain_icon": "⏱️",
        "desc": "Cross-check against independent NTP stratum reference",
    },
    "position_deviation": {
        "name": "Antenna Station Deviation",
        "domain": "spatial",
        "domain_title": "Spatial & Kinematic Plausibility",
        "domain_icon": "📍",
        "desc": "Radial drift from surveyed stationary benchmark",
    },
    "velocity_consistency": {
        "name": "Velocity Consistency",
        "domain": "spatial",
        "domain_title": "Spatial & Kinematic Plausibility",
        "domain_icon": "📍",
        "desc": "Kinematic speed delta vs coordinate displacement",
    },
    "trajectory": {
        "name": "Trajectory Plausibility",
        "domain": "spatial",
        "domain_title": "Spatial & Kinematic Plausibility",
        "domain_icon": "📍",
        "desc": "Turn rates and unphysical acceleration jumps",
    },
    "snr_uniformity": {
        "name": "Multi-Satellite SNR Uniformity",
        "domain": "rf",
        "domain_title": "RF & Constellation Physics",
        "domain_icon": "📡",
        "desc": "Carrier-to-noise distribution across visible sky",
    },
    "snr_power": {
        "name": "RF Overpower Anomaly",
        "domain": "rf",
        "domain_title": "RF & Constellation Physics",
        "domain_icon": "📡",
        "desc": "Signal power exceeding 99th percentile baseline",
    },
    "satellite_count": {
        "name": "Satellite Count Anomaly",
        "domain": "rf",
        "domain_title": "RF & Constellation Physics",
        "domain_icon": "📡",
        "desc": "Tracked satellite count vs baseline distribution",
    },
    "dilution": {
        "name": "Dilution of Precision",
        "domain": "rf",
        "domain_title": "RF & Constellation Physics",
        "domain_icon": "📡",
        "desc": "Geometric constellation dispersion",
    },
    "hdop": {
        "name": "Dilution of Precision",
        "domain": "rf",
        "domain_title": "RF & Constellation Physics",
        "domain_icon": "📡",
        "desc": "Geometric constellation dispersion",
    },
}

DOMAIN_SECTIONS = [
    ("time", "⏱️ Time Domain Integrity", "Independent reference clocks and phase alignment"),
    ("spatial", "📍 Spatial & Kinematic Plausibility", "Stationary antenna anchor and motion consistency"),
    ("rf", "📡 RF & Constellation Physics", "Signal levels, constellation geometry, and RF power"),
]


def detector_rail(evidence: Sequence[dict], rationale: dict) -> None:
    """Grouped detector rail organized across 3 functional domains."""
    if not evidence:
        st.markdown('<div class="empty">No detector evidence available for this epoch.</div>',
                    unsafe_allow_html=True)
        return

    # Categorize items into domains
    domain_groups: dict[str, list[dict]] = {"time": [], "spatial": [], "rf": []}
    for item in evidence:
        det_key = item.get("detector", "")
        meta = DETECTOR_META.get(det_key)
        if meta:
            domain_groups[meta["domain"]].append(item)
        else:
            # Fallback grouping
            if "time" in det_key or "clock" in det_key:
                domain_groups["time"].append(item)
            elif any(k in det_key for k in ("pos", "vel", "traj", "motion")):
                domain_groups["spatial"].append(item)
            else:
                domain_groups["rf"].append(item)

    cols_html = []
    for domain_key, domain_title, domain_desc in DOMAIN_SECTIONS:
        items = domain_groups.get(domain_key, [])
        cards = []
        for item in sorted(
            items,
            key=lambda e: (
                not e.get("applicable", False),
                -(float(e.get("score", 0.0)) if not isna(e.get("score")) else 0.0),
            ),
        ):
            key = item.get("detector", "")
            meta = DETECTOR_META.get(key, {})
            friendly_name = meta.get("name", key.replace("_", " ").title())
            raw_score = item.get("score")
            score = float(raw_score) if not isna(raw_score) else 0.0
            applicable = bool(item.get("applicable", False)) and not isna(raw_score)

            if not applicable:
                colour = MUTED
                width = 0
                verdict_html = '<b style="background:rgba(100,116,139,0.15);color:var(--muted)">N/A</b>'
            elif score <= 0:
                colour = GREEN
                width = 4
                verdict_html = f'<b style="background:rgba(16,185,129,0.15);color:{GREEN}">CLEAR</b>'
            elif score < 0.5:
                colour = AMBER
                width = min(100, max(4, int(score * 100)))
                verdict_html = f'<b style="background:rgba(245,158,11,0.15);color:{AMBER}">SUSPECT {score:.2f}</b>'
            else:
                colour = RED
                width = min(100, max(4, int(min(score, 1.0) * 100)))
                verdict_html = f'<b style="background:rgba(244,63,94,0.15);color:{RED}">ALARM {score:.2f}</b>'

            reason = item.get("reason") or rationale.get(key, "") or meta.get("desc", "")

            cards.append(
                f'<div class="det{"" if applicable else " off"}">'
                f'<div class="n"><span>{esc(friendly_name)}</span>{verdict_html}</div>'
                f'<div class="bar"><i style="width:{max(width, 3)}%;background:{colour}"></i></div>'
                f'<div class="r">{esc(reason)}</div></div>'
            )

        if not cards:
            cards.append('<div class="empty">No active checks configured in domain.</div>')

        cols_html.append(
            f'<div class="domain-col">'
            f'<div class="domain-head"><span class="title">{domain_title}</span>'
            f'<span style="font-size:10px;color:var(--muted)">{len(items)} checks</span></div>'
            f'<div class="domain-cards">{"".join(cards)}</div>'
            f'</div>'
        )

    st.markdown(f'<div class="rail-domains">{"".join(cols_html)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Timeline Charts
# ---------------------------------------------------------------------------


def _attack_bands(view: pd.DataFrame) -> list[tuple[int, int]]:
    """Contiguous runs of injected epochs, for shading."""
    if "attacked" not in view.columns or "epoch" not in view.columns or view.empty:
        return []
    bands, start = [], None
    for _, row in view.iterrows():
        is_attacked = bool(row["attacked"]) if not isna(row["attacked"]) else False
        if is_attacked and start is None:
            start = int(row["epoch"])
        elif not is_attacked and start is not None:
            bands.append((start, int(row["epoch"])))
            start = None
    if start is not None:
        bands.append((start, int(view["epoch"].iloc[-1])))
    return bands


def timeline(
    view: pd.DataFrame,
    total: int,
    cursor: int,
    series: list[dict],
    unit: str = "",
    height: int = 200,
    thresholds: Optional[list[dict]] = None,
    log_y: bool = False,
    y_range: Optional[list[float]] = None,
) -> Optional[go.Figure]:
    """Shared time-series layout with injection shading, thresholds, and cursor."""
    if all(s["column"] not in view.columns or view[s["column"]].dropna().empty for s in series):
        return None

    fig = go.Figure()

    for start, end in _attack_bands(view):
        fig.add_vrect(x0=start, x1=end, fillcolor=RED, opacity=0.10,
                      layer="below", line_width=0)

    for spec in series:
        column = spec["column"]
        if column not in view.columns or view[column].dropna().empty:
            continue
        fig.add_trace(go.Scatter(
            x=view["epoch"], y=view[column], mode="lines",
            name=spec.get("name", column),
            line=dict(width=spec.get("width", 1.8), color=spec.get("colour", CYAN),
                      dash=spec.get("dash")),
            fill=spec.get("fill"),
            fillcolor=spec.get("fillcolor"),
            hovertemplate=f"epoch %{{x}}<br>{spec.get('name', column)}: %{{y:.4g}} {unit}<extra></extra>",
        ))

    for line in thresholds or []:
        fig.add_hline(
            y=line["y"], line_dash="dot", line_width=1, line_color=line.get("colour", AMBER),
            annotation_text=line.get("label", ""),
            annotation_position="top left",
            annotation_font=dict(size=9.5, color=line.get("colour", AMBER),
                                family=PLOT_LAYOUT["font"]["family"]),
        )

    fig.add_vline(x=cursor, line_width=1.3, line_color=CYAN, opacity=0.6)

    fig.update_layout(
        **PLOT_LAYOUT, height=height,
        showlegend=len([s for s in series if s["column"] in view.columns and not view[s["column"]].dropna().empty]) > 1,
        legend=dict(orientation="h", y=1.18, x=0, font=dict(size=9.5, color=MUTED),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=_axis(range=[0, max(total - 1, 1)], title=_axis_title("epoch")),
        yaxis=_axis(title=_axis_title(unit),
                    type="log" if log_y else "linear", range=y_range),
    )
    fig.update_layout(margin=dict(l=44, r=10, t=22, b=26))
    return fig


def chart_block(title: str, hint: str, fig: Optional[go.Figure], key: str) -> None:
    """A chart block accompanied by a concise operational subtitle."""
    st.markdown(f'<div class="ct">{esc(title)}</div>', unsafe_allow_html=True)
    if fig is None:
        st.markdown(
            '<div class="empty">Telemetry stream not present in capture for this metric.</div>',
            unsafe_allow_html=True,
        )
        return
    st.plotly_chart(fig, width="stretch", key=key,
                    config={"displayModeBar": False})
    if hint:
        st.markdown(f'<div class="hint">{hint}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Operational Logs
# ---------------------------------------------------------------------------


def event_log(events: list[dict], cursor: int) -> None:
    rows = [e for e in events if e.get("epoch", 0) <= cursor]
    if not rows:
        st.markdown(
            '<div class="empty">No source switches recorded. Primary GPS authority '
            'has remained accepted across all epochs.</div>',
            unsafe_allow_html=True,
        )
        return

    out = []
    for e in reversed(rows[-60:]):
        colour = SOURCE_COLOUR.get(e.get("to", ""), MUTED)
        step_val = e.get("step_s")
        step = "" if (step_val is None or isna(step_val)) else f' <b style="color:{AMBER}">step {float(step_val):+.3f}s</b>'
        out.append(
            f'<div class="row" style="--accent:{colour}">'
            f'<span class="e">{int(e.get("epoch", 0)):04d}</span>'
            f'<span class="w">{esc(e.get("from", "--"))} &rarr; {esc(e.get("to", "--"))}</span>'
            f'<span class="m">{esc(e.get("reason", ""))}{step}</span></div>'
        )
    st.markdown(f'<div class="log">{"".join(out)}</div>', unsafe_allow_html=True)


def detection_log(detections: pd.DataFrame, cursor: int) -> None:
    if detections.empty or "epoch" not in detections.columns:
        st.markdown('<div class="empty">No anomaly detection events triggered.</div>',
                    unsafe_allow_html=True)
        return
    rows = detections[detections["epoch"] <= cursor]
    if rows.empty:
        st.markdown('<div class="empty">No anomaly detection events triggered yet.</div>',
                    unsafe_allow_html=True)
        return

    out = []
    for _, r in rows.tail(80).iloc[::-1].iterrows():
        raw_score = r.get("score")
        score = float(raw_score) if not isna(raw_score) else 0.0
        colour = RED if score >= 0.5 else AMBER
        det_name = str(r.get("detector", ""))
        meta = DETECTOR_META.get(det_name, {})
        friendly = meta.get("name", det_name.replace("_", " ").title())
        out.append(
            f'<div class="row" style="--accent:{colour}">'
            f'<span class="e">{int(r["epoch"]):04d}</span>'
            f'<span class="w">{esc(friendly)}</span>'
            f'<span class="m">{esc(r.get("reason", ""))} '
            f'<b style="color:{colour}">score {score:.2f}</b></span></div>'
        )
    st.markdown(f'<div class="log">{"".join(out)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Section Headers and Key-Value Strip
# ---------------------------------------------------------------------------


def panel_open(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="panel-h"><span class="t">{esc(title)}</span>'
        f'<span class="s">{esc(subtitle)}</span></div>',
        unsafe_allow_html=True,
    )


def kv_strip(items: list[tuple[str, str]]) -> None:
    body = "".join(
        f'<div class="i"><div class="k">{esc(k)}</div><div class="v">{v}</div></div>'
        for k, v in items
    )
    st.markdown(f'<div class="kv">{body}</div>', unsafe_allow_html=True)
