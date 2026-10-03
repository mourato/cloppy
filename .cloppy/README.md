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
| `UPSTREAM` | Upstream commit the patches were last generated against. |

## Regenerating

From a clean checkout of the commit in `UPSTREAM`:

```sh
git checkout --detach "$(cat .cloppy/UPSTREAM)"   # keep .cloppy/ from main
.cloppy/apply.sh
git diff main --stat                              # empty: patches reproduce main
```

## Changing a patch

Edit the code on `main`, then rewrite the affected patch with
`git diff "$(cat .cloppy/UPSTREAM)" -- <paths> > .cloppy/patches/<patch>` (fork-owned files:
copy them into `overlay/`). The `.cloppy/` folder itself is not part of any patch.
