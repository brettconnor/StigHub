"""Helpers for filling a COPY of a Word template with content from a source document.

Import from a per-job build script:

    import sys
    sys.path.insert(0, "<skill_dir>/scripts")
    from docx_helpers import *

Design rules these helpers enforce or support:
  * The template file is never written: copy_template() makes a new file and
    refuses to overwrite anything.
  * Text is written into the template's own runs, cells, and paragraphs, so
    template fonts, sizes, styles, and numbering are kept.
  * More rows or paragraphs come from cloning the template's own elements.
  * Placeholder highlighting is removed from anything that is filled.

See docx_helpers.spec.md for the full contract.
"""
from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches
from docx.text.paragraph import Paragraph

__all__ = [
    'W_NS', 'w', 'sha256_file', 'copy_template', 'assert_unchanged', 'open_docx',
    'body_blocks', 'tables', 'rows', 'cells', 'text_of', 'para_text', 'cell_lines', 'read_table',
    'find_paragraphs', 'find_one', 'expect', 'strip_highlight', 'strip_highlight_if_filled',
    'set_rpr', 'new_run', 'append_run', 'remove_runs', 'replace_span', 'set_paragraph_text',
    'fill_cell', 'clone', 'clone_after', 'insert_after', 'remove', 'remove_blank_rows', 'is_blank',
    'run_specs', 'paragraph_from_specs', 'list_images', 'extract_image', 'put_picture',
    'text_width_inches', 'PLACEHOLDER_RE',
]

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
_WP_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
_MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
_R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

PLACEHOLDER_RE = re.compile(r'<(?!https?://|mailto:)[^<>\n]{1,80}>|\[(?:Add|Insert|Enter|TBD)\b[^\]\n]{0,80}\]')

# Element order inside w:rPr (ECMA-376). Inserting out of order makes Word reject the file.
_RPR_ORDER = ['rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps', 'strike', 'dstrike',
              'outline', 'shadow', 'emboss', 'imprint', 'noProof', 'snapToGrid', 'vanish', 'webHidden',
              'color', 'spacing', 'w', 'kern', 'position', 'sz', 'szCs', 'highlight', 'u', 'effect',
              'bdr', 'shd', 'fitText', 'vertAlign', 'rtl', 'cs', 'em', 'lang', 'eastAsianLayout',
              'specVanish', 'oMath']
_REVISION_IN_RPR = ('ins', 'del', 'moveFrom', 'moveTo', 'rPrChange')


def w(tag: str) -> str:
    """Clark name for a WordprocessingML tag: w('p') -> '{...main}p'."""
    return '{%s}%s' % (W_NS, tag)


# --------------------------------------------------------------------------- files
def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def copy_template(template, output) -> str:
    """Copy template -> output without ever overwriting. Returns the template SHA-256.

    Raises FileNotFoundError if the template is missing, FileExistsError if the
    output (or a symlink at that path) already exists, ValueError if both paths
    are the same file, and RuntimeError if the template changed during the copy.
    """
    template, output = Path(template), Path(output)
    if not template.is_file():
        raise FileNotFoundError('template not found: %s' % template)
    if output.exists() or output.is_symlink():
        raise FileExistsError('output already exists (refusing to overwrite): %s' % output)
    if not output.parent.is_dir():
        raise FileNotFoundError('output folder does not exist: %s' % output.parent)
    if template.resolve() == output.resolve():
        raise ValueError('template and output are the same path')
    digest = sha256_file(template)
    with open(template, 'rb') as src, open(output, 'xb') as dst:   # 'x' = O_EXCL, no overwrite
        for chunk in iter(lambda: src.read(1 << 20), b''):
            dst.write(chunk)
    assert_unchanged(template, digest)
    if sha256_file(output) != digest:
        raise RuntimeError('copy is not identical to the template')
    return digest


def assert_unchanged(path, digest) -> None:
    actual = sha256_file(path)
    if actual != digest:
        raise RuntimeError('%s changed: sha256 %s != %s' % (path, actual, digest))


def open_docx(path):
    return Document(str(path))


# --------------------------------------------------------------------------- navigation
def body_blocks(doc) -> list:
    """Body children in order. Index i matches inventory.py's B# label."""
    return list(doc.element.body.iterchildren())


def tables(doc) -> list:
    """Top-level w:tbl elements. Index matches inventory.py's T# label and doc.tables."""
    return [t._tbl for t in doc.tables]


def rows(tbl) -> list:
    return tbl.findall(w('tr'))


