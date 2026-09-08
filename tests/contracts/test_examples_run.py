"""The examples are executed, so they cannot rot.

An example that no longer runs is worse than no example: it teaches a signature
that does not exist. These run each one in a subprocess with PySide6 blocked,
which checks three things at once -- the public API still has the shape the
example uses, the example produces output, and none of it needs Qt.

A failure here after an API change is the intended signal, not noise: the
example and the contract move together or the change is not finished.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXAMPLES = sorted((ROOT / "examples" / "compressible").glob("*_example.py"))
NAMES = [path.stem for path in EXAMPLES]


def test_the_example_suite_covers_every_module():
    """One example per public module, plus the end-to-end script."""
    expected = {
        "isentropic_example", "mass_flow_example", "normal_shock_example",
        "prandtl_meyer_example", "oblique_shock_example", "fanno_example",
        "rayleigh_example", "cd_nozzle_example", "end_to_end_example",
    }
    assert set(NAMES) == expected


@pytest.mark.parametrize("name", NAMES)
def test_the_example_runs_without_qt(name):
    """Executed as a module from the project root, exactly as documented."""
    completed = subprocess.run(
        [sys.executable, "-c",
         "import sys\n"
         "class Block:\n"
         "    def find_module(self, name, path=None):\n"
         "        return self if name.split('.')[0] == 'PySide6' else None\n"
         "    def load_module(self, name):\n"
         "        raise ImportError('PySide6 is blocked')\n"
         "sys.meta_path.insert(0, Block())\n"
         "import runpy\n"
         f"runpy.run_module('examples.compressible.{name}', run_name='__main__')\n"
         "assert 'PySide6' not in sys.modules\n"],
        cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert completed.returncode == 0, (
        f"{name} failed:\n{completed.stdout[-2000:]}\n{completed.stderr[-2000:]}")
    assert completed.stdout.strip(), f"{name} produced no output"


@pytest.mark.parametrize("path", EXAMPLES, ids=NAMES)
def test_the_example_uses_only_the_public_namespace(path):
    """No example may reach past the package to a private module path."""
    source = path.read_text(encoding="utf-8")
    for line in source.splitlines():
        if line.startswith(("import ", "from ")) and "rocketforge" in line:
            assert "from rocketforge.physics.compressible import" in line, (
                f"{path.name} imports from a private path: {line.strip()}")
    assert "PySide6" not in source
    assert "_" + "helper" not in source


@pytest.mark.parametrize("path", EXAMPLES, ids=NAMES)
def test_the_example_documents_how_to_run_it(path):
    source = path.read_text(encoding="utf-8")
    assert "-m examples.compressible." + path.stem in source
