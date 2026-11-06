# DB-4B — Engine-level Isp ratio: a non-locking comparison

Status: IMPLEMENTED, report only. The owner accepted all five decisions in §1 on 2026-11-07.

The rules were written and accepted before any ideal value was computed for any engine, so nothing in them could be
fitted to a result. The first run is in §10.

This answers the two questions in DB-4A §7. It does not create a regression reference. The hard and validation totals stay
0, and no result here can fail, pass or lock anything.

## 1. Decisions (accepted 2026-11-07)

| # | Decision | Accepted |
|---|---|---|
| 1 | Add a non-locking comparison of a printed engine Isp with RocketForge's ideal Isp | Yes, under the name "engine-level Isp ratio", not "efficiency" (§2) |
| 2 | Allow an engine mixture ratio as the model's input in this comparison, declared on the result | Yes. It still never stands for a thrust-chamber ratio, for any cycle, J-2S included (§4) |
| 3 | Allow a printed Isp whose engine or thrust-chamber basis is not stated, declared on the result | Yes. Every shipped Isp has this basis as `UNKNOWN`, so refusing means no comparison at all |
| 4 | Fix the inlet state at the normal boiling points and show both gamma bases, with no single headline number | Yes (§5) |
| 5 | Report only for now, with no workspace display | Yes. Decide on a display after reading the two results (§9) |

Refusing 2 or 3 leaves no eligible engine, which is an acceptable outcome. Then there is nothing to build, and DB-4A stands.

## 2. What the number is, and what it is not

```text
ratio = printed engine Isp / RocketForge ideal Isp
        (Pc, area ratio, engine O/F from the same record; each gamma basis)
```

It is not a thrust-chamber efficiency, and it is deliberately not called one:

- The numerator is an engine rating. Its basis is not printed. For a gas-generator engine it may include turbine exhaust.
- The denominator is evaluated at the engine's mixture ratio, not the injector's, because no source prints the injector's.
- The model has no losses and uses one constant gamma. A ratio above 1 is possible and is not a defect in either side.

So the ratio supports one statement: "this printed rating, against this model, under these declared choices, gives this
value". It says nothing about whether the model is right or how good the engine's combustion was.

## 3. Eligibility

A configuration is eligible only if all of these hold, with exactly one record for each quantity. The evidence's
`regression_blockers` stay in force and are not relaxed.

| Input | Must be |
|---|---|
| Isp | One number, `NOMINAL`, `RATED` or `TEST_RESULT`, environment `VACUUM` or `SEA_LEVEL`, stated for the configuration |
| Chamber pressure | Station `NOZZLE_STAGNATION`, basis `ABSOLUTE`, same value kinds |
| Mixture ratio | Printed direction `OXIDIZER_TO_FUEL`, basis `THRUST_CHAMBER` or `ENGINE`. `UNKNOWN` is refused |
| Area ratio | One number, same value kinds |
| Propellants | Recorded for the configuration, each mapped by an exact table to a model definition |
| All running values | One operating point |

Thrust is out of scope. The model needs an engine size to compute it, no source records one, and deriving one from the
printed thrust and Isp would be circular.

## 4. The mixture-ratio question

DB-4A asks whether an engine ratio may stand for a thrust-chamber ratio for the tap-off J-2S. The recommendation is no, and
this comparison does not need it to.

For a tap-off engine the two may coincide, but no source prints that. Accepting it would write an inference into the
evidence-facing rules, one cycle at a time. Here the result declares `mixture_ratio_basis: ENGINE`, and the name
"engine-level" carries the same meaning. J-2 and J-2S follow one rule.

`test_engine_mixture_ratio_is_not_taken_as_the_thrust_chambers` keeps passing, and the DB-4A review keeps blocking that input.

## 5. Model choices, fixed now

| Choice | Fixed as | Why |
|---|---|---|
| Gamma basis | Both `FROZEN` and `EQUILIBRIUM`, always shown together | Neither is printed. Picking one would make the ratio a property of the pick |
| Gamma strategy | `CHAMBER` | `THROAT` gives the same exponent in this model (`handshake.py:204`), and `EXIT`, `CHAMBER_EXIT_MEAN` and `EFFECTIVE_ISENTROPIC` are refused |
| Inlet state | LOX 90.17 K, LH2 20.27 K, the definitions' reference temperatures | No source prints it. Recorded as an assumption on the result |
| Ambient | Vacuum or 101,325 Pa, from the recorded environment | A regime the nozzle model refuses stays a refusal |

There is no average of the two bases and no preferred value. DB-4A §2 lists gamma strategy as a third open choice; in this
model it does not change the exponent, so it does not add a case.

## 6. Why it stays non-locking

