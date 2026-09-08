"""Mapping NASA CEA's failures onto RocketForge's error vocabulary.

Deliberately small. The rule this module exists to enforce is that three
outcomes are never conflated (``13`` section 9):

* **malformed input** -- refused before CEA is reached, by the request itself;
* **no solution / not converged** -- a ``Solution`` whose status says so;
* **provider failure** -- the machinery is missing or broken.

Nothing here catches bare ``Exception``. A ``KeyError`` or an ``AttributeError``
from this adapter is a programming defect and must stay visible; turning it
into "CEA failed" would hide our own bug behind the provider's name.
"""

from __future__ import annotations

from rocketforge.physics.thermochemistry import (
    ProviderDomainError,
    ProviderError,
    ProviderUnavailableError,
)

__all__ = [
    "CEAProviderError",
    "CEAMappingError",
    "CEASolveError",
    "translate_cea_exception",
]


class CEAProviderError(ProviderError):
    """Base class for failures attributable to the CEA provider."""


class CEAMappingError(CEAProviderError):
    """A RocketForge request could not be expressed in CEA's terms.

    Not a domain error about the request -- the request is well formed --
    but a statement that *this provider* cannot represent it. A propellant
    with no CEA name, or a name longer than CEA's field width, lands here.
    """


class CEASolveError(CEAProviderError):
    """CEA raised while solving a well-formed, mappable problem."""


#: CEA reports failures through ``RuntimeError`` and ``ValueError`` carrying a
#: ``CEA_*`` token in the message. Phase 5B-0 catalogued these by triggering
#: them; each entry names the token and how RocketForge classifies it.
_TOKENS: tuple[tuple[str, str], ...] = (
    ("CEA_INVALID_SIZE", "mapping"),
    ("Species not found in ThermoDB", "mapping"),
    ("not found in thermo database", "mapping"),
    ("CEA_INVALID_EQUILIBRIUM_TYPE", "mapping"),
    ("CEA_INVALID_PROPERTY_TYPE", "mapping"),
    ("CEA_INVALID_FILENAME", "unavailable"),
    ("thermo.lib not found", "unavailable"),
    ("trans.lib not found", "unavailable"),
    ("CEA_FORTRAN_ABORT", "solve"),
    ("CEA_NOT_CONVERGED", "solve"),
)


def translate_cea_exception(exc: BaseException, context: str) -> ProviderError:
    """Classify a CEA exception into RocketForge's provider error branch.

    ``context`` is a short phrase describing what was being attempted, so the
    message says which step failed rather than only that something did.

    An exception whose text matches nothing known is still wrapped -- as a
    :class:`CEASolveError` naming the original type -- because an unrecognised
    provider failure is still a provider failure. What is *not* done is
    swallowing it: the original exception is chained, so the traceback survives.
    """
    text = str(exc)
    for token, kind in _TOKENS:
        if token in text:
            if kind == "mapping":
                return CEAMappingError(
                    f"NASA CEA rejected the {context}: {text.strip()}")
            if kind == "unavailable":
                return ProviderUnavailableError(
                    f"NASA CEA could not find a required resource while "
                    f"{context}: {text.strip()}")
            return CEASolveError(f"NASA CEA failed while {context}: {text.strip()}")
    return CEASolveError(
        f"NASA CEA raised {type(exc).__name__} while {context}: {text.strip()}")


def out_of_range(what: str, value: float, low: float, high: float) -> ProviderDomainError:
    """A refusal that names the range, rather than extrapolating into it."""
    return ProviderDomainError(
        f"{what} is {value!r}, outside NASA CEA's validated range "
        f"[{low}, {high}]. The provider refuses rather than extrapolating.")
