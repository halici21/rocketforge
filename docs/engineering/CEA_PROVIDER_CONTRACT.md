# NASA CEA v3 Provider Contract

`rocketforge.providers.cea`

What RocketForge's first production thermochemistry provider does, what it
refuses, what it cannot do, and where its numbers come from.

**Status:** **FROZEN as NASA CEA Provider v1.0** by Phase 5G, versioned
separately from the domain it implements, so a provider fix does not reopen the
Thermochemistry API. 11 files, digest
`0a46b5f089a9cc7a47278eecd0868b8d68730aa1abbf9c5775e35cb70eb9285a`. The
provider-independent contract it implements is
[THERMOCHEMISTRY_API_V1.md](THERMOCHEMISTRY_API_V1.md), also frozen.

---

## 1. Version and dependency

| | |
| --- | --- |
| Provider id | `cea` |
| Adapter version | `1.0-phase5c` |
| Validated library | **`cea==3.3.4`**, NASA CEA v3, Apache-2.0 |
| Dependency profile | `requirements-thermochemistry.txt` |
| Base `requirements.txt` | **unchanged** — the library is optional |
| Official desktop build | **includes** the provider; an end user never runs pip |

`SUPPORTED_CEA_VERSIONS` holds the versions Phase 5C validated end to end. A
different installed version reports `VERSION_UNSUPPORTED` — usable, because the
API is likely compatible, but flagged in provenance so its results are never
mistaken for validated ones. Raising the pin is a deliberate act with a
re-validation run attached.

---

## 2. Availability

`check_availability()` answers four distinct questions, and never raises:

| Status | Meaning | The fix |
| --- | --- | --- |
| `AVAILABLE` | imported, initialised, validated version | — |
| `NOT_INSTALLED` | the distribution is absent | install the profile |
| `LOAD_FAILED` | present but will not import or initialise | repair the installation |
| `VERSION_UNSUPPORTED` | works, but not a validated version | usable at your risk |

`NOT_INSTALLED` and `LOAD_FAILED` are kept apart deliberately. Phase 5B-0
established that `import cea` initialises the native library **and loads
thermo.lib**, so a missing data file surfaces as a `ValueError` during import,
not an `ImportError`. A check that only caught `ImportError` would report a
broken installation as a missing one and send the user to pip.

**Importing the adapter does not import CEA.** Provider discovery, availability
reporting and provider construction all work on a machine with nothing
installed — which is what lets the base test suite prove optionality on every
run.

---

## 3. What it computes

One production operation:

```python
provider.solve_chamber(request) -> Solution[ChamberGas]
```

Ideal **adiabatic HP chamber equilibrium**: fixed reactant enthalpy, fixed
chamber pressure, chemical equilibrium. Solved with `EqSolver` and the `HP`
constraint directly — not by running the full rocket solver and reading the
chamber station out of it, which would compute an expansion nobody asked for.

A non-HP constraint is **refused**, not silently substituted.

---

## 4. Units

Every conversion has exactly one owner, in `units.py`. All were established by
identity rather than read off a label.

| Quantity | CEA native | RocketForge | Conversion | How established |
| --- | --- | --- | --- | --- |
| pressure | **bar** | Pa | ×1e5 | a solve given 100.0 reported `P = 100.0`; `p = ρRT` closed only at 1e7 Pa |
| temperature | K | K | none | identical |
| molar mass | **kg/kmol** | **kg/mol** | ÷1e3 | `p = ρRT` closes only with M read as kg/kmol |
| cp, cv | **kJ/(kg·K)** | J/(kg·K) | ×1e3 | `cp_fr − cv_fr = 0.38736` against R = 387.36 J/(kg·K) |
| enthalpy | **kJ/kg** | J/kg | ×1e3 | cross-checked against Cantera on the matched case |
| entropy | **kJ/(kg·K)** | J/(kg·K) | ×1e3 | same |
| density | kg/m³ | kg/m³ | none | `p = ρRT` closes with the raw value |
| c\*, Isp (oracle) | m/s | m/s | none | `Isp == Cf · c*` exactly |

