# ENV-1 — Atmosphere foundation

ENV-1 adds a reusable atmosphere capability. It provides one resolved-state
contract and the first standard model, the U.S. Standard Atmosphere, 1976. It
connects that capability to the LIQ-2 design environment, so an altitude can be
the source of a design ambient pressure. It is the foundation for later nozzle
design points, flight conditions, trajectory and drag work, and it implements
none of them.

## Where it lives

| Part | Location | Layer |
| --- | --- | --- |
| State contract, manual and vacuum states | `rocketforge/physics/atmosphere/state.py` | physics |
| U.S. Standard Atmosphere, 1976 | `rocketforge/physics/atmosphere/ussa1976.py` | physics |
| its 86–1000 km species model (ENV-1B) | `rocketforge/physics/atmosphere/ussa1976_upper.py` | physics |
| the Standard's constants, once | `rocketforge/physics/atmosphere/_ussa1976_constants.py` | physics |
| Model registry, `standard_atmosphere()` | `rocketforge/physics/atmosphere/__init__.py` | physics |
| LIQ-2 environment → resolved state | `rocketforge/application/analysis/environment_service.py` | application |
| Altitude intent in the requirement | `rocketforge/engine/requirement.py` (`DesignEnvironment`) | engine |

The atmosphere package imports only `core` and itself. It knows nothing about
engines, Qt or the network, and a test enforces this.

## The state

An `AtmosphereState` states what it came from: model identity, name and
version, inputs, regime and provenance. It carries each of these only where the
source defines them:
- pressure;
- geometric and geopotential altitude;
- kinetic and molecular-scale temperature;
- mass density, number density and mean molar mass;
- species number densities;
- speed of sound, dynamic viscosity and layer index.

A value the source does not define is `None`. When that absence has a
scientific reason, `unavailable` names the field and the reason. A field can
never be both valued and unavailable. Pressure is always defined. Record
version 2 adds these fields (ENV-1B), and version 1 records still read.

| Source | Pressure | Other quantities |
| --- | --- | --- |
| Manual | as stated (finite, ≥ 0) | none: a manual pressure is not an atmosphere |
| Vacuum | 0 | density 0. Temperature, speed of sound and viscosity are undefined. Vacuum is not a high altitude. |
| `ussa1976` at Z | eq. 33a/33b | all of them |

Resolution returns a `Solution`. A refusal carries no state, and its diagnostic
names the input that failed (`AMBIENT_PRESSURE_INVALID`, `ALTITUDE_INVALID`,
`ALTITUDE_OUT_OF_RANGE`, `ATMOSPHERE_MODEL_UNKNOWN`). Nothing is clamped. A
state round-trips through versioned JSON (`rocketforge.atmosphere-state`) with
its identity and provenance.

## U.S. Standard Atmosphere, 1976

Source: NOAA-S/T 76-1562 / NASA-TM-X-74335 (NTRS 19770009539), section 1. The
equations and constants are the Standard's own; no table is fitted or
interpolated.

- **Altitudes.** The input is geometric altitude Z. The temperature profile is
  defined in geopotential altitude, `H = r0 Z / (r0 + Z)` (eq. 18, Γ = 1). The
  two are never confused: Z = 11 000 m is H = 10 981 m′, still in layer 0
  (Table I: 216.774 K).
- **Layers.** Table 4's seven (Hb, LM,b) pairs. TM is linear in H (eq. 23),
  and P comes from 33a (LM,b ≠ 0) or 33b (LM,b = 0). Base pressures are those
  equations applied at each base, as the Standard specifies. Then
  ρ = P M0/(R* TM) (42), Cs = (γ R* TM/M0)^½ (50), and
  μ = β T^{3/2}/(T + S) (51).
- **Constants, from the defining text.** R* = 8.31432 × 10³ J/(kmol K),
  M0 = 28.9644 kg/kmol, r0 = 6 356 766 m, g0 = g0′ = 9.80665, P0 = 101 325 Pa,
  T0 = 288.15 K, γ = 1.40, β = 1.458 × 10⁻⁶, S = 110.4 K. The scan's Table 2
  has known misprints (NASA STI errata: R*, r0, S, σ), and p. 4 prints
  S = 110 K. Eq. 51's text (p. 19) and Table III both require 110.4 K. R* is
  the Standard's value, not CODATA's: the two differ by 1.7 × 10⁻⁵, and only
  the Standard's reproduces its tables.

