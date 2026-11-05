import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from docx import Document  # noqa: E402

import fixtures  # noqa: E402
from docx_helpers import (W_NS, append_run, assert_unchanged, body_blocks, cells, clone,  # noqa: E402
                          clone_after, copy_template, expect, extract_image, fill_cell, find_one,
                          list_images, new_run, open_docx, para_text, paragraph_from_specs,
                          put_picture, read_table, remove_blank_rows, replace_span, rows,
                          run_specs, set_paragraph_text, set_rpr, sha256_file, strip_highlight_if_filled,
                          tables, text_width_inches, w)


def highlighted(el):
    return any(True for _ in el.iter(w('highlight')))


class CopyTemplateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.tpl = fixtures.make_template(self.d / 'template.docx')

    def tearDown(self):
        self.tmp.cleanup()

    def test_copy_returns_digest_and_is_identical(self):
        before = sha256_file(self.tpl)
        out = self.d / 'out.docx'
        digest = copy_template(self.tpl, out)
        self.assertEqual(digest, before)
        self.assertEqual(sha256_file(out), before)
        assert_unchanged(self.tpl, digest)

    def test_refuses_existing_output(self):
        out = self.d / 'out.docx'
        out.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):
            copy_template(self.tpl, out)
        self.assertEqual(out.read_bytes(), b'existing')

    def test_refuses_symlink_output(self):
        link = self.d / 'link.docx'
        os.symlink(self.d / 'nowhere.docx', link)
        with self.assertRaises(FileExistsError):
            copy_template(self.tpl, link)
        self.assertFalse((self.d / 'nowhere.docx').exists())

    def test_missing_template_or_folder(self):
        with self.assertRaises(FileNotFoundError):
            copy_template(self.d / 'missing.docx', self.d / 'out.docx')
        with self.assertRaises(FileNotFoundError):
            copy_template(self.tpl, self.d / 'no_such_dir' / 'out.docx')

    def test_assert_unchanged_detects_change(self):
        digest = sha256_file(self.tpl)
        with open(self.tpl, 'ab') as f:
            f.write(b'x')
        with self.assertRaises(RuntimeError):
            assert_unchanged(self.tpl, digest)


class FillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.tpl = fixtures.make_template(self.d / 'template.docx')
        self.out = self.d / 'out.docx'
        self.digest = copy_template(self.tpl, self.out)
        self.doc = open_docx(self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def reopen(self):
        self.doc.save(str(self.out))
        assert_unchanged(self.tpl, self.digest)
        return open_docx(self.out)

    def test_replace_span_across_runs_keeps_format_and_unhighlights(self):
        p = find_one(self.doc, r'SYSTEM TITLE')
        replace_span(p, '<Add System Name>', 'Example System')
        self.assertIn('SYSTEM TITLE.  Example System Release <Add Version>', para_text(p))
        run = [r for r in p.findall(w('r')) if 'Example System' in ''.join(t.text or '' for t in r.iter(w('t')))][0]
        sz = run.find(w('rPr') + '/' + w('sz'))
        self.assertEqual(sz.get(w('val')), '28')  # 14 pt kept from the run holding most of the span
        self.assertIsNone(run.find(w('rPr') + '/' + w('highlight')))
        with self.assertRaises(LookupError):
            replace_span(p, '<Not There>', 'x')

    def test_replace_span_respects_tabs_and_emits_word_breaks(self):
        p = self.doc.add_paragraph()
        p.add_run('A')
        p.add_run('\t')
        p.add_run('B')
        with self.assertRaises(LookupError):
            replace_span(p._p, 'AB', 'wrong')
        replace_span(p._p, 'A\tB', 'line 1\nline 2')
        self.assertEqual(para_text(p._p), 'line 1\nline 2')
        self.assertEqual(len(list(p._p.iter(w('br')))), 1)
        self.assertEqual(len(list(p._p.iter(w('tab')))), 0)

    def test_strip_highlight_if_filled_only_when_no_placeholder_left(self):
        p = find_one(self.doc, r'SYSTEM TITLE')
        replace_span(p, '<Add System Name>', 'Example System')
        self.assertFalse(strip_highlight_if_filled(p))  # <Add Version> still there
        self.assertTrue(highlighted(p))
        replace_span(p, '<Add Version>', '1.0')
        self.assertTrue(highlighted(p))  # neighbour ' Release ' run still highlighted
        self.assertTrue(strip_highlight_if_filled(p))
        self.assertFalse(highlighted(p))
        doc = self.reopen()
        self.assertEqual(para_text(find_one(doc, 'SYSTEM TITLE')), 'SYSTEM TITLE.  Example System Release 1.0')

    def test_fill_cell_clone_rows_and_remove_blank(self):
        tbl = tables(self.doc)[0]
        r1 = rows(tbl)[1]
        proto = [clone(c) for c in cells(r1)]
        extra = clone_after(r1, 2)
        data = [('Alpha', '1', 'first'), ('Beta', '2', ''), ('Gamma', '3', 'line a\nline b')]
        for tr, vals in zip([r1] + extra, data):
            for tc, pc, v in zip(cells(tr), proto, vals):
                fill_cell(tc, v.split('\n') if '\n' in v else v, proto_tc=pc)
        self.assertEqual(remove_blank_rows(tbl), 1)  # the template's empty row
        doc = self.reopen()
        grid = read_table(doc.tables[0])
        self.assertEqual([r[0] for r in grid], ['Component', 'Alpha', 'Beta', 'Gamma', 'NOTE: sample note.'])
        self.assertEqual(grid[3][2], 'line a\nline b')
        t0 = tables(doc)[0]
        self.assertFalse(highlighted(t0))
        for tr in rows(t0)[1:4]:
            r = cells(tr)[0].find('.//' + w('r'))
            self.assertEqual(r.find(w('rPr') + '/' + w('sz')).get(w('val')), '18')  # 9 pt kept

    def test_fill_cell_bold_override(self):
        tc = cells(rows(tables(self.doc)[0])[1])[0]
        fill_cell(tc, 'Bold part', bold=True)
        b = tc.find('.//' + w('b'))
        self.assertIsNotNone(b)

    def test_find_one_errors_and_expect(self):
        with self.assertRaises(LookupError):
            find_one(self.doc, r'NO SUCH TEXT')
        with self.assertRaises(LookupError):
            find_one(self.doc, r'<Add')  # several paragraphs and cells
        p = find_one(self.doc, r'Boilerplate')
        expect(p, 'must not change')
        with self.assertRaises(AssertionError):
            expect(p, 'something else')

    def test_set_paragraph_text_keeps_style(self):
        p = find_one(self.doc, r'Boilerplate')
        set_paragraph_text(p, 'Replaced item')
        doc = self.reopen()
        para = [x for x in doc.paragraphs if x.text == 'Replaced item'][0]
        self.assertEqual(para.style.name, 'List Bullet')

    def test_set_paragraph_text_removes_tab_only_runs_and_emits_breaks(self):
        p = self.doc.add_paragraph()
        p.add_run('OLD')
        p.add_run('\t\n')
        set_paragraph_text(p._p, 'NEW\nLINE\tEND')
        self.assertEqual(para_text(p._p), 'NEW\nLINE\tEND')
        self.assertEqual(len(list(p._p.iter(w('br')))), 1)
        self.assertEqual(len(list(p._p.iter(w('tab')))), 1)

    def test_body_blocks_and_tables_indexing(self):
        blocks = body_blocks(self.doc)
        self.assertIs(blocks[3], tables(self.doc)[0])
        self.assertEqual(len(tables(self.doc)), len(self.doc.tables))


class RunTests(unittest.TestCase):
    def test_set_rpr_schema_order(self):
        r = new_run(None, 'x', color='0000FF')
        rpr = r.find(w('rPr'))
        set_rpr(rpr, 'sz', {'val': '20'})
        set_rpr(rpr, 'b', {})
        order = [c.tag.split('}')[1] for c in rpr]
        self.assertEqual(order, ['b', 'color', 'sz'])
        set_rpr(rpr, 'color', None)
        self.assertEqual([c.tag.split('}')[1] for c in rpr], ['b', 'sz'])

    def test_new_run_breaks_tabs_and_strips_revision_marks(self):
        proto = new_run(None, 'p', bold=True).find(w('rPr'))
        proto.append(fixtures.parse_xml('<w:highlight xmlns:w="%s" w:val="yellow"/>' % W_NS))
        r = new_run(proto, 'a\nb\tc')
        kinds = [c.tag.split('}')[1] for c in r]
        self.assertEqual(kinds, ['rPr', 't', 'br', 't', 'tab', 't'])
        self.assertIsNone(r.find(w('rPr') + '/' + w('highlight')))
        self.assertIsNotNone(r.find(w('rPr') + '/' + w('b')))

    def test_run_specs_and_paragraph_from_specs(self):
        with tempfile.TemporaryDirectory() as d:
            src = Document(str(fixtures.make_source(Path(d) / 's.docx', marking=False, tracked=False,
                                                    comment=False)))
            p = [x for x in src.paragraphs if x.text.startswith('Mitigation')][0]
            specs = run_specs(p)
            self.assertEqual(specs[0][0], 'Mitigation:')
            self.assertTrue(specs[0][1]['bold'])
            self.assertEqual(specs[1][1]['color'], '0000FF')
            ppr = fixtures.parse_xml('<w:pPr xmlns:w="%s"><w:ind w:left="720"/></w:pPr>' % W_NS)
            newp = paragraph_from_specs(ppr, specs)
            self.assertEqual(para_text(newp), 'Mitigation: Use ACLs.')
            runs = newp.findall(w('r'))
            self.assertIsNotNone(runs[0].find(w('rPr') + '/' + w('b')))
            self.assertEqual(runs[1].find(w('rPr') + '/' + w('color')).get(w('val')), '0000FF')
            self.assertIsNotNone(newp.find(w('pPr') + '/' + w('ind')))
            append_run(newp, ' tail')
            self.assertTrue(para_text(newp).endswith(' tail'))

    def test_read_table_resolves_vertical_merge(self):
        with tempfile.TemporaryDirectory() as d:
            src = Document(str(fixtures.make_source(Path(d) / 's.docx', marking=False, tracked=False,
                                                    comment=False)))
            grid = read_table(src.tables[0])
            self.assertEqual([r[0] for r in grid], ['Group', 'Group A', 'Group A'])
            raw = cells(rows(src.tables[0]._tbl)[2])[0]
            self.assertEqual(para_text(raw.find(w('p'))), '')  # continuation cell is empty


class PictureTests(unittest.TestCase):
    def test_put_list_extract_picture(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            tpl = fixtures.make_template(d / 't.docx')
            out = d / 'o.docx'
            copy_template(tpl, out)
            doc = open_docx(out)
            png = fixtures.write_png(d / 'img.png', 80, 40)
            p = find_one(doc, r'<Add Diagram>')
            with self.assertRaises(ValueError):
                put_picture(doc, p, png, text_width_inches(doc) + 1)
            shape = put_picture(doc, p, png, 2.0)
            self.assertAlmostEqual(shape.width.inches, 2.0, places=2)
            self.assertAlmostEqual(shape.height.inches, 1.0, places=2)
            self.assertFalse(highlighted(p))
            doc.save(str(out))
            doc = open_docx(out)
            imgs = list_images(doc)
            self.assertEqual(len(imgs), 1)
            self.assertEqual(imgs[0]['size_in'], (2.0, 1.0))
            target = extract_image(doc, imgs[0]['rid'], d / 'x.png')
            self.assertEqual(target.read_bytes(), png.read_bytes())
            with self.assertRaises(FileExistsError):
                extract_image(doc, imgs[0]['rid'], d / 'x.png')


if __name__ == '__main__':
    unittest.main()
