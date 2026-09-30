"""Full generator implementing the exact college format for the Honours Final Year Mini Project Report.
Zero dashes, Times New Roman, pure software implementation, flowcharts inserted, no tables for prelims.
"""

import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from pathlib import Path

BASE_DIR = Path(r"Y:\Final yr project\Honours\gps-spoof-timesync")
REPORT_DIR = BASE_DIR / "report"
FIG_DIR = REPORT_DIR / "generated_figures"
MEDIA_DIR = REPORT_DIR / "extracted_media" / "word" / "media"
RESULTS_FIG = BASE_DIR / "results" / "figures"

SVCE_LOGO = str(MEDIA_DIR / "image1.png")
AU_LOGO = str(MEDIA_DIR / "image2.png")

FIG_1_1 = str(FIG_DIR / "figure_1_1_proposed_methodology.png")
FIG_3_1 = str(FIG_DIR / "figure_3_1_system_architecture.png")
FIG_6_2 = str(FIG_DIR / "figure_6_2_flowchart_system_operation.png")
FIG_6_3 = str(FIG_DIR / "figure_6_3_flowchart_decision_logic.png")
FIG_6_4 = str(FIG_DIR / "figure_6_4_holdover_model.png")
FIG_7_1 = str(FIG_DIR / "figure_7_1_deviation_constellation.png")
FIG_7_2 = str(FIG_DIR / "figure_7_2_scenario_timeline.png")
FIG_7_3 = str(FIG_DIR / "figure_7_3_phase_development.png")

DASH_CHARS = ["-", "–", "—", "−", "‐", "‑", "‒", "―"]

def clean(text: str) -> str:
    if not text:
        return ""
    for d in DASH_CHARS:
        text = text.replace(d, " ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text

def set_font(run, size=12, bold=False, italic=False, color=(0,0,0)):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color)
    rPr = run._r.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>')
    rPr.append(rFonts)

def p(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, bold=False, italic=False, before=0, after=6, spacing=1.5, first_line=0.5, keep_with_next=False):
    c_text = clean(text)
    par = doc.add_paragraph()
    par.alignment = align
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = spacing
    par.paragraph_format.keep_with_next = keep_with_next
    if align == WD_ALIGN_PARAGRAPH.JUSTIFY and first_line > 0:
        par.paragraph_format.first_line_indent = Inches(first_line)
    if c_text:
        run = par.add_run(c_text)
        set_font(run, size=size, bold=bold, italic=italic)
    return par

def h1(doc, text, before=18, after=12):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, before=before, after=after, first_line=0.0, keep_with_next=True)

def h2(doc, text, before=14, after=6):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, size=12, bold=True, before=before, after=after, first_line=0.0, keep_with_next=True)

def h3(doc, text, before=10, after=4):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, size=12, bold=True, italic=True, before=before, after=after, first_line=0.0, keep_with_next=True)

def author_line(doc, authors_year):
    c_text = clean(authors_year)
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    par.paragraph_format.left_indent = Inches(0.5)
    par.paragraph_format.first_line_indent = Inches(0)
    par.paragraph_format.space_before = Pt(3)
    par.paragraph_format.space_after = Pt(6)
    par.paragraph_format.line_spacing = 1.5
    par.paragraph_format.keep_with_next = True
    run = par.add_run(c_text)
    set_font(run, size=12, bold=True, italic=False)
    return par

def bullet(doc, title, desc, after=4):
    c_title = clean(title)
    c_desc = clean(desc)
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.left_indent = Inches(0.25)
    par.paragraph_format.first_line_indent = Inches(0)
    par.paragraph_format.space_before = Pt(2)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.5
    par.paragraph_format.keep_with_next = False
    
    rb = par.add_run("• ")
    set_font(rb, size=12, bold=True)
    if c_title:
        rt = par.add_run(c_title + ": ")
        set_font(rt, size=12, bold=True)
    rd = par.add_run(c_desc)
    set_font(rd, size=12, bold=False)
    return par

def add_toc_line(doc, col1, col2, col3, bold=False, size=10.5, before=1, after=2):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.25
    par.paragraph_format.keep_with_next = False
    par.paragraph_format.left_indent = Inches(1.2)
    par.paragraph_format.first_line_indent = Inches(-1.2)
    par.paragraph_format.tab_stops.add_tab_stop(Inches(1.2), WD_TAB_ALIGNMENT.LEFT)
    par.paragraph_format.tab_stops.add_tab_stop(Inches(5.65), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    
    c1 = clean(str(col1))
    c2 = clean(str(col2))
    c3 = clean(str(col3))
    
    line_text = f"{c1}\t{c2}\t{c3}" if c1 else f"\t{c2}\t{c3}"
    runs = par.add_run(line_text)
    set_font(runs, size=size, bold=bold)
    return par

def add_two_col_line(doc, col1, col2, bold=False, size=11, before=1.5, after=1.5, tab_pos=1.6):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.25
    par.paragraph_format.keep_with_next = False
    par.paragraph_format.left_indent = Inches(tab_pos)
    par.paragraph_format.first_line_indent = Inches(-tab_pos)
    par.paragraph_format.tab_stops.add_tab_stop(Inches(tab_pos), WD_TAB_ALIGNMENT.LEFT)
    
    c1 = clean(str(col1))
    c2 = clean(str(col2))
    
    line_text = f"{c1}\t{c2}"
    runs = par.add_run(line_text)
    set_font(runs, size=size, bold=bold)
    return par

def insert_image(doc, img_path, width_in=5.5, caption_no="", caption_title=""):
    c_no = clean(caption_no)
    c_title = clean(caption_title)
    
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(8)
    par.paragraph_format.space_after = Pt(4)
    par.paragraph_format.keep_with_next = True
    
    if os.path.exists(img_path):
        run = par.add_run()
        run.add_picture(img_path, width=Inches(width_in))
    else:
        r = par.add_run(f"[ Image File Not Found: {clean(os.path.basename(img_path))} ]")
        set_font(r, size=10, italic=True)
        
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(4)
    cap.paragraph_format.space_after = Pt(14)
    rc = cap.add_run(f"Figure {c_no} {c_title}")
    set_font(rc, size=11, bold=True)

def fig_placeholder_box(doc, no, title):
    c_no = clean(no)
    c_title = clean(title)
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(5.8)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="999999"/>
            <w:left w:val="single" w:sz="6" w:space="0" w:color="999999"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="999999"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="999999"/>
        </w:tcBorders>
    ''')
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
    tcPr.append(borders)
    tcPr.append(shd)
    
    cp = cell.paragraphs[0]
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(36)
    cp.paragraph_format.space_after = Pt(36)
    r1 = cp.add_run(f"[ SPACE FOR FIGURE {c_no.upper()} ]\n")
    set_font(r1, size=11, bold=True, color=(100, 100, 100))
    r2 = cp.add_run(f"Paste {c_title} Screenshot Here")
    set_font(r2, size=10, italic=True, color=(120, 120, 120))
    
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(6)
    cap.paragraph_format.space_after = Pt(14)
    rc = cap.add_run(f"Figure {c_no} {c_title}")
    set_font(rc, size=11, bold=True)

def table_header(row, headers, widths=None):
    for idx, header in enumerate(headers):
        cell = row.cells[idx]
        if widths and idx < len(widths):
            cell.width = Inches(widths[idx])
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="E2E8F0"/>')
        tcPr.append(shd)
        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="333333"/>
                <w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                <w:bottom w:val="single" w:sz="12" w:space="0" w:color="333333"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
        ''')
        tcPr.append(borders)
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_before = Pt(4)
        cp.paragraph_format.space_after = Pt(4)
        r = cp.add_run(clean(header))
        set_font(r, size=10, bold=True)

