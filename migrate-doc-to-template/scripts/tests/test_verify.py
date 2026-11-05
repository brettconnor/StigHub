import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))

import fixtures  # noqa: E402
from docx_helpers import (cells, clone, clone_after, copy_template, fill_cell, find_one,  # noqa: E402
                          open_docx, put_picture, replace_span, rows, sha256_file,
                          strip_highlight_if_filled, tables)


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPTS / 'verify.py'), *map(str, args)],
                          capture_output=True, text=True)


class VerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = cls.d = Path(cls.tmp.name)
        cls.tpl = fixtures.make_template(d / 'template.docx')
        cls.src = fixtures.make_source(d / 'source.docx')
        cls.tpl_sha = sha256_file(cls.tpl)
        cls.src_sha = sha256_file(cls.src)
        # a fully filled output
        cls.out = d / 'filled.docx'
        copy_template(cls.tpl, cls.out)
        doc = open_docx(cls.out)
        p = find_one(doc, 'SYSTEM TITLE')
        replace_span(p, '<Add System Name>', 'Example System')
        replace_span(p, '<Add Version>', '1.0')
        strip_highlight_if_filled(p)
        tbl = tables(doc)[0]
        r1 = rows(tbl)[1]
        proto = [clone(c) for c in cells(r1)]
        r2 = clone_after(r1)[0]
        for tr, vals in ((r1, ('A', '1', 'n1')), (r2, ('B', '2', 'n2'))):
            for tc, pc, v in zip(cells(tr), proto, vals):
                fill_cell(tc, v, proto_tc=pc)
        put_picture(doc, find_one(doc, '<Add Diagram>'), fixtures.write_png(d / 'i.png'), 1.0)
        doc.save(str(cls.out))
        # a partially filled output (placeholders remain)
        cls.partial = d / 'partial.docx'
        copy_template(cls.tpl, cls.partial)
        doc = open_docx(cls.partial)
        replace_span(find_one(doc, 'SYSTEM TITLE'), '<Add System Name>', 'Example System')
        doc.save(str(cls.partial))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_filled_output_passes(self):
        r = run_cli('--output', self.out, '--unchanged', self.tpl, self.tpl_sha,
                    '--unchanged', self.src, self.src_sha, '--strict')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('RESULT: PASS', r.stdout)

    def test_changed_input_fails(self):
        r = run_cli('--output', self.out, '--unchanged', self.tpl, '0' * 64)
        self.assertEqual(r.returncode, 1)
        self.assertIn('FAIL  input unchanged', r.stdout)

    def test_placeholders_warn_or_fail_with_strict(self):
        r = run_cli('--output', self.partial)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('WARN  placeholders remaining', r.stdout)
        self.assertIn('<Add Version>', r.stdout)
        self.assertIn('WARN  highlighted text remaining', r.stdout)
        r = run_cli('--output', self.partial, '--strict')
        self.assertEqual(r.returncode, 1)

    def test_identical_output_warns(self):
        r = run_cli('--output', self.tpl.parent / 'filled.docx', '--unchanged', self.tpl, self.tpl_sha)
        self.assertNotIn('byte-identical', r.stdout)
        copy = self.d / 'same.docx'
        if not copy.exists():
            copy_template(self.tpl, copy)
        r = run_cli('--output', copy, '--unchanged', self.tpl, self.tpl_sha)
        self.assertIn('byte-identical', r.stdout)

    def test_revisions_comments_markings_fail(self):
        r = run_cli('--output', self.src, '--json')
        self.assertEqual(r.returncode, 1)
        data = json.loads(r.stdout)
        levels = {c['check']: c['level'] for c in data['checks']}
        self.assertEqual(levels['no tracked changes'], 'FAIL')
        self.assertEqual(levels['no markings/forbidden text'], 'FAIL')
        if hasattr(__import__('docx').document.Document, 'add_comment'):
            self.assertEqual(levels['no comments'], 'FAIL')
        r = run_cli('--output', self.src, '--allow-revisions', '--allow-comments', '--no-default-patterns')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('WARN  no tracked changes', r.stdout)

    def test_forbid_pattern(self):
        r = run_cli('--output', self.out, '--forbid', 'boilerplate')
        self.assertEqual(r.returncode, 1)
        self.assertIn("'Boilerplate'", r.stdout)

    def test_usage_errors(self):
        r = run_cli('--output', self.out, '--unchanged', self.tpl, 'nothex')
        self.assertEqual(r.returncode, 2)
        r = run_cli('--output', self.out, '--unchanged', self.out, self.tpl_sha)
        self.assertEqual(r.returncode, 2)
        r = run_cli('--output', self.d / 'missing.docx')
        self.assertEqual(r.returncode, 2)
        r = run_cli('--output', self.out, '--forbid', '(')
        self.assertEqual(r.returncode, 2)

    def test_output_not_modified(self):
        before = sha256_file(self.out)
        run_cli('--output', self.out)
        self.assertEqual(sha256_file(self.out), before)


if __name__ == '__main__':
    unittest.main()
