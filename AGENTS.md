# Cloppy project instructions

## Project and ownership

Cloppy is a fork of Clop, a native macOS media and clipboard optimiser.
The Xcode project, targets, app bundle and shared scheme retain the Clop names.

- `Clop/`: SwiftUI/AppKit app, settings, optimisation engines and pipelines.
- `ClopCLI/`: command-line client and MCP server.
- `Shared.swift` and `Shared/`: contracts and types used across app and CLI.
- `Clop.xcodeproj/`: target membership, dependencies, signing and build settings.
- `Scripts/`: project scripts; preserve this directory's capitalisation.

Trace app and CLI callers before changing a shared request, response, setting
or pipeline type. Preserve Codable compatibility, error replies, cancellation,
file backups and concurrency limits when changing optimisation behaviour.
Match existing Swift style and English product terminology.

## Build and installation

Resolve `repo="$(git rev-parse --show-toplevel)"` in the checkout being changed.
Use the root Makefile for its documented tasks; inspect targets with
`make -C "$repo" -n <target>` before execution.

- `make -C "$repo" build`: signed Release build and DMG; a distribution task,
  not a lightweight compilation check.
- `make -C "$repo" install`: archive/export with Developer ID signing, then
  replace `/Applications/Clop.app`. Run only when installation is requested.
- `make -C "$repo" hooks`: enable this clone's versioned Git hooks.

The Makefile uses external developer tools, including `fish` and `make-app`.
The Xcode project references a local WarpDrop Swift package; verify that its
configured relative path resolves from the task worktree before building.
Report missing tools, packages or signing prerequisites instead of changing
project dependencies or signing to work around them.

App and CLI targets currently specify macOS 13 and Swift 5 language mode.
Preserve configured deployment targets; guard newer platform APIs as needed.

Installation must use the Makefile's Developer ID archive/export path.
An Apple Development-signed Release installation can deactivate the licence.
Do not use `xrel Clop --install` or copy an unsigned validation build over the
installed app. Keep signing identities and entitlements intact.

## Validation

There is no Makefile `test`/`validate` target or test target in the shared Clop
scheme. Select proof for the changed behaviour; do not claim a passing test
suite from a build or invent unavailable targets.

- Documentation: check references and `git diff --check`; no app build needed.
- Shell hooks/scripts: syntax checks and isolated Git/filesystem fixtures.
- Swift: focused compilation and behaviour proof for the changed owner.
  For compile-only verification, use Xcode's Clop Debug scheme with a separate
  DerivedData directory and `CODE_SIGNING_ALLOWED=NO`; this does not prove
  installed-app signing, permissions or runtime behaviour.
- UI: record an interaction and expected result; verify in the changed
  worktree, or report the manual check as unavailable before integration.

`ClopTests/`, private specs and corpora are ignored by Git. Preserve that
publication boundary; private local tests may not exist in another checkout.
`Clop/bin.tar.lrz` is tracked through Git LFS. Preserve LFS hooks and attributes.
Release, upload, notarisation and Sentry tasks are explicit delivery operations.

## Git integration and cleanup

Integration branch is `main`. Hooks are opt-in per clone through
`core.hooksPath=.githooks`; they also retain the existing Git LFS behaviour.
An authorised merge on `main`/`master` triggers push, followed by cleanup.
Push failure skips cleanup. Merge authorisation includes these hook effects.

Cleanup delegates to
`${AGENT_CONFIG_HOME:-$HOME/.agents}/scripts/cleanup-merged-worktrees.sh`;
the agent-config checkout is a local prerequisite.
Before integration, confirm the push upstream and helper's integration ref
agree: the helper prefers `origin/HEAD`. A stale pointer to another branch
must be resolved before automatic cleanup.

Only clean, fully merged canonical `.worktrees/<slug>` checkouts with matching
branch names qualify. Dirty and unmerged worktrees remain. Inspect a dry-run
before manual cleanup and limit it to the current task with `--branch <slug>`.
Report `MERGED`, `PUSHED` and `CLEANED` separately after checking actual state.
