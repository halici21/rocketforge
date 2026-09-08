# Rocket Performance — UI contract

Phase 5E. What the workspace promises, and what enforces each promise.

---

## Shape

Third analysis domain, its own sidebar section, one page with three views of
one calculation.

| View | Question |
| --- | --- |
| **Performance** | For this chamber, this nozzle, this ambient — what does the ideal model give? |
| **Model** | What produced those numbers, and what are they not? |
| **Provider comparison** | What does the provider get for the same case? |

The views share the controller's single current result, so switching never
recomputes and two views cannot disagree.

### Files

| File | Role |
| --- | --- |
| `ui/pages/RocketPerformancePage.qml` | header, view selector, stack |
| `ui/pages/rocketperformance/PerfCalculator.qml` | inputs and results |
| ~~`ui/pages/rocketperformance/PerfResultHeader.qml`~~ | *superseded — see below* |
| ~~`ui/pages/rocketperformance/PerfResultGroup.qml`~~ | *superseded — see below* |
| `ui/pages/rocketperformance/PerfModel.qml` | assumptions, reduction, identities, provenance |
| `ui/pages/rocketperformance/PerfOracle.qml` | the provider's own answer, in its own panel |

Built entirely from the existing component kit. **No shared component was
changed for this phase** — a test asserts none of them mentions this workspace.

#### Superseded by the visual pilot

The Rocket Performance visual pilot replaced the uniform result list with a
metric hierarchy, a schematic propulsion canvas and two term breakdowns.
`PerfResultHeader` and `PerfResultGroup` had no remaining caller and were
removed; a test now fails if any pilot component is left instantiated nowhere.
The components that replaced them are listed in
`docs/design/ROCKET_PERFORMANCE_VISUAL_PILOT.md`.

**Nothing above this heading changed.** The promises in the rest of this
document — no equations in QML, refusal semantics, one result shared by three
views, zero re-solve on a view change — are unchanged and still enforced by the
same tests, plus the pilot's own rules in
`tests/test_performance_visual_architecture.py`.

---

## The rules, and what enforces them

### No equations, no constants, no unit conversion in QML

Every number arrives already formatted. `Math` is restricted to
`max/min/floor/ceil/round/abs`; a scan bans `8314`, `9.80665`, `101325` and the
rest; a third scan bans scale factors. Each has a negative control proving it
is not vacuous.

### No provider import, and no provider name, in QML

The provider's name is **data**, read from the result that carries it.
Hard-coding "NASA CEA" would survive a provider change and start lying the day
one happens. A test bans the string in every literal.

### No chamber state, no numbers

The workspace refuses and says where to get one. Nothing is estimated in its
place, and `Calculate` is disabled.

### No engine size, no thrust

The engine group is **absent**, not zeroed, and a note says why.

### A result is never relabelled

The header is built from the case and the chamber outcome the result carries,
not from the live form. Editing an input marks the result stale; the numbers
and the header do not move.

### An upstream chamber change invalidates, it does not recompute

Compared by **identity** — two chamber outcomes with equal numbers are still
two different answers. On change:

| | |
| --- | --- |
| `chamberSuperseded` | true, and a banner explains it |
| the numbers | unchanged |
| the header | unchanged |
| the result | kept, not discarded |

Silently recomputing would move numbers the user is reading. Silently keeping
them unmarked would attach them to a chamber that no longer exists.

### Grouping is part of the meaning

| Group | What it has in common |
| --- | --- |
| Chamber / choked flow | c\*. Independent of area ratio and ambient pressure. |
| Nozzle expansion | exit state, Cf. Ambient enters the pressure term only. |
| Total propulsive performance | c_eff, Isp. The two above multiplied. |
| Scaled engine | needs an engine size. |

A flat list of eight numbers invites a reader to take c\* for an exhaust
velocity, which is the most common misreading of these quantities. Each group
carries a note; each row carries a tooltip saying what the quantity is **not**.

### The ideal framing is on the page header

Not buried in a details panel. The header chip reads *Ideal — no efficiency
factors*, and the Model tab opens with "read this list as what is absent".

The assumptions are shown in **two attributed groups** — what the ideal model
claims, and what this particular reduction committed to. Concatenated they
overlap, and a list that appears to repeat itself undermines the panel it is
trying to make authoritative.

### Caveats cross the layer boundary

A chamber-state warning — an assigned-enthalpy reactant, say — is shown on the
performance result with its origin marked. It does not stop the algebra, and it
does not stop applying: the chamber it describes is the one every number was
computed from.

### The oracle is separated by construction

| | |
| --- | --- |
| its own view and panel | a boundary the eye can see |
| runs only on **Run provider** | no nozzle input reaches it |
| the calculator view never reads an oracle property | asserted by test |
| every residual labelled *model difference* | never "error" |
| each row states its reference condition | vacuum against vacuum, optimum against optimum |

---

## Wording audits

Banned as claims: *actual / real / predicted engine performance*, *guaranteed*,
*exact result*, *optimal design*, *recommended design*, *combustion
efficiency*, *expected thrust*, *delivered Isp*.

The audit skips a phrase preceded by a negation, because this workspace's
honest wording contains the banned phrases inside disclaimers — "an example,
**not a recommended design**". Flagging those would push the disclaimers out of
the interface. The negative control fires on the claim and stays silent on the
disclaimer.

QML wraps long sentences by concatenating literals, so the audits rejoin and
collapse whitespace before matching. A helper test proves the rejoining works.

---

## The packaged diagnostic

```
RocketForge.exe --selftest-rocket-performance <directory>
```

Loads the real QML, drives the real controllers through the same slots the
controls call, writes one JSON report and 29 PNG captures, exits. **No
synthetic desktop input** — a test bans `QTest`, `sendEvent`, `pyautogui` and
the rest — so it cannot type into whatever window is in front, and it runs
under the offscreen platform plugin.

It also counts provider calls across the tour. A frozen build that quietly
re-solved chemistry on every input change would still look correct in a
screenshot; the count is the only thing that catches it.

### Results

| | Source | Packaged |
| --- | --- | --- |
| Captures | 29 | 29 |
| Qt messages | **0** | **0** |
| Chamber solves from input changes | **0** | **0** |
| Resolutions | 2560×1440, 1920×1080, 1366×768, plus light theme | same |

**Parity: 5013 fields compared, 0 differing, 0 present in only one build.**

---

## Defects found and fixed during this phase

**Nested layouts default `Layout.fillHeight` to true.** The result header
competed with the results Flickable for the panel's height and won, leaving the
performance numbers with none. Caught by reading the 1366×768 capture, not by a
test — which is what the visual gate is for.

**`anchors.verticalCenter` inside a `RowLayout`** produced 1464 Qt warnings
in an intermediate run. Replaced with `Layout.alignment`; every accepted run
afterwards, source and packaged, reported **0** Qt warnings.

**A Phase 5D architecture rule was scoped as an exclusion** — "every page that
is not thermochemistry must not mention Thermochemistry" — which silently
began asserting that this workspace may not name the tab a user must visit to
get a chamber state. Rescoped to name the analysis domains explicitly, with a
test that the exclusion covers only those, so it cannot be widened later to
make a failure go away.
