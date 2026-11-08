"""Moved to heroCommon as hero_common.usage_log (Decision #3463, 2026-11-08).

This shim keeps `usage_log` imports and the CLI working. Edit
heroCommon/src/hero_common/usage_log.py, never this file (invariant 166).
"""
import sys
from pathlib import Path

try:
    import hero_common  # noqa: F401
except ImportError:  # interpreter without the editable install (python3 -I, a fresh venv): use the sibling checkout
    sys.path.append(str(Path(__file__).resolve().parents[2] / "heroCommon" / "src"))

if __name__ == "__main__":
    import runpy

    runpy.run_module("hero_common.usage_log", run_name="__main__")
else:
    import importlib

    sys.modules[__name__] = importlib.import_module("hero_common.usage_log")
    sys.modules[__name__].configure(str(Path(__file__).resolve().parent / "usage"))
