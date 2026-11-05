"""Synthetic .docx fixtures for the tests. No real documents or data are used."""
from __future__ import annotations

import struct
import zipfile
import zlib
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import parse_xml
from docx.shared import Pt, RGBColor

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
V_NS = 'urn:schemas-microsoft-com:vml'
YELLOW = WD_COLOR_INDEX.YELLOW


def png_bytes(width=40, height=20) -> bytes:
    raw = b''.join(b'\x00' + b'\x20\x40\x80' * width for _ in range(height))

    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def write_png(path, width=40, height=20) -> Path:
    path = Path(path)
    path.write_bytes(png_bytes(width, height))
    return path


def _hl(run, size=None):
    run.font.highlight_color = YELLOW
    if size:
        run.font.size = Pt(size)
    return run


def make_template(path) -> Path:
    """Template: split highlighted placeholders, a neighbour highlighted run,
    boilerplate, a table with placeholder row + blank row + merged note row,
    an image placeholder, a URL in angle brackets, and a footer."""
    doc = Document()
    p = doc.add_paragraph()
    p.add_run('SYSTEM TITLE.  ').bold = True
    _hl(p.add_run('<Add System'), size=14)
    _hl(p.add_run(' Name>'))
    _hl(p.add_run(' Release '))
    _hl(p.add_run('<Add Version>'))
    doc.add_paragraph('Boilerplate paragraph that must not change.', style='List Bullet')
    doc.add_paragraph('See <https://example.com/guide> for details.')
    t = doc.add_table(rows=4, cols=3)
    t.style = 'Table Grid'
    for c, txt in zip(t.rows[0].cells, ('Component', 'Count', 'Notes')):
        c.paragraphs[0].add_run(txt).bold = True
    for c, txt in zip(t.rows[1].cells, ('<Add Component>', '<#>', '<Add Notes>')):
        _hl(c.paragraphs[0].add_run(txt), size=9)
    note = t.rows[3].cells[0].merge(t.rows[3].cells[2])
    note.paragraphs[0].add_run('NOTE: sample note.')
    _hl(doc.add_paragraph().add_run('<Add Diagram>'))
    doc.sections[0].footer.paragraphs[0].text = 'Example Public'
    doc.core_properties.author = 'Template Author'
    doc.save(str(path))
    return Path(path)


def make_source(path, image_path=None, marking=True, tracked=True, comment=True) -> Path:
    """Source: data paragraphs, emphasis (bold + blue), a vertically merged table,
    optional picture, optional text box with markings, tracked insertion, comment."""
    doc = Document()
    doc.add_paragraph('Example System')
    p = doc.add_paragraph()
    p.add_run('Mitigation:').bold = True
    r = p.add_run(' Use ACLs.')
    r.font.color.rgb = RGBColor(0x00, 0x00, 0xFF)
    t = doc.add_table(rows=3, cols=2)
    t.rows[0].cells[0].text, t.rows[0].cells[1].text = 'Group', 'Item'
    a = t.rows[1].cells[0].merge(t.rows[2].cells[0])
    a.text = 'Group A'
    t.rows[1].cells[1].text, t.rows[2].cells[1].text = 'x', 'y'
    if image_path:
        doc.add_picture(str(image_path))
    body = doc.element.body
    if marking:
        tb = parse_xml(
            '<w:p xmlns:w="%s" xmlns:v="%s"><w:r><w:pict><v:shape id="tb1" style="width:200pt;height:50pt">'
            '<v:textbox><w:txbxContent>'
            '<w:p><w:r><w:t>Controlled by: Example Agency</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>CUI Category: TEST</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>Distribution Statement C: test only</w:t></w:r></w:p>'
            '</w:txbxContent></v:textbox></v:shape></w:pict></w:r></w:p>' % (W_NS, V_NS))
        body.insert(len(body) - 1, tb)
    if tracked:
        ins = parse_xml(
            '<w:p xmlns:w="%s"><w:r><w:t xml:space="preserve">Base </w:t></w:r>'
            '<w:ins w:id="901" w:author="Test Reviewer" w:date="2026-01-01T00:00:00Z">'
            '<w:r><w:t>inserted text</w:t></w:r></w:ins></w:p>' % W_NS)
        body.insert(len(body) - 1, ins)
    if comment and hasattr(doc, 'add_comment'):
        para = doc.add_paragraph()
        run = para.add_run('Commented text')
        doc.add_comment(run, text='check this', author='Test Reviewer', initials='TR')
    doc.sections[0].footer.paragraphs[0].text = 'Example Confidential'
    doc.core_properties.author = 'Source Author'
    doc.save(str(path))
    return Path(path)


def make_doctype_docx(src_docx, out_path) -> Path:
    """Copy of src_docx whose document.xml carries a DOCTYPE/ENTITY declaration."""
    with zipfile.ZipFile(src_docx) as zin, zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info)
            if info.filename == 'word/document.xml':
                text = data.decode('utf-8')
                decl_end = text.index('?>') + 2
                data = (text[:decl_end] + '<!DOCTYPE x [<!ENTITY a "b">]>' + text[decl_end:]).encode('utf-8')
            zout.writestr(info, data)
    return Path(out_path)
