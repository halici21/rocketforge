# DB-0 — Proposed DB-1 schema for a reference engine database

> **Implemented as DB-1** in `rocketforge/evidence/engines`; the production contract is
> [docs/engineering/design/DB1_REFERENCE_ENGINE_EVIDENCE_SCHEMA.md](../../engineering/design/DB1_REFERENCE_ENGINE_EVIDENCE_SCHEMA.md).
> This proposal is kept as the research record that led to it.

Proposal only. Nothing here is implemented, and nothing changes the accepted
`rocketforge.evidence` package. The proposal is derived from what the DB-0
corpus needed to hold, and every structural feature below is justified by a
real engine (cited) that a simpler schema could not represent.

## 1. What the existing evidence model already gets right

`rocketforge/evidence/values.py` and `records.py` already encode the four
principles DB-0 needs:

| Existing concept | Keep as-is for engines |
| --- | --- |
| `ReportedValue(value, unit, source_id, locator, status, decimals/significant_figures, note)` | Yes — value **as printed**, in the printed unit, never converted at rest |
| `ValueStatus` REPORTED / DERIVED / DIGITISED / INFERRED | Yes |
| `Missing(reason, note)` with `Datum = ReportedValue \| Missing` | Yes — a field is never silently absent |
| `SourceReference` with `tier`, `access_class`, `rights_statement` ("not inferred"), `shipping` | Yes, extended (§4.9) |
| `validate_against_sources`: only VALUES_WITH_ATTRIBUTION sources may supply shipped values | Yes |
| Capability per dimension, no overall score (`EvidenceStatus`) | Yes — the same "no GOLD label" rule should apply to engines (§6) |

## 2. Where the existing model breaks on real engines

Each line is a concrete failure found in DB-0 data.

| # | Gap | Breaking example |
| --- | --- | --- |
| G1 | `ReportedValue.value` is a float. Engine facts are also enumerations (cycle "LOx rich, closed cycle, staged combustion"), ranges (RD-180 throttle "47–100%" vs "40–100%"), integers with meaning (chamber count), and text (injector type) | RD-180, BE-4, every cycle claim |
| G2 | No **condition** qualifier. Thrust without sea level / vacuum, Pc without absolute/gauge and injector-face/nozzle-stagnation, Isp without engine/chamber basis are ambiguous | SSME "491,000 lbf at 104.5%" was labelled sea level in a summary and is the vacuum value by arithmetic (us_hist conflict) |
| G3 | No **operating point**. One variant has several rated points | RS-25 100/104.5/109/111% power levels; J-2 MR 5.5 and 4.5; BE-4 640,000 → 220,000 lbf; MR-80B > 100:1 |
| G4 | No **effective date / rating epoch** for a value. Manufacturers re-rate the same designation in place | Merlin 1D 147,000 → 170,000 → 190,000 lbf; BE-3U 160,000 → 173,000 → 200,000 lbf; F-1 1.500 → 1.522 Mlbf "after the third Saturn V launch" |
| G5 | `MissingReason` lacks `ACCESS_BLOCKED` and names rights withholding `WITHHELD_RIGHTS` (DB-0 brief calls it `RIGHTS_RESTRICTED`) | Every DB-0 value: the documents exist but could not be opened |
| G6 | `SourceReference.tier` is 1–3. DB-0 needs A–E to separate agency/manufacturer, peer-reviewed, textbook, encyclopedic and forum sources, and a separate **access** state (`search_result_only`) | All DB-0 sources |
| G7 | One `shipping` decision per source; rights differ by content kind | Huzel & Huang 1992: values OK, figures not (RIGHTS_MATRIX.md §1) |
| G8 | No place for a **secondary claim** distinct from a primary report. Proposal: do **not** add a `ValueStatus`; a value is REPORTED *by* a source, and the source's tier/primary flag says how far it is from the hardware | Merlin cycle "gas generator": REPORTED by Wikipedia (Tier D), never by SpaceX |
| G9 | No entity for family/variant/configuration, no topology, no subsystem objects | see §3 |

## 3. Entities

