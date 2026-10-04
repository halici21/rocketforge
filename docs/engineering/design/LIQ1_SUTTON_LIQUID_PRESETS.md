# LIQ-1 — Sutton liquid propellant presets

The liquid bipropellant combinations of Sutton & Biblarz, *Rocket Propulsion
Elements*, 9th ed. (2017), Table 5-5, are selectable in the Thermochemistry
workspace and solved through the existing NASA CEA 3.3.4 chamber path. Twelve
of the fourteen are executable; the two red fuming nitric acid (RFNA) pairs are
blocked because the source never defines RFNA's composition.

## Where it lives

| Part | Location |
| --- | --- |
| Reactant definitions, CEA ranges | `rocketforge/providers/cea_liquid/propellants.py` |
| N/F product sets, formulae, phase reading | `rocketforge/providers/cea_liquid/species.py` |
| Provider (frozen provider + product-set selection) | `rocketforge/providers/cea_liquid/provider.py` |
| Preset catalogue (pair, O/F, blocker, source) | `rocketforge/application/analysis/thermochemistry_presets.py` |
| Selector | `ui/pages/thermochemistry/ThermoCalculator.qml`, `ThermochemistryController.presetOptions` / `applyPreset` |

`rocketforge/providers/cea` is byte-frozen (`freeze_cea_provider_v1_1`) and is
**not modified**. The extension is a sibling package, the route
`SOLID_PROPELLANT_R1_ARCHITECTURE.md` set for `cea_solid`. `CEALiquidProvider`
subclasses the frozen provider: it supplies an explicit product set when the
frozen selection cannot be trusted, widens the species table, and checks the new
reactants' ranges. The mapping, solve, conversion, element balance, state
identities, warnings and provenance are the frozen provider's. For LOX/LCH4,
LOX/LH2 and GOX/GCH4 the request reaches the frozen provider untouched, and the
results are bit-identical (tested).

## Support matrix

| Sutton oxidiser | Sutton fuel | CEA reactants | Mixture basis | Status |
| --- | --- | --- | --- | --- |
| Oxygen | Methane | `O2(L)` / `CH4(L)` | — | executable |
| Oxygen | Hydrazine | `O2(L)` / `N2H4(L)` | — | executable |
| Oxygen | Hydrogen | `O2(L)` / `H2(L)` | — | executable |
| Oxygen | RP-1 | `O2(L)` / `RP-1` | — | executable |
| Oxygen | UDMH | `O2(L)` / `C2H8N2(L),UDMH` | — | executable |
| Fluorine | Hydrazine | `F2(L)` / `N2H4(L)` | — | executable |
| Fluorine | Hydrogen | `F2(L)` / `H2(L)` | — | executable |
| Nitrogen tetroxide | Hydrazine | `N2O4(L)` / `N2H4(L)` | — | executable |
| Nitrogen tetroxide | 50 % UDMH + 50 % hydrazine | `N2O4(L)` / `C2H8N2(L),UDMH` 0.5 + `N2H4(L)` 0.5 | mass | executable |
| Nitrogen tetroxide | RP-1 | `N2O4(L)` / `RP-1` | — | executable |
| Nitrogen tetroxide | MMH | `N2O4(L)` / `CH6N2(L)` | — | executable |
| Red fuming nitric acid | RP-1 | — | — | **blocked** |
| Red fuming nitric acid | 50 % UDMH + 50 % hydrazine | — | — | **blocked** |
| Hydrogen peroxide (90 %) | RP-1 | `H2O2(L)` 0.9 + `H2O(L)` 0.1 / `RP-1` | mass | executable |

Every name was verified in cea 3.3.4's `thermo.lib` (sha256 `8e5df1cc…`) through
`cea.Reactant` and a one-species `cea.Mixture`. Each reactant formula was read
from its database record, and each curated formula is checked against CEA's own
molar mass. `RP-1` is CEA's pseudo-species C 1.00 H 1.95. `H2O(L)` is not listed
by `cea.Reactant` but is accepted and temperature-dependent through `cea.Mixture`.

## Mixture bases

Sutton prints "50 % UDMH / 50 % hydrazine" and "hydrogen peroxide (90 %)"
without saying mass or mole. Both are read **by mass**:

- Aerozine-50 by mass is the convention `09` §4.3 already fixes.
- HTP concentrations are weight percent.
- Table 5-5 itself discriminates between the readings:

| Case | By mass | By mole | Sutton |
| --- | --- | --- | --- |
| HTP-90 / RP-1, O/F 7.0 | 2773 K, M 21.70 | 2884 K, M 21.97 | 2760 K, 21.7 |
| NTO / Aerozine-50, O/F 1.62 | 3241 K, M 20.96 | 3153 K, M 20.51 | 3242 K, 21.0 |

## RFNA verdict: blocked

- **The source gives no composition.** Sutton defines RFNA only as nitric acid
  with "5 to 20 %" (Table 7-1, note a) or "5 to 27 %" (§7.2) dissolved NO₂. It
  states no water content and no composition for Table 5-5.
- **The database has no RFNA entry.**
- **`IRFNA` is a different substance.** Its record is H 1.57 N 1.63 O 4.7
  **F 0.02**: the fluoride-inhibited acid that Sutton names separately.
- **No custom reactant is invented.** Composing RFNA from `HNO3(L)` + NO₂ would
  require picking an NO₂ and water content that no source states.

