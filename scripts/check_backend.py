import py_compile
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def compile_backend() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        for path in sorted((ROOT / "backend").glob("*.py")):
            py_compile.compile(
                str(path),
                cfile=str(cache_dir / f"{path.stem}.pyc"),
                doraise=True,
            )


def run_tests() -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    compile_backend()
    run_tests()
