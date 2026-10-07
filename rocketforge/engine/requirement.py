"""The liquid-engine requirement: what engine is wanted, before any of it is sized.

LIQ-2. A requirement is **engineering intent**, recorded honestly. It states a
target thrust in a stated design environment for a stated burn time, and the
preferences a designer has (or has not yet formed) about the propellant pair,
the chamber pressure, the mixture ratio, the feed architecture and -- for a
pump-fed engine -- the power cycle. It computes nothing and solves nothing.

Three rules shape this module:

* **"Auto" is an open decision, never a hidden one.** An ``AUTO`` preference
  means the choice is deliberately left to a later stage of design. Nothing here
  resolves it, ranks candidates or recommends a value, and :meth:`open_decisions`
  lists every one still open so an interface can say so.
* **Feed architecture and power cycle are different questions.** How propellant
  is pressurised (tank pressure, or pumps) is the feed architecture. How the
  pumps are powered is the cycle, and only a pump-fed engine has one. A
  pressure-fed engine therefore has *no* cycle -- not a "pressure-fed cycle" --
  and a cycle preference on anything but a pump-fed engine is refused.
* **A propellant pair is referenced, never copied.** The requirement holds the
  LIQ-1 preset key. What that pair *is* -- its reactants, its source O/F, or
  why it is blocked -- stays in the catalogue that owns it, and the application
  layer checks the key against that catalogue. This layer cannot import it and
  does not need to.

The design environment is stated as one of: a manual (custom) ambient
pressure, vacuum, the standard sea-level pressure, or an altitude in a named
standard atmosphere model (ENV-1). Vacuum and sea level stay named pressures,
not altitudes. An altitude is **intent**: this module records it and checks
that it is stated, but resolves nothing, because a requirement computes
nothing. The pressure an altitude resolves to comes from
:mod:`rocketforge.physics.atmosphere`, through the application layer's
``environment_service``. Nothing here restates an atmosphere equation.

Units are SI throughout: N, Pa, s. Display units belong to ``application``.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Final

__all__ = [
    "SCHEMA",
    "SCHEMA_VERSION",
    "STANDARD_SEA_LEVEL_PRESSURE",
    "DEFAULT_ATMOSPHERE_MODEL",
    "AmbientMode",
    "AmbientNotResolvedHere",
    "ChamberPressureMode",
    "ChamberPressurePreference",
    "CyclePreference",
    "DesignEnvironment",
    "DesignPriority",
    "EngineRequirement",
    "FeedArchitecture",
    "MixtureRatioMode",
    "MixtureRatioPreference",
    "PropellantMode",
    "PropellantPreference",
    "RequirementFormatError",
    "RequirementIssue",
    "validate_requirement",
]

#: Identifies a serialised requirement, so a payload of some other kind is
#: refused rather than half-read.
SCHEMA: Final = "rocketforge.liquid-engine-requirement"

#: Bumped only when the serialised shape changes incompatibly.
SCHEMA_VERSION: Final = 1

#: Standard sea-level atmospheric pressure, in Pa. Exact by definition: the
#: standard atmosphere is 101 325 Pa (10th CGPM, 1954; ISO 2533:1975). The same
#: value Rocket Performance names "sea level".
STANDARD_SEA_LEVEL_PRESSURE: Final = 101325.0

#: The atmosphere model an altitude is read in unless another is named: the
#: U.S. Standard Atmosphere, 1976. A key only; the model is
#: ``rocketforge.physics.atmosphere``'s, and a test holds the two equal.
DEFAULT_ATMOSPHERE_MODEL: Final = "ussa1976"


class RequirementFormatError(ValueError):
    """A serialised requirement that cannot be read as one.

    Raised for structure -- an unknown schema, a missing section, a value that
    is not one of an enumeration's members. An *incomplete* or inconsistent
    requirement is not a format error; it reads back as written and
    :func:`validate_requirement` says what is wrong with it.
    """


class AmbientNotResolvedHere(ValueError):
    """An altitude environment's pressure was asked of the requirement itself.

    It is resolved through an atmosphere model, outside this layer
    (``application.analysis.environment_service``). Raising rather than
    guessing means no caller can read a wrong pressure silently.
    """


# ---------------------------------------------------------------------------
# the vocabulary
# ---------------------------------------------------------------------------


class AmbientMode(StrEnum):
    """Where the design ambient pressure comes from."""

    VACUUM = "vacuum"
    SEA_LEVEL = "sea_level"
    CUSTOM = "custom"                            # a manual ambient pressure
    STANDARD_ATMOSPHERE = "standard_atmosphere"  # an altitude in a named model (ENV-1)


class PropellantMode(StrEnum):
    AUTO = "auto"            # the pair is an open decision
    EXPLICIT = "explicit"    # one LIQ-1 catalogue pair, by key


class ChamberPressureMode(StrEnum):
    AUTO = "auto"                  # an open decision
    TARGET = "target"              # design at this chamber pressure
    UPPER_LIMIT = "upper_limit"    # any chamber pressure up to this one


class MixtureRatioMode(StrEnum):
    AUTO = "auto"                      # an open decision
    PAIR_REFERENCE = "pair_reference"  # the selected pair's catalogue O/F
    EXPLICIT = "explicit"              # this O/F, by mass


class FeedArchitecture(StrEnum):
    """How propellant reaches the chamber at pressure. Not a power cycle."""

    AUTO = "auto"
    PRESSURE_FED = "pressure_fed"
    PUMP_FED = "pump_fed"


class CyclePreference(StrEnum):
    """How a pump-fed engine powers its pumps. Recorded intent only.

    No cycle is modelled in LIQ-2: there is no power balance, no gas generator
    or preburner, and no feasibility check. Full-flow staged combustion is a
    member like the others -- an intent a designer can record -- and has no
    model behind it in this build either.
    """

    AUTO = "auto"
    GAS_GENERATOR = "gas_generator"
    EXPANDER = "expander"
    STAGED_COMBUSTION = "staged_combustion"
    FULL_FLOW_STAGED_COMBUSTION = "full_flow_staged_combustion"


class DesignPriority(StrEnum):
    """What the designer says matters most. A label, never a weight.

    Nothing ranks propellants or cycles by it in LIQ-2; it records intent for
    the trade study that will.
    """

    UNSTATED = "unstated"
    SPECIFIC_IMPULSE = "specific_impulse"
    DENSITY_IMPULSE = "density_impulse"
    STORABILITY = "storability"
    SIMPLICITY = "simplicity"


# ---------------------------------------------------------------------------
# the parts
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DesignEnvironment:
    """Where the requirement's thrust is stated, resolved to an ambient pressure.

    ``custom_pressure`` is read only in ``CUSTOM`` mode, and ``altitude`` (m,
    geometric) and ``atmosphere_model`` only in ``STANDARD_ATMOSPHERE`` mode.
    Each is kept otherwise, so switching to "vacuum" and back does not lose
    what was typed.
    """

    mode: AmbientMode = AmbientMode.SEA_LEVEL
    custom_pressure: float = STANDARD_SEA_LEVEL_PRESSURE
    altitude: float | None = None                 # m, geometric
    atmosphere_model: str = DEFAULT_ATMOSPHERE_MODEL

    @property
    def is_altitude(self) -> bool:
        """Whether the pressure is resolved from an altitude in a model."""
        return self.mode is AmbientMode.STANDARD_ATMOSPHERE

    @property
    def ambient_pressure(self) -> float:
        """The stated design ambient pressure, in Pa: vacuum, sea level or custom.

        An altitude environment raises :class:`AmbientNotResolvedHere`: its
        pressure comes from an atmosphere model, which this layer does not
        reach. Read it through ``environment_service.ambient_pressure``.
        """
        if self.mode is AmbientMode.VACUUM:
            return 0.0
        if self.mode is AmbientMode.SEA_LEVEL:
            return STANDARD_SEA_LEVEL_PRESSURE
        if self.mode is AmbientMode.CUSTOM:
            return float(self.custom_pressure)
        raise AmbientNotResolvedHere(
            "An altitude environment is resolved through an atmosphere model; read "
            "its pressure through application.analysis.environment_service.")

    def to_dict(self) -> dict[str, Any]:
        """The record. Altitude and model appear only once an altitude is in
        use, so a record without one is byte-identical to the pre-ENV-1 form."""
        record: dict[str, Any] = {"mode": self.mode.value,
                                  "custom_pressure_Pa": self.custom_pressure}
        if self.mode is AmbientMode.STANDARD_ATMOSPHERE or self.altitude is not None:
            record["altitude_m"] = self.altitude
            record["atmosphere_model"] = self.atmosphere_model
        return record


@dataclass(frozen=True, slots=True)
class PropellantPreference:
    """An open decision, or one LIQ-1 catalogue pair named by its key."""

    mode: PropellantMode = PropellantMode.AUTO
    pair_key: str = ""

    @property
    def is_explicit(self) -> bool:
        return self.mode is PropellantMode.EXPLICIT


@dataclass(frozen=True, slots=True)
class ChamberPressurePreference:
    """An open decision, a target, or an upper limit. ``value`` in Pa."""

    mode: ChamberPressureMode = ChamberPressureMode.AUTO
    value: float | None = None


@dataclass(frozen=True, slots=True)
class MixtureRatioPreference:
    """An open decision, the selected pair's catalogue O/F, or an O/F by mass.

    ``PAIR_REFERENCE`` stores no number: the O/F is the catalogue's, looked up
    when it is needed, so a requirement can never carry a stale copy of it.
    """

    mode: MixtureRatioMode = MixtureRatioMode.AUTO
    value: float | None = None


@dataclass(frozen=True, slots=True)
class RequirementIssue:
    """One reason a requirement is incomplete or inconsistent."""

    code: str
    field: str
    message: str


# ---------------------------------------------------------------------------
# the requirement
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EngineRequirement:
    """One liquid-engine requirement / design point. Immutable.

    Attributes:
        thrust: Target thrust at the design environment, in N, or ``None``
            while not yet stated.
        environment: Where that thrust is required.
        burn_time: Required burn duration, in s, or ``None``.
        propellant: The pair, or an open decision.
        chamber_pressure: The chamber-pressure intent.
        mixture_ratio: The O/F intent.
        feed: The feed architecture.
        cycle: The pump power cycle. ``None`` unless ``feed`` is pump-fed:
            only a pump-fed engine has one. Use :meth:`with_feed` to change
            the feed so the two stay consistent.
        priority: What matters most, if the designer has said.
        name: A display name. Not part of the requirement's identity.
    """

    thrust: float | None = None
    environment: DesignEnvironment = DesignEnvironment()
    burn_time: float | None = None
    propellant: PropellantPreference = PropellantPreference()
    chamber_pressure: ChamberPressurePreference = ChamberPressurePreference()
    mixture_ratio: MixtureRatioPreference = MixtureRatioPreference()
    feed: FeedArchitecture = FeedArchitecture.AUTO
    cycle: CyclePreference | None = None
    priority: DesignPriority = DesignPriority.UNSTATED
    name: str = ""

    def replace(self, **changes: Any) -> "EngineRequirement":
        return replace(self, **changes)

    def with_feed(self, feed: FeedArchitecture) -> "EngineRequirement":
        """The same requirement with another feed architecture.

        Entering pump-fed opens the cycle as an open decision (``AUTO``);
        leaving it removes the cycle, because a pressure-fed engine -- or one
        whose feed is itself undecided -- has no pump to power. A cycle
        preference is never silently kept where it cannot apply.
        """
        feed = FeedArchitecture(feed)
        if feed is self.feed:
            return self
        cycle = CyclePreference.AUTO if feed is FeedArchitecture.PUMP_FED else None
        return replace(self, feed=feed, cycle=cycle)

    def issues(self) -> tuple[RequirementIssue, ...]:
        return validate_requirement(self)

    @property
    def is_complete(self) -> bool:
        """Every required quantity is stated and every preference consistent.

        Open decisions do not make a requirement incomplete: "propellant to
        be decided" is a complete statement of intent.
        """
        return not self.issues()

    def open_decisions(self) -> tuple[str, ...]:
        """The fields whose choice is deliberately left to later design."""
        open_: list[str] = []
        if self.propellant.mode is PropellantMode.AUTO:
            open_.append("propellant")
        if self.chamber_pressure.mode is ChamberPressureMode.AUTO:
            open_.append("chamber_pressure")
        if self.mixture_ratio.mode is MixtureRatioMode.AUTO:
            open_.append("mixture_ratio")
        if self.feed is FeedArchitecture.AUTO:
            open_.append("feed")
        if self.cycle is CyclePreference.AUTO:
            open_.append("cycle")
        return tuple(open_)

    # -- serialisation -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """A JSON-shaped record of the whole requirement, name included."""
        return {
            "schema": SCHEMA,
            "version": SCHEMA_VERSION,
            "name": self.name,
            "thrust_N": self.thrust,
            "environment": self.environment.to_dict(),
            "burn_time_s": self.burn_time,
            "propellant": {"mode": self.propellant.mode.value,
                           "pair_key": self.propellant.pair_key},
            "chamber_pressure": {"mode": self.chamber_pressure.mode.value,
                                 "value_Pa": self.chamber_pressure.value},
            "mixture_ratio": {"mode": self.mixture_ratio.mode.value,
                              "value": self.mixture_ratio.value},
            "feed": self.feed.value,
            "cycle": None if self.cycle is None else self.cycle.value,
            "priority": self.priority.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EngineRequirement":
        """Read a record written by :meth:`to_dict`.

        Structure is checked strictly; content is not judged here. A record
        that says pressure-fed with a gas-generator cycle reads back exactly
        as written, and :func:`validate_requirement` reports it -- rewriting
        it on load would hide what the file says.
        """
        if not isinstance(payload, Mapping):
            raise RequirementFormatError("a requirement record must be a mapping")
        if payload.get("schema") != SCHEMA:
            raise RequirementFormatError(
                f"not a liquid-engine requirement (schema {payload.get('schema')!r})")
        if payload.get("version") != SCHEMA_VERSION:
            raise RequirementFormatError(
                f"requirement version {payload.get('version')!r} is not "
                f"supported; this build reads version {SCHEMA_VERSION}")
        try:
            environment = _section(payload, "environment")
            propellant = _section(payload, "propellant")
            chamber = _section(payload, "chamber_pressure")
            ratio = _section(payload, "mixture_ratio")
            cycle = payload.get("cycle")
            return cls(
                thrust=_optional_number(payload.get("thrust_N"), "thrust_N"),
                environment=DesignEnvironment(
                    mode=AmbientMode(environment["mode"]),
                    custom_pressure=_number(environment["custom_pressure_Pa"],
                                            "environment.custom_pressure_Pa"),
                    altitude=_optional_number(environment.get("altitude_m"),
                                              "environment.altitude_m"),
                    atmosphere_model=_text(
                        environment.get("atmosphere_model", DEFAULT_ATMOSPHERE_MODEL),
                        "environment.atmosphere_model")),
                burn_time=_optional_number(payload.get("burn_time_s"), "burn_time_s"),
                propellant=PropellantPreference(
                    mode=PropellantMode(propellant["mode"]),
                    pair_key=_text(propellant.get("pair_key", ""), "propellant.pair_key")),
                chamber_pressure=ChamberPressurePreference(
                    mode=ChamberPressureMode(chamber["mode"]),
                    value=_optional_number(chamber.get("value_Pa"),
                                           "chamber_pressure.value_Pa")),
                mixture_ratio=MixtureRatioPreference(
                    mode=MixtureRatioMode(ratio["mode"]),
                    value=_optional_number(ratio.get("value"), "mixture_ratio.value")),
                feed=FeedArchitecture(payload["feed"]),
                cycle=None if cycle is None else CyclePreference(cycle),
                priority=DesignPriority(payload.get("priority", "unstated")),
                name=_text(payload.get("name", ""), "name"),
            )
        except KeyError as missing:
            raise RequirementFormatError(f"requirement record lacks {missing}") from None
        except ValueError as error:
            if isinstance(error, RequirementFormatError):
                raise
            raise RequirementFormatError(str(error)) from None

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False,
                          allow_nan=False) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "EngineRequirement":
        try:
            payload = json.loads(text)
        except (TypeError, ValueError) as error:
            raise RequirementFormatError(f"not valid JSON: {error}") from None
        return cls.from_dict(payload)

    def canonical(self) -> dict[str, Any]:
        """The engineering content, without the display name.

        Two requirements that differ only by name are the same requirement,
        exactly as a renamed trade study is the same study.
        """
        record = self.to_dict()
        del record["name"]
        return record

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True,
                             separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def _positive(value: float | None) -> bool:
    return value is not None and math.isfinite(value) and value > 0.0


def validate_requirement(requirement: EngineRequirement) -> tuple[RequirementIssue, ...]:
    """Every reason the requirement is incomplete or inconsistent, in form order.

    Empty means complete. Open ("Auto") decisions are not issues. Catalogue
    membership of the propellant key is checked by the application layer,
    which alone can see the catalogue.
    """
    issues: list[RequirementIssue] = []

    def add(code: str, field: str, message: str) -> None:
        issues.append(RequirementIssue(code, field, message))

    if requirement.thrust is None:
        add("THRUST_MISSING", "thrust", "State the target thrust.")
    elif not _positive(requirement.thrust):
        add("THRUST_INVALID", "thrust", "Target thrust must be a finite value above zero.")

    environment = requirement.environment
    ambient_ok = True
    if environment.mode is AmbientMode.CUSTOM:
        pressure = environment.custom_pressure
        if not (math.isfinite(pressure) and pressure >= 0.0):
            ambient_ok = False
            add("AMBIENT_PRESSURE_INVALID", "environment",
                "A custom ambient pressure must be finite and at or above zero. "
                "Zero is vacuum.")
    elif environment.is_altitude:
        # Stated-ness only. The model's range and the chamber-versus-ambient
        # check need the resolved pressure, and are the application layer's.
        ambient_ok = False
        if environment.altitude is None:
            add("ALTITUDE_MISSING", "environment", "State the design altitude.")
        elif not math.isfinite(environment.altitude):
            add("ALTITUDE_INVALID", "environment", "The design altitude must be finite.")
        if not environment.atmosphere_model.strip():
            add("ATMOSPHERE_MODEL_MISSING", "environment",
                "Name the atmosphere model the altitude is read in.")

    if requirement.burn_time is None:
        add("BURN_TIME_MISSING", "burn_time", "State the required burn time.")
    elif not _positive(requirement.burn_time):
        add("BURN_TIME_INVALID", "burn_time", "Burn time must be a finite value above zero.")

    propellant = requirement.propellant
    if propellant.is_explicit and not propellant.pair_key.strip():
        add("PROPELLANT_PAIR_MISSING", "propellant",
            "Choose a propellant pair, or leave the pair as Auto.")

    chamber = requirement.chamber_pressure
    if chamber.mode is not ChamberPressureMode.AUTO:
        if chamber.value is None:
            add("CHAMBER_PRESSURE_MISSING", "chamber_pressure",
                "State the chamber pressure, or leave it as Auto.")
        elif not _positive(chamber.value):
            add("CHAMBER_PRESSURE_INVALID", "chamber_pressure",
                "A chamber-pressure target or limit must be a finite value above zero.")
        elif ambient_ok and chamber.value <= environment.ambient_pressure:
            word = "target" if chamber.mode is ChamberPressureMode.TARGET else "limit"
            add("CHAMBER_PRESSURE_NOT_ABOVE_AMBIENT", "chamber_pressure",
                f"The chamber-pressure {word} is not above the design ambient "
                "pressure; a chamber at or below ambient cannot expel its flow.")

    ratio = requirement.mixture_ratio
    if ratio.mode is MixtureRatioMode.EXPLICIT:
        if ratio.value is None:
            add("MIXTURE_RATIO_MISSING", "mixture_ratio",
                "State the O/F, or leave it as Auto.")
        elif not _positive(ratio.value):
            add("MIXTURE_RATIO_INVALID", "mixture_ratio",
                "An explicit O/F must be a finite value above zero.")
    if ratio.mode is MixtureRatioMode.PAIR_REFERENCE and not propellant.is_explicit:
        add("MIXTURE_RATIO_REFERENCE_WITHOUT_PAIR", "mixture_ratio",
            "The pair's reference O/F needs an explicit propellant pair.")

    if requirement.feed is FeedArchitecture.PUMP_FED:
        if requirement.cycle is None:
            add("CYCLE_MISSING", "cycle",
                "A pump-fed engine needs a cycle preference, even if it is Auto.")
    elif requirement.cycle is not None:
        add("CYCLE_WITHOUT_PUMP_FEED", "cycle",
            "Only a pump-fed engine has a power cycle; this feed architecture has none.")

    return tuple(issues)


# ---------------------------------------------------------------------------
# reading helpers
# ---------------------------------------------------------------------------


def _section(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload[key]
    if not isinstance(value, Mapping):
        raise RequirementFormatError(f"requirement field {key!r} must be a mapping")
    return value


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RequirementFormatError(f"requirement field {field!r} must be a number")
    return float(value)


def _optional_number(value: Any, field: str) -> float | None:
    return None if value is None else _number(value, field)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise RequirementFormatError(f"requirement field {field!r} must be text")
    return value
