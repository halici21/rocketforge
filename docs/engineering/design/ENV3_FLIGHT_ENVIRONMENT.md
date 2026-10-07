# ENV-3 — Flight environment foundation

ENV-3 adds the point-state layer between an `AtmosphereState` (ENV-1) and
future trajectory and aerodynamics work. You give it an atmosphere state and
explicit flight conditions, and it returns these quantities, each with its
relation or the reason it is not defined:
- local gravity;
- the air-relative speed;
- Mach number;
- dynamic pressure;
- Reynolds number.

It integrates no trajectory and computes no force, coefficient or loss.

## Where it lives

| Part | Location | Layer |
| --- | --- | --- |
| Spherical gravity model, WGS 84 constants | `rocketforge/physics/flight/gravity.py` | physics |
| `FlightEnvironment`, `flight_environment()`, `standard_flight_environment()` | `rocketforge/physics/flight/environment.py` | physics |

The package imports only `core` and `physics.atmosphere`. It knows nothing
about engines, vehicles, providers or Qt. A test checks the imports, and a
subprocess test checks that a calculation loads no provider, engine,
application or Qt module.

## Inputs

| Input | Unit | Contract |
| --- | --- | --- |
| `atmosphere` | — | A resolved `AtmosphereState`: manual, vacuum or a model. It owns every gas property. |
| `air_speed` | m/s | Speed **relative to the local air**, a magnitude ≥ 0. Negative, NaN, ±∞, `bool` and text are refused (`AIR_SPEED_INVALID`). |
| `geometric_altitude` | m | Above mean sea level, used for gravity. A state resolved at an altitude carries one: a stated altitude must equal it (`ALTITUDE_MISMATCH`), and an omitted one is taken from it. Its source is recorded (`stated` / `atmosphere`). Allowed from −5 000 m up (`ALTITUDE_OUT_OF_RANGE` below). |
| `characteristic_length` | m | Optional. > 0 and finite, otherwise refused (`CHARACTERISTIC_LENGTH_INVALID`). Only the Reynolds number uses it. |
| `gravity_model` | — | A `SphericalGravity`. The default is `WGS84_SPHERICAL`. |

**Air-relative speed, not ground or inertial speed.** The physics takes
only the speed relative to the air and never converts another speed. Winds
are not modelled. A future application or UI caller that has only a ground or
inertial speed must state its zero-wind assumption itself, at its own
boundary.

## Relations

| Quantity | Relation | Needs |
| --- | --- | --- |
| r | R + Z | altitude |
| g | GM / r² | altitude |
| M | V_air / a | speed of sound `a` from the state |
| q | ρ V_air² / 2 | density `ρ` from the state |
| Re | ρ V_air L / μ | `ρ`, viscosity `μ` from the state, and `L` |

### Gravity: spherical WGS 84 baseline

The constants come from NGA.STND.0036_1.0.0_WGS84 (2014), Table 3.1:
- GM = 3.986004418 × 10¹⁴ m³/s², including the atmosphere;
- reference radius R = a = 6 378 137 m.

At Z = 0 this gives g = 9.798285 m/s², the pure attraction at the equatorial
radius. There is no latitude, J2/oblateness, rotation or centrifugal term.
Real surface gravity, rotation included, runs from 9.780 m/s² at the equator
to 9.832 m/s² at the poles.

Two similar-looking values are deliberately not used:
- **g0 = 9.80665 m/s²** is a defined convention for weight and Isp.
- **USSA76 r0 = 6 356 766 m** is the Standard's effective radius for its own
  hydrostatics (eq. 17).

The atmosphere keeps its own internal gravity. The flight layer does not
reuse it, and the atmosphere does not use this one.

The lower bound, −5 000 m, is the lowest altitude any atmosphere in this
build reaches. Below it there is no flight condition, and the point-mass law
does not hold inside the Earth. There is no upper bound: the inverse-square
law holds outside the Earth.

## Undefined quantities stay undefined

Each derived quantity is either valued or listed in `unavailable` with a
reason, never both and never neither. The reason quotes the atmosphere's own
reason for the missing ingredient.

| Atmosphere | g | M | q | Re |
| --- | --- | --- | --- | --- |
| USSA76, Z ≤ 86 km | ✓ | ✓ | ✓ | ✓ with L |
| USSA76, 86 km < Z ≤ 1000 km | ✓ | — (no speed of sound above 86 km, §1.3.10) | ✓ | — (no viscosity above 86 km, §1.3.11) |
| Vacuum | with stated Z | — (no gas) | 0 | — (no gas) |
| Manual pressure | with stated Z | — | — | — |

- **q above 86 km is given.** It is the free-stream momentum flux and needs
  only density, which the Standard defines to 1000 km. It is not a
  continuum quantity.
- **Mach and Re above 86 km are not given.** They need a speed of sound and
  a viscosity, which the Standard does not define there.
- **At exactly 86 km the state defines both**, so M and Re are given. One
  millimetre above, they are not.
- **Vacuum.** Zero density makes q = 0, which is true. No continuum property
  is invented to produce a Mach or Reynolds number of zero.

## Records and provenance

`FlightEnvironment.to_dict()` writes `rocketforge.flight-environment`,
version 1. The record carries the SI-suffixed fields (`gravity_m_s2`,
`dynamic_pressure_Pa`, …), and also:
- `unavailable`, the reasons;
- `provenance`, the relation per quantity plus the scope;
- the full gravity model, with its constants and source;
- the full atmosphere state record.

`from_dict` validates and round-trips exactly. Results are deterministic and
closed-form, so no solver or provider is reached.

## Verified

Oracles independent of the implementation:
- **Gravity** from the WGS 84 constants in exact rational arithmetic. The
  inverse-square ratio is closed across −5 km to 1000 km.
- **Mach, q and Re at 0, 11 and 20 km**, against Table I's printed Cs, ρ and
  μ, within their printed rounding.
- **A dense grid** of 28 175 points: −5 km to 1000 km every 250 m, both sides
  of 80 and 86 km, and seven speeds up to 11.2 km/s.
  - Gravity falls strictly.
  - M and Re are defined exactly where Z ≤ 86 km. They agree with eqs. 50/51
    recomputed from the state's temperatures.
  - q scales with ρV², M with V, and Re with ρ, V and L.

## Not in ENV-3

- **Mean free path and Knudsen number.** They would need the Standard's mean
  collision diameter σ. Its Table 2 value is among the scan's known misprints
  (NASA STI errata), and the defining text was not available to check it
  against. A continuum-regime criterion is also a judgement for the
  aerodynamics that will consume it. Future work.
- **Out of scope:**
  - drag and lift forces, and Cd/Cl models;
  - Max-Q search;
  - trajectory integration;
  - gravity, drag and steering losses;
  - Earth rotation and winds;
  - latitude or J2 gravity, and orbit propagation;
  - re-entry and heating;
  - free-molecular aerodynamics;
  - NRLMSIS, Earth-GRAM and DTM2020 (ENV-2 is deferred on rights);
  - any UI page.
