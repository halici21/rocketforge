# 12 — Combustion Chamber State Specification

The chamber-state contract, and exactly how a reacting-gas chamber state becomes
an input to the frozen Compressible v1 API without touching it.

**Status:** specification. The frozen compressible API is an input to this
document and is not modified by it. Manifest digest
`8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` (Phase 4G);
the reproducible manifest is
`tests/acceptance/freeze/phase_4g/freeze_compressible_api_v1.json`.

---

## 1. What a chamber state is

`ChamberGas` (`09` §7) is the **stagnation state of the combustion products at
the nozzle entrance**. It is a chemistry result, not a device description:

* it knows T₀, γ, R, M̄ and composition;
* it does not know the chamber's volume, its L\*, its contraction ratio, its
  residence time or its wall temperature — those are `engineering.chamber`
  (`08` §4);
* it is the single object that crosses from chemistry into gas dynamics.

`06` §4.1 fixed this role in Phase 3 and this document does not change it.

---

## 2. The verified starting point

The handshake's target was measured on 2026-09-03 against the frozen API, not
assumed:

```python
PerfectGas(gamma: float, gas_constant: float | None)
NozzleOperating(stagnation_pressure, back_pressure, stagnation_temperature)
nozzle.solve(geometry, operating, gas, tolerances) -> Solution[NozzleSolution]
```

Two findings from that inspection matter for Phase 5B:

**Real rocket gammas are already accepted cleanly.** `PerfectGas` carries an
advisory band (`gamma_advisory_min=1.05`, `gamma_advisory_max=1.9` in
`ToleranceSet`). Chamber gases sit inside it:

| γ | Representative of | Diagnostics raised |
| --- | --- | --- |
| 1.14 | LOX/LH₂, hot and dissociated | none |
| 1.21 | LOX/RP-1 | none |
| 1.26 | LOX/CH₄, frozen | none |
| 1.04 | below the advisory band | `EXTRAPOLATED_GAMMA` |

So the frozen module needs no change, no widened band and no special case to
accept combustion products. **The handshake is a data conversion, not a
modification.** This is the single most important input to the Phase 5B
recommendation.

**The gas constant is specific R in J/(kg·K), and it is optional.** `ChamberGas`
carries R directly (`09` §7), so the dimensional path is available; `M̄` is the
molar quantity and must not be passed where specific R is expected. The
consistency invariant `R = R_universal / M̄` (`09` §7.2) is what protects against
that swap.

---

## 3. The handshake, precisely

```
    ChamberGas                                     engineering.chamber
      temperature        T0  [K]        ---------> NozzleOperating.stagnation_temperature
      gas_constant       R   [J/(kg K)] ---------> PerfectGas.gas_constant
      gamma              (see section 5) --------> PerfectGas.gamma
      composition        Mixture        ---------> (not passed; retained for reporting)
      molar_mass         M_bar          ---------> (not passed; consistency check only)

    chamber pressure     p_c [Pa]       ---------> NozzleOperating.stagnation_pressure
    ambient pressure     p_amb [Pa]     ---------> NozzleOperating.back_pressure
    nozzle contour                      ---------> AreaDistribution (engineering.nozzle)

                                        ---------> nozzle.solve(...) [FROZEN]
```

Composition and molar mass deliberately **do not cross**. The compressible
module has no field for them and must not acquire one. They stay on the
`ChamberGas`, are reported alongside the result, and are what a later
equilibrium-expansion path consumes instead (§7).

---

## 4. Preconditions

`engineering.chamber` refuses to build the handshake unless all of these hold.
Each is a refusal with a diagnostic, never a silent correction.

| # | Precondition | Why |
| --- | --- | --- |
| P1 | `provenance` is present and states the mode | γ's meaning depends on it (`11` §4); a state that cannot say which γ it holds cannot be used |
| P2 | `gamma > 1`, finite | perfect-gas relations require it; the frozen module validates too, but the caller should not rely on that to catch a chemistry defect |
| P3 | `gas_constant > 0`, finite | dimensional path requires it |
| P4 | `R == R_universal / M̄` within tolerance | catches an adapter that scaled one and not the other (`09` §7.2) |
| P5 | `temperature > 0`, finite | trivially, but a failed equilibrium can return a sentinel |
| P6 | `condensed_mass_fraction` is present **and** below the declared threshold | two-phase flow is not a perfect gas (`11` §7.3) |
| P7 | `condensed_mass_fraction is None` **rejects** | "the provider did not say" is not "there is none" (`11` §7.3) |
| P8 | the γ strategy is explicitly chosen | §5 — there is no default |

