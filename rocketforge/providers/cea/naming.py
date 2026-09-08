"""Translating RocketForge identities into the names CEA understands.

This is the *only* place CEA's naming constraints exist. RocketForge's
canonical identifiers are unconstrained by design (Phase 5B spec §117); one
provider's Fortran field width must not become the domain model's rule.

The limit is 15 characters, established by measurement rather than by reading
it somewhere: names of 16 characters and longer are rejected with
``CEA_INVALID_SIZE`` before any database lookup happens, while names of 15 and
shorter reach the lookup (and fail there only if the species does not exist).
The longest name in RocketForge's curated product set, ``HCHO,formaldehy``, is
exactly 15 and works.
"""

from __future__ import annotations

from rocketforge.physics.thermochemistry import PropellantDefinition

from .errors import CEAMappingError

__all__ = ["PROVIDER_ID", "CEA_MAX_NAME_LENGTH", "cea_name_for", "check_name"]

#: The provider id used in ``provider_names`` mappings and in provenance.
PROVIDER_ID = "cea"

#: Measured, not assumed. See the module docstring.
CEA_MAX_NAME_LENGTH = 15


def check_name(name: str, what: str) -> str:
    """Return ``name`` if CEA can accept it, else raise a mapping error.

    A refusal rather than a truncation. Silently shortening a species name
    would hand CEA a different substance than the one asked for -- and it
    would look like it worked.
    """
    if not isinstance(name, str) or not name.strip():
        raise CEAMappingError(f"{what} has an empty CEA name")
    if len(name) > CEA_MAX_NAME_LENGTH:
        raise CEAMappingError(
            f"{what} maps to the CEA name {name!r}, which is "
            f"{len(name)} characters; NASA CEA accepts at most "
            f"{CEA_MAX_NAME_LENGTH} and rejects longer names with "
            "CEA_INVALID_SIZE. This is a provider limit, not a RocketForge "
            "one: give the propellant a shorter provider_names['cea'] entry.")
    return name


def cea_name_for(propellant: PropellantDefinition) -> str:
    """The CEA reactant name for a RocketForge propellant.

    Requires an explicit ``provider_names["cea"]`` entry. There is deliberately
    **no fallback** to the canonical name or the display label: RocketForge
    calls liquid oxygen ``LOX`` and CEA calls it ``O2(L)``, and a fallback
    would silently substitute gaseous ``O2`` for a propellant whose whole point
    is that it is a cryogenic liquid. Phase 5B-0 measured that substitution as
    74.9 K of chamber temperature, so it must be impossible rather than
    unlikely (5C brief §34).
    """
    mapped = propellant.provider_names.get(PROVIDER_ID)
    if not mapped:
        raise CEAMappingError(
            f"propellant {propellant.name!r} has no NASA CEA name. Add "
            f"provider_names={{'{PROVIDER_ID}': '<CEA identifier>'}} to its "
            "definition. The canonical name is not used as a fallback: it "
            "would silently substitute a different substance or phase.")
    return check_name(mapped, f"propellant {propellant.name!r}")
