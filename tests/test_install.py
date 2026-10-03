"""Installer transactions use disposable bundles and stub only OS signing/process APIs."""
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cloppy-install-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / 'project'
        self.apps = self.root / 'Applications'
        self.tools = self.root / 'tools'
        for directory in [self.project / 'Scripts', self.apps, self.tools]:
            directory.mkdir(parents=True)
        for script in ['install-cloppy.sh', 'validate-cloppy.sh', 'signing.sh']:
            shutil.copy2(ROOT / 'Scripts' / script, self.project / 'Scripts' / script)
        self.bundle(self.project / 'build/Cloppy.app', 'new')
        self.bundle(self.apps / 'Cloppy.app', 'old')
        self.bundle(self.apps / 'Clop.app', 'official')
        self.tool('security', '#!/bin/bash\nprintf \' 1) AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA "Apple Development: Test"\\n\'\n')
        self.tool('pgrep', '#!/bin/bash\nexit 1\n')
        self.tool('codesign', '''#!/bin/bash
for argument in "$@"; do
    if [[ "${FAIL_INSTALLED_VERIFY:-0}" == 1 && "$argument" == "$APPLICATIONS_DIR/Cloppy.app" && -f "$argument/marker" ]] && grep -q new "$argument/marker"; then exit 1; fi
done
exit 0
''')
        self.env = dict(os.environ, PATH=f'{self.tools}:{os.environ["PATH"]}', APPLICATIONS_DIR=str(self.apps), CLOPPY_CODE_SIGN_IDENTITY='Apple Development')

    def tool(self, name, content):
        path = self.tools / name
        path.write_text(content)
        path.chmod(0o755)

    def bundle(self, app, marker):
        for directory in ['Contents/MacOS', 'Contents/Resources', 'Contents/SharedSupport']:
            (app / directory).mkdir(parents=True)
        info = {'CFBundleIdentifier': 'local.cloppy.app', 'CFBundleName': 'Cloppy', 'CFBundleDisplayName': 'Cloppy', 'NSPrincipalClass': 'NSApplication', 'CFBundleURLTypes': [{'CFBundleURLSchemes': ['cloppy']}]}
        (app / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
        for resource in ['bin.tar.lrz', 'bin.tar.lrz.sha256', 'lrzip']:
            (app / 'Contents/Resources' / resource).write_text('fixture')
        (app / 'Contents/MacOS/Cloppy').write_text('fixture')
        (app / 'Contents/SharedSupport/ClopCLI').write_text('fixture')
        (app / 'marker').write_text(marker)

    def invoke(self):
        return subprocess.run([str(self.project / 'Scripts/install-cloppy.sh')], env=self.env, text=True, capture_output=True)

    def assert_clean(self):
        self.assertEqual(list(self.apps.glob('.cloppy-install.*')), [])
        self.assertEqual((self.apps / 'Clop.app/marker').read_text(), 'official')

    def test_replaces_only_cloppy_and_removes_transaction(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.apps / 'Cloppy.app/marker').read_text(), 'new')
        self.assert_clean()

    def test_failed_final_validation_restores_previous_bundle(self):
        self.env['FAIL_INSTALLED_VERIFY'] = '1'
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.apps / 'Cloppy.app/marker').read_text(), 'old')
        self.assert_clean()

    def test_other_installer_lock_is_not_removed(self):
        lock = self.apps / '.cloppy-install.lock'
        lock.mkdir()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(lock.is_dir())
        self.assertEqual((self.apps / 'Cloppy.app/marker').read_text(), 'old')
        lock.rmdir()
        self.assert_clean()

    def test_symlink_target_is_never_replaced(self):
        shutil.rmtree(self.apps / 'Cloppy.app')
        (self.apps / 'Cloppy.app').symlink_to(self.apps / 'Clop.app')
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertTrue((self.apps / 'Cloppy.app').is_symlink())
        self.assert_clean()

    def test_missing_certificate_stops_before_replacement(self):
        self.env['CLOPPY_CODE_SIGN_IDENTITY'] = 'Missing test certificate'
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertEqual((self.apps / 'Cloppy.app/marker').read_text(), 'old')
        self.assert_clean()

    def test_lowercase_certificate_fingerprint_is_resolved(self):
        self.env['CLOPPY_CODE_SIGN_IDENTITY'] = 'a' * 40
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.apps / 'Cloppy.app/marker').read_text(), 'new')
        self.assert_clean()


if __name__ == '__main__':
    unittest.main()