**P1, P6, P7 and P8 are the ones that carry real weight.** The others are
hygiene; these four are the difference between an honest coupling and a
plausible wrong answer.

---

## 5. The γ strategies

A single-γ perfect gas cannot represent a reacting mixture whose γ varies along
the expansion. Reducing one to the other loses information, and **which** γ is
kept is an engineering choice. Phase 5A's position: the choice is **named,
explicit and recorded** — never defaulted, never averaged behind the user's
back.

```python
class GammaStrategy(Enum):
    """Which single gamma represents a varying-gamma expansion. Explicit."""

    CHAMBER = "chamber"                  # gamma at the chamber state
    THROAT = "throat"                    # gamma at the sonic condition
    EXIT = "exit"                        # gamma at the exit condition
    CHAMBER_EXIT_MEAN = "chamber_exit_mean"   # arithmetic mean of the endpoints
    EFFECTIVE_ISENTROPIC = "effective_isentropic"  # fitted to match p0/pe over the actual expansion
```

| Strategy | Best for | Known bias |
| --- | --- | --- |
| `CHAMBER` | small expansion ratios; comparison with chamber-referenced data | overstates γ at the exit, so understates exit Mach |
| `THROAT` | mass flow and c\*, which are set at the throat | not representative of the diverging section |
| `EXIT` | exit-plane conditions and thrust coefficient | misrepresents the throat, so distorts mass flow |
| `CHAMBER_EXIT_MEAN` | a crude compromise | endpoints are not where the variation is |
| `EFFECTIVE_ISENTROPIC` | best overall single-γ fit for the expansion actually being run | requires a provider expansion first, so it is not free |

**No strategy is correct.** Each is a stated approximation with a stated bias,
and that is why the enum has no default member and P8 requires an explicit
choice. A strategy the user did not pick is a number the user cannot interpret.

`EFFECTIVE_ISENTROPIC` deserves a note: it is fitted so that the single-γ
isentropic relation reproduces the true temperature ratio over the actual
pressure ratio of this expansion. That makes it the most defensible single-γ
choice — and it is *still* an approximation, because a fitted exponent that
matches the endpoints does not match the interior. It is a better answer, not a
right one.

---

## 6. The error is quantified, not hidden

`08` §5.2 promised this. The requirement:

> Every result produced through the single-γ handshake carries the strategy that
> produced it and a statement of the error character.

Phase 5B implements it as:

* `GammaStrategy` recorded in the result's provenance;
* a **computed** discrepancy where a provider expansion is available: run the
  equilibrium expansion, then compare the frozen module's single-γ prediction of
  exit temperature and pressure against it, and report the difference as a
  number rather than a warning;
* a `Diagnostic` when that difference exceeds a declared threshold, naming the
  magnitude;
* the UI showing it (`15` §3).

This turns "a single γ is approximate" from a disclaimer into a measurement.
It is the same instinct as the compressible module's reference-comparison
panels: state the discrepancy, do not gesture at it. And it is only possible
because both paths exist side by side — which is the argument for §7.

---

## 7. What the single-γ path is *not* for

The single-γ handshake exists so that **nozzle geometry, back-pressure regimes,
internal shocks and the full quasi-1D station distribution** — everything Phase
4F built and Phase 4G froze — become available to a chemically computed gas. It
is genuinely valuable: regime classification and shock location are structural
results that do not need a variable γ to be useful.

It is **not** the path for accurate delivered performance. For that:

* the provider's own equilibrium expansion (`09` §9.2, `11` §5.2) computes
  station properties with composition shifting, and the exit velocity follows
  from the energy equation on this layer's enthalpy datum;
* `engineering.nozzle` turns that into thrust, Cf, c\* and Isp (ADR-15);
* the frozen compressible module is not involved, because its assumptions do not
  hold there.