One further case: the HP constraint is handed to CEA as **H/R**, a quantity in
kelvin. Both operands come from CEA — `calc_property(ENTHALPY, …)` and `cea.R` —
so RocketForge's CODATA constant is deliberately **not** substituted there.
Doing so would inject a 5.7e-06 inconsistency into the solver's own input.

---

## 5. Input mapping

### Propellant names

`provider_names["cea"]`, required. There is **no fallback** to the canonical
name or the display label: RocketForge calls it `LOX` and CEA calls it `O2(L)`,
and a fallback would silently substitute gaseous `O2` for a cryogenic liquid —
worth 74.9 K of chamber temperature.

**CEA's name limit is 15 characters**, measured rather than assumed: 16 and
longer are rejected with `CEA_INVALID_SIZE` before any database lookup. The
limit lives in `naming.py` and constrains nothing in the domain model; a name
that does not fit is refused, never truncated.

### Reactant temperature and phase

The **actual `PropellantStream` temperature** is used, never the definition's
reference value. A stream outside the range CEA declares for that reactant is
refused with the range named.

### O/F

RocketForge's orientation is oxidiser mass ÷ fuel mass, and so is CEA's, so the
value passes through unchanged. Fuel and oxidiser weight vectors are disjoint
and the roles are checked, so a swap raises rather than inverting.

### Blends

Mass-basis blends pass straight through, since CEA's reactant weights are
masses. Mole-basis blends are converted using molar masses obtained **from
CEA**, so the numbers are the provider's own.

**Limitation, stated rather than hidden:** a blend's component species keys are
used directly as CEA names, because `PropellantDefinition` carries one provider
name for the substance, not one per component. Blends whose component keys are
already valid CEA species names work today; anything else needs a domain
extension and says so through `CEAMappingError` rather than guessing.

---

## 6. Product species

The default product set is **curated**, not `products_from_reactants`.

CEA's automatic selection yields **124 species** for LOX/CH₄, most below 1e-20,
with names such as `C2H2,acetylene`, `HCHO,formaldehy`, `CH3C(CH3)2CH3` and
`(HCOOH)2`. Deriving elemental formulae from those requires a parser handling
parentheses and comma-suffixed common names — the fragile universal parser the
architecture warns against — and CEA exposes no per-species elemental
composition of its own.

Measured cost of curating instead (LOX/CH₄, O/F 3.4, Pc 100 bar, NBP reactants):

| Product set | Tc [K] | M [kg/kmol] | γ_s | ΔTc | Δγ/γ |
| --- | --- | --- | --- | --- | --- |
| automatic, 124 species | 3598.2855 | 21.77009 | 1.13259 | — | — |
| curated 12 | 3598.3332 | 21.76947 | 1.13265 | +0.048 K | 5.1e-05 |
| **curated 28** | **3598.2860** | **21.77008** | **1.13259** | **+0.0005 K** | **1.0e-06** |

1e-06 is an order of magnitude **below** CEA's own pre-2019 gas-constant
discrepancy of 5.7e-06, which is already the floor under every provider
identity check. The truncation therefore costs less than a difference the
architecture already tolerates and documents.

The set actually used is recorded in `provenance.species_set`. A caller may
override it. A species with no curated formula raises rather than being
dropped, because a dropped species breaks element conservation while the
composition still sums to one.

Molar masses come **from CEA** (`Mixture.moles_to_weights` on a unit vector),
which removes the atomic-weight-vintage mismatch from every element balance.
Only the formulae — unambiguous integers — are curated, and a test checks them
against CEA's own molar masses.

---

## 7. Output mapping