def cells(tr) -> list:
    """RAW w:tc cells of a row: a gridSpan cell appears once; vMerge continuation
    cells are separate (empty) elements. Write to these, never to merged copies."""
    return tr.findall(w('tc'))


def _in_textbox(el, stop):
    for anc in el.iterancestors():
        if anc is stop:
            return False
        if anc.tag == w('txbxContent'):
            return True
    return False


def _in_fallback(el):
    return any(a.tag == '{%s}Fallback' % _MC_NS for a in el.iterancestors())


def text_of(el) -> str:
    """All w:t text below el (includes text boxes)."""
    return ''.join(t.text or '' for t in el.iter(w('t')))


def _run_text(r) -> str:
    out = []
    for c in r:
        if c.tag == w('t'):
            out.append(c.text or '')
        elif c.tag == w('tab'):
            out.append('\t')
        elif c.tag in (w('br'), w('cr')):
            out.append('\n')
    return ''.join(out)


def _text_runs(p):
    return [r for r in p.iter(w('r')) if not _in_textbox(r, p)]


def para_text(p) -> str:
    """Visible text of one paragraph, excluding text boxes anchored in it."""
    if hasattr(p, '_p'):
        p = p._p
    return ''.join(_run_text(r) for r in _text_runs(p))


def cell_lines(tc) -> list:
    """Non-blank paragraph texts of a cell, stripped."""
    return [para_text(p).strip() for p in tc.findall(w('p')) if para_text(p).strip()]


def read_table(table) -> list:
    """MERGE-RESOLVED text grid of a python-docx Table (use for reading the source).

    Each row has one entry per grid column; merged cells repeat their text.
    """
    return [['\n'.join(cell_lines(c._tc)) for c in row.cells] for row in table.rows]


def find_paragraphs(root, pattern, flags=0, include_tables=True, include_textboxes=False) -> list:
    """w:p elements whose visible text matches regex `pattern` (re.search)."""
    if hasattr(root, 'element'):
        root = root.element.body
    rx = re.compile(pattern, flags)
    out = []
    for p in root.iter(w('p')):
        if _in_fallback(p):
            continue
        if not include_textboxes and _in_textbox(p, root):
            continue
        if not include_tables and any(a.tag == w('tbl') for a in p.iterancestors()):
            continue
        if rx.search(para_text(p)):
            out.append(p)
    return out


def find_one(root, pattern, **kw):
    """Exactly one matching paragraph, else LookupError with what was found."""
    hits = find_paragraphs(root, pattern, **kw)
    if len(hits) != 1:
        raise LookupError('pattern %r matched %d paragraphs: %r' % (
            pattern, len(hits), [para_text(h)[:80] for h in hits[:5]]))
    return hits[0]


def expect(el, fragment) -> None:
    """Guard: fail loudly if a located element does not contain the expected template text."""
    txt = para_text(el) if el.tag == w('p') else text_of(el)
    if fragment not in txt:
        raise AssertionError('expected %r in element, found %r' % (fragment, txt[:120]))


# --------------------------------------------------------------------------- formatting
def strip_highlight(el) -> None:
    """Remove w:highlight from every rPr at or below el (runs and paragraph marks)."""
    if el is None:
        return
    for h in list(el.iter(w('highlight'))):
        h.getparent().remove(h)


def strip_highlight_if_filled(el, pattern=PLACEHOLDER_RE) -> bool:
    """For each paragraph at/below el that no longer contains a placeholder, remove all
    highlight (catches highlighted neighbour runs that were part of the placeholder).
    Returns True if anything was un-highlighted."""
    paras = [el] if el.tag == w('p') else list(el.iter(w('p')))
    changed = False
    for p in paras:
        if not pattern.search(para_text(p)) and any(True for _ in p.iter(w('highlight'))):
            strip_highlight(p)
            changed = True
    return changed


def set_rpr(rpr, tag, attrs) -> None:
    """Set (attrs dict) or remove (attrs None) one rPr child, in schema order."""
    for e in rpr.findall(w(tag)):
        rpr.remove(e)
    if attrs is None:
        return
    el = OxmlElement('w:' + tag)
    for k, v in attrs.items():
        el.set(qn('w:' + k), v)
    idx = _RPR_ORDER.index(tag)
    pos = len(rpr)
    for i, c in enumerate(rpr):
        ln = c.tag.split('}')[-1]
        if ln in _RPR_ORDER and _RPR_ORDER.index(ln) > idx:
            pos = i
            break
    rpr.insert(pos, el)


