# Methane dynamic viscosity — transport validation

**Verdict: VALIDATED** over the declared liquid envelope.

The fluids foundation shipped CoolProp as the production property provider but
explicitly did **not** claim methane viscosity was validated: it had compared
two software packages, found a 0.4–1.4 % difference, and had no basis for
saying which was right or whether the difference mattered. This document closes
that gap with evidence, and it is a precondition for `engineering.line`, the
first consumer of a transport property.

---

## 1. The model actually in use

Read from CoolProp's own fluid JSON, not inferred from an API name.

| | |
| --- | --- |
| Provider | CoolProp 8.0.0, `HEOS` backend |
| Viscosity model | **friction theory (f-theory)** |
| BibTeX key | `QuinonesCisneros-JPCB-2006` |
| Publication | Quiñones-Cisneros & Deiters, *Generalization of the Friction Theory for Viscosity Modeling*, J. Phys. Chem. B **110** (2006) 12820–12834, DOI 10.1021/jp0618577 |
| Structure | a dilute-gas term in powers of T/T_c (T_c = 190.564 K) plus a friction-theory residual |
| Residual coupling | computed from the repulsive and attractive pressure contributions of the equation of state |
| Equation of state | `Setzmann-JPCRD-1991`, the methane reference EOS |
| Critical enhancement | none for viscosity |
| State-dependent model switching | none — one dilute term and one residual throughout |

The residual term's coupling to the EOS matters for what follows: because the
provider and the reference implementations share the Setzmann–Wagner EOS, the
**density agrees to 0.00000 %** at every state compared below, which isolates
every viscosity difference to the transport correlation alone.

---

## 2. The envelope, derived rather than chosen

| | |
| --- | --- |
| Fluid | methane |
| Phase | **single-phase liquid** |
| Temperature | **100 – 125 K** |
| Pressure | **0.5 – 3.0 MPa** |
| Saturation margin | p ≥ 1.5 · p_sat(T) |

Why these numbers:

* **Temperature** brackets NASA CEA's own declared range for the `CH4(L)`
  reactant, 101.643–121.643 K, with margin at each end, so every propellant
  state RocketForge can request lies inside the validated band.
* **Pressure** is a feed-system range for a preliminary design. It is
  emphatically not a chamber pressure: the canonical chamber runs at 10 MPa
  and a feed line does not.
* The whole box lies **inside Diller's experimental range** (100–300 K,
  0.6–33.1 MPa) and inside the 33 MPa limit of the 2025 evaluated correlation,
  so every state is covered by primary evidence rather than extrapolation.
* The saturation margin keeps the box clear of the two-phase boundary, which
  the line model does not support. At 125 K — the warmest state — p_sat is
  0.27 MPa against a lowest validated pressure of 0.5 MPa.

**Excluded:** two-phase and saturated states; gas and supercritical states;
T below 100 K; p above 3 MPa.

---

## 3. Sources

| Tier | Source | Role |
| --- | --- | --- |
| 1 | **Sotiriadou, Antoniadis, Assael, Martinek & Huber (NIST)**, *Correlation for the Viscosity of Methane from the Triple Point to 625 K and Pressures to 1000 MPa*, Int. J. Thermophys. **47** (2025) 18, DOI 10.1007/s10765-025-03690-7 | the current evaluated reference correlation, and the source of the uncertainty |
| 1 | **Diller**, *Measurements of the viscosity of compressed gaseous and liquid methane*, Physica **104A** (1980) 417–426 | primary experiment: 116 points, 100–300 K, 0.6–33.1 MPa, torsionally oscillating quartz crystal |
| 1 | Haynes (1973), 17 liquid points; **Boon et al. (1967)**, 8 saturated-liquid points; Slyusar et al. (1974), 15 points | the supporting primary data the correlations rest on |
| 1 | **NIST Chemistry WebBook**, SRD 69, retrieved 2026-09-06 | an independent implementation of a *different* correlation |
| 1 | Quiñones-Cisneros & Deiters (2006) | the provider's own model publication |

### Stated uncertainties

| Source | Uncertainty |
| --- | --- |
| Sotiriadou 2025, **compressed liquid to 33 MPa** | **3 % (k = 2)** |
| Diller 1980 | 2 % accuracy, 0.5 % precision |
| Haynes 1973 | 2 % |
| Boon 1967, saturated liquid | 1 % |
| Slyusar 1974 | 4 % |

The 2025 paper compares itself against the friction-theory model in the liquid
and reports that **the performance of both correlations is similar**.

---

## 4. The acceptance criterion, and where it comes from

> **|μ_provider − μ_reference| / μ_reference ≤ 3 %**