| `ChamberGas` field | Source |
| --- | --- |
| `temperature` | CEA `T` (a stagnation temperature) |
| `pressure` | the request's chamber pressure |
| `density` | CEA `density` |
| `molar_mass` | CEA `MW`, converted kg/kmol → kg/mol |
| `gas_constant` | **derived**, `Ru_CODATA / M` |
| `cp`, `cv` | CEA `cp_fr`, `cv_fr` — the **frozen** pair |
| `cp_frozen`, `cp_equilibrium` | both preserved |
| `gamma`, `gamma_equilibrium` | CEA `gamma_s`, the isentropic exponent |
| `gamma_frozen` | `cp_fr / cv_fr` |
| `enthalpy`, `entropy` | converted from kJ |
| `composition` | CEA `mole_fractions`, complete |
| `condensed_mass_fraction` | computed from the **composition** |
| `request`, `provenance` | full traceability |

**cp and cv carry the frozen pair** because only that pair satisfies
`cp − cv = R`; the equilibrium pair does not and is not meant to (measured:
7.162 − 6.066 kJ/(kg·K) against R = 0.387).

**R is derived from RocketForge's CODATA constant.** CEA returns a molar mass,
not a gas constant, so R must be derived, and deriving it with our constant
makes `R = Ru/M` close exactly. The consequence — CEA's own `cp − cv` and
`p = ρRT` then miss ours by 5.7e-06 — is absorbed by
`provider_identity_rel_tol`, which exists for exactly this.

---

## 8. Condensed phases

Presence is read from the **returned composition**, never from CEA's
`num_condensed`. That counter reports how many condensed species are in the
product *list*, not how many are present: the canonical Phase 5C production
case reports candidates while the amount present is 6.2e-08.

Both halves are covered by tests: candidates without presence at O/F 3.4, and
genuine solid carbon at O/F 0.5.

---

## 9. Provenance

Every successful result carries:

* provider id and adapter version;
* the `cea` distribution version and the underlying library version, recorded
  separately because they are separate identifiers;
* `database = "thermo.lib"` and its **SHA-256**, computed from the file the
  solve actually used — in a frozen build that is the bundled copy, because the
  path is derived from the imported module rather than from a project path;
* chemistry mode and equilibrium constraint;
* the species set;
* the reactant conditions;
* CEA's own universal gas constant, in `options`, for traceability.

---

## 10. Errors and status

| Outcome | Mechanism |
| --- | --- |
| Malformed request | `InputError` subclass, **raised** — usually by the request itself, before the provider is reached |
| Provider unavailable | `ProviderUnavailableError` |
| Unsupported capability | `UnsupportedCapabilityError`, immediately |
| Out of a declared range | `ProviderDomainError`, naming the range |
| Unmappable request | `CEAMappingError` |
| CEA did not converge | `Solution` with `NO_SOLUTION` |
| Converged but failed validation | `Solution` with `NO_SOLUTION` and a diagnostic naming the failed check |

Nothing catches bare `Exception` except the availability probe, where the
failure modes are genuinely open-ended and the exception type is preserved in
the detail. A `KeyError` from the adapter stays visible: it is our defect, not
the provider's.

**Malformed input never reaches CEA.** A spy test counts the calls and asserts
zero for negative temperature, zero temperature, negative pressure, zero and
negative O/F, NaN O/F, zero and negative chamber pressure, and an unsupported
capability — then asserts the spy does see a legitimate call, so it cannot pass
vacuously. The guard matters because Phase 5B-0 measured CEA accepting a
negative temperature and a negative pressure without complaint.

---

## 11. Known limitations

### Assigned-enthalpy reactants ignore the temperature you give them

Several CEA reactant entries — the cryogenic liquids among them — carry a
single **assigned enthalpy** at one reference condition rather than a
temperature-dependent fit. CEA accepts a different temperature and then ignores
it. Verified at the library level:

```
Mixture(['CH4','O2'])       T=[298.15, 298.15] -> H = -1056854.44
                            T=[350.00, 298.15] -> H = -1029844.11   varies
Mixture(['CH4(L)','O2(L)']) T=[111.643, 90.17] -> H = -1577584.52
                            T=[111.643, 99.00] -> H = -1577584.52   identical
```

Affected in the shipped set: `O2(L)` at 90.17 K, `CH4(L)` at 111.643 K,
`H2(L)` at 20.27 K, `RP-1` at 298.15 K. Gaseous reactants respond normally.

