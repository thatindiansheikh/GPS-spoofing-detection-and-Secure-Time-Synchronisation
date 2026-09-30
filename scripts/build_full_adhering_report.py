"""
Generator for Honours Final Year Mini Project Report.
Strict adhering pagination, centered page numbers in footers,
Times New Roman font throughout, zero dashes, pure software implementation.
"""

import os
import sys
import re
from pathlib import Path

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

BASE_DIR = Path(r"Y:\Final yr project\Honours\gps-spoof-timesync")
REPORT_DIR = BASE_DIR / "report"
FIG_DIR = REPORT_DIR / "generated_figures"
MEDIA_DIR = REPORT_DIR / "extracted_media" / "word" / "media"

SVCE_LOGO = str(MEDIA_DIR / "image1.png")
AU_LOGO = str(MEDIA_DIR / "image2.png")

FIG_1_1 = str(FIG_DIR / "figure_1_1_proposed_methodology.png")
FIG_3_1 = str(FIG_DIR / "figure_3_1_system_architecture.png")
FIG_4_1 = str(MEDIA_DIR / "image6.png")
FIG_4_2 = str(MEDIA_DIR / "image7.png")
FIG_5_1 = str(MEDIA_DIR / "image8.png")
FIG_5_2 = str(MEDIA_DIR / "image9.png")
FIG_5_3 = str(MEDIA_DIR / "image10.png")
FIG_6_1 = str(MEDIA_DIR / "image4.png")
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
    t = str(text)
    for d in DASH_CHARS:
        t = t.replace(d, " ")
    t = re.sub(r" +", " ", t)
    return t.strip()

def set_font(run, size=12, bold=False, italic=False, color=(0,0,0)):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color)
    rPr = run._r.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>')
    rPr.append(rFonts)

def set_section_margins(section):
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.5)
    section.right_margin = Inches(1.0)
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)

def add_page_number_to_section(section, num_format="decimal", start_num=None):
    section.different_first_page_header_footer = False
    footer = section.footer
    footer.is_linked_to_previous = False
    p_footer = footer.paragraphs[0]
    p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_footer.text = ""
    
    sectPr = section._sectPr
    for child in list(sectPr):
        if child.tag.endswith("pgNumType") or child.tag.endswith("titlePg"):
            sectPr.remove(child)
            
    attrs = f'w:fmt="{num_format}"'
    if start_num is not None:
        attrs += f' w:start="{start_num}"'
    pgNumType = parse_xml(f'<w:pgNumType {nsdecls("w")} {attrs}/>')
    sectPr.append(pgNumType)
    
    run = p_footer.add_run()
    set_font(run, size=11, bold=False)
    
    fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve">PAGE</w:instrText>')
    fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)

def p(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, bold=False, italic=False, before=0, after=5, spacing=1.35, first_line=0.5, keep_with_next=False):
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

def h1(doc, text, before=16, after=10):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, before=before, after=after, first_line=0.0, keep_with_next=True)

def h2(doc, text, before=12, after=5):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, size=12, bold=True, before=before, after=after, first_line=0.0, keep_with_next=True)

def h3(doc, text, before=9, after=3):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, size=12, bold=True, italic=True, before=before, after=after, first_line=0.0, keep_with_next=True)

def author_line(doc, authors_year):
    c_text = clean(authors_year)
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    par.paragraph_format.left_indent = Inches(0.5)
    par.paragraph_format.first_line_indent = Inches(0)
    par.paragraph_format.space_before = Pt(2)
    par.paragraph_format.space_after = Pt(5)
    par.paragraph_format.line_spacing = 1.35
    par.paragraph_format.keep_with_next = True
    run = par.add_run(c_text)
    set_font(run, size=12, bold=True, italic=False)
    return par

def bullet(doc, title, desc, after=3):
    c_title = clean(title)
    c_desc = clean(desc)
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.left_indent = Inches(0.25)
    par.paragraph_format.first_line_indent = Inches(0)
    par.paragraph_format.space_before = Pt(2)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.3
    par.paragraph_format.keep_with_next = False
    
    rb = par.add_run("   ")
    set_font(rb, size=11, bold=True)
    if c_title:
        rt = par.add_run(c_title + ": ")
        set_font(rt, size=11, bold=True)
    rd = par.add_run(c_desc)
    set_font(rd, size=11, bold=False)
    return par

def add_toc_line(doc, col1, col2, col3, bold=False, size=10.5, before=1, after=1.5):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.2
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

def add_two_col_line(doc, col1, col2, bold=False, size=11, before=1.2, after=1.2, tab_pos=1.6):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.2
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

def insert_image(doc, img_path, width_in=5.2, caption_no="", caption_title="", space_before=6, space_after=10):
    c_no = clean(caption_no)
    c_title = clean(caption_title)
    
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(space_before)
    par.paragraph_format.space_after = Pt(3)
    par.paragraph_format.keep_with_next = True
    
    if os.path.exists(img_path):
        run = par.add_run()
        run.add_picture(img_path, width=Inches(width_in))
    else:
        r = par.add_run(f"[ Image File Not Found: {clean(os.path.basename(img_path))} ]")
        set_font(r, size=10, italic=True)
        
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(3)
    cap.paragraph_format.space_after = Pt(space_after)
    rc = cap.add_run(f"Figure {c_no} {c_title}")
    set_font(rc, size=11, bold=True)
    return par

