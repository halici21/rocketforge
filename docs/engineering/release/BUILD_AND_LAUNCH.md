# RocketForge — build identity, building and launching

One question must always have one answer: **which RocketForge is running?**
This page defines the terms, the one build command, the one package location,
and how each way of starting RocketForge identifies itself.

## Terms

| Term | Meaning |
| --- | --- |
| **Source of truth** | The tracked source on `master`, named by its **full commit SHA**. A branch name is not an identity: `master` moves. |
| **Development run** | RocketForge started from the source tree (`run.bat`). Always *development*, whatever the tree. Build ID `<commit>-dev`, plus `-dirty` when the application's files differ from the commit. |
| **Canonical packaged build** | `dist\RocketForge\RocketForge.exe`, made by `build_exe.bat` from a clean `master` commit that `origin/master` contains, and verified. Channel *production*; build ID is the short commit. |
| **Stale build** | A package whose commit is not the current `master` HEAD. `packaging\verify_package.py` says so by name. |
| **Unknown build** | A package whose identity cannot be read — no manifest, an unreadable one, or one the build marked as failed. It reports `[UNKNOWN BUILD]` and is never presented as current. Every package made before this scheme existed is unknown. |

"Latest", "new" or "final" are not identities. Name a build by its commit.

## Where the identity lives

| Carrier | What it says | Read by |
| --- | --- | --- |
| `dist\RocketForge\rocketforge_build.json` | commit, describe (`v0.1.0-25-g7cb6cd4`), branch, channel, dirty, build time, Python/PySide6/Qt, NASA CEA, CoolProp, PyInstaller | the application at start-up, the verifier |
| `RocketForge.exe` version resource | ProductVersion `0.1.0 build 7cb6cd4`; Comments `commit <full SHA>; channel production; built …` | Explorer → Properties → Details; the verifier. It survives a copied `.exe`. |
| `dist\RocketForge\BUILD.md` | the build record: commit, SHA-256 and size of the executable, versions, verification result | people |
| Settings (gear, top right) | `RocketForge 0.1.0`, `Build 7cb6cd4 · production · packaged`, Qt/PySide6/Python, and **Copy build info** | users |
| Window title | `RocketForge` for a production package; `RocketForge [DEV 7cb6cd4]` (or `[DEV 7cb6cd4-dirty]`) for a source run; `[UNKNOWN BUILD]` for an unidentified package | everyone |

One implementation: `rocketforge/application/build_identity.py`. The build
writes the manifest with `capture()`, the application reads it with
`identity_for_process()`, and the verifier checks it with `read_manifest()`.
**A package never looks for git or a repository**: it reads its manifest and
nothing else. Git is used only by a source run and by the build.

**Asking a user which build they ran:** Settings → **Copy build info**, and
paste it into the report. A screenshot of the Settings menu is enough: it
shows source run or packaged, the commit, the channel, and the Qt and PySide6
versions.

The product version (`main.APP_VERSION`, `0.1.0`) is the last release. The
commit is the build's identity; `describe` says how far past the release it
is (`v0.1.0-25-g…` = 25 commits after v0.1.0). `rocketforge.__version__` is
the engineering backend's own version and is independent of both.

## Launching

| Launch | Target | Meaning |
| --- | --- | --- |
| `run.bat` | `main.py` from this tree, with `.venv-cea` (else `.venv`) | Development run. It never starts a package, and it never uses a `python` from `PATH`. |
| `dist\RocketForge\RocketForge.exe` | the canonical package | Packaged run. Needs no Python. |
| Desktop shortcut **RocketForge** | `dist\RocketForge\RocketForge.exe`, working directory `dist\RocketForge` | Packaged run. There is one such shortcut. |

To create or repair the desktop shortcut after a verified build:

```powershell
$exe = Resolve-Path dist\RocketForge\RocketForge.exe
$lnk = (New-Object -ComObject WScript.Shell).CreateShortcut(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) 'RocketForge.lnk'))
$lnk.TargetPath = $exe; $lnk.WorkingDirectory = Split-Path $exe
$lnk.IconLocation = "$exe,0"; $lnk.Save()
```

