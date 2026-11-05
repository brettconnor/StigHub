"""Executable acceptance tests for stig-view.spec.md, V1–V4."""
import errno
import os
from pathlib import Path
import pty
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'stig-view.sh'


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rule = 'SRG-001'
        self.product = 'Cisco IOS-XE'
        (self.root / self.rule).mkdir()
        (self.root / self.rule / 'srg.txt').write_bytes(b'Baseline requirement\n')
        self.product_dir = self.root / self.product / self.rule
        self.product_dir.mkdir(parents=True)
        (self.product_dir / 'status.txt').write_bytes(b'Open\n')
        (self.product_dir / 'fix.txt').write_bytes(b'Product fix\n')

    def run_view(self, *args, cwd=None, env=None):
        return subprocess.run(['/bin/bash', str(SCRIPT), *args], cwd=cwd or self.root,
                              capture_output=True, timeout=10, env=env)

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def rejected(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Error:', result.stderr)
        self.assertEqual(result.stdout, b'')

    def test_zero_and_one_argument_legacy_modes(self):
        for args, cwd in [((), self.root / self.rule), ((self.rule,), self.root)]:
            result = self.run_view(*args, cwd=cwd)
            self.success(result)
            self.assertEqual(result.stdout, b'Baseline requirement\n')

    def test_root_and_no_pager(self):
        result = self.run_view('--root', str(self.root), '--no-pager', self.rule,
                               cwd=self.root / self.rule)
        self.success(result)
        self.assertEqual(result.stdout, b'Baseline requirement\n')

    def test_product_labels_order_and_text_filter(self):
        (self.product_dir / 'artifact.txt').write_bytes(b'')
        (self.product_dir / 'ignored.pdf').write_text('not a text file')
        (self.product_dir / 'nested.txt').mkdir()
        result = self.run_view(self.rule, self.product)
        self.success(result)
        self.assertEqual(result.stdout, b'Baseline requirement\n\n===== artifact.txt =====\n'
                         b'\n===== fix.txt =====\nProduct fix\n'
                         b'\n===== status.txt =====\nOpen\n')

    def test_empty_product_directory(self):
        for p in self.product_dir.iterdir():
            p.unlink()
        result = self.run_view(self.rule, self.product)
        self.success(result)
        self.assertEqual(result.stdout, b'Baseline requirement\n')

    def test_missing_baseline_or_product_fails_before_output(self):
        self.rejected(self.run_view('missing'))
        self.rejected(self.run_view(self.rule, 'missing'))
        self.rejected(self.run_view(cwd=self.root))

    def test_bad_options_and_excess_arguments(self):
        for args in [('--unknown',), ('--root',), (self.rule, self.product, 'extra')]:
            with self.subTest(args=args):
                self.rejected(self.run_view(*args))

    def test_invalid_identifiers(self):
        for name in ('../outside', '/absolute', 'a/b', 'a\\b', 'a..b', '',
                     '$(touch injected)', 'ends.', 'ends ', 'a' * 201):
            with self.subTest(name=name):
                self.rejected(self.run_view(name))
                self.rejected(self.run_view(self.rule, name))
        self.assertFalse((self.root / 'injected').exists())

    def test_double_dash_and_help(self):
        result = self.run_view('--', self.rule)
        self.success(result)
        self.assertEqual(result.stdout, b'Baseline requirement\n')
        result = self.run_view('--help')
        self.success(result)
        self.assertIn(b'--root', result.stdout)
        self.assertIn(b'--no-pager', result.stdout)

    def test_baseline_symlink_rejected(self):
        baseline = self.root / self.rule / 'srg.txt'
        baseline.unlink()
        baseline.symlink_to(self.product_dir / 'fix.txt')
        self.rejected(self.run_view(self.rule))

    def test_directory_and_product_file_symlinks_rejected(self):
        (self.root / 'Linked').symlink_to(self.root / self.rule, target_is_directory=True)
        self.rejected(self.run_view('Linked'))
        (self.root / 'LinkedProduct').symlink_to(self.root / self.product, target_is_directory=True)
        self.rejected(self.run_view(self.rule, 'LinkedProduct'))
        target = self.product_dir / 'fix.txt'
        target.unlink()
        target.symlink_to(self.root / self.rule / 'srg.txt')
        self.rejected(self.run_view(self.rule, self.product))

    def test_explicit_root_symlink_rejected(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.rejected(self.run_view('--root', str(alias), self.rule))

    def test_pager_environment_is_not_executed_when_piped(self):
        environment = os.environ.copy()
        environment['PAGER'] = 'touch injected'
        environment['LESSOPEN'] = '|touch injected %s'
        result = self.run_view(self.rule, env=environment)
        self.success(result)
        self.assertEqual(result.stdout, b'Baseline requirement\n')
        self.assertFalse((self.root / 'injected').exists())

    def pager_environment(self, exit_code=0):
        binary = self.root / 'bin'
        binary.mkdir()
        pager = binary / 'less'
        pager.write_text('#!/bin/bash\n'
                         'printf "%s|%s|%s|%s|%s\\n" "$*" "$LESSSECURE" '
                         '"${LESSOPEN-unset}" "${LESS-unset}" "$LESSHISTFILE" > "$PAGER_LOG"\n'
                         '/bin/cat\n'
                         f'exit {exit_code}\n')
        pager.chmod(0o755)
        environment = os.environ.copy()
        environment.update(PATH=str(binary) + os.pathsep + environment['PATH'],
                           LESS='-R', LESSOPEN='|touch injected %s',
                           PAGER='touch injected', PAGER_LOG=str(self.root / 'pager.log'))
        return environment

    def tty_view(self, *args, env):
        master, slave = pty.openpty()
        process = subprocess.Popen(['/bin/bash', str(SCRIPT), *args], cwd=self.root,
                                   stdout=slave, stderr=subprocess.PIPE, env=env)
        os.close(slave)
        output = b''
        try:
            while True:
                try:
                    chunk = os.read(master, 4096)
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                output += chunk
            _, error = process.communicate(timeout=10)
        finally:
            os.close(master)
            if process.poll() is None:
                process.kill()
                process.wait()
        return process.returncode, output, error

    def test_terminal_pager_is_safe(self):
        code, output, error = self.tty_view(self.rule, env=self.pager_environment())
        self.assertEqual(code, 0, error)
        self.assertIn(b'Baseline requirement', output)
        log = (self.root / 'pager.log').read_text()
        self.assertEqual(log, '-FX|1|||-\n')
        self.assertFalse((self.root / 'injected').exists())

    def test_no_pager_on_terminal_when_requested(self):
        code, output, error = self.tty_view('--no-pager', self.rule, env=self.pager_environment())
        self.assertEqual(code, 0, error)
        self.assertIn(b'Baseline requirement', output)
        self.assertFalse((self.root / 'pager.log').exists())

    def test_pager_failure_propagates(self):
        code, _, error = self.tty_view(self.rule, env=self.pager_environment(exit_code=7))
        self.assertNotEqual(code, 0)
        self.assertIn(b'Error:', error)

    def test_early_pager_quit_is_successful(self):
        environment = self.pager_environment()
        (self.root / 'bin/less').write_text('#!/bin/bash\nexit 0\n')
        (self.root / self.rule / 'srg.txt').write_bytes(b'x' * (2 * 1024 * 1024))
        code, _, error = self.tty_view(self.rule, env=environment)
        self.assertEqual(code, 0, error)
        self.assertNotIn(b'Error:', error)

    def test_terminal_fallback_when_less_is_unavailable(self):
        binary = self.root / 'bin'
        binary.mkdir()
        (binary / 'cat').symlink_to('/bin/cat')
        environment = os.environ.copy()
        environment['PATH'] = str(binary)
        code, output, error = self.tty_view(self.rule, env=environment)
        self.assertEqual(code, 0, error)
        self.assertIn(b'Baseline requirement', output)

    def test_renderer_failure_propagates(self):
        binary = self.root / 'bin'
        binary.mkdir()
        cat = binary / 'cat'
        cat.write_text('#!/bin/bash\nexit 13\n')
        cat.chmod(0o755)
        environment = os.environ.copy()
        environment['PATH'] = str(binary)
        self.rejected(self.run_view(self.rule, env=environment))