```
EngineFamily 1─* EngineVariant 1─* EngineConfiguration 1─* OperatingPoint
                       │                    │
                       │                    ├─ ThrustChamberAssembly (1..n, with role main|vernier|steering)
                       │                    │      ├─ Injector ─ StabilityDevice*
                       │                    │      ├─ Chamber   (cooling zones*)
                       │                    │      └─ Nozzle    (sections*: regen / extension / extendible)
                       │                    ├─ TurbopumpAssembly* ─ Shaft* ─┬ Pump* (─ Inducer?, stages)
                       │                    │                               ├ Turbine* (gas or hydraulic)
                       │                    │                               └ Gearbox?
                       │                    ├─ Combustor* (role: gas_generator | preburner_fuel_rich | preburner_ox_rich | steam_generator)
                       │                    ├─ EnergyStore* (battery, start tank, start cartridge, pressurant)  [electric pump, starts]
                       │                    ├─ ControlEffector* (valve, regulator, bypass, PU valve) + Sequence*
                       │                    ├─ IgnitionSystem*
                       │                    └─ FeedTopology (TopologyNode*, TopologyEdge*)
                       └─ Lineage edges (derived_from, uprate_of, licence_of, renamed_from, export_of, module_of)

VehicleInstallation (stage/vehicle) ─* EngineConfiguration (count, position, role)
      └─ PressurizationSystem, PropellantManagement, stage feed ducts (SYS-1..5 objects)

SourceRecord 1─* Assertion ─? OperatingPoint
Assertion: (subject, field_path, value|Missing, unit, conditions, status, source_id, locator, epoch, confidence)
FlowSchematic ─* TopologyNode/Edge provenance
RightsRecord (per source, per content kind)
Conflict  ─* Assertion (≥2, never averaged)
Alias ─ EngineFamily | EngineVariant (with kind and sources)
```

### 3.1 Identity layer

| Entity | Key fields | Why it exists (breaking example) |
| --- | --- | --- |
| `EngineFamily` | `family_id`, name, developer(s), country(ies), notes | RL10 spans 1960s A-1 to C-X with different cycles of hardware; RD-170 family spans 4-chamber RD-170/171/171M, 2-chamber RD-180 and 1-chamber RD-191/181/151/193 |
| `EngineVariant` | `engine_id`, designation, family_id, parent variant, relation, status, period, roles | RL10A-4-2 vs RL10B-2 have different nozzles, extendible extension, thrust; NK-33 → AJ26-58/59/62 (the AJ26 mapping of NK-43 is itself disputed) |
| `EngineConfiguration` | `config_id`, variant, block/rating label, effective dates | SSME FPL / Phase II / Block I / Block IIA / Block II; Merlin 1D epochs; F-1 pre/post SA-504 rating |
| `OperatingPoint` | `op_id`, configuration, label (e.g. "104.5% RPL", "MR 4.5"), environment (sea level / vacuum / altitude), throttle %, MR | RS-25, J-2, BE-4, MR-80B |
| `Alias` | name, kind (native, transliteration, GRAU index, manufacturer index, military, export, former name, module name), target, sources | RD-170 = 11D521 (only via a reference title); RD-107A = 14D22; NK-33 = 11D111 or 14D15 (conflict); RD-0212 = 8D49 is a **propulsion system** made of RD-0213 + RD-0214 |
| `LineageEdge` | from, to, kind (`derived_from`, `uprate_of`, `licence_of`, `renamed_from`, `export_of`, `module_of`, `powerpack_from`), sources | Viking → Vikas (licence, separate engines); S-3D → RZ.2 (Rolls-Royce licence); RD-0146 → MR10; M10 → MR10 (rename, 2024); YF-20 → YF-21 (module of four) |

Rules:
- **Facts attach at the lowest level the source supports.** A value printed for
  "the RL10" without a variant attaches to the family with `scope=family` and
  is **never copied down** to variants. A reader may *display* it on a variant
  as "family-level, variant unknown"; a validator must refuse to use it as a
  variant value.
- **Configuration overrides variant; variant overrides family** only for
  identity-level descriptors (names, roles). Numeric performance never
  inherits.
