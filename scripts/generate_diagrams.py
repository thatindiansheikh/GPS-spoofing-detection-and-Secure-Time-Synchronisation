"""Generate spacious, clear, uncluttered engineering flowcharts in Times New Roman.
Zero text overflow (at least 25-35% padding inside all shapes), zero dashes.
Dimensions tailored to 5.2-5.4 inch printable Word page width to avoid downscaling shrinkage.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# Enforce Times New Roman globally
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "mathtext.fontset": "stix",
})

OUT_DIR = Path(r"Y:\Final yr project\Honours\gps-spoof-timesync\report\generated_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_flowchart_operation():
    """Generates Figure 6.2: Complete End to End Flow of Operation.
    Spacious vertical layout with ample margins, zero box clipping, and zero dashes.
    Large, bold typography engineered for maximum legibility in Word.
    """
    fig, ax = plt.subplots(figsize=(6.2, 8.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(-3, 103)
    ax.axis("off")
    
    # 9 Sequential Steps: Centered, generously padded (width 62, height 5.8)
    steps = [
        ("START", "System Initialization", 94, "pill", "#E2E8F0", "#334155"),
        ("RECEIVE TELEMETRY", "Stream NMEA 0183 Messages", 83, "rect", "#DBEAFE", "#1D4ED8"),
        ("SYNTAX & CHECKSUM", "Verify Sentence Integrity", 72, "rect", "#DBEAFE", "#1D4ED8"),
        ("EPOCH ASSEMBLY", "Collate 1 Hz Satellite Fix", 61, "rect", "#DBEAFE", "#1D4ED8"),
        ("SURVEY READY?", "Calibration Finished?", 49, "diamond", "#FEF3C7", "#B45309"),
        ("EXECUTE DETECTORS", "8 Plausibility Engines", 36, "rect", "#DCFCE7", "#15803D"),
        ("TRUST FUSION", "Multi Domain Evidence Score", 25, "rect", "#DCFCE7", "#15803D"),
        ("CLOCK DISCIPLINING", "Select Time Authority", 14, "rect", "#FEF3C7", "#B45309"),
        ("SERVE NETWORK TIME", "NTP Stratum Disciplined", 3, "pill", "#E2E8F0", "#334155"),
    ]
    
    for tag, label, y, shape, fc, ec in steps:
        if shape == "pill":
            box = patches.FancyBboxPatch((19, y-2.9), 62, 5.8, boxstyle="round,pad=0.8,rounding_size=2.8", fc=fc, ec=ec, lw=1.6)
            ax.add_patch(box)
            ax.text(50, y+1.0, tag, ha="center", va="center", fontsize=11.5, fontweight="bold", color="#0F172A")
            ax.text(50, y-1.1, label, ha="center", va="center", fontsize=9.5, color="#334155")
        elif shape == "diamond":
            poly = patches.Polygon([[50, y+5.2], [73, y], [50, y-5.2], [27, y]], closed=True, fc=fc, ec=ec, lw=1.6)
            ax.add_patch(poly)
            ax.text(50, y+1.1, tag, ha="center", va="center", fontsize=11.0, fontweight="bold", color="#78350F")
            ax.text(50, y-1.2, label, ha="center", va="center", fontsize=9.2, color="#92400E")
        else: # rect
            box = patches.FancyBboxPatch((19, y-2.9), 62, 5.8, boxstyle="round,pad=0.5", fc=fc, ec=ec, lw=1.6)
            ax.add_patch(box)
            ax.text(50, y+1.0, tag, ha="center", va="center", fontsize=11.5, fontweight="bold", color="#0F172A")
            ax.text(50, y-1.1, label, ha="center", va="center", fontsize=9.5, color="#334155")
            
    # Connect sequential steps with straight vertical arrows
    for i in range(len(steps)-1):
        y_top = steps[i][2] - 3.2
        y_bot = steps[i+1][2] + 3.2
        if steps[i][3] == "diamond":
            y_top = steps[i][2] - 5.4
        if steps[i+1][3] == "diamond":
            y_bot = steps[i+1][2] + 5.4
        ax.annotate("", xy=(50, y_bot), xytext=(50, y_top),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color="#334155", mutation_scale=12))
                    
    # Side branch for calibration: If NO -> accumulate survey fixes
    ax.text(75, 50.8, "NO", fontsize=10.0, fontweight="bold", color="#B45309")
    # Clean 3-segment orthogonal conduit: (73, 49) -> (89, 49) -> (89, 61) -> (81, 61)
    ax.plot([73, 89], [49, 49], color="#B45309", lw=1.6)
    ax.plot([89, 89], [49, 61], color="#B45309", lw=1.6)
    ax.annotate("", xy=(81, 61), xytext=(89, 61),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#B45309", mutation_scale=11))
    ax.text(89, 55, "Accumulate\nFixes", ha="center", va="center", fontsize=8.8, fontweight="bold", color="#78350F",
            bbox=dict(boxstyle="round,pad=0.4", fc="#FEF3C7", ec="#B45309", lw=1.2))
            
    # Straight down branch for YES
    ax.text(53.5, 41.5, "YES", fontsize=10.0, fontweight="bold", color="#15803D")
    
    # Continuous execution loop on left
    ax.plot([19, 7], [3, 3], color="#64748B", lw=1.5, ls="--")
    ax.plot([7, 7], [3, 83], color="#64748B", lw=1.5, ls="--")
    ax.annotate("", xy=(19, 83), xytext=(7, 83),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#64748B", ls="--", mutation_scale=11))
    ax.text(4.5, 43, "Continuous 1 Hz Execution Cycle", rotation=90, fontsize=9.5, fontweight="bold", color="#475569", va="center", ha="right")
    
    plt.tight_layout()
    out_file = OUT_DIR / "figure_6_2_flowchart_system_operation.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print("Generated clean operation flowchart:", out_file)

def generate_flowchart_decision():
    """Generates Figure 6.3: System Flowchart and Decision Logic.
    Spacious tree structure with ample gaps between boxes and zero overlapping text.
    All connectors enter boxes at their exact horizontal center.
    """
    fig, ax = plt.subplots(figsize=(6.6, 8.4), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(-2, 102)
    ax.axis("off")
    
    # 1. Root Box: Incoming Epoch Trust Score (width 66, centered at x=50, y=93)
    b_root = patches.FancyBboxPatch((17, 89.5), 66, 7.5, boxstyle="round,pad=0.5", fc="#EFF6FF", ec="#1D4ED8", lw=1.6)
    ax.add_patch(b_root)
    ax.text(50, 94.0, "COMPUTE EPOCH TRUST SCORE (T)", ha="center", va="center", fontsize=11.5, fontweight="bold", color="#1E3A8A")
    ax.text(50, 91.2, "Multi Domain Evidence Fusion Engine", ha="center", va="center", fontsize=9.5, color="#1D4ED8")
    
    # Down arrow to Diamond 1
    ax.annotate("", xy=(50, 83), xytext=(50, 89.5),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#1E293B", mutation_scale=12))
    
    # 2. Diamond 1: Is T < 0.80? (center x=50, y=75; width 44, height 16)
    poly1 = patches.Polygon([[50, 83], [72, 75], [50, 67], [28, 75]], closed=True, fc="#FEF3C7", ec="#B45309", lw=1.8)
    ax.add_patch(poly1)
    ax.text(50, 76.5, "Is Trust Score T < 0.80?", ha="center", va="center", fontsize=11.0, fontweight="bold", color="#78350F")
    ax.text(50, 73.0, "(Rejection Threshold)", ha="center", va="center", fontsize=9.2, color="#92400E")
    
    # ------------------ LEFT BRANCH: ATTACK REJECT ------------------
    ax.text(16, 77.5, "YES (Spoofed)", fontsize=10.0, fontweight="bold", color="#B91C1C", ha="center")
    # Orthogonal arrow: exits tip (28, 75) horizontally to x=25, then drops vertically to Diamond 2 top (25, 59)
    ax.annotate("", xy=(25, 59), xytext=(28, 75),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#DC2626",
                                connectionstyle="angle,angleA=0,angleB=90,rad=4", mutation_scale=12))
    
    # Diamond 2: NTP Available? (centered at x=25, y=51; width 24, height 16)
    poly_ntp = patches.Polygon([[25, 59], [37, 51], [25, 43], [13, 51]], closed=True, fc="#FEE2E2", ec="#DC2626", lw=1.6)
    ax.add_patch(poly_ntp)
    ax.text(25, 52.8, "NTP Peer", ha="center", va="center", fontsize=10.0, fontweight="bold", color="#7F1D1D")
    ax.text(25, 49.5, "Available?", ha="center", va="center", fontsize=9.0, color="#991B1B")
    
    # Diamond 2 Exits (Drop straight down from tips into box centers):
    # YES branch (left tip at 13, 51): drops straight down to Box 1 center at (13, 34)
    ax.text(9.5, 43.5, "YES", fontsize=9.5, fontweight="bold", color="#1D4ED8", ha="center")
    ax.annotate("", xy=(13, 34), xytext=(13, 51),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#2563EB", mutation_scale=11))
    
    # NO branch (right tip at 37, 51): drops straight down to Box 2 center at (37, 34)
    ax.text(40.5, 43.5, "NO", fontsize=9.5, fontweight="bold", color="#B45309", ha="center")
    ax.annotate("", xy=(37, 34), xytext=(37, 51),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#D97706", mutation_scale=11))
    
    # Box 1: NTP PEER (centered at x=13, width 16, height 8.5 -> x = [5, 21])
    b_ntp = patches.FancyBboxPatch((5.0, 25.5), 16.0, 8.5, boxstyle="round,pad=0.5", fc="#EFF6FF", ec="#2563EB", lw=1.6)
    ax.add_patch(b_ntp)
    ax.text(13, 30.8, "NTP PEER", ha="center", va="center", fontsize=10.2, fontweight="bold", color="#1E3A8A")
    ax.text(13, 27.5, "Stratum 2 Ref", ha="center", va="center", fontsize=8.8, color="#1E40AF")
    
    # Box 2: HOLDOVER (centered at x=37, width 16, height 8.5 -> x = [29, 45])
    b_hold = patches.FancyBboxPatch((29.0, 25.5), 16.0, 8.5, boxstyle="round,pad=0.5", fc="#FEF3C7", ec="#D97706", lw=1.6)
    ax.add_patch(b_hold)
    ax.text(37, 30.8, "HOLDOVER", ha="center", va="center", fontsize=10.2, fontweight="bold", color="#78350F")
    ax.text(37, 27.5, "Local Clock", ha="center", va="center", fontsize=8.8, color="#92400E")
    
    # ------------------ RIGHT BRANCH: NOMINAL / SUSPECT ------------------
    ax.text(84, 77.5, "NO (Nominal)", fontsize=10.0, fontweight="bold", color="#15803D", ha="center")
    # Orthogonal arrow: exits tip (72, 75) horizontally to x=75, then drops vertically to Diamond 3 top (75, 59)
    ax.annotate("", xy=(75, 59), xytext=(72, 75),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#16A34A",
                                connectionstyle="angle,angleA=0,angleB=90,rad=4", mutation_scale=12))
    
    # Diamond 3: Suspect Check? (centered at x=75, y=51; width 24, height 16)
    poly_susp = patches.Polygon([[75, 59], [87, 51], [75, 43], [63, 51]], closed=True, fc="#FEF3C7", ec="#D97706", lw=1.6)
    ax.add_patch(poly_susp)
    ax.text(75, 52.8, "Trust Score", ha="center", va="center", fontsize=10.0, fontweight="bold", color="#78350F")
    ax.text(75, 49.5, "T < 0.90?", ha="center", va="center", fontsize=9.0, color="#92400E")
    
    # Diamond 3 Exits (Drop straight down from tips into box centers):
    # YES branch (left tip at 63, 51): drops straight down to Box 3 center at (63, 34)
    ax.text(59.5, 43.5, "YES", fontsize=9.5, fontweight="bold", color="#C2410C", ha="center")
    ax.annotate("", xy=(63, 34), xytext=(63, 51),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#D97706", mutation_scale=11))
    
    # NO branch (right tip at 87, 51): drops straight down to Box 4 center at (87, 34)
    ax.text(90.5, 43.5, "NO", fontsize=9.5, fontweight="bold", color="#15803D", ha="center")
    ax.annotate("", xy=(87, 34), xytext=(87, 51),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#16A34A", mutation_scale=11))
    
    # Box 3: GPS SUSPECT (centered at x=63, width 16, height 8.5 -> x = [55, 71])
    b_susp = patches.FancyBboxPatch((55.0, 25.5), 16.0, 8.5, boxstyle="round,pad=0.5", fc="#FFFBEB", ec="#F59E0B", lw=1.6)
    ax.add_patch(b_susp)
    ax.text(63, 30.8, "GPS SUSPECT", ha="center", va="center", fontsize=10.2, fontweight="bold", color="#92400E")
    ax.text(63, 27.5, "Raise Alert", ha="center", va="center", fontsize=8.8, color="#B45309")
    
    # Box 4: GPS TRUSTED (centered at x=87, width 16, height 8.5 -> x = [79, 95])
    b_trust = patches.FancyBboxPatch((79.0, 25.5), 16.0, 8.5, boxstyle="round,pad=0.5", fc="#DCFCE7", ec="#16A34A", lw=1.6)
    ax.add_patch(b_trust)
    ax.text(87, 30.8, "GPS TRUSTED", ha="center", va="center", fontsize=10.2, fontweight="bold", color="#14532D")
    ax.text(87, 27.5, "Stratum 0 Lock", ha="center", va="center", fontsize=8.8, color="#15803D")
    
    # ------------------ RECOVERY HYSTERESIS NOTE ------------------
    b_rec = patches.FancyBboxPatch((44.0, 44.5), 12.0, 13.0, boxstyle="round,pad=0.4", fc="#F8FAFC", ec="#94A3B8", lw=1.4, ls="--")
    ax.add_patch(b_rec)
    ax.text(50, 53.5, "RECOVERY", ha="center", va="center", fontsize=9.0, fontweight="bold", color="#1E293B")
    ax.text(50, 49.0, "20 Clean\nEpochs\n(T > 0.85)", ha="center", va="center", fontsize=8.0, color="#475569")
    
    # ------------------ COMMON ACTIONS (BOTTOM) ------------------
    b_act = patches.FancyBboxPatch((3.5, 4.5), 93.0, 12.0, boxstyle="round,pad=0.6", fc="#F1F5F9", ec="#334155", lw=1.6)
    ax.add_patch(b_act)
    ax.text(50, 12.5, "DISCIPLINE HOST CLOCK & COMMIT AUDIT LOGS", ha="center", va="center", fontsize=11.5, fontweight="bold", color="#0F172A")
    ax.text(50, 7.8, "Compute Uncertainty  |  Record Event to SQLite  |  Refresh Operations Console", ha="center", va="center", fontsize=9.5, color="#334155")
    
    # Connect all 4 outcome boxes straight down into bottom action box from their centers
    for x in [13, 37, 63, 87]:
        ax.annotate("", xy=(x, 16.5), xytext=(x, 25.5),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569", mutation_scale=11))
                    
    plt.tight_layout()
    out_file = OUT_DIR / "figure_6_3_flowchart_decision_logic.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print("Generated clean decision logic flowchart:", out_file)

def generate_system_architecture():
    """Generates Figure 3.1: System Architecture Overview.
    Clean 4-layer architectural diagram with ample padding (zero text overflow).
    """
    fig, ax = plt.subplots(figsize=(6.4, 5.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    
    layers = [
        ("LAYER 1: TELEMETRY INGESTION AND COLLATION",
         "Ingests NMEA 0183 sentences ($GPGGA, $GPRMC, $GPGSA, $GPGSV)",
         "Validates hexadecimal checksums and groups messages into 1s epochs",
         81, "#EFF6FF", "#2563EB", "#1E3A8A"),
        ("LAYER 2: MULTI DOMAIN PLAUSIBILITY DETECTION (8 CHECKS)",
         "Spatial: Station deviation, velocity kinematics, trajectory acceleration",
         "RF Physics: Multi satellite SNR spread, overpower, sat count, HDOP, NTP",
         55, "#F0FDF4", "#16A34A", "#14532D"),
        ("LAYER 3: PROBABILISTIC TRUST FUSION AND FAILOVER",
         "Non scoring evidence abstention for missing telemetry fields",
         "Noisy OR fusion engine with thresholds (0.80 Reject, 0.90 Suspect)",
         29, "#FEF3C7", "#D97706", "#78350F"),
        ("LAYER 4: TIME SERVICE AND OPERATIONS DASHBOARD",
         "Disciplines system clock and maintains historical state buffers",
         "SQLite audit logging with interactive Streamlit monitoring console",
         3, "#F1F5F9", "#475569", "#0F172A"),
    ]
    
    for title, line1, line2, y, fc, ec, tc in layers:
        box = patches.FancyBboxPatch((3, y), 94, 18, boxstyle="round,pad=0.7", fc=fc, ec=ec, lw=1.6)
        ax.add_patch(box)
        ax.text(50, y+13.0, title, ha="center", va="center", fontsize=10.8, fontweight="bold", color=tc)
        ax.text(50, y+7.5, line1, ha="center", va="center", fontsize=8.8, color="#1E293B")
        ax.text(50, y+3.2, line2, ha="center", va="center", fontsize=8.8, color="#334155")
        
    for y_top in [81, 55, 29]:
        ax.annotate("", xy=(50, y_top-6), xytext=(50, y_top),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color="#334155", mutation_scale=13))
                    
    plt.tight_layout()
    out_file = OUT_DIR / "figure_3_1_system_architecture.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print("Generated clean system architecture diagram:", out_file)

def generate_methodology_diagram():
    """Generates Figure 1.1: Proposed Solution and Methodology."""
    fig, ax = plt.subplots(figsize=(6.4, 4.4), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    
    # 5 clean pipeline blocks with concise centered labels (max 11 chars)
    steps = [
        ("1. Ingest", "Serial NMEA\nCRC Check", 10, "#EFF6FF", "#2563EB"),
        ("2. Collate", "Group Fixes\n1s Epoch", 30, "#F0FDF4", "#16A34A"),
        ("3. Detect", "8 Physical\nChecks", 50, "#FEF3C7", "#D97706"),
        ("4. Fuse", "Noisy OR\nTrust Score", 70, "#FEE2E2", "#DC2626"),
        ("5. Route", "Clock Select\nHoldover", 90, "#F3E8FF", "#7C3AED"),
    ]
    
    for title, desc, cx, fc, ec in steps:
        box = patches.FancyBboxPatch((cx-8.5, 34), 17, 48, boxstyle="round,pad=0.6", fc=fc, ec=ec, lw=1.6)
        ax.add_patch(box)
        ax.text(cx, 68, title, ha="center", va="center", fontsize=10.2, fontweight="bold", color="#0F172A")
        ax.text(cx, 48, desc, ha="center", va="center", fontsize=8.8, color="#334155", linespacing=1.35)
        
    for i in range(len(steps)-1):
        x1 = steps[i][2] + 8.5
        x2 = steps[i+1][2] - 8.5
        ax.annotate("", xy=(x2, 58), xytext=(x1, 58),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color="#475569", mutation_scale=12))
                    
    cal_box = patches.FancyBboxPatch((6, 6), 88, 18, boxstyle="round,pad=0.6", fc="#F8FAFC", ec="#94A3B8", lw=1.4, ls="--")
    ax.add_patch(cal_box)
    ax.text(50, 17, "INITIAL QUIET SEGMENT SURVEY CALIBRATION (FIRST 40 PERCENT)", ha="center", fontsize=9.2, fontweight="bold", color="#1E293B")
    ax.text(50, 10.5, "Calculates empirical baselines for position scatter, carrier to noise, and geometry", ha="center", fontsize=8.4, color="#475569")
    
    ax.annotate("", xy=(30, 34), xytext=(30, 24), arrowprops=dict(arrowstyle="->", lw=1.4, color="#64748B", ls="--", mutation_scale=10))
    ax.annotate("", xy=(50, 34), xytext=(50, 24), arrowprops=dict(arrowstyle="->", lw=1.4, color="#64748B", ls="--", mutation_scale=10))
    
    plt.tight_layout()
    out_file = OUT_DIR / "figure_1_1_proposed_methodology.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print("Generated clean methodology diagram:", out_file)

def generate_phase_development():
    """Generates Figure 7.3: Phase Wise Development Cycle."""
    fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    
    phases = [
        ("Phase 1: Ingestion", "• Threat modeling\n• JammerTest data\n• NMEA parser\n• Epoch collation", 18, "#EFF6FF", "#2563EB"),
        ("Phase 2: Detectors", "• 8 physical checks\n• Baseline tuning\n• Abstention rules\n• Noisy OR fusion", 50, "#F0FDF4", "#16A34A"),
        ("Phase 3: Failover", "• State machine\n• Holdover model\n• SQLite event log\n• NOC dashboard", 82, "#FEF3C7", "#D97706"),
    ]
    
    for title, desc, cx, fc, ec in phases:
        box = patches.FancyBboxPatch((cx-14, 8), 28, 80, boxstyle="round,pad=0.7", fc=fc, ec=ec, lw=1.6)
        ax.add_patch(box)
        ax.text(cx, 75, title, ha="center", va="center", fontsize=10.2, fontweight="bold", color="#0F172A")
        ax.text(cx, 44, desc, ha="center", va="center", fontsize=8.8, color="#334155", linespacing=1.4)
        
    for i in range(len(phases)-1):
        x1 = phases[i][2] + 14
        x2 = phases[i+1][2] - 14
        ax.annotate("", xy=(x2, 48), xytext=(x1, 48),
                    arrowprops=dict(arrowstyle="->", lw=2.0, color="#475569", mutation_scale=13))
                    
    plt.tight_layout()
    out_file = OUT_DIR / "figure_7_3_phase_development.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print("Generated clean phase development diagram:", out_file)

if __name__ == "__main__":
    generate_flowchart_operation()
    generate_flowchart_decision()
    generate_system_architecture()
    generate_methodology_diagram()
    generate_phase_development()
    print("All diagrams regenerated with ample padding and zero text overflow!")
