"""Enterprise theme, color palette, and stylesheet for the monitoring console.

Designed to reflect a high-reliability aerospace/telecom NOC monitoring console.
Colour carries state and operational meaning:
- Emerald (#10b981): Nominal, verified GPS / GNSS stratum-0 authority
- Blue (#3b82f6): NTP network peer reference or recovery validation
- Amber (#f59e0b): Holdover operation, anomaly warning, or degraded telemetry
- Rose Red (#f43f5e): Active spoofing attack detected, untrusted feed, failover rejected
- Sky Cyan (#0ea5e9): RF & constellation telemetry instrumentation
"""

from __future__ import annotations

# -- Enterprise Dark-Slate Palette --------------------------------------------

BG = "#0b0f19"         # Slate 950: deep, low-fatigue background
PANEL = "#111827"      # Slate 900: structural panels
PANEL_HI = "#1e293b"   # Slate 800: elevated cards and interactive elements
BORDER = "#2d3748"     # Crisp divider border
GRID = "#1e293b"       # Subtle chart gridlines

TEXT = "#f1f5f9"       # Slate 100: primary readouts and headings
DIM = "#94a3b8"        # Slate 400: secondary text and labels
MUTED = "#64748b"      # Slate 500: timestamps, captions, units

# State and authority colors
CYAN = "#0ea5e9"       # Sky 500: telemetry / instrumentation
GREEN = "#10b981"      # Emerald 500: nominal / verified GPS
AMBER = "#f59e0b"      # Amber 500: suspect anomaly / holdover
RED = "#f43f5e"        # Rose 500: spoofing attack / untrusted
BLUE = "#3b82f6"       # Blue 500: NTP network peer / recovery
VIOLET = "#8b5cf6"     # Violet 500: surveyed benchmark reference
MAGENTA = "#ec4899"    # Pink 500: secondary highlight

#: Trust state -> colour.
STATE_COLOUR = {
    "trusted": GREEN,
    "suspect": AMBER,
    "untrusted": RED,
    "recovering": BLUE,
    "unknown": MUTED,
}

#: Plain-language description for operational status.
STATE_MEANING = {
    "trusted": "GPS accepted as disciplined time authority",
    "suspect": "Anomalous telemetry, serving with caution",
    "untrusted": "GPS rejected; active failover engaged",
    "recovering": "Validation phase; awaiting stability holdover",
    "unknown": "Insufficient telemetry evidence",
}

#: Active time source -> colour.
SOURCE_COLOUR = {
    "gps": GREEN,
    "ntp": BLUE,
    "holdover": AMBER,
    "none": RED,
}

#: Professional NOC source labels.
SOURCE_LABEL = {
    "gps": "GNSS STRATUM-0",
    "ntp": "NTP NETWORK PEER",
    "holdover": "LOCAL HOLDOVER",
    "none": "NO SYNC SOURCE",
}

#: Colour ramp for satellite carrier-to-noise density (C/N0, dB-Hz).
SNR_SCALE = [
    [0.00, "#1e293b"],
    [0.35, BLUE],
    [0.65, CYAN],
    [1.00, GREEN],
]

# Typography
SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
MONO = 'ui-monospace, "Cascadia Code", "Roboto Mono", Consolas, monospace'

# Plotly layout and axis configurations
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        family=SANS,
        size=11,
        color=DIM,
    ),
    margin=dict(l=8, r=8, t=8, b=8),
    hoverlabel=dict(
        bgcolor=PANEL_HI,
        bordercolor=BORDER,
        font=dict(
            family=MONO,
            size=11,
            color=TEXT,
        ),
    ),
)

AXIS = dict(
    gridcolor=GRID,
    zerolinecolor=GRID,
    linecolor=BORDER,
    tickfont=dict(size=10, color=MUTED, family=MONO),
    title=dict(font=dict(size=10, color=DIM, family=SANS)),
)


