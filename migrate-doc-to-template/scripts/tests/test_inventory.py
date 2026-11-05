import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))

import fixtures  # noqa: E402
from inventory import DocxError, safe_parse, scan  # noqa: E402


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPTS / 'inventory.py'), *map(str, args)],
                          capture_output=True, text=True)


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.png = fixtures.write_png(d / 'img.png')
        cls.tpl = fixtures.make_template(d / 'template.docx')
        cls.src = fixtures.make_source(d / 'source.docx', image_path=cls.png)
        cls.d = d

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_template_placeholders_highlights_tables(self):
        res = scan(self.tpl)
        found = [p['text'] for p in res['placeholders']]
        for ph in ('<Add System Name>', '<Add Version>', '<Add Component>', '<#>', '<Add Notes>',
                   '<Add Diagram>'):
            self.assertIn(ph, found)
        self.assertNotIn('<https://example.com/guide>', found)
        locs = {p['text']: p['loc'] for p in res['placeholders']}
        self.assertRegex(locs['<Add Component>'], r'^B\d+ T0 r1 c0$')
        self.assertTrue(res['highlights'])
        table = [b for b in res['body'] if b['type'] == 'table'][0]
        self.assertEqual(table['rows'][3][0]['span'], 3)
        self.assertEqual(res['headers_footers'][0]['text'], ['Example Public'])
        self.assertEqual(res['markings'], [])
        self.assertEqual(res['sections'][0]['text_width_in'], 6.0)
        self.assertEqual(len(res['sha256']), 64)

    def test_source_markings_textbox_revisions_comments_images(self):
        res = scan(self.src)
        matches = {m['match'] for m in res['markings']}
        self.assertTrue({'CUI', 'Distribution Statement', 'Controlled by:'} <= matches, matches)
        self.assertTrue(all('textbox' in m['loc'] for m in res['markings']))
        self.assertIn('CUI Category: TEST', res['textboxes'][0]['text'])
        self.assertEqual(res['tracked_changes']['authors'], ['Test Reviewer'])
        self.assertEqual(res['tracked_changes']['items'][0]['text'], 'inserted text')
        self.assertEqual(len(res['images']), 1)
        self.assertEqual(res['properties']['core.creator'], 'Source Author')
        body_text = ' '.join(b.get('text', '') for b in res['body'])
        self.assertNotIn('CUI', body_text)  # text-box text is not merged into paragraph text
        merged = [b for b in res['body'] if b['type'] == 'table'][0]['rows']
        self.assertEqual(merged[1][0]['vmerge'], 'restart')
        self.assertEqual(merged[2][0]['vmerge'], 'continue')

    @unittest.skipUnless(hasattr(__import__('docx').document.Document, 'add_comment'),
                         'python-docx without comment support')
    def test_comments(self):
        res = scan(self.src)
        self.assertEqual(res['comments']['count'], 1)
        self.assertEqual(res['comments']['items'][0]['author'], 'Test Reviewer')

    def test_custom_patterns(self):
        res = scan(self.src, marking_patterns=[r'Example Agency'])
        self.assertEqual([m['match'] for m in res['markings']], ['Example Agency'])
        res = scan(self.tpl, placeholder_patterns=[r'NOTE:'])
        self.assertEqual([p['text'] for p in res['placeholders']], ['NOTE:'])

    def test_cli_text_and_json(self):
        r = run_cli(self.src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('== MARKINGS', r.stdout)
        self.assertIn('Test Reviewer', r.stdout)
        r = run_cli(self.tpl, '--json')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn('placeholders', data)
        r = run_cli(self.src, '--no-default-patterns', '--pattern', 'Example Agency', '--no-body')
        self.assertIn("'Example Agency'", r.stdout)
        self.assertNotIn("'CUI'", r.stdout)

    def test_full_report_does_not_truncate_table_cells(self):
        docx = self.d / 'full-table.docx'
        from docx import Document
        doc = Document()
        doc.add_table(rows=1, cols=1).cell(0, 0).text = 'CELL_SENTINEL_' + ('x' * 80)
        doc.save(docx)
        r = run_cli(docx, '--full')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('CELL_SENTINEL_' + ('x' * 80), r.stdout)

    def test_nested_tables_are_inventoried_recursively(self):
        from docx import Document
        docx = self.d / 'nested.docx'
        doc = Document()
        outer = doc.add_table(rows=1, cols=1)
        outer.cell(0, 0).text = 'OUTER_SENTINEL'
        outer.cell(0, 0).add_table(rows=1, cols=1).cell(0, 0).text = 'NESTED_SENTINEL'
        doc.save(docx)
        res = scan(docx)
        body_table = next(b for b in res['body'] if b['type'] == 'table')
        self.assertIn('NESTED_SENTINEL', json.dumps(body_table))
        r = run_cli(docx, '--full')
        self.assertIn('NESTED_SENTINEL', r.stdout + r.stderr)

    def test_relationship_named_header_is_scanned_for_markings(self):
        from docx import Document
        docx = self.d / 'renamed-header.docx'
        temp = self.d / 'header-source.docx'
        doc = Document()
        doc.sections[0].header.paragraphs[0].text = 'CUI'
        doc.save(temp)
        with zipfile.ZipFile(temp) as src, zipfile.ZipFile(docx, 'w', zipfile.ZIP_DEFLATED) as out:
            for info in src.infolist():
                name = info.filename
                data = src.read(name)
                if name == 'word/header1.xml':
                    name = 'word/notice.xml'
                elif name == 'word/_rels/document.xml.rels':
                    data = data.replace(b'Target="header1.xml"', b'Target="notice.xml"')
                out.writestr(name, data)
        res = scan(docx)
        self.assertTrue(any(m['match'] == 'CUI' for m in res['markings']), res['markings'])

    def test_rejects_dtd_late_and_utf16_encoded(self):
        payloads = [b' ' * 65536 + b'<!DOCTYPE x><x/>', '<!DOCTYPE x><x/>'.encode('utf-16')]
        for payload in payloads:
            with self.subTest(payload=payload[:4]):
                with self.assertRaises(DocxError):
                    safe_parse(payload, 'synthetic.xml')

    def test_rejects_bad_input(self):
        txt = self.d / 'not.docx'
        txt.write_text('plain text')
        r = run_cli(txt)
        self.assertEqual(r.returncode, 2)
        self.assertIn('not a .docx', r.stderr)
        r = run_cli(self.d / 'missing.docx')
        self.assertEqual(r.returncode, 2)
        bad = fixtures.make_doctype_docx(self.tpl, self.d / 'doctype.docx')
        with self.assertRaises(DocxError):
            scan(bad)
        r = run_cli(bad)
        self.assertEqual(r.returncode, 2)
        self.assertIn('DOCTYPE', r.stderr)
        r = run_cli(self.tpl, '--pattern', '(')
        self.assertEqual(r.returncode, 2)

    def test_input_not_modified(self):
        from inventory import sha256_file
        before = sha256_file(self.src)
        scan(self.src)
        run_cli(self.src, '--json')
        self.assertEqual(sha256_file(self.src), before)


if __name__ == '__main__':
    unittest.main()