### Supported range: −5 000 m ≤ Z ≤ 1 000 000 m (geometric)

ENV-1A stopped at 80 km. ENV-1B (below) completes the Standard to its
documented top. The values at and below 80 km are unchanged, bit for bit.

- **Lower bound.** Table I begins at Z = −5 000 m, computed from (33a) with
  b = 0.
- **Upper bound.** 1000 km: Z12, the top of the Standard's tables.

Outside the range a state is refused, and the message says nothing is
extrapolated.

## ENV-1B — the Standard from 80 km to 1000 km

Three formulations meet at the Standard's own boundaries. Each is
implemented as the Standard defines it.

| Regime | Z | Formulation | Source |
| --- | --- | --- | --- |
| lower | ≤ 80 km | hydrostatic, M = M0, T = TM | eqs. 18, 23, 33a/b |
| transition | 80–86 km | hydrostatic. M/M0 from Table 8, T = TM·M/M0 | §1.2.4, eq. 22, Table 8 |
| upper | 86–1000 km | diffusive: each species integrated | eqs. 25–40, 33c, 42 |

**Transition (80–86 km).** P, ρ and Cs depend on TM only, so they stay exact.
The Standard gives M/M0 only at 0.5 km geometric nodes (Table 8, the values
"initially selected for intervals of 0.5 geometric kilometres"). It is
interpolated linearly in Z between those nodes. M/M0 = 1 at 80 km, so the
lower atmosphere joins continuously (steps ≤ 2 × 10⁻¹⁰). The Standard's own
printed 80–86 km rows were computed without this correction (§1.2.4), so the
model's kinetic T, M, N and μ differ from them by up to 0.04 %, as the Standard
says they should.

**Upper (86–1000 km).** Temperature is isothermal, then an ellipse, then
linear, then exponential (eqs. 25–32). The ellipse constants are derived from
their defining conditions (Appendix B, B-5/B-8/B-9). The printed four-decimal
values would end 2.7 × 10⁻⁴ K short of T9 and step at 110 km. N₂, O, O₂, Ar
and He follow eqs. 35–38 from Table 9 at 86 km:
- O and O₂ diffuse through N₂.
- Ar and He diffuse through N₂ + O + O₂.
- M = M0 below 100 km for all of them (p. 14).
- Eddy diffusion K follows eq. 7, and the flux terms follow eq. 37 with Table 7.

Hydrogen (eqs. 39–40) exists from 150 km, referenced to n(H) = 8.0 × 10¹⁰ m⁻³
at 500 km with the escape flux φ. Above 500 km its flux integral is neglected,
as the Standard states (p. 14). Its tables are computed that way: keeping the
term would put n(H) 0.30 % below Table VIII at 1000 km. Totals: N = Σnᵢ,
P = NkT (33c), ρ = Σnᵢ Mᵢ/N_A, M = Σnᵢ Mᵢ/N, and TM = T M0/M.

The species are integrated once, lazily, by a Dormand–Prince 5(4) integrator
(no SciPy at runtime) to whole-kilometre nodes; every breakpoint of the
Standard is a whole kilometre. A query between nodes continues the same
equations from the node below. Nothing is interpolated.

**Not defined, and said so.** Above 86 km the state has no speed of sound
and no dynamic viscosity. The Standard terminates both at 86 km: eq. 50
holds only while sound is a small perturbation (§1.3.10), and eq. 51 "fails
for conditions of very high and very low temperatures" (§1.3.11). Pressure
*is* defined (eq. 33c) and is given. Composition is given from 86 km, where the
Standard tabulates it (Table VIII). Below that it is absent, with that reason.

**Two steps that belong to the Standard.** They were measured and decomposed,
not tolerated:
- **86 km.** The hydrostatic and species forms differ by 1.08 × 10⁻⁵ in P and
  8 × 10⁻⁶ in ρ and N. This decomposes exactly into three defining values of
  the Standard that disagree with each other:
  - Table 9 / Appendix A take Z7 = 86 km as H7 = 84.8520 km′, while eq. 18 gives
    84.85205 km′ (8.1 × 10⁻⁶ in ρ).
  - k exceeds R*/N_A by 2.29 × 10⁻⁶ (p. 3).
  - T7 = 186.8673 K is rounded (4.3 × 10⁻⁷).
  - In M, Table 8's 0.999579 against Appendix A's 0.99957908 differ by 7 × 10⁻⁸.
