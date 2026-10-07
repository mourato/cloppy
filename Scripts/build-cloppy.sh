#!/bin/bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
source "$repo/Scripts/signing.sh"
source "$repo/Scripts/launch-services.sh"
identity="$(resolve_signing_identity)"
# Xcode can register its product even when a later signing/validation step fails.
trap unregister_cloppy_builds EXIT
xcodebuild -project "$repo/Clop.xcodeproj" -scheme Clop -configuration Release \
    -derivedDataPath "${CLOPPY_DERIVED_DATA_PATH:-$repo/build/DerivedData}" -disableAutomaticPackageResolution \
    -destination "platform=macOS,arch=$(uname -m)" ONLY_ACTIVE_ARCH=YES \
    CODE_SIGN_IDENTITY=- CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM= \
    CODE_SIGNING_ALLOWED=YES ENABLE_APP_SANDBOX=NO build
mkdir -p "$repo/build"
candidate="${CLOPPY_DERIVED_DATA_PATH:-$repo/build/DerivedData}/Build/Products/Release/Cloppy.app"
codesign --force --deep --preserve-metadata=identifier,entitlements,flags --timestamp=none --sign "$identity" "$candidate"
codesign --verify --deep --strict -R "=certificate leaf = H\"$identity\"" "$candidate"
"$repo/Scripts/validate-cloppy.sh" "$candidate"
rm -rf "$repo/build/Cloppy.app"
ditto "$candidate" "$repo/build/Cloppy.app"
"$repo/Scripts/validate-cloppy.sh" "$repo/build/Cloppy.app"
printf 'Built %s\n' "$repo/build/Cloppy.app"
