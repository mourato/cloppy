#!/bin/bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
source "$repo/Scripts/signing.sh"
identity="$(resolve_signing_identity)"
candidate="$repo/build/Cloppy.app"
applications="${APPLICATIONS_DIR:-/Applications}"
applications="$(cd "$applications" && pwd -P)"
[[ "$applications" != / && "$applications" != "$HOME" ]] || {
    echo 'Refusing unsafe installation directory' >&2; exit 1;
}
target="$applications/Cloppy.app"
"$repo/Scripts/validate-cloppy.sh" "$candidate"
codesign --verify --deep --strict -R "=certificate leaf = H\"$identity\"" "$candidate"
[[ ! -L "$target" ]] || { echo 'Refusing symlink installation target' >&2; exit 1; }
if [[ -e "$target" ]]; then
    "${repo}/Scripts/validate-cloppy.sh" "$target"
fi
initial_target="$(stat -f '%d:%i:%m' "$target" 2>/dev/null || true)"
if pgrep -x Cloppy >/dev/null; then
    osascript -e 'tell application id "local.cloppy.app" to quit'
    for ((waited=0; waited<15; waited++)); do
        pgrep -x Cloppy >/dev/null || break
        sleep 1
    done
    if pgrep -x Cloppy >/dev/null; then
        echo 'Cloppy is still running. Quit it before retrying make install.' >&2; exit 1
    fi
fi
# Stage on the destination volume; keep the old bundle until replacement verifies.
transaction="$(mktemp -d "$applications/.cloppy-install.XXXXXX")"
published_identity=""
committed=0
locked=0
cleanup() {
    local result=$?
    if [[ "$committed" == 0 ]]; then
        if [[ -n "$published_identity" && ( -e "$target" || -L "$target" ) ]]; then
            if [[ ! -L "$target" && "$(stat -f '%d:%i' "$target" 2>/dev/null || true)" == "$published_identity" ]]; then
                rm -rf "$target" || result=1
            else
                echo "Destination changed; preserved it. Recovery files: $transaction" >&2
                if [[ "$locked" == 1 ]]; then rmdir "$applications/.cloppy-install.lock"; fi
                exit 1
            fi
        fi
        if [[ -e "$transaction/previous.app" ]]; then
            if [[ -e "$target" || -L "$target" ]] || ! mv "$transaction/previous.app" "$target"; then
                echo "Recovery required: old app remains at $transaction/previous.app" >&2
                if [[ "$locked" == 1 ]]; then rmdir "$applications/.cloppy-install.lock"; fi
                exit 1
            fi
        fi
    fi
    rm -rf "$transaction"
    if [[ "$locked" == 1 ]]; then rmdir "$applications/.cloppy-install.lock"; fi
    exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir "$applications/.cloppy-install.lock" || {
    echo 'Another install owns .cloppy-install.lock; inspect before retrying.' >&2; exit 1;
}
locked=1
ditto "$candidate" "$transaction/Cloppy.app"
"$repo/Scripts/validate-cloppy.sh" "$transaction/Cloppy.app"
if [[ -L "$target" || "$(stat -f '%d:%i:%m' "$target" 2>/dev/null || true)" != "$initial_target" ]]; then
    echo 'Installation target changed while staging; refusing replacement.' >&2; exit 1
fi
if [[ -e "$target" ]]; then mv "$target" "$transaction/previous.app"; fi
published_identity="$(stat -f '%d:%i' "$transaction/Cloppy.app")"
mv "$transaction/Cloppy.app" "$target"
"$repo/Scripts/validate-cloppy.sh" "$target"
codesign --verify --deep --strict -R "=certificate leaf = H\"$identity\"" "$target"
[[ ! -L "$target" && "$(stat -f '%d:%i' "$target" 2>/dev/null || true)" == "$published_identity" ]] || {
    echo 'Installation target changed during validation.' >&2; exit 1;
}
committed=1
printf 'Installed %s (not launched)\n' "$target"