- An engine **module** (YF-21) and a **propulsion system** (RD-0212, Atlas
  MA-5) are entities of their own with `module_of` edges, not variants.

### 3.2 Hardware layer

| Entity | Key fields | Breaking example |
| --- | --- | --- |
| `ThrustChamberAssembly` | count, role (`main`, `vernier`, `steering`), gimbal per chamber, shared turbopump ref | RD-107 = 4 main + 2 vernier on one turbopump; RD-108 = 4 + 4; RD-0124 = 4 chambers; RD-0110 = 4 chambers + GG-exhaust steering nozzles |
| `Injector` | element class, element count, Δp per propellant **per operating point**, stability devices list | LE-5B (180 coaxial elements) vs LE-5B-2 (306) — same family, different injector |
| `CoolingZone` | zone, method, coolant, path, channel/tube count | F-1: regen tubes to ε 10, turbine-exhaust film to ε 16; Vulcain 2 tube nozzle + turbine-gas film; Vulcain 2.1 H2-cooled extension |
| `NozzleSection` | from ε, to ε, construction, cooling, extendible flag | RL10B-2 extendible extension; Merlin 1C Vac niobium extension |
| `TurbopumpAssembly` → `Shaft` → `Pump` / `Turbine` / `Gearbox` / `Inducer` | each pump: propellant, stages, type, inlet/outlet p, speed; each turbine: working fluid (gas **or liquid**), stages, inlet state, exhaust destination edge | RS-25 four turbopumps incl. LPOTP driven by a **hydraulic** (liquid-LOX) turbine; R-7 single axle with ox, fuel and H2O2 pumps; F-1 single shaft; geared H-1/RL10 (to verify) |
| `Combustor` | role, rich side, propellants, MR, p, T, flow fraction | RS-25 two fuel-rich preburners; Raptor and IPD one of each side; RD-170 one-vs-two dispute |
| `EnergyStore` | kind (battery, start tank, solid start cartridge, pressurant bottle, H2O2 tank), owner (engine/stage) | Rutherford batteries; J-2 GH2 start tank; LR87 solid start cartridge; R-7 H2O2 and LN2 |
| `ControlEffector` / `Sequence` | valve, regulator, bypass, PU valve; ordered start/shutdown steps with times | Apollo SPS primary/secondary regulators at different set points; LE-9 electro-mechanical valves and closed-loop control; RL10 turbine bypass |

### 3.3 Topology layer (first-class)

```
TopologyNode { node_id, component_type, label, subsystem_owner: engine|stage|vehicle|ambiguous,
               hardware_ref?, provenance: [Evidence] }
TopologyEdge { edge_id, from, to, fluid, phase?, role, split_group?, merge_group?,
               state_annotations: {p?, T?, mdot?} as Assertions (per operating point),
               provenance: [Evidence] }
Evidence     { status: SHOWN_IN_SCHEMATIC | REPORTED_IN_TEXT | DERIVED_FROM_BOTH | INFERRED | UNKNOWN,
               source_id, locator (figure/page), schematic_id? }
```

Plus two additions the anchors forced:
- **Mechanical edges** (`role = mechanical_shaft`, `fluid = none`) between a
  turbine and the pumps on its shaft, and **gear edges** with a ratio. Without
  them, "pumps share a shaft" and "shafts are geared" cannot be stated.
- **Energy edges** (`role = electrical_power`) battery → motor → pump for
  electric-pump engines (Rutherford).

And one rule: **completeness is a property of the graph, not of each node.**
Each topology carries `completeness: {declared_complete: false, known_omissions:
[…]}`. A component absent from the graph is `NOT_SHOWN`, never "absent".
Absence is asserted only with an explicit `ABSENT` node that cites a source
saying so.

### 3.4 Evidence layer

