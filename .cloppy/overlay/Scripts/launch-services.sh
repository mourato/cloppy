#!/bin/bash
# Catalogue maintenance must not invalidate a signed build or committed install.
cloppy_launch_services() {
    local tool=/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister
    if ! "$tool" "$@"; then
        printf 'Warning: Launch Services update failed for %s\n' "$*" >&2
    fi
}

unregister_cloppy_builds() {
    local app
    for app in "${CLOPPY_DERIVED_DATA_PATH:-$repo/build/DerivedData}/Build/Products/Release/Cloppy.app" "$repo/build/Cloppy.app"; do
        if [[ -d "$app" ]]; then
            cloppy_launch_services -u "$app"
        fi
    done
}
