"""Is this package the canonical RocketForge build of that commit? Checked, not assumed.

usage:
    verify_package.py [--package DIR] [--expect-commit SHA|HEAD] [--smoke]
                      [--allow-development]

Defaults: the package is dist/RocketForge beside this repository, and the
expected commit is the repository's HEAD. Exit status 0 only when every check
passes; each failure is printed on its own line.

Checks, each a function so the tests can drive its failure cases:

    layout          dist/RocketForge holds one RocketForge.exe and its runtime,
                    and dist/ holds no other RocketForge build beside it
    manifest        rocketforge_build.json is valid, production, clean, and
                    names exactly the expected commit
    pins            the manifest's PySide6, NASA CEA and CoolProp are the
                    versions the requirement files pin
    version         the executable's own Windows version resource names the
                    same commit -- the identity survives a copied .exe
    runtime         the executable, asked with --build-info, reports itself as
                    that packaged build: the identity the user will see
    3d runtime      the package carries exactly the Qt Quick 3D files the 3D view
                    loads, and no other file of the PySide6-Addons wheel
                    (packaging/qt3d_runtime.py)
    smoke           (--smoke) the bundled thermochemistry provider, the
                    Operating point -> Thermochemistry route that once crashed,
                    and the science self-test, all inside the package; and,
                    when the package carries Qt Quick 3D, Rocket Performance's
                    3D view opened and closed on the real windows platform
                    (the offscreen platform cannot run Qt Quick 3D)
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rocketforge.application import build_identity  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qt3d_runtime  # noqa: E402

EXE_NAME = "RocketForge.exe"

#: The route the navigation crash took, run twice through: Isentropic ->
#: Oblique Shock -> Nozzle Lab -> Operating point -> Thermochemistry, then
#: Operating point <-> Thermochemistry. Must finish with no warning.
CRASH_ROUTE = ("solve,page:isentropic,section:0,page:obliqueshock,section:0,section:1,"
               "page:nozzlelab,section:0,section:1,page:thermochem,section:1,"
               "page:nozzlelab,section:1,page:thermochem,page:nozzlelab,section:1,"
               "page:thermochem")

#: Rocket Performance solved and its 3D view opened -- a scene must exist --
#: then, with the flow cues playing, a solid chamber that Rocket Performance
#: refuses (the snapshot goes invalid under the live particle system: this
#: once crashed), the bipropellant case solved again, and the view closed --
#: the scene must be gone.
VIEWPORT_ROUTE = ("solve,page:performance,view:3d,expect3d:yes,capture:viewport3d,"
                  "solid:rp1311-example5,solve,expect3d:yes,biprop,solve,expect3d:yes,"
                  "view:2d,expect3d:no,"
                  # Nozzle Lab's regime map, in the same shared viewport
                  "page:nozzlelab,section:0,view:3d,expect3d:yes,capture:nozzle3d,"
                  "view:2d,expect3d:no")


def git_head(repo: Path) -> str:
    done = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit(f"cannot read HEAD of {repo}: {done.stderr.strip()}")
    return done.stdout.strip()


def pinned(requirements: Path, name: str) -> str:
    """The exact version a requirements file pins for ``name``, or ""."""
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*==\s*([^\s#;]+)", re.IGNORECASE)
    for line in requirements.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1)
    return ""


def check_layout(package: Path) -> list[str]:
    failures = []
    exe = package / EXE_NAME
    if not exe.is_file():
        return [f"layout: {exe} is missing"]
    if not (package / "_internal").is_dir():
        failures.append("layout: _internal/ runtime folder is missing")
    executables = sorted(p.name for p in package.glob("*.exe"))
    if executables != [EXE_NAME]:
        failures.append(f"layout: expected only {EXE_NAME} at the top, found {executables}")
    dist = package.parent
    siblings = sorted(p.name for p in dist.iterdir()
                      if p != package and "rocketforge" in p.name.lower())
    if siblings:
        failures.append(f"layout: other RocketForge builds beside the canonical one in "
                        f"{dist}: {siblings}")
    return failures


def check_manifest(package: Path, expected_commit: str, *,
                   allow_development: bool = False) -> tuple[list[str], dict | None]:
    try:
        manifest = build_identity.read_manifest(package / build_identity.MANIFEST_NAME)
    except ValueError as error:
        return [f"manifest: {error}"], None
    failures = []
    if manifest["commit"] != expected_commit:
        failures.append(f"manifest: built from {manifest['commit']}, expected "
                        f"{expected_commit} -- this package is stale")
    if not allow_development:
        if manifest["channel"] != build_identity.PRODUCTION:
            failures.append(f"manifest: channel is {manifest['channel']!r}, not production")
        if manifest["dirty"] is not False:
            failures.append("manifest: built from a dirty tree")
    return failures, manifest


def check_pins(manifest: dict, repo: Path) -> list[str]:
    failures = []
    for key, requirements, name in (
            ("pyside6", "requirements.txt", "PySide6-Essentials"),
            ("cea", "requirements-thermochemistry.txt", "cea"),
            ("coolprop", "requirements-fluids.txt", "CoolProp")):
        wanted = pinned(repo / requirements, name)
        if manifest.get(key) != wanted:
            failures.append(f"pins: package has {name} {manifest.get(key)!r}, "
                            f"{requirements} pins {wanted!r}")
    return failures


def read_version_strings(exe: Path) -> dict:
    """The executable's StringFileInfo, read with the Windows version API."""
    if sys.platform != "win32":
        return {}
    api = ctypes.windll.version
    size = api.GetFileVersionInfoSizeW(str(exe), None)
    if not size:
        return {}
    buffer = ctypes.create_string_buffer(size)
    if not api.GetFileVersionInfoW(str(exe), 0, size, buffer):
        return {}
    pointer, length = ctypes.c_void_p(), ctypes.c_uint()
    if not api.VerQueryValueW(buffer, "\\VarFileInfo\\Translation",
                              ctypes.byref(pointer), ctypes.byref(length)):
        return {}
    language, codepage = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ushort * 2)).contents
    block = f"\\StringFileInfo\\{language:04x}{codepage:04x}\\"
    strings = {}
    for key in ("ProductName", "FileDescription", "ProductVersion", "FileVersion",
                "OriginalFilename", "InternalName", "Comments", "LegalCopyright"):
        if api.VerQueryValueW(buffer, block + key, ctypes.byref(pointer),
                              ctypes.byref(length)) and length.value:
            strings[key] = ctypes.wstring_at(pointer, length.value - 1)
    return strings


