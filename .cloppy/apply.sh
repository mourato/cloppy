#!/bin/bash
# Turns a pristine upstream Clop checkout into Cloppy: copies the fork-owned files from
# .cloppy/overlay, then applies every .cloppy/patches file in name order. --3way falls back to a merge
# when upstream context drifted, so only a real conflict fails.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
[ ! -d .cloppy/overlay ] || cp -Rp .cloppy/overlay/. .
# Every patch is attempted so a conflict leaves the full candidate to resolve, not half of it.
failed=0
for patch in .cloppy/patches/*.patch; do
  [ -e "$patch" ] || continue
  echo "applying ${patch##*/}"
  git apply --3way --whitespace=nowarn "$patch" || failed=1
done
exit "$failed"
