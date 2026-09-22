"""Reference solid formulations, spelled the way NASA CEA spells them.

These live in the provider package for the same reason ``propellants.py``'s
``LOX`` and ``LIQUID_METHANE`` do: the names are CEA's. ``NH4CLO4(I)`` and
``AL(cr)`` are library identifiers, phase suffix included, not generic
chemistry. A different provider would need a different spelling of the same
grain, which is exactly what keeps this out of the physics package.

What is here is a **validation case**, not a product preset dressed up as one.
It reproduces NASA RP-1311 Example 5 exactly as published -- including the
binder, which is represented as the custom ``CHOS-Binder`` reactant the source
document defines rather than being relabelled HTPB, PBAN or any other real
binder it superficially resembles. A reader comparing RocketForge's output
against the published table sees the same identifiers on both sides.
"""

from __future__ import annotations

from rocketforge.physics.solid_propellant import (
    CustomReactant,
    SolidFormulation,
    SolidIngredient,
)

__all__ = [
    "RP1311_EXAMPLE5_BINDER",
    "RP1311_EXAMPLE5",
    "RP1311_EXAMPLE5_OMIT",
    "RP1311_EXAMPLE5_PRESSURES_BAR",
]

#: The assigned-enthalpy binder from RP-1311 Example 5, verbatim.
#:
#: Not a library species: no polymer binder is. The formula is an average over
#: the polymer, which is why the hydrogen count is fractional, and the enthalpy
#: is assigned at 298.15 K in cal/mol because that is how the source states it.
RP1311_EXAMPLE5_BINDER = CustomReactant(
    formula={"C": 1.0, "H": 1.86955, "O": 0.031256, "S": 0.008415},
    heat_of_formation=-2999.082,
    heat_of_formation_units="cal/mol",
    reference_temperature=298.15,
    # Stated by the source, and needed: CEA's own derivation from the formula
    # shifts the mass-basis enthalpy by 2.0e-05 relative.
    molecular_weight=14.6652984484,
    source=("NASA RP-1311 Example 5 input, as shipped with cea 3.3.4 in "
            "cea/samples/rp1311/example5.py (chos_binder_h_cal_per_mol)"),
)

#: The grain, by mass. The five published fractions sum to exactly 1.0.
RP1311_EXAMPLE5 = SolidFormulation(
    name="RP-1311 Example 5",
    ingredients=(
        SolidIngredient("NH4CLO4(I)", 0.7206),
        SolidIngredient("CHOS-Binder", 0.1858, custom=RP1311_EXAMPLE5_BINDER),
        SolidIngredient("AL(cr)", 0.09),
        SolidIngredient("MgO(cr)", 0.002),
        SolidIngredient("H2O(L)", 0.0016),
    ),
    initial_temperature=298.15,
    reference="NASA RP-1311 Example 5",
)

#: The pressures the published table reports, in bar.
#:
#: The source prints atmospheres (34.023 atm and down) but solves in bar; the
#: first entry is 500 psia. Stated in bar here so no conversion sits between
#: this constant and what CEA is actually given.
RP1311_EXAMPLE5_PRESSURES_BAR = (
    34.473652, 17.236826, 8.618413, 3.447365, 0.344737,
)


#: Products RP-1311 Example 5 excludes, verbatim from the published input.
#:
#: Reproducing a published number requires reproducing its omissions: heavy
#: hydrocarbons that do not form at these conditions are excluded so the solver
#: does not carry them, and the list is part of the case, not a tuning knob.
#:
#: ``H2O(L)`` appears here *and* as a reactant. That is not a contradiction --
#: liquid water is loaded into the grain and is not permitted to re-form as a
#: product at 2723 K.
#:
#: The list holds 114 entries but only 113 distinct names: ``(HCOOH)2`` is
#: listed twice in the published input. Kept as published rather than
#: deduplicated, because the point of this constant is fidelity to the source
#: and a repeated omission has no effect on the solve.
RP1311_EXAMPLE5_OMIT = (
    'COOH', 'C2', 'C2H', 'CHCO,ketyl', 'C2H2,vinylidene', 'CH2CO,ketene',
    'C2H3,vinyl', 'CH3CO,acetyl', 'C2H4O,ethylen-o', 'CH3CHO,ethanal',
    'CH3COOH', '(HCOOH)2', 'C2H5', 'C2H6', 'CH3N2CH3', 'CH3OCH3', 'C2H5OH',
    'CCN', 'CNC', 'C2N2', 'C2O', 'C3', 'C3H3,propargyl', 'C3H4,allene',
    'C3H4,propyne', 'C3H4,cyclo-', 'C3H5,allyl', 'C3H6,propylene',
    'C3H6,cyclo-', 'C3H6O', 'C3H7,n-propyl', 'C3H7,i-propyl', 'C3H8',
    'C3H8O,1propanol', 'C3H8O,2propanol', 'C3O2', 'C4', 'C4H2',
    'C4H4,1,3-cyclo-', 'C4H6,butadiene', 'C4H6,2-butyne', 'C4H6,cyclo-',
    'C4H8,1-butene', 'C4H8,cis2-buten', 'C4H8,tr2-butene', 'C4H8,isobutene',
    'C4H8,cyclo-', '(CH3COOH)2', 'C4H9,n-butyl', 'C4H9,i-butyl',
    'C4H9,s-butyl', 'C4H9,t-butyl', 'C4H10,isobutane', 'C4H10,n-butane',
    'C4N2', 'C5', 'C5H6,1,3cyclo-', 'C5H8,cyclo-', 'C5H10,1-pentene',
    'C5H10,cyclo-', 'C5H11,pentyl', 'C5H11,t-pentyl', 'C5H12,n-pentane',
    'C5H12,i-pentane', 'CH3C(CH3)2CH3', 'C6H2', 'C6H5,phenyl',
    'C6H5O,phenoxy', 'C6H6', 'C6H5OH,phenol', 'C6H10,cyclo-',
    'C6H12,1-hexene', 'C6H12,cyclo-', 'C6H13,n-hexyl', 'C7H7,benzyl',
    'C7H8', 'C7H8O,cresol-mx', 'C7H14,1-heptene', 'C7H15,n-heptyl',
    'C7H16,n-heptane', 'C8H8,styrene', 'C8H10,ethylbenz', 'C8H16,1-octene',
    'C8H17,n-octyl', 'C8H18,isooctane', 'C8H18,n-octane', 'C9H19,n-nonyl',
    'C10H8,naphthale', 'C10H21,n-decyl', 'C12H9,o-bipheny',
    'C12H10,biphenyl', 'Jet-A(g)', 'HNCO', 'HNO', 'HNO2', 'HNO3', 'HCCN',
    'HCHO,formaldehy', 'HCOOH', 'NH', 'NH2', 'NH2OH', 'NCN', 'N2H2',
    'NH2NO2', 'N2H4', 'H2O2', '(HCOOH)2', 'C6H6(L)', 'C7H8(L)',
    'C8H18(L),n-octa', 'Jet-A(L)', 'H2O(s)', 'H2O(L)',
)
