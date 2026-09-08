"""Reference records for the compressible-flow relations.

One registry, keyed by identifier, holding the equation, its assumptions, its
domain and its source. Results carry a lightweight :class:`RelationRef` that
points here rather than copying the prose, so there is exactly one place where
an assumption list can be wrong (``01`` section 10, ``02`` section 9).

``html`` is written with the entity markup the existing Equation Library page
already renders, so that page can eventually read this registry instead of its
hand-written placeholder list -- with no change to the QML.

Sources are cited at chapter or report level. Where a value has been checked
against a printed table, the check is recorded in
``tests/reference_data/SOURCES.md`` rather than here.
"""

from __future__ import annotations

from typing import Final, Mapping

from ...core.provenance import EquationRecord, RelationRef, VariableRef

__all__ = [
    "MODEL_ISENTROPIC",
    "MODEL_MASS_FLOW",
    "MODEL_NORMAL_SHOCK",
    "MODEL_OBLIQUE_SHOCK",
    "MODEL_PRANDTL_MEYER",
    "MODEL_FANNO",
    "MODEL_RAYLEIGH",
    "EQUATIONS",
    "record",
    "reference",
    "REL_TEMPERATURE_RATIO",
    "REL_PRESSURE_RATIO",
    "REL_DENSITY_RATIO",
    "REL_AREA_RATIO",
    "REL_STARRED_RATIOS",
    "REL_MACH_ANGLE",
    "REL_SPEED_OF_SOUND",
    "REL_MASS_FLOW_PARAMETER",
    "REL_CHOKED_MASS_FLOW",
    "REL_NORMAL_SHOCK",
    "REL_PITOT_RATIO",
    "REL_THETA_BETA_MACH",
    "REL_THETA_MAX",
    "REL_PRANDTL_MEYER",
    "REL_FANNO_RATIOS",
    "REL_FANNO_FRICTION",
    "REL_RAYLEIGH_RATIOS",
    "REL_RAYLEIGH_STAGNATION",
]

#: Model identifier for the perfect-gas isentropic family (ADR-13).
MODEL_ISENTROPIC: Final = "perfect_gas_isentropic_v1"

#: Model identifier for the perfect-gas mass-flow family.
MODEL_MASS_FLOW: Final = "perfect_gas_mass_flow_v1"

#: Model identifier for the perfect-gas normal-shock family.
MODEL_NORMAL_SHOCK: Final = "perfect_gas_normal_shock_v1"

#: Model identifier for the perfect-gas oblique-shock family.
MODEL_OBLIQUE_SHOCK: Final = "perfect_gas_oblique_shock_v1"

#: Model identifier for the perfect-gas Prandtl-Meyer family.
MODEL_PRANDTL_MEYER: Final = "perfect_gas_prandtl_meyer_v1"

#: Model identifier for the perfect-gas Fanno family (adiabatic, with friction).
MODEL_FANNO: Final = "perfect_gas_fanno_v1"

#: Model identifier for the perfect-gas Rayleigh family (frictionless, with heat).
MODEL_RAYLEIGH: Final = "perfect_gas_rayleigh_v1"

_ASSUMPTIONS: Final = (
    "Steady flow",
    "One-dimensional (quasi-one-dimensional for the area relation)",
    "Adiabatic and reversible, therefore isentropic",
    "Calorically perfect gas: constant gamma, constant R",
    "Ideal equation of state",
    "No body forces and no work exchange",
)

_SOURCE_ANDERSON: Final = "Anderson, Modern Compressible Flow, 3rd ed., ch. 3 and 5"
_SOURCE_NACA: Final = (
    "Ames Research Staff, NACA Report 1135, 'Equations, Tables, and Charts for "
    "Compressible Flow' (1953), eqs. 43-50 and Tables I-II"
)

_SOURCE_SHAPIRO: Final = (
    "Shapiro, 'The Dynamics and Thermodynamics of Compressible Fluid Flow', "
    "vol. I (1953), ch. 6 (Fanno) and ch. 7 (Rayleigh)"
)

#: Fanno: adiabatic with friction. Adiabatic is not isentropic -- friction is
#: irreversible, so p0 falls on both branches. Section 8 of ``03``.
_ASSUMPTIONS_FANNO: Final = (
    "Steady flow",
    "One-dimensional",
    "Constant area",
    "Adiabatic: no heat exchange, so T0 is constant along the duct",
    "Wall friction, which is irreversible: adiabatic does not mean isentropic",
    "No shaft work",
    "Calorically perfect gas: constant gamma, constant R",
)

#: Rayleigh: frictionless with heat exchange. Section 9 of ``03``.
_ASSUMPTIONS_RAYLEIGH: Final = (
    "Steady flow",
    "One-dimensional",
    "Constant area",
    "Frictionless",
    "Heat exchange with the surroundings, through the state relation only: no "
    "combustion model, no chemistry, no radiation, no finite-rate transfer",
    "No shaft work",
    "Calorically perfect gas: constant gamma, constant R",
)

