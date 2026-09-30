"""Script to generate the complete Honours Final Year Mini Project Report in DOCX format.
Strict rules:
1. Font must be Times New Roman ONLY across all styles, paragraphs, tables, and runs.
2. NO '-' dashes anywhere (no hyphens, en-dashes, em-dashes, or minus signs).
3. NO personal names (use placeholders like [Candidate Name], [Supervisor Name]).
4. Complete college format following Anna University / SVCE structure.
5. High detail, specific to GPS Spoofing Detection and Secure Time Synchronization.
6. Leave framed placeholder boxes for figures.
"""

import re
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def sanitize_no_dashes(text: str) -> str:
    """Removes any hyphen, en-dash, em-dash, minus, or dash character."""
    # Common replacements
    text = text.replace("—", " ")
    text = text.replace("–", " ")
    text = text.replace("-", " ")
    # Clean up double spaces if introduced
    while "  " in text:
        text = text.replace("  ", " ")
    return text

def set_run_font(run, font_name="Times New Roman", size_pt=12, bold=False, italic=False, color_rgb=(0,0,0)):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color_rgb)
    # Ensure XML also explicitly sets Times New Roman for complex scripts and ascii
    rPr = run._r.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="{font_name}" w:hAnsi="{font_name}" w:cs="{font_name}"/>')
    rPr.append(rFonts)

def add_para(doc, text="", style='Normal', align=WD_ALIGN_PARAGRAPH.JUSTIFY, 
             font_size=12, bold=False, italic=False, space_before=0, space_after=6, line_spacing=1.5):
    clean_text = sanitize_no_dashes(text)
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if clean_text:
        run = p.add_run(clean_text)
        set_run_font(run, font_name="Times New Roman", size_pt=font_size, bold=bold, italic=italic)
    return p

def add_heading_1(doc, text, space_before=18, space_after=12):
    return add_para(doc, text, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=14, bold=True, space_before=space_before, space_after=space_after)

def add_heading_2(doc, text, space_before=12, space_after=6):
    return add_para(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, font_size=12, bold=True, space_before=space_before, space_after=space_after)

def add_heading_3(doc, text, space_before=8, space_after=4):
    return add_para(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, font_size=12, bold=True, italic=True, space_before=space_before, space_after=space_after)

def add_bullet_point(doc, title, description, space_after=4):
    clean_title = sanitize_no_dashes(title)
    clean_desc = sanitize_no_dashes(description)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.5
    
    r_bullet = p.add_run("• ")
    set_run_font(r_bullet, font_name="Times New Roman", size_pt=12, bold=True)
    
    if clean_title:
        r_title = p.add_run(clean_title + ": ")
        set_run_font(r_title, font_name="Times New Roman", size_pt=12, bold=True)
        
    r_desc = p.add_run(clean_desc)
    set_run_font(r_desc, font_name="Times New Roman", size_pt=12, bold=False)
    return p

def add_figure_placeholder(doc, fig_no, fig_title):
    clean_no = sanitize_no_dashes(fig_no)
    clean_title = sanitize_no_dashes(fig_title)
    
    # Table as placeholder box
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(5.5)
    
    # Set light border and padding
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="999999"/>
            <w:left w:val="single" w:sz="6" w:space="0" w:color="999999"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="999999"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="999999"/>
        </w:tcBorders>
    ''')
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8F9FA"/>')
    tcPr.append(borders)
    tcPr.append(shading)
    
    cp = cell.paragraphs[0]
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(36)
    cp.paragraph_format.space_after = Pt(36)
    r1 = cp.add_run(f"[ SPACE FOR FIGURE {clean_no.upper()} ]\n")
    set_run_font(r1, font_name="Times New Roman", size_pt=11, bold=True, color_rgb=(100, 100, 100))
    r2 = cp.add_run(f"Paste {clean_title} Illustration Here")
    set_run_font(r2, font_name="Times New Roman", size_pt=10, italic=True, color_rgb=(120, 120, 120))
    
    # Caption below table
    caption = doc.add_paragraph()
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.space_before = Pt(6)
    caption.paragraph_format.space_after = Pt(14)
    rc = caption.add_run(f"Figure {clean_no} {clean_title}")
    set_run_font(rc, font_name="Times New Roman", size_pt=11, bold=True)

print("Helper functions defined successfully")
