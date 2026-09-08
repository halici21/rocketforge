"""Named numerical tolerances.

``docs/engineering/04_numerical_methods_and_domain_policy.md`` section 5 forbids
a single magic epsilon reused everywhere, and defines a frozen ``ToleranceSet``
whose fields are named for what they govern.

**This set grows one phase at a time.** Phase 4A defined the generic and
root-finding fields; Phase 4B adds the Mach, area and sonic fields that the
isentropic and area-Mach relations need. The remaining fields of the full
specification (``angle_abs_tol``, ``angle_tol``, ``nu_tol``, ``fanno_tol``,
``rayleigh_tol``, ``pressure_tol``) arrive with the modules that use them --
with ``pressure_tol``, the last of them, arriving with the Phase 4F nozzle.
Field names and default values are verbatim from the specification, so the set
only ever grows -- an existing caller never has to change.

The set is immutable and passed explicitly. There is no module-level mutable
configuration and no global solver: determinism requires that a result depend
on nothing but its arguments.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import InputError

__all__ = ["ToleranceSet", "DEFAULT_TOLERANCES"]


@dataclass(frozen=True, slots=True)
class ToleranceSet:
    """Numerical tolerances, grouped by what they govern.

    Attributes:
        rel_tol: Relative comparison of two computed values. Roughly 4500 times
            machine epsilon -- loose enough that a different but legitimate
            evaluation order does not fail a comparison, tight enough to catch
            a real formula error.
        abs_tol: Absolute floor for comparisons against values near zero, where
            a relative tolerance is meaningless.
        residual_tol: The magnitude of ``|f(x)|`` accepted as a converged root
            **by a caller**, for the well-scaled residuals the physics layer
            produces. It is deliberately *not* a termination criterion inside
            :func:`rocketforge.core.numerics.roots.brent`; see that module's
            docstring and DECISION-4A-01 in the Phase 4A implementation note.
        max_iter: Default iteration ceiling for bracketed scalar solvers. A
            bracketing method halves the interval in the worst case, so about
            60 iterations exhausts double precision; 100 leaves headroom
            without permitting a runaway.
        mach_abs_tol: Absolute accuracy required of a solved Mach number.
        mach_rel_tol: Relative accuracy required of a solved Mach number.
        area_abs_tol: Absolute accuracy on a solved area ratio.
        area_rel_tol: Relative accuracy on a solved area ratio.
        angle_abs_tol: Absolute accuracy required of a solved angle, in
            radians. Used as ``xtol`` when inverting the theta-beta-M
            relation for the wave angle.
        area_sonic_tol: ``|A/A* - 1|`` within which the flow is taken as sonic
            and Mach 1 is returned exactly. Sized from the conditioning of the
            relation: A/A* is quadratically flat at the sonic point, so an area
            ratio this close to unity corresponds to a Mach number within about
            ``sqrt((gamma+1)/2 * 1e-11)``, roughly 3.5e-6 at gamma = 1.4. Inside
            that window returning exactly 1 is more accurate than anything a
            root finder could produce (``04`` section 4).
        sonic_tol: ``|M - 1|`` within which a Mach number is treated as sonic.
        angle_tol: An angle in radians treated as zero, or as coincident
            with another: it decides a zero-deflection Mach wave and the
            merge of the weak and strong oblique-shock roots at theta_max.
        angle_margin: How far an angular bracket endpoint is held off a
            singular limit (the Mach angle, or a right angle), in radians.
            The angular counterpart of ``sonic_margin``, and equal to it:
            Phase 3's pseudocode names ANGLE_MARGIN without fixing a value,
            and the two play the same role for the same reason.
        nu_tol: A Prandtl-Meyer angle in radians treated as zero, or as
            having reached the maximum expansion.
        fanno_tol: A value of ``4 f L*/D`` treated as zero, so that a duct
            of that length is taken to reach exactly M = 1. Also the margin
            on the finite supersonic limit.
        rayleigh_tol: A departure of ``T0/T0*`` from 1 treated as sonic, so
            that heat addition reaching it is taken to choke the flow
            exactly. Also the margin on the supersonic ``T0/T0*`` limit.
        pressure_tol: Relative width of a nozzle back-pressure regime
            boundary. The three criticals are computed to about 1e-15, so
            1e-9 makes the measure-zero regimes -- choking onset, shock at
            exit, ideal expansion -- reachable by a user typing a rounded
            number, without swallowing a genuinely different operating point.
        near_theta_max: Relative closeness to theta_max, as a fraction of
            theta_max, below which the wave angle is poorly determined and
            the ``NEAR_THETA_MAX`` advisory is raised.
        sonic_margin: How far a bracket endpoint is held off M = 1, so the
            interval stays open without straddling the minimum.
        near_sonic_mach: Window around M = 1 within which a solved Mach number
            carries the ``NEAR_SONIC`` advisory. Deliberately wide: it is an
            honesty flag about resolution, not an error.
        mach_floor: Smallest Mach number a bracket will reach. At 1e-6 the area
            ratio is already about 5.8e5 and the flow is indistinguishable from
            stagnant; below this is arithmetic, not physics.
        mach_ceiling: Largest Mach number a bracket will reach. At M = 100 and
            gamma = 1.4, A/A* is 4.6e7 and p/p0 is 2.8e-12 -- beyond every real
            device by orders of magnitude, and past the point where a
            calorically perfect gas is arguable at all.
        gamma_min: Hard lower limit on the ratio of specific heats.
        gamma_max: Hard upper limit on the ratio of specific heats.
        gamma_advisory_min: Below this, results are computed but carry the
            ``EXTRAPOLATED_GAMMA`` advisory.
        gamma_advisory_max: Above this, likewise.
    """

    # --- generic comparison ---
    rel_tol: float = 1e-12
    abs_tol: float = 1e-14

    # --- root finding ---
    residual_tol: float = 1e-10
    max_iter: int = 100
    mach_abs_tol: float = 1e-10
    mach_rel_tol: float = 1e-12
    area_abs_tol: float = 1e-10
    area_rel_tol: float = 1e-12
    angle_abs_tol: float = 1e-10

    # --- sonic / branch handling ---
    area_sonic_tol: float = 1e-11
    sonic_tol: float = 1e-9
    sonic_margin: float = 1e-9
    near_sonic_mach: float = 1e-3
    angle_tol: float = 1e-9
    angle_margin: float = 1e-9
    nu_tol: float = 1e-12
    near_theta_max: float = 0.01
    fanno_tol: float = 1e-12
    rayleigh_tol: float = 1e-12
    pressure_tol: float = 1e-9

    # --- domain limits ---
    mach_floor: float = 1e-6
    mach_ceiling: float = 100.0
    gamma_min: float = 1.001
    gamma_max: float = 3.0
    gamma_advisory_min: float = 1.05
    gamma_advisory_max: float = 1.9

    def __post_init__(self) -> None:
        positive = (
            "rel_tol", "abs_tol", "residual_tol",
            "mach_abs_tol", "mach_rel_tol", "area_abs_tol", "area_rel_tol",
            "area_sonic_tol", "sonic_tol", "sonic_margin", "near_sonic_mach",
            "angle_abs_tol", "angle_tol", "angle_margin", "nu_tol", "near_theta_max",
            "fanno_tol", "rayleigh_tol", "pressure_tol",
            "mach_floor", "mach_ceiling",
        )
        for name in positive:
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or value <= 0.0:
                raise InputError(f"ToleranceSet.{name} must be a positive number, got {value!r}")
        if not isinstance(self.max_iter, int) or isinstance(self.max_iter, bool) or self.max_iter < 1:
            raise InputError(f"ToleranceSet.max_iter must be an integer >= 1, got {self.max_iter!r}")
        if not 1.0 < self.gamma_min <= self.gamma_max:
            raise InputError(
                "ToleranceSet requires 1 < gamma_min <= gamma_max, got "
                f"gamma_min={self.gamma_min!r}, gamma_max={self.gamma_max!r}"
            )
        if not self.gamma_min <= self.gamma_advisory_min <= self.gamma_advisory_max <= self.gamma_max:
            raise InputError(
                "the gamma advisory band must sit inside the hard limits, got "
                f"[{self.gamma_advisory_min!r}, {self.gamma_advisory_max!r}] "
                f"inside [{self.gamma_min!r}, {self.gamma_max!r}]"
            )
        if self.mach_floor >= 1.0 or self.mach_ceiling <= 1.0:
            raise InputError(
                "the Mach bracket limits must straddle the sonic point, got "
                f"floor={self.mach_floor!r}, ceiling={self.mach_ceiling!r}"
            )


#: The tolerances used when a caller expresses no preference. Immutable, so
#: this constant can be shared freely without any risk of action at a distance.
DEFAULT_TOLERANCES = ToleranceSet()
