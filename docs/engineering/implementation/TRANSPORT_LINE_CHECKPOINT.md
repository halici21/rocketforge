# Transport validation and engineering.line — Checkpoint

Two strictly ordered gates. **No phase number**: the authoritative roadmap
orders modules, not phases.

| | |
| --- | --- |
| **GATE A** | Methane dynamic-viscosity validation |
| **GATE B** | `engineering.line` v1 — **only** if Gate A passes |

**Status:** ✅ **COMPLETE** — GATE A **PASS**, GATE B **ACCEPTED / FROZEN**

---

## Position

| Field | Value |
| --- | --- |
| CURRENT_GATE | — both closed |
| CURRENT_SEGMENT | L — freeze and final verdict, complete |
| LAST_COMPLETED_STEP | STEP 109 — final verdict returned |
| NEXT_STEP | — this workstream is closed |
| NEXT_ACTION | Next roadmap components per `06` §8 step 2: `engineering.valve`, `engineering.orifice`. Not started. |

---

## Opening gates

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | **6648 passed, 154 skipped**, exit 0, 50.93 s | 6648 / 154 | ✅ |
| Production (`.venv-cea`) | **6803 total** (6801 + the 2 self-inflicted failures below, since fixed), exit 1 → now green | 6803 / 2 | ✅ |
| Freeze manifests | ✅ all reproduce, after the incident below was repaired |

**Authoritative production interpreter: `.venv-cea`.** Confirmed from
`build_exe.bat` (`set "PY=%~dp0.venv-cea\Scripts\python.exe"`, with `.venv` as
a documented fallback that builds without the providers) and from the fluids
acceptance manifest, which records the closing production gate against it.

---

## Incident: the v1.0 CEA manifest was overwritten, and restored

Running `experiments/phase_5g/generate_freeze_manifests.py` during the opening
gates regenerated `freeze_cea_provider_v1.json` **from the current v1.1 tree**,
writing 12 files under a "1.0" label and destroying the historical record.

The fluids-foundation supersession tests caught it within seconds
(`test_the_superseded_manifest_file_was_not_modified` and
`test_the_two_versions_actually_differ`), which is the only reason it was
recoverable rather than a silent falsification.

**Restored, and proved.** The v1.0 digest
`0a46b5f089a9cc7a47278eecd0868b8d68730aa1abbf9c5775e35cb70eb9285a` is published
in four documents that were not overwritten. `mapping.py` and `provider.py`
were reconstructed by inverting the exact v1.1 edits, and the restoration was
accepted **only** because it reproduces that digest — a SHA-256 over all eleven
files, which cannot be matched by accident. Nothing was written until it did.

**Cause fixed.** The Phase 5G generator now refuses to regenerate a superseded
contract and says why. A generator that can silently rewrite history is the
wrong shape.

---

## GATE A state

### The provider model, identified exactly

Read from CoolProp's own fluid JSON, not inferred from an API name:

| | |
| --- | --- |
| Provider | CoolProp 8.0.0, backend `HEOS` |
| Fluid | `Methane` |
| Viscosity BibTeX | `QuinonesCisneros-JPCB-2006` |
| Structure | dilute-gas term + higher-order **friction-theory** residual |
| Dilute term | `powers_of_Tr`, `T_reducing` = 190.564 K, coefficients `a` = [2.60536e-06, −1.85247e-05, 2.34216e-05, 0], `t` = [0, 0.25, 0.5, 0.75] |
| Residual term | friction theory with `Aa`, `Aaa`, `Adrdr`, `Ai`, `Aii`, `Ar` and exponents `Na`=1, `Naa`=3, `Nii`=3, `Nr`=1, `Nrr`=3 |
| Critical enhancement | none for viscosity |
| Model switching by state | none — one dilute plus one residual term throughout |

Friction theory computes the residual viscosity from the repulsive and
attractive pressure contributions of the equation of state, so it is coupled to
Setzmann–Wagner (the methane EOS, `Setzmann-JPCRD-1991`).

### Primary and independent sources

| Tier | Source |
| --- | --- |
| 1 — provider model | Quiñones-Cisneros & Deiters, *Generalization of the Friction Theory for Viscosity Modeling*, **J. Phys. Chem. B 110 (2006) 12820**, DOI 10.1021/jp0618577 |
| 1 — evaluated reference correlation | Sotiriadou, Antoniadis, Assael, Martinek & **Huber (NIST)**, *Correlation for the Viscosity of Methane from the Triple Point to 625 K and Pressures to 1000 MPa*, **Int. J. Thermophys. 47 (2025) 18**, DOI 10.1007/s10765-025-03690-7 |
| 1 — primary experiment | **Diller**, *Measurements of the viscosity of compressed gaseous and liquid methane*, **Physica 104A (1980) 417**. 116 points, 100–300 K, 0.6–33.1 MPa, torsionally oscillating quartz crystal |
| 1 — primary experiment | Haynes (1973), 17 liquid points; Boon et al. (1967), 8 saturated-liquid points |
| 1 — independent implementation | NIST Chemistry WebBook, SRD 69, isothermal tables, retrieved 2026-09-06 |