The provider **does not pass this silence on**. When a stream temperature
differs from the assigned value it emits `PROVIDER_ASSIGNED_ENTHALPY_REACTANT`
(WARNING), names both temperatures, and returns `OK_WITH_WARNINGS`. Detection
is empirical — the enthalpy is evaluated at two temperatures inside the
declared range — so it cannot be wrong about a reactant it has measured.

### Others

* **15-character name limit**, isolated to the adapter.
* **No per-species elemental data** in CEA's API, hence the curated formulae.
* **Pre-2019 universal gas constant** (8314.51 against CODATA's
  8314.46261815324), a 5.7e-06 difference in every derived identity.
* **Element-conservation residual** reaching 1.9e-08 across the measured range,
  worst at fuel-rich conditions.
* **Threading gives no benefit**: Phase 5B-0 measured four threads at ~0.85× of
  serial. The provider runs serially, in process, with no lock — no
  contamination was observed in A/B/A/B/A leakage tests, and a lock without
  evidence is superstition.
* **Only single-species propellants** have full blend support; see §5.

---

## 12. Performance

Measured on the production case, LOX/CH₄ at O/F 3.4 and 10 MPa, 28 species:

| | |
| --- | --- |
| Provider package import (no CEA loaded) | 181 ms |
| First availability check (imports CEA) | 41.9 ms |
| First solve on a cold provider | 2.91 ms |
| Warm solve, **full RocketForge pipeline** | **0.543 ms** |
| Warm solve, raw CEA call only | 0.275 ms |
| RocketForge mapping + validation overhead | **0.268 ms (49 %)** |
| 100-point O/F sweep | 56.5 ms (0.565 ms/point) |
| 1000-point O/F sweep | 568 ms (0.568 ms/point) |

The 49 % overhead buys element conservation, four state identities, composition
validation and provenance on **every** solve. The raw figure is larger than
Phase 5B-0's 44 µs because that benchmark used an 11-species set against this
one's 28.

Provider instances are reusable and cache both the imported module and the
species tables. A normal application launch never imports CEA at all.

---

## 13. Provider-native performance outputs

CEA returns c\*, Cf and Isp. **They are not on `ChamberGas` and must not be.**

`oracle.py` exposes them as `CEARocketOracle`, a provider-native reference
record carrying the full conditions each value was produced under — chamber
pressure, area ratio, chemistry mode, freeze station — so that a future Phase 5E
can compare like for like. RocketForge implements no rocket performance in
Phase 5C; ownership belongs to `engineering.nozzle` (ADR-15).

`n_frz` never leaves the module: the public vocabulary is `FreezeLocation`.

Measured, LOX/CH₄ at O/F 3.4, Pc 10 MPa, Ae/At 40:

| Mode | c\* [m/s] | Cf | Isp [m/s] | Isp [s] | T_exit [K] |
| --- | --- | --- | --- | --- | --- |
| equilibrium | 1846.89 | 1.8597 | 3434.59 | 350.23 | 1809.18 |
| frozen at throat | 1846.89 | 1.7857 | 3297.92 | 336.29 | 1248.65 |
| frozen at chamber | 1809.23 | 1.7950 | 3247.59 | 331.16 | 1167.58 |

The ordering equilibrium > frozen-at-throat > frozen-at-chamber is what
`11` §5 predicts, and `Isp == Cf · c*` holds exactly.

---

## 14. Packaging

The official desktop build is made from `.venv-cea` and **bundles the
provider**. `packaging/RocketForge.spec` collects CEA's data and binaries when
the library is present in the build environment, and prints which; a build
environment without it still produces a working executable, one without
thermochemistry.

Verified on the shipped bundle:

* the frozen executable solves a real chamber equilibrium from the bundled
  `thermo.lib`, reached through `RocketForge.exe --selftest-thermochemistry`;
* the database hash it reports matches the bundled file;
* source and frozen results are **bitwise identical** on every mapped field;
* Cantera, RocketCEA, CoolProp, the tests and the experiment scripts are all
  absent from the bundle.
