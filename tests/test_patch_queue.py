"""The checked-in tree must equal upstream + .cloppy, so the queue never drifts from main."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent


class PatchQueueTests(unittest.TestCase):
    def test_upstream_plus_queue_reproduces_the_index(self):
        result = subprocess.run([sys.executable, str(ROOT / '.cloppy/queue.py'), 'verify'], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
