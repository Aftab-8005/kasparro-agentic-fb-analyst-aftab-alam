import sys
import os
import pathlib

# Absolute path to project root (folder that contains src/)
ROOT = pathlib.Path(__file__).resolve().parent

# Add project root to PYTHONPATH
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

print("PYTHONPATH configured:", sys.path[:3])
