#!/usr/bin/env python3
"""Rebuild Cloppy on the latest stable upstream release from .cloppy, then build, review and fast-forward locally."""
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


def git(repo, *args, capture=True):
    result = subprocess.run(
        ['git', '-C', str(repo), *args], check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else None


def candidate_upstream(worktree):
    path = worktree / '.cloppy/UPSTREAM'
    return path.read_text().strip() if path.is_file() else None


def assemble(worktree, base, upstream):
    """Stage upstream's tree plus base's .cloppy queue; False leaves patch conflicts to resolve."""
    git(worktree, 'read-tree', '-u', '--reset', upstream)
    git(worktree, 'checkout', base, '--', '.cloppy')
    (worktree / '.cloppy/UPSTREAM').write_text(f'{upstream}\n')
    if subprocess.run([str(worktree / '.cloppy/apply.sh')], cwd=worktree).returncode:
        return False
    git(worktree, 'add', '-A')
    return True


def update(repo):
    if git(repo, 'status', '--porcelain'):
        raise RuntimeError('Commit or save local changes before make update.')
    branch = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    base = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'fetch', 'upstream', '+refs/tags/v*:refs/remotes/upstream/releases/v*', capture=False)
    refs = git(repo, 'for-each-ref', '--format=%(refname)', 'refs/remotes/upstream/releases/').splitlines()
    versions = []
    for ref in refs:
        match = re.fullmatch(r'refs/remotes/upstream/releases/v(\d+)\.(\d+)\.(\d+)', ref)
        if match:
            versions.append((tuple(map(int, match.groups())), ref))
    if not versions:
        raise RuntimeError('Upstream has no stable vMAJOR.MINOR.PATCH release.')
    _, ref = max(versions)
    release = ref.rsplit('/', 1)[-1]
    upstream = git(repo, 'rev-parse', f'{ref}^{{commit}}')
    if subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', upstream, base]).returncode == 0:
        print(f'Already includes latest stable release {release}.')
        return
    if not sys.stdin.isatty():
        raise RuntimeError('Review needs an interactive terminal. Run make update there.')
    helper = Path(os.environ.get('AGENT_CONFIG_HOME', str(Path.home() / '.agents'))) / 'scripts/new-worktree.sh'
    if not helper.is_file():
        raise RuntimeError(f'Canonical worktree helper unavailable: {helper}')
    common = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    slug = f'cloppy-update-{release.replace(".", "-")}'
    worktree = common.parent / '.worktrees' / slug
    if worktree.exists():
        if git(worktree, 'symbolic-ref', '--quiet', '--short', 'HEAD') != slug or git(worktree, 'rev-parse', 'HEAD') != base or candidate_upstream(worktree) != upstream:
            raise RuntimeError(f'Existing candidate has another base/release; inspect {worktree}.')
        if git(worktree, 'ls-files', '--unmerged'):
            raise RuntimeError(f'Resolve conflicts in {worktree}, stage everything with git add -A, then rerun make update.')
    else:
        subprocess.run([str(helper), slug, '--repo', str(repo), '--base', base], check=True)
        if not assemble(worktree, base, upstream):
            raise RuntimeError(f'Patches conflict with upstream. Current version unchanged; resolve in {worktree}, stage everything with git add -A, then rerun make update.')
    print(f'Update candidate: {worktree}', flush=True)
    if git(worktree, 'diff') or git(worktree, 'ls-files', '--others', '--exclude-standard'):
        raise RuntimeError(f'Stage candidate edits before validation: {worktree}.')
    # Fold conflict resolutions back into the queue, then prove upstream + queue gives this tree.
    queue = worktree / '.cloppy/queue.py'
    subprocess.run([sys.executable, str(queue), 'refresh'], cwd=worktree, check=True)
    git(worktree, 'add', '-A', '--', '.cloppy')
    subprocess.run([sys.executable, str(queue), 'verify'], cwd=worktree, check=True)
    try:
        git(worktree, 'diff', '--check')
        git(worktree, 'diff', '--cached', '--check')
        tree = git(worktree, 'write-tree')
        subprocess.run(['make', '-C', str(worktree), 'check'], check=True)
        subprocess.run(['make', '-C', str(worktree), 'build'], check=True)
        print('\nIncoming changes:', flush=True)
        git(worktree, 'diff', '--stat', base, capture=False)
        for line in git(worktree, 'diff', base).splitlines():
            if re.search(r'api.?key|token|password|secret|credential|sentryDSN', line, re.IGNORECASE):
                print('[credential-related diff line omitted; inspect locally]')
            else:
                print(line)
        print('\nReview local access, updater, telemetry, sharing, identity and permission gates.')
        print(f'Full local diff: git -C {shlex.quote(str(worktree))} diff {base}')
        if input('Reviewed changes and approve local integration? [y/N] ').strip().lower() not in {'y', 'yes'}:
            print(f'Not integrated. Candidate remains at {worktree}.')
            return
        if git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD') != branch or git(repo, 'rev-parse', 'HEAD') != base or git(repo, 'status', '--porcelain'):
            raise RuntimeError('Source checkout changed during review; refusing integration.')
        if git(worktree, 'symbolic-ref', '--quiet', '--short', 'HEAD') != slug or git(worktree, 'rev-parse', 'HEAD') != base or candidate_upstream(worktree) != upstream or git(worktree, 'write-tree') != tree or git(worktree, 'diff') or git(worktree, 'ls-files', '--others', '--exclude-standard'):
            raise RuntimeError('Candidate changed during build/review. Validate edits before integrating manually.')
        # The candidate tree is upstream + .cloppy, not a merge result; upstream as second parent keeps
        # releases detectable by ancestry and lets main fast-forward.
        candidate = git(worktree, 'commit-tree', tree, '-p', base, '-p', upstream, '-m', f'Merge Clop {release} into Cloppy')
        git(worktree, 'reset', '-q', '--soft', candidate)
        if git(worktree, 'rev-parse', f'{candidate}^{{tree}}') != tree or git(worktree, 'show', '-s', '--format=%P', candidate).split() != [base, upstream] or git(worktree, 'status', '--porcelain'):
            raise RuntimeError('Committed candidate changed after validation; refusing integration.')
        if git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD') != branch or git(repo, 'rev-parse', 'HEAD') != base or git(repo, 'status', '--porcelain'):
            raise RuntimeError('Source checkout changed during commit; refusing integration.')
        git(repo, 'merge', '--ff-only', candidate, capture=False)
        print(f'Integrated {release} on {branch}. No installation performed.')
        print('Enabled post-merge hooks may push and clean merged worktrees; check their output.')
        artifact = worktree / 'build/Cloppy.app'
        if artifact.is_dir():
            print(f'Validated artifact: {artifact}')
        else:
            print('Candidate artifact unavailable after integration; make build rebuilds it.')
        print('Next: make install')
    except (subprocess.CalledProcessError, RuntimeError):
        print(f'Candidate preserved at {worktree}; no automatic reset or cleanup.', file=sys.stderr)
        raise


if __name__ == '__main__':
    try:
        update(Path(__file__).resolve().parent.parent)
    except (subprocess.CalledProcessError, RuntimeError, EOFError, KeyboardInterrupt) as error:
        print(f'Update stopped: {error}', file=sys.stderr)
        sys.exit(1)