def _apply_fmt(rpr, bold=None, italic=None, underline=None, color=None):
    if bold is not None:
        set_rpr(rpr, 'b', {} if bold else {'val': '0'})
        set_rpr(rpr, 'bCs', {} if bold else {'val': '0'})
    if italic is not None:
        set_rpr(rpr, 'i', {} if italic else {'val': '0'})
        set_rpr(rpr, 'iCs', {} if italic else {'val': '0'})
    if underline is not None:
        set_rpr(rpr, 'u', {'val': 'single' if underline is True else (underline or 'none')})
    if color is not None:
        set_rpr(rpr, 'color', {'val': color} if color else None)


def new_run(rpr_proto, text, bold=None, italic=None, underline=None, color=None):
    """New w:r with a copy of rpr_proto (highlight and revision marks removed).

    '\\n' in text becomes a line break, '\\t' a tab. bold/italic/underline/color
    override the prototype only when not None (color: hex like '0000FF')."""
    r = OxmlElement('w:r')
    rpr = None
    if rpr_proto is not None:
        rpr = copy.deepcopy(rpr_proto)
        rpr.tag = w('rPr')
        strip_highlight(rpr)
        for tag in _REVISION_IN_RPR:
            for e in rpr.findall(w(tag)):
                rpr.remove(e)
        r.append(rpr)
    if any(v is not None for v in (bold, italic, underline, color)):
        if rpr is None:
            rpr = OxmlElement('w:rPr')
            r.append(rpr)
        _apply_fmt(rpr, bold, italic, underline, color)
    for i, line in enumerate(text.split('\n')):
        if i:
            r.append(OxmlElement('w:br'))
        for j, part in enumerate(line.split('\t')):
            if j:
                r.append(OxmlElement('w:tab'))
            if part:
                t = OxmlElement('w:t')
                t.text = part
                t.set(qn('xml:space'), 'preserve')
                r.append(t)
    return r


def append_run(p, text, rpr_proto=None, **fmt):
    """Append a new run to paragraph p; returns the run."""
    r = new_run(rpr_proto, text, **fmt)
    p.append(r)
    return r


def remove_runs(p, start=0, end=None) -> None:
    """Remove direct-child runs p.findall('w:r')[start:end] (keeps pPr, bookmarks)."""
    for r in p.findall(w('r'))[start:end]:
        p.remove(r)


def replace_span(p, old, new) -> None:
    """Replace the first occurrence of `old` in paragraph p with `new`.

    `old` may span several runs. The new text goes into the run that held most of
    `old` (keeping its formatting); highlight is removed from all affected runs.
    Raises LookupError if `old` is not in the paragraph text."""
    if hasattr(p, '_p'):
        p = p._p
    visible = (w('t'), w('tab'), w('br'), w('cr'))
    nodes = [c for r in _text_runs(p) for c in r if c.tag in visible]
    def node_text(node):
        return (node.text or '') if node.tag == w('t') else ('\t' if node.tag == w('tab') else '\n')
    full = ''.join(node_text(node) for node in nodes)
    idx = full.find(old)
    if idx < 0:
        raise LookupError('%r not found in %r' % (old, full[:200]))
    end = idx + len(old)
    pos, segs = 0, []
    for node in nodes:
        s, e = pos, pos + len(node_text(node))
        pos = e
        if e > idx and s < end:
            segs.append((node, s, e))
    if not segs:   # empty `old`
        raise LookupError('empty search text')
    target = max(segs, key=lambda sg: min(sg[2], end) - max(sg[1], idx))[0]
    target_run = target.getparent()
    rpr = target_run.find(w('rPr'))
    replacement = new_run(rpr, new)
    generated = [child for child in replacement if child.tag != w('rPr')]
    parent = target.getparent()
    insert_at = parent.index(target) + 1
    affected_runs = {node.getparent() for node, _, _ in segs}
    for node, s, e in segs:
        value = node_text(node)
        pre = value[:max(0, idx - s)]
        post = value[max(0, end - s):] if end < e else ''
        if node is target:
            if node.tag == w('t'):
                node.text = pre
                node.set(qn('xml:space'), 'preserve')
                for offset, child in enumerate(generated):
                    parent.insert(insert_at + offset, child)
                if post:
                    tail = next((child for child in reversed(generated) if child.tag == w('t')), None)
                    if tail is not None:
                        tail.text = (tail.text or '') + post
                    else:
                        t = OxmlElement('w:t'); t.text = post; t.set(qn('xml:space'), 'preserve')
                        parent.insert(insert_at + len(generated), t)
                elif not generated:
                    node.text = pre
            else:
                parent.remove(node)
                for offset, child in enumerate(generated):
                    parent.insert(insert_at - 1 + offset, child)
        elif node.tag == w('t'):
            node.text = pre + post
            node.set(qn('xml:space'), 'preserve')
        else:
            node.getparent().remove(node)
    for run in affected_runs:
        strip_highlight(run.find(w('rPr')))


