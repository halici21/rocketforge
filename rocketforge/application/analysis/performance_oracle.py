"""The provider's own performance numbers, kept at arm's length. Qt-free.

NASA CEA computes c*, Cf and Isp itself. This module fetches them, and it
exists so that two things stay true at once:

* a user can see an independent answer for the same case, which is the whole
  value of having a validated provider installed; and
* **no RocketForge performance field is ever assigned from one of them.**

Three properties keep the second one true rather than merely intended:

1. This module returns an ``OracleOutcome``, never an
   ``IdealRocketPerformance``. The types do not interchange, so a substitution
   would have to be written deliberately and would not typecheck by accident.
2. Nothing in ``performance_service`` imports it. The performance chain has no
   path to this code at all.
3. It runs only when asked. Changing an area ratio, an ambient pressure or an
   engine size never reaches this module -- which is also why the
   zero-re-solve guarantee survives having an oracle in the workspace.

Every provider import is function-local, as in ``thermochemistry_provider``,
so importing this module costs nothing on a build with no chemistry library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .thermochemistry_service import ChamberCase, build_request

__all__ = [
    "ORACLE_EMPTY",
    "ORACLE_OK",
    "ORACLE_UNAVAILABLE",
    "ORACLE_FAILED",
    "ORACLE_MODES",
    "OracleOutcome",
    "EMPTY_ORACLE",
    "run_oracle",
    "oracle_rows",
    "oracle_comparison_rows",
]

ORACLE_EMPTY = "empty"
ORACLE_OK = "ok"
ORACLE_UNAVAILABLE = "unavailable"
ORACLE_FAILED = "failed"

#: The expansion treatments CEA can be asked for, with what each one means for
#: a comparison against RocketForge.
#:
#: None of them is like-for-like. CEA is calorically imperfect in every mode --
#: cp varies with temperature even when the composition is frozen -- while
#: RocketForge v1 holds gamma and R constant through the expansion. The closest
#: is frozen-at-chamber, where at least the composition assumption matches, and
#: the note says so instead of letting a reader infer it.
ORACLE_MODES: tuple[dict[str, str], ...] = (
    {"key": "equilibrium", "label": "Equilibrium (shifting)",
     "note": "Composition re-solved at every station. The upper bracket, and "
             "the mode CEA is usually quoted in."},
    {"key": "frozen", "label": "Frozen at chamber",
     "note": "Composition held at the chamber value. The closest of the three "
             "to RocketForge's constant-composition model, though CEA remains "
             "calorically imperfect, so the residual is still a model "
             "difference and not an error."},
    {"key": "frozen_at_throat", "label": "Frozen at throat",
     "note": "Equilibrium to the throat, frozen thereafter. The lower "
             "bracket for a real expansion."},
)


@dataclass(frozen=True, slots=True)
class OracleOutcome:
    """One native provider performance run, or one completed refusal.

    Deliberately **not** an ``IdealRocketPerformance``. It carries plain floats
    under their own names, so there is no object here that could be handed to
    something expecting a RocketForge result.
    """

    kind: str
    case: ChamberCase | None = None
    area_ratio: float | None = None
    mode: str = ""
    characteristic_velocity: float | None = None
    thrust_coefficient: float | None = None
    specific_impulse: float | None = None
    specific_impulse_vacuum: float | None = None
    provider: str = ""
    reference_condition: str = ""
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.kind == ORACLE_OK

    @property
    def status_label(self) -> str:
        return {
            ORACLE_EMPTY: "Not run",
            ORACLE_OK: "Provider result",
            ORACLE_UNAVAILABLE: "Provider unavailable",
            ORACLE_FAILED: "Provider run failed",
        }.get(self.kind, "Unknown")


EMPTY_ORACLE = OracleOutcome(kind=ORACLE_EMPTY)

#: What CEA's printed Cf and Isp columns are referenced to.
#:
#: Measured on the v3 provider in Phase 5E rather than assumed: across all
#: three chemistry modes, ``Cf + (p_e/p_c)*epsilon`` reproduces ``Ivac/c*`` to
#: between 6e-09 and 4e-07. Comparing a vacuum figure against them would be
#: high by the entire pressure term -- 5.6 % on a LOX/LH2 case at Ae/At 40.
REFERENCE_CONDITION = ("optimum expansion, p_e = p_a. The vacuum value is "
                       "reported separately.")


def run_oracle(case: ChamberCase, area_ratio: float,
               mode: str = "equilibrium") -> OracleOutcome:
    """Ask the provider for its own performance. Never raises.

    **This runs a provider solve.** It is called only from an explicit user
    action, never from a nozzle input change, which is what keeps the
    zero-chemistry-re-solve property of the performance chain intact.
    """
    from .thermochemistry_provider import PROVIDER_LABEL, availability, chamber_provider

    status = availability()
    if not status.usable:
        return OracleOutcome(
            kind=ORACLE_UNAVAILABLE, case=case, area_ratio=area_ratio,
            mode=mode, provider=PROVIDER_LABEL,
            message=status.detail or
                    f"{PROVIDER_LABEL} is not available in this build, so no "
                    f"independent performance figure can be shown. "
                    f"RocketForge's own result above does not depend on it.")

    try:
        from rocketforge.physics.thermochemistry import ExpansionMode

        expansion = ExpansionMode(mode)
    except ValueError:
        return OracleOutcome(
            kind=ORACLE_FAILED, case=case, area_ratio=area_ratio, mode=mode,
            provider=PROVIDER_LABEL,
            message=f"{mode!r} is not an expansion mode this provider offers.")

    try:
        provider = chamber_provider()
        request = build_request(case)
        native = provider.rocket_oracle(request, area_ratio=area_ratio,
                                        expansion_mode=expansion)
    except Exception as error:  # noqa: BLE001 - the panel reports, never crashes
        return OracleOutcome(
            kind=ORACLE_FAILED, case=case, area_ratio=area_ratio, mode=mode,
            provider=PROVIDER_LABEL,
            message=f"{type(error).__name__}: {error}")

    from rocketforge.core.constants import STANDARD_GRAVITY

    return OracleOutcome(
        kind=ORACLE_OK, case=case, area_ratio=float(area_ratio), mode=mode,
        characteristic_velocity=float(native.c_star),
        thrust_coefficient=float(native.thrust_coefficient),
        specific_impulse=float(native.specific_impulse) / STANDARD_GRAVITY,
        specific_impulse_vacuum=(float(native.specific_impulse_vacuum)
                                 / STANDARD_GRAVITY),
        provider=PROVIDER_LABEL,
        reference_condition=REFERENCE_CONDITION,
        detail={"stations": len(native.stations),
                "species": len(native.species_set)})


def oracle_rows(outcome: OracleOutcome) -> tuple[dict[str, Any], ...]:
    """The provider's numbers, labelled as the provider's."""
    if not outcome.ok:
        return ()
    return (
        {"key": "c_star", "label": "Characteristic velocity  c*", "unit": "m/s",
         "value": outcome.characteristic_velocity},
        {"key": "cf", "label": "Thrust coefficient  Cf", "unit": "",
         "value": outcome.thrust_coefficient},
        {"key": "isp", "label": "Specific impulse  Isp", "unit": "s",
         "value": outcome.specific_impulse},
        {"key": "isp_vacuum", "label": "Specific impulse  Isp, vacuum",
         "unit": "s", "value": outcome.specific_impulse_vacuum},
    )


def oracle_comparison_rows(rocketforge: dict[str, float | None],
                           outcome: OracleOutcome
                           ) -> tuple[dict[str, Any], ...]:
    """RocketForge beside the provider, each row at a matched reference.

    Two rules, and both of them are about not producing a misleading per cent.

    **The reference condition is matched per row.** The provider quotes Cf and
    Isp at optimum expansion and reports a vacuum Isp separately, so each row
    names the condition and expects a RocketForge value evaluated at the same
    one. Placing a vacuum figure beside an optimum-expansion figure is wrong by
    the entire pressure term, which on a LOX/LH2 case at Ae/At 40 is 5.6 % --
    larger than any model difference this table exists to show.

    **Every residual is a model difference, never an error.** The two
    calculations do not share a model: RocketForge holds gamma and R constant
    through the expansion, and the provider is calorically imperfect in every
    mode it offers. No setting of either makes them the same calculation.

    ``rocketforge`` is keyed by this function's own row keys, so a caller that
    has not evaluated a reference condition simply omits it and the row reports
    the gap instead of comparing the wrong number.
    """
    if not outcome.ok:
        return ()
    specification = (
        ("c_star", "Characteristic velocity  c*", "m/s",
         outcome.characteristic_velocity,
         "chamber quantity — no expansion reference applies"),
        ("cf_optimum", "Thrust coefficient  Cf", "",
         outcome.thrust_coefficient, "both at optimum expansion, p_a = p_e"),
        ("isp_optimum", "Specific impulse  Isp", "s",
         outcome.specific_impulse, "both at optimum expansion, p_a = p_e"),
        ("isp_vacuum", "Specific impulse  Isp, vacuum", "s",
         outcome.specific_impulse_vacuum, "both in vacuum, p_a = 0"),
    )
    rows = []
    for key, label, unit, provider_value, reference in specification:
        own = rocketforge.get(key)
        if own is None or provider_value is None or provider_value == 0.0:
            difference = None
        else:
            difference = (float(own) - float(provider_value)) / abs(
                float(provider_value))
        rows.append({
            "key": key, "label": label, "unit": unit,
            "rocketforge": own, "provider": provider_value,
            "difference": difference, "reference": reference,
            "kind": "model difference",
        })
    return tuple(rows)
