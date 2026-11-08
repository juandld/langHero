"""Moved to heroCommon as hero_common.jev_client (Decision #3463, 2026-11-08).

This shim keeps `lib.jev_client` imports and the CLI working. Edit
heroCommon/src/hero_common/jev_client.py, never this file (invariant 166).
"""
import sys
from pathlib import Path

try:
    import hero_common  # noqa: F401
except ImportError:  # interpreter without the editable install (python3 -I, a fresh venv): use the sibling checkout
    sys.path.append(str(Path(__file__).resolve().parents[3] / "heroCommon" / "src"))

if __name__ == "__main__":
    import runpy

    runpy.run_module("hero_common.jev_client", run_name="__main__")
else:
    import importlib

    sys.modules[__name__] = importlib.import_module("hero_common.jev_client")
