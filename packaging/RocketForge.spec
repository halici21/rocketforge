# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build description for RocketForge.

Why PyInstaller and not pyside6-deploy: the official tool wraps Nuitka, which
needs a working C toolchain on the build machine. There is none here, and
having the build silently download a compiler is a worse deal than a packager
that already understands PySide6. PyInstaller ships a PySide6 hook that
collects the Qt runtime, the platform plugins and Qt's own QML modules, which
is the part that is genuinely hard to get right by hand.

Why a directory and not one file: a --onefile build unpacks the whole Qt
runtime to a temporary folder on every launch. For a Qt Quick application that
is a slow start and a fragile one - QML resolves imports against real paths,
and the temporary directory is a moving target. The directory build starts
immediately and is what gets shipped.

The interface itself is plain .qml read from disk at run time, so ui/ is
carried as data and main.py finds it through sys._MEIPASS. Nothing is compiled
into a resource bundle: the QML stays inspectable in the shipped build, which
is what the UI phase wants.

The engineering backend is a normal Python package that main.py imports, so
PyInstaller follows it without help. Its *data* files do need declaring: the
published reference table is read at run time and would otherwise be missing
from the bundle, leaving the comparison feature dead in the shipped build.

The NASA CEA thermochemistry provider is collected when it is present in the
build environment. PyInstaller does not follow it on its own: it is imported
lazily -- deliberately, so that RocketForge starts on a machine without it --
and its native extension, its bindings DLL and its thermodynamic database are
data and binaries rather than importable modules. Phase 5B-0 established that
``--collect-data`` plus ``--collect-binaries`` is what the package needs, and
Phase 5C proved a frozen build then solves a real chamber equilibrium from the
bundled ``thermo.lib``.

Collection is conditional. A build environment without CEA still produces a
working executable, one without thermochemistry; the official desktop build is
made from an environment that has the provider installed, so the shipped
product carries it and an end user never runs pip.
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(SPECPATH))
UI_DIR = os.path.join(ROOT, "ui")
REFERENCE_DIR = os.path.join(ROOT, "rocketforge", "data", "reference")
ICON = os.path.join(SPECPATH, "RocketForge.ico")

if not os.path.isdir(UI_DIR):
    raise SystemExit("ui/ not found next to the spec at %s" % ROOT)
if not os.path.isdir(REFERENCE_DIR):
    raise SystemExit("reference data not found at %s" % REFERENCE_DIR)

# ---------------------------------------------------------------------------
# Build identity. Every package names the commit it was built from: the
# canonical build (build_exe.bat -> packaging/build_release.py) writes the
# manifest and the Windows version resource and passes them in. Run on its own,
# this spec would produce a package nobody could identify, so it refuses.
# docs/engineering/release/BUILD_AND_LAUNCH.md.
# ---------------------------------------------------------------------------
VERSION_INFO = os.environ.get("ROCKETFORGE_VERSION_INFO", "")
BUILD_MANIFEST = os.environ.get("ROCKETFORGE_BUILD_MANIFEST", "")
if not (os.path.isfile(VERSION_INFO) and os.path.isfile(BUILD_MANIFEST)):
    raise SystemExit("packaging/RocketForge.spec is built through build_exe.bat, which "
                     "records the build's identity; it will not package an "
                     "unidentified build")
if not os.path.isfile(ICON):
    raise SystemExit("packaging/RocketForge.ico is missing: build_exe.bat regenerates "
                     "it with packaging/make_brand_icon.py --icons-only")


# ---------------------------------------------------------------------------
# NASA CEA thermochemistry provider, collected only when it is installed.
# ---------------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

cea_datas = []
cea_binaries = []
cea_hiddenimports = []
try:
    import cea as _cea

    cea_version = getattr(_cea, "__version__", "unknown")
    # Data first: thermo.lib and trans.lib live under cea/data/ and are found
    # by the provider relative to the imported module, which is why they must
    # land in the same place inside the bundle.
    cea_datas = collect_data_files("cea")
    # Then the native side: the Cython extension and the bindings DLL.
    cea_binaries = collect_dynamic_libs("cea")
    # The extension is imported through cea.lib.libcea, which PyInstaller's
    # static analysis does not see because the package imports it dynamically.
    cea_hiddenimports = ["cea.lib", "cea.lib.libcea", "cea.constants", "cea.units"]
    print("[rocketforge] bundling NASA CEA %s: %d data files, %d binaries"
          % (cea_version, len(cea_datas), len(cea_binaries)))
