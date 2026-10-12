# DB-4A — Reference Engine Regression Acceptance

Status: COMPLETE, with zero real-engine hard regressions accepted.

- Baseline: `670e2c6` (integrated into master by fast-forward, 2026-10-12).
- Review gate: `rocketforge/application/analysis/reference_engine_regression.py`.
- Tests: `tests/application/test_reference_engine_regression.py`.

| Totals | |
|---|---|
| Hard numerical regressions accepted | **0** |
| Non-locking validation comparisons accepted | **0** |
| Delivered-efficiency comparisons accepted | **0** |
| Candidates reviewed | **2**, both blocked at the quantity level |

The production reference-engine corpus is byte-for-byte unchanged.

## 1. What REGRESSION_CANDIDATE means, and what it does not

`REGRESSION_CANDIDATE` is an **evidence** capability (`rocketforge/evidence/engines/capabilities.py`). It is
SUPPORTED when the configuration's thrust, specific impulse, chamber pressure and mixture ratio are recorded
at one operating point, with an area ratio, and they pass `regression_blockers`:

- each value is admitted, from an opened source, under shipped rights;
- no open conflict touches it;
- the thrust and Isp environments are stated;
- none is an average or an approximation.

That makes the record **eligible to be reviewed** as a regression reference. It is not an accepted
regression, a validated solver or a known-good expected output. DB-4A is that review, and its answer for
every current candidate is "not a hard regression".

The capability's definition is consistent with its documented meaning. It is unchanged, and so is every DB-3A
label ("eligibility only").

## 2. The model a candidate would be compared with

RocketForge's ideal rocket performance (`rocketforge/engineering/nozzle/performance.py`):

- NASA CEA HP chamber equilibrium;
- reduced to a constant-gamma gas;
- expanded through a frozen ideal nozzle;
- **no efficiency of any kind**.

Its specific impulse and thrust are **ideal thrust-chamber** quantities. Three things the ideal value
depends on are visible model choices that no reference-engine source prints:

- the gamma strategy (chamber or throat);
- the gamma basis (frozen cp/cv or equilibrium gamma_s);
- the propellant inlet state of the cryogenic reactants.

The existing comparison layer (`rocketforge/comparison/cases.py`, `compare.py`) draws a verdict only against
`CEA_DIRECT` or `NASA_PUBLISHED` thermochemistry printouts. `EXPERIMENT` is reserved: differences only, no
verdict. There is **no accepted delivered/ideal efficiency comparison class**. Adding one is an owner decision
(§7); DB-4A did not add one.

## 3. Candidates reviewed

Two configurations are SUPPORTED by the production capability. The research file
`docs/research/engine_database/db05/regression_candidates.json` lists five candidates: the two above, plus three
the production capability rates NOT_SUPPORTED (its gaps, as it reports them):

- RS-25 at 109% (SLS), `CFG-RS25-SLS`: no shipped specific impulse, chamber pressure, mixture ratio or area
  ratio for the configuration.
- SPS Block I, `CFG-SPS-BLOCK-I`: the Isp (AS-DB05-US-AJ10-137-003) has no stated environment and is printed
  as an average. (An unstated Pc station and Isp basis are caveats, not the gaps.)
- RL10A-3-3A, `CFG-RL10A-3-3A`: the Isp (AS-DB05-US-RL10A-3-3A-010) has no stated environment.

So these three are not production candidates and were not reviewed as such.

### CFG-J2-230K — J-2, 230,000 lb nominal vacuum thrust rating

Source: NTRS 20100027318 PDF p.14, Rocketdyne viewgraph 'J-2 Basic Engine Features' (authority A).
Operating point: OP-J2-230K-MR55.

| Quantity | Assertion | Printed | Role | Result | Why |
|---|---|---|---|---|---|
| thrust | AS-DB05-US-J-2-001 | 230,000 lb, "Nominal vacuum thrust" | expected output | BLOCKED_MISSING_INPUTS | no engine size (throat area or mass flow) is recorded; the mixture-ratio input is blocked; delivered against ideal (see note) |
| specific impulse | AS-DB05-US-J-2-002 | 425 s, "Nominal vacuum specific impulse" | expected output | BLOCKED_SEMANTICS | engine or thrust-chamber basis not stated; the mixture-ratio input is blocked; delivered against ideal |
| chamber pressure | AS-DB05-US-J-2-003 | 717 psia, nozzle stagnation | input | INPUT_ELIGIBLE | absolute, at the station the model's Pc means |
| mixture ratio | AS-DB05-US-J-2-004 | 5.5:1 O/F, engine | input | BLOCKED_SEMANTICS | an ENGINE ratio: in a gas-generator engine it counts the generator's propellant, while the model takes the thrust chamber's (injector) ratio |
| area ratio | AS-DB05-US-J-2-007 | 27.5:1 | input | INPUT_ELIGIBLE | geometry |

### CFG-J2S — J-2S, as described by Rocketdyne's 'J-2S Basic Engine Features' viewgraph

Source: NTRS 19940016798 PDF p.9 (authority A). Operating point: OP-J2S-MR55.

