"""Exercise update orchestration with real disposable Git histories, no live app."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
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
        queue = self.repo / '.cloppy'
        (queue / 'patches').mkdir(parents=True)
        for name in ['apply.sh', 'queue.py']:
            shutil.copy2(ROOT / '.cloppy' / name, queue / name)
        (queue / 'UPSTREAM').write_text(self.run_git(self.upstream, 'rev-parse', 'HEAD') + '\n')
        self.refresh_queue('local fork')
        self.base = self.run_git(self.repo, 'rev-parse', 'HEAD')
        self.interactive = patch.object(updater.sys.stdin, 'isatty', return_value=True)
        self.interactive.start()
        self.addCleanup(self.interactive.stop)

    def refresh_queue(self, message):
        self.run_git(self.repo, 'add', '-A')
        subprocess.run([sys.executable, str(self.repo / '.cloppy/queue.py'), 'refresh'], cwd=self.repo, check=True)
        self.commit(self.repo, message)

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
        self.assertEqual(self.run_git(self.repo, 'show', '-s', '--format=%P', 'HEAD').split(), [self.base, stable])
        self.assertEqual((self.repo / '.cloppy/UPSTREAM').read_text(), stable + '\n')
        self.assertTrue((self.repo / '.cloppy/overlay/local.txt').is_file())
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

    def test_post_merge_cleanup_does_not_report_a_removed_artifact(self):
        self.release()
        hooks = Path(self.temp.name) / 'hooks'
        hooks.mkdir()
        hook = hooks / 'post-merge'
        hook.write_text(
            '#!/bin/sh\n'
            'git worktree remove .worktrees/cloppy-update-v1-1-0\n'
            'git branch -d cloppy-update-v1-1-0\n'
        )
        hook.chmod(0o755)
        self.run_git(self.repo, 'config', 'core.hooksPath', str(hooks))
        output = io.StringIO()
        with patch('builtins.input', return_value='yes'), contextlib.redirect_stdout(output):
            updater.update(self.repo)
        self.assertTrue((self.repo / 'new.txt').is_file())
        self.assertFalse((self.repo / '.worktrees/cloppy-update-v1-1-0').exists())
        self.assertIn('Candidate artifact unavailable', output.getvalue())
        self.assertNotIn('Validated artifact:', output.getvalue())
        self.assertNotIn('No push', output.getvalue())

    def own_shared_in_patch(self):
        (self.repo / '.cloppy/patches/0001-shared.patch').write_text('diff --git a/shared.txt b/shared.txt\n')
        (self.repo / 'shared.txt').write_text('local edit\n')
        self.refresh_queue('local edit')
        (self.upstream / 'shared.txt').write_text('upstream edit\n')
        self.release()

    def test_conflict_never_changes_current_version(self):
        self.own_shared_in_patch()
        base = self.run_git(self.repo, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(RuntimeError, 'conflict'):
            self.invoke()
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), base)
        self.assertEqual((self.repo / 'shared.txt').read_text(), 'local edit\n')

    def test_resolved_conflict_is_folded_back_into_the_patch(self):
        self.own_shared_in_patch()
        with self.assertRaisesRegex(RuntimeError, 'conflict'):
            self.invoke()
        candidate = self.repo / '.worktrees/cloppy-update-v1-1-0'
        with self.assertRaisesRegex(RuntimeError, 'Resolve conflicts'):
            self.invoke()
        (candidate / 'shared.txt').write_text('upstream edit, local edit\n')
        self.run_git(candidate, 'add', '-A')
        self.invoke()
        self.assertEqual((self.repo / 'shared.txt').read_text(), 'upstream edit, local edit\n')
        self.assertIn('+upstream edit, local edit', (self.repo / '.cloppy/patches/0001-shared.patch').read_text())
        subprocess.run([sys.executable, str(self.repo / '.cloppy/queue.py'), 'verify'], cwd=self.repo, check=True)

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

    def test_commit_hooks_never_alter_the_reviewed_tree(self):
        self.release()
        hooks = Path(self.temp.name) / 'hooks'
        hooks.mkdir()
        hook = hooks / 'pre-commit'
        hook.write_text('#!/bin/sh\nprintf "unreviewed hook edit\\n" > new.txt\ngit add new.txt\n')
        hook.chmod(0o755)
        self.run_git(self.repo, 'config', 'core.hooksPath', str(hooks))
        self.invoke()
        self.assertEqual((self.repo / 'new.txt').read_text(), 'stable upstream feature\n')

    def test_same_tree_history_change_during_review_is_rejected(self):
        self.release()
        candidate = self.repo / '.worktrees/cloppy-update-v1-1-0'
        def edit(_):
            self.run_git(candidate, 'commit', '-qm', 'external merge')
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