```
Assertion {
  assertion_id
  subject: (entity_type, entity_id)          # family | variant | configuration | operating point | hardware | node | edge
  field_path                                  # e.g. performance.thrust, pumps.HPFTP.speed
  value: number | integer | range{min,max} | enum | text | Missing(reason, note)
  unit_as_printed, conditions{environment, pressure_basis(abs|gauge), pc_station, isp_basis(engine|chamber),
                              mr_basis(engine|chamber), throttle_pct, epoch/effective_date}
  status: REPORTED | DERIVED | DIGITISED | INFERRED
  derivation?: {inputs: [assertion_id], formula}  # DERIVED must show its arithmetic
  source_id, locator, retrieved_on, access: fetched|search_result_only|...
  confidence: high|medium|low, note
}
MissingReason: NOT_REPORTED | NOT_AUDITED | UNKNOWN | ACCESS_BLOCKED | RIGHTS_RESTRICTED
Conflict { conflict_id, field_path, subject, assertions: [≥2], explanation?, resolution: UNRESOLVED |
           EXPLAINED(kind: different_condition | different_epoch | different_variant | unit | typo | definition) }
```

Multiple independent reports of one value are **multiple assertions**. A
"display value" may be chosen by rule (highest tier, latest epoch, matching
condition), but the rule is stored and the others stay visible.

### 3.5 Source and rights layer

```
SourceRecord { source_id, title, authors, organization, year, source_type, identifiers{ntrs,doi,report,patent},
               url, tier: A|B|C|D|E, primary: primary|secondary|tertiary, access, access_checked_on,
               rights_statement (verbatim, never inferred), notes }
RightsRecord { source_id, values, figures, tables, text  (each a DB-0 rights class), basis, review_flag }
FlowSchematic { schematic_id, source_id, locator, title, type, detail, rights, verification, components_visible[] }
```

`SourceRecord.tier` A–E maps to the existing 1–3 as A/B → 1, C → 2, D/E → 3
for backwards compatibility. Shipping is derived from `RightsRecord.values`.

### 3.6 Installation layer

`VehicleInstallation { stage_id, vehicle, engine config refs with count and
position, pressurization system (SYS-4 modes + autogenous/warm-gas ports),
propellant management (SYS-3 modes), stage feed ducts (SYS-5 components) }`.
This is how RocketForge's existing SYS-1…SYS-5 objects meet the engine
database: **the stage owns tanks, pressurant and ducts; the engine owns ports.**

## 4. Stress test — the questions the brief requires

| Question | Answer | Real case |
| --- | --- | --- |
| Can one variant have several operating points? | Yes — `OperatingPoint` under `EngineConfiguration` | RS-25 104.5 / 109 %; J-2 MR 5.5 / 4.5; BE-4 640 → 220 klbf |
| Can one engine have several thrust chambers? | Yes — `ThrustChamberAssembly` with count and role | RD-170 (4), RD-180 (2), RD-0124 (4) |
| Can one turbopump feed several chambers? | Yes — topology edges from one pump outlet to n chamber manifolds; TCA refs the shared TPA | RD-107/108, RD-0110 |
| Can one engine have two preburners? | Yes — `Combustor*` | RS-25, Raptor, IPD, RD-270 |
| Can a pump have a booster pump? | Yes — a separate `Pump` (on its own shaft/TPA) with a feed edge into the main pump | RS-25 LPFTP→HPFTP, LPOTP→HPOTP; RD-170 boost pumps |
| Can pumps share a shaft? | Yes — `Shaft` with several `Pump`s, mechanical edges | F-1 Mk10; R-7 axle with H2O2 pump |
| Can shafts be geared? | Yes — `Gearbox` + gear edge with ratio (`Missing` when unreported) | H-1, RL10 ox pump (to verify) |
| Can one propellant split into several branches? | Yes — edges with `split_group` | RS-25 fuel: MCC cooling, nozzle cooling, preburners |
| Can cooling flow bypass the turbine? | Yes — bypass edge with a `ControlEffector` on it | RL10 turbine bypass valve [BG] |
| Can turbine exhaust return to the injector? | Yes — exhaust edge → injector node | every closed cycle |
| … dump overboard? | Yes — edge → `ambient` node | GG, tap-off, expander bleed |
| … inject into the nozzle? | Yes — edge → `NozzleSection` node | F-1, Vulcain 2 |
| … drive steering nozzles? | Yes — edge → `ThrustChamberAssembly(role=steering)` | RD-0110 |
| Can pressurization belong to the vehicle? | Yes — `subsystem_owner = stage`; the engine contributes a port node | S-IVB/J-2 HEX; Titan II GG gas and N2O4 superheater; every spacecraft |
| Can a schematic omit real components without declaring them absent? | Yes — graph `completeness`; absence only via cited `ABSENT` | all simplified schematics |
| Can conflicting assertions coexist? | Yes — `Conflict` over ≥ 2 assertions, never averaged | RD-180 Pc 3,722 vs 3,734 psia vs 261 kgf/cm² |
| Can a family hold facts without copying them to variants? | Yes — `scope=family`, no numeric inheritance | "RL10" values without a variant |
| Can configuration facts override family descriptors? | Yes for identity descriptors only | "RS-25" vs "RS-25D" roles and vehicles |
| Can one value have several independent reports? | Yes — several assertions | Vulcain 2 vacuum thrust 1340 / 1359 / 1390 kN (one Tier A) |
| Can a source be scientifically strong but rights-restricted? | Yes — tier and `RightsRecord` are independent | Huzel & Huang 1992; JAXA papers |
| Can data stay missing without breaking serialization or the UI? | Yes — `Missing(reason)` is a value; the UI already distinguishes refusal/unavailable (rf-scientific-ui-contract) | most fields of most engines |