| Quantity | Assertion | Printed | Role | Result | Why |
|---|---|---|---|---|---|
| thrust | AS-DB05-US-J-2S-001 | 265,000 lb, "Nominal vacuum thrust" | expected output | BLOCKED_MISSING_INPUTS | no engine size; the mixture-ratio input is blocked; delivered against ideal |
| specific impulse | AS-DB05-US-J-2S-002 | 436 s, "Nominal vacuum specific impulse" | expected output | BLOCKED_SEMANTICS | basis not stated; the mixture-ratio input is blocked; delivered against ideal |
| chamber pressure | AS-DB05-US-J-2S-003 | 1,200 psia, nozzle stagnation | input | INPUT_ELIGIBLE | |
| mixture ratio | AS-DB05-US-J-2S-004 | 5.5:1 O/F, engine | input | BLOCKED_SEMANTICS | an ENGINE ratio. A tap-off cycle diverts chamber gas rather than propellant, so the two ratios may coincide, but no source prints that; equating them would be an engineering inference |
| area ratio | AS-DB05-US-J-2S-008 | 40:1 | input | INPUT_ELIGIBLE | |

Note: the J-2 thrust also has a research-only conflict, CF-DB05-J2-THRUST (PARTIALLY_RESOLVED), which the
owner admitted for this configuration. No conflict is shipped in the production corpus, so the gate does not
emit it; it is listed here as context, not as gate output.

Even with every input and basis complete, a delivered Isp against an ideal one is at most a non-locking
efficiency. The tests construct that case (test 1): the review returns `EFFICIENCY_COMPARISON_ONLY`, never
`HARD_REGRESSION_ELIGIBLE`.

## 4. Blockers, grouped

| Blocker | Where |
|---|---|
| Delivered vs ideal | every thrust and Isp (J-2, J-2S): engine ratings against an ideal thrust-chamber model |
| Semantic mismatch | engine mixture ratio vs the thrust chamber's (J-2, J-2S) |
| Unknown basis | Isp engine or thrust-chamber basis not stated (J-2, J-2S) |
| Missing input | engine size for thrust (J-2, J-2S) |
| Model choices not printed | gamma strategy, gamma basis and inlet state (every output) |
| No accepted comparison class | delivered/ideal efficiency (owner decision) |
| No justified tolerance | no source states an uncertainty; printed precision (425 s → ±0.5 s) is a reading bound, not a physical uncertainty, and is not a tolerance basis on its own |
| Unknown environment | none among the candidates; the research-only SPS Block I and RL10A-3-3A have it |
| Conflict | J-2 thrust: research conflict CF-DB05-J2-THRUST, admitted for this configuration by owner decision |
| Rights | none: both sources' values ship with attribution |

## 5. Tolerance provenance

No hard regression exists, so no tolerance was set. The gate fixes where a tolerance may come from: a stated
uncertainty, a provider's numerical tolerance, or an established validation contract (the comparison layer's
significant-figure rule for thermochemistry printouts is one). Printed precision alone is not a basis. It
refuses a tolerance derived after a comparison (`tolerance_problems`).

`tolerance_problems` is a **declarative** rule: the check a future case must pass. Nothing calls it today,
because no case exists, so it enforces nothing yet. No RocketForge result was computed against either
candidate, so nothing could be fitted.

## 6. Provider

NASA CEA was **not run** by DB-4A: no case cleared its gate. A comparison-layer `ReferenceCase`
(`rocketforge/comparison/cases.py`) records the code, its version, the thermo database version, the origin
and free-form inputs; its quantity keys are thermochemistry only. It has **no field** for the performance
formulation, the gamma strategy and basis, or a frozen versus equilibrium expansion. A future engine case would
have to record those, in its inputs or in new fields; deciding which is part of the owner decision in §7. A
RocketForge CEA computation is not a NASA-published value.

### What the gate can return today

The result vocabulary includes `HARD_REGRESSION_ELIGIBLE` and `VALIDATION_COMPARISON_ELIGIBLE`, but the gate
as written cannot return either. A delivered value ends at `EFFICIENCY_COMPARISON_ONLY` at best (test 1). An
ideal value is blocked, because no evidence field can carry its expansion model and inlet state (test 1b).
`REFERENCE_ONLY` and `BLOCKED_MODEL_CAPABILITY` are also unused. So "0 hard, 0 validation" holds by
construction, which errs on the safe side. Adding a path to either result is an owner decision.

The gate also keeps every reason the evidence's `regression_blockers` gives, and adds stricter checks of its
own:

- the point value kinds are NOMINAL, RATED and TEST_RESULT only (no average, bound or approximation);
- only VACUUM or SEA_LEVEL counts as a known environment;
- the Pc station and basis, and the MR form and basis, must match the model's;
- every value must be one number (no range or text), and stated for the configuration or its operating
  point (never a variant, family, propulsion unit or component).

## 7. Owner decisions that would be needed for any future case

- Whether to add a non-locking delivered/ideal efficiency comparison class, and with which model choices
  (gamma strategy and basis, inlet state). An efficiency computed under a choice the source does not print
  would be a property of that choice.
- Whether an engine mixture ratio may stand for a thrust-chamber ratio for a tap-off cycle (J-2S). DB-4A does
  not decide this.

## 8. Why the rejected candidates remain valid reference records

The records are correct evidence of what Rocketdyne printed. Being unsuitable as a solver oracle says
nothing against them. No production record or capability was changed, and the corpus SHA-256
(`18108af7…dbada59`) is pinned by a test.

## 9. Deferred model capabilities

These would be needed before a real-engine delivered quantity could test RocketForge, and none was added:

- delivered-performance or efficiency models;
- engine-level cycles (generator or tap-off flow splits);
- engine sizing from a printed thrust.

LIQ-7 stays PAUSED.
