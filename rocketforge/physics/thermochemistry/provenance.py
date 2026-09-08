"""Provider provenance: who computed a state, how, and against what data.

Distinct from :mod:`rocketforge.core.provenance`, which records the *equation*
behind a relation. This module records the *provider* behind a number: which
library, which version, which thermodynamic database, which chemistry mode.

Both are needed and neither substitutes for the other. An equation reference
says "this is the area-Mach relation"; a provider provenance says "this came
from NASA CEA 3.3.4 against thermo.lib with sha256 8e5df1cc..., solved at
constant enthalpy and pressure, with the oxidiser at 90.17 K".

Provenance is what makes a chemistry result reproducible. Phase 5B-0 confirmed
that both candidate providers expose enough to fill this record: version
strings, and on-disk databases that can be hashed without modifying them.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .errors import ThermochemistryError
from .types import ChemistryMode, EquilibriumConstraint, ExpansionMode

__all__ = ["ThermochemistryProvenance"]


@dataclass(frozen=True, slots=True)
class ThermochemistryProvenance:
    """Where a thermochemical state came from.

    Attributes:
        provider_id: Stable machine identifier for the provider, e.g.
            ``"cea"``, ``"cantera"``, ``"tabulated:LOX-CH4-v1"``, ``"stub:test"``.
            A test stub's id must be recognisably a stub, because a stub value
            escaping into an acceptance artifact would be a fabricated number.
        provider_version: The adapter's own version.
        library_version: The underlying library's version, when there is one --
            ``cea.__version__``, ``cantera.__version__``.
        database: Name of the thermodynamic data set, e.g. ``"thermo.lib"``.
        database_version: Version or, preferably, a content hash.
        database_sha256: Hex digest of the database file, when the adapter
            computed one. Phase 5B-0 demonstrated this is practical for both
            candidates without modifying provider files. Computed by the
            adapter, never by this package.
        chemistry_mode: How chemistry was treated for the chamber.
        equilibrium_constraint: Which pair of properties was held fixed.
        expansion_mode: How chemistry was treated during expansion, when the
            state came from one.
        species_set: The species actually considered, for reproducibility. A
            result from a 9-species set and one from a 50-species set are not
            the same calculation.
        reactant_conditions: Temperatures and any other reactant state the
            provider was given, keyed by a descriptive name, in SI.
        options: Provider-specific settings actually used, as strings. A
            free-form escape hatch **for provenance only**; nothing reads it to
            decide behaviour.
        warnings: Anything the provider reported that a reader should know.

    Deliberately absent: a timestamp. Two identical calculations should produce
    equal provenance so that results remain comparable and reproducible, and a
    wall-clock field would make every record unique (Phase 5B spec section 109).
    """

    provider_id: str
    provider_version: str = ""
    library_version: str = ""
    database: str = ""
    database_version: str = ""
    database_sha256: str = ""
    chemistry_mode: ChemistryMode | None = None
    equilibrium_constraint: EquilibriumConstraint | None = None
    expansion_mode: ExpansionMode | None = None
    species_set: tuple[str, ...] = ()
    reactant_conditions: Mapping[str, float] = field(default_factory=dict)
    options: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ThermochemistryError(
                "provenance must name a provider id; a state that cannot say where "
                "it came from is not reproducible")
        for name in ("provider_version", "library_version", "database",
                     "database_version", "database_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise ThermochemistryError(f"{name} must be a string, got {value!r}")
        if self.database_sha256:
            digest = self.database_sha256.strip().lower()
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ThermochemistryError(
                    f"database_sha256 must be 64 hex characters, got "
                    f"{self.database_sha256!r}")
        if self.chemistry_mode is not None and not isinstance(
                self.chemistry_mode, ChemistryMode):
            raise ThermochemistryError(
                f"chemistry_mode must be a ChemistryMode member or None, "
                f"got {self.chemistry_mode!r}")
        if self.equilibrium_constraint is not None and not isinstance(
                self.equilibrium_constraint, EquilibriumConstraint):
            raise ThermochemistryError(
                f"equilibrium_constraint must be an EquilibriumConstraint member "
                f"or None, got {self.equilibrium_constraint!r}")
        if self.expansion_mode is not None and not isinstance(
                self.expansion_mode, ExpansionMode):
            raise ThermochemistryError(
                f"expansion_mode must be an ExpansionMode member or None, "
                f"got {self.expansion_mode!r}")
        if not isinstance(self.species_set, tuple):
            raise ThermochemistryError("species_set must be a tuple of names")
        for name in self.species_set:
            if not isinstance(name, str) or not name:
                raise ThermochemistryError(
                    f"species_set entries must be non-empty strings, got {name!r}")
        if not isinstance(self.reactant_conditions, Mapping):
            raise ThermochemistryError("reactant_conditions must be a mapping")
        for key, value in self.reactant_conditions.items():
            if not isinstance(key, str) or not key:
                raise ThermochemistryError(
                    f"reactant condition key must be a non-empty string, got {key!r}")
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise ThermochemistryError(
                    f"reactant condition {key!r} must be a real number, "
                    f"got {value!r}") from exc
            if not math.isfinite(number):
                raise ThermochemistryError(
                    f"reactant condition {key!r} must be finite, got {number!r}")
        if not isinstance(self.options, Mapping):
            raise ThermochemistryError("options must be a mapping of strings")
        for key, value in self.options.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ThermochemistryError(
                    f"options must map strings to strings, got {key!r}: {value!r}")
        if not isinstance(self.warnings, tuple):
            raise ThermochemistryError("warnings must be a tuple of strings")

    @property
    def conditions(self) -> Mapping[str, float]:
        """Read-only view of the recorded reactant conditions."""
        return MappingProxyType(dict(self.reactant_conditions))

    @property
    def is_reproducible(self) -> bool:
        """Whether this record identifies its provider *and* its data.

        A result whose provenance names a provider but not the thermodynamic
        data behind it cannot be reproduced later, because the data can change
        under a version bump. This property is what a completeness check reads;
        it does not make the state invalid, it makes the state's reproducibility
        claim honest (``10`` section 9).
        """
        return bool(
            self.provider_id.strip()
            and (self.library_version.strip() or self.provider_version.strip())
            and (self.database_sha256.strip() or self.database_version.strip())
        )

    @property
    def is_stub(self) -> bool:
        """Whether this provenance came from a test stub rather than a solver."""
        return self.provider_id.startswith("stub:")