## Building

```bat
build_exe.bat
```

The only build command. It runs `packaging\build_release.py` with
`.venv-cea` (requirements.txt, requirements-thermochemistry.txt and
requirements-fluids.txt installed; it installs PyInstaller if missing).

1. **Preconditions**, all of them, or no package:
   - a git checkout on `master`;
   - an application tree that does not differ from the commit. Application
     paths are `main.py`, `rocketforge/`, `ui/`, `assets/`, `packaging/`,
     `build_exe.bat` and the requirement files. Tests and docs do not count.
   - a HEAD that `origin/master` contains, so the package names a commit
     anyone can check out;
   - Python 3.13;
   - **exactly** the pinned PySide6-Essentials (and a matching shiboken6),
     NASA CEA and CoolProp. PySide6 6.11.2 hung Thermochemistry; no build
     ships an unpinned PySide6 by accident.
2. **Identity**: `build\rocketforge_build.json` and the Windows version
   resource, from `build_identity.capture()`.
3. **Icons**: both `.ico` files regenerated from
   `packaging\make_brand_icon.py --icons-only`. They are generated, not
   tracked, and the generation is byte-for-byte deterministic.
4. **Clean**: `build\RocketForge` and `dist\RocketForge` are removed, and
   nothing else.
5. **Package**: PyInstaller, from `packaging\RocketForge.spec`. The spec
   refuses to run without the identity files, so no unidentified package can
   be made from it.
6. **Verify**: `packaging\verify_package.py` with its smoke checks. A package
   that fails loses its manifest (it is renamed
   `rocketforge_build.FAILED.json`), so it can only report itself as an
   unknown build.
7. **Record**: `dist\RocketForge\BUILD.md`.

`build_exe.bat --development` packages any tree and labels it *development*
(and *dirty* where it is). It never produces a production build. For a
development experiment only, `--experimental-pyside6` lifts the PySide6 pin
gate, and `--skip-smoke` skips the package smoke checks.

Two builds of the same commit have the same identity and the same location.
The executable's bytes differ, because the version resource records the
build time: compare builds by commit, not by checksum.

### What the package contains

It contains the Python runtime, Qt and its QML modules, `ui/`, the brand
icon, the reference data, NASA CEA with `thermo.lib` and `trans.lib`,
CoolProp, and `rocketforge_build.json`.

It does not contain tests or pytest (CoolProp's own test suite is excluded),
setuptools, SciPy, `acceptance/`, `.git`, Graphify output, or any path from the
build machine. These lists were audited on the first canonical build, by
reading the package's contents and PyInstaller's module table, and searching
every file for build-machine paths. Repeat that audit whenever the spec
changes.

## Verifying a package

```bat
.venv-cea\Scripts\python.exe packaging\verify_package.py --smoke
```

This checks `dist\RocketForge` against the repository's HEAD:

- **layout**: one `RocketForge.exe`, and no other RocketForge build in `dist\`;
- **manifest**: production, clean, and exactly that commit, else *stale*;
- **pins**: PySide6, CEA and CoolProp are the pinned versions;
- **version resource**: the executable names the same commit;
- **runtime**: the executable, asked with `--build-info`, reports itself as
  that packaged build;
- **smoke**: the bundled provider, the Nozzle Lab → Thermochemistry route that
  once crashed, and the science self-test, all run inside the package.

`--expect-commit <sha>` checks against another commit.

## Diagnostic flags

Every flag works in `python main.py` and in `RocketForge.exe`. None opens a
window that outlives it.

| Flag | Writes |
| --- | --- |
| `--build-info <out.json>` | this process's build identity |
| `--selftest-navigation <out.json> <route>` | drives the shell through a route (syntax in `rocketforge/application/navsmoke.py`) under a real event loop; records warnings and optional captures |
| `--selftest-science <out.json>` | a bit-exact digest of representative cases in every workspace. Source and package digests of one commit must be identical. |
| `--selftest-thermochemistry` | the bundled provider solves a chamber |
| `--selftest-thermochemistry-ui`, `--selftest-rocket-performance`, `--selftest-workspaces`, … | the existing workspace tours |
