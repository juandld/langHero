"""Moved to heroCommon as hero_common.telegram_out (Decision #3463, 2026-11-08).

This shim keeps `lib.telegram_out` imports and the CLI working. Edit
heroCommon/src/hero_common/telegram_out.py, never this file (invariant 166).
"""
import sys
from pathlib import Path

try:
    import hero_common  # noqa: F401
except ImportError:  # interpreter without the editable install (python3 -I, a fresh venv): use the sibling checkout
    sys.path.append(str(Path(__file__).resolve().parents[3] / "heroCommon" / "src"))

if __name__ == "__main__":
    import runpy

    runpy.run_module("hero_common.telegram_out", run_name="__main__")
else:
    import importlib

    sys.modules[__name__] = importlib.import_module("hero_common.telegram_out")
