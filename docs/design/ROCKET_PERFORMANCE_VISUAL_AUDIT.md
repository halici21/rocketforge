# Rocket Performance — visual audit

Written **before any code was changed**, from the capture matrix in
`acceptance/ui_visual_pilot/before/` — 27 captures across 2560×1440,
1920×1080 and 1366×768 in both themes, at ten canonical scientific states.

The workspace is scientifically excellent and visually a calculator. This
document says exactly where, with evidence, so the redesign has something to
answer to rather than a feeling.

---

## A. Hierarchy

**The most important number on the page is the last one you reach.**

At 1920×1080 the Performance tab shows a single 15-row readout list. Reading
order top to bottom: c\*, then exit Mach, exit pressure, exit pressure ratio,
exit temperature, exit velocity, Cf momentum, Cf pressure, Cf, then c_eff and
**Isp at row 13**, then throat area, exit area, mass flow.

Specific impulse — the quantity the workspace exists to produce — sits below
ten secondary values.

**Every value has identical typographic weight.** All fifteen numbers are the
same size, same font, same weight. The only thing separating a headline
quantity from a diagnostic one is **colour**: c\*, Cf, c_eff and Isp are amber,
the rest are white. That is a colour-only hierarchy, which is both weak
perceptually and an accessibility problem.

Can the primary result be found in under two seconds? No. You have to read
labels.

## B. Composition

The page is **form-left, results-right**. That is the canonical desktop
calculator layout, and it is what makes the workspace read as one.

There is **no visual centre**. The 1920 layout is a 320 px control column and a
1290 px list. Nothing occupies the middle; the middle *is* the list.

Empty space is not composed — it is leftover. Below the Calculate button at
1920 the left column has roughly 150 px of unused height because the form ran
out of fields, and the right column simply runs to the bottom edge.

## C. Card saturation

| Surface | Count |
| --- | --- |
| `RFPanel` in the Performance tab | **2** |
| `RFPanel` in the Model tab | **4** |
| `RFPanel` in the Provider comparison tab | **3** |
| **Total across the workspace** | **9** |

Plus a segmented pill for the three tabs and two status chips in the header.

Inside the left panel, five sections (CHAMBER STATE, GAS MODEL, NOZZLE,
AMBIENT, ENGINE SIZE) are separated by full-width dividers — the panel is
already doing container work internally, so its own border and radius are a
second, redundant container.

The right panel wraps a list that has its own section headings. Its border
adds nothing.

## D. Typography

Hierarchy is carried by **borders, section labels and colour** rather than by
type. There is effectively one numeric size on the page.

What is already good and must be kept: the numbers are monospace and decimal
positions line up down the column; units are present, smaller and muted;
qualifiers ("chamber and throat only", "signed", "V_e / c\*") are quieter still.
That restraint is real and the redesign should build on it rather than discard
it.

What is missing: any sense that 348.658 s matters more than 0.00212414.

## E. Engineering object

**There is none.** The workspace computes a nozzle and never shows one.

The word "nozzle" appears as a section label and as "Area ratio Ae/At". A
user reading `40.000` gets no physical sense of what a forty-to-one expansion
is. Chamber → throat → exit — the entire spatial story of the calculation — is
absent.

This is the single largest gap. The page is a list of numbers about an object
that is never depicted.

## F. Chrome

Visible UI that carries no engineering meaning: two panel borders, the
segmented tab pill, two header chips, five internal dividers, and a page
subtitle that restates the section labels below it.

## G. Motion

Values are replaced. Nothing indicates *which* values changed after a
recalculation, and nothing moves to show that a changed expansion ratio has
changed the physical situation. The interface responds to state textually, not
spatially.

## H. What specifically makes it read as a student calculator

Concrete tells, not impressions:

1. **Form on the left, answers on the right.** The archetypal calculator shape.
2. **A fifteen-row uniform readout table.** It reads as a spreadsheet dump: no
   quantity is designed, they are enumerated.
3. **A "Calculate" button as the visual anchor of the left column** — the most
   saturated element on the page is a form-submit control.
4. **Colour as the only importance signal.**
5. **Three tabs in a pill.** Generic app chrome sitting directly under a large
   page title that repeats what the tabs say.
6. **Nothing physical.** A propulsion tool with no propulsion object in it.

---

## The 1366×768 finding — this one is a defect, not taste

At 1366×768 the workspace does not merely feel cramped. It fails:

* The left rail is **clipped mid-section**. The word "NOZZLE" is cut in half by
  the Calculate button's row. **Area ratio, Ambient and Engine size are not
  reachable at all** — the panel does not scroll to them, it is simply cut.
* The right list ends at "Thrust coefficient Cf". **c_eff, Isp, throat area,
  exit area and mass flow are all below the fold.**

So at the smallest supported desktop size a user can neither set the expansion
ratio nor see the specific impulse. Both are core to the workspace.

This is recorded as **`RESPONSIVE_LAYOUT_BLOCKER`** against the *current*
design and is a requirement on the new one.

---

## What is already right, and must not be lost

The audit is not a case for a rewrite of everything. These are genuinely good
and the redesign must preserve them:

* **Refusal semantics.** No chamber → no numbers. No engine size → thrust
  withheld entirely, never shown as 0.
* **Qualifier text.** "not the effective exhaust velocity" beside V_e, "signed"
  beside the pressure term, "chamber and throat only" beside c\*. These are
  small, quiet, and prevent real misreadings.
* **Monospace numerics with aligned decimals.**
* **The model/provenance separation** into its own tab, so the oracle can never
  be mistaken for a RocketForge result.
* **Zero chemistry re-solve.** Measured again in this baseline: editing ε,
  ambient or scale, and every view/theme/resize interaction, cost **0**
  provider calls.

---

## Audit verdict

| Dimension | State |
| --- | --- |
| Hierarchy | colour-only; the headline quantity is thirteenth |
| Composition | form + list; no centre |
| Cards | 9 panels; several redundant |
| Typography | one numeric level |
| Engineering object | **absent** |
| Chrome | moderate, removable |
| Motion | none |
| 1366×768 | **broken** — primary control and primary result both unreachable |

The redesign has a clear brief: give the page a physical centre, give the
numbers a hierarchy, remove the containers that typography can replace, and
make the compact size a designed composition rather than a truncation.
