"""Acceptance tests for extract_srg.spec.md, E1–E4."""
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'extract_srg.py'


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / 'input.zip'
        self.output = self.root / 'out'

    def archive_with(self, entries):
        with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in entries:
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', message='Duplicate name:')
                    archive.writestr(name, data)

    def run_cli(self, source=None):
        return subprocess.run([sys.executable, str(SCRIPT), str(source or self.archive),
                               '--output-dir', str(self.output)], cwd=self.root,
                              text=True, capture_output=True, timeout=30)

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def rejected(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Error:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_extracts_structure_and_binary_bytes(self):
        self.archive_with([('Manual/', b''), ('Manual/rules.xml', b'<Benchmark/>'),
                           ('overview.pdf', b'\x00\xffbinary')])
        self.success(self.run_cli())
        self.assertEqual((self.output / 'Manual/rules.xml').read_bytes(), b'<Benchmark/>')
        self.assertEqual((self.output / 'overview.pdf').read_bytes(), b'\x00\xffbinary')

    def test_rerun_preserves_identical_and_unrelated_files(self):
        self.archive_with([('rules.xml', b'content')])
        self.success(self.run_cli())
        target = self.output / 'rules.xml'
        os.utime(target, ns=(1234567890000000000, 1234567890000000000))
        before = target.stat().st_mtime_ns
        (self.output / 'notes.txt').write_text('authored')
        self.success(self.run_cli())
        self.assertEqual(target.stat().st_mtime_ns, before)
        self.assertEqual((self.output / 'notes.txt').read_text(), 'authored')

    def test_differing_file_blocks_all_publication(self):
        self.archive_with([('new.xml', b'new'), ('existing.xml', b'new')])
        self.output.mkdir()
        (self.output / 'existing.xml').write_bytes(b'authored')
        self.rejected(self.run_cli())
        self.assertFalse((self.output / 'new.xml').exists())
        self.assertEqual((self.output / 'existing.xml').read_bytes(), b'authored')

    def test_directory_permissions_not_copied(self):
        directory = zipfile.ZipInfo('Manual/')
        directory.create_system = 3
        directory.external_attr = (stat.S_IFDIR | 0o555) << 16
        self.archive_with([(directory, b''), ('Manual/rules.xml', b'content')])
        self.success(self.run_cli())
        self.assertTrue((self.output / 'Manual').stat().st_mode & stat.S_IWUSR)

    def test_unsafe_names_rejected_before_writes(self):
        for name in ('../escape', '/absolute', 'C:/drive', 'a\\b',
                     'a/../escape', 'a//b', './file', 'a/./b', 'bad\x01name'):
            with self.subTest(name=name):
                self.archive_with([('good.xml', b'good'), (name, b'bad')])
                self.rejected(self.run_cli())
                self.assertFalse(self.output.exists())

    def test_symlink_and_special_archive_entries(self):
        for kind in (stat.S_IFLNK, stat.S_IFIFO):
            member = zipfile.ZipInfo('unsafe')
            member.create_system = 3
            member.external_attr = (kind | 0o777) << 16
            self.archive_with([(member, b'outside')])
            self.rejected(self.run_cli())
            self.assertFalse(self.output.exists())

    def test_duplicate_aliases_and_parent_conflicts(self):
        for names in [('a', 'a'), ('A', 'a'), ('café', 'cafe\u0301'),
                      ('parent', 'parent/child'), ('parent/child', 'parent'),
                      ('A/one', 'a/two')]:
            with self.subTest(names=names):
                self.archive_with([(n, b'content') for n in names])
                self.rejected(self.run_cli())
                self.assertFalse(self.output.exists())

    def test_destination_symlinks_rejected(self):
        self.archive_with([('nested/file', b'content')])
        outside = self.root / 'outside'
        outside.mkdir()
        self.output.symlink_to(outside, target_is_directory=True)
        self.rejected(self.run_cli())
        self.output.unlink()
        self.output.mkdir()
        (self.output / 'nested').symlink_to(outside, target_is_directory=True)
        self.rejected(self.run_cli())
        self.assertEqual(list(outside.iterdir()), [])

    def test_destination_file_symlink_rejected(self):
        self.archive_with([('file', b'content')])
        self.output.mkdir()
        outside = self.root / 'outside'
        outside.write_bytes(b'content')
        (self.output / 'file').symlink_to(outside)
        self.rejected(self.run_cli())
        self.assertEqual(outside.read_bytes(), b'content')

    def test_file_directory_conflicts(self):
        self.archive_with([('nested/file', b'content')])
        self.output.mkdir()
        (self.output / 'nested').write_text('authored')
        self.rejected(self.run_cli())
        self.assertEqual((self.output / 'nested').read_text(), 'authored')

    def test_missing_malformed_and_empty_archives(self):
        self.rejected(self.run_cli())
        self.archive.write_bytes(b'not a zip')
        self.rejected(self.run_cli())
        self.archive_with([])
        self.rejected(self.run_cli())
        self.assertFalse(self.output.exists())

    def test_encrypted_and_unsupported_compression(self):
        self.archive_with([('file', b'content')])
        data = bytearray(self.archive.read_bytes())
        local = data.index(b'PK\x03\x04')
        central = data.index(b'PK\x01\x02')
        data[local + 6] |= 1
        data[central + 8] |= 1
        self.archive.write_bytes(data)
        self.rejected(self.run_cli())
        with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_BZIP2) as archive:
            archive.writestr('file', b'content')
        self.rejected(self.run_cli())
        self.assertFalse(self.output.exists())

    def test_nul_names_and_directory_payloads(self):
        self.archive_with([('dir/', b'invalid directory data'), ('file', b'content')])
        self.rejected(self.run_cli())
        self.assertFalse(self.output.exists())
        self.archive_with([('badxname', b'content')])
        self.archive.write_bytes(self.archive.read_bytes().replace(b'badxname', b'bad\x00name'))
        self.rejected(self.run_cli())
        self.assertFalse(self.output.exists())

    def test_corrupt_crc_is_detected_before_publication(self):
        with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_STORED) as archive:
            archive.writestr('good', b'good')
            archive.writestr('bad', b'unique-crc-payload')
        data = self.archive.read_bytes().replace(b'unique-crc-payload', b'broken-crc-payload')
        self.archive.write_bytes(data)
        self.rejected(self.run_cli())
        self.assertFalse(self.output.exists())

    def test_limits_and_default_paths(self):
        spec = importlib.util.spec_from_file_location('extract_srg', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        args = module.arguments([])
        self.assertEqual(args.archive, SCRIPT.parents[1] / 'zips/U_VPN_V3R5_SRG.zip')
        self.assertEqual(args.output_dir, SCRIPT.parents[1] / 'srgs')
        self.archive_with([('one', b'1234'), ('two', b'5678')])
        for name, value in [('MAX_ENTRIES', 1), ('MAX_FILE_BYTES', 3), ('MAX_TOTAL_BYTES', 7)]:
            with self.subTest(limit=name), patch.object(module, name, value):
                with self.assertRaises(ValueError):
                    module.extract_archive(self.archive, self.output)
                self.assertFalse(self.output.exists())

    def test_help_needs_no_dependencies(self):
        result = subprocess.run([sys.executable, '-S', str(SCRIPT), '--help'],
                                capture_output=True, text=True)
        self.success(result)
        self.assertIn('--output-dir', result.stdout)


if __name__ == '__main__':
    unittest.main()