### Uncertainty, captured from the sources

| Quantity | Stated uncertainty |
| --- | --- |
| Sotiriadou 2025 correlation, **liquid to 33 MPa** | **3 % (k = 2)** |
| Diller 1980 | 2 % accuracy, 0.5 % precision |
| Haynes 1973 | 2 % |
| Boon 1967, saturated liquid | 1 % |
| Slyusar 1974 | 4 % |

The 2025 paper compares itself against the friction-theory model in the liquid
and reports that **"the performance of both correlations is similar"**, at the
same ~3 % level.

### Reference values obtained

* Sotiriadou 2025 Table 8, saturated liquid: 100 K → 154.50 µPa·s;
  120 K → 98.180; 150 K → 56.233.
* NIST WebBook isotherms at **100, 110, 120, 125 K** × **0.5 … 3.0 MPa** in
  0.5 MPa steps — **24 states, every one reported `liquid`**, 8 significant
  digits.

---

## GATE A verdict: **PASS**

| Blocking item | Result |
| --- | --- |
| Provider model identified exactly | friction theory, `QuinonesCisneros-JPCB-2006`, coefficients read from CoolProp's own JSON |
| Intended envelope explicit | 100–125 K, 0.5–3.0 MPa, liquid, p ≥ 1.5·p_sat |
| Independent authoritative evidence | Sotiriadou 2025 evaluated correlation; Diller 1980 primary experiment; NIST WebBook |
| Multi-point validation | **24 states**, 4 T × 6 p, 0 failures |
| Uncertainty captured | 3 % (k=2) reference; 2 % Diller; 1 % Boon |
| Evidence-derived criterion | 3 %, the published expanded uncertainty — not chosen, not widened |
| Units proven | inside band; ×1000, ÷1000, ×1e6 mutations all detected; no conversion in the adapter |
| Phase proven | 6/6, two-phase withholds viscosity entirely |
| No hidden extrapolation | whole box inside Diller's measured range |
| Cross-model difference classified | worst 2.885 % vs the WebBook, explained by the **three-way spread**: CoolProp is 0.734 % from the 2025 reference where the WebBook is 2.294 % the other way |
| Determinism | identical repeats, A/B/A clean |
| Outliers | none unexplained |

Document: `docs/engineering/METHANE_TRANSPORT_VALIDATION.md`.

## GATE B verdict: **ACCEPTED / FROZEN**

**LINE API v1.0** — 7 files, digest
`3de3a979b7ce7ea2acd37a20e1a028671411506bbea5d3f97bb290713c5cca4d`.

| | |
| --- | --- |
| Reynolds identity | residual 0.0 |
| Hagen-Poiseuille identity | worst 3.9e-16 |
| Colebrook vs an independent Decimal bisection | 48 cases, worst 1.3e-14 |
| Colebrook residual / iterations | 4.4e-14 / 15 |
| Fanning-for-Darcy mutation | detected, 75 % error |
| Canonical LCH4 case vs independent recomputation | ≤ 2.7e-16 |
| Line ρ, μ vs the fluid state | bit-identical |
| Transition band | friction factor withheld, never interpolated |
| Source ↔ packaged | 149 fields, 0 differences |
| Self-tests | 8 / 8 exit 0 |
| Qt messages | 0 |

## Final test counts

| Suite | Result |
| --- | --- |
| Base (`.venv`) | **6831 passed, 154 skipped**, exit 0 |
| Production (`.venv-cea`) | **6986 passed, 2 skipped**, exit 0 |
| Repeat | **6986 / 2 — identical** |
| Added | **+183** in each environment |

---

## Files created

`docs/engineering/implementation/TRANSPORT_LINE_CHECKPOINT.md`.

## Files modified

*(none yet)*

---

## Frozen manifest state

Compressible 22/22 byte-identical. Every prior contract reproduces. CEA
Provider v1.0 restored and digest-verified after the incident above. LINE API
v1.0 newly frozen.

## Current blockers

None. The gap this workstream existed to close — methane viscosity compared
between two software packages rather than validated against evidence — is
closed with primary sources, a derived envelope, an evidence-based criterion
and a three-way reference spread that explains the residual.
