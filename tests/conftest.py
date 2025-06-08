import sys
from pathlib import Path


# Ensure the src directory is on the path for tests
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.as_posix() not in sys.path:
    sys.path.insert(0, SRC.as_posix())