def set_paragraph_text(p, text) -> None:
    """Replace all visible text of p with `text`, keeping the first text run's formatting
    and the paragraph properties (style, numbering, indent)."""
    visible = (w('t'), w('tab'), w('br'), w('cr'))
    runs = [r for r in _text_runs(p) if any(c.tag in visible for c in r)]
    if not runs:
        ppr = p.find(w('pPr'))
        proto = ppr.find(w('rPr')) if ppr is not None else None
        append_run(p, text, proto)
        strip_highlight(p.find(w('pPr')))
        return
    first = runs[0]
    insertion = 1 if first.find(w('rPr')) is not None else 0
    for c in list(first):
        if c.tag in visible:
            first.remove(c)
    for offset, c in enumerate(new_run(first.find(w('rPr')), text)):
        if c.tag != w('rPr'):
            first.insert(insertion + offset, c)
    for r in runs[1:]:
        for c in list(r):
            if c.tag in (w('t'), w('tab'), w('br'), w('cr')):
                r.remove(c)
    strip_highlight(first.find(w('rPr')))
    strip_highlight(p.find(w('pPr')))


def _proto_from(tc):
    for p in tc.findall(w('p')):
        rs = [r for r in p.findall(w('r')) if r.find(w('t')) is not None]
        if rs:
            return p, rs[0].find(w('rPr'))
    p = tc.find(w('p'))
    ppr = p.find(w('pPr')) if p is not None else None
    return p, (ppr.find(w('rPr')) if ppr is not None else None)


def fill_cell(tc, lines, proto_tc=None, **fmt) -> None:
    """Replace a cell's paragraphs with one paragraph per line.

    Paragraph and run formatting come from the first text-bearing paragraph of
    proto_tc (default: the cell itself; pass a deep copy of a template cell when
    filling blank cloned rows). '' gives an empty paragraph. fmt = bold/italic/
    underline/color overrides. Cell properties (width, borders, merges) are kept."""
    proto_p, proto_rpr = _proto_from(proto_tc if proto_tc is not None else tc)
    proto_p = copy.deepcopy(proto_p) if proto_p is not None else OxmlElement('w:p')
    proto_rpr = copy.deepcopy(proto_rpr) if proto_rpr is not None else None
    if isinstance(lines, str):
        lines = [lines]
    for p in tc.findall(w('p')):
        tc.remove(p)
    for line in lines:
        np_ = copy.deepcopy(proto_p)
        for c in list(np_):
            if c.tag != w('pPr'):
                np_.remove(c)
        strip_highlight(np_.find(w('pPr')))
        if line != '':
            np_.append(new_run(proto_rpr, line, **fmt))
        tc.append(np_)
    if not lines:   # a cell must contain at least one paragraph
        np_ = copy.deepcopy(proto_p)
        for c in list(np_):
            if c.tag != w('pPr'):
                np_.remove(c)
        tc.append(np_)


# --------------------------------------------------------------------------- structure
def clone(el):
    return copy.deepcopy(el)


def insert_after(ref, els):
    """Insert els (list) after ref, in order. Returns the last inserted element."""
    for e in els:
        ref.addnext(e)
        ref = e
    return ref


def clone_after(el, n=1) -> list:
    """Insert n deep copies of el directly after it. Returns the copies in order."""
    copies = [copy.deepcopy(el) for _ in range(n)]
    insert_after(el, copies)
    return copies


def remove(el) -> None:
    el.getparent().remove(el)


def is_blank(el) -> bool:
    """No visible text and no drawing/picture/text box."""
    if text_of(el).strip():
        return False
    return el.find('.//' + w('drawing')) is None and el.find('.//' + w('pict')) is None


def remove_blank_rows(tbl, first=1) -> int:
    """Remove completely blank rows from index `first` on. Returns how many were removed.
    Do NOT use on tables whose blank rows are intentional (revision history, sign-off)."""
    n = 0
    for tr in rows(tbl)[first:]:
        if is_blank(tr):
            remove(tr)
            n += 1
    return n


