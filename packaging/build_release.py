"""The canonical RocketForge build. Run through ``build_exe.bat``.

    build_exe.bat                 a production package of the committed master
    build_exe.bat --development   a package of any tree, labelled development

Output, always the same place and nowhere else:

    dist/RocketForge/RocketForge.exe          the application
    dist/RocketForge/rocketforge_build.json   its identity (read at run time)
    dist/RocketForge/BUILD.md                 the human-readable build record

Steps, each of which stops the build when it fails:

    1. preconditions  the repository, master, a clean application tree, a HEAD
                      that origin/master contains, Python 3.13, and exactly the
                      pinned PySide6, NASA CEA and CoolProp -- PySide6 6.11.2
                      hung Thermochemistry and must never ship by accident
    2. identity       rocketforge_build.json, from build_identity.capture(), and
                      a Windows version resource naming the same commit
    3. icons          both .ico files regenerated from packaging/make_brand_icon.py
    4. clean          build/RocketForge and dist/RocketForge removed -- only those
    5. package        PyInstaller, from packaging/RocketForge.spec
    6. verify         packaging/verify_package.py with --smoke. A package that
                      fails loses its manifest, so it can only ever report itself
                      as an unknown build, never as current.
    7. record         BUILD.md: commit, checksum, size, versions, checks
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packaging"))

from rocketforge.application import build_identity  # noqa: E402
import verify_package  # noqa: E402

#: The Python the product is built and tested on (README, CI).
SUPPORTED_PYTHON = (3, 13)

PACKAGE = ROOT / "dist" / "RocketForge"
WORK = ROOT / "build"


def say(message: str) -> None:
    print(f"[rocketforge] {message}", flush=True)


def git(*args: str) -> str:
    done = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else ""


def installed(*names: str) -> str:
    from importlib import metadata
    for name in names:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return ""


def preconditions(production: bool, experimental_pyside6: bool = False) -> list[str]:
    """Every reason this environment and tree may not make this build."""
    problems = []
    if not (ROOT / ".git").exists() or not git("rev-parse", "HEAD"):
        return [f"{ROOT} is not a git checkout; the build must name its commit"]
    facts = build_identity.git_facts(ROOT)
    if production:
        if facts["branch"] != "master":
            problems.append(f"production builds are made from master, not {facts['branch']!r}")
        if facts["dirty"] is not False:
            status = git("status", "--porcelain", "--untracked-files=all", "--",
                         *build_identity.APPLICATION_PATHS)
            problems.append("the application tree differs from the commit:\n    "
                            + status.replace("\n", "\n    "))
        if not git("rev-parse", "--verify", "refs/remotes/origin/master"):
            problems.append("no origin/master to check the commit against")
        elif subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor",
                             "HEAD", "origin/master"]).returncode != 0:
            problems.append("HEAD is not on origin/master: push it first, so the "
                            "package names a commit anyone can check out")
    if sys.version_info[:2] != SUPPORTED_PYTHON:
        problems.append(f"Python {sys.version.split()[0]}; builds use "
                        f"{'.'.join(map(str, SUPPORTED_PYTHON))}")
    for requirements, name, dist_names, required in (
            ("requirements.txt", "PySide6-Essentials",
             ("PySide6-Essentials", "PySide6_Essentials"), True),
            ("requirements-thermochemistry.txt", "cea", ("cea",), production),
            ("requirements-fluids.txt", "CoolProp", ("CoolProp", "coolprop"), production)):
        wanted = verify_package.pinned(ROOT / requirements, name)
        have = installed(*dist_names)
        if not have and not required:
            continue
        if name == "PySide6-Essentials" and experimental_pyside6 and have != wanted:
            say(f"EXPERIMENT: PySide6 {have} instead of the pinned {wanted} "
                "(development build only)")
            continue
        if have != wanted:
            problems.append(f"{name} {have or 'is not installed'}; {requirements} pins "
                            f"{wanted} -- the build refuses any other version")
    shiboken = installed("shiboken6")
    pyside = installed("PySide6-Essentials", "PySide6_Essentials")
    if shiboken != pyside:
        problems.append(f"shiboken6 {shiboken} does not match PySide6 {pyside}")
    if not installed("pyinstaller"):
        problems.append("PyInstaller is not installed (build_exe.bat installs it)")
    return problems


def version_resource(manifest: dict) -> str:
    """The executable's Windows version resource, naming the build's commit."""
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo,
        VarStruct, VSVersionInfo)

    numbers = [int(part) for part in re.findall(r"\d+", manifest["version"])[:3]]
    numbers += [0] * (3 - len(numbers))
    distance = re.match(r".*-(\d+)-g[0-9a-f]+$", manifest["describe"] or "")
    numbers.append(int(distance.group(1)) if distance else 0)
    identity = build_identity.BuildIdentity(
        product=manifest["product"], version=manifest["version"],
        commit=manifest["commit"], describe=manifest["describe"],
        branch=manifest["branch"], channel=manifest["channel"], packaged=True,
        dirty=manifest["dirty"], build_timestamp_utc=manifest["build_timestamp_utc"],
        python=manifest["python"], pyside6=manifest["pyside6"], qt=manifest["qt"],
        cea=manifest["cea"], coolprop=manifest["coolprop"])
    strings = [
        StringStruct("ProductName", manifest["product"]),
        StringStruct("FileDescription", manifest["product"]),
        StringStruct("ProductVersion", f"{manifest['version']} build {identity.build_id}"),
        StringStruct("FileVersion", ".".join(map(str, numbers))),
        StringStruct("InternalName", "RocketForge"),
        StringStruct("OriginalFilename", verify_package.EXE_NAME),
        StringStruct("Comments", f"commit {manifest['commit']}; channel "
                                 f"{manifest['channel']}; built {manifest['build_timestamp_utc']}"),
    ]
    # The project's own licence line, if it has one -- nothing is invented.
    licence = ROOT / "LICENSE"
    if licence.is_file():
        line = next((l.strip() for l in licence.read_text(encoding="utf-8").splitlines()
                     if l.strip().lower().startswith("copyright")), "")
        if line:
            strings.append(StringStruct("LegalCopyright", line))
    info = VSVersionInfo(
        ffi=FixedFileInfo(filevers=tuple(numbers), prodvers=tuple(numbers), mask=0x3F,
                          flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
        kids=[StringFileInfo([StringTable("040904B0", strings)]),
              VarFileInfo([VarStruct("Translation", [0x0409, 1200])])])
    return str(info)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_record(manifest: dict, failures: list[str], smoke: bool) -> Path:
    exe = PACKAGE / verify_package.EXE_NAME
    files = [p for p in PACKAGE.rglob("*") if p.is_file()]
    record = PACKAGE / "BUILD.md"
    record.write_text("\n".join([
        f"# {manifest['product']} build {manifest['commit'][:7]}",
        "",
        "Written by packaging/build_release.py from rocketforge_build.json. "
        "Nothing here is edited by hand.",
        "",
        "| | |",
        "| --- | --- |",
        f"| Product version | {manifest['version']} |",
        f"| Commit | `{manifest['commit']}` |",
        f"| Describe | `{manifest['describe']}` |",
        f"| Branch at build | {manifest['branch']} |",
        f"| Channel | {manifest['channel']} |",
        f"| Dirty | {manifest['dirty']} |",
        f"| Built (UTC) | {manifest['build_timestamp_utc']} |",
        f"| Executable | `dist/RocketForge/{exe.name}` |",
        f"| SHA-256 | `{sha256(exe)}` |",
        f"| Executable size | {exe.stat().st_size} bytes |",
        f"| Package | {len(files)} files, {sum(p.stat().st_size for p in files)} bytes |",
        f"| Python / PySide6 / Qt | {manifest['python']} / {manifest['pyside6']} / {manifest['qt']} |",
        f"| NASA CEA / CoolProp | {manifest['cea'] or '-'} / {manifest['coolprop'] or '-'} |",
        f"| PyInstaller | {manifest['pyinstaller']} |",
        f"| Verification | {'PASS' if not failures else 'FAIL'}"
        f"{' (with package smoke)' if smoke else ' (smoke skipped)'} |",
        "",
    ] + [f"- FAIL {failure}" for failure in failures]) + "\n", encoding="utf-8")
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="The canonical RocketForge build.")
    parser.add_argument("--development", action="store_true",
                        help="package any tree, labelled development, never production")
    parser.add_argument("--skip-smoke", action="store_true",
                        help="skip the in-package smoke checks (development only)")
    parser.add_argument("--experimental-pyside6", action="store_true",
                        help="allow a PySide6 other than the pinned one (development only)")
    args = parser.parse_args(argv)
    production = not args.development
    if (args.skip_smoke or args.experimental_pyside6) and production:
        say("--skip-smoke and --experimental-pyside6 are for development builds only")
        return 2

    problems = preconditions(production, args.experimental_pyside6)
    if problems:
        for problem in problems:
            say(f"PRECONDITION FAILED: {problem}")
        say("no package was built")
        return 1

    import main as application
    channel = build_identity.PRODUCTION if production else build_identity.DEVELOPMENT
    manifest = build_identity.capture(ROOT, product=application.APP_NAME,
                                      version=application.APP_VERSION, channel=channel)
    say(f"building {manifest['product']} {manifest['version']} "
        f"{manifest['commit'][:7]} ({channel}{', dirty' if manifest['dirty'] else ''})")
    say(f"Python {manifest['python']}  PySide6 {manifest['pyside6']}  Qt {manifest['qt']}  "
        f"CEA {manifest['cea'] or '-'}  CoolProp {manifest['coolprop'] or '-'}  "
        f"PyInstaller {manifest['pyinstaller']}")

    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    subprocess.run([sys.executable, str(ROOT / "packaging" / "make_brand_icon.py"),
                    "--icons-only"], cwd=ROOT, env=env, check=True)

    for folder in (WORK / "RocketForge", PACKAGE):
        if folder.exists():
            say(f"removing {folder.relative_to(ROOT)}")
            shutil.rmtree(folder)
    WORK.mkdir(exist_ok=True)
    manifest_path = WORK / build_identity.MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    version_path = WORK / "rocketforge_version_info.txt"
    version_path.write_text(version_resource(manifest), encoding="utf-8")

    say("packaging with PyInstaller")
    log = WORK / "pyinstaller.log"
    with open(log, "w", encoding="utf-8") as handle:
        done = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
             "--distpath", str(ROOT / "dist"), "--workpath", str(WORK),
             str(ROOT / "packaging" / "RocketForge.spec")],
            cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, text=True,
            env=dict(os.environ, ROCKETFORGE_VERSION_INFO=str(version_path),
                     ROCKETFORGE_BUILD_MANIFEST=str(manifest_path)))
    if done.returncode != 0 or not (PACKAGE / verify_package.EXE_NAME).is_file():
        say(f"PyInstaller failed ({done.returncode}); see {log.relative_to(ROOT)}")
        return 1
    shutil.copyfile(manifest_path, PACKAGE / build_identity.MANIFEST_NAME)

    smoke = not args.skip_smoke
    say("verifying the package" + (" and running its smoke checks" if smoke else ""))
    failures = verify_package.verify(PACKAGE, manifest["commit"], ROOT, smoke=smoke,
                                     allow_development=not production)
    record = write_record(manifest, failures, smoke)
    if failures:
        for failure in failures:
            say(f"VERIFY FAILED: {failure}")
        # A package that failed must never read as current: without its
        # manifest it reports itself as an unknown build.
        (PACKAGE / build_identity.MANIFEST_NAME).rename(
            PACKAGE / "rocketforge_build.FAILED.json")
        say(f"build FAILED; the package is marked unknown. Record: {record.relative_to(ROOT)}")
        return 1
    say(f"build PASSED: {(PACKAGE / verify_package.EXE_NAME).relative_to(ROOT)}  "
        f"commit {manifest['commit']}")
    say(f"SHA-256 {sha256(PACKAGE / verify_package.EXE_NAME)}")
    say(f"record: {record.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
