#!/bin/bash
# Turns a pristine upstream Clop checkout into Cloppy: copies the fork-owned files from
# .cloppy/overlay, then applies .cloppy/patches in name order. --3way falls back to a merge
# when upstream context drifted, so only a real conflict fails.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
cp -Rp .cloppy/overlay/. .
for patch in .cloppy/patches/*.patch; do
  echo "applying ${patch##*/}"
  git apply --3way --whitespace=nowarn "$patch"
done