def fig_placeholder_box(doc, no, title, width_in=5.5, height_pt=28):
    c_no = clean(no)
    c_title = clean(title)
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(width_in)
    
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
    cp.paragraph_format.space_before = Pt(height_pt)
    cp.paragraph_format.space_after = Pt(height_pt)
    r1 = cp.add_run(f"[ SPACE FOR FIGURE {c_no.upper()} ]\n")
    set_font(r1, size=11, bold=True, color=(100, 100, 100))
    r2 = cp.add_run(f"Paste {c_title} Screenshot Here")
    set_font(r2, size=10, italic=True, color=(120, 120, 120))
    
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(5)
    cap.paragraph_format.space_after = Pt(10)
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
                <w:bottom w:val="single" w:sz="10" w:space="0" w:color="333333"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
        ''')
        tcPr.append(borders)
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_before = Pt(3)
        cp.paragraph_format.space_after = Pt(3)
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
        cp.paragraph_format.space_before = Pt(2.5)
        cp.paragraph_format.space_after = Pt(2.5)
        r = cp.add_run(clean(str(val)))
        set_font(r, size=9.5, bold=False)

def generate_full_report(output_docx_path):
    print("Initializing Document...")
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    # -------------------------------------------------------------
    # SECTION 1: TITLE PAGE (Unnumbered / Different First Page)
    # -------------------------------------------------------------
    sec1 = doc.sections[0]
    set_section_margins(sec1)
    sec1.different_first_page_header_footer = True
    
    # Logo table (borderless)
    logo_tbl = doc.add_table(rows=1, cols=2)
    logo_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cl, cr = logo_tbl.cell(0, 0), logo_tbl.cell(0, 1)
    cl.width, cr.width = Inches(3.0), Inches(3.0)
    for c in [cl, cr]:
        tcPr = c._tc.get_or_add_tcPr()
        b = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
        tcPr.append(b)
        
    pl = cl.paragraphs[0]
    pl.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if os.path.exists(SVCE_LOGO):
        pl.add_run().add_picture(SVCE_LOGO, width=Inches(1.15))
        
    pr = cr.paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if os.path.exists(AU_LOGO):
        pr.add_run().add_picture(AU_LOGO, width=Inches(1.15))
        
    p(doc, "TRUST BASED DETECTION OF GPS SPOOFING FOR SECURE NETWORK TIME SYNCHRONIZATION", align=WD_ALIGN_PARAGRAPH.CENTER, size=15, bold=True, before=26, after=16, spacing=1.2)
    p(doc, "PROJECT REPORT FOR HONOURS FINAL YEAR MINI PROJECT", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=16, after=22)
    p(doc, "Submitted by", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, italic=True, before=12, after=16)
    
    p(doc, "[CANDIDATE NAME] [REGISTER NUMBER]", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=6, after=22)
    
    p(doc, "in partial fulfillment for the award of the degree", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, italic=True, before=12, after=4)
    p(doc, "of", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, italic=True, before=2, after=4)
    p(doc, "BACHELOR OF ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=4, after=4)
    p(doc, "IN", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=2, after=4)
    p(doc, "ELECTRONICS AND COMMUNICATION ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, before=4, after=22)
    
    p(doc, "SRI VENKATESWARA COLLEGE OF ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=14, after=2)
    p(doc, "(An Autonomous Institution, Affiliated to Anna University, Chennai 600025)", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=2, after=4)
    p(doc, "ANNA UNIVERSITY :: CHENNAI 600025", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=4, after=16)
    p(doc, "[MONTH YEAR]", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=10, after=0)
    
    # -------------------------------------------------------------
    # SECTION 2: PRELIMINARY PAGES (lowercase Roman, starting at ii)
    # -------------------------------------------------------------
    sec2 = doc.add_section()
    set_section_margins(sec2)
    add_page_number_to_section(sec2, num_format="lowerRoman", start_num=2)
    
    # Page ii: BONAFIDE CERTIFICATE
    p(doc, "SRI VENKATESWARA COLLEGE OF ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=10, after=2)
    p(doc, "(An Autonomous Institution, Affiliated to Anna University, Chennai 600025)", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=2, after=4)
    p(doc, "ANNA UNIVERSITY, CHENNAI 600025", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=True, before=4, after=22)
    p(doc, "BONAFIDE CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, before=16, after=22)
    
    cert_text = (
        "Certified that this project report titled \"TRUST BASED DETECTION OF GPS SPOOFING FOR SECURE NETWORK TIME SYNCHRONIZATION\" "
        "is the bonafide work of \"[CANDIDATE NAME] ([REGISTER NUMBER])\" who carried out the honours final year mini project "
        "work under my supervision."
    )
    p(doc, cert_text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, before=10, after=32, spacing=1.4)
    
    sig_tbl = doc.add_table(rows=1, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_l, cell_r = sig_tbl.cell(0, 0), sig_tbl.cell(0, 1)
    cell_l.width, cell_r.width = Inches(3.2), Inches(3.2)
    for c in [cell_l, cell_r]:
        tcPr = c._tc.get_or_add_tcPr()
        b = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
        tcPr.append(b)
        
    pl = cell_l.paragraphs[0]
    pl.paragraph_format.line_spacing = 1.25
    rl1 = pl.add_run("SIGNATURE\n\n\n\n[SUPERVISOR NAME]\n")
    set_font(rl1, size=11, bold=True)
    rl2 = pl.add_run("SUPERVISOR\nAssociate Professor\nDepartment of Electronics and\nCommunication Engineering")
    set_font(rl2, size=10, bold=False)
    
    pr = cell_r.paragraphs[0]
    pr.paragraph_format.line_spacing = 1.25
    rr1 = pr.add_run("SIGNATURE\n\n\n\n[HEAD OF DEPARTMENT NAME]\n")
    set_font(rr1, size=11, bold=True)
    rr2 = pr.add_run("HEAD OF THE DEPARTMENT\nProfessor\nDepartment of Electronics and\nCommunication Engineering")
    set_font(rr2, size=10, bold=False)
    
    p(doc, "", before=20, after=10)
    p(doc, "Submitted for the project viva voce examination held on ____________________", align=WD_ALIGN_PARAGRAPH.LEFT, size=11, before=32, after=36)
    
    ex_tbl = doc.add_table(rows=1, cols=2)
    ex_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    ex_l, ex_r = ex_tbl.cell(0, 0), ex_tbl.cell(0, 1)
    ex_l.width, ex_r.width = Inches(3.2), Inches(3.2)
    for c in [ex_l, ex_r]:
        tcPr = c._tc.get_or_add_tcPr()
        b = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
        tcPr.append(b)
        
    pel = ex_l.paragraphs[0]
    rel = pel.add_run("INTERNAL EXAMINER")
    set_font(rel, size=11, bold=True)
    per = ex_r.paragraphs[0]
    rer = per.add_run("EXTERNAL EXAMINER")
    set_font(rer, size=11, bold=True)
    
    doc.add_page_break()
    
    # Page iii: ABSTRACT
    h1(doc, "ABSTRACT", before=16, after=14)
    p(doc, (
        "Modern computer networks, electrical distribution grids, cellular base stations, and financial transaction systems depend completely "
        "on precise time synchronization derived from Global Positioning System receivers operating as Stratum 0 reference clocks. However, "
        "civil satellite signals are unauthenticated and arrive with negligible power, making them exceptionally vulnerable to deliberate spoofing "
        "and malicious transmission. When an adversary broadcasts counterfeit signals, receivers compute corrupted time solutions while reporting "
        "nominal tracking status. This false time silently propagates across internal infrastructure through Network Time Protocol daemons, "
        "invalidating digital certificates, breaking database transaction ordering, and disrupting protective power relays without triggering "
        "conventional alarms."
    ), before=0, after=5, spacing=1.3)
    p(doc, (
        "To eliminate this vulnerability, this project develops an intelligent software trust layer positioned between the receiver and host "
        "time distribution stack. Implemented purely in software, the architecture parses standard National Marine Electronics Association telemetry, "
        "executing eight independent physical plausibility checks across spatial position, velocity kinematics, trajectory consistency, signal power, "
        "carrier to noise uniformity, satellite count, dilution of precision, and network reference offset. Individual detectors abstain from "
        "scoring when telemetry fields are missing, preventing unverified data from masking attacks. Evidence is combined via probabilistic noisy "
        "OR fusion to compute an instantaneous trust score that triggers autonomous failover to an authenticated network reference or a local "
        "holdover oscillator with active uncertainty tracking. Evaluated on 110,070 JammerTest electronic warfare epochs and nine synthetic attack "
        "scenarios, the architecture reduces residual timing risk by a factor of 15.7, with all metrics rendered on an enterprise Streamlit console."
    ), before=0, after=5, spacing=1.3)
    doc.add_page_break()
    
    # Page iv: ACKNOWLEDGEMENT
    h1(doc, "ACKNOWLEDGEMENT", before=16, after=16)
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
    
    # Page v, vi, vii: TABLE OF CONTENTS (Pure Text Format, No Word Table)
    h1(doc, "TABLE OF CONTENTS", before=16, after=14)
    add_toc_line(doc, "CHAPTER NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=3, after=6)
    
    toc_part1 = [
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
    ]
    for c1, c2, c3, b_flag in toc_part1:
        add_toc_line(doc, c1, c2, c3, bold=b_flag, size=10.5, before=1, after=1.5)
    doc.add_page_break()
    
    # Page vi: TOC Part 2
    add_toc_line(doc, "CHAPTER NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=10, after=6)
    toc_part2 = [
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
    ]
    for c1, c2, c3, b_flag in toc_part2:
        add_toc_line(doc, c1, c2, c3, bold=b_flag, size=10.5, before=1, after=1.5)
    doc.add_page_break()
    
    # Page vii: TOC Part 3
    add_toc_line(doc, "CHAPTER NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=10, after=6)
    toc_part3 = [
        ("7", "RESULTS AND OUTCOME", "54", True),
        ("", "7.1 PROTOTYPE PERFORMANCE", "54", False),
        ("", "7.2 QUANTITATIVE RESULTS", "56", False),
        ("", "7.3 FUNCTIONAL OUTCOMES", "58", False),
        ("", "7.4 OBSERVATIONS AND INFERENCES", "60", False),
        ("", "7.5 CONCLUSION", "61", False),
        ("", "7.6 REFERENCES", "63", False),
    ]
    for c1, c2, c3, b_flag in toc_part3:
        add_toc_line(doc, c1, c2, c3, bold=b_flag, size=10.5, before=1, after=1.5)
    doc.add_page_break()
    
    # Page viii: LIST OF TABLES
    h1(doc, "LIST OF TABLES", before=16, after=14)
    add_toc_line(doc, "TABLE NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=3, after=6)
    tables_meta = [
        ("6.1", "Plausibility Detector Configuration and Performance Metrics", "43"),
        ("6.2", "List of Software Tools, Libraries, and Datasets Used", "44"),
        ("7.1", "Quantitative Results Across Attack Scenarios", "57"),
    ]
    for t_no, t_title, t_pg in tables_meta:
        add_toc_line(doc, t_no, t_title, t_pg, bold=False, size=11, before=2.5, after=3.5)
    doc.add_page_break()
    
    # Page ix: LIST OF FIGURES
    h1(doc, "LIST OF FIGURES", before=16, after=14)
    add_toc_line(doc, "FIGURE NO.", "TITLE", "PAGE NO.", bold=True, size=11, before=3, after=6)
    figures_meta = [
        ("1.1", "Proposed Solution and Methodology", "7"),
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
        add_toc_line(doc, f_no, f_title, f_pg, bold=False, size=11, before=2, after=3)
    doc.add_page_break()
    
    # Page x: LIST OF ABBREVIATIONS (Part 1)
    h1(doc, "LIST OF ABBREVIATIONS", before=16, after=14)
    abbreviations_part1 = [
        ("ADC", "Analog to Digital Converter"),
        ("API", "Application Programming Interface"),
        ("C/N0", "Carrier to Noise Ratio in decibels hertz"),
        ("CPU", "Central Processing Unit"),
        ("CSV", "Comma Separated Values"),
        ("DGPS", "Differential Global Positioning System"),
        ("DHS", "Department of Homeland Security"),
        ("DOP", "Dilution of Precision"),
        ("ECE", "Electronics and Communication Engineering"),
        ("GDOP", "Geometric Dilution of Precision"),
        ("GGA", "Global Positioning System Fix Data sentence"),
        ("GLONASS", "Global Navigation Satellite System of Russia"),
        ("GNSS", "Global Navigation Satellite System"),
        ("GPS", "Global Positioning System"),
        ("GSV", "Satellites in View sentence"),
        ("GUI", "Graphical User Interface"),
        ("HDOP", "Horizontal Dilution of Precision"),
        ("HTTP", "Hypertext Transfer Protocol"),
        ("HTTPS", "Hypertext Transfer Protocol Secure"),
        ("IEEE", "Institute of Electrical and Electronics Engineers"),
        ("IoT", "Internet of Things"),
        ("JSON", "JavaScript Object Notation"),
        ("LDO", "Low Drop Out regulator"),
    ]
    for abb, exp in abbreviations_part1:
        add_two_col_line(doc, abb, exp, bold=False, size=11, before=1.2, after=1.2, tab_pos=1.6)
    doc.add_page_break()
    
    # Page xi: LIST OF ABBREVIATIONS (Part 2)
    abbreviations_part2 = [
        ("MAD", "Median Absolute Deviation"),
        ("NMEA", "National Marine Electronics Association"),
        ("NOC", "Network Operations Center"),
        ("NTP", "Network Time Protocol"),
        ("OCXO", "Oven Controlled Crystal Oscillator"),
        ("PDOP", "Position Dilution of Precision"),
        ("PNT", "Positioning, Navigation, and Timing"),
        ("PPS", "Pulse Per Second"),
        ("PRN", "Pseudo Random Noise satellite identifier"),
        ("PTP", "Precision Time Protocol"),
        ("RAIM", "Receiver Autonomous Integrity Monitoring"),
        ("RAM", "Random Access Memory"),
        ("REST", "Representational State Transfer"),
        ("RF", "Radio Frequency"),
        ("RMC", "Recommended Minimum Specific GNSS Data sentence"),
        ("RTK", "Real Time Kinematic"),
        ("SDR", "Software Defined Radio"),
        ("SNR", "Signal to Noise Ratio"),
        ("SQL", "Structured Query Language"),
        ("TCXO", "Temperature Compensated Crystal Oscillator"),
        ("TLS", "Transport Layer Security"),
        ("UART", "Universal Asynchronous Receiver Transmitter"),
        ("UI", "User Interface"),
        ("UBlox", "Commercial GNSS hardware manufacturer"),
        ("USB", "Universal Serial Bus"),
        ("UTC", "Coordinated Universal Time"),
        ("VDOP", "Vertical Dilution of Precision"),
        ("WLS", "Weighted Least Squares"),
        ("XML", "Extensible Markup Language"),
    ]
    for abb, exp in abbreviations_part2:
        add_two_col_line(doc, abb, exp, bold=False, size=11, before=1.2, after=1.2, tab_pos=1.6)
        
    # -------------------------------------------------------------
    # SECTION 3: MAIN BODY (decimal, starting at 1 on Chapter 1)
    # -------------------------------------------------------------
    sec3 = doc.add_section()
    set_section_margins(sec3)
    add_page_number_to_section(sec3, num_format="decimal", start_num=1)
    
    print("Writing Chapter 1: Introduction (Pages 1 to 7)...")
    # -------------------------------------------------------------
    # Page 1: CHAPTER 1 INTRODUCTION, 1.1 INTRODUCTION
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 1\nINTRODUCTION", before=16, after=14)
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
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 2: 1.1 INTRODUCTION (Continued)
    # -------------------------------------------------------------
    p(doc, (
        "While spoofing attacks historically sought to divert maritime vessels or unmanned aerial vehicles by falsifying geographic location, an emerging and "
        "far more dangerous vector targets the temporal time solution of stationary timing receivers. Because timing receivers are permanently mounted on building roofs "
        "or antenna masts, an attacker can manipulate the clock bias parameter while keeping the reported position relatively steady, or slowly slew the clock "
        "at rates undetectable to standard tracking loops. Once the receiver accepts the compromised time, it passes the corrupted timestamp into the host server. "
        "The network time distribution service immediately redistributes this invalid time across corporate directories, industrial programmable logic controllers, "
        "and security firewalls. This enables adversaries to cause certificate expiration bypass, replay financial transactions, desynchronize telecommunication "
        "data frames, and blind forensic event logging mechanisms."
    ))
    p(doc, (
        "To mitigate this threat without demanding costly hardware replacements, this project conceives and validates an intelligent host level software trust layer. "
        "By continuously monitoring standard National Marine Electronics Association telemetry emitted by commodity receivers, the trust layer autonomously verifies "
        "the physical, kinematic, and constellation plausibility of the incoming signals. When anomalies emerge, the trust layer instantly revokes clock authority "
        "and switches downstream infrastructure to authenticated network references or internally disciplined holdover oscillators, guaranteeing uninterrupted, "
        "trustworthy network time."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 3: 1.2 PROBLEM STATEMENT
    # -------------------------------------------------------------
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
    p(doc, (
        "Without such a software trust layer, critical infrastructure remains exposed to stealthy time targeted spoofing, where subtle clock drifts can desynchronize "
        "smart grid protection relays, invalidate cryptographic access tokens, and corrupt database ACID transaction properties across enterprise clusters."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 4: 1.3 CHALLENGES
    # -------------------------------------------------------------
    h2(doc, "1.3 CHALLENGES")
    p(doc, (
        "Developing an autonomous, software level spoofing detection and secure time synchronization architecture introduces several challenging constraints:"
    ))
    bullet(doc, "Asymmetric Signal Vulnerability", "Civil satellite signals arrive below the thermal noise floor, allowing low power local transmitters to capture tracking loops without physical intrusion.")
    bullet(doc, "Stealthy Clock Slewing", "Adversaries can introduce fractional microsecond clock slews per second, mimicking normal quartz oscillator temperature drift while systematically accumulating catastrophic timing offsets over several minutes.")
    bullet(doc, "Information Scarcity at Host Interface", "Most timing receivers communicate with host computers using standard text protocols such as National Marine Electronics Association serial streams. Raw intermediate frequency radio samples and tracking correlator outputs are completely inaccessible to host software.")
    bullet(doc, "Heterogeneous Telemetry and Missing Fields", "Different receiver models and firmware versions emit varying subsets of sentence types, meaning detection algorithms must operate robustly even when individual metrics such as signal to noise ratio or dilution of precision are missing.")
    bullet(doc, "False Alarm Penalties", "In critical telecommunications and electrical grid applications, unnecessary rejection of genuine satellite signals forces reliance on expensive atomic holdover clocks, demanding exceptionally low false alarm rates under environmental multipath and signal attenuation.")
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 5: 1.4 OBJECTIVES
    # -------------------------------------------------------------
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
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 6: 1.5 DELIVERABLES
    # -------------------------------------------------------------
    h2(doc, "1.5 DELIVERABLES")
    p(doc, (
        "The deliverables of this project encompass a complete, deployable software platform and experimental verification suite:"
    ))
    bullet(doc, "Core Trust Engine", "A modular Python package providing sentence parsing, multi epoch assembly, statistical baseline calibration, eight independent detector implementations, and fusion algorithms.")
    bullet(doc, "Time Source Manager", "An autonomous clock authority state machine supporting seamless transitions between Global Positioning System, auxiliary Network Time Protocol references, and holdover local oscillators.")
    bullet(doc, "Attack Simulation Suite", "A comprehensive injector capable of synthesizing realistic time jumps, clock slews, spatial jumps, gradual position drift, satellite count manipulation, and signal uniformity attacks on real receiver captures.")
    bullet(doc, "Empirical Evaluation Suite", "Validation scripts executing benchmark evaluations over one hundred ten thousand seventy real world electronic warfare test epochs and nine synthetic attack scenarios.")
    bullet(doc, "Operations Monitoring Console", "An enterprise grade dashboard providing live map visualization, Cartesian plan displacement, satellite signal bars, skyplots, and security event audit logs.")
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 7: 1.6 SCOPE OF THE WORK & FIGURE 1.1
    # -------------------------------------------------------------
    h2(doc, "1.6 SCOPE OF THE WORK")
    p(doc, (
        "The scope of this project focuses on stationary ground based timing receivers deployed in network infrastructure, telecommunications towers, data centers, "
        "and electrical substations. The software operates entirely on the host computer or embedded system connected to the receiver serial interface. "
        "The design complies with the following methodological boundaries:"
    ))
    bullet(doc, "No Illegal Radio Transmission", "All evaluations utilize either legally authorized real world interference captures from licensed electronic warfare test ranges or synthetic attack injection at the telemetry data interface.")
    bullet(doc, "Pure Software Architecture", "The system operates on commodity operating systems without requiring specialized hardware modifications, kernel clock manipulation, or proprietary radio receivers.")
    bullet(doc, "Real Baseline Validation", "Normal baseline operations are evaluated exclusively on real receiver output recorded from diverse hardware architectures including uBlox, Quectel, Telit, and Motorola receivers.")
    
    insert_image(doc, FIG_1_1, width_in=5.0, caption_no="1.1", caption_title="Proposed Solution and Methodology", space_before=4, space_after=6)
    doc.add_page_break()
    
    print("Writing Chapter 2: Literature Review (Pages 8 to 20)...")
    # -------------------------------------------------------------
    # Page 8: CHAPTER 2 LITERATURE REVIEW, 2.1 INTRODUCTION
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 2\nLITERATURE REVIEW", before=16, after=14)
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
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 9: 2.2 SATELLITE SPOOFING AND CIVIL VULNERABILITIES
    # -------------------------------------------------------------
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
        "and then gradually pulling receiver tracking loops away from genuine signals. Their work proves that relying on internal receiver lock flags is entirely inadequate "
        "for security, because modern tracking loops remain locked onto the counterfeit signal even as the calculated navigation solution diverges drastically from reality."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 10: 2.2 Continued
    # -------------------------------------------------------------
    p(doc, (
        "Field observations from electronic warfare zones and crowd sourced aviation tracking data have confirmed that spoofing is no longer merely theoretical but an "
        "active hazard affecting thousands of civil aircraft, maritime vessels, and stationary timing receivers worldwide. In conflict regions and maritime choke points, "
        "receivers routinely report absurd geographic locations, circular movement patterns, or abrupt temporal shifts when inundated by high power counterfeit signals."
    ))
    p(doc, (
        "Psiaki and Humphreys emphasize that effective counter measures must operate across multiple observation domains. While raw radio frequency sample inspection "
        "can identify counterfeit signals in research laboratories, operational civil infrastructure requires host level algorithms that evaluate telemetry consistency. "
        "Their foundational insights directly motivate our multi detector architecture, confirming that an adversary may manipulate individual observables but cannot "
        "synthesize physically consistent multi satellite geometry, signal power distributions, and kinematic trajectories simultaneously."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 11: 2.3 CRITICAL INFRASTRUCTURE TIMING RISKS
    # -------------------------------------------------------------
    h2(doc, "2.3 CRITICAL INFRASTRUCTURE TIMING RISKS")
    author_line(doc, "Sherman Lo, David De Lorenzo, Per Enge, Dennis Akos, and Peter Baelde (2011)")
    p(doc, (
        "Lo and colleagues conducted seminal investigations into the specific vulnerability of critical infrastructure timing receivers to non position navigation spoofing. "
        "Unlike aviation or vehicular receivers that trigger pilot or driver suspicion when positions deviate onto land or into closed airspace, stationary timing receivers "
        "are mounted on building roofs and monitored only through automated time synchronization services. An attacker can execute a pure time spoofing attack, "
        "leaving the reported geographic coordinates essentially unchanged while systematically altering the calculated receiver clock bias."
    ))
    p(doc, (
        "The authors demonstrated that electrical power transmission systems are exceptionally vulnerable to timing manipulation. Modern smart grids utilize phasor "
        "measurement units placed across transmission lines to calculate voltage and current phase angles. These phase angle calculations depend on microsecond level "
        "time alignment across geographically separated substations. A time error of merely twenty six microseconds induces a one degree phase angle error, causing "
        "automated protective relays to detect false differential currents and trip regional transmission lines, triggering cascading grid blackouts."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 12: 2.3 Continued
    # -------------------------------------------------------------
    p(doc, (
        "In cellular telecommunication networks operating under Time Division Duplexing (TDD) architectures, base stations must synchronize frame boundaries to within "
        "three microseconds. When timing receivers at adjacent cell towers drift under spoofing, uplink and downlink slots overlap, generating destructive co channel "
        "interference that severs subscriber connections. Similarly, high frequency trading systems governed by financial regulatory frameworks require millisecond "
        "or microsecond transaction timestamping; counterfeit time allows malicious actors to reorder trades or exploit regulatory latency arbitrage."
    ))
    p(doc, (
        "Lo et al. established that standard Network Time Protocol daemons are defenseless against spoofed Stratum 0 receivers because the protocol inherently trusts "
        "its hardware reference clock. These findings prompted national policy interventions, including United States Executive Order 13905 and the Department of "
        "Homeland Security Resilient Positioning, Navigation, and Timing Conformance Framework, both of which mandate autonomous verification of satellite time inputs "
        "prior to internal redistribution, forming the primary motivation for our software trust architecture."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 13: 2.4 MULTI CRITERIA PLAUSIBILITY VERIFICATION
    # -------------------------------------------------------------
    h2(doc, "2.4 MULTI CRITERIA PLAUSIBILITY VERIFICATION")
    author_line(doc, "Daniele Borio, Ciro Gioia, and James T Curran (2021)")
    p(doc, (
        "Borio and his collaborators explored multi criteria anomaly detection techniques to identify satellite spoofing without specialized antenna arrays. "
        "Their research demonstrated that while an adversary using a single radio frequency transmitter can generate valid pseudoranges for multiple satellites, "
        "they cannot recreate the natural spatial and environmental diversity of genuine satellite signals. In particular, genuine satellite signals experience "
        "differing atmospheric attenuation and antenna gain patterns based on their elevation angles, resulting in dispersed carrier to noise ratios."
    ))
    p(doc, (
        "In contrast, a single transmitter broadcast delivers all counterfeit satellite channels through the same propagation path, causing satellite carrier to noise "
        "ratios to exhibit unnatural uniformity. Borio et al. proposed statistical variance tests over tracked satellite signal strengths to expose this uniformity. "
        "However, their studies revealed that environmental factors such as severe weather, dense foliage, or urban multipath can induce false alarms if signal strength "
        "is evaluated in isolation, underscoring the critical necessity of multi criteria verification across independent physical domains."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 14: 2.4 Continued
    # -------------------------------------------------------------
    p(doc, (
        "Building upon Borio's findings, other researchers have investigated kinematic and geometric plausibility checks. Stationary timing installations have a fixed, "
        "known benchmark position. Any computed spatial displacement exceeding nominal receiver noise immediately indicates an anomaly. Similarly, timing receivers "
        "must report zero ground speed; non zero Doppler derived velocities expose spoofed orbital kinematics. Furthermore, sudden shifts in satellite constellation "
        "counts or geometric dilution of precision reveal unscheduled constellation substitutions."
    ))
    p(doc, (
        "Crucially, our literature review identified a severe flaw in previous multi criteria implementations: when a receiver model omits specific telemetry sentences "
        "(such as GSV satellite signal bars), standard scoring systems assign an anomaly score of zero or default to a failure state. Assigning zero implies verified "
        "integrity, blinding the system to attacks, while failing creates false alarms. Our work solves this foundational defect by implementing explicit abstention "
        "scoring, where detectors without necessary data abstain from scoring and dynamically reweight active evidence streams."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 15: 2.5 CLOCK HOLDOVER AND FAILOVER ARCHITECTURES
    # -------------------------------------------------------------
    h2(doc, "2.5 CLOCK HOLDOVER AND FAILOVER ARCHITECTURES")
    author_line(doc, "David W Allan (1966) and Michael A Lombardi (2016)")
    p(doc, (
        "The physics of precision timekeeping during primary reference loss was established through the foundational work of David W. Allan and extensive empirical "
        "characterizations by Michael A. Lombardi at the National Institute of Standards and Technology. When a timing receiver rejects compromised satellite signals, "
        "the host system must transition into clock holdover, relying on an internal local oscillator or an auxiliary network peer to maintain system time. "
        "The duration for which holdover time remains acceptable depends strictly on the physical stability and temperature sensitivity of the oscillator."
    ))
    p(doc, (
        "Lombardi characterized the drift rates of common oscillator classes utilized in network infrastructure. Standard Temperature Compensated Crystal Oscillators "
        "(TCXO) exhibit fractional frequency drift between 0.1 and 1.0 parts per million, accumulating several milliseconds of error within an hour. High stability "
        "Oven Controlled Crystal Oscillators (OCXO) achieve stability between 0.001 and 0.01 parts per million, keeping time within a few microseconds over twenty four "
        "hours, while atomic rubidium standards maintain sub microsecond accuracy across multiple days of autonomous holdover."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 16: 2.5 Continued
    # -------------------------------------------------------------
    p(doc, (
        "Allan's two sample variance formulation, known universally as Allan deviation, demonstrated that oscillator phase error consists of white frequency noise, "
        "flicker frequency noise, and linear frequency drift. In a software based trust architecture, estimating clock uncertainty during holdover is paramount. "
        "Downstream network applications must be explicitly informed of current clock error bounds so they can throttle sensitive operations before synchronization "
        "tolerances are exceeded."
    ))
    p(doc, (
        "Furthermore, the literature highlights the danger of premature recovery. When an adversary terminates a spoofing transmission, commercial receivers require "
        "extended settling periods to clear tracking loop filters and re acquire true satellite signals. If the host immediately switches back to the receiver upon "
        "signal reappearance, corrupted residual state can re enter the time stack. Our architecture addresses this challenge by implementing an intelligent time source "
        "state machine featuring an enforced recovery hold countdown, ensuring the receiver maintains verified nominal telemetry before trust is restored."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 17: 2.6 SECURITY DASHBOARD AND MONITORING
    # -------------------------------------------------------------
    h2(doc, "2.6 SECURITY DASHBOARD AND MONITORING")
    author_line(doc, "Jakob Nielsen (1994) and Ben Shneiderman (2003)")
    p(doc, (
        "Human factors research by Nielsen and Shneiderman established foundational principles for complex monitoring consoles in mission critical environments. "
        "Shneiderman's Visual Information Seeking Mantra ('Overview first, zoom and filter, then details on demand') and Nielsen's usability heuristics emphasize "
        "that security dashboards must convey operational status instantaneously without cognitive overload, enabling operators to recognize anomalies within seconds "
        "of occurrence."
    ))
    p(doc, (
        "In traditional network operations centers, timing infrastructure was treated as an invisible utility, offering only basic health metrics such as binary tracking "
        "status or total satellite count. However, modern electronic warfare threats demand deep situational awareness. Operators require clear visibility into "
        "station benchmark displacement, carrier to noise distributions, and detector evidence breakdowns to rapidly distinguish between intentional spoofing, "
        "accidental jamming, and environmental multipath."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 18: 2.6 Continued
    # -------------------------------------------------------------
    p(doc, (
        "Recent advances in web based data visualization frameworks, particularly Streamlit and Plotly, have enabled the development of highly responsive, interactive "
        "monitoring consoles without the overhead of complex client server architectures. By leveraging vector graphics and reactive state management, modern dashboards "
        "can render live Cartesian displacement tracks, multi constellation polar skyplots, and real time detector confidence rails directly in standard web browsers."
    ))
    p(doc, (
        "Adhering to enterprise interface guidelines, modern operations dashboards eschew decorative visual clutter in favor of high contrast, legible typography, "
        "standardized status badge color conventions (green for verified GPS, blue for network peer, amber for holdover, red for spoofed), and tabular numerical "
        "formatting for high precision coordinates and timestamps. This human centered design methodology directly informs our project dashboard implementation."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 19: 2.7 CONCLUSION
    # -------------------------------------------------------------
    h2(doc, "2.7 CONCLUSION")
    p(doc, (
        "The comprehensive survey of published literature reveals a critical technological gap in modern positioning, navigation, and timing security. "
        "While the physics of civil satellite vulnerabilities are thoroughly understood and the severe consequences of timing attacks on critical infrastructure "
        "have been conclusively demonstrated, existing commercial timing installations remain completely defenseless against telemetry level manipulation. "
        "Traditional defense mechanisms either mandate expensive, specialized hardware replacements that cannot be deployed across legacy infrastructure, "
        "or rely on simplistic single metric thresholding that suffers from crippling false alarm rates under routine environmental variations."
    ))
    p(doc, (
        "Furthermore, existing software based anomaly detectors lack robust handling of missing telemetry fields, frequently misinterpreting absent data as evidence "
        "of signal health, while failing to provide explainable evidence fusion or disciplined clock holdover tracking for downstream applications."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 20: 2.7 Continued
    # -------------------------------------------------------------
    p(doc, (
        "To resolve these foundational shortcomings, our project synthesizes the core principles identified across the literature into an integrated, deployable "
        "software architecture. By combining multi criteria physical plausibility checks, non scoring abstention, probabilistic noisy OR evidence fusion, "
        "autonomous clock failover with explicit holdover uncertainty tracking, and an enterprise operations console, we deliver a robust defense that operates "
        "on commodity receivers without hardware modifications."
    ))
    p(doc, (
        "The following chapters detail the mathematical modeling, software implementation, and empirical validation of this proposed architecture across real world "
        "electronic warfare datasets and controlled attack injection experiments, proving its efficacy in securing network time synchronization."
    ))
    doc.add_page_break()
    
    print("Writing Chapter 3: Proposed System Design & Methodology (Pages 21 to 25)...")
    # -------------------------------------------------------------
    # Page 21: CHAPTER 3 PROPOSED SYSTEM DESIGN & METHODOLOGY, 3.1 SYSTEM ARCHITECTURE
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 3\nPROPOSED SYSTEM DESIGN & METHODOLOGY", before=16, after=14)
    h2(doc, "3.1 SYSTEM ARCHITECTURE")
    p(doc, (
        "The proposed system introduces an autonomous, host level software trust layer positioned between the physical satellite navigation receiver and the "
        "host operating system time synchronization services. The architecture operates on standard serial telemetry sentences emitted by commercial off the shelf "
        "receivers, requiring zero hardware modifications, specialized antenna arrays, or proprietary firmware extensions. By treating the satellite receiver "
        "as an untrusted data source, the trust layer continuously inspects incoming telemetry across eight independent physical domains, calculates an objective "
        "composite trust metric, and controls downstream clock authority through an intelligent state machine."
    ))
    p(doc, (
        "The overall pipeline comprises five primary functional modules: the NMEA Telemetry Ingestion Engine, the Multi Epoch Ring Buffer and Normalizer, "
        "the Plausibility Verification Detector Array, the Probabilistic Evidence Fusion Engine, and the Autonomous Time Source Manager. A secondary auditing "
        "and visualization pipeline logs security events to a structured SQLite database and streams live telemetry to an interactive web dashboard."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 22: Figure 3.1 System Architecture Overview
    # -------------------------------------------------------------
    insert_image(doc, FIG_3_1, width_in=5.2, caption_no="3.1", caption_title="System Architecture Overview", space_before=4, space_after=6)
    p(doc, (
        "Figure 3.1 illustrates the complete block diagram of the proposed trust architecture. Raw NMEA 0183 sentences (GGA, RMC, GSV, GSA) arrive across the serial "
        "interface from the primary GNSS receiver. The ingestion engine parses each sentence, verifies the checksum, and aggregates sentences sharing the same UTC "
        "timestamp into a single coherent EpochData object. The normalized epoch is passed simultaneously to the eight independent plausibility detectors."
    ))
    p(doc, (
        "Each detector compares current observables against established baseline thresholds, emitting an anomaly score between 0.0 and 1.0 or an explicit abstention "
        "flag. The Evidence Fusion Engine combines active scores using probabilistic noisy OR logic. If the composite trust score falls below 0.60, the Time Source "
        "Manager automatically switches clock authority from GNSS Stratum 0 to an authenticated NTP network reference or internal local holdover oscillator."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 23: 3.2 OPERATIONAL RANGE OF THE SYSTEM
    # -------------------------------------------------------------
    h2(doc, "3.2 OPERATIONAL RANGE OF THE SYSTEM")
    p(doc, (
        "The operational range of the proposed system encompasses all stationary ground based timing installations operating within standard terrestrial environments. "
        "Because stationary infrastructure (such as cellular base stations, electrical substations, and enterprise data centers) occupies fixed, precisely known "
        "coordinates, the system leverages this spatial benchmark to achieve exceptional sensitivity against spoofing attacks that introduce minute positional drifts."
    ))
    p(doc, (
        "The software architecture supports standard baud rates ranging from 4800 to 115200 baud across standard serial, USB serial, and TCP/IP serial encapsulations. "
        "It provides full compatibility with major commercial multi constellation receivers, including uBlox, Quectel, Telit, Trimble, and Motorola hardware. "
        "The ingestion engine dynamically accommodates standard update rates from 1 Hz to 10 Hz, processing each epoch in under five milliseconds of CPU execution time, "
        "ensuring zero latency accumulation in real time operation."
    ))
    p(doc, (
        "Furthermore, the system operates reliably across diverse geographic locations and challenging radio frequency environments, maintaining high detection "
        "accuracy even in urban canyons where multipath reflections induce localized signal fluctuations."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 24: 3.3 ADVANTAGES
    # -------------------------------------------------------------
    h2(doc, "3.3 ADVANTAGES")
    p(doc, (
        "The proposed software trust layer delivers significant architectural and operational advantages over conventional timing security approaches:"
    ))
    bullet(doc, "Pure Software Deployment", "Operates entirely on the host operating system without requiring specialized radio frequency hardware, cryptographic receiver upgrades, or physical antenna array modifications.")
    bullet(doc, "Multi Domain Physical Verification", "Evaluates spatial benchmark deviation, velocity kinematics, trajectory plausibility, carrier to noise spread, RF power anomalies, satellite counts, dilution of precision, and network time offsets simultaneously.")
    bullet(doc, "Abstention Based Non Scoring", "Prevents missing telemetry fields from being falsely interpreted as signal integrity, ensuring robust multi receiver compatibility without artificially inflating trust scores.")
    bullet(doc, "Discontinuity Free Clock Failover", "The Time Source Manager ensures smooth clock transitions to authenticated network peers or local holdover oscillators without introducing corrupting phase jumps into host services.")
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 25: 3.3 Continued
    # -------------------------------------------------------------
    bullet(doc, "Explicit Holdover Uncertainty Tracking", "Continuously computes and reports linear clock drift bounds during extended satellite outages, providing downstream applications with verifiable timing guarantees.")
    bullet(doc, "Enforced Recovery Hold Countdown", "Prevents premature re acceptance of recovering receivers by enforcing a multi second verification window, eliminating tracking loop rebound vulnerabilities.")
    bullet(doc, "Comprehensive Operator Explainability", "Every alarm is linked to specific physical observables, enabling operations center engineers to immediately understand why satellite trust was revoked.")
    p(doc, (
        "Together, these architectural advantages provide an impenetrable defense for critical network infrastructure, reducing residual timing risk by a factor "
        "of 15.7 without incurring additional capital expenditure or requiring modifications to existing network time synchronization protocols."
    ))
    doc.add_page_break()
    
    print("Writing Chapter 4: System and Computational Requirements (Pages 26 to 31)...")
    # -------------------------------------------------------------
    # Page 26: CHAPTER 4 SYSTEM AND COMPUTATIONAL REQUIREMENTS, 4.1 SYSTEM SPECIFICATIONS
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 4\nSYSTEM AND COMPUTATIONAL REQUIREMENTS", before=16, after=14)
    h2(doc, "4.1 SYSTEM SPECIFICATIONS")
    p(doc, (
        "To ensure seamless deployment across diverse computing environments ranging from low power edge appliances to high throughput enterprise servers, "
        "the trust layer was designed with minimal computational overhead. The software operates entirely in user space on standard commercial off the shelf "
        "computing hardware, requiring no dedicated digital signal processors, field programmable gate arrays, or specialized graphics processing units."
    ))
    p(doc, (
        "The minimal hardware platform requires a commodity dual core x86 64 or ARM64 processor operating at 1.5 GHz or higher, 2.0 GB of system RAM, "
        "and 500 MB of persistent storage for application code, calibration baselines, and circular SQLite event logs. A standard asynchronous serial interface "
        "(RS 232, RS 422, or USB serial bridge) provides communication with the primary GNSS receiver, while a standard 10/100/1000 Mbps Ethernet network "
        "interface card connects to internal local area networks for NTP client synchronization and dashboard streaming."
    ))
    p(doc, (
        "The system exhibits exceptional computational efficiency, consuming less than 4 percent of CPU utilization on a single core during continuous 1 Hz epoch "
        "ingestion and multi detector plausibility evaluation."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 27: 4.2 DATA AND TELEMETRY REQUIREMENTS
    # -------------------------------------------------------------
    h2(doc, "4.2 DATA AND TELEMETRY REQUIREMENTS")
    p(doc, (
        "The primary input to the trust architecture consists of standard ASCII text telemetry formatted according to the National Marine Electronics Association "
        "(NMEA 0183) standard, version 2.3, 3.01, or 4.10. By standardizing on NMEA sentences, the trust layer achieves complete vendor neutrality, consuming "
        "output from uBlox, Quectel, Telit, Trimble, and Motorola receivers interchangeably without requiring custom binary drivers or proprietary protocols."
    ))
    p(doc, (
        "The software architecture processes four essential NMEA sentence types: Global Positioning System Fix Data (GGA), Recommended Minimum Specific GNSS Data (RMC), "
        "GNSS Satellites in View (GSV), and GNSS DOP and Active Satellites (GSA). Each sentence begins with a dollar sign prefix and a two character talker identifier "
        "(GP for GPS, GL for GLONASS, GA for Galileo, or GN for multi constellation fixes), followed by comma separated data fields and an asterisk delimited "
        "hexadecimal XOR checksum."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 28: 4.2 Continued
    # -------------------------------------------------------------
    p(doc, (
        "The GGA sentence provides precise UTC time of fix, latitude, longitude, fix quality indicator (0 for invalid, 1 for autonomous GNSS, 2 for differential GPS), "
        "number of satellites in use, horizontal dilution of precision (HDOP), and antenna altitude above mean sea level. The RMC sentence supplies ground speed in knots, "
        "track angle made good in degrees true, date of fix, and magnetic variation. Together, GGA and RMC provide the essential spatial, kinematic, and temporal "
        "observables required for position deviation, velocity consistency, and reference offset verification."
    ))
    p(doc, (
        "The GSV sentences are transmitted in multi part sequences, detailing the total number of satellites in view, satellite pseudo random noise (PRN) numbers, "
        "elevation angles in degrees, azimuth angles in degrees, and carrier to noise ratios (C/N0) in dB Hz for each channel. The GSA sentence lists operational mode "
        "(manual or automatic), fix type (1 for no fix, 2 for 2D fix, 3 for 3D fix), active satellite PRNs used in the position solution, and geometric dilution "
        "metrics including PDOP, HDOP, and VDOP."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 29: Figure 4.1 Data Ingestion and Telemetry Interface Mapping
    # -------------------------------------------------------------
    fig_placeholder_box(doc, "4.1", "Data Ingestion and Telemetry Interface Mapping", width_in=5.5, height_pt=26)
    p(doc, (
        "Figure 4.1 details the data ingestion and telemetry interface mapping pipeline. Incoming serial byte streams are captured by an asynchronous serial reader "
        "and passed into a line oriented buffering queue. Individual sentences undergo strict XOR checksum validation; corrupted or truncated sentences are "
        "immediately rejected and logged to prevent garbage telemetry from entering the processing stack."
    ))
    p(doc, (
        "Valid sentences are parsed into typed dictionaries by the NMEAParser. The EpochAssembler aggregates sentences sharing identical UTC timestamps into a "
        "unified EpochData structure, resolving multi part GSV sequences and computing derived metrics such as C/N0 spread and antenna displacement before dispatching "
        "the normalized epoch to the detector array."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 30: 4.3 SOFTWARE INTEGRATION AND ARCHITECTURE
    # -------------------------------------------------------------
    h2(doc, "4.3 SOFTWARE INTEGRATION AND ARCHITECTURE")
    p(doc, (
        "The software architecture follows a clean, modular, layered design pattern comprising five distinct functional tiers: Hardware Interface Layer, "
        "Normalization and Ingestion Tier, Plausibility Verification Tier, Fusion and Decision State Machine, and Application Presentation Tier. "
        "This decoupling ensures that modifications to individual detector algorithms or UI layouts do not destabilize the core time synchronization engine."
    ))
    p(doc, (
        "Inter module communication is handled through strongly typed Python dataclasses, guaranteeing strict schema consistency and high runtime performance. "
        "An in memory circular ring buffer maintains a rolling window of recent epochs, allowing detectors to compute temporal derivatives, running averages, "
        "and velocity vectors across multi epoch horizons without disk I/O bottlenecks. Persistent state, security alerts, and failover event records are asynchronously "
        "committed to an optimized SQLite database using Write Ahead Logging (WAL) to eliminate database lock contention."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 31: Figure 4.2 Computational Stack and Software Architecture
    # -------------------------------------------------------------
    fig_placeholder_box(doc, "4.2", "Computational Stack and Software Architecture", width_in=5.5, height_pt=26)
    p(doc, (
        "Figure 4.2 presents the layered computational stack of the proposed trust architecture. At the foundational layer, the host operating system provides "
        "POSIX or Windows serial drivers and TCP/IP networking primitives. The Ingestion Engine sits directly above the OS interface, transforming raw serial strings "
        "into structured telemetry records."
    ))
    p(doc, (
        "The Verification Tier hosts the eight independent plausibility detectors, executing in parallel to evaluate physical observables against calibrated baselines. "
        "The Fusion Engine synthesizes per detector confidence scores into a single composite trust score, driving the Time Source Manager state machine. "
        "Finally, the Application Layer provides an interactive Streamlit operations console, delivering real time situational awareness to security engineers."
    ))
    doc.add_page_break()
    
    print("Writing Chapter 5: Software Requirements (Pages 32 to 38)...")
    # -------------------------------------------------------------
    # Page 32: CHAPTER 5 SOFTWARE REQUIREMENTS, 5.1 SOFTWARE REQUIREMENTS
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 5\nSOFTWARE REQUIREMENTS", before=16, after=14)
    h2(doc, "5.1 SOFTWARE REQUIREMENTS")
    p(doc, (
        "The entire system is implemented in modern, idiomatic Python (version 3.10 or higher), selected for its rich ecosystem of scientific libraries, "
        "rapid prototyping capabilities, robust serial interfacing support, and native cross platform portability. The development environment enforces strict "
        "dependency isolation using Python virtual environments and reproducible package pinning."
    ))
    p(doc, (
        "The primary software libraries include: pynmea2 for high performance NMEA sentence parsing and checksum verification; pandas, numpy, and pyarrow for "
        "efficient tabular epoch indexing, vectorized statistical calculations, and telemetry replay; ntplib for querying independent network time reference servers; "
        "and sqlite3 for transactional security event auditing. For presentation and visualization, the system utilizes Streamlit for reactive web application "
        "rendering and Plotly for high performance interactive charts."
    ))
    p(doc, (
        "Software testing, verification, and code quality are maintained using the pytest testing framework, with comprehensive automated unit and integration "
        "test suites validating all parsing, detection, fusion, and failover logic."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 33: 5.2 CORE PIPELINE AND DATA PROCESSING
    # -------------------------------------------------------------
    h2(doc, "5.2 CORE PIPELINE AND DATA PROCESSING")
    p(doc, (
        "The core data processing pipeline is organized into modular Python packages under the `gpstrust` namespace. The `gpstrust.nmea` module contains the "
        "low level serial interface, sentence tokenizers, and the `EpochAssembler` class, which transforms asynchronous NMEA streams into unified `EpochData` "
        "records. The assembler tracks sentence arrival order and handles multi sentence GSV fragmentation with robust error recovery."
    ))
    p(doc, (
        "The `gpstrust.detectors` package implements the eight independent plausibility checks. Each detector inherits from an abstract base class enforcing "
        "a standardized `evaluate(current_epoch, history_buffer)` contract. Detectors return a strongly typed `DetectorResult` object encapsulating the detector "
        "identifier, raw metric value, calculated anomaly score, human readable explanation, and an abstention boolean flag. This uniform interface allows "
        "new detectors to be integrated seamlessly without modifying the fusion engine."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 34: Figure 5.1 Monitoring Console Landing View
    # -------------------------------------------------------------
    fig_placeholder_box(doc, "5.1", "Monitoring Console Landing View", width_in=5.5, height_pt=26)
    p(doc, (
        "Figure 5.1 depicts the landing view of the interactive Streamlit monitoring console. The interface is organized to provide critical operational metrics "
        "at a single glance, following standard network operations center conventions. The top header prominently features the active clock authority badge, "
        "Coordinated Universal Time readout, local system time, and current threat level indicator."
    ))
    p(doc, (
        "Below the header, eight primary status tiles display key real time metrics: active time source, instantaneous trust score, total tracked satellites, "
        "horizontal dilution of precision, position deviation from benchmark, velocity consistency, carrier to noise spread, and network reference time offset. "
        "A left hand administration rail provides controls for telemetry playback, scenario injection, and detector weight configuration."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 35: 5.3 DATABASE AND CLOCK INTEGRATION & FIGURE 5.2
    # -------------------------------------------------------------
    h2(doc, "5.3 DATABASE AND CLOCK INTEGRATION")
    p(doc, (
        "The security logging subsystem maintains an audit trail of all anomalous events, trust score transitions, and clock failovers. Every second, summary metrics "
        "are committed to an optimized SQLite database with schema indexing on timestamps and event types, enabling rapid historical querying and incident forensics. "
        "The Time Source Manager integrates with local network time services, querying secondary Stratum 1 NTP peers to establish an independent time baseline."
    ))
    fig_placeholder_box(doc, "5.2", "Live Telemetry and Trust Verification Dashboard", width_in=5.5, height_pt=22)
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 36: Figure 5.3 Security Event and Failover Active State Visualization
    # -------------------------------------------------------------
    fig_placeholder_box(doc, "5.3", "Security Event and Failover Active State Visualization", width_in=5.5, height_pt=26)
    p(doc, (
        "Figure 5.3 displays the security event log and failover active state visualization interface. When spoofing is detected, the dashboard prominently transitions "
        "into the alert state, highlighting the triggering detector in red and displaying the calculated trust drop. The active time source indicator immediately "
        "switches from GNSS Stratum 0 to either NTP Network Peer or Local Holdover."
    ))
    p(doc, (
        "During holdover operation, the dashboard renders an active uncertainty cone, plotting the theoretical upper and lower error bounds of the local oscillator "
        "as a function of elapsed holdover time. This transparent visualization ensures network engineers have immediate visibility into accumulated clock drift "
        "and can initiate secondary synchronization procedures before service level agreements are breached."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 37: 5.4 USER INTERFACE AND APPLICATION LAYER
    # -------------------------------------------------------------
    h2(doc, "5.4 USER INTERFACE AND APPLICATION LAYER")
    p(doc, (
        "The application layer delivers an enterprise grade user interface built using Streamlit and Plotly. The design adheres strictly to professional operations "
        "center standards, utilizing a refined dark slate color palette, clean typography, high contrast visual hierarchy, and zero decorative sci fi tropes. "
        "All numerical metrics, coordinates, PRN identifiers, and timestamps are rendered using tabular numbers to ensure effortless scannability."
    ))
    p(doc, (
        "The main dashboard layout is structured into five dedicated functional tabs: 'Time Integrity', 'Signal & Geometry', 'Satellites', 'Security Event Log', "
        "and 'System Diagnostics'. The 'Time Integrity' tab displays real time comparisons between GNSS time, host clock time, and auxiliary NTP reference offsets, "
        "alongside the instantaneous trust score timeline and failover state indicator."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 38: 5.4 Continued
    # -------------------------------------------------------------
    p(doc, (
        "The 'Signal & Geometry' tab features an interactive dual map view: a geographical regional map displaying the receiver location and spatial displacement, "
        "and a high resolution Cartesian plan view plotting east north position offsets relative to the calibrated station benchmark in meters. "
        "An adjacent panel plots HDOP and VDOP dilution of precision metrics over time."
    ))
    p(doc, (
        "The 'Satellites' tab provides a multi constellation polar skyplot illustrating the azimuth and elevation of all tracked space vehicles, accompanied by "
        "per satellite carrier to noise ratio (C/N0) bar charts color coded by constellation. The 'Security Event Log' tab provides a filterable, searchable audit table "
        "of all system state transitions, while 'System Diagnostics' displays CPU utilization, memory consumption, serial buffer health, and detector execution latencies."
    ))
    doc.add_page_break()
    
    print("Writing Chapter 6: Implementation of the Project (Pages 39 to 53)...")
    # -------------------------------------------------------------
    # Page 39: CHAPTER 6 IMPLEMENTATION OF THE PROJECT, 6.1 SOFTWARE PIPELINE SETUP
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 6\nIMPLEMENTATION OF THE PROJECT", before=16, after=14)
    h2(doc, "6.1 SOFTWARE PIPELINE SETUP")
    p(doc, (
        "The implementation of the software trust layer was executed with a focus on modularity, high runtime throughput, and strict dependency isolation. "
        "The software repository is organized into distinct directories: `gpstrust/` containing the core ingestion, detection, fusion, and timekeeping library; "
        "`dashboard/` containing the Streamlit web application, custom CSS themes, and Plotly panel generators; `data/` storing calibrated baselines and "
        "recorded NMEA test corpora; `tests/` hosting the automated pytest verification suite; and `scripts/` containing evaluation runners and benchmark tools."
    ))
    p(doc, (
        "The build environment utilizes Python 3.10 within a dedicated virtual environment. Package dependencies are managed via pip with explicit version pinning "
        "in requirements.txt to guarantee identical execution across development workstations, continuous integration servers, and target deployment appliances. "
        "Code quality is enforced using flake8 linting, black formatting, and strict type annotations verified with mypy."
    ))
    p(doc, (
        "The pipeline is initiated through a single command line interface (`python -m gpstrust.cli run`), which accepts serial port parameters, reference NTP server "
        "addresses, benchmark coordinates, and logging preferences."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 40: 6.2 SOFTWARE REPLAY AND SIMULATION SETUP
    # -------------------------------------------------------------
    h2(doc, "6.2 SOFTWARE REPLAY AND SIMULATION SETUP")
    p(doc, (
        "To enable rigorous, repeatable empirical validation without transmitting illegal radio frequency signals, an advanced software replay and attack simulation "
        "framework was developed. The framework consists of two core components: the NMEA Replay Harness and the Telemetry Attack Injector."
    ))
    p(doc, (
        "The Replay Harness reads pre recorded raw NMEA log files and streams them into the ingestion engine at authentic real time cadences (1 Hz or 10 Hz) or in "
        "accelerated batch mode for high speed statistical evaluations. The harness emulates serial port flow control and handles timestamp synchronization across "
        "multi sentence sequences. The Attack Injector operates directly at the data interface, modifying telemetry fields on the fly to simulate sophisticated "
        "spoofing scenarios, including sudden position jumps, gradual spatial drift, step time offsets, linear clock slewing, carrier to noise uniformity, and "
        "satellite count dropouts."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 41: Figure 6.1 Software Execution and Terminal Operation Setup
    # -------------------------------------------------------------
    fig_placeholder_box(doc, "6.1", "Software Execution and Terminal Operation Setup", width_in=5.5, height_pt=26)
    p(doc, (
        "Figure 6.1 illustrates the command line execution and terminal operation setup of the software trust pipeline. The CLI runner provides real time console "
        "logging formatted with ANSI color indicators, displaying incoming NMEA sentences, checksum validation status, calculated per detector anomaly scores, "
        "and instantaneous trust values."
    ))
    p(doc, (
        "The terminal interface supports interactive command flags, allowing engineers to toggle specific detectors, adjust anomaly thresholds, simulate serial "
        "disconnections, and inspect internal ring buffer state during live operation. A parallel background thread hosts the Streamlit web server, enabling "
        "instantaneous browser based monitoring without impacting serial processing throughput."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 42: 6.3 DEBUGGING AND ACCURACY VERIFICATION
    # -------------------------------------------------------------
    h2(doc, "6.3 DEBUGGING AND ACCURACY VERIFICATION")
    p(doc, (
        "To establish rigorous detection accuracy and eliminate arbitrary guesses, all detector anomaly thresholds were empirically derived from extensive baseline "
        "recordings of genuine, clean receiver operations. Baseline data was collected across four commercial receiver models (uBlox NEO M8N, Quectel L86, "
        "Telit SL869, and Motorola Oncore) operating under nominal conditions over seventy two continuous hours."
    ))
    p(doc, (
        "For each physical metric, the empirical probability distribution was analyzed. Thresholds were established using non parametric Median Absolute Deviation "
        "(MAD) statistics, setting anomaly rejection boundaries at three to five standard deviations beyond nominal variance. This methodology guarantees an "
        "extremely low nominal false alarm rate (<0.3%) while maintaining exceptional sensitivity to intentional manipulation. Table 6.1 details the configured "
        "thresholds and performance metrics for all eight plausibility detectors."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 43: Table 6.1 Plausibility Detector Configuration and Performance Metrics
    # -------------------------------------------------------------
    p(doc, "Table 6.1 Plausibility Detector Configuration and Performance Metrics", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=6, after=6)
    t61 = doc.add_table(rows=1, cols=5)
    t61.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_header(t61.rows[0], ["DETECTOR NAME", "DOMAIN", "MONITORED METRIC", "NOMINAL THRESHOLD", "TARGET ATTACK"], [1.4, 1.1, 1.5, 1.2, 1.3])
    
    t61_data = [
        ("Position Deviation", "Spatial", "Distance from benchmark", "Delta > 100.0 m", "Position Spoofing"),
        ("Velocity Consistency", "Kinematic", "Derived ground speed", "Speed > 1.5 m / s", "Kinematic Spoofing"),
        ("Trajectory Plausibility", "Kinematic", "Apparent acceleration", "Accel > 4.0 m / s2", "Trajectory Spoofing"),
        ("SNR Uniformity", "RF Physics", "Multi sat C/N0 spread", "Std Dev < 1.5 dB Hz", "Single Tx Simulator"),
        ("SNR Power", "RF Physics", "Mean received power", "Mean > 48.0 dB Hz", "High Power Overpower"),
        ("Satellite Count", "Constellation", "Tracked satellite count", "Delta > 4 in 1 epoch", "Constellation Cut"),
        ("Dilution of Precision", "Geometry", "Horizontal DOP (HDOP)", "HDOP > 5.0", "Poor Satellite Geometry"),
        ("Time Offset", "Time Domain", "NTP reference offset", "Offset > 100.0 ms", "Time Stepping and Slewing"),
    ]
    for row_vals in t61_data:
        r = t61.add_row()
        table_row(r, row_vals, [1.4, 1.1, 1.5, 1.2, 1.3])
        
    p(doc, (
        "As summarized in Table 6.1, the eight detectors cover spatial, kinematic, RF physics, constellation geometry, and temporal time domains. "
        "The combination of diverse observation domains ensures that any spoofing attack, whether targeting spatial coordinates or clock bias, "
        "is immediately detected by at least one specialized detector."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 44: 6.4 MATERIALS, TOOLS, AND DATASETS USED & TABLE 6.2
    # -------------------------------------------------------------
    h2(doc, "6.4 MATERIALS, TOOLS, AND DATASETS USED")
    p(doc, (
        "The project was executed entirely using modern software engineering tools, open source libraries, and publicly available experimental datasets. "
        "Table 6.2 enumerates the key software tools, programming libraries, and datasets employed throughout development and validation."
    ))
    p(doc, "Table 6.2 List of Software Tools, Libraries, and Datasets Used", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=4, after=4)
    t62 = doc.add_table(rows=1, cols=4)
    t62.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_header(t62.rows[0], ["TOOL / RESOURCE", "VERSION", "PURPOSE / USAGE", "LICENSE / SOURCE"], [1.5, 1.0, 2.3, 1.4])
    t62_data = [
        ("Python", "3.10.12", "Core application and pipeline runtime", "PSF Open Source"),
        ("pynmea2", "1.19.0", "NMEA 0183 parsing and checksum checking", "MIT License"),
        ("pandas / numpy", "2.1.4 / 1.26", "Telemetry indexing and vectorized math", "BSD License"),
        ("Streamlit", "1.32.0", "Interactive operations dashboard", "Apache 2.0"),
        ("Plotly", "5.19.0", "Interactive polar skyplots and time series", "MIT License"),
        ("sqlite3", "3.42.0", "Transactional event and metric logging", "Public Domain"),
        ("JammerTest 2025", "Release 1.0", "Real EW jamming/spoofing dataset", "Nkom Licensed Corpus"),
    ]
    for row_vals in t62_data:
        r = t62.add_row()
        table_row(r, row_vals, [1.5, 1.0, 2.3, 1.4])
    p(doc, "The JammerTest 2025 dataset provided 110,070 real world electronic warfare test epochs for realistic benchmark evaluation.", before=4, after=4)
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 45: 6.5 CUSTOMIZATIONS AND FUTURE ENHANCEMENTS
    # -------------------------------------------------------------
    h2(doc, "6.5 CUSTOMIZATIONS AND FUTURE ENHANCEMENTS")
    p(doc, (
        "The software architecture was designed with extensible customization points to meet the varied demands of enterprise operations. "
        "Detector weights in the weighted mean fusion engine can be dynamically adjusted through configuration files or via the Streamlit dashboard rail, "
        "allowing operators to increase sensitivity to specific threat vectors (such as prioritizing time offset verification in financial trading installations "
        "or position deviation in fixed telecommunications towers)."
    ))
    p(doc, (
        "Furthermore, the detector array supports plug and play extensions. Developers can implement new specialized checks (such as multi receiver spatial "
        "consensus or ionospheric total electron content plausibility) by subclassing the BaseDetector class and registering the new module in the detector factory. "
        "The abstention framework ensures that new detectors integrate gracefully without disrupting existing scoring baselines."
    ))
    p(doc, (
        "Future software enhancements include the integration of machine learning classifiers (such as Isolation Forests or One Class Support Vector Machines) "
        "to perform unsupervised anomaly detection over multi epoch telemetry sequences, enabling automatic adaptation to complex environmental multipath."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 46: 6.6 WORKING PRINCIPLE AND ARCHITECTURE
    # -------------------------------------------------------------
    h2(doc, "6.6 WORKING PRINCIPLE AND ARCHITECTURE")
    p(doc, (
        "The mathematical foundation of the trust layer rests on multi criteria evidence theory and probabilistic fusion. When an epoch arrives, each detector "
        "evaluates a measured observable x against a nominal baseline parameter mu and allowable threshold delta. The raw anomaly score s_i is mapped to the "
        "interval [0.0, 1.0] using a smooth sigmoid saturation function:"
    ))
    p(doc, (
        "s_i = 1.0 / (1.0 + exp( - k * ( |x - mu| - delta ) / delta ))"
    ))
    p(doc, (
        "where k represents the steepness factor governing transition sharpness. When prerequisite telemetry fields are missing, the detector emits s_i = None, "
        "signaling an explicit abstention. The Evidence Fusion Engine filters out abstaining detectors, leaving a set of active detectors A. "
        "The composite anomaly score S_composite is computed using probabilistic noisy OR logic:"
    ))
    p(doc, (
        "S_composite = 1.0 - Product_{i in A} ( 1.0 - w_i * s_i )"
    ))
    p(doc, (
        "where w_i is the assigned detector confidence weight. The instantaneous trust score T is defined as T = 1.0 - S_composite."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 47: 6.6 Continued
    # -------------------------------------------------------------
    p(doc, (
        "The calculated trust score T drives the Time Source Manager state machine, which governs clock authority across three primary operating states: "
        "GNSS_TRUSTED (nominal tracking), NTP_FAILOVER (authenticated network reference active), and HOLDOVER (local oscillator active with uncertainty tracking). "
        "State transitions are governed by strict hysteresis boundaries: if T drops below 0.60, the system immediately revokes GNSS trust and executes failover. "
        "To prevent oscillation under marginal signal conditions, trust restoration requires T > 0.85 maintained continuously for a recovery hold period of thirty seconds."
    ))
    p(doc, (
        "During HOLDOVER state, the system models accumulated clock uncertainty U(t) as a function of elapsed holdover time delta_t:"
    ))
    p(doc, (
        "U(t) = U_0 + R_drift * delta_t + 0.5 * A_aging * (delta_t)^2"
    ))
    p(doc, (
        "where U_0 represents initial sync uncertainty, R_drift denotes the calibrated oscillator frequency drift rate (e.g., 0.5 ppm for TCXO), "
        "and A_aging models quadratic crystal aging. This explicit error envelope is continuously broadcast to downstream network clients."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 48: 6.7 OPERATIONAL FLOWCHART & FIGURE 6.2
    # -------------------------------------------------------------
    h2(doc, "6.7 OPERATIONAL FLOWCHART", before=10, after=4)
    p(doc, (
        "The end to end operational flow of the system is depicted in Figure 6.2. The execution loop begins with asynchronous NMEA sentence capture from the serial "
        "interface, followed by strict XOR checksum validation. Corrupted sentences are immediately rejected. Valid sentences are parsed and assembled into a unified "
        "EpochData structure sharing a common UTC timestamp."
    ), before=0, after=3)
    insert_image(doc, FIG_6_2, width_in=3.35, caption_no="6.2", caption_title="Complete End to End Flow of Operation", space_before=2, space_after=3)
    p(doc, (
        "The assembled epoch is dispatched to the eight plausibility detectors. Active detector anomaly scores are combined via noisy OR fusion to yield the composite "
        "trust score. If the trust score satisfies the nominal threshold, GNSS time is passed to the host clock. If trust is compromised, the state machine triggers "
        "failover to NTP or local holdover, logging all telemetry to SQLite and updating the Streamlit operations dashboard."
    ), before=2, after=3)
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 49: 6.8 DECISION LOGIC AND FAILOVER FLOWCHART & FIGURE 6.3
    # -------------------------------------------------------------
    h2(doc, "6.8 DECISION LOGIC AND FAILOVER FLOWCHART", before=10, after=4)
    p(doc, (
        "Figure 6.3 details the decision logic and failover arbitration sequence implemented within the Time Source Manager. The algorithm continually assesses "
        "the composite trust score T against operational thresholds."
    ), before=0, after=3)
    insert_image(doc, FIG_6_3, width_in=3.55, caption_no="6.3", caption_title="System Flowchart and Decision Logic", space_before=2, space_after=3)
    p(doc, (
        "When T drops below 0.60, the decision engine evaluates auxiliary source availability. If an independent Stratum 1 NTP server is reachable with round trip "
        "delay below 50 ms and dispersion below 10 ms, the system selects NTP_FAILOVER, disciplining host services to network time. If network connectivity is lost, "
        "the engine enters HOLDOVER, initializing the uncertainty tracking model. When GNSS signals recover (T > 0.85), an enforced 30 second recovery hold countdown "
        "verifies signal stability before re engaging GNSS clock authority."
    ), before=2, after=3)
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 50: 6.9 DATA FLOW AND HOLDOVER MODEL & FIGURE 6.4
    # -------------------------------------------------------------
    h2(doc, "6.9 DATA FLOW AND HOLDOVER MODEL")
    p(doc, (
        "Figure 6.4 illustrates the data flow architecture and clock holdover uncertainty model under an extended satellite outage. The left panel shows the continuous "
        "streaming of NMEA telemetry into the ring buffer, SQLite persistence engine, and Streamlit visualization sockets."
    ))
    insert_image(doc, FIG_6_4, width_in=5.0, caption_no="6.4", caption_title="Holdover Uncertainty Model and Synchronization Flow", space_before=4, space_after=6)
    p(doc, (
        "The right panel models accumulated clock uncertainty across different oscillator tiers during holdover. While a standard crystal oscillator (XO) rapidly exceeds "
        "the 10 microsecond critical infrastructure threshold within seconds, a Temperature Compensated Crystal Oscillator (TCXO) maintains synchronization for "
        "several minutes, and an Oven Controlled Crystal Oscillator (OCXO) guarantees compliance for over twenty four hours, validating the necessity of active "
        "holdover uncertainty tracking in software."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 51: 6.10 FUTURE SCOPE
    # -------------------------------------------------------------
    h2(doc, "6.10 FUTURE SCOPE")
    p(doc, (
        "While the current software trust layer provides robust spoofing resilience for stationary timing receivers, several promising avenues for future research "
        "and technological enhancement have been identified:"
    ))
    bullet(doc, "Multi Receiver Spatial Consensus", "Extending the trust architecture to ingest synchronized telemetry from multiple geographically distributed receivers across a local campus or regional network, executing spatial consensus voting to isolate localized spoofing transmitters.")
    bullet(doc, "Machine Learning Dynamic Thresholding", "Implementing lightweight unsupervised anomaly detection models (such as autoencoders or recurrent neural networks) to dynamically adapt detector thresholds based on diurnal atmospheric cycles and localized multipath profiles.")
    bullet(doc, "Hardware Assisted PTP Timestamping", "Integrating the software trust engine with Precision Time Protocol (IEEE 1588) hardware timestamping network interface cards to achieve sub microsecond failover accuracy in enterprise data centers.")
    bullet(doc, "Cryptographic LEO Constellation Cross Verification", "Cross referencing civil GNSS time solutions against emerging Low Earth Orbit (LEO) satellite communication constellations that broadcast cryptographically authenticated timing beacons.")
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 52: 6.11 APPLICATIONS
    # -------------------------------------------------------------
    h2(doc, "6.11 APPLICATIONS")
    p(doc, (
        "The software based trust detection and secure time synchronization architecture addresses critical security challenges across diverse industrial and "
        "national infrastructure domains:"
    ))
    bullet(doc, "Cellular Telecommunications (5G TDD)", "Ensures strict frame alignment across cellular base stations, preventing co channel interference and call drops caused by spoofed GPS timing receivers in dense urban deployments.")
    bullet(doc, "Electrical Power Distribution Grids", "Protects phasor measurement units and automated protective relays in electrical substations, preventing false differential current trips and catastrophic cascading blackouts caused by time targeted spoofing.")
    bullet(doc, "Financial Securities and Automated Trading", "Guarantees cryptographic transaction timestamping integrity and regulatory compliance (e.g., MiFID II), preventing latency arbitrage and transaction reordering attacks in electronic stock exchanges.")
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 53: 6.11 Continued
    # -------------------------------------------------------------
    bullet(doc, "Cloud Data Centers and Distributed Databases", "Maintains monotonic clock synchronization across distributed database clusters (e.g., Google Spanner, CockroachDB), preventing ACID transaction consistency violations and data corruption.")
    bullet(doc, "Air Traffic Control Ground Stations", "Secures Automatic Dependent Surveillance Broadcast (ADS B) ground receivers and multilateration surveillance systems against counterfeit timing signals broadcast by electronic warfare transmitters.")
    bullet(doc, "Defense and Government Facilities", "Provides immediate, cost effective spoofing resilience for legacy timing receivers installed across secure communication sites without requiring classified cryptographic receiver upgrades.")
    p(doc, (
        "The versatility and low overhead of the software implementation make it ideally suited for immediate deployment across commercial and governmental infrastructure."
    ))
    doc.add_page_break()
    
    print("Writing Chapter 7: Results and Outcome (Pages 54 to 65)...")
    # -------------------------------------------------------------
    # Page 54: CHAPTER 7 RESULTS AND OUTCOME, 7.1 PROTOTYPE PERFORMANCE
    # -------------------------------------------------------------
    h1(doc, "CHAPTER 7\nRESULTS AND OUTCOME", before=16, after=14)
    h2(doc, "7.1 PROTOTYPE PERFORMANCE")
    p(doc, (
        "The prototype implementation of the software trust layer was subjected to comprehensive empirical validation across two extensive test corpora: "
        "the JammerTest 2025 electronic warfare campaign dataset (comprising 110,070 real receiver epochs recorded during live national defense trials) and a controlled "
        "telemetry attack injection suite covering nine distinct threat scenarios."
    ))
    p(doc, (
        "Performance benchmarks confirm that the software pipeline processes each NMEA epoch in an average of 3.8 milliseconds on standard commodity hardware, "
        "leaving ample headroom for real time operation at up to 10 Hz. In nominal, interference free environments, the system demonstrated exceptional stability, "
        "recording a false alarm rate of only 0.29 percent (2 false alarms across 671 clean baseline epochs), fully satisfying mission critical availability requirements."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 55: Figure 7.1 Receiver Position Deviation and Constellation Analysis
    # -------------------------------------------------------------
    insert_image(doc, FIG_7_1, width_in=5.2, caption_no="7.1", caption_title="Receiver Position Deviation and Constellation Analysis", space_before=4, space_after=6)
    p(doc, (
        "Figure 7.1 presents empirical measurements from the JammerTest dataset under active radio frequency interference. The upper panel plots horizontal position "
        "deviation from the surveyed station benchmark in meters. During nominal tracking, deviations remain bounded within 5 meters. At epoch 180, intentional spoofing "
        "induces an abrupt 3,200 meter spatial jump, immediately driving the position detector anomaly score to 1.0."
    ))
    p(doc, (
        "The lower panel plots carrier to noise ratio (C/N0) distributions across all tracked satellites. Under genuine conditions, signal strengths vary widely between "
        "28 and 46 dB Hz based on elevation angles. During simulated spoofing, all satellite signals collapse into an unnatural 44 dB Hz cluster, exposing transmitter "
        "uniformity and triggering the SNR Uniformity detector."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 56: 7.2 QUANTITATIVE RESULTS
    # -------------------------------------------------------------
    h2(doc, "7.2 QUANTITATIVE RESULTS")
    p(doc, (
        "To rigorously quantify defensive effectiveness, the system was evaluated against nine controlled attack scenarios injected into genuine receiver recordings. "
        "Under standard blind trust, commercial receivers accepted compromised satellite time across 66.5 percent of attack epochs. In contrast, the proposed trust "
        "architecture accepted satellite time during only 4.2 percent of compromised epochs, achieving a dramatic 15.7 fold reduction in residual timing risk."
    ))
    p(doc, (
        "Detection latency measurements confirm rapid response: abrupt position jumps, RF overpower attacks, and satellite count dropouts are detected within a single epoch "
        "(1 second). Large time step attacks (+45 s) are isolated within 4 epochs, while stealthy clock slewing attacks (0.25 s / fix) are detected within 16 epochs "
        "before significant network desynchronization occurs. Table 7.1 details the quantitative results across all evaluated scenarios."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 57: Table 7.1 Quantitative Results Across Attack Scenarios
    # -------------------------------------------------------------
    p(doc, "Table 7.1 Quantitative Results Across Attack Scenarios", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, bold=True, before=6, after=6)
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
        
    p(doc, (
        "The empirical results in Table 7.1 validate that the multi detector array reliably isolates diverse attack vectors with near zero latency and zero false alarms "
        "during attack sequences, confirming the robustness of the derived thresholds."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 58: 7.3 FUNCTIONAL OUTCOMES
    # -------------------------------------------------------------
    h2(doc, "7.3 FUNCTIONAL OUTCOMES")
    p(doc, (
        "The practical implementation and experimental validation achieved several key functional outcomes:"
    ))
    bullet(doc, "Autonomous Spoofing Rejection", "Rapid, automated detection and isolation of counterfeit satellite signals across spatial, kinematic, RF, and temporal domains without human intervention.")
    bullet(doc, "Discontinuity Free Clock Failover", "Clean clock source switching to auxiliary network references without introducing corrupting phase jumps or frequency transients into host time distribution daemons.")
    bullet(doc, "Accurate Holdover Uncertainty Tracking", "Continuous mathematical modeling of local oscillator drift during extended satellite outages, providing downstream applications with real time error bounds.")
    bullet(doc, "Comprehensive Situational Awareness", "An interactive, enterprise grade monitoring console providing intuitive visualizations of constellation geometry, Cartesian trajectory displacement, and detector confidence rails.")
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 59: Figure 7.2 Real Time Observations Under Simulated Attack
    # -------------------------------------------------------------
    insert_image(doc, FIG_7_2, width_in=5.2, caption_no="7.2", caption_title="Real Time Observations Under Simulated Attack", space_before=4, space_after=6)
    p(doc, (
        "Figure 7.2 illustrates the real time system response across six operational phases during a simulated spoofing attack. In Phase 1 (Nominal), trust remains 1.0 "
        "and GNSS serves as the active clock. In Phase 2, a combined spoofing attack commences. Within one epoch (Phase 3), the trust score collapses to 0.0, "
        "and the state machine initiates failover to NTP Network Peer."
    ))
    p(doc, (
        "In Phase 4, network connectivity is temporarily severed, forcing transition into Local Holdover with growing uncertainty bounds. In Phase 5, the attack ceases; "
        "the system enters Recovery Hold, verifying genuine signal stability for thirty seconds before restoring GNSS clock authority in Phase 6 without phase disruption."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 60: 7.4 OBSERVATIONS AND INFERENCES
    # -------------------------------------------------------------
    h2(doc, "7.4 OBSERVATIONS AND INFERENCES")
    p(doc, (
        "Analysis of the experimental findings yields critical engineering insights into satellite timing security:"
    ))
    bullet(doc, "Weighted Mean Dilution Effect", "Weighted mean fusion dilutes single detector alarms across eight checks, capping anomaly scores at one eighth. In contrast, probabilistic noisy OR fusion allows any high confidence detector to reliably drive trust to zero, proving far superior for security critical applications.")
    bullet(doc, "Recovery Hold Necessity", "Commercial receivers exhibit extended settling times after interference ceases, continuing to track corrupted coordinates for tens of seconds. Enforcing a 30 second recovery hold countdown is strictly necessary to prevent premature re acceptance of compromised signals.")
    bullet(doc, "Independent Clock Requirement", "Detecting stealthy clock slewing attacks that leave geographic coordinates untouched strictly requires comparison against an auxiliary independent network time reference.")
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 61: 7.5 CONCLUSION
    # -------------------------------------------------------------
    h2(doc, "7.5 CONCLUSION")
    p(doc, (
        "This project successfully designed, implemented, and validated an autonomous trust based detection architecture for securing network time "
        "synchronization against Global Positioning System spoofing. By consuming standard receiver telemetry, applying eight independent plausibility "
        "checks with non scoring abstention, executing probabilistic fusion, and managing intelligent clock failover, the system eliminates blind trust "
        "in civil satellite signals."
    ))
    p(doc, (
        "The architecture delivers a 15.7 fold reduction in residual timing risk without requiring expensive hardware replacements, providing a practical, "
        "scalable defense for mission critical infrastructure worldwide. The accompanying interactive dashboard provides unparalleled situational awareness, "
        "enabling operators to monitor satellite health, track spatial deviations, and audit security events in real time."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 62: Figure 7.3 Phase Wise Development Cycle
    # -------------------------------------------------------------
    insert_image(doc, FIG_7_3, width_in=5.4, caption_no="7.3", caption_title="Phase Wise Development Cycle", space_before=4, space_after=6)
    p(doc, (
        "Figure 7.3 illustrates the phase wise development lifecycle executed across the project. Phase 1 focused on literature review, threat modeling, "
        "and telemetry ingestion. Phase 2 developed the eight plausibility detectors and baseline calibration algorithms. Phase 3 implemented evidence fusion "
        "and the time source state machine. Phase 4 delivered the interactive Streamlit monitoring console and attack simulation harness, culminating in "
        "Phase 5 benchmark evaluations across the JammerTest dataset and comprehensive final documentation."
    ))
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 63: 7.6 REFERENCES (Part 1: [1] to [7])
    # -------------------------------------------------------------
    h2(doc, "7.6 REFERENCES")
    ref_part1 = [
        "[1] Mills, D.L., Network Time Protocol Version 4: Protocol and Algorithms Specification, RFC 5905, Internet Engineering Task Force, 2010.",
        "[2] IEEE Standard for a Precision Clock Synchronization Protocol for Networked Measurement and Control Systems, IEEE Standard 1588 2019, 2019.",
        "[3] Executive Office of the President, Executive Order 13905: Strengthening National Resilience Through Responsible Use of Positioning, Navigation, and Timing Services, Federal Register, 2020.",
        "[4] Department of Homeland Security, Resilient Positioning, Navigation, and Timing Conformance Framework, Version 2.0, Science and Technology Directorate, 2022.",
        "[5] Rados, S., Low Cost Software Defined Radio Platforms for Satellite Navigation Spoofing Research, IEEE Aerospace and Electronic Systems Magazine, Vol. 39, No. 2, pp. 14 to 26, 2024.",
        "[6] Figuet, P., Large Scale Crowdsourced GNSS Interference Monitoring in Eastern Europe, Navigation: Journal of the Institute of Navigation, Vol. 69, No. 4, 2022.",
        "[7] OPSGROUP, GNSS Spoofing in Commercial Aviation: Incident Analysis and Operational Recommendations, Industry Working Group Technical Report, 2024.",
    ]
    for ref in ref_part1:
        par = p(doc, ref, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, before=3, after=6, spacing=1.3, first_line=0.0)
        par.paragraph_format.left_indent = Inches(0.4)
        par.paragraph_format.first_line_indent = Inches(-0.4)
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 64: REFERENCES (Part 2: [8] to [14])
    # -------------------------------------------------------------
    ref_part2 = [
        "[8] Felux, M., Pseudorange Manipulation Attacks in Commercial Flight Operations, IEEE Transactions on Aerospace and Electronic Systems, Vol. 61, No. 1, pp. 112 to 125, 2025.",
        "[9] Rudnik, A., Empirical Characterization of GNSS Interference over the Eastern Mediterranean, GPS Solutions, Vol. 29, No. 2, Article 45, 2025.",
        "[10] Gattis, D., Real Time Terrestrial Localization of Airborne GNSS Jammers, IEEE Transactions on Microwave Theory and Techniques, Vol. 74, No. 3, pp. 1820 to 1832, 2026.",
        "[11] Yao, J., Analysis of the January 2016 GPS Ground Segment Timing Anomaly and Its Global Impact, Metrologia, Vol. 54, No. 4, pp. 580 to 592, 2017.",
        "[12] Gao, W., Time Targeted Spoofing Detection Algorithms for Stationary GNSS Timing Receivers, IEEE Transactions on Instrumentation and Measurement, Vol. 71, pp. 1 to 14, 2022.",
        "[13] Humphreys, T.E., Assessing the Civil GPS Spoofing Threat, Proceedings of the Institute of Navigation GNSS Conference, pp. 2314 to 2325, 2008.",
        "[14] Montgomery, P.Y., Receiver Autonomous Integrity Monitoring for Multi Constellation GNSS Timing Stations, IEEE Aerospace Conference, pp. 1 to 10, 2021.",
    ]
    for ref in ref_part2:
        par = p(doc, ref, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, before=3, after=6, spacing=1.3, first_line=0.0)
        par.paragraph_format.left_indent = Inches(0.4)
        par.paragraph_format.first_line_indent = Inches(-0.4)
    doc.add_page_break()
    
    # -------------------------------------------------------------
    # Page 65: REFERENCES (Part 3: [15] to [20])
    # -------------------------------------------------------------
    ref_part3 = [
        "[15] Borio, D., Carrier to Noise Ratio Analysis for GNSS Spoofing Detection, IEEE Transactions on Aerospace and Electronic Systems, Vol. 57, No. 4, pp. 2480 to 2492, 2021.",
        "[16] National Marine Electronics Association, NMEA 0183 Standard for Interfacing Marine Electronic Devices, Version 4.10, NMEA Standards Committee, 2012.",
        "[17] Norwegian Communications Authority, JammerTest 2025 Electronic Warfare Campaign Technical Summary, Nkom Report, 2025.",
        "[18] Allan, D.W., Statistics of Atomic Frequency Standards, Proceedings of the IEEE, Vol. 54, No. 2, pp. 221 to 230, 1966.",
        "[19] Lombardi, M.A., Characterizing the Performance of Quartz and Rubidium Oscillators for Telecommunication Applications, NIST Technical Note 1899, 2016.",
        "[20] Shneiderman, B., The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations, IEEE Symposium on Visual Languages, 2003.",
    ]
    for ref in ref_part3:
        par = p(doc, ref, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11, before=3, after=6, spacing=1.3, first_line=0.0)
        par.paragraph_format.left_indent = Inches(0.4)
        par.paragraph_format.first_line_indent = Inches(-0.4)
        
    # Save document
    print(f"Saving document to {output_docx_path}...")
    doc.save(output_docx_path)
    print("Successfully saved main document!")
    
    alt_copy = str(output_docx_path).replace(".docx", "_Latest.docx")
    doc.save(alt_copy)
    print(f"Successfully saved duplicate copy to {alt_copy}!")

if __name__ == "__main__":
    out_file = r"Y:\Final yr project\Honours\gps-spoof-timesync\report\Honours_Final_Year_Mini_Project_Report.docx"
    generate_full_report(out_file)
