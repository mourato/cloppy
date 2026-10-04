# .cloppy

Everything that makes Cloppy differ from upstream [FuzzyIdeas/Clop](https://github.com/FuzzyIdeas/Clop).
The tree on `main` is meant to equal *upstream + `apply.sh`*: fork-owned files come from `overlay/`,
changes to upstream files come from `patches/`.

| Path | Contents |
| --- | --- |
| `overlay/` | Files the fork owns outright (`Makefile`, `README.md`, `AGENTS.md`, `.gitignore`, `.githooks/`, `Scripts/*-cloppy*`, `Scripts/signing.sh`, `Scripts/cleanup-merged-worktrees.sh`, `tests/`). Copied over the checkout, never patched, so upstream edits to them cannot conflict. |
| `patches/0001-identity.patch` | `local.cloppy.app` bundle IDs, IPC ports, `cloppy://` scheme, `cloppy` CLI and MCP names, Application Scripts and cache paths, user-facing "Cloppy" strings, Info.plist without Sparkle feed or Sentry exception class. |
| `patches/0002-local-access.patch` | `CloppyAccess.swift` and the `#if CLOPPY` guards that remove Paddle licensing, Pro limits, Sentry, update checks and licence UI. |
| `patches/0003-no-warpdrop.patch` | WarpDrop / "Send securely" removed from actions. |
| `patches/0004-project.patch` | `project.pbxproj` (Cloppy product name and bundle IDs, `CLOPPY` compilation condition, `CloppyAccess.swift`, no WarpDrop package) and `Package.resolved`. |
| `apply.sh` | Copies `overlay/` and applies every patch in name order with `git apply --3way`; exits non-zero after all patches if any conflicted. |
| `queue.py refresh` | Rewrites `patches/` and `overlay/` from the index against `UPSTREAM`. A path keeps its owning patch; a new file absent upstream joins `overlay/`; an unowned upstream path stops the refresh. |
| `queue.py verify` | Proves `UPSTREAM` + `apply.sh` reproduces the index tree. Runs in `make check` and in `make update`. |
| `UPSTREAM` | Upstream commit the queue applies to; `make update` moves it to each release. |

## Changing the fork

Edit on `main`, `git add` the change, run `.cloppy/queue.py refresh`, `git add .cloppy` and
commit both together. New upstream-file changes need an owner first: add a
`diff --git a/<path> b/<path>` line to the right patch (or a new `000N-*.patch`), then refresh.

## Upstream releases

`make update` stages the release tree, restores `.cloppy`, applies it and, after conflicts are
resolved and staged, refreshes and verifies the queue before tests, signed build and review. The
integrated commit has the previous `main` and the release as parents, so `main` only fast-forwards.