_MACH = VariableRef("M", "Mach number", "", "mach")
_GAMMA = VariableRef("γ", "ratio of specific heats", "", "gamma")


def _entry(record_: EquationRecord) -> tuple[str, EquationRecord]:
    return record_.identifier, record_


EQUATIONS: Final[Mapping[str, EquationRecord]] = dict(
    (
        _entry(
            EquationRecord(
                identifier="isentropic.temperature_ratio.v1",
                name="Stagnation temperature ratio",
                group="Isentropic",
                latex=r"\frac{T}{T_0} = \left[1 + \frac{\gamma-1}{2}M^2\right]^{-1}",
                html="<i>T</i>/<i>T</i><sub>0</sub> = [ 1 + ½ (γ−1) <i>M</i><sup>2</sup> ] <sup>−1</sup>",
                description=(
                    "Static temperature as a fraction of stagnation temperature. Follows "
                    "from energy conservation alone, so it holds across an adiabatic shock "
                    "as well as along an isentropic passage."
                ),
                variables=(
                    _MACH,
                    _GAMMA,
                    VariableRef("T", "static temperature", "K", "temperature"),
                    VariableRef("T₀", "stagnation temperature", "K", "stagnation_temperature"),
                ),
                assumptions=_ASSUMPTIONS,
                domain="M >= 0, 1.001 <= gamma <= 3.0",
                source=_SOURCE_ANDERSON,
                related=("isentropic.pressure_ratio.v1", "isentropic.density_ratio.v1"),
            )
        ),
        _entry(
            EquationRecord(
                identifier="isentropic.pressure_ratio.v1",
                name="Stagnation pressure ratio",
                group="Isentropic",
                latex=r"\frac{p}{p_0} = \left[1 + \frac{\gamma-1}{2}M^2\right]^{-\frac{\gamma}{\gamma-1}}",
                html=(
                    "<i>p</i>/<i>p</i><sub>0</sub> = [ 1 + ½ (γ−1) <i>M</i><sup>2</sup> ]"
                    " <sup>−γ/(γ−1)</sup>"
                ),
                description=(
                    "Static pressure as a fraction of stagnation pressure. Unlike the "
                    "temperature ratio this one is isentropic: stagnation pressure is lost "
                    "across a shock, so the relation does not carry across one."
                ),
                variables=(
                    _MACH,
                    _GAMMA,
                    VariableRef("p", "static pressure", "Pa", "pressure"),
                    VariableRef("p₀", "stagnation pressure", "Pa", "stagnation_pressure"),
                ),
                assumptions=_ASSUMPTIONS,
                domain="M >= 0, 1.001 <= gamma <= 3.0",
                source=_SOURCE_ANDERSON,
                related=("isentropic.temperature_ratio.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="isentropic.density_ratio.v1",
                name="Stagnation density ratio",
                group="Isentropic",
                latex=r"\frac{\rho}{\rho_0} = \left[1 + \frac{\gamma-1}{2}M^2\right]^{-\frac{1}{\gamma-1}}",
                html=(
                    "<i>ρ</i>/<i>ρ</i><sub>0</sub> = [ 1 + ½ (γ−1) <i>M</i><sup>2</sup> ]"
                    " <sup>−1/(γ−1)</sup>"
                ),
                description="Static density as a fraction of stagnation density.",
                variables=(
                    _MACH,
                    _GAMMA,
                    VariableRef("ρ", "static density", "kg/m³", "density"),
                    VariableRef("ρ₀", "stagnation density", "kg/m³", "stagnation_density"),
                ),
                assumptions=_ASSUMPTIONS,
                domain="M >= 0, 1.001 <= gamma <= 3.0",
                source=_SOURCE_ANDERSON,
                related=("isentropic.pressure_ratio.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="isentropic.area_ratio.v1",
                name="Area-Mach relation",
                group="Isentropic",
                latex=(
                    r"\frac{A}{A^*} = \frac{1}{M}\left[\frac{2}{\gamma+1}"
                    r"\left(1+\frac{\gamma-1}{2}M^2\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}}"
                ),
                html=(
                    "<i>A</i>/<i>A</i>* = (1/<i>M</i>) [ (2/(γ+1)) ( 1 + ½ (γ−1) "
                    "<i>M</i><sup>2</sup> ) ] <sup>(γ+1)/2(γ−1)</sup>"
                ),
                description=(
                    "Duct area as a multiple of the area at which the same flow would be "
                    "sonic. Its minimum is exactly 1 at M = 1, so every area ratio above "
                    "one is reached by two Mach numbers, one subsonic and one supersonic; "
                    "the inverse therefore requires the caller to name a branch."
                ),
                variables=(
                    _MACH,
                    _GAMMA,
                    VariableRef("A", "local area", "m²", "area"),
                    VariableRef("A*", "sonic reference area", "m²", "area_star"),
                ),
                assumptions=_ASSUMPTIONS + ("Area varies slowly enough for quasi-1D flow",),
                domain="M > 0, 1.001 <= gamma <= 3.0; inverse requires A/A* >= 1",
                source=_SOURCE_NACA,
                related=("isentropic.temperature_ratio.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="isentropic.starred_ratios.v1",
                name="Sonic reference ratios",
                group="Isentropic",
                latex=r"\frac{T}{T^*} = \frac{\gamma+1}{2+(\gamma-1)M^2}",
                html=(
                    "<i>T</i>/<i>T</i>* = (γ+1) / ( 2 + (γ−1) <i>M</i><sup>2</sup> ), with "
                    "<i>p</i>/<i>p</i>* and <i>ρ</i>/<i>ρ</i>* the same bracket raised to "
                    "γ/(γ−1) and 1/(γ−1)"
                ),
                description=(
                    "Static properties as multiples of their values at the sonic point of "
                    "the same isentropic flow. Obtained by evaluating the stagnation "
                    "relations at M = 1 and dividing."
                ),
                variables=(
                    _MACH,
                    _GAMMA,
                    VariableRef("T*", "sonic static temperature", "K", "temperature_star"),
                    VariableRef("p*", "sonic static pressure", "Pa", "pressure_star"),
                ),
                assumptions=_ASSUMPTIONS,
                domain="M >= 0, 1.001 <= gamma <= 3.0",
                source=_SOURCE_ANDERSON,
                related=("isentropic.area_ratio.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="isentropic.mach_angle.v1",
                name="Mach angle",
                group="Isentropic",
                latex=r"\mu = \arcsin\!\left(\frac{1}{M}\right)",
                html="μ = arcsin( 1/<i>M</i> )",
                description=(
                    "Angle between a Mach wave and the flow direction. Defined only in "
                    "supersonic flow, where disturbances cannot propagate upstream."
                ),
                variables=(_MACH, VariableRef("μ", "Mach angle", "rad", "mach_angle")),
                assumptions=("Supersonic flow", "Infinitesimal disturbance"),
                domain="M >= 1",
                source=_SOURCE_ANDERSON,
            )
        ),
        _entry(
            EquationRecord(
                identifier="mass_flow.parameter.v1",
                name="Mass-flow parameter",
                group="Mass flow",
                latex=(r"\frac{\dot m \sqrt{R T_0}}{A p_0} = \sqrt{\gamma}\,M"
                       r"\left[1+\frac{\gamma-1}{2}M^2\right]^{-\frac{\gamma+1}{2(\gamma-1)}}"),
                html=("&#7745;&#8730;(<i>R T</i><sub>0</sub>) / (<i>A p</i><sub>0</sub>) = "
                      "&#8730;&#947; <i>M</i> [ 1 + &#189; (&#947;&#8722;1) <i>M</i><sup>2</sup> ] "
                      "<sup>&#8722;(&#947;+1)/2(&#947;&#8722;1)</sup>"),
                description=(
                    "The dimensionless group that fixes mass flow for a given stagnation "
                    "state and area. It rises from zero at rest to a maximum at Mach 1 and "
                    "falls thereafter, which is what makes a passage choke."
                ),
                variables=(
                    _MACH, _GAMMA,
                    VariableRef("m-dot", "mass flow", "kg/s", "mass_flow"),
                    VariableRef("A", "area", "m2", "area"),
                    VariableRef("p0", "stagnation pressure", "Pa", "stagnation_pressure"),
                    VariableRef("T0", "stagnation temperature", "K", "stagnation_temperature"),
                    VariableRef("R", "specific gas constant", "J/(kg K)", "gas_constant"),
                ),
                assumptions=_ASSUMPTIONS + ("Flow through a known cross-sectional area",),
                domain="M >= 0, 1.001 <= gamma <= 3.0; dimensional form needs R, A, p0, T0 > 0",
                source=_SOURCE_ANDERSON,
                related=("mass_flow.choked.v1", "isentropic.pressure_ratio.v1"),
            )
        ),
        _entry(
            EquationRecord(
                identifier="mass_flow.choked.v1",
                name="Choked mass flow",
                group="Mass flow",
                latex=(r"\dot m_{\max} = \frac{\Gamma(\gamma)\, p_0 A^{*}}{\sqrt{R T_0}},\quad"
                       r"\Gamma = \sqrt{\gamma}\left(\frac{2}{\gamma+1}\right)"
                       r"^{\frac{\gamma+1}{2(\gamma-1)}}"),
                html=("&#7745;<sub>max</sub> = &#915;(&#947;) <i>p</i><sub>0</sub> <i>A</i>* / "
                      "&#8730;(<i>R T</i><sub>0</sub>), &#915; = &#8730;&#947; "
                      "( 2/(&#947;+1) ) <sup>(&#947;+1)/2(&#947;&#8722;1)</sup>"),
                description=(
                    "The largest mass flow a passage of a given minimum area can pass for a "
                    "given stagnation state. Reached when the minimum-area station is sonic; "
                    "lowering the downstream pressure further cannot increase it."
                ),
                variables=(
                    _GAMMA,
                    VariableRef("Gamma", "choked-flow coefficient", "", "choked_mass_flow_coefficient"),
                    VariableRef("A*", "sonic reference area", "m2", "throat_area"),
                ),
                assumptions=_ASSUMPTIONS + ("Minimum-area station is sonic",),
                domain="1.001 <= gamma <= 3.0, A* > 0, p0 > 0, T0 > 0, R > 0",
                source=_SOURCE_ANDERSON,
                related=("mass_flow.parameter.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="normal_shock.jump.v1",
                name="Normal shock relations",
                group="Normal shock",
                latex=(r"M_2^2 = \frac{1+\frac{\gamma-1}{2}M_1^2}"
                       r"{\gamma M_1^2-\frac{\gamma-1}{2}},\quad"
                       r"\frac{p_2}{p_1} = 1+\frac{2\gamma}{\gamma+1}\left(M_1^2-1\right)"),
                html=("<i>M</i><sub>2</sub><sup>2</sup> = ( 1 + &#189; (&#947;&#8722;1) "
                      "<i>M</i><sub>1</sub><sup>2</sup> ) / ( &#947; <i>M</i><sub>1</sub>"
                      "<sup>2</sup> &#8722; &#189; (&#947;&#8722;1) ), &nbsp; "
                      "<i>p</i><sub>2</sub>/<i>p</i><sub>1</sub> = 1 + (2&#947;/(&#947;+1)) "
                      "( <i>M</i><sub>1</sub><sup>2</sup> &#8722; 1 )"),
                description=(
                    "Property jumps across a stationary normal shock. The flow decelerates to "
                    "subsonic; static pressure, density and temperature all rise; stagnation "
                    "pressure falls because the process is irreversible; stagnation "
                    "temperature is unchanged because it is adiabatic."
                ),
                variables=(
                    _GAMMA,
                    VariableRef("M1", "upstream Mach number", "", "mach1"),
                    VariableRef("M2", "downstream Mach number", "", "mach2"),
                    VariableRef("p2/p1", "static pressure ratio", "", "pressure_ratio"),
                    VariableRef("rho2/rho1", "density ratio", "", "density_ratio"),
                    VariableRef("T2/T1", "temperature ratio", "", "temperature_ratio"),
                    VariableRef("p02/p01", "stagnation pressure ratio", "", "stagnation_pressure_ratio"),
                ),
                assumptions=(
                    "Steady flow",
                    "One-dimensional",
                    "Adiabatic, with no work exchange",
                    "Calorically perfect gas: constant gamma, constant R",
                    "Discontinuity of zero thickness",
                    "Compressive shock: upstream flow is supersonic",
                ),
                domain="M1 >= 1, 1.001 <= gamma <= 3.0",
                source=_SOURCE_NACA,
                related=("normal_shock.pitot.v1", "isentropic.pressure_ratio.v1"),
            )
        ),
        _entry(
            EquationRecord(
                identifier="normal_shock.pitot.v1",
                name="Rayleigh pitot ratio",
                group="Normal shock",
                latex=r"\frac{p_{0,2}}{p_1} = \frac{p_{0,2}}{p_{0,1}}\cdot\frac{p_{0,1}}{p_1}",
                html=("<i>p</i><sub>02</sub>/<i>p</i><sub>1</sub> = "
                      "(<i>p</i><sub>02</sub>/<i>p</i><sub>01</sub>) &#183; "
                      "(<i>p</i><sub>01</sub>/<i>p</i><sub>1</sub>)"),
                description=(
                    "Downstream stagnation pressure over upstream static pressure: what a "
                    "pitot probe reads in supersonic flow, since the probe sits behind its "
                    "own bow shock. Composed from the shock stagnation ratio and the "
                    "upstream isentropic relation rather than given a closed form."
                ),
                variables=(
                    _GAMMA,
                    VariableRef("M1", "upstream Mach number", "", "mach1"),
                    VariableRef("p02/p1", "pitot ratio", "", "stagnation_pressure_over_upstream_static"),
                ),
                assumptions=(
                    "Steady flow",
                    "Adiabatic normal shock ahead of the probe",
                    "Isentropic deceleration behind the shock",
                    "Calorically perfect gas",
                ),
                domain="M1 >= 1, 1.001 <= gamma <= 3.0",
                source=_SOURCE_NACA,
                related=("normal_shock.jump.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="oblique_shock.theta_beta_mach.v1",
                name="theta-beta-M relation",
                group="Oblique shock",
                latex=(r"\tan\theta = 2\cot\beta\,"
                       r"\frac{M_1^{2}\sin^{2}\beta - 1}"
                       r"{M_1^{2}\left(\gamma+\cos 2\beta\right)+2}"),
                html=("tan &#952; = 2 cot &#946; &#183; "
                      "( <i>M</i><sub>1</sub><sup>2</sup> sin<sup>2</sup>&#946; &#8722; 1 ) / "
                      "( <i>M</i><sub>1</sub><sup>2</sup> (&#947; + cos 2&#946;) + 2 )"),
                description=(
                    "The flow deflection produced by a straight attached oblique shock at "
                    "wave angle beta. Zero at both ends of its range -- a Mach wave at "
                    "beta = mu, a normal shock at beta = 90 degrees -- with a maximum "
                    "between them, which is why every attainable deflection has two "
                    "wave angles."
                ),
                variables=(
                    _GAMMA,
                    VariableRef("M1", "upstream Mach number", "", "mach1"),
                    VariableRef("theta", "flow deflection angle", "rad", "theta"),
                    VariableRef("beta", "shock wave angle", "rad", "beta"),
                    VariableRef("mu", "Mach angle", "rad", "mach_angle"),
                ),
                assumptions=(
                    "Steady flow",
                    "Two-dimensional planar wedge, not a cone",
                    "Straight, attached shock",
                    "Adiabatic, inviscid, no work exchange",
                    "Calorically perfect gas: constant gamma, constant R",
                    "Supersonic upstream flow",
                ),
                domain="M1 > 1, mu <= beta <= pi/2, 1.001 <= gamma <= 3.0",
                source=_SOURCE_NACA,
                related=("oblique_shock.theta_max.v1", "normal_shock.jump.v1"),
            )
        ),
        _entry(
            EquationRecord(
                identifier="oblique_shock.theta_max.v1",
                name="Maximum deflection angle",
                group="Oblique shock",
                latex=(r"\sin^{2}\beta_{\theta\max} = \frac{1}{\gamma M_1^{2}}"
                       r"\left[\frac{(\gamma+1)M_1^{2}}{4} - 1 + "
                       r"\sqrt{(\gamma+1)\left(\frac{(\gamma+1)M_1^{4}}{16} + "
                       r"\frac{(\gamma-1)M_1^{2}}{2} + 1\right)}\right]"),
                html=("sin<sup>2</sup>&#946;<sub>&#952;max</sub> = "
                      "(1 / &#947;<i>M</i><sub>1</sub><sup>2</sup>) [ "
                      "(&#947;+1)<i>M</i><sub>1</sub><sup>2</sup>/4 &#8722; 1 + "
                      "&#8730;( (&#947;+1) ( (&#947;+1)<i>M</i><sub>1</sub><sup>4</sup>/16 + "
                      "(&#947;&#8722;1)<i>M</i><sub>1</sub><sup>2</sup>/2 + 1 ) ) ]"),
                description=(
                    "The wave angle at which the deflection is greatest, in closed form: "
                    "the stationary point of the theta-beta-M relation, obtained by "
                    "solving dtheta/dbeta = 0. Beyond the deflection it produces, no "
                    "attached shock exists and the shock detaches from the body."
                ),
                variables=(
                    _GAMMA,
                    VariableRef("M1", "upstream Mach number", "", "mach1"),
                    VariableRef("theta_max", "maximum deflection", "rad", "theta_max"),
                    VariableRef("beta", "wave angle at maximum deflection", "rad",
                                "beta_at_theta_max"),
                ),
                assumptions=(
                    "Steady flow",
                    "Two-dimensional planar wedge",
                    "Calorically perfect gas",
                    "Supersonic upstream flow",
                ),
                domain="M1 > 1, 1.001 <= gamma <= 3.0",
                source=_SOURCE_NACA,
                related=("oblique_shock.theta_beta_mach.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="prandtl_meyer.nu.v1",
                name="Prandtl-Meyer function",
                group="Prandtl-Meyer",
                latex=(r"\nu(M) = \sqrt{\frac{\gamma+1}{\gamma-1}}\,"
                       r"\arctan\sqrt{\frac{\gamma-1}{\gamma+1}(M^{2}-1)}"
                       r" - \arctan\sqrt{M^{2}-1}"),
                html=("&#957;(<i>M</i>) = &#8730;((&#947;+1)/(&#947;&#8722;1)) "
                      "arctan &#8730;( (&#947;&#8722;1)/(&#947;+1) "
                      "(<i>M</i><sup>2</sup>&#8722;1) ) &#8722; "
                      "arctan &#8730;(<i>M</i><sup>2</sup>&#8722;1)"),
                description=(
                    "The angle through which a sonic stream must turn to reach Mach M by "
                    "an isentropic expansion. Zero at Mach 1, strictly increasing, and "
                    "bounded above by (pi/2)(sqrt((gamma+1)/(gamma-1)) - 1) -- the total "
                    "turning available to expand to an infinite Mach number."
                ),
                variables=(
                    _MACH, _GAMMA,
                    VariableRef("nu", "Prandtl-Meyer angle", "rad", "nu"),
                    VariableRef("mu", "Mach angle", "rad", "mach_angle"),
                ),
                assumptions=(
                    "Steady flow",
                    "Two-dimensional centred expansion about a convex corner",
                    "Isentropic: no shock, no friction, no heat exchange",
                    "Calorically perfect gas: constant gamma, constant R",
                    "Supersonic flow throughout the fan",
                ),
                domain="M >= 1, 1.001 <= gamma <= 3.0; the inverse needs 0 <= nu < nu_max",
                source=_SOURCE_ANDERSON,
                related=("isentropic.mach_angle.v1", "isentropic.pressure_ratio.v1"),
            )
        ),
        _entry(
            EquationRecord(
                identifier="fanno.starred_ratios.v1",
                name="Fanno starred ratios",
                group="Fanno",
                latex=(r"\frac{T}{T^{*}} = \frac{\gamma+1}{\varphi}, \quad "
                       r"\frac{p}{p^{*}} = \frac{1}{M}\sqrt{\frac{\gamma+1}{\varphi}}, \quad "
                       r"\frac{\rho}{\rho^{*}} = \frac{1}{M}\sqrt{\frac{\varphi}{\gamma+1}}, \quad "
                       r"\frac{p_0}{p_0^{*}} = \frac{1}{M}"
                       r"\left[\frac{\varphi}{\gamma+1}\right]^{\frac{\gamma+1}{2(\gamma-1)}}"
                       r"\qquad \varphi = 2+(\gamma-1)M^{2}"),
                html=("<i>T</i>/<i>T</i>* = (γ+1)/φ &nbsp;·&nbsp; "
                      "<i>p</i>/<i>p</i>* = (1/<i>M</i>) √( (γ+1)/φ ) &nbsp;·&nbsp; "
                      "<i>ρ</i>/<i>ρ</i>* = (1/<i>M</i>) √( φ/(γ+1) ) &nbsp;·&nbsp; "
                      "<i>p</i><sub>0</sub>/<i>p</i><sub>0</sub>* = (1/<i>M</i>) "
                      "[ φ/(γ+1) ]<sup>(γ+1)/(2(γ−1))</sup>, &nbsp; "
                      "φ = 2 + (γ−1)<i>M</i><sup>2</sup>"),
                description=(
                    "State ratios referred to the sonic state the duct would reach at "
                    "the end of a length L*. That star state is reached by friction, "
                    "not isentropically, so it is a different state from the isentropic "
                    "A/A* reference. T0/T0* is identically 1 because the flow is "
                    "adiabatic. Two ratios nevertheless coincide with the isentropic "
                    "family, both because the flow is adiabatic at fixed mass flow: "
                    "T/T* equals the isentropic T/T*, and p0/p0* equals A/A*."
                ),
                variables=(
                    _MACH, _GAMMA,
                    VariableRef("T/T*", "static temperature ratio", "", "temperature_ratio"),
                    VariableRef("p/p*", "static pressure ratio", "", "pressure_ratio"),
                    VariableRef("ρ/ρ*", "density ratio", "", "density_ratio"),
                    VariableRef("p0/p0*", "stagnation pressure ratio", "",
                                "stagnation_pressure_ratio"),
                    VariableRef("V/V*", "velocity ratio", "", "velocity_ratio"),
                ),
                assumptions=_ASSUMPTIONS_FANNO,
                domain="M > 0, 1.001 <= gamma <= 3.0",
                source=_SOURCE_SHAPIRO,
                related=("fanno.friction_parameter.v1", "isentropic.area_ratio.v1"),
            )
        ),
        _entry(
            EquationRecord(
                identifier="fanno.friction_parameter.v1",
                name="Fanno friction parameter",
                group="Fanno",
                latex=(r"\frac{4 f L^{*}}{D} = \frac{1-M^{2}}{\gamma M^{2}}"
                       r" + \frac{\gamma+1}{2\gamma}"
                       r"\ln\!\left[\frac{(\gamma+1)M^{2}}{2+(\gamma-1)M^{2}}\right]"),
                html=("4<i>f</i><sub>Fanning</sub><i>L</i>*/<i>D</i> = "
                      "(1 − <i>M</i><sup>2</sup>)/(γ<i>M</i><sup>2</sup>) + "
                      "[(γ+1)/(2γ)] ln[ (γ+1)<i>M</i><sup>2</sup> / "
                      "(2 + (γ−1)<i>M</i><sup>2</sup>) ]"),
                description=(
                    "The duct length still available before the flow chokes, in the "
                    "Fanning convention: f is the FANNING friction factor and "
                    "f_Darcy = 4 f_Fanning, so this group equals f_Darcy L*/D for the "
                    "same physical duct. Zero at M = 1, diverging as M tends to 0, and "
                    "approaching the finite limit -1/gamma + [(gamma+1)/(2 gamma)] "
                    "ln[(gamma+1)/(gamma-1)] as M grows without bound. It decreases "
                    "monotonically along the duct on both branches, because friction "
                    "drives subsonic and supersonic flow alike towards sonic."
                ),
                variables=(
                    _MACH, _GAMMA,
                    VariableRef("f", "Fanning friction factor", "", "fanning_friction_factor"),
                    VariableRef("L*", "duct length to choking", "m", "length"),
                    VariableRef("D", "hydraulic diameter", "m", "hydraulic_diameter"),
                    VariableRef("4fL*/D", "friction parameter", "", "friction_parameter"),
                ),
                assumptions=_ASSUMPTIONS_FANNO,
                domain=(
                    "M > 0, 1.001 <= gamma <= 3.0. The supersonic branch is bounded "
                    "above by the finite M -> infinity limit"
                ),
                source=_SOURCE_SHAPIRO,
                related=("fanno.starred_ratios.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="rayleigh.starred_ratios.v1",
                name="Rayleigh starred ratios",
                group="Rayleigh",
                latex=(r"\frac{p}{p^{*}} = \frac{\gamma+1}{1+\gamma M^{2}}, \quad "
                       r"\frac{T}{T^{*}} = M^{2}\left(\frac{\gamma+1}{1+\gamma M^{2}}\right)^{2}, "
                       r"\quad \frac{\rho}{\rho^{*}} = \frac{1}{M^{2}}"
                       r"\cdot\frac{1+\gamma M^{2}}{\gamma+1}"),
                html=("<i>p</i>/<i>p</i>* = (γ+1)/(1 + γ<i>M</i><sup>2</sup>) &nbsp;·&nbsp; "
                      "<i>T</i>/<i>T</i>* = <i>M</i><sup>2</sup> "
                      "[ (γ+1)/(1 + γ<i>M</i><sup>2</sup>) ]<sup>2</sup> &nbsp;·&nbsp; "
                      "<i>ρ</i>/<i>ρ</i>* = (1/<i>M</i><sup>2</sup>) "
                      "(1 + γ<i>M</i><sup>2</sup>)/(γ+1)"),
                description=(
                    "Static ratios referred to the sonic state on the same Rayleigh "
                    "line. T/T* is NOT monotone on the subsonic branch: it reaches its "
                    "maximum of (gamma+1)^2/(4 gamma) at M = 1/sqrt(gamma), so between "
                    "that Mach number and 1 the static temperature falls while heat is "
                    "still being added. That is correct rather than a defect: in that "
                    "band the flow accelerates fast enough that the kinetic-energy rise "
                    "exceeds the heat put in. No Rayleigh ratio coincides with its "
                    "isentropic or Fanno counterpart."
                ),
                variables=(
                    _MACH, _GAMMA,
                    VariableRef("p/p*", "static pressure ratio", "", "pressure_ratio"),
                    VariableRef("T/T*", "static temperature ratio", "", "temperature_ratio"),
                    VariableRef("ρ/ρ*", "density ratio", "", "density_ratio"),
                ),
                assumptions=_ASSUMPTIONS_RAYLEIGH,
                domain="M > 0, 1.001 <= gamma <= 3.0",
                source=_SOURCE_SHAPIRO,
                related=("rayleigh.stagnation_ratios.v1",),
            )
        ),
        _entry(
            EquationRecord(
                identifier="rayleigh.stagnation_ratios.v1",
                name="Rayleigh stagnation ratios",
                group="Rayleigh",
                latex=(r"\frac{T_0}{T_0^{*}} = \frac{(\gamma+1)M^{2}"
                       r"\left[2+(\gamma-1)M^{2}\right]}{\left(1+\gamma M^{2}\right)^{2}}, "
                       r"\quad \frac{p_0}{p_0^{*}} = \frac{\gamma+1}{1+\gamma M^{2}}"
                       r"\left[\frac{2+(\gamma-1)M^{2}}{\gamma+1}\right]"
                       r"^{\frac{\gamma}{\gamma-1}}"),
                html=("<i>T</i><sub>0</sub>/<i>T</i><sub>0</sub>* = "
                      "(γ+1)<i>M</i><sup>2</sup>[2 + (γ−1)<i>M</i><sup>2</sup>] / "
                      "(1 + γ<i>M</i><sup>2</sup>)<sup>2</sup> &nbsp;·&nbsp; "
                      "<i>p</i><sub>0</sub>/<i>p</i><sub>0</sub>* = "
                      "[(γ+1)/(1 + γ<i>M</i><sup>2</sup>)] "
                      "[ (2 + (γ−1)<i>M</i><sup>2</sup>)/(γ+1) ]<sup>γ/(γ−1)</sup>"),
                description=(
                    "T0/T0* has its maximum of exactly 1 at M = 1, so heat addition "
                    "drives both branches towards sonic and the sonic state is the "
                    "thermal choking limit: this is the relation that answers 'how much "
                    "can I heat this flow'. As M grows without bound it approaches the "
                    "finite limit (gamma^2 - 1)/gamma^2, so a supersonic Rayleigh flow "
                    "can only be cooled so far. p0/p0* exceeds 1 on both sides with its "
                    "minimum of 1 at sonic: heat addition always destroys stagnation "
                    "pressure, on either branch."
                ),
                variables=(
                    _MACH, _GAMMA,
                    VariableRef("T0/T0*", "stagnation temperature ratio", "",
                                "stagnation_temperature_ratio"),
                    VariableRef("p0/p0*", "stagnation pressure ratio", "",
                                "stagnation_pressure_ratio"),
                    VariableRef("q", "heat added per unit mass", "J/kg", "heat"),
                ),
                assumptions=_ASSUMPTIONS_RAYLEIGH,
                domain=(
                    "M > 0, 1.001 <= gamma <= 3.0. The inverse needs 0 < T0/T0* <= 1 "
                    "and an explicit branch, since the ratio rises to 1 from both sides"
                ),
                source=_SOURCE_SHAPIRO,
                related=("rayleigh.starred_ratios.v1", "gas.speed_of_sound.v1"),
            )
        ),
        _entry(
            EquationRecord(
                identifier="gas.speed_of_sound.v1",
                name="Speed of sound",
                group="Gas model",
                latex=r"a = \sqrt{\gamma R T}",
                html="<i>a</i> = √( γ <i>R</i> <i>T</i> )",
                description="Speed of sound in a calorically perfect gas.",
                variables=(
                    _GAMMA,
                    VariableRef("R", "specific gas constant", "J/(kg·K)", "gas_constant"),
                    VariableRef("T", "static temperature", "K", "temperature"),
                    VariableRef("a", "speed of sound", "m/s", "speed_of_sound"),
                ),
                assumptions=("Calorically perfect gas", "Ideal equation of state"),
                domain="T > 0, 1.001 <= gamma <= 3.0, R > 0",
                source=_SOURCE_ANDERSON,
            )
        ),
    )
)


def record(identifier: str) -> EquationRecord:
    """The full reference record for a relation identifier."""
    try:
        return EQUATIONS[identifier]
    except KeyError:  # pragma: no cover - guards a typo at import time
        raise KeyError(f"no equation record for {identifier!r}") from None


def reference(identifier: str, model: str = MODEL_ISENTROPIC) -> RelationRef:
    """The lightweight reference a result carries for a relation."""
    return record(identifier).reference(model)


REL_TEMPERATURE_RATIO: Final = reference("isentropic.temperature_ratio.v1")
REL_PRESSURE_RATIO: Final = reference("isentropic.pressure_ratio.v1")
REL_DENSITY_RATIO: Final = reference("isentropic.density_ratio.v1")
REL_AREA_RATIO: Final = reference("isentropic.area_ratio.v1")
REL_STARRED_RATIOS: Final = reference("isentropic.starred_ratios.v1")
REL_MACH_ANGLE: Final = reference("isentropic.mach_angle.v1")
REL_SPEED_OF_SOUND: Final = reference("gas.speed_of_sound.v1", model="perfect_gas_v1")
REL_MASS_FLOW_PARAMETER: Final = reference("mass_flow.parameter.v1", model=MODEL_MASS_FLOW)
REL_CHOKED_MASS_FLOW: Final = reference("mass_flow.choked.v1", model=MODEL_MASS_FLOW)
REL_NORMAL_SHOCK: Final = reference("normal_shock.jump.v1", model=MODEL_NORMAL_SHOCK)
REL_PITOT_RATIO: Final = reference("normal_shock.pitot.v1", model=MODEL_NORMAL_SHOCK)
REL_THETA_BETA_MACH: Final = reference("oblique_shock.theta_beta_mach.v1",
                                       model=MODEL_OBLIQUE_SHOCK)
REL_THETA_MAX: Final = reference("oblique_shock.theta_max.v1", model=MODEL_OBLIQUE_SHOCK)
REL_PRANDTL_MEYER: Final = reference("prandtl_meyer.nu.v1", model=MODEL_PRANDTL_MEYER)
REL_FANNO_RATIOS: Final = reference("fanno.starred_ratios.v1", model=MODEL_FANNO)
REL_FANNO_FRICTION: Final = reference("fanno.friction_parameter.v1", model=MODEL_FANNO)
REL_RAYLEIGH_RATIOS: Final = reference("rayleigh.starred_ratios.v1", model=MODEL_RAYLEIGH)
REL_RAYLEIGH_STAGNATION: Final = reference("rayleigh.stagnation_ratios.v1",
                                           model=MODEL_RAYLEIGH)
