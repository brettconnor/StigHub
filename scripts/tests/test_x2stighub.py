"""Acceptance tests for scripts/x2stighub.spec.md (S1–S5)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'x2stighub.py'
FIELDS = {'requirement', 'vuldiscussion', 'status', 'check', 'severity',
          'fix', 'mitigation', 'artifact', 'justification'}


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input.xml'
        self.output = self.root / 'out'
        self.xml()

    def xml(self, namespace='1.1', names=('SRG-001',)):
        rules = ''.join(f'''<Rule severity="high"><version>{name}</version>
          <title>Requirement</title><description>&lt;VulnDiscussion&gt;Discussion
          &amp;amp; detail&lt;/VulnDiscussion&gt;</description>
          <check><check-content>Check</check-content></check><fixtext>Fix</fixtext>
          </Rule>''' for name in names)
        self.source.write_text(f'<Benchmark xmlns="http://checklists.nist.gov/xccdf/{namespace}">{rules}</Benchmark>')

    def run_cli(self, *extra, source=None, product='Cisco-IOS-XE'):
        return subprocess.run([sys.executable, str(SCRIPT), '--input',
            str(source or self.source), '--srg', 'VPN', '--product', product,
            '--output-root', str(self.output), *extra], text=True,
            capture_output=True, input='', cwd=self.root, timeout=30)

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def rejected(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Error:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def run_baseline(self, *extra, source=None):
        return subprocess.run([sys.executable, str(SCRIPT), '--input',
            str(source or self.source), '--srg', 'VPN', '--baseline-only',
            '--output-root', str(self.output), *extra], text=True,
            capture_output=True, input='', cwd=self.root, timeout=30)

    def test_baseline_only_populates_shared_rules(self):
        self.xml(names=('SRG-001', 'SRG-002'))
        self.success(self.run_baseline())
        self.assertEqual({p.name for p in (self.output / 'VPN').iterdir()},
                         {'SRG-001', 'SRG-002'})
        for name in ('SRG-001', 'SRG-002'):
            folder = self.output / 'VPN' / name
            self.assertEqual([p.name for p in folder.iterdir()], ['srg.txt'])
            content = (folder / 'srg.txt').read_text()
            for section in ('Severity:\nhigh', 'SRG Requirement:\nRequirement',
                            'SRG VulDiscussion:\nDiscussion', 'SRG Check:\nCheck',
                            'SRG Fix:\nFix'):
                self.assertIn(section, content)

    def test_baseline_only_preserves_authored_content_and_timestamps(self):
        self.success(self.run_baseline())
        target = self.output / 'VPN/SRG-001/srg.txt'
        target.write_bytes(b'Authored baseline\r\n')
        before = target.stat().st_mtime_ns
        self.success(self.run_baseline())
        self.assertEqual(target.read_bytes(), b'Authored baseline\r\n')
        self.assertEqual(target.stat().st_mtime_ns, before)

    def test_baseline_only_rejects_conflicting_product(self):
        self.rejected(self.run_baseline('--product', 'Cisco-IOS-XE'))
        self.assertFalse(self.output.exists())

    def test_baseline_only_excel_mapping(self):
        source = self.workbook()
        self.success(self.run_baseline('--start-row', '2', '--end-row', '2', source=source))
        self.assertEqual(list((self.output / 'VPN').iterdir()),
                         [self.output / 'VPN/SRG-001'])
        content = (self.output / 'VPN/SRG-001/srg.txt').read_text()
        for value in ('Severity:\nhigh', 'SRG Requirement:\nRequirement',
                      'SRG VulDiscussion:\nDiscussion', 'SRG Check:\nCheck',
                      'SRG Fix:\nFix'):
            self.assertIn(value, content)

    def test_xml_namespaces_and_legacy_content(self):
        for ns in ('1.1', '1.2'):
            with self.subTest(ns=ns):
                self.xml(namespace=ns)
                self.success(self.run_cli(product='Product-' + ns))
                baseline = self.output / 'VPN/SRG-001/srg.txt'
                self.assertEqual(baseline.read_text(), '\nSRG-001\n\nSeverity:\nhigh\n\nSRG Requirement:\nRequirement\n\nSRG VulDiscussion:\nDiscussion\n          & detail\n\nSRG Check:\nCheck\n\nSRG Fix:\nFix\n\n')
                folder = self.output / 'VPN' / ('Product-' + ns) / 'SRG-001'
                self.assertEqual({p.stem for p in folder.iterdir()}, FIELDS)
                self.assertTrue(all(p.read_bytes() == b'' for p in folder.iterdir()))

    def test_rerun_preserves_authored_files_and_fills_blanks(self):
        self.success(self.run_cli())
        folder = self.output / 'VPN/Cisco-IOS-XE/SRG-001'
        (folder / 'fix.txt').write_bytes(b'Authored\r\nfix\n')
        baseline = self.output / 'VPN/SRG-001/srg.txt'
        baseline.write_text(' \n')
        self.success(self.run_cli())
        self.assertEqual((folder / 'fix.txt').read_bytes(), b'Authored\r\nfix\n')
        self.assertIn('SRG Requirement:', baseline.read_text())
        saved = baseline.read_bytes()
        self.success(self.run_cli(product='Cisco-Secure-Firewall'))
        self.assertEqual(baseline.read_bytes(), saved)

    def test_read_only_authored_file_is_preserved(self):
        self.success(self.run_cli())
        target = self.output / 'VPN/Cisco-IOS-XE/SRG-001/fix.txt'
        target.write_bytes(b'Approved product fix\r\n')
        target.chmod(0o444)
        self.addCleanup(target.chmod, 0o644)
        self.success(self.run_cli())
        self.assertEqual(target.read_bytes(), b'Approved product fix\r\n')

    def test_invalid_rule_names_rejected_before_output(self):
        for name in ('../escape', '/absolute', 'a\\b', 'bad:name', '.'):
            with self.subTest(name=name):
                self.xml(names=('SRG-001', name))
                self.rejected(self.run_cli())
                self.assertFalse(self.output.exists())

    def test_invalid_product_and_layout_collision(self):
        for product in ('', '../escape', '/absolute', 'srg-001'):
            with self.subTest(product=product):
                self.rejected(self.run_cli(product=product))
                self.assertFalse(self.output.exists())

    def test_invalid_documents(self):
        for ns, names in [('9.9', ('SRG-001',)), ('1.1', ()),
                          ('1.1', ('',)), ('1.1', ('SRG-001', 'srg-001'))]:
            with self.subTest(ns=ns, names=names):
                self.xml(namespace=ns, names=names)
                self.rejected(self.run_cli())
                self.assertFalse(self.output.exists())

    def test_malformed_and_dtd_xml(self):
        for data in ('<broken>', '<!DOCTYPE Benchmark [<!ENTITY x "secret">]><Benchmark/>'):
            self.source.write_text(data)
            self.rejected(self.run_cli())
            self.assertFalse(self.output.exists())

    def test_xml_resource_limits(self):
        for data in ('<a>' * 130 + '</a>' * 130, ' ' * (32 * 1024 * 1024 + 1)):
            self.source.write_text(data)
            self.rejected(self.run_cli())
            self.assertFalse(self.output.exists())

    def test_element_limit_and_utf16_dtd(self):
        self.source.write_text('<Benchmark>' + '<a/>' * 200_001 + '</Benchmark>')
        self.rejected(self.run_cli())
        self.source.write_bytes(('<?xml version="1.0" encoding="UTF-16"?>'
                                 '<!DOCTYPE Benchmark [<!ENTITY x "secret">]>'
                                 '<Benchmark>&x;</Benchmark>').encode('utf-16'))
        self.rejected(self.run_cli())
        self.assertFalse(self.output.exists())

    def test_filesystem_conflicts_rejected_before_writing(self):
        self.output.mkdir()
        (self.output / 'VPN').write_text('existing file')
        self.rejected(self.run_cli())
        self.assertEqual((self.output / 'VPN').read_text(), 'existing file')
        (self.output / 'VPN').unlink()
        conflict = self.output / 'VPN/Cisco-IOS-XE/SRG-001/fix.txt'
        conflict.mkdir(parents=True)
        self.rejected(self.run_cli())
        self.assertFalse((self.output / 'VPN/SRG-001').exists())

    def test_missing_source_and_xml_row_range(self):
        self.rejected(self.run_cli(source=self.root / 'missing.xml'))
        self.rejected(self.run_cli('--start-row', '1', '--end-row', '2'))
        self.assertFalse(self.output.exists())

    def test_xml_and_help_do_not_require_site_packages(self):
        result = subprocess.run([sys.executable, '-S', str(SCRIPT), '--help'],
                                capture_output=True, text=True)
        self.success(result)
        result = subprocess.run([sys.executable, '-S', str(SCRIPT), '--input',
            str(self.source), '--srg', 'VPN', '--product', 'Generic',
            '--output-root', str(self.output)], capture_output=True, text=True)
        self.success(result)

    def test_reject_zip_and_partial_cli(self):
        archive = self.root / 'input.zip'
        archive.write_bytes(b'PK')
        result = self.run_cli(source=archive)
        self.rejected(result)
        self.assertIn('extract', result.stderr.lower())
        result = subprocess.run([sys.executable, str(SCRIPT), '--srg', 'VPN'],
                                input='', capture_output=True, text=True)
        self.rejected(result)
        self.assertFalse(self.output.exists())

    def test_symlink_directory_and_file_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        self.output.mkdir()
        (self.output / 'VPN').symlink_to(outside, target_is_directory=True)
        self.rejected(self.run_cli())
        self.assertEqual(list(outside.iterdir()), [])
        (self.output / 'VPN').unlink()
        self.success(self.run_cli())
        target = self.output / 'VPN/Cisco-IOS-XE/SRG-001/fix.txt'
        target.unlink()
        victim = outside / 'victim'
        victim.write_text('')
        target.symlink_to(victim)
        self.rejected(self.run_cli())
        self.assertEqual(victim.read_bytes(), b'')

    def test_interactive_prompt_compatibility(self):
        answers = f'VPN\n{self.source}\nCisco-IOS-XE\n'
        result = subprocess.run([sys.executable, str(SCRIPT)], input=answers,
                                text=True, capture_output=True, cwd=self.root)
        self.success(result)
        self.assertTrue((self.root / 'VPN/Cisco-IOS-XE/SRG-001/fix.txt').exists())

    def workbook(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        for col, text in {'C':'SRG-001', 'E':'Requirement', 'G':'Discussion',
                          'J':'Check', 'L':'Fix', 'N':'high', 'F':'Product requirement',
                          'H':'Product discussion', 'I':'Open', 'K':'Product check',
                          'M':'Product fix', 'O':'Mitigation', 'P':'Artifact',
                          'Q':'Justification'}.items():
            ws[f'{col}2'] = text
        source = self.root / 'input.xlsx'
        wb.save(source)
        wb.close()
        return source

    def test_excel_mapping(self):
        source = self.workbook()
        self.success(self.run_cli('--start-row', '1', '--end-row', '2', source=source))
        folder = self.output / 'VPN/Cisco-IOS-XE/SRG-001'
        values = {'requirement':'Product requirement','vuldiscussion':'Product discussion',
                  'status':'Open','check':'Product check','severity':'high','fix':'Product fix',
                  'mitigation':'Mitigation','artifact':'Artifact','justification':'Justification'}
        for field, value in values.items():
            self.assertEqual((folder / (field + '.txt')).read_text(), f'\n{field.upper()}:\n{value}\n\n')

    def test_excel_invalid_ranges(self):
        source = self.workbook()
        for start, end in [('0','2'),('2','1'),('1','3'),('abc','2')]:
            self.rejected(self.run_cli('--start-row', start, '--end-row', end, source=source))
            self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