- **150 km.** Hydrogen joins the sum, adding n(H)/N = 7.3 × 10⁻⁶ to N and P.

**References checked** (read from the scan, not generated):
- Table VIII composition at 15 heights from 86 to 1000 km: all six species
  agree within one unit of the last printed digit.
- Table I T, P and ρ at 15 heights.
- Table II N and M at 7 heights.
- Table 9, and Appendix A's N, M and ρ at 86 km.
- Appendix B's ellipse constants.
- Sutton Appendix 2 at 160, 400 and 600 km. Sutton misprints the upper
  atmosphere too: 845.56 K for 854.56 K at 200 km, and ρ 2.137 × 10⁻¹³ for
  1.137 × 10⁻¹³ at 600 km.

A dense audit (3 700 points from 80 to 1000 km, plus both sides of every
breakpoint) finds P, ρ and N strictly falling and M non-increasing everywhere
except at the two documented steps, whose sizes it checks.

## LIQ-2 integration

`AmbientMode` gains `standard_atmosphere`. `DesignEnvironment` gains `altitude`
(m, geometric) and `atmosphere_model` (default `ussa1976`). Like the custom
pressure, both are kept when the mode changes.

- **The requirement records intent and computes nothing.** `requirement.py`
  still imports only the standard library, as LIQ-2 requires. It checks that
  an altitude is stated and finite. Its `ambient_pressure` property raises
  `AmbientNotResolvedHere` for an altitude environment rather than guess.
- **`environment_service` resolves.** `resolve()` returns the state, and
  `ambient_pressure()` returns the pressure. Vacuum, sea level and custom
  pressures are returned directly, without the atmosphere package, so their
  numbers and call counts are unchanged. `environment_issues()` adds the
  model's range check and the chamber-versus-ambient check against the
  resolved pressure.
- **Downstream.** LIQ-3 (trade) and LIQ-4 (sizing) read the ambient through
  `environment_service.ambient_pressure`. No atmosphere equation exists
  outside the package. An altitude and the same pressure stated manually give
  identical trade, sizing and chamber-geometry numbers (tested with the stub
  provider and with NASA CEA).
- **Records.** A requirement without an altitude writes the same JSON, byte for
  byte, as before ENV-1, so its fingerprint is unchanged. The altitude and the
  model key appear only once an altitude is in use. The schema version stays
  1: the change is additive.
- **Page.** "Altitude (USSA 1976)" shows an altitude field (km). The ambient
  pressure becomes read-only and shows the resolved value, and the resolved
  state is listed with its source. In altitude mode, reading the page resolves
  the state, which is closed-form and deterministic. No provider or solver is
  reached, and a runtime test counts every call to prove it.

## References checked

The tests compare the model with values read from the Standard's printed
tables, not with the implementation:

- **Table I** (geometric): −5 000, 11 000, 11 100, 11 200, 19 000, 38 000,
  60 000, 75 000 and 80 000 m.
- **Table II** (geopotential): 11 000, 20 000, 60 000 and 75 000 m′.
- **Table III**: −1 000, 3 000 and 27 000 m.

Temperature and density agree within the rounding of their printed digits.
The pressure column is printed **truncated**, not rounded. In every row the
model's pressure, cut to the printed digits, gives the printed value, so
pressure is checked against that interval.

**Sutton Appendix 2 is not a clean reference.** It cites the Standard but mixes
geometric rows (0, 1, 10, 25, 50 km) with geopotential ones (3, 5, 75 km). It
also carries digit transpositions: P/P0 at 3 km, ρ at 5 km, and a 2-unit
P/P0 at 10 km. The tests pin each row to the reading it matches and record the
misprints.

## Not in ENV-1

An empirical upper atmosphere. **ENV-2 (NRLMSIS 2.1) is deferred.** NRL's MSIS
2.x licence (NRL-SOF-014-1) grants use "for academic, non-commercial purposes
only". It forbids modification, it requires NRL IP Counsel's written consent
for other distribution, and the method is covered by US Patent 10,641,925.
RocketForge is MIT-licensed and its executable bundles its providers, so it
cannot carry that licence. The pymsis wheel bundles the compiled MSIS code
without that licence text. No MSIS code or dependency was added. Also not in
ENV-1: weather,
winds, humidity, Mach, dynamic pressure or Reynolds number, drag and lift,
trajectory, gravity and drag losses, orbit decay, re-entry, Earth rotation,
and any nozzle redesign.