except ImportError:
    print("[rocketforge] NASA CEA not installed in this environment; building "
          "without the thermochemistry provider. Install "
          "requirements-thermochemistry.txt for the official desktop build.")


# ---------------------------------------------------------------------------
# CoolProp fluid-property provider, collected only when it is installed.
#
# The same conditional shape as the CEA block above, and for the same reason: a
# build environment without the optional profile must still produce a working
# executable, one that reports the provider as unavailable rather than failing
# to start. The official desktop build has both profiles installed, because the
# reactant-enthalpy coupling needs both at once.
# ---------------------------------------------------------------------------
coolprop_datas = []
coolprop_binaries = []
coolprop_hiddenimports = []
try:
    import CoolProp as _coolprop

    coolprop_version = getattr(_coolprop, "__version__", "unknown")
    # CoolProp's fluid JSON is compiled into the extension rather than shipped
    # as loose data, so collect_data_files finds little; collect it anyway
    # rather than assume, because assuming is how a bundle loses a data file.
    coolprop_datas = collect_data_files("CoolProp")
    coolprop_binaries = collect_dynamic_libs("CoolProp")
    # CoolProp.CoolProp is the SI interface the adapter imports, and it is
    # reached through a lazy function-local import that static analysis cannot
    # see -- which is the whole point of the lazy import, so it is declared.
    coolprop_hiddenimports = ["CoolProp", "CoolProp.CoolProp",
                              "CoolProp.constants"]
    print("[rocketforge] bundling CoolProp %s: %d data files, %d binaries"
          % (coolprop_version, len(coolprop_datas), len(coolprop_binaries)))
except ImportError:
    print("[rocketforge] CoolProp not installed in this environment; building "
          "without the fluid-property provider. Install "
          "requirements-fluids.txt for the official desktop build.")


a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=cea_binaries + coolprop_binaries,
    datas=[
        # The whole interface, kept as readable QML inside the bundle.
        (UI_DIR, "ui"),
        # The product mark. main.py resolves it through resource_root() for
        # QGuiApplication.setWindowIcon, so the frozen window, Alt-Tab entry
        # and taskbar button carry the same icon the executable does.
        (os.path.join(ROOT, "assets", "branding"),
         os.path.join("assets", "branding")),
        # Published reference tables. Read at run time by the analysis pages;
        # the path is resolved relative to the package, so it must land in the
        # same place inside the bundle as it sits in the source tree.
        (REFERENCE_DIR, os.path.join("rocketforge", "data", "reference")),
    ] + cea_datas + coolprop_datas,
    hiddenimports=cea_hiddenimports + coolprop_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Deliberately short.
    #
    # An earlier version of this file pruned Qt modules the interface does not
    # import - QtNetwork among them - and the build died on launch with
    # "could not import module PySide6.QtNetwork": QtQml links against it, so
    # it is a dependency whether or not any Python here imports it. Guessing at
    # a Qt module graph from the outside is how packaging becomes fragile, and
    # PySide6-Essentials is already the trimmed distribution. Only non-Qt
    # standard-library baggage is dropped.
    excludes=[
        "tkinter",
        "unittest",
        "pydoc_data",
        "pdb",
        "doctest",
        # CoolProp ships its own test suite as a subpackage; collecting it pulled
        # pytest (and with it setuptools) into the product. Nothing at run time
        # imports either -- verify_package.py's smoke and science checks confirm.
        "CoolProp.tests",
        "pytest",
        "_pytest",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RocketForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # A desktop application, so no console window behind it. Diagnostics still
    # reach a terminal when the executable is started from one.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
    # ProductVersion and Comments name the commit, so even a copied .exe says
    # which build it is (Properties > Details in Explorer).
    version=VERSION_INFO,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="RocketForge",
)
