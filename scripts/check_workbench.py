"""Run the offline test suite.

  python scripts/check_workbench.py            all tests
  python scripts/check_workbench.py -k mirror  only tests whose name contains 'mirror'
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    loader = unittest.TestLoader()
    if argv[:1] == ["-k"] and len(argv) > 1:
        loader.testNamePatterns = [f"*{argv[1]}*"]
    suite = loader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
