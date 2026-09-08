"""Shared types for the compressible-flow module.

Branch selectors and grouped result records, specified in
``docs/engineering/02_data_model_and_api_contracts.md`` sections 4 and 11.
Kept separate from the relations so that later modules -- normal shock, nozzle
-- can import the branch vocabulary without importing the isentropic relations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "FlowBranch",
    "IsentropicRatios",
    "AreaMachSolutions",
    "ShockBranch",
    "ThetaMaxResult",
    "ObliqueShockResult",
    "ObliqueShockPair",
    "ThetaBetaCurve",
    "FannoState",
    "FannoDuctResult",
    "RayleighState",
    "RayleighDuctResult",
    "NozzleRegime",
    "StagnationState",
    "FlowState",
    "NozzleOperating",
    "CriticalPressureRatios",
    "ShockLocation",
    "NozzleRegimeResult",
    "NozzleSolution",
]


class FlowBranch(StrEnum):
    """Which side of the sonic point a solution is wanted on.

    The area-Mach relation has two roots for every area ratio above one, and
    the equations cannot say which the caller means: the same nozzle station
    is subsonic before the throat is choked and supersonic after. So the branch
    is a required argument with no default, and this enum is how it is stated.

    ``BOTH`` is a *request*, not a result: it is accepted by
    ``mach_from_area_ratio_both`` and never appears in a returned record.
    """

    SUBSONIC = "subsonic"
    SUPERSONIC = "supersonic"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class IsentropicRatios:
    """Every isentropic ratio at one Mach number.

    All ratios are oriented **static over stagnation**, or **static over the
    sonic reference**, as their names say. That orientation is fixed and
    tested: p/p0 falls from 1 at rest towards 0 at high Mach, so a value above
    1 in any of the three static-to-stagnation fields is a bug, not a
    convention difference.

    Attributes:
        mach: The Mach number these ratios describe [-].
        temperature_ratio: T/T0 [-], in (0, 1].
        pressure_ratio: p/p0 [-], in (0, 1].
        density_ratio: rho/rho0 [-], in (0, 1].
        area_ratio: A/A* [-], >= 1. None at M = 0, where it is unbounded.
        temperature_ratio_star: T/T* [-].
        pressure_ratio_star: p/p* [-].
        density_ratio_star: rho/rho* [-].
        mach_angle: mu [rad]. None for M < 1, where no Mach wave exists.
        prandtl_meyer_angle: nu [rad]. Always None in this release: the
            Prandtl-Meyer function is a separate relation family and arrives
            with its own module and its own verification. The field is present
            because the record's shape is fixed by the data-model contract.
    """

    mach: float
    temperature_ratio: float
    pressure_ratio: float
    density_ratio: float
    area_ratio: float | None
    temperature_ratio_star: float
    pressure_ratio_star: float
    density_ratio_star: float
    mach_angle: float | None = None
    prandtl_meyer_angle: float | None = None


@dataclass(frozen=True, slots=True)
class AreaMachSolutions:
    """Both Mach numbers that share one area ratio.

    Named fields rather than a tuple, so no caller has to remember which of two
    numbers came first.

    Attributes:
        area_ratio: The A/A* that was inverted [-].
        subsonic: The root below Mach 1.
        supersonic: The root above Mach 1.
        sonic: True when the input was within the sonic tolerance of unity, in
            which case both roots are exactly 1.
    """

    area_ratio: float
    subsonic: float
    supersonic: float
    sonic: bool


class ShockBranch(StrEnum):
    """Which of the two wave angles that turn a flow through the same angle.

    The theta-beta-M relation rises from zero at the Mach angle to a maximum
    and falls back to zero at a right angle, so every attainable deflection has
    two wave angles: a weak shock at the lower one and a strong shock at the
    higher one. The equations cannot say which is meant.

    Unlike :class:`FlowBranch`, this enum has a *default* -- ``WEAK`` -- and the
    reason is physical rather than convenient: an unconstrained external flow
    takes the weak branch essentially always, the strong solution being realised
    only when downstream conditions force it. A result that took the default
    says so through a diagnostic, so the assumption is never silent.

    ``BOTH`` is a *request*, not a result: it never appears in a returned
    record.
    """

    WEAK = "weak"
    STRONG = "strong"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class ThetaMaxResult:
    """The attachment limit for one upstream Mach number. Angles in radians."""

    mach1: float
    theta_max: float
    beta_at_theta_max: float
    mach_angle: float


@dataclass(frozen=True, slots=True)
class ObliqueShockResult:
    """One attached oblique shock, as one record. Angles in radians.

    Every property ratio here came from the normal-shock relations evaluated at
    ``mach_normal1``; none of them was computed by the oblique-shock module.

    ``downstream_supersonic`` is stated rather than inferred from the branch,
    because the two do not coincide: the wave angle at which the flow behind
    turns sonic sits just *below* the angle of maximum deflection, so a narrow
    band of weak solutions is already subsonic behind the shock.
    """

    mach1: float
    theta: float
    beta: float
    branch: ShockBranch
    mach_normal1: float
    mach_normal2: float
    mach2: float
    pressure_ratio: float
    temperature_ratio: float
    density_ratio: float
    stagnation_pressure_ratio: float
    stagnation_temperature_ratio: float
    entropy_change: float
    downstream_flow_angle: float
    theta_max: float
    downstream_supersonic: bool


@dataclass(frozen=True, slots=True)
class ObliqueShockPair:
    """Both solutions for one deflection, named rather than ordered."""

    weak: ObliqueShockResult
    strong: ObliqueShockResult


@dataclass(frozen=True, slots=True)
class ThetaBetaCurve:
    """Data for the theta-beta-M diagram. Angles in radians, no presentation."""

    mach1: float
    beta: object          # np.ndarray, from the Mach angle to pi/2
    theta: object         # np.ndarray
    theta_max: float
    beta_at_theta_max: float
    beta_sonic: float
    mach_angle: float


@dataclass(frozen=True, slots=True)
class FannoState:
    """Every Fanno ratio at one Mach number, against the Fanno sonic state.

    The starred state here is the state this flow would reach at the end of a
    duct of length L* -- reached *by friction*, not isentropically. It is a
    different state from the isentropic A/A* reference, and confusing the two
    is a known implementation trap; ``03`` section 8.4 records the two genuine
    coincidences and the tests assert both those and the inequalities.

    ``friction_parameter`` is ``4 f L*/D`` with **f the Fanning friction
    factor**, and nothing in this project uses any other convention below the
    application boundary.
    """

    mach: float
    temperature_ratio: float             # T/T*
    pressure_ratio: float                # p/p*
    density_ratio: float                 # rho/rho*
    stagnation_pressure_ratio: float     # p0/p0*
    velocity_ratio: float                # V/V*
    friction_parameter: float            # 4 f_Fanning L*/D  [-]


@dataclass(frozen=True, slots=True)
class FannoDuctResult:
    """A finite constant-area duct with friction, inlet to outlet.

    ``choked`` is True only when the duct reaches exactly M = 1. A duct longer
    than the choking length has no solution at all and is reported as such --
    never as a silently truncated duct, and never by crossing the sonic point
    onto the other branch.
    """

    upstream: FannoState
    downstream: FannoState
    duct_parameter: float                # 4 f L/D supplied
    remaining_to_choking: float          # 4 f L*/D at the downstream station
    choked: bool
    pressure_ratio_12: float             # p2/p1
    temperature_ratio_12: float
    stagnation_pressure_ratio_12: float


@dataclass(frozen=True, slots=True)
class RayleighState:
    """Every Rayleigh ratio at one Mach number, against the Rayleigh sonic state.

    None of these coincides with its isentropic or Fanno counterpart, and a
    test asserts the difference: T/T* here is M^2[(gamma+1)/(1+gamma M^2)]^2,
    while the isentropic and Fanno families share (gamma+1)/(2+(gamma-1)M^2).
    """

    mach: float
    temperature_ratio: float               # T/T*
    pressure_ratio: float                  # p/p*
    density_ratio: float                   # rho/rho*
    stagnation_temperature_ratio: float    # T0/T0*
    stagnation_pressure_ratio: float       # p0/p0*


@dataclass(frozen=True, slots=True)
class RayleighDuctResult:
    """A finite constant-area duct with heat exchange, inlet to outlet.

    ``thermally_choked`` is True only when the heat added brings the flow to
    exactly M = 1. More heat than that has no solution on the same Rayleigh
    line: the upstream condition has to change, and saying so is the engineering
    answer rather than a failure.
    """

    upstream: RayleighState
    downstream: RayleighState
    stagnation_temperature_ratio_12: float   # T02/T01
    pressure_ratio_12: float
    temperature_ratio_12: float
    stagnation_pressure_ratio_12: float
    thermally_choked: bool


# ---------------------------------------------------------------------------
# nozzle (03 section 10, 02 sections 1.3, 1.4 and 11)
# ---------------------------------------------------------------------------


class NozzleRegime(StrEnum):
    """How a converging-diverging nozzle is operating.

    The seven states a quasi-1D C-D nozzle can be in, ordered by descending
    back pressure. Every one of them is a *different internal solution*, not a
    label attached to the same one -- which is why this is an enum in the
    physics layer rather than a string chosen in a controller.

    ``CHOKED_SUBSONIC_EXIT`` is the regime the task list calls choking onset.
    The name here says what the flow is doing rather than what has just
    happened to it, and reads correctly in a status chip.

    The last three share one internal solution and differ only outside the exit
    plane, which this model does not compute. That is stated rather than
    hidden: the regime is reported, the external wave pattern is not claimed.
    """

    UNCHOKED_SUBSONIC = "unchoked_subsonic"
    CHOKED_SUBSONIC_EXIT = "choked_subsonic_exit"
    INTERNAL_NORMAL_SHOCK = "internal_normal_shock"
    SHOCK_AT_EXIT = "shock_at_exit"
    OVEREXPANDED = "overexpanded"
    IDEALLY_EXPANDED = "ideally_expanded"
    UNDEREXPANDED = "underexpanded"


@dataclass(frozen=True, slots=True)
class StagnationState:
    """Stagnation conditions at a station.

    Separate from :class:`FlowState` rather than folded into it, because
    stagnation quantities are precisely the ones this module's processes
    conserve or destroy: both constant through an isentropic passage, T0
    constant with p0 falling across a shock. Keeping them their own object is
    what lets a nozzle solution say p0 is one value upstream of the shock and
    another downstream without two half-filled states.
    """

    stagnation_pressure: float | None = None       # p0 [Pa]
    stagnation_temperature: float | None = None    # T0 [K]
    stagnation_density: float | None = None        # rho0 [kg/m3]


@dataclass(frozen=True, slots=True)
class FlowState:
    """One station of a one-dimensional flow.

    ``mach`` and ``gas`` are mandatory because Mach number plus gamma fixes
    every ratio in the module, which is the level at which the physics is
    actually defined. The dimensional trio is all-or-nothing: a state with p
    but no T cannot give density, speed of sound or velocity, so allowing it
    would only produce a half-usable object.

    Attributes:
        mach: Mach number [-].
        gas: The gas model.
        pressure: Static pressure [Pa], or None.
        temperature: Static temperature [K], or None.
        density: Static density [kg/m3], or None. Stored rather than always
            derived, so a provider-supplied state needs no back-computation,
            but checked against p/(R T) when all three are present.
        stagnation: Stagnation conditions at this station, if known.
    """

    mach: float
    gas: object                        # PerfectGas; loosely typed so that
    pressure: float | None = None      # types.py imports no relations
    temperature: float | None = None
    density: float | None = None
    stagnation: StagnationState | None = None

    def __post_init__(self) -> None:
        if (self.pressure is not None and self.temperature is not None
                and self.density is not None):
            gas_constant = getattr(self.gas, "gas_constant", None)
            if gas_constant:
                expected = self.pressure / (gas_constant * self.temperature)
                if abs(self.density - expected) > 1e-9 * max(abs(expected), 1.0):
                    from ...core.errors import InconsistentStateError
                    raise InconsistentStateError(
                        f"density {self.density!r} disagrees with p/(R T) = "
                        f"{expected!r} for this perfect gas")

    @property
    def is_dimensional(self) -> bool:
        """Whether p and T are both known, so the derived quantities exist."""
        return self.pressure is not None and self.temperature is not None

    @property
    def speed_of_sound(self) -> float | None:
        """sqrt(gamma R T) [m/s], or None without a temperature or an R."""
        if self.temperature is None:
            return None
        speed = getattr(self.gas, "speed_of_sound", None)
        return None if speed is None else float(speed(self.temperature))

    @property
    def velocity(self) -> float | None:
        """M a [m/s], or None when the speed of sound is unknown."""
        sound = self.speed_of_sound
        return None if sound is None else self.mach * sound


@dataclass(frozen=True, slots=True)
class NozzleOperating:
    """What is imposed on the nozzle from outside: reservoir and environment.

    T0 is optional because the dimensionless half of the module -- thresholds,
    regime, shock area ratio -- needs only pressures and gamma. Without it the
    dimensional arrays come back as None with a diagnostic saying so, rather
    than fabricated from an assumed reservoir temperature.
    """

    stagnation_pressure: float                     # p0 [Pa]
    back_pressure: float                           # pb [Pa]
    stagnation_temperature: float | None = None    # T0 [K]

    @property
    def pressure_ratio_back(self) -> float:
        """pb/p0 [-], the single number the regime classifier needs."""
        return self.back_pressure / self.stagnation_pressure


@dataclass(frozen=True, slots=True)
class CriticalPressureRatios:
    """The three back-pressure thresholds of a C-D nozzle, as pb/p0.

    All three follow from Ae/A* and gamma alone -- there is no hard-coded
    pressure anywhere in the classifier. The ordering is always
    ``third < second < first < 1``, and it is asserted rather than assumed,
    because a violation would mean one of the three had been computed on the
    wrong branch.
    """

    area_ratio_exit: float
    first_critical: float          # choking onset: subsonic-branch exit pressure
    second_critical: float         # normal shock standing exactly at the exit
    third_critical: float          # ideal expansion: supersonic-branch exit pressure
    mach_exit_subsonic: float
    mach_exit_supersonic: float


@dataclass(frozen=True, slots=True)
class ShockLocation:
    """Where a normal shock stands in the diverging section, and how strong.

    ``area_ratio_shock`` is As/A1*, referred to the *upstream* sonic area,
    which for a choked nozzle is the throat. ``x`` is present only when a
    geometry profile was supplied: an area ratio alone fixes the shock's area
    but says nothing about where that area occurs.
    """

    area_ratio_shock: float            # As/A1*
    x: float | None                    # [m], only with a supplied geometry
    mach_upstream: float
    mach_downstream: float
    pressure_ratio: float              # p2/p1 across the shock
    stagnation_pressure_ratio: float   # p02/p01
    area_star_downstream_ratio: float  # A2*/A1*


@dataclass(frozen=True, slots=True)
class NozzleRegimeResult:
    """The cheap answer: which regime, at what exit condition, and why.

    Classification needs no distributed solution, so this record is what a
    sweep of a thousand back pressures produces per point.
    """

    regime: NozzleRegime
    critical: CriticalPressureRatios
    pressure_ratio_back: float         # pb/p0 as supplied, never clamped
    mach_exit: float
    pressure_ratio_exit: float         # pe/p0
    shock: ShockLocation | None        # INTERNAL_NORMAL_SHOCK / SHOCK_AT_EXIT only


@dataclass(frozen=True, slots=True)
class NozzleSolution:
    """The full distributed quasi-1D solution.

    The arrays are the supplied x grid plus, when a shock exists, one
    duplicated station: ``x[i] == x[i+1] == x_s`` with the pre-shock state
    first and the post-shock state second, and ``shock_index`` is ``i``. The
    duplicate is how a discontinuity is told honestly to a renderer that draws
    polylines -- and smoothing it would erase the stagnation-pressure loss the
    page exists to show.

    The dimensional arrays are None together when T0 or R is missing. Ratios
    are always present, because ratios are what gamma alone can supply.
    """

    regime: NozzleRegime
    critical: CriticalPressureRatios
    shock: ShockLocation | None
    choked: bool
    mass_flow: float | None            # [kg/s]; None without T0 and an R

    throat: FlowState
    exit: FlowState

    x: object                          # np.ndarray [m]
    area: object                       # np.ndarray [m2]
    area_ratio: object                 # np.ndarray A/At [-]
    mach: object                       # np.ndarray [-]
    pressure_ratio: object             # np.ndarray p/p01 [-]
    temperature_ratio: object          # np.ndarray T/T01 [-]
    stagnation_pressure_ratio: object  # np.ndarray p0(x)/p01 [-], steps at a shock
    pressure: object                   # np.ndarray [Pa] or None
    temperature: object                # np.ndarray [K] or None
    density: object                    # np.ndarray [kg/m3] or None
    speed_of_sound: object             # np.ndarray [m/s] or None
    velocity: object                   # np.ndarray [m/s] or None
    stagnation_pressure: object        # np.ndarray [Pa] or None
    stagnation_temperature: object     # np.ndarray [K] or None
    shock_index: int | None
    throat_index: int