### Cases that broke simpler assumptions (from DB-0)

1. **"One engine, one thrust."** Merlin 1C had two ratings for two vehicles
   (Falcon 1: 78,000/90,000 lbf; Falcon 9: 95,000/>108,000 lbf, 2007 SpaceX
   release) → two configurations.
2. **"Thrust is per engine."** Merlin 1D "7,605 kN" is a nine-engine stage
   total; RD-0124MS is described as "two blocks of two chambers"; YF-40 "≈100
   kN" may be per unit or per stage (unresolved).
3. **"The designation is the engine."** RD-0212, Atlas MA-5, YF-21 are
   propulsion systems or modules.
4. **"One cycle per family."** BE-3PM (tap-off) vs BE-3U (open expander);
   LE-5 (GG) → LE-5A/B (expander bleed); LE-7A (staged) → LE-9 (expander bleed)
   in successor families.
5. **"Two propellants."** A4, R-7 and Redstone need a third fluid (H2O2) plus a
   catalyst and an inert pressurant (R-7 LN2).
6. **"A turbine is driven by gas."** RS-25 LPOTP and RD-170 fuel boost pump are
   driven by liquid hydraulic turbines (to verify, [BG]).
7. **"Cooling is one method."** F-1, Vulcain 2, RL10B-2 each have 2–3 methods
   by zone.
8. **"A rating is permanent."** Merlin 1D, BE-3U, Rutherford, F-1 were
   re-rated under one designation.
9. **"Isp is a property of the engine."** Rocket Lab labels 311 s as
   Rutherford's sea-level Isp, which is physically doubtful for that engine
   class (kept as a conflict, not corrected).
10. **"Names are stable."** M10 → MR10 (2024); "RD-124MV" in press is almost
    certainly a garbling of RD-0124MS; GRAU indices are disputed (NK-33 11D111
    vs 14D15).
11. **"Countries are single-valued."** Rocket Lab (NZ/US), RD-181/AJ26 (Russian
    hardware, US designation), Aestus II/RS-72 (US powerpack + German chamber),
    MR10 (Italian derived from Russian RD-0146).
12. **"Engine data excludes stage hardware."** R-7's LN2 evaporator and the
    S-IVB helium heat exchanger are engine-mounted hardware serving the stage.

## 5. Worked example (illustrative structure only — values are DB-0 search-summary evidence)

