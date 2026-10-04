#!/usr/bin/env python3
"""Keep the Cloppy patch queue in step with the index.

refresh  rewrites .cloppy/patches and .cloppy/overlay from the index, diffed against
         .cloppy/UPSTREAM. Each changed path keeps the patch (or overlay) that already owns it;
         a new path absent upstream joins the overlay. A changed upstream path without an owner
         stops the refresh until it is listed in a patch.
verify   proves that UPSTREAM + apply.sh reproduces the index tree exactly.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def git(root, *args, text=True):
    return subprocess.run(['git', '-C', str(root), *args], check=True, text=text, capture_output=True).stdout


def lines(output):
    return [line for line in output.split('\0') if line]


def refresh(root):
    queue = root / '.cloppy'
    upstream = (queue / 'UPSTREAM').read_text().strip()
    tree = git(root, 'write-tree').strip()
    changed = lines(git(root, 'diff', '-z', '--name-only', '--no-renames', upstream, tree, '--', '.', ':!.cloppy'))
    in_upstream = set(lines(git(root, 'ls-tree', '-z', '-r', '--name-only', upstream)))
    overlay = queue / 'overlay'
    owners = {}
    for path in lines(git(root, 'ls-files', '-z', '--', '.cloppy/overlay')):
        owners[path.removeprefix('.cloppy/overlay/')] = overlay
    patches = sorted((queue / 'patches').glob('*.patch'))
    for patch in patches:
        for line in patch.read_bytes().decode(errors='replace').splitlines():
            if line.startswith('diff --git a/'):
                owners[line.split(' b/', 1)[1]] = patch
    groups = {}
    orphans = []
    for path in changed:
        owner = owners.get(path) or (overlay if path not in in_upstream else None)
        if owner is None:
            orphans.append(path)
        else:
            groups.setdefault(owner, []).append(path)
    if orphans:
        raise SystemExit('List these upstream paths in a .cloppy/patches file first:\n  ' + '\n  '.join(orphans))
    shutil.rmtree(overlay, ignore_errors=True)
    for path in groups.get(overlay, []):
        target = overlay / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git(root, 'show', f':{path}', text=False))
        mode = git(root, 'ls-files', '-s', '--', path).split()[0]
        target.chmod(0o755 if mode == '100755' else 0o644)
    for patch in patches:
        if paths := groups.get(patch):
            patch.write_bytes(git(root, 'diff', '--binary', '--no-renames', upstream, tree, '--', *paths, text=False))
        else:
            patch.unlink()


def verify(root):
    upstream = (root / '.cloppy/UPSTREAM').read_text().strip()
    tree = git(root, 'write-tree').strip()
    env = {**os.environ, 'GIT_LFS_SKIP_SMUDGE': '1'}
    with tempfile.TemporaryDirectory(prefix='cloppy-queue-') as temp:
        work = Path(temp) / 'proof'
        subprocess.run(['git', 'clone', '-q', '--shared', '--no-checkout', str(root), str(work)], check=True, env=env)
        subprocess.run(['git', '-C', str(work), 'checkout', '-q', '--detach', upstream], check=True, env=env)
        archive = subprocess.run(['git', '-C', str(root), 'archive', tree, '.cloppy'], check=True, capture_output=True).stdout
        subprocess.run(['tar', '-x', '-C', str(work)], input=archive, check=True)
        applied = subprocess.run([str(work / '.cloppy/apply.sh')], cwd=work, env=env, text=True, capture_output=True)
        if applied.returncode:
            raise SystemExit(f'apply.sh fails on upstream {upstream[:7]}:\n{applied.stdout}{applied.stderr}')
        git(work, 'add', '-A')
        proof = git(work, 'write-tree').strip()
    if proof != tree:
        raise SystemExit(f'.cloppy does not reproduce the index: upstream {upstream[:7]} + apply.sh gives {proof[:7]}, index is {tree[:7]}.')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in {'refresh', 'verify'}:
        raise SystemExit('usage: queue.py refresh|verify')
    root = Path(git(Path.cwd(), 'rev-parse', '--show-toplevel').strip())
    {'refresh': refresh, 'verify': verify}[sys.argv[1]](root)
