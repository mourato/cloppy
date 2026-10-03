#!/bin/bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
xcodebuild -project "$repo/Clop.xcodeproj" -scheme Clop -configuration Release \
    -derivedDataPath "$repo/build/DerivedData" -disableAutomaticPackageResolution \
    -destination "platform=macOS,arch=$(uname -m)" ONLY_ACTIVE_ARCH=YES \
    CODE_SIGN_IDENTITY=- CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM= \
    CODE_SIGNING_ALLOWED=YES ENABLE_APP_SANDBOX=NO build
mkdir -p "$repo/build"
rm -rf "$repo/build/Cloppy.app"
ditto "$repo/build/DerivedData/Build/Products/Release/Cloppy.app" "$repo/build/Cloppy.app"
codesign --verify --deep --strict "$repo/build/Cloppy.app"
printf 'Built %s\n' "$repo/build/Cloppy.app"
python3 - "$repo/build/Cloppy.app/Contents/Info.plist" <<'CHECK'
import plistlib, sys
with open(sys.argv[1], 'rb') as source:
    info = plistlib.load(source)
assert info['CFBundleIdentifier'] == 'local.cloppy.app'
assert info['CFBundleName'] == 'Cloppy'
assert info.get('CFBundleDisplayName') == 'Cloppy'
assert 'SUFeedURL' not in info and 'SUPublicEDKey' not in info
assert info['NSPrincipalClass'] == 'NSApplication'
assert info['CFBundleURLTypes'][0]['CFBundleURLSchemes'] == ['cloppy']
CHECK
