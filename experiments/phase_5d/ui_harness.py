"""Phase 5D UI harness, source side.

The tour itself lives in :mod:`rocketforge.application.uismoke`, so that the
source build and the packaged executable run **the same code** and their
reports can be compared field by field. This file only supplies the bootstrap,
the output directory and the offscreen platform.

Usage::

    .venv-cea\\Scripts\\python.exe experiments\\phase_5d\\ui_harness.py <outdir>

Run it from ``.venv`` instead and it captures the provider-unavailable states,
which is the point of that environment existing.

Set ``QT_QPA_FONTDIR=C:/Windows/Fonts`` alongside the offscreen platform: the
offscreen plugin ships no fonts of its own, and without one every text run
falls back to a missing family. That is a property of the plugin -- the same
warning appears on the existing Nozzle Lab charts -- not of the workspace.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import main as bootstrap  # noqa: E402
from rocketforge.application.uismoke import run_ui_smoke  # noqa: E402

if __name__ == "__main__":
    target = (sys.argv[1] if len(sys.argv) > 1
              else str(ROOT / "acceptance" / "phase_5d"))
    sys.exit(run_ui_smoke([target], bootstrap.configure_application,
                          bootstrap.build_engine, bootstrap.UI_DIR))