# --------------------------------------------------------------------------- carrying emphasis
def _on(rpr, tag):
    if rpr is None:
        return None
    e = rpr.find(w(tag))
    if e is None:
        return None
    return e.get(w('val'), 'true') not in ('0', 'false', 'none')


def run_specs(p) -> list:
    """Source paragraph -> [(text, {'bold','italic','underline','color'})] with only
    emphasis kept (no fonts/sizes/highlight; the template decides those).
    Adjacent runs with identical emphasis are merged."""
    if hasattr(p, '_p'):
        p = p._p
    out = []
    for r in _text_runs(p):
        txt = _run_text(r)
        if not txt:
            continue
        rpr = r.find(w('rPr'))
        col = rpr.find(w('color')) if rpr is not None else None
        color = col.get(w('val')) if col is not None and col.get(w('val')) not in (None, 'auto', '000000') else None
        fmt = {'bold': bool(_on(rpr, 'b')), 'italic': bool(_on(rpr, 'i')),
               'underline': bool(_on(rpr, 'u')), 'color': color}
        if out and out[-1][1] == fmt:
            out[-1] = (out[-1][0] + txt, fmt)
        else:
            out.append((txt, fmt))
    return out


def paragraph_from_specs(ppr_proto, specs, rpr_proto=None):
    """Build a new w:p: copy of ppr_proto (template paragraph properties) + runs from specs.
    Emphasis False/None in a spec leaves the prototype's value alone."""
    p = OxmlElement('w:p')
    if ppr_proto is not None:
        ppr = copy.deepcopy(ppr_proto)
        ppr.tag = w('pPr')
        strip_highlight(ppr)
        p.append(ppr)
    for text, fmt in specs:
        p.append(new_run(rpr_proto, text,
                         bold=True if fmt.get('bold') else None,
                         italic=True if fmt.get('italic') else None,
                         underline=True if fmt.get('underline') else None,
                         color=fmt.get('color') or None))
    return p


# --------------------------------------------------------------------------- images
def list_images(doc) -> list:
    """Images in body order: block index, rId, part name, content type, size in inches."""
    body = doc.element.body
    kids = list(body.iterchildren())
    pos = {id(k): i for i, k in enumerate(kids)}
    out = []
    for blip in body.iter('{%s}blip' % _A_NS):
        if _in_fallback(blip):
            continue
        rid = blip.get('{%s}embed' % _R_NS)
        top = blip
        while top.getparent() is not body:
            top = top.getparent()
        size = None
        for anc in blip.iterancestors():
            if anc.tag in ('{%s}inline' % _WP_NS, '{%s}anchor' % _WP_NS):
                e = anc.find('{%s}extent' % _WP_NS)
                if e is not None:
                    size = (round(int(e.get('cx')) / 914400, 2), round(int(e.get('cy')) / 914400, 2))
                break
        part = doc.part.related_parts.get(rid)
        out.append({'block': pos.get(id(top)), 'rid': rid,
                    'partname': str(part.partname) if part is not None else None,
                    'content_type': part.content_type if part is not None else None,
                    'size_in': size})
    return out


def extract_image(doc, rid, out_path) -> Path:
    """Write the image behind relationship rid to out_path (never overwrites)."""
    out_path = Path(out_path)
    blob = doc.part.related_parts[rid].blob
    with open(out_path, 'xb') as f:
        f.write(blob)
    return out_path


def text_width_inches(doc, section_index=0) -> float:
    s = doc.sections[section_index]
    if None in (s.page_width, s.left_margin, s.right_margin):
        raise ValueError('section %d has no page width/margins' % section_index)
    return (int(s.page_width) - int(s.left_margin) - int(s.right_margin)) / 914400


def put_picture(doc, p, image_path, width_in, section_index=0):
    """Replace the runs of paragraph p (e.g. an '<Add Diagram>' placeholder) with an
    inline picture `width_in` inches wide (height keeps aspect ratio). Body or table
    paragraphs only (not headers/footers). Returns the python-docx InlineShape."""
    limit = text_width_inches(doc, section_index)
    if width_in > limit + 1e-6:
        raise ValueError('picture wider than the text width (%.2f in)' % limit)
    remove_runs(p)
    strip_highlight(p.find(w('pPr')))
    run = Paragraph(p, doc).add_run()
    return run.add_picture(str(image_path), width=Inches(width_in))