IRFNA is therefore not offered under any name, and the two RFNA presets carry
this blocker instead of an O/F.

## Product species

The frozen selection knows only C/H/O. The new sets were measured against CEA's
own `products_from_reactants`:

| System | Pairs | Set | Truncation cost |
| --- | --- | --- | --- |
| H/O, C/H/O | accepted pairs, LOX/RP-1, HTP-90/RP-1 | the frozen sets, by reference | C/H/O at RP-1: ΔTc ≤ 4.4e-4 K |
| H/O/N | LOX & NTO / N₂H₄ | CEA's complete 32 | zero |
| H/F | LF₂ / LH₂ | CEA's complete 11 | zero |
| H/N/F | LF₂ / N₂H₄ | CEA's complete 30 | zero |
| C/H/O/N | LOX/UDMH, NTO/A-50, NTO/RP-1, NTO/MMH | 77 of 161 (≥ 1e-10 anywhere in the nozzle, 5–200 bar, 0.5–2× O/F) | ΔTc ≤ 1.2e-7 K |

A pair whose element system has no curated set (LF₂ with a carbon fuel, for
example) is refused.

### Two frozen-provider behaviours found on the way

Both are worked around in `cea_liquid`. The frozen package is unchanged.

1. **Unknown composition keys silently pick the H/O set.** The frozen
   `select_product_species` reads elements from composition keys and skips any
   key with no formula. RP-1 (key `RP-1`) with LOX was read as oxygen-only and
   given H/O products. NASA CEA then **aborted the whole process** ("Element
   lists for products and reactants must match"), which is not a catchable
   error. It is unreachable with the five Phase 5C reactants. `cea_liquid`
   hands the frozen selection only requests whose every key it knows, and
   refuses any product set that lacks a reactant element before CEA is called.
2. **Condensed species must follow the gases.** With `H2O(L)` sorted among the
   gases, CEA returned `converged = True` and a 758 K chamber for O₂/UDMH. Every
   new set lists gases first. The frozen C/H/O set has `C(gr)` mid-list, which
   costs 4.4e-4 K at O₂/RP-1, below its documented truncation cost.

## Comparison with Table 5-5

The comparison is in `tests/providers/cea_liquid/test_sutton_table_5_5.py`. Only
the compared quantities are transcribed, in a test fixture.

**Conditions:** 1000 psia chamber, exit at 14.7 psia, reactants at their CEA
reference temperatures. Sutton states none.

**Semantics:**

- Chamber temperature, M and k come from the HP chamber.
- Shifting Isp and c* come from CEA's equilibrium expansion.
- Frozen Isp comes from the expansion frozen at the chamber.
- Both expansions use the area ratio whose exit pressure is 1 atm.
- k is compared with cp/cv frozen. The test shows every printed k is nearer
  that than γs.

**Bands:** 3 % for T, c\*, Isp and k, and 5 % for M. These are a
classification threshold, not a fitted tolerance. 87 of the 97 compared cells
fall inside. The ten outside are each classified, and the classification is
tested:

| Cells | Classification | Evidence |
| --- | --- | --- |
| LOX/LH₂ O/F 3.40, T | source inconsistency | the row's c\*, M and Isp agree within 1.1 % |
| LF₂/N₂H₄ Isp, both rows | source columns swapped | "shifting 334" is the frozen value at 1.83; "frozen 365" is the shifting value at 2.30 |
| NTO/N₂H₄ T, both rows | source rows swapped | 3258 K matches O/F 1.34, 3152 K matches 1.08 |
| c\* at NTO/A-50 1.62, NTO/MMH 1.65 | source inconsistency | c\* 5–10 % low on both the equilibrium and frozen basis, and below the ideal c\* of the row's own T, M and k, while the same row's Isp agrees |
| c\* at LF₂/N₂H₄ 1.83 | source basis, not an error | 2128 m/s is the frozen-throat c\*: it equals the ideal c\* of the row's own T, M and k and agrees with CEA's frozen c\* within 0.6 %. It is outside the band only against the equilibrium c\* compared here |
| frozen Isp 297 s for NTO/RP-1 and HTP-90/RP-1 | source inconsistency | the rows' T, M and k agree within 1.5 %; the ideal frozen Isp from those values is 262 and 260 s |

**Source audit.** The cells were re-read from the page image of the 9th-edition
PDF (p. 180), not from the fixture. That page is typeset text with embedded
fonts and no raster image, so it has no OCR layer to be wrong. The fixture
matches the printed page in every transcribed cell. All nine source
inconsistencies are therefore in the table as published, not transcription
errors. Each one is also confirmed by Sutton's own numbers. Ideal-gas c\* and
frozen Isp recomputed from the row's printed T, M and k single out the same
cell that CEA flags.

No cell was classified as a RocketForge defect. RocketForge's own single-γ
ideal performance (Rocket Performance workspace) completes for every preset.
With the frozen basis, its Isp is within about 1.2 % of CEA's frozen
expansion at the Table 5-5 rows. That figure is measured, not asserted by a
test.

## Presets

A preset sets the oxidiser, the fuel, Sutton's O/F and each stream's reference
temperature. It never solves. The O/F is Table 5-5's shifting-equilibrium row
where two are printed. For LF₂/N₂H₄ that is O/F 2.30, because the table's
columns are swapped for that pair. The chamber pressure is left as the user set
it.
