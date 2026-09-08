"""Is the NASA CEA provider usable, and if not, why not.

Asked and answered **without importing CEA at module import time**. RocketForge
must start, and its whole provider-independent domain must work, on a machine
where no chemistry library is installed at all -- which is the base ``.venv``.

The distinction this module exists to preserve: *not installed* and *installed
but broken* are different problems with different fixes, and reporting both as
"unavailable" would send a user looking for a pip command when their real
problem is a missing data file.

That distinction is not hypothetical here. Phase 5B-0 established that
``import cea`` initialises the native library **and loads thermo.lib**, so a
missing or corrupt database surfaces as a ``ValueError`` during import rather
than at first solve. An availability check that only caught ``ImportError``
would misreport it.
"""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from enum import StrEnum
from types import ModuleType

__all__ = [
    "CEAStatus",
    "CEAAvailability",
    "SUPPORTED_CEA_VERSIONS",
    "check_availability",
    "load_cea",
]

#: The CEA versions Phase 5C validated end to end. A version outside this set
#: is reported as ``VERSION_UNSUPPORTED``: it is not rejected outright, because
#: the API may well be compatible, but it is not silently treated as validated
#: either. Raising the pin is a deliberate act with a re-validation run
#: attached (``10`` section 9).
SUPPORTED_CEA_VERSIONS: frozenset[str] = frozenset({"3.3.4"})


class CEAStatus(StrEnum):
    """Why the provider can or cannot be used."""

    AVAILABLE = "available"
    """Imported, initialised, and a validated version."""

    NOT_INSTALLED = "not_installed"
    """The ``cea`` distribution is absent. Fix: install the thermochemistry
    dependency profile."""

    LOAD_FAILED = "load_failed"
    """The package is present but will not import or initialise -- a missing
    ``thermo.lib``, a broken native extension, an ABI mismatch. Fix: repair the
    installation. Distinct from NOT_INSTALLED on purpose."""

    VERSION_UNSUPPORTED = "version_unsupported"
    """Imported and working, but not a version Phase 5C validated. Usable at
    the caller's risk; results carry the actual version in provenance."""


@dataclass(frozen=True, slots=True)
class CEAAvailability:
    """The outcome of an availability check.

    Attributes:
        status: Which of the four cases holds.
        version: The installed ``cea`` version, when it could be determined.
        library_version: The underlying CEA library version, which is a
            separate identifier from the Python distribution's and is not
            assumed to match it.
        detail: A human-readable explanation, always populated for a
            non-available status.
    """

    status: CEAStatus
    version: str = ""
    library_version: str = ""
    detail: str = ""

    @property
    def is_usable(self) -> bool:
        """Whether a solve may be attempted.

        ``VERSION_UNSUPPORTED`` counts as usable: the version is recorded in
        provenance, so a result produced by it is never mistaken for a
        validated one.
        """
        return self.status in (CEAStatus.AVAILABLE, CEAStatus.VERSION_UNSUPPORTED)

    @property
    def is_validated(self) -> bool:
        """Whether this is a version Phase 5C actually validated."""
        return self.status is CEAStatus.AVAILABLE


def _installed() -> bool:
    """Whether the distribution exists, without importing it.

    ``find_spec`` does not execute the module, so this stays cheap and cannot
    trip the native initialisation that a real import performs.
    """
    try:
        return importlib.util.find_spec("cea") is not None
    except (ImportError, ValueError):
        # find_spec itself raises for a package whose parent is broken.
        return False


def check_availability() -> CEAAvailability:
    """Determine whether the CEA provider can be used, and report why not.

    Imports CEA only when the distribution is present. Never raises: the whole
    point is to answer the question safely.
    """
    if not _installed():
        return CEAAvailability(
            status=CEAStatus.NOT_INSTALLED,
            detail="the 'cea' distribution is not installed. Install the "
                   "thermochemistry profile: python -m pip install -r "
                   "requirements-thermochemistry.txt")

    try:
        module = importlib.import_module("cea")
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see below
        # Broad on purpose, and only here. Importing CEA initialises a native
        # library and loads thermo.lib, so the failure modes are open-ended:
        # ImportError for a missing DLL, ValueError for a missing database,
        # OSError for an ABI mismatch. The exception type is preserved in the
        # detail rather than discarded.
        return CEAAvailability(
            status=CEAStatus.LOAD_FAILED,
            detail=f"'cea' is installed but failed to load: "
                   f"{type(exc).__name__}: {exc}")

    version = str(getattr(module, "__version__", "") or "")
    try:
        library_version = str(module.lib_version())
    except Exception as exc:  # noqa: BLE001
        return CEAAvailability(
            status=CEAStatus.LOAD_FAILED, version=version,
            detail=f"'cea' imported but its native library is not responding: "
                   f"{type(exc).__name__}: {exc}")

    try:
        initialised = bool(module.is_initialized())
    except Exception:  # noqa: BLE001
        initialised = False
    if not initialised:
        return CEAAvailability(
            status=CEAStatus.LOAD_FAILED, version=version,
            library_version=library_version,
            detail="'cea' imported but reports that its native library is not "
                   "initialised; the thermodynamic database may be missing")

    if version not in SUPPORTED_CEA_VERSIONS:
        return CEAAvailability(
            status=CEAStatus.VERSION_UNSUPPORTED, version=version,
            library_version=library_version,
            detail=f"cea {version} is installed; Phase 5C validated "
                   f"{sorted(SUPPORTED_CEA_VERSIONS)}. It may work, but its "
                   "results are not covered by RocketForge's validation.")

    return CEAAvailability(status=CEAStatus.AVAILABLE, version=version,
                           library_version=library_version,
                           detail="")


def load_cea() -> ModuleType:
    """Import and return the ``cea`` module, or raise a provider error.

    The single place this adapter imports CEA. Everything else takes the module
    as an argument, which is what keeps the rest of the package importable and
    unit-testable with no provider installed.
    """
    from .errors import CEAProviderError  # local: keeps import order simple
    from rocketforge.physics.thermochemistry import ProviderUnavailableError

    availability = check_availability()
    if not availability.is_usable:
        raise ProviderUnavailableError(
            f"NASA CEA is not usable ({availability.status.value}): "
            f"{availability.detail}")
    try:
        return importlib.import_module("cea")
    except Exception as exc:  # noqa: BLE001
        raise ProviderUnavailableError(
            f"NASA CEA became unimportable after reporting "
            f"{availability.status.value}: {type(exc).__name__}: {exc}") from exc
