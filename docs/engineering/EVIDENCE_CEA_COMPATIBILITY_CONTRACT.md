# Evidence → NASA CEA compatibility (EV-3) — contract

Normative for the current implementation. The design research this builds on is
the R1 propulsion-knowledge blueprint (`integration_blueprint.md`, Gate D, §4 and
§7), a historical research artifact that is kept as written. Where this contract
and R1 differ, this contract describes the accepted behaviour, and §6 lists every
difference.

Code: `rocketforge/application/analysis/evidence_cea_bridge.py` (`access_gate()`,
`assess()`), the gateway function `probe_solid_library_species()` in
`thermochemistry_provider.py`, and `PropulsionEvidenceController`
(`checkCompatibility()`, `openInThermochemistry()`). Tests:
`tests/application/test_evidence_cea_bridge.py`,
`tests/application/test_propulsion_evidence_runtime.py`.

## 1. When anything happens

| Action | Access gate | Library probe | Formulation built | Solve |
| --- | --- | --- | --- | --- |
| Browsing (construct, select, filter, inspector, table, drawers, theme, resize, re-entry) | no | **0** | no | **0** |
| Check CEA compatibility (explicit) | yes | only if the gate permits, names not yet known (§3) | only if nothing blocks | **0** |
| Open in Thermochemistry (explicit, executable records only) | — | 0 | — | **0**; Thermochemistry arrives unsolved, the user presses Calculate |

A record that is not a CEA target (no propellant, or VA `NOT_APPLICABLE`) is
recognised from the record alone and offers no check.

## 2. The order of a check

1. **Record gate** (pure evidence): `NOT_A_CEA_TARGET`.
2. **Access gate** (pure evidence, `access_gate()`): may the check use this
   record's values at all? See §4.
3. **Structural and definition checks** (pure evidence): `UNDERDEFINED`,
   `BLOCKED_INCOMPLETE_CUSTOM`.
4. **Library probe** through the gateway: `LIBRARY_SPECIES_ABSENT` names the
   name and the `thermo.lib` sha256.
5. **Build** (physics re-validates): `EXECUTABLE_VERIFIED` /
   `EXECUTABLE_SOURCE_COMPLETE`; `PROVIDER_UNAVAILABLE` when no provider could
   be asked, which is not a block.

Nothing is normalised, substituted, re-spelled, converted or defaulted, and a
`Missing` value is never read as zero.

## 3. Library probes: once per process per `thermo.lib` identity

`CACHE POLICY = ONCE-PER-PROCESS`.

* What is cached: only whether a name, asked verbatim, is present in one
  `thermo.lib`. Never an assessment, a record's answer, a formulation or a
  solve.
* The key: (database, database sha256, library version, name). A name already
  asked of the same identity is answered from the cache; `LibrarySpeciesProbe.probed`
  lists the names a call actually asked.
* Why this is correct: the answer is a fact about one database, and a process
  holds one provider and one `thermo.lib`. `reset_provider_state()` — the only
  way a process re-reads its provider (Thermochemistry's `refreshProvider`) —
  drops the cache, and a different identity is a different key.
* Provider unavailable: nothing is probed and nothing is cached; the answer is
  `PROVIDER_UNAVAILABLE`.
* Answers stay with their record. Selecting another record shows "Not checked"
  until someone asks again, and a repeated check assesses again — reusing only
  the name lookups.

## 4. Rights and access: a separate gate before the assessment

`RIGHTS MODEL = SEPARATE GATE`.

A datum the check needs that the source states but this build withholds
(EV-1 `Missing(MissingReason.WITHHELD_RIGHTS)`) stops the check at the access
gate:

* `CompatibilityAssessment.state` is `None` — compatibility **not evaluated**.
  There is no rights value among the scientific states (`CompatibilityState`).
* `CompatibilityAssessment.access` is an `AccessDecision(permitted=False)`
  whose `AccessRestriction`s name each withheld datum (code `WITHHELD_RIGHTS`,
  field path, ingredient, the cited sources' shipping policies).
* `blockers` is empty: an access restriction is never a scientific blocker,
  never `UNDERDEFINED`, `BLOCKED_INCOMPLETE_CUSTOM`, `LIBRARY_SPECIES_ABSENT`
  or `PROVIDER_UNAVAILABLE`.
* Nothing is probed, nothing is built, nothing is solved, and no Open action exists.
* The page shows the presentation state `NOT_EVALUATED` — "Not evaluated ·
  access restricted" — with the restrictions listed apart from blockers, and
  says the check says nothing about the chemistry.

A permitted record (`AccessDecision(permitted=True)`) goes on to the assessment
unchanged. `NOT_CHECKED` and `NOT_EVALUATED` are presentation states of the
Propulsion Database; the bridge's own states are those in §2.

## 5. Open in Thermochemistry

Offered only after an `EXECUTABLE_*` answer whose evidence-built formulation
equals an existing Thermochemistry catalogue case field for field (the record's
`executable_key`, today `rp1311-example5`). It sets solid mode and loads that
case — the provider constant stays the executable authority — and routes the
shell there. It never calls `calculate()`.

## 6. Differences from R1

| R1 | Accepted | Why |
| --- | --- | --- |
| §4 lists no rights step | a separate access gate (§4) before the structural checks | a withheld payload is a limit on what ships, not a scientific finding, and must not be probed or read as a gap |
| §4 names only `LIBRARY_SPECIES_ABSENT` and `CUSTOM_THERMO_INCOMPLETE` | also `NOT_EXACT_FORMULATION`, `VALUE_MISSING`, `MASS_FRACTION_SUM`, `NO_THERMO_DEFINITION`, `AMBIGUOUS_THERMO_DEFINITION`, `UNIT_NOT_ACCEPTED`, `PHYSICS_REFUSED` | each names the reason R1's `UNDERDEFINED`/`BLOCKED` stands for |
| §7 "once per process (cached)" | kept, keyed by `thermo.lib` identity, cleared by `reset_provider_state()` | same rule, with the key stated |
| — | a missing grain temperature blocks; units must be CEA's own | nothing is defaulted or converted |
