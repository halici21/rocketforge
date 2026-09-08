"""Named tolerances for the thermochemistry domain.

Modelled on :mod:`rocketforge.core.tolerances`: one frozen record of named
values, a module-level default, and a docstring that says where each number
came from. A tolerance with no stated justification is a magic number, and this
package has none.

**The categories are deliberately separate** (Phase 5B spec section 164). One
``thermochemistry_tol`` covering everything would force the loosest requirement
onto the strictest check. Five categories, in increasing looseness:

=================================  ========  =====================================
``identity_rel_tol``               1e-12     RocketForge's own arithmetic
``element_balance_rel_tol``        1e-8      conservation between two inventories
``composition_sum_tol``            1e-9      how far a fraction set may miss unity
``state_identity_rel_tol``         1e-9      identities on supplied field values
``provider_identity_rel_tol``      1e-5      identities a provider computed
``provider_element_balance_rel_tol`` 1e-6    conservation in a provider's solution
=================================  ========  =====================================

The last two exist because of measurements, not guesses. NASA CEA uses the
pre-2019 universal gas constant, so its own ``cp - cv`` and ``p = rho R T``
close on *its* R and miss CODATA's by 5.7e-06; and its equilibrium solver's own
element-conservation residual reaches 1.9e-08 across a measured operating
range. Both are facts about CEA rather than defects, and both are absorbed by
named categories rather than by loosening the strict ones.

What is **not** here is a cross-provider *comparison* tolerance: how far CEA and
Cantera may differ from each other depends on which databases are being
compared, so it belongs to whatever does the comparing, measured first and set
afterwards (``13`` section 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = ["ThermochemistryTolerances", "DEFAULT_THERMO_TOLERANCES"]


@dataclass(frozen=True, slots=True)
class ThermochemistryTolerances:
    """Tolerances for composition, conservation and state-identity checks.

    Attributes:
        composition_sum_tol: How far the sum of a fraction set may lie from
            exactly 1 and still be accepted. Chosen as 1e-9: loose enough to
            absorb float accumulation over a few hundred species and input
            written to nine significant figures, tight enough that ``0.99`` or
            ``1.2`` is refused rather than quietly rescaled. A sum inside this
            window is canonicalised to exactly 1 and the correction is recorded
            (``09`` section 5); a sum outside it raises.
        fraction_negative_tol: How negative a fraction may be and still be
            treated as zero. **Zero by default**, meaning no negative value is
            tolerated at all. Phase 5B spec section 36 forbids clamping
            ``-1e-12`` to ``0`` unless a tolerance policy explicitly permits
            it; this field is that policy, and its default permits nothing.
            A future provider adapter that must absorb solver noise sets it
            explicitly, at its own boundary, where the decision is visible.
        element_balance_rel_tol: Relative tolerance for elemental conservation
            between two inventories. 1e-8. Phase 5B-0 measured a real
            equilibrium solve closing to 1.04e-09 on an independent
            atom-by-atom check, so 1e-8 leaves an order of magnitude of margin
            without being so loose that a dropped trace species would pass.
        identity_rel_tol: Relative tolerance for internal algebraic identities
            that should hold to floating-point accuracy -- mole/mass round
            trips, the two mean-molar-mass paths, ``R = Ru/M``. 1e-12. These are
            RocketForge's own arithmetic, so the tolerance is strict; it is not
            relaxed to accommodate any provider.
        state_identity_rel_tol: Relative tolerance for thermodynamic-state
            identities computed from *supplied* field values -- ``gamma = cp/cv``,
            ``cp - cv = R``, ``p = rho R T``. 1e-9, looser than
            ``identity_rel_tol`` because the inputs are measured or
            provider-supplied values that have already been rounded on their way
            in, not quantities this package computed.
        molar_mass_floor: Smallest admissible molar mass, kg/mol. 1e-6
            (1 g/kmol) is below any real species -- atomic hydrogen is about
            1.008e-3 kg/mol -- so this catches a zero or a unit slip without
            constraining legitimate data.
        molar_mass_ceiling: Largest admissible molar mass, kg/mol. 1.0
            (1000 kg/kmol) is far above any species RocketForge will meet and
            catches the common ``kg/kmol`` mistake by three orders of magnitude.
        provider_identity_rel_tol: Relative tolerance for state identities
            checked on values a **provider** computed, where the provider used
            its own physical constants. 1e-5, and the number has a measurement
            behind it: Phase 5B-0 found NASA CEA using the pre-2019 universal
            gas constant, 8314.51 against CODATA's 8314.46261815324, a relative
            difference of **5.7e-06**. CEA's own ``cp - cv`` and ``p = rho R T``
            therefore close on *its* R, not ours, and miss ours by that much.
            1e-5 clears it with margin while still catching a real error.

            This is **not** a relaxation of ``state_identity_rel_tol``, which
            stays strict. It is a different question: "is this state internally
            consistent on RocketForge's constants" versus "is this state
            consistent with the constants its provider used". An adapter passes
            this one; RocketForge's own algebra is held to the strict value.
        provider_element_balance_rel_tol: Relative tolerance for elemental
            conservation on a **provider's** equilibrium solution. 1e-6, and
            like the field above it has a measurement behind it rather than a
            guess.

            ``element_balance_rel_tol`` above is 1e-8, justified in Phase 5B
            from a single Phase 5B-0 sample that closed to 1.04e-09. Phase 5C
            measured the real spread of NASA CEA's own convergence residual
            across **52 converged solves** spanning O/F 1.5 to 7.5 and chamber
            pressures of 1 to 20 MPa: the scale-aware residual reaches
            **1.864e-08** and the per-element residual **5.888e-08**, worst at
            fuel-rich conditions where dissociation is strongest. Those figures
            come from CEA's own molar masses and its own mass fractions, with
            no RocketForge conversion in the path, so they are the solver's
            residual and not an adapter defect.

            1e-6 clears the measured worst case by about 50x -- enough that a
            marginal solve is not mistaken for a defect -- while remaining four
            or more orders of magnitude tighter than any real chemistry error:
            a dropped species, an inverted O/F or a molar-mass unit slip
            produce residuals of order 1e-1 to 1e0.
    """

    composition_sum_tol: float = 1e-9
    fraction_negative_tol: float = 0.0
    element_balance_rel_tol: float = 1e-8
    identity_rel_tol: float = 1e-12
    state_identity_rel_tol: float = 1e-9
    molar_mass_floor: float = 1e-6
    molar_mass_ceiling: float = 1.0
    provider_identity_rel_tol: float = 1e-5
    provider_element_balance_rel_tol: float = 1e-6

    def __post_init__(self) -> None:
        for name in ("composition_sum_tol", "element_balance_rel_tol",
                     "identity_rel_tol", "state_identity_rel_tol",
                     "provider_identity_rel_tol",
                     "provider_element_balance_rel_tol",
                     "molar_mass_floor", "molar_mass_ceiling"):
            value = getattr(self, name)
            if not (value > 0.0) or value != value or value == float("inf"):
                raise ValueError(f"{name} must be a positive finite number, got {value!r}")
        if self.fraction_negative_tol < 0.0 or self.fraction_negative_tol != self.fraction_negative_tol:
            raise ValueError(
                "fraction_negative_tol must be a non-negative finite number, "
                f"got {self.fraction_negative_tol!r}"
            )
        if self.molar_mass_floor >= self.molar_mass_ceiling:
            raise ValueError("molar_mass_floor must be below molar_mass_ceiling")


#: The tolerances every public entry point uses unless a caller supplies its own.
DEFAULT_THERMO_TOLERANCES: Final = ThermochemistryTolerances()