- **No verdict.** The result has no pass, fail or tolerance field. `VERDICT_KINDS` is unchanged and `tolerance_problems` stays uncalled.
- **No pinned value.** No test asserts a ratio for a real engine. Tests pin arithmetic on stated numbers, and the rules.
- **Nothing written to evidence.** `reference_engines.json` and its pinned SHA-256 do not change.
- **Nothing tuned.** No model, gamma choice or eligibility rule may change in response to a ratio. A change needs its own reason, stated without reference to the result.
- **The DB-4A totals stand.** `HARD_REGRESSION_ELIGIBLE` and `VALIDATION_COMPARISON_ELIGIBLE` stay unreachable.

## 7. Who qualifies

Under decisions 2 and 3, exactly two configurations, both from Rocketdyne viewgraphs:

| Configuration | Printed Isp | Pc | O/F | Area ratio | Cycle |
|---|---|---|---|---|---|
| `CFG-J2-230K` | 425 s, vacuum | 717 psia | 5.5, engine | 27.5 | Gas generator |
| `CFG-J2S` | 436 s, vacuum | 1,200 psia | 5.5, engine | 40 | Tap-off |

The closest others, and what stops them:

| Configuration | Blocked by |
|---|---|
| `CFG-RL10A-3-3A` | Isp environment, Pc station and O/F basis not stated |
| `CFG-RL10A-3-3-FR1769` | Isp environment and O/F basis not stated; Pc values are design values at other stations; no propellants recorded |
| `CFG-F1` | No O/F; Pc station not stated |
| `CFG-F1A-MSFC-2013` | No O/F; Pc station not stated; no propellants recorded |
| `CFG-RS68-1999-BASELINE` | No O/F; average Isp; Pc station not stated; no propellants recorded |
| `CFG-SPS-BLOCK-I` | Average Isp; environment, Pc station and O/F basis not stated; no propellants recorded |

The rest lack an Isp, a Pc or an O/F. Ways to add engines are sources that print these conditions, not looser rules.

## 8. Where the code would go

| Part | Place | Rule it keeps |
|---|---|---|
| Result record and ratio arithmetic | New `rocketforge/comparison/engine_isp_ratio.py` | The comparison layer is handed values and reaches no solver |
| Eligibility, solver-free | New `rocketforge/application/analysis/reference_engine_isp_ratio.py` | Reads the catalog and writes nothing, as `reference_engine_regression.py` does |
| Run | Same application module, through `solve_case` and `solve_performance` | CEA only through the existing lazy gateway. Without CEA it reports that, with no substitute |
| Report | A `tools/` script that prints the two results | Run by hand, not by the test suite |

Isp is compared in seconds on both sides, and the model already reports it in seconds. The comparison layer's unit table
does not know `s`, so the ratio needs no conversion through it and accepts only the printed units `s` and `sec`. Pc converts
through that table, which knows `psia`.

The DB-4A review changes in one place: `_NO_EFFICIENCY_CLASS` would point to this class. Its results do not change.

Tests: the eligibility rules, including one refusal per row of §3; the arithmetic; the absence of verdict and tolerance
fields; no change to the corpus hash; both bases always present; and, in `.venv-cea`, that a run returns both bases for both
engines without asserting their values.

## 9. Limits

- **It adds no regression reference.** A hard reference needs a source that prints an ideal value with its expansion model and inlet state. No shipped source does. That is a separate search.
- **Two numbers from two viewgraphs.** This is a plausibility reading, not a survey of engines.
- **Deferred:** CEA's own Isp beside the ratio (`performance_oracle.py` could supply it at arm's length), a mixture-ratio sensitivity (any band would be invented today), and a workspace display.

A display would need its own review under the scientific UI contract. A bare percentage would read as an efficiency.

## 10. First run (2026-11-07)

These are readings. No test pins them, and no rule or model may change in response to them. To reproduce them:

```bash
.venv-cea/Scripts/python.exe tools/reference_engines/report_isp_ratio.py
```

| Configuration | Printed Isp | Ideal, frozen | Ratio | Ideal, equilibrium | Ratio |
|---|---|---|---|---|---|
| `CFG-J2-230K` | 425 s | 433.49 s | 0.9804 | 454.22 s | 0.9357 |
| `CFG-J2S` | 436 s | 443.93 s | 0.9821 | 464.31 s | 0.9390 |

How far these go:

- The choice of gamma basis moves each ratio by about 0.04. The two engines differ by at most about 0.003 under either
  basis. So these numbers cannot rank the two engines, and they say nothing about combustion quality.
- Both ratios are below 1 under both bases, so this run raises no question about the model. It does not validate it either:
  the printed values are ratings, and the model and the engines differ in ways the ratio cannot separate.
