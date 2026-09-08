"""Provider availability, in both worlds.

The tests that must pass whether or not CEA is installed. Their job is to prove
that RocketForge is honest about what it has: "not installed" and "installed
but broken" are different problems with different fixes, and reporting both as
"unavailable" would send someone looking for a pip command when their real
problem is a missing data file.
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys

import pytest

from rocketforge.providers.cea import (
    SUPPORTED_CEA_VERSIONS,
    CEAAvailability,
    CEAStatus,
    CEAThermochemistryProvider,
    check_availability,
)

#: Computed per module rather than imported from conftest: the tests tree has
#: no ``__init__.py``, so a relative import across test modules is not
#: available. The check is cheap and does not import the chemistry library
#: when it is absent.
_AVAILABILITY = check_availability()
CEA_PRESENT = _AVAILABILITY.is_usable

requires_cea = pytest.mark.skipif(
    not CEA_PRESENT,
    reason=(f"NASA CEA provider unavailable ({_AVAILABILITY.status.value}): "
            f"{_AVAILABILITY.detail or 'install requirements-thermochemistry.txt'}"),
)


def test_checking_availability_never_raises():
    """The whole point is to answer the question safely."""
    result = check_availability()
    assert isinstance(result, CEAAvailability)
    assert isinstance(result.status, CEAStatus)


def test_a_non_available_status_always_explains_itself():
    result = check_availability()
    if result.status is not CEAStatus.AVAILABLE:
        assert result.detail, "an unavailable provider must say why"


def test_availability_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        check_availability().status = CEAStatus.AVAILABLE  # type: ignore[misc]


def test_the_provider_can_be_constructed_without_cea():
    """Construction must not import the chemistry library.

    An application that lists providers, or shows which are installed, must be
    able to do so on a machine with nothing installed.
    """
    provider = CEAThermochemistryProvider()
    assert provider.provider_id == "cea"
    assert provider.capabilities.supported


def test_importing_the_provider_package_does_not_import_cea():
    """Checked in a subprocess, so nothing else in the suite can mask it.

    The claim is about the **package import** only. ``check_availability`` does
    import CEA when the distribution is present, and must: it verifies the
    version and that the native library initialised, and neither can be known
    without importing. What matters for startup is that merely importing the
    adapter -- which provider discovery does -- costs nothing.
    """
    script = """
import sys
import rocketforge.providers.cea as pkg
assert "cea" not in sys.modules, "importing the adapter imported the library"
assert pkg.CEAThermochemistryProvider().provider_id == "cea"
assert "cea" not in sys.modules, "constructing the provider imported the library"
print("LAZY_OK")
"""
    result = subprocess.run([sys.executable, "-c", script],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "LAZY_OK" in result.stdout


@requires_cea
def test_checking_availability_does_import_cea_when_present():
    """Stated explicitly rather than left as a surprise.

    The version and the initialisation state are properties of the imported
    module, so answering "is this usable and is it the validated version"
    requires the import. The cost is paid on the first availability check, not
    on application startup.
    """
    import sys as _sys

    check_availability()
    assert "cea" in _sys.modules


def test_the_four_statuses_are_distinct():
    """Absent, broken, unvalidated and available are four answers, not two."""
    assert len({s.value for s in CEAStatus}) == 4
    assert CEAStatus.NOT_INSTALLED is not CEAStatus.LOAD_FAILED


def test_unvalidated_version_is_still_usable_but_flagged():
    """A version we did not validate is not refused; it is labelled."""
    unvalidated = CEAAvailability(status=CEAStatus.VERSION_UNSUPPORTED,
                                  version="9.9.9", detail="synthetic")
    assert unvalidated.is_usable
    assert not unvalidated.is_validated
    broken = CEAAvailability(status=CEAStatus.LOAD_FAILED, detail="synthetic")
    assert not broken.is_usable


def test_validated_version_set_matches_the_pinned_dependency():
    """The pin in requirements-thermochemistry.txt and the code agree."""
    import pathlib
    profile = (pathlib.Path(__file__).resolve().parents[3]
               / "requirements-thermochemistry.txt").read_text(encoding="utf-8")
    for version in SUPPORTED_CEA_VERSIONS:
        assert f"cea=={version}" in profile


@pytest.mark.skipif(CEA_PRESENT, reason="this test describes the CEA-absent world")
def test_absent_provider_reports_not_installed_and_refuses_clearly():
    result = check_availability()
    assert result.status is CEAStatus.NOT_INSTALLED
    assert "requirements-thermochemistry" in result.detail
    provider = CEAThermochemistryProvider()
    assert not provider.is_available
    from rocketforge.physics.thermochemistry import ProviderUnavailableError
    with pytest.raises(ProviderUnavailableError, match="not usable"):
        provider.resources()


@requires_cea
def test_present_provider_reports_a_validated_version():
    result = check_availability()
    assert result.status is CEAStatus.AVAILABLE
    assert result.version in SUPPORTED_CEA_VERSIONS
    assert result.library_version


@requires_cea
def test_library_version_is_recorded_separately_from_the_distribution():
    """They are separate identifiers and are not assumed to match."""
    result = check_availability()
    assert result.version
    assert result.library_version


def test_a_broken_installation_is_not_reported_as_missing(monkeypatch):
    """Simulated: metadata present, import fails.

    This is the case Phase 5B-0 made non-hypothetical -- CEA loads its database
    at import, so a missing data file raises ValueError during import, not
    ImportError. An availability check that only caught ImportError would
    misreport it as "not installed" and send the user to pip.
    """
    import importlib

    import rocketforge.providers.cea.availability as availability

    monkeypatch.setattr(availability, "_installed", lambda: True)

    def explode(name):
        raise ValueError("thermo.lib not found. Searched: ...")

    monkeypatch.setattr(importlib, "import_module", explode)
    result = availability.check_availability()
    assert result.status is CEAStatus.LOAD_FAILED
    assert result.status is not CEAStatus.NOT_INSTALLED
    assert "thermo.lib" in result.detail
    assert "ValueError" in result.detail


def test_an_uninitialised_native_library_is_a_load_failure(monkeypatch):
    """Imported, but the native side is not up."""
    import importlib
    import types

    import rocketforge.providers.cea.availability as availability

    fake = types.SimpleNamespace(
        __version__="3.3.4",
        lib_version=lambda: "3.3.4",
        is_initialized=lambda: False,
    )
    monkeypatch.setattr(availability, "_installed", lambda: True)
    monkeypatch.setattr(importlib, "import_module", lambda name: fake)
    result = availability.check_availability()
    assert result.status is CEAStatus.LOAD_FAILED
    assert "not initialised" in result.detail