def css() -> str:
    """The modern enterprise NOC console stylesheet."""
    return f"""
<style>
:root {{
  --bg: {BG};
  --panel: {PANEL};
  --panel-hi: {PANEL_HI};
  --border: {BORDER};
  --text: {TEXT};
  --dim: {DIM};
  --muted: {MUTED};
  --cyan: {CYAN};
  --green: {GREEN};
  --amber: {AMBER};
  --red: {RED};
  --blue: {BLUE};
  --violet: {VIOLET};
  --sans: {SANS};
  --mono: {MONO};
}}

/* ---- Base Shell & Typography ---- */
.stApp {{
  background:
    radial-gradient(1200px 700px at 25% -10%, #162033 0%, transparent 65%),
    radial-gradient(900px 500px at 100% 0%, #131c2d 0%, transparent 55%),
    var(--bg);
  color: var(--text);
  font-family: var(--sans);
}}

.block-container {{
  padding: 0.75rem 1.25rem 2.5rem 1.25rem !important;
  max-width: 100% !important;
}}

header[data-testid="stHeader"] {{
  background: transparent;
  height: 0;
}}

#MainMenu, footer {{
  visibility: hidden;
}}

html, body, [class*="css"], .stApp {{
  font-family: var(--sans);
}}

code, kbd, samp, pre, .mono {{
  font-family: var(--mono) !important;
  font-variant-numeric: tabular-nums;
}}

/* ---- Enterprise Sidebar ---- */
section[data-testid="stSidebar"] {{
  background: #0d131f;
  border-right: 1px solid var(--border);
  width: 330px !important;
}}

section[data-testid="stSidebar"] .block-container {{
  padding-top: 0.75rem !important;
}}

section[data-testid="stSidebar"] * {{
  font-family: var(--sans);
}}

section[data-testid="stSidebar"] label {{
  font-size: 11px !important;
  font-weight: 500 !important;
  letter-spacing: .02em;
  color: var(--dim) !important;
  text-transform: uppercase;
}}

.grp {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 18px 0 8px 0;
  color: var(--dim);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .06em;
  text-transform: uppercase;
}}

.grp:before {{
  content: "";
  width: 3px;
  height: 12px;
  background: var(--blue);
  border-radius: 2px;
}}

.grp:after {{
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border);
}}

/* ---- Executive Status Bar (Topbar) ---- */
.topbar {{
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: linear-gradient(180deg, #162235 0%, var(--panel) 100%);
  padding: 10px 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}}

.brand-group {{
  display: flex;
  align-items: center;
  gap: 8px;
}}

.brand {{
  font-size: 14px;
  font-weight: 700;
  letter-spacing: .06em;
  color: var(--text);
}}

.brand-badge {{
  font-size: 9.5px;
  font-weight: 600;
  padding: 2px 7px;
  background: rgba(14, 165, 233, 0.12);
  color: var(--cyan);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 4px;
  letter-spacing: .06em;
  text-transform: uppercase;
}}

.topbar .sep {{
  width: 1px;
  height: 26px;
  background: var(--border);
}}

.tb {{
  display: flex;
  flex-direction: column;
  gap: 2px;
}}

.tb .k {{
  font-size: 9.5px;
  font-weight: 500;
  letter-spacing: .05em;
  color: var(--muted);
  text-transform: uppercase;
}}

.tb .v {{
  font-size: 13px;
  font-family: var(--mono);
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}}

.spacer {{
  flex: 1;
}}

/* ---- Status Badges & Pills ---- */
.badge-pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .02em;
  line-height: 1.2;
}}

.badge-pill .pill-dot {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}}

.badge-emerald {{
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: {GREEN};
}}

.badge-blue {{
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.35);
  color: {BLUE};
}}

.badge-amber {{
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
  color: {AMBER};
}}

.badge-rose {{
  background: rgba(244, 63, 94, 0.12);
  border: 1px solid rgba(244, 63, 94, 0.35);
  color: {RED};
}}

.badge-slate {{
  background: rgba(100, 116, 139, 0.12);
  border: 1px solid rgba(100, 116, 139, 0.3);
  color: {DIM};
}}

.threat-badge {{
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .03em;
  text-transform: uppercase;
}}

.threat-badge.nominal {{
  border: 1px solid rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.12);
  color: {GREEN};
}}

.threat-badge.suspect {{
  border: 1px solid rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.12);
  color: {AMBER};
}}

.threat-badge.attack {{
  border: 1px solid rgba(244, 63, 94, 0.45);
  background: rgba(244, 63, 94, 0.14);
  color: {RED};
}}

.threat-badge.recovering {{
  border: 1px solid rgba(59, 130, 246, 0.35);
  background: rgba(59, 130, 246, 0.12);
  color: {BLUE};
}}

/* Live Feed Pill Indicator */
.live-pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 11px;
  border-radius: 9999px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: .04em;
  text-transform: uppercase;
}}

.live-pill.on {{
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: {GREEN};
  background: rgba(16, 185, 129, 0.12);
}}

.live-pill.off {{
  border: 1px solid rgba(100, 116, 139, 0.3);
  color: {MUTED};
  background: rgba(255, 255, 255, 0.04);
}}

.live-pill .dot {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}}

.live-pill.on .dot {{
  animation: live-blip 1.6s ease-in-out infinite;
}}

@keyframes live-blip {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.25; }}
}}

/* ---- Structured Panels ---- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  background: var(--panel) !important;
  padding: 12px 14px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
}}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: transparent !important;
}}

.panel {{
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel);
  padding: 12px 14px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}}

.panel-h {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(45, 55, 72, 0.4);
}}

.panel-h .t {{
  font-size: 13px;
  font-weight: 600;
  letter-spacing: .02em;
  color: var(--text);
}}

.panel-h .s {{
  font-size: 11px;
  color: var(--muted);
}}

/* ---- Status Tiles (Metrics Grid) ---- */
.tiles {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}}

.tile {{
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent, var(--border));
  border-radius: 6px;
  background: var(--panel-hi);
  padding: 9px 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 82px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
}}

.tile .k {{
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: .05em;
  text-transform: uppercase;
  color: var(--muted);
}}

.tile .v-box {{
  margin: 4px 0 2px 0;
}}

.tile .v {{
  font-size: 18px;
  font-weight: 600;
  font-family: var(--mono);
  color: var(--text);
  line-height: 1.25;
  font-variant-numeric: tabular-nums;
}}

.tile .u {{
  font-size: 11px;
  color: var(--dim);
  font-family: var(--sans);
}}

.tile .n {{
  font-size: 10px;
  color: var(--dim);
  line-height: 1.35;
}}

/* ---- Functional Domain Grouped Rail ---- */
.rail-domains {{
  display: grid;
  grid-template-columns: 1fr 1.35fr 1.65fr;
  gap: 12px;
}}

@media (max-width: 1000px) {{
  .rail-domains {{
    grid-template-columns: 1fr;
  }}
}}

.domain-col {{
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #0f1623;
  padding: 10px 12px;
}}

.domain-head {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}}

.domain-head .title {{
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .03em;
  text-transform: uppercase;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 6px;
}}

.domain-cards {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}

.det {{
  border: 1px solid var(--border);
  border-radius: 5px;
  background: var(--panel-hi);
  padding: 8px 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}}

.det .n {{
  font-size: 11px;
  color: var(--text);
  display: flex;
  justify-content: space-between;
  align-items: center;
}}

.det .n span {{
  font-weight: 500;
}}

.det .n b {{
  font-family: var(--mono);
  font-weight: 600;
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 4px;
}}

.det .bar {{
  height: 4px;
  background: #0b0f19;
  border-radius: 2px;
  margin: 6px 0 5px 0;
  overflow: hidden;
}}

.det .bar i {{
  display: block;
  height: 100%;
  border-radius: 2px;
}}

.det .r {{
  font-size: 10.5px;
  color: var(--muted);
  line-height: 1.35;
}}

.det.off {{
  opacity: .45;
}}

/* ---- Key/Value Metadata Strip ---- */
.kv {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px 16px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}}

.kv .i .k {{
  font-size: 9.5px;
  font-weight: 500;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--muted);
}}

.kv .i .v {{
  font-size: 12.5px;
  font-family: var(--mono);
  color: var(--text);
  font-variant-numeric: tabular-nums;
  word-break: break-word;
}}

/* ---- Structured Operational Log ---- */
.log {{
  max-height: 260px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}}

.row {{
  display: grid;
  grid-template-columns: 56px 110px 1fr;
  gap: 10px;
  align-items: center;
  padding: 6px 10px;
  border-left: 3px solid var(--accent, var(--border));
  background: var(--panel-hi);
  border-radius: 4px;
  font-size: 11.5px;
  border-top: 1px solid rgba(45, 55, 72, 0.3);
  border-right: 1px solid rgba(45, 55, 72, 0.3);
  border-bottom: 1px solid rgba(45, 55, 72, 0.3);
}}

.row .e {{
  color: var(--muted);
  font-family: var(--mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
}}

.row .w {{
  color: var(--accent, var(--dim));
  font-weight: 600;
  letter-spacing: .02em;
  font-size: 11px;
}}

.row .m {{
  color: var(--dim);
  font-size: 11px;
}}

.empty {{
  color: var(--muted);
  font-size: 11.5px;
  padding: 12px 4px;
  font-style: italic;
}}

/* ---- Subtitles, Hints & Chart Elements ---- */
.hint {{
  font-size: 11px;
  color: var(--muted);
  line-height: 1.45;
  margin: 3px 0 10px 2px;
}}

.hint b {{
  color: var(--dim);
  font-weight: 600;
}}

.ct {{
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .02em;
  color: var(--text);
  margin: 6px 0 2px 2px;
}}

.chips {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--muted);
  margin-top: 8px;
}}

.chip {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
}}

.chip i {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}}

.chip b {{
  color: var(--text);
  font-family: var(--mono);
  font-weight: 600;
}}

/* ---- Enterprise Tabs ---- */
button[data-baseweb="tab"] {{
  font-family: var(--sans) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: .02em !important;
  color: var(--dim) !important;
  padding: 8px 14px !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
  color: var(--text) !important;
  font-weight: 600 !important;
}}

/* ---- DataFrames ---- */
[data-testid="stDataFrame"] {{
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}}

/* ---- Enterprise Segmented Controls (Radio) ---- */
div[data-testid="stRadio"] > div {{
  gap: 4px;
}}

div[data-testid="stRadio"] label {{
  background: var(--panel-hi);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 11px !important;
  font-weight: 500 !important;
  color: var(--dim) !important;
  cursor: pointer;
  transition: all 0.15s ease;
}}

div[data-testid="stRadio"] label:hover {{
  background: #253349;
  color: var(--text) !important;
  border-color: #3b4d6b;
}}

div[data-testid="stRadio"] label[data-checked="true"],
div[data-testid="stRadio"] label:has(input:checked) {{
  background: #1e3a5f !important;
  border-color: var(--cyan) !important;
  color: #ffffff !important;
  font-weight: 600 !important;
}}

div[data-testid="stRadio"] input[type="radio"] {{
  display: none;
}}
</style>
"""