Two paths, both legitimate, each labelled. What is forbidden is the third thing:
bolting a γ(x) hook into the frozen module so it *looks* like it handles
variable γ. ADR-14 rejected that in Phase 3 and the v1.0 freeze rejects it
again. A partially wired variable-γ path is worse than either honest option,
because its results carry the frozen module's authority without its assumptions.

---

## 8. Where the adapter lives

```python
# engineering/chamber/handshake.py   (SPECIFICATION - Phase 5B)

def perfect_gas_from_chamber(
    chamber: ChamberGas,
    strategy: GammaStrategy,
    *,
    expansion: Sequence[GasStation] | None = None,
) -> Solution[PerfectGas]: ...

def operating_from_chamber(
    chamber_pressure: float,
    ambient_pressure: float,
    chamber: ChamberGas,
) -> Solution[NozzleOperating]: ...
```

In `engineering`, not `physics`, for three reasons that all point the same way:

1. **`physics.thermochemistry` must not import `physics.compressible`**
   (`08` §8). Constructing a `PerfectGas` would require exactly that import.
2. **The γ choice is an engineering judgement**, not a chemical fact.
3. **`Solution[T]` belongs at the engineering boundary** (`09` §9.4), which is
   where provider exceptions become diagnostics.

The return type is `Solution[PerfectGas]` rather than a bare `PerfectGas`
because the preconditions of §4 fail as diagnostics, and because the
strategy's error estimate (§6) travels with the result.

`expansion` is optional and required only by `EFFECTIVE_ISENTROPIC`; requesting
that strategy without it is a construction error, not a silent fallback to
another strategy.

---

## 9. Worked example of the intended flow

Illustrative of the call sequence only; no numbers are asserted here, because
Phase 5A computes nothing. `13` §3 fixes the reference cases that will carry
real values.

```python
# 1. Chemistry: chamber equilibrium
chamber = provider.equilibrium_chamber(
    fuel="CH4", oxidiser="LOX",
    mixture_ratio=3.4, chamber_pressure=10.0e6,
    fuel_temperature=111.0, oxidiser_temperature=90.0,
)

# 2. Chemistry: the expansion, for the exponent fit and the error estimate
stations = [provider.expand_to_pressure(chamber, p, ExpansionMode.EQUILIBRIUM)
            for p in pressure_schedule]

# 3. Engineering: reduce to a single-gamma gas, explicitly
gas = perfect_gas_from_chamber(
    chamber, GammaStrategy.EFFECTIVE_ISENTROPIC, expansion=stations,
).unwrap()

operating = operating_from_chamber(10.0e6, 101_325.0, chamber).unwrap()

# 4. Gas dynamics: FROZEN v1.0, untouched
solution = nozzle.solve(geometry, operating, gas)

# 5. Engineering: performance
#    - structural results (regime, shock location) from `solution`
#    - delivered performance from `stations`, not from `solution`
```

Step 5 is the one to read twice. The regime and the shock location come from the
frozen quasi-1D solution; the delivered Isp comes from the equilibrium
expansion. Taking performance from the single-γ path when the equilibrium path
is right there would be choosing the worse number for no reason.

---

## 10. What must never happen

| Forbidden | Because |
| --- | --- |
| Editing `physics/compressible/*` to accommodate chemistry | v1.0 is frozen; the manifest digest is the record |
| A γ(x) hook in the frozen module | ADR-14, and §7 |
| Defaulting `GammaStrategy` | the user cannot interpret a number whose approximation they did not choose (§5) |
| Passing a two-phase state through the handshake | `11` §7.3, P6/P7 |
| Passing `molar_mass` where `gas_constant` is expected | P4 exists to catch it |
| Presenting single-γ performance as delivered performance | §7 |
| Widening the compressible tolerances for chemistry cases | the tolerances are part of the frozen contract |

---

## 11. Consequences for Phase 5B

The frozen API is **usable as it stands**. Confirmed on 2026-09-03: rocket γ
values raise no diagnostics, `PerfectGas` takes the two fields `ChamberGas`
already provides, and `NozzleOperating` takes the three quantities the chamber
already knows.

Phase 5B therefore needs **no change to `physics/compressible/`** for this
coupling. The work is a new adapter module in `engineering.chamber`, and the
Phase 4G manifest stays valid.
