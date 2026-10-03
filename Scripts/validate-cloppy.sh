#!/bin/bash
set -euo pipefail
app="${1:?Usage: validate-cloppy.sh APP}"
codesign --verify --deep --strict "$app"
python3 - "$app" <<'CHECK'
import pathlib, plistlib, sys
app = pathlib.Path(sys.argv[1])
with (app / 'Contents/Info.plist').open('rb') as source:
    info = plistlib.load(source)
assert info['CFBundleIdentifier'] == 'local.cloppy.app', 'Unexpected bundle ID'
assert info['CFBundleName'] == info.get('CFBundleDisplayName') == 'Cloppy'
assert 'SUFeedURL' not in info and 'SUPublicEDKey' not in info, 'Official updater configured'
assert info['NSPrincipalClass'] == 'NSApplication'
assert info['CFBundleURLTypes'][0]['CFBundleURLSchemes'] == ['cloppy']
assert (app / 'Contents/MacOS/Cloppy').is_file()
for resource in ['bin.tar.lrz', 'bin.tar.lrz.sha256', 'lrzip']:
    assert (app / 'Contents/Resources' / resource).is_file(), resource
assert (app / 'Contents/SharedSupport/ClopCLI').is_file()
CHECK
