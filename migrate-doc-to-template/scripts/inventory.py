#!/usr/bin/env python3
"""Read-only inventory of a Word .docx file.

Lists, in document order, everything an agent needs before migrating content
into a template: body paragraphs (style, numbering, flags), tables (raw cells
with span/merge annotations), placeholders, highlighted text, text boxes,
images, headers/footers, file properties, tracked changes, comments, and
marking hits (CUI, distribution statements, classification banners, ...).

The file is never modified. See inventory.spec.md for the behavior contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

from lxml import etree

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'v': 'urn:schemas-microsoft-com:vml',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'op': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties',
    'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}
W = '{%s}' % NS['w']
R = '{%s}' % NS['r']
MC = '{%s}' % NS['mc']

# Package bounds. A normal report/guide is far below these.
MAX_ENTRIES = 5000
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_XML_PART_BYTES = 64 * 1024 * 1024

DEFAULT_MARKING_PATTERNS = [
    r'\bCUI\b',
    r'Controlled Unclassified',
    r'Distribution Statement',
    r'Distribution authorized',
    r'Controlled by\s*:',
    r'\bFOUO\b',
    r'For Official Use Only',
    r'\bNOFORN\b',
    r'\b(?:TOP SECRET|SECRET|CONFIDENTIAL|UNCLASSIFIED)//',
    r'Classified By\s*:',
    r'Derived From\s*:',
    r'Declassify On\s*:',
]

DEFAULT_PLACEHOLDER_PATTERNS = [
    r'<(?!https?://|mailto:)[^<>\n]{1,80}>',
    r'\[(?:Add|Insert|Enter|TBD)\b[^\]\n]{0,80}\]',
]

REVISION_TAGS = ['ins', 'del', 'moveFrom', 'moveTo', 'rPrChange', 'pPrChange',
                 'sectPrChange', 'tblPrChange', 'trPrChange', 'tcPrChange',
                 'tblGridChange', 'numberingChange']

STORY_ROOTS = {W + name for name in ('document', 'hdr', 'ftr', 'footnotes', 'endnotes', 'comments')}

_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                          dtd_validation=False, huge_tree=False)


class DocxError(Exception):
    """The input is missing, not a .docx, malformed, or outside safety bounds."""


# --------------------------------------------------------------------------- package
def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_parse(data: bytes, name: str):
    # XML's UTF-16/32 encodings interleave ASCII declaration bytes with NULs.
    # Removing NULs preserves markup token spellings while staying bounded by
    # MAX_XML_PART_BYTES and lets the rejection check cover the entire part.
    declaration_bytes = data.replace(b'\x00', b'')
    if re.search(rb'<!\s*(?:DOCTYPE|ENTITY)\b', declaration_bytes, re.I):
        raise DocxError('%s: DOCTYPE/ENTITY declarations are not allowed' % name)
    try:
        return etree.fromstring(data, _PARSER)
    except etree.XMLSyntaxError as exc:
        raise DocxError('%s: XML parse error: %s' % (name, exc)) from exc


class Package:
    """Bounded, read-only view of the XML parts of a .docx package."""

    def __init__(self, path):
        self.path = Path(path)
        if not self.path.is_file():
            raise DocxError('not a file: %s' % self.path)
        if not zipfile.is_zipfile(self.path):
            raise DocxError('not a .docx (zip) package: %s' % self.path)
        self.sha256 = sha256_file(self.path)
        self.xml_bytes = {}
        self.names = []
        try:
            with zipfile.ZipFile(self.path) as z:
                infos = z.infolist()
                if len(infos) > MAX_ENTRIES:
                    raise DocxError('too many package entries (%d)' % len(infos))
                total = 0
                for info in infos:
                    name = info.filename
                    pp = PurePosixPath(name)
                    if name.startswith('/') or '..' in pp.parts or '\\' in name or '\x00' in name:
                        raise DocxError('unsafe entry name: %r' % name)
                    total += info.file_size
                    if total > MAX_TOTAL_BYTES:
                        raise DocxError('package too large when uncompressed')
                    self.names.append(name)
                    if name.endswith(('.xml', '.rels')):
                        if info.file_size > MAX_XML_PART_BYTES:
                            raise DocxError('XML part too large: %s' % name)
                        self.xml_bytes[name] = z.read(info)
        except zipfile.BadZipFile as exc:
            raise DocxError('corrupt package: %s' % exc) from exc
        if 'word/document.xml' not in self.xml_bytes:
            raise DocxError('word/document.xml missing; not a Word document')
        self._cache = {}
        for name, data in self.xml_bytes.items():  # validate every XML part up front
            self._cache[name] = safe_parse(data, name)

    def xml(self, name):
        return self._cache.get(name)

    def parts(self, pattern):
        rx = re.compile(pattern)
        return sorted(n for n in self._cache if rx.match(n))

    def story_parts(self):
        return sorted(name for name, root in self._cache.items()
                      if etree.QName(root).namespace == NS['w']
                      and root.tag in STORY_ROOTS)

    def rels(self, part='word/document.xml'):
        p = PurePosixPath(part)
        relname = str(p.parent / '_rels' / (p.name + '.rels'))
        root = self.xml(relname)
        out = {}
        if root is None:
            return out
        for rel in root.findall('{%s}Relationship' % NS['rel']):
            out[rel.get('Id')] = (rel.get('Target'), rel.get('TargetMode'), rel.get('Type', '').rsplit('/', 1)[-1])
        return out


# --------------------------------------------------------------------------- text helpers
def _in(el, tag, stop=None):
    for anc in el.iterancestors():
        if anc is stop:
            return False
        if anc.tag == tag:
            return True
    return False


def in_fallback(el):
    return _in(el, MC + 'Fallback')


def para_text(p) -> str:
    """Visible text of a paragraph, excluding text boxes anchored in it."""
    out = []
    for r in p.iter(W + 'r'):
        if _in(r, W + 'txbxContent', stop=p):
            continue
        for c in r:
            if c.tag == W + 't':
                out.append(c.text or '')
            elif c.tag == W + 'tab':
                out.append('\t')
            elif c.tag in (W + 'br', W + 'cr'):
                out.append('\n')
    return ''.join(out)


def run_text(r) -> str:
    return ''.join((c.text or '') if c.tag == W + 't' else ('\t' if c.tag == W + 'tab' else '')
                   for c in r)


def short(s, width):
    s = s.replace('\n', ' / ').replace('\t', ' ')
    if width and len(s) > width:
        return s[:width - 3] + '...'
    return s


class Locator:
    """Maps any element in document.xml to a readable location label."""

    def __init__(self, body):
        self.body = body
        self.children = list(body.iterchildren())
        self.index = {id(c): i for i, c in enumerate(self.children)}
        self.tables = [c for c in self.children if c.tag == W + 'tbl']
        self.tindex = {id(t): i for i, t in enumerate(self.tables)}

    def __call__(self, el):
        if self.body is None:
            return '?'
        top = el
        while top is not None and top.getparent() is not self.body:
            top = top.getparent()
        if top is None:
            return '?'
        label = 'B%d' % self.index[id(top)]
        if id(top) in self.tindex:
            tbl = top
            chain = [el] + list(el.iterancestors())
            # the top-level table's own cell: a w:tc whose grandparent is the table
            tc = next((a for a in chain if a.tag == W + 'tc' and a.getparent() is not None
                       and a.getparent().getparent() is tbl), None)
            if tc is not None:
                tr = tc.getparent()
                label += ' T%d r%d c%d' % (self.tindex[id(tbl)], tbl.findall(W + 'tr').index(tr),
                                           tr.findall(W + 'tc').index(tc))
            else:
                label += ' T%d' % self.tindex[id(tbl)]
            if any(a.tag == W + 'tbl' and a is not tbl for a in chain[1:]):
                label += ' (nested table)'
        if _in(el, W + 'txbxContent'):
            label += ' textbox'
        return label


# --------------------------------------------------------------------------- scan
def scan(path, marking_patterns=None, placeholder_patterns=None):
    """Return a dict describing the document. Raises DocxError on bad input."""
    pkg = Package(path)
    marking_rx = [re.compile(p, re.I) for p in (marking_patterns if marking_patterns is not None
                                                else DEFAULT_MARKING_PATTERNS)]
    ph_rx = [re.compile(p) for p in (placeholder_patterns if placeholder_patterns is not None
                                     else DEFAULT_PLACEHOLDER_PATTERNS)]
    doc = pkg.xml('word/document.xml')
    body = doc.find(W + 'body')
    loc = Locator(body)
    rels = pkg.rels()

    # styles
    styles = {}
    st = pkg.xml('word/styles.xml')
    if st is not None:
        for s in st.findall(W + 'style'):
            n = s.find(W + 'name')
            styles[s.get(W + 'styleId')] = n.get(W + 'val') if n is not None else s.get(W + 'styleId')

    result = {
        'file': str(pkg.path), 'sha256': pkg.sha256,
        'summary': {}, 'properties': {}, 'headers_footers': [], 'sections': [], 'body': [],
        'placeholders': [], 'highlights': [], 'textboxes': [], 'images': [],
        'tracked_changes': {'counts': {}, 'authors': [], 'items': []},
        'comments': {'count': 0, 'references': 0, 'items': []}, 'markings': [],
    }

    # ---------------- body blocks
    def para_info(p, label):
        ppr = p.find(W + 'pPr')
        sid = ppr.find(W + 'pStyle').get(W + 'val') if ppr is not None and ppr.find(W + 'pStyle') is not None else None
        num = None
        if ppr is not None and ppr.find(W + 'numPr') is not None:
            npr = ppr.find(W + 'numPr')
            nid, ilvl = npr.find(W + 'numId'), npr.find(W + 'ilvl')
            num = '%s/%s' % (nid.get(W + 'val') if nid is not None else '?',
                             ilvl.get(W + 'val') if ilvl is not None else '0')
        flags = []
        if p.find('.//' + W + 'drawing') is not None or p.find('.//' + W + 'pict') is not None:
            if p.find('.//' + W + 'txbxContent') is not None:
                flags.append('TEXTBOX')
            if p.find('.//{%s}blip' % NS['a']) is not None or p.find('.//{%s}imagedata' % NS['v']) is not None:
                flags.append('IMAGE')
        brs = [b for b in p.iter(W + 'br') if not _in(b, W + 'txbxContent', stop=p)]
        if any(b.get(W + 'type') == 'page' for b in brs):
            flags.append('PAGEBREAK')
        if any(b.get(W + 'type') in (None, 'textWrapping') for b in brs):
            flags.append('LINEBREAKS')
        if ppr is not None and ppr.find(W + 'sectPr') is not None:
            flags.append('SECTIONBREAK')
        if any(r.find(W + 'rPr/' + W + 'highlight') is not None
               and r.find(W + 'rPr/' + W + 'highlight').get(W + 'val') != 'none'
               and run_text(r).strip() for r in p.iter(W + 'r') if not _in(r, W + 'txbxContent', stop=p)):
            flags.append('HIGHLIGHT')
        return {'loc': label, 'type': 'p', 'style': styles.get(sid, sid) if sid else 'Normal(default)',
                'num': num, 'flags': flags, 'text': para_text(p)}

    def table_info(tbl, label, tindex):
        grid = [g.get(W + 'w') for g in tbl.findall(W + 'tblGrid/' + W + 'gridCol')]
        tpr = tbl.find(W + 'tblPr')
        sid = tpr.find(W + 'tblStyle').get(W + 'val') if tpr is not None and tpr.find(W + 'tblStyle') is not None else None
        rows = []
        for tr in tbl.findall(W + 'tr'):
            cells = []
            for tc in tr.findall(W + 'tc'):
                tcpr = tc.find(W + 'tcPr')
                span = vm = None
                if tcpr is not None:
                    gs = tcpr.find(W + 'gridSpan')
                    span = int(gs.get(W + 'val')) if gs is not None else None
                    v = tcpr.find(W + 'vMerge')
                    if v is not None:
                        vm = v.get(W + 'val') or 'continue'
                text = ' / '.join(para_text(p) for p in tc.findall(W + 'p') if para_text(p).strip())
                nested = [table_info(child, '%s r%d c%d nested%d' % (label, len(rows), len(cells), ni), None)
                          for ni, child in enumerate(tc.findall(W + 'tbl'))]
                cells.append({'text': text, 'span': span, 'vmerge': vm, 'tables': nested})
            rows.append(cells)
        return {'loc': label, 'type': 'table', 'table_index': tindex, 'style': styles.get(sid, sid),
                'grid_cols': len(grid), 'rows': rows}

    def walk(children, prefix):
        for i, c in enumerate(children):
            label = '%s%d' % (prefix, i) if prefix == 'B' else '%s[%d]' % (prefix, i)
            if c.tag == W + 'p':
                result['body'].append(para_info(c, label))
            elif c.tag == W + 'tbl':
                ti = loc.tindex.get(id(c))
                result['body'].append(table_info(c, label + (' T%d' % ti if ti is not None else ''), ti))
            elif c.tag == W + 'sdt':
                content = c.find(W + 'sdtContent')
                if content is not None:
                    walk(list(content), label + '/sdt')

    if body is not None:
        walk(list(body.iterchildren()), 'B')

    # ---------------- sections
    for sp in doc.iter(W + 'sectPr'):
        if _in(sp, W + 'pPrChange') or _in(sp, W + 'sectPrChange'):
            continue
        pg, mar = sp.find(W + 'pgSz'), sp.find(W + 'pgMar')

        def tw(el, attr):
            v = el.get(W + attr) if el is not None else None
            return int(v) if v and v.lstrip('-').isdigit() else None
        wdt, lm, rm = tw(pg, 'w'), tw(mar, 'left'), tw(mar, 'right')
        result['sections'].append({
            'page_w_in': round(wdt / 1440, 2) if wdt else None,
            'page_h_in': round(tw(pg, 'h') / 1440, 2) if tw(pg, 'h') else None,
            'margin_l_in': round(lm / 1440, 2) if lm is not None else None,
            'margin_r_in': round(rm / 1440, 2) if rm is not None else None,
            'text_width_in': round((wdt - lm - rm) / 1440, 2) if None not in (wdt, lm, rm) else None,
            'orientation': pg.get(W + 'orient', 'portrait') if pg is not None else None,
        })

    # ---------------- story parts: placeholders, highlights, textboxes, markings, revisions
    seen_tb, seen_mark = set(), set()
    authors = set()
    for part in pkg.story_parts():
        root = pkg.xml(part)
        is_doc = part == 'word/document.xml'

        def where(el):
            return loc(el) if is_doc else part

        for p in root.iter(W + 'p'):
            if in_fallback(p):
                continue
            text = para_text(p)
            label = where(p)
            for rx in ph_rx:
                for m in rx.finditer(text):
                    result['placeholders'].append({'loc': label, 'text': m.group(0)})
            hl = []
            for r in p.iter(W + 'r'):
                if _in(r, W + 'txbxContent', stop=p):
                    continue
                h = r.find(W + 'rPr/' + W + 'highlight')
                if h is not None and h.get(W + 'val') != 'none' and run_text(r).strip():
                    hl.append(run_text(r))
            if hl:
                result['highlights'].append({'loc': label, 'color_runs': hl, 'paragraph': text})
            for rx in marking_rx:
                for m in rx.finditer(text):
                    key = (label, m.group(0), text)
                    if key in seen_mark:
                        continue
                    seen_mark.add(key)
                    s = max(0, m.start() - 60)
                    result['markings'].append({'loc': label, 'pattern': rx.pattern, 'match': m.group(0),
                                               'context': text[s:m.end() + 60]})
        for tb in root.iter(W + 'txbxContent'):
            if in_fallback(tb):
                continue
            text = ' | '.join(para_text(p) for p in tb.findall('.//' + W + 'p') if para_text(p).strip())
            key = (where(tb), text)
            if text and key not in seen_tb:
                seen_tb.add(key)
                result['textboxes'].append({'loc': where(tb), 'text': text})
        for tag in REVISION_TAGS:
            for el in root.iter(W + tag):
                if in_fallback(el):
                    continue
                result['tracked_changes']['counts'][tag] = result['tracked_changes']['counts'].get(tag, 0) + 1
                a = el.get(W + 'author')
                if a:
                    authors.add(a)
                if tag in ('ins', 'del', 'moveFrom', 'moveTo'):
                    txt = ''.join(t.text or '' for t in el.iter(W + 't', W + 'delText'))
                    result['tracked_changes']['items'].append({'loc': where(el), 'type': tag, 'author': a,
                                                               'text': txt})
        if is_doc:
            result['comments']['references'] = len(list(root.iter(W + 'commentReference')))
    result['tracked_changes']['authors'] = sorted(authors)

    cm = pkg.xml('word/comments.xml')
    if cm is not None:
        for c in cm.findall(W + 'comment'):
            result['comments']['items'].append({
                'author': c.get(W + 'author'),
                'text': ' / '.join(para_text(p) for p in c.findall('.//' + W + 'p') if para_text(p).strip())})
        result['comments']['count'] = len(result['comments']['items'])

    # ---------------- headers / footers
    for part in pkg.story_parts():
        root = pkg.xml(part)
        if root.tag not in (W + 'hdr', W + 'ftr'):
            continue
        texts = [para_text(p) for p in root.iter(W + 'p')
                 if not in_fallback(p) and para_text(p).strip()]
        result['headers_footers'].append({'part': part, 'text': texts})

    # ---------------- images
    a_blip, v_img = '{%s}blip' % NS['a'], '{%s}imagedata' % NS['v']
    for el in doc.iter(a_blip, v_img):
        if in_fallback(el):
            continue
        rid = el.get(R + 'embed') or el.get(R + 'link') or el.get(R + 'id')
        target = rels.get(rid, (None,))[0]
        ext = None
        for anc in el.iterancestors():
            if anc.tag in ('{%s}inline' % NS['wp'], '{%s}anchor' % NS['wp']):
                e = anc.find('{%s}extent' % NS['wp'])
                if e is not None:
                    ext = (round(int(e.get('cx')) / 914400, 2), round(int(e.get('cy')) / 914400, 2))
                kind = anc.tag.split('}')[1]
                break
        else:
            kind = 'vml'
        result['images'].append({'loc': loc(el), 'rid': rid, 'target': target, 'size_in': ext, 'kind': kind})

    # ---------------- properties
    props = {}
    core = pkg.xml('docProps/core.xml')
    if core is not None:
        for c in core:
            if c.text and c.text.strip():
                props['core.' + etree.QName(c).localname] = c.text.strip()
    app = pkg.xml('docProps/app.xml')
    if app is not None:
        for key in ('Company', 'Manager', 'Template'):
            e = app.find('{%s}%s' % (NS['ep'], key))
            if e is not None and e.text:
                props['app.' + key] = e.text
    custom = pkg.xml('docProps/custom.xml')
    if custom is not None:
        for prop in custom.findall('{%s}property' % NS['op']):
            val = ''.join(prop.itertext()).strip()
            props['custom.' + (prop.get('name') or '?')] = val
    people = pkg.xml('word/people.xml')
    if people is not None:
        names = [p.get('{%s}author' % NS['w15']) for p in people.iter('{%s}person' % NS['w15'])]
        if names:
            props['people.authors'] = '; '.join(n for n in names if n)
    result['properties'] = props
    for k, v in props.items():   # markings in metadata
        for rx in marking_rx:
            m = rx.search(v)
            if m:
                result['markings'].append({'loc': 'properties:' + k, 'pattern': rx.pattern,
                                           'match': m.group(0), 'context': v[:200]})
    for part in pkg.parts(r'^docMetadata/.*\.xml$'):
        txt = ' '.join(pkg.xml(part).itertext()) + ' ' + ' '.join(
            str(v) for e in pkg.xml(part).iter() for v in e.attrib.values())
        for rx in marking_rx:
            m = rx.search(txt)
            if m:
                result['markings'].append({'loc': part, 'pattern': rx.pattern, 'match': m.group(0),
                                           'context': txt[:200]})

    # ---------------- summary
    tc = result['tracked_changes']['counts']
    result['summary'] = {
        'paragraphs': sum(1 for b in result['body'] if b['type'] == 'p'),
        'tables': sum(1 for b in result['body'] if b['type'] == 'table'),
        'sections': len(result['sections']),
        'images': len(result['images']),
        'textboxes': len(result['textboxes']),
        'placeholders': len(result['placeholders']),
        'highlighted_paragraphs': len(result['highlights']),
        'tracked_changes': sum(tc.values()),
        'comments': result['comments']['count'],
        'marking_hits': len(result['markings']),
    }
    return result


# --------------------------------------------------------------------------- report
def render(res, width=160, show_body=True):
    out = []
    add = out.append

    def render_nested(tbl, depth=0):
        for row in tbl['rows']:
            for cell in row:
                for nested in cell.get('tables', []):
                    add('  ' * depth + '%s TABLE rows=%d grid_cols=%d' %
                        (nested['loc'], len(nested['rows']), nested['grid_cols']))
                    for ri, nrow in enumerate(nested['rows']):
                        values = ['[c%d] %s' % (nci, short(ncell['text'],
                                   0 if width == 0 else max(20, width // 3)))
                                  for nci, ncell in enumerate(nrow)]
                        add('  ' * (depth + 1) + 'r%d: %s' % (ri, ' | '.join(values)))
                    render_nested(nested, depth + 1)
    add('FILE: %s' % res['file'])
    add('SHA-256: %s' % res['sha256'])
    add('')
    add('== SUMMARY ==')
    for k, v in res['summary'].items():
        add('  %-22s %s' % (k, v))
    add('')
    add('== PROPERTIES ==')
    for k, v in res['properties'].items():
        add('  %s = %s' % (k, short(v, width)))
    add('')
    add('== HEADERS / FOOTERS ==')
    for hf in res['headers_footers']:
        add('  %s: %s' % (hf['part'], ' | '.join(short(t, width) for t in hf['text']) or '(empty)'))
    add('')
    add('== SECTIONS ==')
    for i, s in enumerate(res['sections']):
        add('  S%d: page %sx%s in, margins L%s R%s, text width %s in, %s' % (
            i, s['page_w_in'], s['page_h_in'], s['margin_l_in'], s['margin_r_in'],
            s['text_width_in'], s['orientation']))
    if show_body:
        add('')
        add('== BODY (B# = index in body children; T# = doc.tables index; cells are raw w:tc) ==')
        for b in res['body']:
            if b['type'] == 'p':
                if not b['text'].strip() and not b['flags']:
                    continue
                add('  %-8s P [%s]%s%s %s' % (b['loc'], b['style'], ' num=' + b['num'] if b['num'] else '',
                                             ' {' + ','.join(b['flags']) + '}' if b['flags'] else '',
                                             short(b['text'].strip(), width)))
            else:
                add('  %-8s TABLE rows=%d grid_cols=%d style=%s' % (b['loc'], len(b['rows']), b['grid_cols'],
                                                                     b['style']))
                for ri, row in enumerate(b['rows']):
                    cells = []
                    for ci, c in enumerate(row):
                        tag = 'c%d' % ci
                        if c['span']:
                            tag += ' span=%d' % c['span']
                        if c['vmerge']:
                            tag += ' vm=%s' % c['vmerge']
                        cells.append('[%s] %s' % (tag, short(c['text'],
                                                              0 if width == 0 else max(20, width // 3))))
                    add('      r%d: %s' % (ri, ' | '.join(cells)))
                render_nested(b)
    add('')
    add('== PLACEHOLDERS ==')
    for p in res['placeholders']:
        add('  %-22s %s' % (p['loc'], short(p['text'], width)))
    add('')
    add('== HIGHLIGHTED TEXT ==')
    for h in res['highlights']:
        add('  %-22s runs=%s' % (h['loc'], short(repr(h['color_runs']), width)))
    add('')
    add('== TEXT BOXES ==')
    for t in res['textboxes']:
        add('  %-22s %s' % (t['loc'], short(t['text'], width)))
    add('')
    add('== IMAGES ==')
    for im in res['images']:
        add('  %-22s %s %s size_in=%s (%s)' % (im['loc'], im['rid'], im['target'], im['size_in'], im['kind']))
    add('')
    add('== TRACKED CHANGES ==')
    tc = res['tracked_changes']
    add('  counts: %s' % (tc['counts'] or 'none'))
    add('  authors: %s' % (tc['authors'] or 'none'))
    for it in tc['items']:
        add('  %-22s %s by %s: %s' % (it['loc'], it['type'], it['author'], short(it['text'], width)))
    add('')
    add('== COMMENTS ==')
    add('  comments: %d, references in body: %d' % (res['comments']['count'], res['comments']['references']))
    for c in res['comments']['items']:
        add('  %s: %s' % (c['author'], short(c['text'], width)))
    add('')
    add('== MARKINGS (never copy these into the output) ==')
    if not res['markings']:
        add('  none found (default patterns are a safety net, not a guarantee)')
    for m in res['markings']:
        add('  %-22s %r in: %s' % (m['loc'], m['match'], short(m['context'], width)))
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Read-only inventory of a .docx file.')
    ap.add_argument('docx', help='path to a .docx file')
    ap.add_argument('--json', action='store_true', help='print JSON instead of text')
    ap.add_argument('--full', action='store_true', help='do not truncate text')
    ap.add_argument('--width', type=int, default=160, help='truncate text to N chars (default 160)')
    ap.add_argument('--no-body', action='store_true', help='omit the body listing')
    ap.add_argument('--pattern', action='append', default=[], metavar='REGEX',
                    help='extra marking pattern (case-insensitive); repeatable')
    ap.add_argument('--no-default-patterns', action='store_true', help='do not use built-in marking patterns')
    ap.add_argument('--placeholder', action='append', default=[], metavar='REGEX',
                    help='extra placeholder pattern; repeatable')
    args = ap.parse_args(argv)
    marks = ([] if args.no_default_patterns else list(DEFAULT_MARKING_PATTERNS)) + args.pattern
    phs = list(DEFAULT_PLACEHOLDER_PATTERNS) + args.placeholder
    try:
        for p in marks + phs:
            re.compile(p)
    except re.error as exc:
        print('error: invalid regex: %s' % exc, file=sys.stderr)
        return 2
    try:
        res = scan(args.docx, marks, phs)
    except DocxError as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, indent=1))
    else:
        print(render(res, width=0 if args.full else args.width, show_body=not args.no_body))
    return 0


if __name__ == '__main__':
    sys.exit(main())