Derived from the sources **before** any comparison was run:

1. The 2025 evaluated correlation states 3 % (k = 2) for the compressed liquid.
   Nothing computed from liquid methane viscosity in this region can be known
   better than that.
2. The primary data the correlations rest on carry 2 % (Diller, Haynes) and
   1 % (Boon). A model agreeing with a reference to better than 3 % agrees to
   within the measurements that define the quantity.
3. The 2025 paper states the friction-theory model performs similarly in the
   liquid, so a cross-model difference of this order is the expected result.

**This is not a widened tolerance.** It is the published expanded uncertainty
of the field. A point outside it would mean two models disagreeing by more than
the measurements permit, and would be investigated rather than accepted.

---

## 5. The comparison

24 states: 4 temperatures × 6 pressures, every one reported `liquid` by the
provider and inside the saturation margin.

| | |
| --- | --- |
| States compared | **24** |
| Density agreement | **0.00000 %** at every state — same EOS, so the difference is purely transport |
| Worst viscosity difference | **2.885 %** at 100 K, 0.5 MPa |
| Criterion | 3 % (k = 2) |
| Failures | **0** |

The difference is systematic and changes sign:

| T | difference vs the WebBook |
| --- | --- |
| 100 K | **+1.8 % to +2.9 %** (provider higher) |
| 110 K | ±0.3 %, the crossover |
| 120 K | −0.6 % to −1.2 % |
| 125 K | −0.5 % to −1.1 % |

### Why the worst case is not what it looks like

2.885 % against a 3 % criterion is close enough that accepting it without
understanding it would be exactly the tolerance-hiding this gate exists to
prevent. So the third leg was measured — the two *references* against each
other, at 100 K saturated liquid:

| Source | μ (µPa·s) | vs the 2025 correlation |
| --- | --- | --- |
| **Sotiriadou 2025** (evaluated reference) | **154.500** | — |
| **CoolProp** (friction theory) | **155.635** | **+0.734 %** |
| **NIST WebBook** (older model) | **150.956** | **−2.294 %** |

**CoolProp sits roughly three times closer to the current evaluated reference
correlation than the WebBook does.** The 2.885 % is the sum of two deviations
in opposite directions from the best available reference — a spread *between
references*, not an error in the provider.

That is precisely what a 3 % (k = 2) uncertainty means in practice, and it is
why judging a provider against one of two disagreeing references, without
measuring how far apart they are, would have reached the wrong conclusion.

Additional saturated check values against the 2025 correlation: **0.734 %** at
100 K, **0.043 %** at 120 K, 2.019 % at 150 K (outside the line envelope).

---

## 6. Units, phase, determinism

| Check | Result |
| --- | --- |
| Canonical value at 110 K, 3 bar | 1.2189 × 10⁻⁴ Pa·s, inside the liquid band |
| ×1000, ÷1000 and ×10⁶ mutations | **all three detected** |
| Conversion in the adapter | **none** — CoolProp's SI interface returns Pa·s directly |
| Phase agreement | **6 / 6**, including gas at 125 K / 1 atm |
| Two-phase state | reported `TWO_PHASE`, **viscosity withheld entirely** |
| Five identical queries | identical, exact float64 |
| A/B/A/B/A with oxygen | `a1 == a2 == a3`, `b1 == b2`, `a ≠ b` |

---

## 7. The other production fluids

Confirmed from the fluids-foundation artifact rather than taken on trust: the
recorded set of unvalidated properties was exactly
`{METHANE.dynamic_viscosity}`.

| Fluid | Density | Viscosity |
| --- | --- | --- |
| Oxygen | validated | validated (Lemmon-IJT-2004, same lineage as the reference) |
| Methane | validated | **validated here** |
| Hydrogen | validated | validated (Muzny-JCED-2013, same lineage) |

All three are therefore eligible for a line model that consumes ρ and μ.

---

## 8. Limitations of this validation

* **Liquid only, 100–125 K, 0.5–3.0 MPa.** Outside that box the provider still
  answers, but this document makes no claim about it, and the line workspace
  refuses to present a production result there.
* The comparison is against **evaluated correlations and their tabulated
  values**, not against raw experimental points re-reduced here. The
  experimental layer enters through the correlations' stated uncertainties,
  which is how the 3 % criterion was set.
* The 2025 correlation's own liquid uncertainty, 3 % (k = 2), is the floor on
  what any downstream pressure drop can claim. A friction-factor computed from
  a viscosity known to 3 % inherits that, and the line documentation says so.
* No claim is made about methane **thermal conductivity**, which no component
  in this work consumes.