```json
{
  "family": {"family_id": "FAM-RD-170", "name": "RD-170 family"},
  "variant": {"engine_id": "ENG-RU-RD-180", "designation": "RD-180", "family_id": "FAM-RD-170",
              "lineage": [{"kind": "derived_from", "to": "ENG-SU-RD-170",
                           "note": "70% parts commonality claimed", "status": "REPORTED"}]},
  "configuration": {"config_id": "CFG-RD-180-ATLAS-V", "label": "Atlas III/V flight engine"},
  "operating_points": [{"op_id": "OP-100", "label": "100% rated", "environment": ["sea_level", "vacuum"]}],
  "assertions": [
    {"subject": ["operating_point", "OP-100"], "field_path": "performance.thrust",
     "value": 860200, "unit_as_printed": "lbf", "conditions": {"environment": "sea_level"},
     "status": "REPORTED", "source_id": "SRC-ULA-RD180-RECORD", "locator": "summary only",
     "access": "search_result_only", "confidence": "low"},
    {"subject": ["operating_point", "OP-100"], "field_path": "performance.pc",
     "value": 3722, "unit_as_printed": "psia", "conditions": {"pressure_basis": "abs", "pc_station": "UNKNOWN"},
     "status": "REPORTED", "source_id": "…", "access": "search_result_only"}
  ],
  "conflicts": [{"field_path": "performance.pc", "assertions": ["3722 psia", "3734 psia", "261 kgf/cm2"],
                 "resolution": "UNRESOLVED"}],
  "thrust_chambers": {"count": 2, "role": "main", "shared_turbopump": "TPA-1"},
  "combustors": [{"id": "PB-1", "role": "preburner_ox_rich", "count": {"Missing": "NOT_AUDITED"}}],
  "topology": {"completeness": {"declared_complete": false,
                                "known_omissions": ["boost pumps", "valves", "ignition", "fuel cooling paths"]}}
}
```

## 6. Capability, not quality score

Following `EvidenceStatus`, an engine record should state what it can support
**per use**, never a single grade:

| Use | Requires |
| --- | --- |
| `IDENTITY` | family, variant, developer, country, status, propellants with sources |
| `ARCHITECTURE` | feed, cycle axes B1–B3 with REPORTED status from Tier A/B |
| `PERFORMANCE_REFERENCE` | thrust, Pc, MR, Isp, ε at a defined operating point and condition, Tier A/B |
| `REGRESSION_CANDIDATE` | the above, fetched (not search-only), VALUES_WITH_ATTRIBUTION, no unresolved conflict on the fields used |
| `TOPOLOGY` | a topology graph whose nodes/edges are SHOWN_IN_SCHEMATIC or REPORTED_IN_TEXT from a located figure |

No DB-0 record reaches `REGRESSION_CANDIDATE`: nothing was fetched.

## 7. Recommended DB-1 scope

1. Implement the evidence-layer extensions first (G1–G8): typed `Assertion`
   value (number/range/enum/text), `conditions`, `OperatingPoint`, `epoch`,
   `MissingReason.ACCESS_BLOCKED` (and decide `RIGHTS_RESTRICTED` vs the
   existing `WITHHELD_RIGHTS`), A–E tier with backwards mapping, per-content
   rights. Keep `ReportedValue` unchanged; add engine types alongside it.
2. Identity layer (family, variant, configuration, alias, lineage) with the
   no-numeric-inheritance rule enforced by a validator.
3. Topology graph with mechanical and electrical edges and graph-level
   completeness.
4. Hardware entities only as far as the first production corpus needs (§8 of
   [DB0_RESEARCH_OVERVIEW.md](DB0_RESEARCH_OVERVIEW.md)).
5. Versioned JSON with a schema version and strict refusal of unknown fields,
   like `rocketforge/evidence/load.py`.

## 8. Changes forced by DB-0.5 opened sources (2026-10-08)

Reading the documents themselves broke the proposal in the following places.
Each item names the document that forced it. Nothing here is implemented.