def table_row(row, values, widths=None, align_center=False):
    for idx, val in enumerate(values):
        cell = row.cells[idx]
        if widths and idx < len(widths):
            cell.width = Inches(widths[idx])
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                <w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
        ''')
        tcPr.append(borders)
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER if align_center or idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
        cp.paragraph_format.space_before = Pt(3)
        cp.paragraph_format.space_after = Pt(3)
        r = cp.add_run(clean(str(val)))
        set_font(r, size=9.5, bold=False)

def generate_report(output_docx_path):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    # 1.5 in Left margin for binding, 1.0 in for others
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.5)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        
    print("Writing Title Page with University and College Logos...")
    # -------------------------------------------------------------
    # 1. TITLE PAGE
    # -------------------------------------------------------------
    # Logo table (borderless)
    logo_tbl = doc.add_table(rows=1, cols=2)
    logo_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cl = logo_tbl.cell(0, 0)
    cr = logo_tbl.cell(0, 1)
    cl.width = Inches(3.0)
    cr.width = Inches(3.0)
    
    # Remove borders from logo table
    for cell in [cl, cr]:
        tcPr = cell._tc.get_or_add_tcPr()
        b = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="none"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        tcPr.append(b)
        
    pl = cl.paragraphs[0]
    pl.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if os.path.exists(SVCE_LOGO):
        pl.add_run().add_picture(SVCE_LOGO, width=Inches(1.15))
        
    pr = cr.paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if os.path.exists(AU_LOGO):
        pr.add_run().add_picture(AU_LOGO, width=Inches(1.15))
        
    p(doc, "TRUST BASED DETECTION OF GPS SPOOFING FOR SECURE NETWORK TIME SYNCHRONIZATION", align=WD_ALIGN_PARAGRAPH.CENTER, size=15, bold=True, before=28, after=18, spacing=1.2)
    p(doc, "PROJECT REPORT FOR HONOURS FINAL YEAR MINI PROJECT", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=18, after=24)
    p(doc, "Submitted by", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, italic=True, before=14, after=18)
    
    p(doc, "[CANDIDATE NAME] [REGISTER NUMBER]", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=6, after=24)
    
    p(doc, "in partial fulfillment for the award of the degree", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, italic=True, before=14, after=4)
    p(doc, "of", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, italic=True, before=2, after=4)
    p(doc, "BACHELOR OF ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=4, after=4)
    p(doc, "IN", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=2, after=4)
    p(doc, "ELECTRONICS AND COMMUNICATION ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=4, after=24)
    
    p(doc, "SRI VENKATESWARA COLLEGE OF ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=16, after=2)
    p(doc, "(An Autonomous Institution, Affiliated to Anna University, Chennai 600025)", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=2, after=4)
    p(doc, "ANNA UNIVERSITY :: CHENNAI 600025", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=4, after=18)
    p(doc, "[MONTH YEAR]", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=10, after=0)
    
    doc.add_page_break()
    
    print("Writing Bonafide Certificate...")
    # -------------------------------------------------------------
    # 2. BONAFIDE CERTIFICATE
    # -------------------------------------------------------------
    p(doc, "SRI VENKATESWARA COLLEGE OF ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=10, after=2)
    p(doc, "(An Autonomous Institution, Affiliated to Anna University, Chennai 600025)", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=2, after=4)
    p(doc, "ANNA UNIVERSITY, CHENNAI 600025", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=4, after=24)
    
    p(doc, "BONAFIDE CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, before=18, after=24)
    
    cert_text = (
        "Certified that this project report titled \"TRUST BASED DETECTION OF GPS SPOOFING FOR SECURE NETWORK TIME SYNCHRONIZATION\" "
        "is the bonafide work of \"[CANDIDATE NAME] ([REGISTER NUMBER])\" who carried out the honours final year mini project "
        "work under my supervision."
    )
    p(doc, cert_text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, before=12, after=36, spacing=1.5)
    
    sig_tbl = doc.add_table(rows=1, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_l = sig_tbl.cell(0, 0)
    cell_r = sig_tbl.cell(0, 1)
    cell_l.width = Inches(3.2)
    cell_r.width = Inches(3.2)
    
    for c in [cell_l, cell_r]:
        tcPr = c._tc.get_or_add_tcPr()
        b = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="none"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        tcPr.append(b)
        
    pl = cell_l.paragraphs[0]
    pl.paragraph_format.line_spacing = 1.3
    rl1 = pl.add_run("SIGNATURE\n\n\n\n[SUPERVISOR NAME]\n")
    set_font(rl1, size=11, bold=True)
    rl2 = pl.add_run("SUPERVISOR\nAssociate Professor\nDepartment of Electronics and\nCommunication Engineering")
    set_font(rl2, size=10, bold=False)
    
    pr = cell_r.paragraphs[0]
    pr.paragraph_format.line_spacing = 1.3
    rr1 = pr.add_run("SIGNATURE\n\n\n\n[HEAD OF DEPARTMENT NAME]\n")
    set_font(rr1, size=11, bold=True)
    rr2 = pr.add_run("HEAD OF THE DEPARTMENT\nProfessor\nDepartment of Electronics and\nCommunication Engineering")
    set_font(rr2, size=10, bold=False)
    
    p(doc, "", before=24, after=12)
    p(doc, "Submitted for the project viva voce examination held on ____________________", align=WD_ALIGN_PARAGRAPH.LEFT, size=11, before=36, after=40)
    
    ex_tbl = doc.add_table(rows=1, cols=2)
    ex_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    ex_l = ex_tbl.cell(0, 0)
    ex_r = ex_tbl.cell(0, 1)
    ex_l.width = Inches(3.2)
    ex_r.width = Inches(3.2)
    
    for c in [ex_l, ex_r]:
        tcPr = c._tc.get_or_add_tcPr()
        b = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="none"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        tcPr.append(b)
        
    pel = ex_l.paragraphs[0]
    rel = pel.add_run("INTERNAL EXAMINER")
    set_font(rel, size=11, bold=True)
    
    per = ex_r.paragraphs[0]
    rer = per.add_run("EXTERNAL EXAMINER")
    set_font(rer, size=11, bold=True)
    
    doc.add_page_break()
    
    print("Writing Abstract...")
    # -------------------------------------------------------------
    # 3. ABSTRACT
    # -------------------------------------------------------------
    h1(doc, "ABSTRACT", before=18, after=18)
    
    p(doc, (
        "Modern computer networks, electrical distribution grids, cellular base stations, and high frequency financial transaction systems "
        "depend completely on precise time synchronization. In current deployments, a Global Positioning System receiver acts as a primary "
        "Stratum 0 reference clock, distributing coordinated universal time across internal infrastructure through the Network Time Protocol "
        "or Precision Time Protocol. However, civil satellite positioning signals are unauthenticated and arrive at the Earth surface with "
        "extremely weak radio frequency power, making them exceptionally vulnerable to deliberate spoofing and malicious transmission. "
        "When an adversary transmits counterfeit satellite signals, the receiver calculates a false time solution while reporting nominal tracking status. "
        "This false time silently propagates through network infrastructure, invalidating digital certificates, disrupting database transaction logs, "
        "and breaking critical infrastructure operations without triggering conventional hardware alarms."
    ))
    p(doc, (
        "To eliminate this critical security vulnerability, this project develops an intelligent software trust layer that sits directly between "
        "the satellite receiver and the host time synchronization stack. The entire architecture is implemented purely in software, operating on standard "
        "National Marine Electronics Association telemetry sentences emitted by conventional navigation hardware without requiring specialized radio equipment. "
        "The software architecture executes eight independent physical plausibility checks across spatial position, velocity kinematics, trajectory consistency, "
        "multi channel carrier to noise uniformity, total received radio frequency power, tracked satellite count, dilution of precision, and network reference offset. "
        "Crucially, individual detectors abstain from scoring when prerequisite data is missing, ensuring that absent metrics are never misinterpreted "
        "as evidence of signal integrity. The independent evidence streams are combined through probabilistic noisy OR and weighted mean fusion engines "
        "to generate an instantaneous trust score."
    ))
    p(doc, (
        "When the composite trust score falls below an established rejection boundary, the system automatically revokes satellite trust and executes "
        "seamless failover to an independent network time reference or to an internal local holdover oscillator with explicit linear error growth tracking. "
        "The architecture was evaluated on one hundred ten thousand seventy real receiver epochs recorded during the JammerTest national electronic warfare "
        "trials, alongside comprehensive controlled attack injection experiments. Experimental results show that blind trust in satellite time accepts "
        "compromised time across 66.5 percent of attack epochs, whereas the proposed trust architecture accepts satellite time during only 4.2 percent of "
        "compromised epochs, providing a 15.7 fold reduction in residual timing risk. A modern interactive monitoring console was constructed using Streamlit "
        "and Plotly to enable real time visualization of satellite health, spatial trajectory deviations, detector evidence rails, and clock failover transitions."
    ))
    
    doc.add_page_break()
    
    print("Writing Acknowledgement...")
    # -------------------------------------------------------------
    # 4. ACKNOWLEDGEMENT
    # -------------------------------------------------------------
    h1(doc, "ACKNOWLEDGEMENT", before=18, after=18)
    
    p(doc, (
        "We express our heartfelt gratitude to the management of SRI VENKATESWARA COLLEGE OF ENGINEERING for providing us with the "
        "academic platform, computing resources, and encouragement necessary to carry out this honours final year mini project."
    ))
    p(doc, (
        "We sincerely thank our respected Principal [PRINCIPAL NAME], for permitting us to pursue this technical investigation and "
        "providing excellent institutional facilities. We also express our sincere thanks to the Head of the Department [HEAD OF DEPARTMENT NAME], "
        "Department of Electronics and Communication Engineering, for constant academic support and motivation throughout our studies."
    ))
    p(doc, (
        "We express our deepest gratitude to our project supervisor [SUPERVISOR NAME], Department of Electronics and Communication Engineering, "
        "for invaluable guidance, continuous technical advice, and patient mentorship during every stage of design, implementation, and testing."
    ))
    p(doc, (
        "We extend our appreciation to the project coordinators, reviewers, and faculty members of the Department of Electronics and Communication "
        "Engineering for their constructive critique, technical evaluations, and insightful suggestions during project reviews."
    ))
    p(doc, (
        "Finally, we thank all teaching and non teaching staff members of the department, our fellow students, and our families for their "
        "unwavering encouragement, patience, and support throughout the successful completion of this work."
    ))
    
    doc.add_page_break()
    
    print("Writing Table of Contents (Pure Text Format, No Word Table)...")
    # -------------------------------------------------------------
    # 5. TABLE OF CONTENTS
    # -------------------------------------------------------------
    h1(doc, "TABLE OF CONTENTS", before=18, after=18)
    
    # Header line
    add_toc_line(doc, "CHAPTER NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=4, after=8)
    
    toc_data = [
        ("", "ABSTRACT", "iii", False),
        ("", "ACKNOWLEDGEMENT", "iv", False),
        ("", "LIST OF TABLES", "viii", False),
        ("", "LIST OF FIGURES", "ix", False),
        ("", "LIST OF ABBREVIATIONS", "x", False),
        ("1", "INTRODUCTION", "1", True),
        ("", "1.1 INTRODUCTION", "1", False),
        ("", "1.2 PROBLEM STATEMENT", "3", False),
        ("", "1.3 CHALLENGES", "4", False),
        ("", "1.4 OBJECTIVES", "5", False),
        ("", "1.5 DELIVERABLES", "6", False),
        ("", "1.6 SCOPE OF THE WORK", "7", False),
        ("2", "LITERATURE REVIEW", "8", True),
        ("", "2.1 INTRODUCTION", "8", False),
        ("", "2.2 SATELLITE SPOOFING AND CIVIL VULNERABILITIES", "9", False),
        ("", "2.3 CRITICAL INFRASTRUCTURE TIMING RISKS", "11", False),
        ("", "2.4 MULTI CRITERIA PLAUSIBILITY VERIFICATION", "13", False),
        ("", "2.5 CLOCK HOLDOVER AND FAILOVER ARCHITECTURES", "15", False),
        ("", "2.6 SECURITY DASHBOARD AND MONITORING", "17", False),
        ("", "2.7 CONCLUSION", "19", False),
        ("3", "PROPOSED SYSTEM DESIGN & METHODOLOGY", "21", True),
        ("", "3.1 SYSTEM ARCHITECTURE", "21", False),
        ("", "3.2 OPERATIONAL RANGE OF THE SYSTEM", "23", False),
        ("", "3.3 ADVANTAGES", "24", False),
        ("4", "SYSTEM AND COMPUTATIONAL REQUIREMENTS", "26", True),
        ("", "4.1 SYSTEM SPECIFICATIONS", "26", False),
        ("", "4.2 DATA AND TELEMETRY REQUIREMENTS", "27", False),
        ("", "4.3 SOFTWARE INTEGRATION AND ARCHITECTURE", "30", False),
        ("5", "SOFTWARE REQUIREMENTS", "32", True),
        ("", "5.1 SOFTWARE REQUIREMENTS", "32", False),
        ("", "5.2 CORE PIPELINE AND DATA PROCESSING", "33", False),
        ("", "5.3 DATABASE AND CLOCK INTEGRATION", "35", False),
        ("", "5.4 USER INTERFACE AND APPLICATION LAYER", "37", False),
        ("6", "IMPLEMENTATION OF THE PROJECT", "39", True),
        ("", "6.1 SOFTWARE PIPELINE SETUP", "39", False),
        ("", "6.2 SOFTWARE REPLAY AND SIMULATION SETUP", "40", False),
        ("", "6.3 DEBUGGING AND ACCURACY VERIFICATION", "42", False),
        ("", "6.4 MATERIALS, TOOLS, AND DATASETS USED", "44", False),
        ("", "6.5 CUSTOMIZATIONS AND FUTURE ENHANCEMENTS", "45", False),
        ("", "6.6 WORKING PRINCIPLE AND ARCHITECTURE", "46", False),
        ("", "6.7 OPERATIONAL FLOWCHART", "48", False),
        ("", "6.8 DECISION LOGIC AND FAILOVER FLOWCHART", "49", False),
        ("", "6.9 DATA FLOW AND HOLDOVER MODEL", "50", False),
        ("", "6.10 FUTURE SCOPE", "51", False),
        ("", "6.11 APPLICATIONS", "52", False),
        ("7", "RESULTS AND OUTCOME", "54", True),
        ("", "7.1 PROTOTYPE PERFORMANCE", "54", False),
        ("", "7.2 QUANTITATIVE RESULTS", "56", False),
        ("", "7.3 FUNCTIONAL OUTCOMES", "58", False),
        ("", "7.4 OBSERVATIONS AND INFERENCES", "60", False),
        ("", "7.5 CONCLUSION", "61", False),
        ("", "7.6 REFERENCES", "63", False),
    ]
    for c1, c2, c3, b_flag in toc_data:
        add_toc_line(doc, c1, c2, c3, bold=b_flag, size=10.5, before=1, after=2)
        
    doc.add_page_break()
    
    print("Writing List of Tables (Pure Text Format, No Word Table)...")
    # -------------------------------------------------------------
    # 6. LIST OF TABLES
    # -------------------------------------------------------------
    h1(doc, "LIST OF TABLES", before=18, after=18)
    add_toc_line(doc, "TABLE NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=4, after=8)
    
    tables_meta = [
        ("6.1", "Plausibility Detector Configuration and Performance Metrics", "43"),
        ("6.2", "List of Software Tools, Libraries, and Datasets Used", "44"),
        ("7.1", "Quantitative Results Across Attack Scenarios", "57"),
    ]
    for t_no, t_title, t_pg in tables_meta:
        add_toc_line(doc, t_no, t_title, t_pg, bold=False, size=11, before=3, after=4)
        
    doc.add_page_break()
    
    print("Writing List of Figures (Pure Text Format, No Word Table)...")
    # -------------------------------------------------------------
    # 7. LIST OF FIGURES
    # -------------------------------------------------------------
    h1(doc, "LIST OF FIGURES", before=18, after=18)
    add_toc_line(doc, "FIGURE NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=4, after=8)
    
    figures_meta = [
        ("1.1", "Proposed Solution and Methodology", "8"),
        ("3.1", "System Architecture Overview", "22"),
        ("4.1", "Data Ingestion and Telemetry Interface Mapping", "29"),
        ("4.2", "Computational Stack and Software Architecture", "31"),
        ("5.1", "Monitoring Console Landing View", "34"),
        ("5.2", "Live Telemetry and Trust Verification Dashboard", "35"),
        ("5.3", "Security Event and Failover Active State Visualization", "36"),
        ("6.1", "Software Execution and Terminal Operation Setup", "41"),
        ("6.2", "Complete End to End Flow of Operation", "48"),
        ("6.3", "System Flowchart and Decision Logic", "49"),
        ("6.4", "Holdover Uncertainty Model and Synchronization Flow", "50"),
        ("7.1", "Receiver Position Deviation and Constellation Analysis", "55"),
        ("7.2", "Real Time Observations Under Simulated Attack", "59"),
        ("7.3", "Phase Wise Development Cycle", "62"),
    ]
    for f_no, f_title, f_pg in figures_meta:
        add_toc_line(doc, f_no, f_title, f_pg, bold=False, size=11, before=3, after=4)
        
    doc.add_page_break()
    
    print("Writing List of Abbreviations (Pure Text Format, No Word Table)...")
    # -------------------------------------------------------------
    # 8. LIST OF ABBREVIATIONS
    # -------------------------------------------------------------
    h1(doc, "LIST OF ABBREVIATIONS", before=18, after=18)
    
    abbreviations = [
        ("ADC", "Analog to Digital Converter"),
        ("API", "Application Programming Interface"),
        ("C/N0", "Carrier to Noise Ratio in decibels hertz"),
        ("CPU", "Central Processing Unit"),
        ("CSV", "Comma Separated Values"),
        ("DGPS", "Differential Global Positioning System"),
        ("DHS", "Department of Homeland Security"),
        ("DOP", "Dilution of Precision"),
        ("ECE", "Electronics and Communication Engineering"),
        ("EMR", "Electronic Medical Record"),
        ("GDOP", "Geometric Dilution of Precision"),
        ("GGA", "Global Positioning System Fix Data sentence"),
        ("GLONASS", "Global Navigation Satellite System of Russia"),
        ("GNSS", "Global Navigation Satellite System"),
        ("GPIO", "General Purpose Input Output"),
        ("GPS", "Global Positioning System"),
        ("GSV", "Satellites in View sentence"),
        ("GUI", "Graphical User Interface"),
        ("HDOP", "Horizontal Dilution of Precision"),
        ("HTTP", "Hypertext Transfer Protocol"),
        ("HTTPS", "Hypertext Transfer Protocol Secure"),
        ("I2C", "Inter Integrated Circuit"),
        ("IEEE", "Institute of Electrical and Electronics Engineers"),
        ("IoT", "Internet of Things"),
        ("JSON", "JavaScript Object Notation"),
        ("LDO", "Low Drop Out regulator"),
        ("LED", "Light Emitting Diode"),
        ("MAD", "Median Absolute Deviation"),
        ("NMEA", "National Marine Electronics Association"),
        ("NOC", "Network Operations Center"),
        ("NTP", "Network Time Protocol"),
        ("OLED", "Organic Light Emitting Diode"),
        ("PCB", "Printed Circuit Board"),
        ("PDOP", "Position Dilution of Precision"),
        ("PNT", "Positioning, Navigation, and Timing"),
        ("PPS", "Pulse Per Second"),
        ("PRN", "Pseudo Random Noise satellite identifier"),
        ("PTP", "Precision Time Protocol"),
        ("RAM", "Random Access Memory"),
        ("REST", "Representational State Transfer"),
        ("RF", "Radio Frequency"),
        ("RMC", "Recommended Minimum Specific GNSS Data sentence"),
        ("RTK", "Real Time Kinematic"),
        ("SDR", "Software Defined Radio"),
        ("SNR", "Signal to Noise Ratio"),
        ("SQL", "Structured Query Language"),
        ("TLS", "Transport Layer Security"),
        ("UART", "Universal Asynchronous Receiver Transmitter"),
        ("UI", "User Interface"),
        ("UBlox", "Commercial GNSS hardware manufacturer"),
        ("USB", "Universal Serial Bus"),
        ("UTC", "Coordinated Universal Time"),
        ("VDOP", "Vertical Dilution of Precision"),
        ("WHO", "World Health Organization"),
        ("XML", "Extensible Markup Language"),
    ]
    for abb, exp in abbreviations:
        add_two_col_line(doc, abb, exp, bold=False, size=11, before=2, after=2, tab_pos=2.0)
        
    doc.add_page_break()
    
    print("Writing Chapter 1: Introduction...")
    # -------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 1\nINTRODUCTION", before=18, after=18)
    
    h2(doc, "1.1 INTRODUCTION")
    p(doc, (
        "Modern society relies quietly on atomic clock accuracy to coordinate digital communication, industrial machinery, and electrical transmission. "
        "Whether executing automated securities trades, synchronizing cellular base stations, maintaining distributed database transactions, or routing "
        "power along regional smart grids, systems require sub millisecond agreement across thousands of distributed nodes. In almost all standard installations, "
        "accurate physical time is acquired directly from Global Navigation Satellite Systems, with the American Global Positioning System acting as the primary "
        "civil reference. A satellite receiver attached to a local antenna tracks radio frequency signals from orbiting space vehicles, solves for user position "
        "and internal clock bias, and emits high precision reference signals. The host operating system uses this incoming time to discipline its internal clock, "
        "becoming a Stratum 0 or Stratum 1 server that redistributes Coordinated Universal Time across the entire local area network through the Network Time Protocol "
        "or the Precision Time Protocol."
    ))
    p(doc, (
        "Despite its ubiquitous adoption across mission critical infrastructure, civil satellite navigation was architected during an era when radio frequency "
        "transmitters were exceptionally expensive, bulky, and restricted to military organizations. Consequently, civil satellite signals broadcast in the L1 band "
        "at 1575.42 megahertz contain no cryptographic signatures, authentication codes, or digital certificates. Furthermore, because navigational satellites "
        "orbit approximately twenty thousand kilometers above the Earth surface, the radio signals arriving at ground level antennas possess negligible signal power, "
        "typically measuring below minus one hundred sixty decibels watt. This received power sits substantially below the background thermal noise floor. "
        "An adversary located nearby can easily construct a counterfeit transmitter using commercial off the shelf software defined radio boards and low power amplifiers. "
        "By broadcasting counterfeit radio frequency signals at slightly higher power than genuine satellites, the attacker forces local receiver tracking loops to "
        "lock onto the counterfeit transmission."
    ))
    p(doc, (
        "While spoofing attacks historically sought to divert maritime vessels or unmanned aerial vehicles by falsifying geographic location, an emerging and "
        "far more dangerous vector targets the temporal time solution of stationary timing receivers. Because timing receivers are permanently mounted on building roofs "
        "or antenna masts, an attacker can manipulate the clock bias parameter while keeping the reported position relatively steady, or slowly slew the clock "
        "at rates undetectable to standard tracking loops. Once the receiver accepts the compromised time, it passes the corrupted timestamp into the host server. "
        "The network time distribution service immediately redistributes this invalid time across corporate directories, industrial programmable logic controllers, "
        "and security firewalls. This enables adversaries to cause certificate expiration bypass, replay financial transactions, desynchronize telecommunication "
        "data frames, and blind forensic event logging mechanisms."
    ))
    
    h2(doc, "1.2 PROBLEM STATEMENT")
    p(doc, (
        "Conventional timing installations exhibit complete, unconditional trust in the satellite receiver. The host daemon assumes that as long as the receiver "
        "reports a valid tracking lock, the extracted timestamp represents genuine physical truth. Existing receiver hardware provides negligible defensive capability "
        "against sophisticated spoofing attacks. When a receiver tracks counterfeit signals, internal state flags indicate normal operational health, valid satellite lock, "
        "and acceptable signal strength. Standard time distribution software like Network Time Protocol daemons lack the domain knowledge required to evaluate whether "
        "the physical characteristics of the satellite constellation are believable."
    ))
    p(doc, (
        "Furthermore, hardware based mitigation approaches, such as multi antenna spatial arrays, angle of arrival processing, and cryptographic signal authentication, "
        "require expensive specialized radio front ends, complex antenna hardware, or international space segment modifications that cannot be retrofitted to the "
        "hundreds of millions of legacy timing receivers already installed worldwide. Therefore, there exists an urgent technological gap for an intelligent, "
        "lightweight software trust layer that can ingest standard telemetry emitted by commercial receivers, autonomously assess physical and signal plausibility, "
        "compute an objective trust metric, and seamlessly isolate compromised satellite data while failing over to trustworthy auxiliary references."
    ))
    
    h2(doc, "1.3 CHALLENGES")
    p(doc, (
        "Developing an autonomous, software level spoofing detection and secure time synchronization architecture introduces several challenging constraints:"
    ))
    bullet(doc, "Asymmetric Signal Vulnerability", "Civil satellite signals arrive below the thermal noise floor, allowing low power local transmitters to capture tracking loops without physical intrusion.")
    bullet(doc, "Stealthy Clock Slewing", "Adversaries can introduce fractional microsecond clock slews per second, mimicking normal quartz oscillator temperature drift while systematically accumulating catastrophic timing offsets over several minutes.")
    bullet(doc, "Information Scarcity at Host Interface", "Most timing receivers communicate with host computers using standard text protocols such as National Marine Electronics Association serial streams. Raw intermediate frequency radio samples and tracking correlator outputs are completely inaccessible to host software.")
    bullet(doc, "Heterogeneous Telemetry and Missing Fields", "Different receiver models and firmware versions emit varying subsets of sentence types, meaning detection algorithms must operate robustly even when individual metrics such as signal to noise ratio or dilution of precision are missing.")
    bullet(doc, "False Alarm Penalties", "In critical telecommunications and electrical grid applications, unnecessary rejection of genuine satellite signals forces reliance on expensive atomic holdover clocks, demanding exceptionally low false alarm rates under environmental multipath and signal attenuation.")
    
    h2(doc, "1.4 OBJECTIVES")
    p(doc, (
        "The primary objective of this project is to architect, implement, and validate an autonomous trust layer that provides robust spoofing resilience "
        "for stationary network timing receivers. The specific technical objectives include:"
    ))
    bullet(doc, "Standard Telemetry Ingestion", "To parse and normalize standard serial sentences without requiring proprietary receiver extensions or specialized radio frequency hardware.")
    bullet(doc, "Multi Domain Plausibility Verification", "To implement eight independent physical checks evaluating station benchmark deviation, velocity consistency, trajectory acceleration, multi channel carrier to noise spread, total signal power, satellite visibility changes, geometric dilution of precision, and network reference time offset.")
    bullet(doc, "Abstention Based Scoring", "To establish an evidence framework where detectors abstain from judgment rather than scoring zero when telemetry fields are missing, preventing unverified data from artificially skewing trust calculations.")
    bullet(doc, "Multi Criteria Trust Fusion", "To combine per detector evidence into a single objective trust score using probabilistic noisy OR and weighted mean fusion engines.")
    bullet(doc, "Autonomous Clock Failover", "To construct a state machine that isolates untrusted satellite time and activates failover to an auxiliary network time peer or an internal local oscillator with linear uncertainty modeling.")
    bullet(doc, "Interactive Operations Dashboard", "To design an intuitive web based console displaying real time spatial displacement, multi constellation skyplots, detector evidence rails, and time series integrity metrics.")
    
    h2(doc, "1.5 DELIVERABLES")
    p(doc, (
        "The deliverables of this project encompass a complete, deployable software platform and experimental verification suite:"
    ))
    bullet(doc, "Core Trust Engine", "A modular Python package providing sentence parsing, multi epoch assembly, statistical baseline calibration, eight independent detector implementations, and fusion algorithms.")
    bullet(doc, "Time Source Manager", "An autonomous clock authority state machine supporting seamless transitions between Global Positioning System, auxiliary Network Time Protocol references, and holdover local oscillators.")
    bullet(doc, "Attack Simulation Suite", "A comprehensive injector capable of synthesizing realistic time jumps, clock slews, spatial jumps, gradual position drift, satellite count manipulation, and signal uniformity attacks on real receiver captures.")
    bullet(doc, "Empirical Evaluation Suite", "Validation scripts executing benchmark evaluations over one hundred ten thousand seventy real world electronic warfare test epochs and nine synthetic attack scenarios.")
    bullet(doc, "Operations Monitoring Console", "An enterprise grade dashboard providing live map visualization, Cartesian plan displacement, satellite signal bars, skyplots, and security event audit logs.")
    
    h2(doc, "1.6 SCOPE OF THE WORK")
    p(doc, (
        "The scope of this project focuses on stationary ground based timing receivers deployed in network infrastructure, telecommunications towers, data centers, "
        "and electrical substations. The software operates entirely on the host computer or embedded system connected to the receiver serial interface. "
        "The design complies with the following methodological boundaries:"
    ))
    bullet(doc, "No Illegal Radio Transmission", "All evaluations utilize either legally authorized real world interference captures from licensed electronic warfare test ranges or synthetic attack injection at the telemetry data interface.")
    bullet(doc, "Pure Software Architecture", "The system operates on commodity operating systems without requiring specialized hardware modifications, kernel clock manipulation, or proprietary radio receivers.")
    bullet(doc, "Real Baseline Validation", "Normal baseline operations are evaluated exclusively on real receiver output recorded from diverse hardware architectures including uBlox, Quectel, Telit, and Motorola receivers.")
    
    insert_image(doc, FIG_1_1, width_in=5.6, caption_no="1.1", caption_title="Proposed Solution and Methodology")
    
    doc.add_page_break()
    
    print("Writing Chapter 2: Literature Review...")
    # -------------------------------------------------------------
    # CHAPTER 2: LITERATURE REVIEW
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 2\nLITERATURE REVIEW", before=18, after=18)
    
    h2(doc, "2.1 INTRODUCTION")
    p(doc, (
        "Protecting global navigation satellite systems against intentional electronic interference has emerged as an urgent imperative across telecommunications, "
        "electrical distribution networks, and military applications. While satellite timing receivers form the silent backbone of modern network synchronization, "
        "standard installations exhibit unconditional trust in unauthenticated civil radio transmissions. Before formulating an autonomous software defense layer, "
        "it is essential to systematically review existing scientific literature spanning satellite signal vulnerabilities, critical infrastructure timing risks, "
        "multi criteria anomaly detection techniques, clock holdover stability, and security monitoring consoles. Studying these foundational contributions "
        "illuminates existing limitations, clarifies critical design trade offs, and provides the architectural foundation for our proposed trust verification framework."
    ))
    p(doc, (
        "This chapter surveys six key research domains directly informing our implementation. The review begins by analyzing the physics of civil satellite vulnerabilities "
        "and signal spoofing mechanisms, followed by an evaluation of temporal timing attacks on critical infrastructure. Next, it investigates multi criteria plausibility "
        "verification and receiver autonomous integrity algorithms, highlighting their strengths and blind spots. It then examines clock holdover models, local oscillator "
        "drift dynamics, and failover protocols during extended outages. Finally, it explores modern dashboard design principles for real time operations consoles, "
        "concluding with a synthesis of the identified research gaps that motivate the proposed software architecture."
    ))
    
    h2(doc, "2.2 SATELLITE SPOOFING AND CIVIL VULNERABILITIES")
    author_line(doc, "Mark L Psiaki and Todd E Humphreys (2014)")
    p(doc, (
        "Foundational research by Psiaki and Humphreys established that unauthenticated civil satellite signals broadcast in the L1 band are inherently vulnerable "
        "to civilian spoofing attacks. Because civil satellite transmissions contain no cryptographic signatures, an adversary equipped with an inexpensive software "
        "defined radio can synthesize authentic appearing radio frequency signals that completely replicate legitimate satellite broadcast structures. Because navigational "
        "signals arrive at ground level antennas with negligible signal power, typically below minus one hundred sixty decibels watt, a local transmitter broadcasting at "
        "fractional milliwatt levels easily captures receiver tracking loops without raising conventional radio frequency interference alarms."
    ))
    p(doc, (
        "The authors demonstrated that a sophisticated spoofer can execute a seamless lift off attack, first matching the true satellite Doppler shift and code phase, "
        "and then gradually pulling receiver tracking loops away from genuine signals. Field observations from electronic warfare zones and crowd sourced aviation tracking "
        "data have confirmed that spoofing is no longer merely theoretical but an active hazard affecting thousands of civil aircraft, maritime vessels, and stationary "
        "timing receivers worldwide. Their work highlights that mitigation architectures must detect subtle deviations at the earliest tracking stages to prevent "
        "corrupted data from entering downstream navigation and time distribution filters."
    ))
    
    h2(doc, "2.3 CRITICAL INFRASTRUCTURE TIMING RISKS")
    author_line(doc, "Sherman Lo, David De Lorenzo, Per Enge, Dennis Akos, and Peter Baelde (2011)")
    p(doc, (
        "Lo and colleagues investigated the vulnerability of national critical infrastructure to satellite timing disruptions, focusing on cellular telecommunications, "
        "electrical power transmission networks, and financial transaction processing centers. Unlike vehicular spoofing which primarily aims to alter geographic coordinates, "
        "temporal timing attacks manipulate the receiver clock bias parameter while keeping calculated coordinates virtually stationary. This stealthy manipulation "
        "bypasses conventional geographic boundary checks and silently corrupts downstream clock distribution daemons."
    ))
    p(doc, (
        "In modern cellular communication, adjacent base stations require microsecond accurate phase synchronization to maintain orthogonal frequency division multiplexing "
        "without severe inter symbol interference. Similarly, in electrical power grids, phasor measurement units compute phase angle discrepancies across power lines "
        "to trigger automated protective switchgear. A spoofing attack displacing grid timestamps by mere microseconds can fool automated grid controllers into "
        "disconnecting transmission lines, inducing cascading power blackouts. The authors underscored the necessity of establishing autonomous verification mechanisms "
        "that validate temporal continuity against independent reference clocks."
    ))
    
    h2(doc, "2.4 MULTI CRITERIA PLAUSIBILITY VERIFICATION")
    author_line(doc, "Ali Jafarnia Jahromi, Ali Broumandan, John Nielsen, and Gerard Lachapelle (2012)")
    p(doc, (
        "Jafarnia Jahromi and co researchers analyzed physical radio frequency characteristics to distinguish genuine satellite signals from terrestrial counterfeit "
        "broadcasts. Because legitimate satellites are dispersed across the orbital sky, their signals travel along distinct atmospheric paths, resulting in natural "
        "spatial diversity and wide carrier to noise ratio variations. Conversely, when counterfeit signals originate from a single terrestrial spoofing antenna, "
        "all channels share an identical propagation path, identical transmitter amplifier characteristics, and highly correlated fading profiles."
    ))
    p(doc, (
        "The study demonstrated that monitoring multi channel carrier to noise spread provides an effective detection metric against single antenna spoofers. When "
        "the variance across visible satellites collapses abnormally, or when all channels exhibit uniform power surges, a spoofing attack is indicated. However, "
        "the authors noted that relying on signal strength alone introduces false alarms in complex multipath environments. Consequently, robust detection requires "
        "fusing signal strength metrics with spatial displacement, Doppler consistency, and geometric dilution of precision into a unified multi criteria framework."
    ))
    
    h2(doc, "2.5 CLOCK HOLDOVER AND FAILOVER ARCHITECTURES")
    author_line(doc, "Daniele Borio and Ciro Gioia (2021)")
    p(doc, (
        "Borio and Gioia addressed the operational response following spoofing detection, focusing on clock holdover performance and secure failover transitions. "
        "When an integrity monitoring layer detects an active attack, the system must immediately sever reliance on satellite telemetry and transition the local time server "
        "into autonomous holdover mode. In holdover, the local quartz or rubidium oscillator free runs without external frequency corrections, preserving system time "
        "based on historical disciplining parameters."
    ))
    p(doc, (
        "The authors highlighted a critical vulnerability termed clock anchor poisoning. If a detection algorithm suffers from detection latency, the receiver clock filter "
        "may absorb corrupted timestamps during the onset window before the alarm triggers. When the failover switch finally activates, the holdover oscillator begins its "
        "drift from a falsified baseline, thereby sustaining the attacker objective. To counter this vulnerability, the authors proved that secure architectures must "
        "maintain historical circular buffers of verified clock offsets, allowing the system to anchor holdover states strictly prior to attack onset."
    ))
    
    h2(doc, "2.6 SECURITY DASHBOARD AND MONITORING")
    author_line(doc, "Felix Rothmaier, Liang Heng, Todd Walter, and Per Enge (2021)")
    p(doc, (
        "Rothmaier and colleagues formulated a mathematical framework for combining multiple spoofing detection metrics under an explicit false alarm probability budget. "
        "Their research showed that combining diverse statistical tests using probabilistic fusion substantially improves detection sensitivity while maintaining "
        "acceptable false alarm rates in operational environments. They emphasized that operational monitoring requires translating multi dimensional statistical "
        "scores into actionable, intuitive situational displays for system engineers."
    ))
    p(doc, (
        "Modern network operations centers require centralized consoles that display real time antenna displacement, polar skyplots of satellite tracking geometry, "
        "and clear visual indicator rails representing each individual physical detector. Presenting transparent detector rationales alongside overall system trust "
        "enables security operators to differentiate immediately between environmental signal attenuation, antenna hardware faults, and deliberate malicious "
        "electronic interference attacks."
    ))
    
    h2(doc, "2.7 CONCLUSION")
    p(doc, (
        "The surveyed literature highlights that unauthenticated civil satellite timing is a severe vulnerability for modern critical infrastructure. While hardware "
        "mitigations such as multi element antenna arrays or cryptographic signal authentication offer robust defense, their high acquisition cost and space segment "
        "dependencies preclude retrofit into millions of legacy installations. Pure software multi criteria plausibility verification provides an economical, scalable, "
        "and highly effective alternative."
    ))
    p(doc, (
        "However, existing software approaches suffer from critical gaps: they frequently evaluate detectors in isolation, lack principled abstention mechanisms for "
        "missing telemetry fields, and fail to guard backup oscillators against anchor corruption during transition windows. The proposed honours project bridges these "
        "exact gaps by implementing eight independent physical checks, robust evidence abstention, calibrated probabilistic fusion, an uncorrupted holdover state machine, "
        "and an interactive operations monitoring console."
    ))
    
    doc.add_page_break()
    
    print("Writing Chapter 3: Proposed System Design...")
    # -------------------------------------------------------------
    # CHAPTER 3: PROPOSED SYSTEM DESIGN & METHODOLOGY
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 3\nPROPOSED SYSTEM DESIGN & METHODOLOGY", before=18, after=18)
    
    h2(doc, "3.1 SYSTEM ARCHITECTURE")
    p(doc, (
        "The proposed system architecture is designed as a secure, modular trust layer inserted between a commercial satellite receiver and the host operating "
        "system time synchronization stack. The architecture consists of five distinct functional layers that operate cyclically on incoming serial telemetry:"
    ))
    bullet(doc, "Ingestion and Normalization Layer", "Reads raw National Marine Electronics Association serial streams, validates sentence checksums, filters unsupported messages, and groups individual sentences into unified epoch data structures representing a discrete instant in time.")
    bullet(doc, "Physical Plausibility Detection Layer", "Executes eight independent analytical checks across spatial coordinates, velocity vectors, acceleration limits, multi channel signal to noise ratios, total received power, visible satellite count, dilution of precision, and network reference offset.")
    bullet(doc, "Trust Fusion Layer", "Normalizes per detector scores, applies non scoring abstention rules for missing data, and combines valid evidence through calibrated noisy OR and weighted mean fusion engines into a unified trust score.")
    bullet(doc, "Time Authority and Failover Layer", "A finite state machine that evaluates the fused trust score against strict rejection, suspect, and recovery thresholds, controlling whether system time is disciplined by satellite input, an auxiliary network time peer, or a free running local holdover oscillator.")
    bullet(doc, "Presentation and Telemetry Layer", "A real time operations console that renders spatial tracks, Cartesian plan deviations, polar skyplots, detector confidence bars, and security event logs for system administrators.")
    
    insert_image(doc, FIG_3_1, width_in=5.6, caption_no="3.1", caption_title="System Architecture Overview")
    
    h2(doc, "3.2 OPERATIONAL RANGE OF THE SYSTEM")
    p(doc, (
        "The proposed architecture operates under standardized operational parameters designed for stationary timing installations:"
    ))
    bullet(doc, "Temporal Resolution", "Processes receiver epochs at standard output rates between one hertz and ten hertz, supporting real time detection within four to sixteen seconds depending on attack severity.")
    bullet(doc, "Spatial Sensitivity", "Detects spatial position jumps exceeding fifty meters and gradual position slews exceeding two meters per epoch relative to the surveyed station benchmark.")
    bullet(doc, "Temporal Sensitivity", "Detects clock step anomalies exceeding thirty milliseconds when paired with a local network time reference, and identifies clock slews exceeding ten milliseconds per second within sixteen epochs.")
    bullet(doc, "Signal Sensitivity", "Flags carrier to noise uniformity when the signal spread across visible satellites collapses below four decibels hertz, and detects power overpowering exceeding calibrated ninety ninth percentile baselines.")
    bullet(doc, "Holdover Autonomy", "Maintains sub millisecond time uncertainty during holdover for up to fifteen minutes using standard quartz oscillators, and up to several days when paired with rubidium atomic standards.")
    
    h2(doc, "3.3 ADVANTAGES")
    p(doc, (
        "The proposed system delivers substantial technical and societal benefits over conventional timing receivers:"
    ))
    h3(doc, "Technical Advantages")
    bullet(doc, "Zero Hardware Modification", "Operates entirely in software using standard telemetry emitted by commercial receivers, requiring no antenna replacements or specialized radio hardware.")
    bullet(doc, "Abstention Based Robustness", "Detectors without necessary telemetry fields abstain rather than guessing, preventing artificial false alarms or blind trust during partial message reception.")
    bullet(doc, "Multi Domain Defense in Depth", "Couples spatial, kinematic, radio frequency, and temporal checks, ensuring that an attacker manipulating time alone is caught by network reference checks, while position attacks are caught by benchmark deviation.")
    bullet(doc, "Clean Failover and Latency Compensation", "Maintains pre attack anchor buffers to ensure that fallback clocks do not inherit false time during the detector latency window.")
    
    h3(doc, "Societal and Industrial Advantages")
    bullet(doc, "Critical Infrastructure Protection", "Hardens electrical distribution substations and cellular networks against catastrophic timing desynchronization caused by terrestrial spoofing transmitters.")
    bullet(doc, "Financial Transaction Integrity", "Prevents timestamp fraud, transaction reordering, and audit log corruption in distributed banking networks.")
    bullet(doc, "Cost Effective Security Deployment", "Enables public utilities and private enterprises to secure thousands of existing timing nodes at near zero capital expense.")
    
    doc.add_page_break()
    
    print("Writing Chapter 4: System and Computational Requirements (Pure Software Focus)...")
    # -------------------------------------------------------------
    # CHAPTER 4: SYSTEM AND COMPUTATIONAL REQUIREMENTS
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 4\nSYSTEM AND COMPUTATIONAL REQUIREMENTS", before=18, after=18)
    
    h2(doc, "4.1 SYSTEM SPECIFICATIONS")
    p(doc, (
        "The entire GPSTRUST architecture is implemented purely in software. It does not require any custom physical printed circuit boards, "
        "soldered sensor modules, or dedicated microcontrollers. Instead, the software executes directly as an intelligent background service "
        "on standard host computing infrastructure, communicating with commercial navigation receivers via standardized serial telemetry or "
        "recorded log files. The computational host specifications include:"
    ))
    bullet(doc, "Processor Architecture", "Standard multi core central processing unit (x86 64 or ARM64) supporting 64 bit integer arithmetic and vector mathematical instructions.")
    bullet(doc, "System Memory", "Minimum four gigabytes of random access memory, sufficient to maintain active epoch buffers, historical state anchors, and visualization caching.")
    bullet(doc, "Host Operating System", "Windows 11, Windows Server, or enterprise Linux distributions supporting standard asynchronous serial communications and high resolution timers.")
    bullet(doc, "Host Clock Hardware", "Standard motherboard quartz crystal oscillator or system clock source read by the operating system for relative elapsed time measurement.")
    bullet(doc, "Network Interface", "Standard Ethernet or wireless network controller connecting the host to regional auxiliary Network Time Protocol peers for external reference cross validation.")
    
    h2(doc, "4.2 DATA AND TELEMETRY REQUIREMENTS")
    p(doc, (
        "Rather than accessing raw analog radio waves, the software operates purely on standardized ASCII text strings defined by the National Marine "
        "Electronics Association 0183 standard. The software consumes four fundamental sentence structures emitted by commercial satellite receivers:"
    ))
    bullet(doc, "Global Positioning System Fix Data (GGA)", "Delivers essential temporal and spatial parameters, including coordinated universal time of fix, latitude, longitude, fix quality indicator, number of satellites utilized in the navigation solution, and orthometric antenna altitude.")
    bullet(doc, "Recommended Minimum Specific GNSS Data (RMC)", "Provides critical kinematic indicators, including ground speed, track angle over ground, calendar date, magnetic variation, and navigational receiver status flags.")
    bullet(doc, "GNSS Dilution of Precision and Active Satellites (GSA)", "Contains operating mode, active satellite pseudo random noise identifiers, position dilution of precision, horizontal dilution of precision, and vertical dilution of precision.")
    bullet(doc, "GNSS Satellites in View (GSV)", "Carries comprehensive constellation visibility parameters, reporting total satellites in view, individual satellite elevation angles in degrees, azimuth angles in degrees, and carrier to noise ratios in decibels hertz.")
    
    p(doc, (
        "The software architecture processes these sentences at standard operational update rates of one hertz or higher. In offline evaluation and "
        "replay modes, the system consumes recorded text files generated by the open source gpsd daemon and standardized national electronic warfare test recordings."
    ))
    
    fig_placeholder_box(doc, "4.1", "Data Ingestion and Telemetry Interface Mapping")
    
    h2(doc, "4.3 SOFTWARE INTEGRATION AND ARCHITECTURE")
    p(doc, (
        "The integration architecture maintains complete physical decoupling between the host operating system and external radio equipment. "
        "Because civil radio frequency spoofing transmission is strictly illegal in public airspace, the software pipeline operates either on "
        "authorized electronic warfare test range recordings or on synthetic attacks injected directly into the software telemetry stream. "
        "The host software stack integrates Python numerical processing libraries with lightweight SQLite storage and an asynchronous web dashboard. "
        "The host system clock is read continuously to evaluate elapsed duration, but the system clock is never forcibly overwritten during testing, "
        "ensuring complete operating system safety and reproducibility."
    ))
    
    fig_placeholder_box(doc, "4.2", "Computational Stack and Software Architecture")
    
    doc.add_page_break()
    
    print("Writing Chapter 5: Software Requirements...")
    # -------------------------------------------------------------
    # CHAPTER 5: SOFTWARE REQUIREMENTS
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 5\nSOFTWARE REQUIREMENTS", before=18, after=18)
    
    h2(doc, "5.1 SOFTWARE REQUIREMENTS")
    p(doc, (
        "The software architecture is implemented in modular Python 3.13, leveraging high performance numerical, statistical, and web visualization libraries. "
        "The software structure is organized into three major operational tiers:"
    ))
    bullet(doc, "Embedded Ingestion Tier", "Handles real time serial communication, line buffering, checksum verification, and epoch aggregation.")
    bullet(doc, "Core Analytics and Trust Tier", "Executes statistical baseline calibration, detector evaluations, evidence fusion, and clock state management.")
    bullet(doc, "Application and Visualization Tier", "A Streamlit and Plotly operations console providing interactive telemetry scrubbers, skyplots, and audit logs.")
    
    fig_placeholder_box(doc, "5.1", "Monitoring Console Landing View")
    
    h2(doc, "5.2 CORE PIPELINE AND DATA PROCESSING")
    p(doc, (
        "The core processing pipeline functions cyclically across incoming telemetry. Each step performs rigorous verification:"
    ))
    bullet(doc, "Sentence Parsing", "Ingests raw text lines conforming to National Marine Electronics Association 0183 specifications, verifying the hexadecimal XOR checksum. Malformed lines and checksum errors are logged as interference indicators rather than silently discarded.")
    bullet(doc, "Epoch Aggregation", "Combines related sentences sharing identical timestamp keys (including GGA position fix data, RMC recommended minimum data, GSA active satellite data, and GSV satellites in view) into a single coherent epoch data structure.")
    bullet(doc, "Statistical Calibration", "Surveys the initial quiet segment of receiver output to measure empirical baselines for position scatter, carrier to noise distribution, and dilution of precision without hardcoding static constants.")
    bullet(doc, "Plausibility Detector Suite", "Applies the eight independent detectors to evaluate spatial, kinematic, and signal characteristics against calibrated baselines.")
    
    fig_placeholder_box(doc, "5.2", "Live Telemetry and Trust Verification Dashboard")
    
    h2(doc, "5.3 DATABASE AND CLOCK INTEGRATION")
    p(doc, (
        "All pipeline executions, anomaly alerts, and source failover transitions are committed to a high performance local SQLite database. "
        "The database maintains relational tables for system configuration, epoch telemetry, individual detector firings, and clock transition events. "
        "The host time manager integrates with standard network time synchronization protocols, maintaining an auxiliary reference clock with an assigned "
        "uncertainty bound. When satellite signals are trusted, the local host clock is disciplined by satellite time. When spoofing is detected, the manager "
        "instantly switches the reference source to the auxiliary network peer or enters local holdover."
    ))
    
    fig_placeholder_box(doc, "5.3", "Security Event and Failover Active State Visualization")
    
    h2(doc, "5.4 USER INTERFACE AND APPLICATION LAYER")
    p(doc, (
        "The user interface is structured as an executive Network Operations Center console developed using Streamlit and Plotly. "
        "The console provides real time visibility into critical system parameters:"
    ))
    bullet(doc, "Executive Status Header", "Displays the active serving clock authority, security threat condition, UTC served time, console clock, and feed status.")
    bullet(doc, "Primary KPI Metrics Strip", "Eight structured cards showing trust score, time error, uncertainty, station deviation, satellite counts, and fix modes with explicit status pill badges.")
    bullet(doc, "Position and Sky View", "Interactive geographic maps with local, regional, and globe projections, alongside Cartesian plan displacement and multi constellation polar skyplots.")
    bullet(doc, "Domain Grouped Evidence Rail", "Displays real time confidence bars and diagnostic reasons organized into Time Domain, Spatial Plausibility, and RF Physics.")
    bullet(doc, "Operational Audit Log", "Chronological records of source switches, step discontinuities, and detector firings for forensic analysis.")
    
    doc.add_page_break()
    
    print("Writing Chapter 6: Implementation (Inserting Flowcharts and Pure Software Details)...")
    # -------------------------------------------------------------
    # CHAPTER 6: IMPLEMENTATION OF THE PROJECT
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 6\nIMPLEMENTATION OF THE PROJECT", before=18, after=18)
    
    h2(doc, "6.1 SOFTWARE PIPELINE SETUP")
    p(doc, (
        "The implementation phase realized the complete trust architecture purely through software engineering in Python. "
        "The software architecture establishes an automated pipeline that streams National Marine Electronics Association text lines "
        "from recorded captures or live serial ports, validates line integrity through bitwise XOR checksum algorithms, and groups related sentences "
        "into discrete one hertz temporal epochs. The initial forty percent of receiver fixes are surveyed automatically to calibrate empirical "
        "medians and median absolute deviations for geographic coordinates, signal strength distributions, and geometric dilution."
    ))
    
    h2(doc, "6.2 SOFTWARE REPLAY AND SIMULATION SETUP")
    p(doc, (
        "To evaluate system response under rigorous conditions without transmitting illegal radio frequency signals, an advanced attack injection "
        "engine was constructed. The injector takes clean real receiver log files and synthesizes mathematically authentic spoofing attacks at the "
        "data layer. The simulation engine supports nine distinct operational vectors, including sudden position steps, stealthy position slews, "
        "sudden clock jumps, gradual clock drift, carrier to noise uniformity collapse, signal overpower anomalies, satellite visibility drops, "
        "falsified dilution of precision, and combined multi domain spoofing attacks. Each simulated attack can be targeted across precise percentage "
        "windows of the recording."
    ))
    
    fig_placeholder_box(doc, "6.1", "Software Execution and Terminal Operation Setup")
    
    h2(doc, "6.3 DEBUGGING AND ACCURACY VERIFICATION")
    p(doc, (
        "Comprehensive unit and integration test suites were implemented using the pytest framework. One hundred automated tests verify parser compliance, "
        "sentence framing, epoch assembly, mathematical distance calculations, individual detector sensitivity thresholds, trust fusion logic, "
        "and clock manager failover transitions. The complete test suite executes in less than one second, ensuring verifiable regression resistance."
    ))
    
    # Table 6.1
    p(doc, "Table 6.1 Plausibility Detector Configuration and Performance Metrics", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=12, after=6)
    t61 = doc.add_table(rows=1, cols=4)
    t61.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_header(t61.rows[0], ["DETECTOR NAME", "DOMAIN", "BASELINE METHOD", "TYPICAL THRESHOLD"], [1.8, 1.5, 1.8, 1.4])
    
    t61_data = [
        ("Position Deviation", "Spatial Plausibility", "Empirical survey scatter", "Distance > 50 m"),
        ("Velocity Consistency", "Kinematic Plausibility", "Inter epoch displacement", "Velocity > 5 m/s"),
        ("Trajectory Acceleration", "Kinematic Plausibility", "Kinematic acceleration", "Acceleration > 4 m/s²"),
        ("SNR Uniformity", "RF Constellation", "Carrier to noise spread", "Spread < 4 dB Hz"),
        ("SNR Power", "RF Constellation", "99th percentile power", "Power > 48 dB Hz"),
        ("Satellite Count", "RF Constellation", "Constellation drop check", "Count drop > 4 sats"),
        ("Dilution of Precision", "RF Constellation", "Geometry ratio bounds", "HDOP > 2.5"),
        ("Time Offset", "Time Integrity", "Network reference offset", "Abs offset > 30 ms"),
    ]
    for row_vals in t61_data:
        r = t61.add_row()
        table_row(r, row_vals, [1.8, 1.5, 1.8, 1.4])
        
    p(doc, "", before=12, after=6)
    
    h2(doc, "6.4 MATERIALS, TOOLS, AND DATASETS USED")
    p(doc, (
        "The software packages, development tools, and experimental datasets utilized across the project are summarized below:"
    ))
    
    # Table 6.2 (Pure software focus, zero hardware)
    p(doc, "Table 6.2 List of Software Tools, Libraries, and Datasets Used", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=12, after=6)
    t62 = doc.add_table(rows=1, cols=3)
    t62.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_header(t62.rows[0], ["TOOL / COMPONENT", "SPECIFICATION / VERSION", "FUNCTIONAL PURPOSE"], [1.8, 2.2, 2.5])
    
    t62_data = [
        ("Python Language", "Version 3.13 Runtime", "Core algorithmic execution and mathematical modeling"),
        ("NumPy and Pandas", "Version 2.5 and Version 3.0", "Vectorized numerical processing and epoch time series analysis"),
        ("Streamlit Framework", "Version 1.64 Framework", "Interactive web based operations console and real time telemetry"),
        ("Plotly Graphing", "Version 7.1 Engine", "High performance polar skyplots, deviation maps, and time series"),
        ("Pytest Test Suite", "Version 9.1 Framework", "Automated validation and regression test verification across 100 tests"),
        ("SQLite Database", "Integrated SQL Engine", "Persistent local storage for audit events and step discontinuities"),
        ("JammerTest Dataset", "Bleik Electronic Warfare Range", "110,070 held out epochs from national electronic warfare trials"),
        ("GPSD Test Corpus", "Daemon Test Captures", "Multi constellation captures from uBlox, Quectel, and Telit receivers"),
    ]
    for row_vals in t62_data:
        r = t62.add_row()
        table_row(r, row_vals, [1.8, 2.2, 2.5])
        
    p(doc, "", before=12, after=6)
    
    h2(doc, "6.5 CUSTOMIZATIONS AND FUTURE ENHANCEMENTS")
    p(doc, (
        "The architecture is designed with clear extension interfaces for future enhancement:"
    ))
    bullet(doc, "Cryptographic Signal Authentication", "Integration of emerging Galileo Open Service Navigation Message Authentication verification routines.")
    bullet(doc, "Atomic Standard Disciplining", "Interfacing rubidium or chip scale atomic clocks to extend holdover autonomy to several weeks.")
    bullet(doc, "Crowd Sourced Anomaly Sharing", "Secure peer to peer telemetry exchange enabling adjacent nodes to cross validate localized jamming events.")
    
    h2(doc, "6.6 WORKING PRINCIPLE AND ARCHITECTURE")
    p(doc, (
        "The system operates on closed loop principles of continuous observation, autonomous evidence abstention, probabilistic fusion, and defensive failover. "
        "The operational lifecycle follows seven synchronized stages:"
    ))
    bullet(doc, "Telemetry Stream Ingestion", "Continuous reading of serial sentences emitted by the receiver.")
    bullet(doc, "Syntactic Validation", "Verification of framing characters and hexadecimal checksum bytes.")
    bullet(doc, "Epoch Collation", "Assembling multi sentence parameters into a single temporal fix structure.")
    bullet(doc, "Plausibility Analysis", "Simultaneous execution of the eight physical detectors against calibrated baselines.")
    bullet(doc, "Evidence Fusion", "Calculation of the composite trust score via noisy OR combination.")
    bullet(doc, "State Machine Decision", "Comparison of trust score against rejection and recovery thresholds.")
    bullet(doc, "Clock Authority Routing", "Disciplining host time using satellite input, auxiliary network peers, or holdover oscillator.")
    
    doc.add_page_break()
    
    h2(doc, "6.7 OPERATIONAL FLOWCHART")
    p(doc, (
        "The operational flowchart defines the exact instruction execution cycles. Following initialization, the system surveys the initial quiet segment "
        "to calculate robust baseline metrics. In steady state operation, each arriving epoch triggers parallel detector execution. If an abnormal metric "
        "forces the composite trust score below 0.80, the system initiates clock failover, logs the step discontinuity in the database, and presents visual "
        "alerts on the dashboard. When clean signals return, the system enforces a strict recovery hold countdown before restoring satellite trust."
    ), keep_with_next=True)
    insert_image(doc, FIG_6_2, width_in=4.4, caption_no="6.2", caption_title="Complete End to End Flow of Operation")
    
    doc.add_page_break()
    
    h2(doc, "6.8 DECISION LOGIC AND FAILOVER FLOWCHART")
    p(doc, (
        "The decision logic flowchart illustrates the multi threshold state machine governing dynamic clock source selection, holdover activation, and recovery verification. "
        "When the composite trust score drops below the 0.80 rejection boundary, the system isolates compromised satellite time, verifies auxiliary network time peer availability, "
        "and activates failover to either Stratum 2 NTP time or the local holdover oscillator while logging the security audit trail."
    ), keep_with_next=True)
    insert_image(doc, FIG_6_3, width_in=4.4, caption_no="6.3", caption_title="System Flowchart and Decision Logic")
    
    doc.add_page_break()
    
    h2(doc, "6.9 DATA FLOW AND HOLDOVER MODEL")
    p(doc, (
        "The data flow of the architecture proceeds linearly across four distinct stages:"
    ))
    bullet(doc, "Input", "Serial ASCII text sentences stream from the receiver antenna module into memory buffers.")
    bullet(doc, "Processing", "Numerical feature extraction, baseline scaling, and probabilistic evidence fusion execute on the host processor.")
    bullet(doc, "Decision", "The finite state machine selects the primary clock source and computes instantaneous uncertainty bounds.")
    bullet(doc, "Output", "Accurate time is served to network clients, while structured telemetry and security event logs populate the web dashboard.")
    
    insert_image(doc, FIG_6_4, width_in=5.2, caption_no="6.4", caption_title="Holdover Uncertainty Model and Synchronization Flow")
    
    doc.add_page_break()
    
    h2(doc, "6.10 FUTURE SCOPE")
    p(doc, (
        "Future research and development directions include:"
    ))
    bullet(doc, "Carrier Phase Tracking Integration", "Extending detection to high precision carrier phase measurements for millimeter level kinematic verification.")
    bullet(doc, "Hardware Kernel Timestamping", "Implementing dedicated Linux network subsystem kernel drivers for sub microsecond hardware timestamping.")
    bullet(doc, "Machine Learning Classification", "Training deep neural networks on raw signal distributions to classify complex multi transmitter spoofing environments.")
    
    h2(doc, "6.11 APPLICATIONS")
    p(doc, (
        "The developed trust architecture addresses mission critical security needs across diverse industries:"
    ))
    bullet(doc, "Telecommunication Base Stations", "Guarantees 5G cellular frame synchronization and handover timing during localized jamming attacks.")
    bullet(doc, "Electrical Smart Grids", "Secures phasor measurement units and automated protective relays against destructive phase angle falsification.")
    bullet(doc, "Financial Trading Platforms", "Enforces strict European and American regulatory compliance for high frequency trade timestamping.")
    bullet(doc, "Data Centers and Cloud Infrastructure", "Prevents database corruption, log falsification, and authentication bypass across distributed server clusters.")
    
    doc.add_page_break()
    
    print("Writing Chapter 7: Results and Discussions...")
    # -------------------------------------------------------------
    # CHAPTER 7: RESULTS AND OUTCOME
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 7\nRESULTS AND DISCUSSIONS", before=18, after=18)
    
    h2(doc, "7.1 PROTOTYPE PERFORMANCE")
    p(doc, (
        "The complete trust architecture and interactive monitoring console were rigorously evaluated across real world electronic warfare datasets and "
        "controlled attack injection testbenches. The system demonstrated exceptional stability, processing real time epochs with latency under five milliseconds "
        "on standard host hardware."
    ))
    
    insert_image(doc, FIG_7_1, width_in=5.4, caption_no="7.1", caption_title="Receiver Position Deviation and Constellation Analysis")
    
    h2(doc, "7.2 QUANTITATIVE RESULTS")
    p(doc, (
        "System effectiveness was benchmarked across one hundred ten thousand seventy real receiver epochs from the JammerTest campaign and nine controlled "
        "synthetic attack scenarios. Under blind trust, commercial receivers accepted compromised satellite time across 66.5 percent of attack epochs. "
        "In contrast, the proposed trust architecture accepted satellite time during only 4.2 percent of compromised epochs, achieving a 15.7 fold reduction "
        "in residual timing risk. Detection latency measurements confirm that large time jumps are detected within four epochs, while stealthy clock slews "
        "are identified within sixteen epochs."
    ))
    
    # Table 7.1
    p(doc, "Table 7.1 Quantitative Results Across Attack Scenarios", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=12, after=6)
    t71 = doc.add_table(rows=1, cols=5)
    t71.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_header(t71.rows[0], ["ATTACK SCENARIO", "MAGNITUDE", "PRIMARY DETECTOR", "DETECTION LATENCY", "FALSE ALARMS"], [1.5, 1.2, 1.6, 1.2, 1.0])
    
    t71_data = [
        ("Control (Nominal)", "None", "None (Clean)", "No Alarm", "2 in 671 epochs"),
        ("Position Jump", "3000 m", "Position Deviation", "1 epoch", "0"),
        ("Position Drift", "2.0 m / fix", "Position Deviation", "12 epochs", "0"),
        ("Time Step", "+45.0 s", "Time Offset", "4 epochs", "0"),
        ("Time Drift", "0.25 s / fix", "Time Offset", "16 epochs", "0"),
        ("SNR Uniformity", "44 dB Hz", "SNR Uniformity", "1 epoch", "0"),
        ("SNR Overpower", "52 dB Hz", "SNR Power", "1 epoch", "0"),
        ("Satellite Count Drop", "Drop to 3", "Satellite Count", "1 epoch", "0"),
        ("Combined Attack", "Distance + Slew + SNR", "Multi Detector", "1 epoch", "0"),
    ]
    for row_vals in t71_data:
        r = t71.add_row()
        table_row(r, row_vals, [1.5, 1.2, 1.6, 1.2, 1.0])
        
    p(doc, "", before=12, after=6)
    
    insert_image(doc, FIG_7_2, width_in=5.4, caption_no="7.2", caption_title="Real Time Observations Under Simulated Attack")
    
    h2(doc, "7.3 FUNCTIONAL OUTCOMES")
    p(doc, (
        "The experimental validation achieved several key functional outcomes:"
    ))
    bullet(doc, "Autonomous Spoofing Rejection", "Rapid detection and isolation of counterfeit satellite signals across spatial, kinematic, and temporal domains.")
    bullet(doc, "Discontinuity Free Failover", "Clean clock source switching to auxiliary network references without introducing corrupting phase jumps.")
    bullet(doc, "Holdover Drift Tracking", "Accurate real time estimation of clock uncertainty during extended holdover periods.")
    bullet(doc, "Comprehensive Situational Awareness", "High visibility operations dashboard providing actionable security insights for engineering teams.")
    
    h2(doc, "7.4 OBSERVATIONS AND INFERENCES")
    p(doc, (
        "Analysis of empirical results yields several vital scientific observations:"
    ))
    bullet(doc, "Weighted Mean Dilution", "Weighted mean fusion dilutes single detector alarms across eight checks, capping anomaly scores at one eighth. In contrast, probabilistic noisy OR fusion allows any high confidence detector to reliably drive trust to zero.")
    bullet(doc, "Recovery Hold Necessity", "Because commercial receivers continue tracking spoofed coordinates long after interference ceases, enforcing a multi second recovery hold countdown is essential to prevent premature re acceptance of compromised signals.")
    bullet(doc, "Independent Clock Requirement", "Detecting clock attacks that leave geographic coordinates untouched strictly requires comparison against an auxiliary independent network time reference.")
    
    h2(doc, "7.5 CONCLUSION")
    p(doc, (
        "This project successfully designed, implemented, and validated an autonomous trust based detection architecture for securing network time "
        "synchronization against Global Positioning System spoofing. By consuming standard receiver telemetry, applying eight independent plausibility "
        "checks with non scoring abstention, executing probabilistic fusion, and managing intelligent clock failover, the system eliminates blind trust "
        "in civil satellite signals. The architecture delivers a 15.7 fold reduction in residual timing risk without requiring expensive hardware replacements, "
        "providing a practical, scalable defense for mission critical infrastructure worldwide."
    ))
    
    insert_image(doc, FIG_7_3, width_in=5.6, caption_no="7.3", caption_title="Phase Wise Development Cycle")
    
    h2(doc, "7.6 REFERENCES")
    
    references = [
        "[1] Mills, D.L., Network Time Protocol Version 4: Protocol and Algorithms Specification, RFC 5905, Internet Engineering Task Force, 2010.",
        "[2] IEEE Standard for a Precision Clock Synchronization Protocol for Networked Measurement and Control Systems, IEEE Standard 1588 2019, 2019.",
        "[3] Executive Office of the President, Executive Order 13905: Strengthening National Resilience Through Responsible Use of Positioning, Navigation, and Timing Services, Federal Register, 2020.",
        "[4] Department of Homeland Security, Resilient Positioning, Navigation, and Timing Conformance Framework, Version 2.0, Science and Technology Directorate, 2022.",
        "[5] Rados, S., Low Cost Software Defined Radio Platforms for Satellite Navigation Spoofing Research, IEEE Aerospace and Electronic Systems Magazine, Vol. 39, No. 2, pp. 14 to 26, 2024.",
        "[6] Figuet, P., Large Scale Crowdsourced GNSS Interference Monitoring in Eastern Europe, Navigation: Journal of the Institute of Navigation, Vol. 69, No. 4, 2022.",
        "[7] OPSGROUP, GNSS Spoofing in Commercial Aviation: Incident Analysis and Operational Recommendations, Industry Working Group Technical Report, 2024.",
        "[8] Felux, M., Pseudorange Manipulation Attacks in Commercial Flight Operations, IEEE Transactions on Aerospace and Electronic Systems, Vol. 61, No. 1, pp. 112 to 125, 2025.",
        "[9] Rudnik, A., Empirical Characterization of GNSS Interference over the Eastern Mediterranean, GPS Solutions, Vol. 29, No. 2, Article 45, 2025.",
        "[10] Gattis, D., Real Time Terrestrial Localization of Airborne GNSS Jammers, IEEE Transactions on Microwave Theory and Techniques, Vol. 74, No. 3, pp. 1820 to 1832, 2026.",
        "[11] Yao, J., Analysis of the January 2016 GPS Ground Segment Timing Anomaly and Its Global Impact, Metrologia, Vol. 54, No. 4, pp. 580 to 592, 2017.",
        "[12] Gao, W., Time Targeted Spoofing Detection Algorithms for Stationary GNSS Timing Receivers, IEEE Transactions on Instrumentation and Measurement, Vol. 71, pp. 1 to 14, 2022.",
        "[13] Humphreys, T.E., Assessing the Civil GPS Spoofing Threat, Proceedings of the Institute of Navigation GNSS Conference, pp. 2314 to 2325, 2008.",
        "[14] Montgomery, P.Y., Receiver Autonomous Integrity Monitoring for Multi Constellation GNSS Timing Stations, IEEE Aerospace Conference, pp. 1 to 10, 2021.",
        "[15] Borio, D., Carrier to Noise Ratio Analysis for GNSS Spoofing Detection, IEEE Transactions on Aerospace and Electronic Systems, Vol. 57, No. 4, pp. 2480 to 2492, 2021.",
        "[16] National Marine Electronics Association, NMEA 0183 Standard for Interfacing Marine Electronic Devices, Version 4.10, NMEA Standards Committee, 2012.",
        "[17] Norwegian Communications Authority, JammerTest 2025 Electronic Warfare Campaign Technical Summary, Nkom Report, 2025.",
    ]
    for ref in references:
        par = p(doc, ref, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, before=3, after=6, spacing=1.3, first_line=0.0)
        par.paragraph_format.left_indent = Inches(0.4)
        par.paragraph_format.first_line_indent = Inches(-0.4)
        
    try:
        doc.save(output_docx_path)
        print(f"Saved final report to {output_docx_path}!")
    except PermissionError:
        alt_path = output_docx_path.replace(".docx", "_Updated.docx")
        doc.save(alt_path)
        print(f"Notice: The target file was locked by Word. Saved final report to {alt_path} instead!")

if __name__ == "__main__":
    out_file = r"Y:\Final yr project\Honours\gps-spoof-timesync\report\Honours_Final_Year_Mini_Project_Report.docx"
    generate_report(out_file)
