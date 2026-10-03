# Cloppy project instructions

## Project and ownership

Cloppy is a personal macOS fork of Clop. Xcode project, shared scheme and target
names remain `Clop`/`ClopCLI`; app is `Cloppy.app` (`local.cloppy.app`).
`CLOPPY` compilation conditions isolate local access and startup from commercial
activation, official Sparkle updates, iCloud sync, reporting and WarpDrop.

- `Clop/`: SwiftUI/AppKit app, optimisation engines, settings and pipelines.
- `Clop/CloppyAccess.swift`: local access policy and compatibility helpers.
- `ClopCLI/`: CLI and MCP server; Settings installs CLI as `~/.local/bin/cloppy`.
- `Shared.swift` and `Shared/`: contracts and types shared by app and CLI.
- `Clop.xcodeproj/`: target membership, pinned packages, signing and build settings.
- `Scripts/`: build, signing, installation, validation and upstream update owners.

Trace app and CLI callers before changing shared requests, responses or settings.
Preserve Codable compatibility, error replies, cancellation, file backups and
concurrency limits. Match existing Swift style and English product terminology.
Preserve configured macOS deployment targets and Swift language mode; guard newer
platform APIs where needed.

## Build, installation and upstream updates

Before build, installation or upstream sync, read [README.md](README.md).
Resolve `repo="$(git rev-parse --show-toplevel)"` in the checkout being changed.
Root Makefile owns commands; inspect `make -C "$repo" -n <target>` first.

- `make -C "$repo" build`: Release build, local Apple Development signing and
  bundle validation; output is `build/Cloppy.app`. Does not install or launch.
- `make -C "$repo" install`: builds and replaces only `/Applications/Cloppy.app`
  with staging, concurrency checks and rollback. Run when installation is requested.
- `make -C "$repo" package`: builds and produces `build/Cloppy.zip`.
- `make -C "$repo" check`: Python tests for installer and update orchestration.
- `make -C "$repo" update`: stable upstream release in an isolated worktree;
  tests, signed build and terminal review precede local integration.
- `make -C "$repo" hooks`: enable this clone's versioned Git hooks.

Build uses Xcode and pinned Swift packages; retain `Package.resolved` and explicit
dependency review. Signing resolves an existing Keychain identity with no silent
ad-hoc fallback. Certificate names and fingerprints stay outside tracked files.
The fork's build scripts replace the original developer's private tooling.

Cloppy has separate preferences, IPC ports, caches, URL scheme and MCP entries.
Preserve coexistence with official Clop, local full access and disabled official
updates. Keep MCP write/script authorization and binary/decompression safeguards.
Preserve installer protections for symlinks, unexpected bundles, changed targets,
locks and rollback. Do not substitute the upstream Clop install workflow.

## Validation

Run changed-surface selection before choosing checks. `make check` is the complete
tracked test suite for workflow scripts; app/CLI changes also require `make build`
and focused behaviour proof. There is no XCTest target in the shared scheme.

- Documentation: reference checks and `git diff --check`; no app build needed.
- Shell/Python workflows: syntax checks and isolated tests through `make check`.
- App/CLI: signed build, bundle validation and proof for the changed behaviour.
- UI: record an interaction and expected result; verify in the changed worktree
  or report the manual check as unavailable before integration.

Build alone does not prove permissions, clipboard, media optimisation or UI.
Use copies of media for manual checks. Tracked `tests/` differs from ignored
private `ClopTests/`, specs and corpora; preserve their publication boundaries.
`Clop/bin.tar.lrz` uses Git LFS. Preserve hooks, attributes and bundled tools.

## Git integration and cleanup

`main` is our integration/default branch. `origin` is our fork; `upstream` is
original Clop. `cloppy` remains a historical reference, not an integration target.

**Upstream is strictly read-only. Under no circumstances commit or merge into
the original Clop repository, push to it, or open pull requests targeting it.**
This prohibition applies regardless of remote name, URL, CLI, API or tooling.
Keep all commits, merges, pushes and pull requests within our Cloppy fork;
merge, push and PR publication still require explicit authorization.
Reading or fetching upstream and importing its releases into our fork is allowed.

Merge upstream releases through the reviewed update flow rather than replacing
fork files with upstream versions; preserve Cloppy's Makefile and scripts.

Hooks are opt-in per clone through `core.hooksPath=.githooks` and retain Git LFS.
Authorised merges on `main`/`master`, including approved `make update` integration,
push before cleanup. Push failure skips cleanup; check actual results because a
successful Git merge alone does not prove successful hook finalization.
Cleanup may remove update-candidate artifacts; rebuild from `main` when needed.

Cleanup delegates to the local agent-config checkout at
`${AGENT_CONFIG_HOME:-$HOME/.agents}/scripts/cleanup-merged-worktrees.sh`.
Before integration, confirm the push destination is our fork (`origin`) and
its tracking branch and helper integration ref agree;
the helper prefers `origin/HEAD`, which should point to `origin/main`.
Only clean, fully merged canonical `.worktrees/<slug>` checkouts with matching
branch names qualify. Inspect dry-run before manual cleanup; limit it to the
current task with `--branch <slug>`. Report `MERGED`, `PUSHED`, `CLEANED` separately.