| # | Change | Forced by |
| --- | --- | --- |
| S1 | `Assertion.configuration` (the configuration the *printed text* describes) separate from the record's subject. A document about one variant routinely prints values for another. | TN D-7375 prints 21,500 lb / 102 psia / 309 s under its **Block I** heading; BC98-04's state-point schematic is **Block IIA** inside a Block II-era book; the SDES H-1 volume is the **SA-10 188K** engine |
| S2 | `value_kind`: `rated` / `nominal` / `limit` / `burst` / `prediction` / `design_goal` / `demonstrated` / `average` / `approximate`. `status` alone cannot say a number is a limit. | JSC-19041 "maximum allowable HPOT ≈30,000 rpm" (DB-0 read it as an operating speed); 1986 large-throat Pc 3,010 psia is a prediction; F-1 "1.8 million pounds" was a demonstration; SPS Isp is an "average"; OMS Pc "approximately 130 psia" |
| S3 | `pc_station` must be an explicit enum including `nozzle_stagnation`, `injector_face` and `UNSTATED`, and must be required. | Rocketdyne prints J-2 717 psia and J-2S 1,200 psia "(nozzle stagnation)"; F-1, RL10, RS-25 sources do not state a station |
| S4 | `RightsRecord` keeps the repository determination **and** the printed notice side by side, with a `conflict` flag; the stricter one governs until reviewed. | MSFC-MAN-503 (NTRS public use vs printed reproduction restriction); AIAA 97-2687 (NTRS vs AIAA copyright); BC98-04 "BOEING PROPRIETARY" on a public website |
| S5 | `SourceRecord.content_sha256`; two source ids with one hash are one document. | TN D-7143 = SRC-NASA-AER-DPS; NTRS 20040084662 registered twice |
| S6 | Provenance chain on an assertion: `origin` (who first stated it) separate from `source_id` (where it was read). | RD-170 placard values (manufacturer) are known only through Rockwell's 1990 transcription |
| S7 | `FlowSchematic.provenance_class`: `manufacturer` / `agency` / `third_party_reconstruction` / `training_simplification`. `SHOWN_IN_SCHEMATIC` on a reconstruction must not count toward the `TOPOLOGY` capability. | Rockwell's "RD-170 schematic based on 1989 Paris Air Show photos", with '?' marks on paths |
| S8 | `DIGITISED` assertions carry `digitised_from = {schematic_id, callout}`; numbers in an illegible scan are recorded as `ILLEGIBLE`, never guessed. | BC98-04 slide 19 state points (legible); AIAA 97-2687 Fig. 1 state points (bilevel scan, illegible at 300 dpi) |
| S9 | Topology edge roles beyond `mechanical_shaft` and gear: `mechanical_linkage` (valve-to-valve, actuator-to-injector) and `accessory_drive`. | LMDE throttle actuator ganged to cavitating-venturi valves and the injector sleeve; OMS fuel and oxidizer ball valves linked in pairs; J-2 hydraulic pump driven by the oxidizer turbine; H-1 accessory drive pads |
| S10 | `Assertion.disposition` beyond status: `PROMOTED`, `REJECTED_FOR_VARIANT` (stale text in a later document), `NOT_PROMOTED_MODEL_PARAMETER` (tuning values in modelling papers). | JSC-19041 Rev F (2003) still prints the pre-large-throat 77.5:1; CR-195478's discharge coefficient 0.975 is a model trim |
| S11 | Document edition as an epoch: the same sentence can change between editions of one manual. | OMS Pc band "100–102%" (JSC-19950, 1995) vs "100–106%" (USA006500, 2006) |
| S12 | Conflicts may be **intra-document**; `Conflict` needs `scope = intra_document / inter_document`. | NRC 2006 prints RL10B-2 633 psi / 465.5 s in text and 644 psia / 466.5 s in its table; NTRS 19910018906 uses MR 2.58 and 2.47 |
| S13 | Component nodes need finding numbers / part ids as optional identifiers, because mechanical schematics name components only by them. | H-1 SDES Fig. 3-1 (B4, B19, B23, B39, B49 …) |

The §6 capability rule held up: applied to the opened evidence it yields five
`REGRESSION_CANDIDATE` sets ([db05/regression_candidates.json](db05/regression_candidates.json))
and correctly blocks the RS-25 sea-level thrust (unresolved 0.5-1.3% spread between sources) and the
whole F-1 performance set (rating epoch unresolved).
