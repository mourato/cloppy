"""Exercise update orchestration with real disposable Git histories, no live app."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('cloppy_update', ROOT / 'Scripts/update-cloppy.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cloppy-update-test-')
        self.addCleanup(self.temp.cleanup)
        self.upstream = Path(self.temp.name) / 'upstream'
        self.repo = Path(self.temp.name) / 'cloppy'
        self.upstream.mkdir()
        self.run_git(self.upstream, 'init', '-q')
        self.configure(self.upstream)
        (self.upstream / '.gitignore').write_text('.worktrees/\nbuild/\n')
        (self.upstream / 'shared.txt').write_text('base\n')
        (self.upstream / 'Makefile').write_text('check:\n\t@true\nbuild:\n\t@mkdir -p build; touch build/verified\n')
        self.commit(self.upstream, 'base')
        self.run_git(self.upstream, 'tag', 'v1.0.0')
        subprocess.run(['git', 'clone', '-q', str(self.upstream), str(self.repo)], check=True)
        self.configure(self.repo)
        self.run_git(self.repo, 'remote', 'rename', 'origin', 'upstream')
        (self.repo / 'local.txt').write_text('Cloppy local changes\n')
        self.commit(self.repo, 'local fork')
        self.base = self.run_git(self.repo, 'rev-parse', 'HEAD')
        self.interactive = patch.object(updater.sys.stdin, 'isatty', return_value=True)
        self.interactive.start()
        self.addCleanup(self.interactive.stop)

    def run_git(self, repo, *args):
        return subprocess.run(['git', '-C', str(repo), *args], check=True, text=True, capture_output=True).stdout.strip()

    def configure(self, repo):
        for key, value in [('user.name', 'Cloppy test'), ('user.email', 'cloppy-test@example.invalid'), ('commit.gpgsign', 'false'), ('core.hooksPath', str(Path(self.temp.name) / 'no-hooks'))]:
            self.run_git(repo, 'config', key, value)

    def commit(self, repo, message):
        self.run_git(repo, 'add', '.')
        self.run_git(repo, 'commit', '-qm', message)

    def release(self, fail_build=False):
        (self.upstream / 'new.txt').write_text('stable upstream feature\n')
        if fail_build:
            (self.upstream / 'Makefile').write_text('check:\n\t@true\nbuild:\n\t@exit 7\n')
        self.commit(self.upstream, 'stable')
        self.run_git(self.upstream, 'tag', 'v1.1.0')
        return self.run_git(self.upstream, 'rev-parse', 'HEAD')

    def invoke(self, answer='yes', side_effect=None):
        with patch('builtins.input', side_effect=side_effect, return_value=answer), contextlib.redirect_stdout(io.StringIO()):
            updater.update(self.repo)

    def test_latest_stable_integrates_after_review_preserving_fork(self):
        stable = self.release()
        (self.upstream / 'beta.txt').write_text('unreleased\n')
        self.commit(self.upstream, 'beta')
        self.run_git(self.upstream, 'tag', 'v9.0.0b1')
        self.invoke()
        self.assertEqual((self.repo / 'local.txt').read_text(), 'Cloppy local changes\n')
        self.assertEqual((self.repo / 'new.txt').read_text(), 'stable upstream feature\n')
        self.assertFalse((self.repo / 'beta.txt').exists())
        self.run_git(self.repo, 'merge-base', '--is-ancestor', stable, 'HEAD')
        self.assertTrue((self.repo / '.worktrees/cloppy-update-v1-1-0/build/verified').is_file())
        self.assertFalse(self.run_git(self.repo, 'status', '--porcelain'))
        tip = self.run_git(self.repo, 'rev-parse', 'HEAD')
        self.invoke()  # Idempotent already-current update.
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), tip)

    def test_decline_preserves_current_branch_and_candidate_can_resume(self):
        self.release()
        self.invoke(answer='no')
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), self.base)
        self.invoke()
        self.assertTrue((self.repo / 'new.txt').is_file())

    def test_conflict_never_changes_current_version(self):
        (self.repo / 'shared.txt').write_text('local edit\n')
        self.commit(self.repo, 'local edit')
        base = self.run_git(self.repo, 'rev-parse', 'HEAD')
        (self.upstream / 'shared.txt').write_text('upstream edit\n')
        self.release()
        with self.assertRaisesRegex(RuntimeError, 'conflicts'):
            self.invoke()
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), base)
        self.assertEqual((self.repo / 'shared.txt').read_text(), 'local edit\n')

    def test_failed_build_never_integrates(self):
        self.release(fail_build=True)
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke()
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), self.base)

    def test_staged_edits_after_build_are_not_published(self):
        self.release()
        candidate = self.repo / '.worktrees/cloppy-update-v1-1-0'
        def edit(_):
            (candidate / 'new.txt').write_text('unreviewed edit\n')
            self.run_git(candidate, 'add', 'new.txt')
            return 'yes'
        with self.assertRaisesRegex(RuntimeError, 'Candidate changed'):
            self.invoke(side_effect=edit)
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), self.base)

    def test_dirty_source_is_rejected_before_fetch(self):
        (self.repo / 'local.txt').write_text('unsaved edit\n')
        with self.assertRaisesRegex(RuntimeError, 'local changes'):
            self.invoke()
        self.assertEqual((self.repo / 'local.txt').read_text(), 'unsaved edit\n')

    def test_source_edits_during_review_are_preserved_without_integration(self):
        self.release()
        def edit(_):
            (self.repo / 'local.txt').write_text('user edit during review\n')
            return 'yes'
        with self.assertRaisesRegex(RuntimeError, 'Source checkout changed'):
            self.invoke(side_effect=edit)
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), self.base)
        self.assertEqual((self.repo / 'local.txt').read_text(), 'user edit during review\n')


if __name__ == '__main__':
    unittest.main()
