"""Complete script to assemble and generate the Honours Final Year Mini Project Report.
Strictly verifies zero dashes and enforces Times New Roman font throughout.
"""

import sys
import os
import re
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def clean(text: str) -> str:
    """Removes all hyphen, en-dash, em-dash, and minus characters."""
    if not text:
        return ""
    text = text.replace("—", " ")
    text = text.replace("–", " ")
    text = text.replace("-", " ")
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

def p(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, bold=False, italic=False, before=0, after=6, spacing=1.5):
    c_text = clean(text)
    par = doc.add_paragraph()
    par.alignment = align
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = spacing
    if c_text:
        run = par.add_run(c_text)
        set_font(run, size=size, bold=bold, italic=italic)
    return par

def h1(doc, text, before=18, after=12):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, before=before, after=after)

def h2(doc, text, before=14, after=6):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, size=12, bold=True, before=before, after=after)

def h3(doc, text, before=10, after=4):
    return p(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, size=12, bold=True, italic=True, before=before, after=after)

def bullet(doc, title, desc, after=4):
    c_title = clean(title)
    c_desc = clean(desc)
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.left_indent = Inches(0.25)
    par.paragraph_format.space_before = Pt(2)
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.5
    
    rb = par.add_run("• ")
    set_font(rb, size=12, bold=True)
    if c_title:
        rt = par.add_run(c_title + ": ")
        set_font(rt, size=12, bold=True)
    rd = par.add_run(c_desc)
    set_font(rd, size=12, bold=False)
    return par

def fig_box(doc, no, title):
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
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8F9FA"/>')
    tcPr.append(borders)
    tcPr.append(shd)
    
    cp = cell.paragraphs[0]
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(36)
    cp.paragraph_format.space_after = Pt(36)
    r1 = cp.add_run(f"[ SPACE FOR FIGURE {c_no.upper()} ]\n")
    set_font(r1, size=11, bold=True, color=(100, 100, 100))
    r2 = cp.add_run(f"Paste {c_title} Diagram or Screenshot Here")
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

def page_break(doc):
    doc.add_page_break()

print("Setup completed successfully.")
