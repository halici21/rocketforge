# Compressible Flow — Performance Baseline

Measured, on one machine, so that a future 100x regression is visible. These
are not hardware-independent guarantees and must not be read as real-time
promises.

## Environment

```
    Python 3.13.2 on Windows 11 (10.0.26200)
    numpy 2.5.2
    AMD64 Family 25 Model 116 (Ryzen mobile class)
    best of three runs, single-threaded, no warm-up excluded
```

## Forward relations — 100 000 samples, vectorised

| Operation | Time |
| --- | --- |
| isentropic, all four ratios | 4.61 ms |
| mass-flow parameter | 2.08 ms |
| normal shock, all ratios | 5.96 ms |
| Prandtl-Meyer nu | 1.49 ms |
| Fanno, all ratios | 3.81 ms |
| Rayleigh, all ratios | 5.26 ms |

Roughly 20-60 ns per sample per relation. Forward relations are pure NumPy and
scale linearly.

## Bracketed inverses — one solve

| Operation | Time |
| --- | --- |
| area-Mach, subsonic | 0.104 ms |
| area-Mach, supersonic | 0.126 ms |
| mass-flow ratio | 0.124 ms |
| Prandtl-Meyer inverse | 0.074 ms |
| oblique beta, weak | 0.448 ms |
| oblique beta, strong | 0.419 ms |
| Fanno inverse | 0.326 ms |
| Rayleigh inverse | 0.096 ms |
| nozzle internal shock | 3.009 ms |

The nozzle shock is the most expensive single call in the subsystem, and
legitimately so: each residual evaluation runs two nested area-Mach inversions,
so one shock location is roughly a dozen inversions.

## Batched inverses

| Operation | Time |
| --- | --- |
| area-Mach, 2 000 supersonic | 238 ms |
| Prandtl-Meyer, 2 000 angles | 157 ms |
| theta-beta-M curve, 400 points | 0.099 ms |

The batched inverses loop over the scalar solver **deliberately**: a vectorised
iteration would converge element by element at different rates and make a
point's answer depend on the batch it was computed in, which the determinism
rule forbids. The theta-beta-M curve is fast because it evaluates the forward
relation on a beta grid rather than inverting anything.

## Nozzle

| Operation | Time |
| --- | --- |
| thresholds, warm cache | 0.004 ms |
| thresholds, cold cache | 0.264 ms |
| one classification | 0.013 ms |
| 100 000 classifications, shock-free | 867 ms |
| distribution, 100 stations, internal shock | 16.3 ms |
| distribution, 500 stations | 62.4 ms |
| distribution, 1 000 stations | 122.6 ms |

Classification is cheap because the three criticals are memoised on
`(area ratio, gas, tolerances)` — a pure function, so the cache changes no
answer, and a test proves a different area ratio or gamma cannot receive
another nozzle's thresholds. Before that memoisation, Phase 4F measured 0.216 ms
per classification and 38.5 s for 100 000; the cache is a 45x improvement on
that path and nothing else.

A back-pressure sweep that crosses the internal-shock interval pays one
bracketed solve per point inside it — about 3 ms each — which is why the
interface's shock curve uses 80 points rather than several hundred.

Distributed solutions cost one area-Mach inversion per station. The interface's
default of 161 stations is about 25 ms, which is comfortable for interaction.

## Regression policy

No absolute timing assertion is written as a unit test: those are brittle across
machines and CI noise, and a 2% variation is not a physics failure. The numbers
above are the baseline. What matters is the *shape*:

* forward relations should stay in the single-digit milliseconds per 100 000;
* a single inverse should stay well under a millisecond, except the nozzle
  shock, which is a few;
* classification should stay in the tens of microseconds;
* a default-resolution distribution should stay in the tens of milliseconds.

An order-of-magnitude departure from any of those is worth investigating. A few
percent is not.

## What was deliberately not done

No threading, no multiprocessing, no worker pools. Phase 3's guidance is that
these are inexpensive algebraic relations, and the measurements agree: nothing
in the default interface path blocks long enough to justify the complexity, or
the nondeterminism that a shared worker would risk.
