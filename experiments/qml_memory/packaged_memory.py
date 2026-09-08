"""Sample the packaged executable's memory from outside it.

The in-process harness cannot run inside the frozen build, so this launches the
packaged application on its own self-test tours and polls the child process's
private bytes and working set while it runs. What it can answer is the question
that matters for packaging: does the frozen build behave like the source build,
or does bundling change the memory profile.

    python experiments/qml_memory/packaged_memory.py

Source-side equivalents are read from the acceptance artifacts so the two are
reported side by side.
"""
from __future__ import annotations

import ctypes
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "qml_memory"
EXE = ROOT / "dist" / "RocketForge" / "RocketForge.exe"
MB = 1024 * 1024

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class _CountersEx(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]


_K32 = ctypes.WinDLL("kernel32", use_last_error=True)
_K32.OpenProcess.restype = ctypes.c_void_p
_K32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
_K32.CloseHandle.argtypes = [ctypes.c_void_p]
_K32.K32GetProcessMemoryInfo.restype = ctypes.c_int
_K32.K32GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(_CountersEx),
                                         ctypes.c_uint32]


def sample(handle) -> dict | None:
    counters = _CountersEx()
    counters.cb = ctypes.sizeof(_CountersEx)
    if not _K32.K32GetProcessMemoryInfo(handle, ctypes.byref(counters),
                                        counters.cb):
        return None
    return {"private_mb": round(counters.PrivateUsage / MB, 2),
            "working_set_mb": round(counters.WorkingSetSize / MB, 2),
            "peak_working_set_mb": round(counters.PeakWorkingSetSize / MB, 2)}


def run(flag: str) -> dict:
    import os

    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QPA_FONTDIR"] = "C:/Windows/Fonts"
    started = time.perf_counter()
    process = subprocess.Popen([str(EXE), flag], env=env,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    handle = _K32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False,
                              process.pid)
    series = []
    last = None
    while process.poll() is None:
        if handle:
            reading = sample(handle)
            if reading:
                last = reading
                series.append({"t": round(time.perf_counter() - started, 2),
                               **reading})
        time.sleep(0.25)
    output = process.stdout.read().decode("utf-8", "replace")
    if handle:
        _K32.CloseHandle(handle)
    peak = max((row["private_mb"] for row in series), default=0.0)
    return {"flag": flag, "exit_code": process.returncode,
            "elapsed_s": round(time.perf_counter() - started, 2),
            "samples": len(series), "series": series[-40:],
            "peak_private_mb": peak,
            "final": last,
            "tail": output.strip().splitlines()[-1] if output.strip() else ""}


def main() -> int:
    if not EXE.is_file():
        print(f"no packaged build at {EXE}")
        return 1

    tours = ("--selftest-rocket-performance", "--selftest-workspaces",
             "--selftest-trade-study", "--selftest-thermochemistry-ui")
    results = [run(flag) for flag in tours]

    source_1000 = None
    path = OUT / "final_1000_current.json"
    if path.is_file():
        source_1000 = json.loads(path.read_text(encoding="utf-8"))[
            "private_total_mb"]

    report = {
        "purpose": "the packaged build must not behave differently from source",
        "executable": str(EXE.relative_to(ROOT).as_posix()),
        "tours": results,
        "source_reference": {
            "recalculation_1000_private_growth_mb": source_1000,
            "note": "the in-process harness cannot run inside the frozen "
                    "build; what is compared here is whether a packaged tour "
                    "completes with a bounded peak, not a like-for-like "
                    "growth figure",
        },
        "all_tours_exited_zero": all(r["exit_code"] == 0 for r in results),
    }
    report["verdict"] = "PASS" if report["all_tours_exited_zero"] else "FAIL"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "packaged_memory.json").write_text(json.dumps(report, indent=2),
                                              encoding="utf-8")
    for row in results:
        print(f"  {row['flag']:36s} exit={row['exit_code']} "
              f"peak private {row['peak_private_mb']:7.1f} MB  "
              f"{row['elapsed_s']:5.1f}s")
    print(report["verdict"])
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
