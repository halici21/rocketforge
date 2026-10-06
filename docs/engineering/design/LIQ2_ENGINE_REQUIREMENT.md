# LIQ-2 — Engine requirement and design point

LIQ-2 records what liquid rocket engine is wanted before any of it is designed:
a target thrust in a design environment, a burn time, and the designer's
preferences about the propellant pair, chamber pressure, O/F, feed architecture
and power cycle. It captures intent. It sizes nothing, trades nothing and
solves nothing.

## Where it lives

| Part | Location |
| --- | --- |
| Domain model, validation, JSON record | `rocketforge/engine/requirement.py` |
| Catalogue check, option labels, display units, summary | `rocketforge/application/analysis/engine_requirement_service.py` |
| QML singleton `EngineRequirement` | `rocketforge/application/analysis/engine_requirement_controller.py` |
| Page (rail family **Liquid Engine**, `ENG`) | `ui/pages/EngineRequirementPage.qml` |

The domain module imports only the standard library. It sits in `engine` (L3,
whole-engine questions) because a requirement is about the engine, not one
component.

## What a requirement holds

| Field | Values | Stored as |
| --- | --- | --- |
| Target thrust | stated or not | N |
| Design environment | sea level, vacuum, custom ambient pressure | Pa |
| Burn time | stated or not | s |
| Propellant pair | Auto, or one LIQ-1 catalogue pair | the preset key |
| Chamber pressure | Auto, target, upper limit | Pa |
| O/F | Auto, pair reference, explicit | mass ratio, or no number |
| Feed architecture | Auto, pressure-fed, pump-fed | — |
| Power cycle | Auto, gas generator, expander, staged combustion, full-flow staged combustion | only when pump-fed |
| Design priority | not stated, specific impulse, density impulse, storable propellants, simplicity | a label |

## Decisions

- **The environment is an ambient pressure.** RocketForge has no validated
  atmosphere model, so an altitude would be a number the program cannot turn
  into a pressure honestly. Sea level is 101 325 Pa and vacuum is 0, the same
  names Rocket Performance uses.
- **Auto is an open decision.** It is never resolved, ranked or recommended.
  The page lists every open decision, and open decisions do not make a
  requirement incomplete.
- **Feed and cycle are separate.** A pressure-fed engine has no cycle, not a
  "pressure-fed cycle". The cycle exists only when the feed is pump-fed:
  choosing pump-fed opens it as Auto, and leaving pump-fed removes it. A record
  that pairs a cycle with another feed loads as written and is reported
  (`CYCLE_WITHOUT_PUMP_FEED`), never repaired.
- **Every cycle is recorded intent.** No cycle has a model in this build.
  Full-flow staged combustion is a member like the others, and its note says
  that no full-flow model, preburner or power balance exists.
- **The pair is referenced, not copied.** The requirement stores the LIQ-1
  preset key. The application resolves it to the catalogue's own
  `BipropellantPreset`. Unknown keys and the blocked RFNA pairs are issues.
  A pair-reference O/F stores no number. It is read from the catalogue when
  shown, so it can never go stale.
- **Chamber pressure must be above ambient.** A target or limit at or below
  the design ambient pressure is refused (`CHAMBER_PRESSURE_NOT_ABOVE_AMBIENT`).
  This is the only physical consistency rule. Nothing else is derived.

## Persistence

`EngineRequirement.to_dict` / `from_dict` write a versioned JSON record
(`schema: rocketforge.liquid-engine-requirement`, `version: 1`, SI units).
Structure is checked strictly: a wrong schema, wrong version, unknown member or
wrong type is refused. Content is not judged on load. `fingerprint` hashes the
record without the display name. The page copies and pastes the record through
the clipboard. The controller also saves and loads files.

## Verified

- `tests/engine/test_requirement_model.py`: states, validation codes,
  feed/cycle rules, full-flow staged combustion as intent, exact round trip
  (inconsistent records included), refusal of malformed records, fingerprint.
- `tests/application/test_engine_requirement.py`: catalogue reference without
  chemistry, blocked and unknown pairs, unit boundary, controller behaviour,
  file and clipboard persistence, and import boundaries.
- `tests/application/test_engine_requirement_runtime.py`: in the real
  application, every field is edited through the real QML controls, then
  copy, reset, paste, theme, size and re-entry follow. Every public function
  below `application` and every service solve entry point is counted. The
  sequence registers **zero** calls. Positive and negative controls show the
  counter works. No Qt warnings.

## Not in LIQ-2

Propellant trade or ranking, automatic cycle selection, cycle feasibility, gas
generator or preburner calculations, pump/turbine power balance, mass-flow
sizing, throat and exit areas, expansion-ratio design, chamber geometry or L*,
injector sizing, feed pressure budget, cooling, tanks, engine closure. LIQ-3
(trade studies) has not started.