def check_version_resource(package: Path, manifest: dict) -> list[str]:
    strings = read_version_strings(package / EXE_NAME)
    if not strings:
        return ["version: the executable carries no version resource"]
    failures = []
    if strings.get("ProductName") != manifest["product"]:
        failures.append(f"version: ProductName is {strings.get('ProductName')!r}")
    if manifest["commit"] not in strings.get("Comments", ""):
        failures.append(f"version: the executable names {strings.get('Comments')!r}, "
                        f"not commit {manifest['commit']}")
    if manifest["commit"][:7] not in strings.get("ProductVersion", ""):
        failures.append(f"version: ProductVersion {strings.get('ProductVersion')!r} "
                        f"does not name {manifest['commit'][:7]}")
    return failures


def _run_packaged(package: Path, *args: str, timeout: float = 300,
                  platform: str = "offscreen") -> int:
    env = dict(os.environ, QT_QPA_PLATFORM=platform)
    env.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    done = subprocess.run([str(package / EXE_NAME), *args], cwd=package, env=env,
                          capture_output=True, timeout=timeout)
    return done.returncode


def check_runtime(package: Path, manifest: dict) -> list[str]:
    with tempfile.TemporaryDirectory() as folder:
        report = Path(folder) / "build_info.json"
        code = _run_packaged(package, "--build-info", str(report), timeout=120)
        if code != 0 or not report.is_file():
            return [f"runtime: --build-info exited {code} without a report"]
        info = json.loads(report.read_text(encoding="utf-8"))
    failures = []
    expected = {"packaged": True, "commit": manifest["commit"],
                "channel": manifest["channel"], "dirty": manifest["dirty"],
                "pyside6": manifest["pyside6"], "qt": manifest["qt"]}
    for key, value in expected.items():
        if info.get(key) != value:
            failures.append(f"runtime: reports {key}={info.get(key)!r}, manifest says {value!r}")
    return failures


def check_smoke(package: Path) -> list[str]:
    failures = []
    code = _run_packaged(package, "--selftest-thermochemistry")
    if code != 0:
        failures.append(f"smoke: --selftest-thermochemistry exited {code}")
    with tempfile.TemporaryDirectory() as folder:
        nav = Path(folder) / "navigation.json"
        code = _run_packaged(package, "--selftest-navigation", str(nav), CRASH_ROUTE)
        if code != 0 or not nav.is_file():
            failures.append(f"smoke: the navigation crash route exited {code} "
                            f"({nav.read_text(encoding='utf-8')[:300] if nav.is_file() else 'no report'})")
        science = Path(folder) / "science.json"
        code = _run_packaged(package, "--selftest-science", str(science))
        if code != 0:
            failures.append(f"smoke: --selftest-science exited {code}")
        if (package / "_internal" / "PySide6" / "QtQuick3D.pyd").is_file():
            viewport = Path(folder) / "viewport.json"
            code = _run_packaged(package, "--selftest-navigation", str(viewport),
                                 VIEWPORT_ROUTE, "--window", "1280x800", platform="windows")
            if code != 0:
                failures.append(f"smoke: the 3D view route exited {code} "
                                f"({viewport.read_text(encoding='utf-8')[:300] if viewport.is_file() else 'no report'})")
    return failures


def check_3d_runtime(package: Path) -> list[str]:
    return qt3d_runtime.check_package(package / "_internal", qt3d_runtime.addons_files())


def verify(package: Path, expected_commit: str, repo: Path, *, smoke: bool,
           allow_development: bool = False) -> list[str]:
    failures = check_layout(package)
    if not (package / EXE_NAME).is_file():
        return failures
    manifest_failures, manifest = check_manifest(package, expected_commit,
                                                 allow_development=allow_development)
    failures += manifest_failures
    if manifest is None:
        return failures
    failures += check_pins(manifest, repo)
    failures += check_3d_runtime(package)
    failures += check_version_resource(package, manifest)
    failures += check_runtime(package, manifest)
    if smoke:
        failures += check_smoke(package)
    return failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--package", type=Path, default=ROOT / "dist" / "RocketForge")
    parser.add_argument("--expect-commit", default="HEAD")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-development", action="store_true")
    args = parser.parse_args(argv)
    expected = git_head(ROOT) if args.expect_commit == "HEAD" else args.expect_commit
    failures = verify(args.package.resolve(), expected, ROOT, smoke=args.smoke,
                      allow_development=args.allow_development)
    for failure in failures:
        print(f"FAIL  {failure}")
    print(f"{'PASS' if not failures else 'FAIL'}  {args.package} against commit {expected}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
