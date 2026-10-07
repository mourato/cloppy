# Cloppy

Personal macOS fork of [Clop](https://github.com/FuzzyIdeas/Clop), based on v3.4.5.
GPLv3; original attribution and licence remain. Full local optimisation has no
commercial activation. WarpDrop, iCloud preference sync, Sentry reporting and
official Sparkle updates are unavailable. Other network actions, such as downloading
an input URL or running a user-configured integration, remain explicit app features.

Our integration and default branch is `main`; `upstream` tracks the original Clop.
The previous `cloppy` branch remains a historical reference.

## Build and install

Requires Xcode (tested toolchain: Xcode 27) and network for pinned Swift packages.
Build targets this Mac’s native architecture. Bundled helper archive remains unchanged.
Uses an existing Apple Development certificate in your Keychain, following GUGU's
local build convention. No Paddle credentials or author's private build scripts required.

```sh
repo="$(git rev-parse --show-toplevel)"
make -C "$repo" build
make -C "$repo" install
make -C "$repo" update
make -C "$repo" package
make -C "$repo" check
```

`make install` builds, signs and validates the app, requests graceful exit if
Cloppy is running, and replaces only `/Applications/Cloppy.app`. It stages on the
destination volume and restores the previous bundle on failure. It does not
launch the app, change preferences or replace the official Clop. An existing
installer lock, symlink, unexpected bundle or changed destination stops installation.
The build is locally signed, not notarized for public distribution.

Signing resolves `Apple Development` to a valid Keychain fingerprint before
building and verifies the resulting certificate requirement. No silent ad-hoc
fallback. Override with an existing certificate name or SHA-1 when needed:

```sh
CLOPPY_CODE_SIGN_IDENTITY='certificate name or SHA-1' make install
```

Certificate names/hashes remain outside tracked configuration. Build outputs
live under `build/`; `CLOPPY_DERIVED_DATA_PATH` may reuse another local Xcode cache.
`APPLICATIONS_DIR` overrides the installation directory for isolated testing.
CLI installation from Settings uses `~/.local/bin/cloppy`. Clop can coexist:
Cloppy owns `local.cloppy.app`, `cloppy://`, its IPC ports, caches and MCP entries.
MCP write/script authorization gates remain intact. No existing Clop preferences
are imported. Updating a local build does not require deleting its preferences.

Builds unregister their two app artifacts from Launch Services on exit, including
after a failed build, to reduce duplicate entries in Finder's Open With menu.
This includes a custom `CLOPPY_DERIVED_DATA_PATH`. Successful installation repeats
that cleanup and registers only the validated installed app. Catalogue failures
print warnings without failing the build or rolling back a committed installation;
no global catalogue reset or change to the official Clop is performed. Opening a
build copy or a later macOS scan can register it again. This workflow and its tests
are fork-owned in `.cloppy/overlay` and are reapplied by `make update`.

## Sync upstream

`make update` performs the complete local sync flow against `upstream`:

```sh
make update
```

It requires a clean attached checkout, fetches version tags, ignores betas and
selects the latest stable `vMAJOR.MINOR.PATCH` release. Already-current updates
exit without changing your branch. New releases use the canonical worktree helper
at `${AGENT_CONFIG_HOME:-$HOME/.agents}/scripts/new-worktree.sh` and an isolated
`cloppy-update-vX-Y-Z` branch. The candidate is rebuilt rather than merged: the
release's tree, plus fork-owned files from `.cloppy/overlay`, plus `.cloppy/patches`
applied with `git apply --3way` (see [.cloppy/README.md](.cloppy/README.md)).
Tests and signed build run before displaying the diff.
Review happens in the terminal: check access, updater, telemetry, sharing,
identity and permissions, then explicitly approve integration. A yes commits
the candidate with the previous branch tip and the release as parents and fast-forwards your original branch to that exact candidate.
Source/candidate changes during review block publication. Installation is separate;
run `make install` afterward. With `make hooks` enabled, integration on `main`
also invokes the post-merge push and cleanup finalizer. Push failure skips cleanup;
inspect hook output to confirm each result. Cleanup may remove the validated
candidate and its build artifacts; `make build` rebuilds from the integrated branch.

Patch conflicts, failed checks or declined review preserve the original branch and
leave the candidate for inspection. Resolve conflicts and stage everything with
`git add -A` in the reported worktree, then rerun `make update` from the original
checkout; the rerun folds the resolution back into `.cloppy` and proves that the
release plus the queue reproduces the candidate.
An existing candidate with another base/release stops rather than being reset.
Without the post-merge finalizer, candidates remain after successful integration
for build evidence and recovery.

Change fork behaviour on `main` as usual, stage it and run
`.cloppy/queue.py refresh` before committing: it rewrites the owning patch or overlay
file. A changed upstream file that no patch owns stops the refresh until you list it
in a patch. `make check` fails whenever `.cloppy` no longer reproduces the tree.

Retain Cloppy's Makefile and scripts in `.cloppy/overlay`; the original project's
install flow targets the official app.

The `CLOPPY` compilation condition separates local startup from commercial
startup. Local full access lives in `Clop/CloppyAccess.swift`; the optimisation
binary/decompression safeguards remain unchanged. Missing WarpDrop clients fail
with an unavailable message rather than copying a fake link. Keep new upstream
features from accidentally reintroducing activation, reports or official updates.

Keep `Package.resolved` under version control. During each update review changes
to it and Lowtech's APIs together. Resolve packages deliberately when upstream
changes requirements, then review and commit the new lockfile. Regular build
passes `-disableAutomaticPackageResolution` to avoid silently advancing branch pins.

Manual release checks: image/video/PDF/audio optimisation, >5 items, clipboard,
batch, restore, CLI and Shortcuts; separate Clop data/IPC, no automatic updater,
no activation/reporting and unavailable WarpDrop. Build alone does not prove
macOS permissions or every interaction. Do not publish as an official Clop build.

---

<p align="center">
    <a href="https://lowtechguys.com/clop"><img width="128" height="128" src="Clop/Assets.xcassets/clop.imageset/clop_256.png" style="filter: drop-shadow(0px 2px 4px rgba(80, 50, 6, 0.2));"></a>
    <h1 align="center"><code style="text-shadow: 0px 3px 10px rgba(8, 0, 6, 0.35); font-size: 3rem; font-family: ui-monospace, Menlo, monospace; font-weight: 800; background: transparent; color: #4d3e56; padding: 0.2rem 0.2rem; border-radius: 6px">Clop</code></h1>
    <h4 align="center" style="padding: 0; margin: 0; font-family: ui-monospace, monospace;">Image, video, PDF and clipboard optimiser</h4>
    <h6 align="center" style="padding: 0; margin: 0; font-family: ui-monospace, monospace; font-weight: 400;">Copy large, paste small, send fast</h6>
</p>

<p align="center">
    <a href="https://files.lowtechguys.com/releases/Clop.dmg">
        <img width=200 src="https://files.lowtechguys.com/macos-app.svg">
    </a>
</p>

## Optimise images as soon as you copy them

As long as the Clop app is running, every time you copy an image to your **clipboard**, Clop will **optimise** it to the **smallest possible size**.

The optimised image will have minimal to zero loss in quality, and will be **ready to paste** in any app.

## Screen recordings as small as screenshots

Sending screen recordings becomes 10x faster with Clop. The app will optimise the video as soon as you stop recording.

The video will be available as a **floating thumbnail**, ready for you to **drag and drop** in any app.

Clop can use Apple Silicon's dedicated **Media Engine chip** for battery-efficient video encoding without using the CPU.

## Downscale in a pinch

Get images and videos ready for sharing by scaling them down to any resolution.

Use handy hotkeys or the floating buttons to downscale the image or video and get an even smaller file size.

* <kbd>-</kbd> downscales incrementally from 90% until 10% of the original resolution
* <kbd>1</kbd>..<kbd>9</kbd> are for downscaling to specific sizes

## Power user features

### 1. On-demand optimisation

Press `Ctrl`-`Shift`-`C` to manually optimise the current clipboard.

The action works on *images*, *video* files, *paths*, *URLs*, even base64 encoded images.

For more aggressive optimisation, `Ctrl`-`Shift`-`A` is also available.


### 2. Compatible formats

Clop automatically **converts** less compatible formats like `HEIC`, `tiff`, `mov` to formats understood by most devices.

The conversion is fully configurable from the app settings.

Original files are kept in a backup folder which can be accessed from the app menu.


### 3. macOS Shortcuts

Integrate Clop optimisation in your workflows through **native macOS Shortcuts**.

- Downscale and optimise images that you email weekly
- Download optimised images directly into your slideshow
- ..and so on


## Free vs Pro

Free version features are free **forever**.

After the **14-day trial**, the app will continue to work with the free features.


| Feature | Clop Pro | Free version |
|---------|----------|--------------|
| Clipboard optimisation | ✅ | ✅ |
| Downscale images | ✅ | ✅ |
| Optimise screen recordings | ✅ | 5 per session |
| Optimise screenshot files | ✅ | 5 per session |
| On-demand optimisation | ✅ | 5 per session |
| Shortcuts support | ✅ | 5 per session |


## Technical details

Clop uses the following open source tools for optimising files, images and videos:

* `pngquant` for PNG
* `jpegoptim` for JPEG
* `gifsicle` for GIF
* `ffmpeg` for videos
* `libvips` for resizing images
* `gifski` for converting videos to GIFs
* `ghostscript` for optimising PDFs

It may also use `libvips` for resizing images if it is installed on your system.

The app is licensed under [GPLv3](https://github.com/FuzzyIdeas/Clop/blob/main/LICENSE).

## What's up with the hat?

*Clop* is the Romanian word for a traditional straw hat with a high crown and raised conical brim, worn more as an adorment in days of celebration.

We thought *"**Cl**ipboard **Op**timizer"* sounds a bit too technical and doesn't roll off the tongue as easily. We're <b style="color: red">Rom</b><b style="color: yellow">an</b><b style="color: blue">ian</b> ourselves and we thought it might be a good idea to keep the memory of our traditions from dying completely, with whatever little we can do.

## Contact

For questions you can contact us through the [contact form](https://lowtechguys.com/contact?app=Clop) or we can do troubleshooting on [Discord](https://discord.gg/YeTuy6adXk) if an async discussion would take too much. 
