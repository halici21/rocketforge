"""The real application shell, driven through the routes that once failed.

Two failures reached a user-facing build while every other test passed:

* **Crash.** Nozzle Lab (Operating point) -> Thermochemistry raised an access
  violation in Qt6Qml, 8 of 9 runs. The notation helper then allocated so much
  on every label binding that Qt's incremental garbage collector ran in the
  middle of the page switch and freed objects still in use. Nothing in the
  suite navigated the shell into Thermochemistry, so nothing saw it.
* **Hang.** Under PySide6 6.11.2 opening Thermochemistry never returned. CI was
  green on that upgrade for the same reason.

Each route runs in its own process under a real event loop with a hard
timeout, so a crash or a hang is a failed test and never a stuck job, and any
Qt/QML warning on the way fails it too. The negative controls prove the
harness can see each of the three failures it guards against.

In the base environment, with no chemistry provider, Thermochemistry shows its
"provider unavailable" state: still a real page load, still a real switch.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

DRIVER = pathlib.Path(__file__).resolve().parent / "shell_navigation_driver.py"
ROOT = DRIVER.parents[2]
ACCESS_VIOLATION = 0xC0000005

#: The audit route that crashed, then the direct routes into and out of
#: Thermochemistry named by the stabilization program.
ROUTES = {
    "nozzle_operating_point_to_thermochemistry": (
        "solve,page:isentropic,section:0,page:obliqueshock,section:0,section:1,"
        "page:nozzlelab,section:0,section:1,page:thermochem,section:1,"
        "page:nozzlelab,section:1,page:thermochem,page:nozzlelab,section:1,page:thermochem"),
    "nozzle_regime_map_to_thermochemistry": (
        "solve,page:nozzlelab,section:0,page:thermochem,page:nozzlelab,section:0,page:thermochem"),
    "isentropic_to_thermochemistry": "solve,page:isentropic,section:0,page:thermochem",
    "rocket_performance_to_thermochemistry": "solve,page:performance,section:0,page:thermochem",
    "trade_study_to_thermochemistry": "solve,page:tradestudy,section:2,page:thermochem",
    "solid_thermochemistry_to_nozzle": (
        "page:thermochem,solid:rp1311-example5,section:1,page:nozzlelab,section:1,"
        "page:thermochem,biprop,page:nozzlelab"),
    "engine_design_and_back": "page:thermochem,mode:engine,mode:analysis,page:nozzlelab,section:1",
}


def run_route(route: str, *, timeout: float = 120.0, inject: str = "",
              env: dict | None = None) -> dict:
    """Run the driver once and classify the outcome. Never raises on failure."""
    command = [sys.executable, "-X", "faulthandler", str(DRIVER), route]
    if inject:
        command += ["--inject", inject]
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1", **(env or {}))
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8",
                               errors="replace")
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # A venv interpreter on Windows is a launcher with the real Python as
        # its child: killing only the launcher would leave the hung process.
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)],
                           capture_output=True)
        else:
            process.kill()
        stdout, _ = process.communicate()
        return {"status": "hang", "steps": stdout.count("STEP "), "warnings": [],
                "detail": f"no exit within {timeout:.0f} s"}
    result = {"status": "failed", "steps": stdout.count("STEP "), "warnings": [],
              "detail": stderr[-1500:]}
    for line in stdout.splitlines():
        if line.startswith("RESULT "):
            result.update(json.loads(line[len("RESULT "):]))
    if (process.returncode & 0xFFFFFFFF) == ACCESS_VIOLATION or "Windows fatal exception" in stderr:
        result["status"] = "crash"
    elif process.returncode != 0:
        result["status"] = "failed"
    result["exit"] = process.returncode
    return result


@pytest.mark.parametrize("name", sorted(ROUTES))
def test_the_route_completes_without_a_crash_a_hang_or_a_warning(name):
    result = run_route(ROUTES[name])
    expected_steps = ROUTES[name].count(",") + 1
    assert result["status"] == "ok", result
    assert result["steps"] == expected_steps, result
    assert result["warnings"] == [], result["warnings"]


def test_the_audit_route_survives_the_incremental_collector_as_well():
    """The notation fix on its own, with Qt's incremental collector back on.

    The application collects in one pass (main.configure_application), which
    would hide a return of the allocation that provoked the crash. This run
    asks Qt for its own default, a 5 ms incremental step, so that regression
    stays visible: before the fix, this route crashed in 5 of 5 runs.
    """
    route = ROUTES["nozzle_operating_point_to_thermochemistry"]
    result = run_route(route, env={"QV4_GC_TIMELIMIT": "5"})
    assert result["status"] == "ok", result
    assert result["steps"] == route.count(",") + 1, result
    assert result["warnings"] == [], result["warnings"]


def test_the_application_collects_the_qml_heap_in_one_pass(monkeypatch):
    """Qt 6.10.2's incremental collector freed objects still in use; the
    application turns it off before any engine exists, unless told otherwise."""
    import main

    monkeypatch.delenv("QV4_GC_TIMELIMIT", raising=False)
    main.configure_application()
    assert os.environ["QV4_GC_TIMELIMIT"] == "0"

    monkeypatch.setenv("QV4_GC_TIMELIMIT", "5")
    main.configure_application()
    assert os.environ["QV4_GC_TIMELIMIT"] == "5"


# ---------------------------------------------------------------------------
# negative controls: the three failures above must each be visible
# ---------------------------------------------------------------------------


def test_the_smoke_would_see_a_qml_warning():
    result = run_route("page:isentropic,page:nozzlelab", inject="warning")
    assert result["status"] == "ok"
    assert any("undefinedThing" in w for w in result["warnings"]), result


def test_the_smoke_would_see_a_crash():
    result = run_route("page:isentropic,page:nozzlelab", inject="crash")
    assert result["status"] == "crash", result


def test_the_smoke_would_see_a_hang():
    result = run_route("page:isentropic,page:nozzlelab", inject="hang", timeout=30)
    assert result["status"] == "hang", result
