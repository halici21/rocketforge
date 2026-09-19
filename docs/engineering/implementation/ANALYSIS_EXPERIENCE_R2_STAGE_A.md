# Analysis Experience R2 — Stage A

Status: **AWAITING USER VISUAL APPROVAL**. Not accepted, not frozen, and
Stage B not begun.

## What this stage set out to fix

The user rejected the rendered Analysis product: it still read as sidebar
→ page → calculator. Engineering stability was never the question, and
prior PASS documents, regression counts and blind reviews were not treated
as evidence against that verdict. Prior *visual* acceptance for Analysis
mode is revoked; prior *scientific* acceptance stands and was preserved.

## What changed, in order of visible impact

1. **Navigation.** A permanently visible 240 px list of 17 destinations
   became a 64 px family rail of 7, plus a contextual drawer that opens
   only for the two families with more than one module and floats over
   the workspace rather than reserving width. Full rationale:
   `docs/design/ANALYSIS_EXPERIENCE_R2_NAVIGATION.md`.
2. **Placeholder routes removed from production navigation.** Compare,
   Charts and Gas Properties are `ModulePlaceholderPage` skeletons and are
   no longer reachable as product features. Their code and routes are
   untouched.
3. **Home.** The five-row "No result yet" inventory became a Continue
   section (only what genuinely has something to continue) over a Start
   section (the families, no status text).
4. **Chart annotation collision — the brief's own blocking condition.**
   `RFLineChart` now places guide and marker labels in claimed vertical
   bands. The two labels that previously overprinted in the θ–β–M view
   are legible as two separate facts.
5. **Three archetype pilots**, compositionally different by design:
   Oblique Shock (hero answer), Thermochemistry (object central in both
   solved and unsolved states), Trade Study (the trade owns the
   workspace). See `docs/design/ANALYSIS_EXPERIENCE_R2_ARCHETYPES.md`.
6. **Brand icon**, designed, small-size reviewed, simplified after that
   review failed, and integrated into the window, the executable and the
   bundle. See `docs/design/ROCKETFORGE_BRAND_ICON_R1.md`.

## Three defects found by looking, not by testing

Recorded because they are the argument for the discipline, not incidental:

- The contextual drawer auto-opened on navigation and sat on top of the
  workspace's own input rail. Fixed: it opens only from a rail click.
- At 1366×768 the θ–β–M chart collapsed to ~120 px and its caption printed
  across the plot while the *secondary* chart kept a fixed 250 px. Fixed by
  reflow: primary floored at 280 px, caption dropped when compact,
  secondary yields entirely.
- The first icon read as a letterform and dissolved below 32 px. Fixed by
  simplifying geometry, not by downscaling harder.

All three passed every automated gate at the moment they were broken.

## Gates

| Gate | Result |
| --- | --- |
| Full regression | 7110 passed, 2 skipped — identical to baseline |
| Physics / engineering / provider files touched | 0 |
| Solve calls during visual interaction | 0, across 25+ interactions and all six monitored domains |
| Qt warnings across every capture | 0 |
| Memory | 300 mixed pilot rounds, 60.11 MB, slope 0.0475 → 0.0065 MB/round, controls A/B/E pass — PASS |
| Window icon | Loads with all 7 sizes |

Artifacts: `acceptance/analysis_experience_r2/` — `before/`, `after/`,
`navigation/`, `charts/`, `skill_design_trace.json`,
`scientific_parity.json`, `solve_call_parity.json`, `memory.json`,
`visual_audit.json`.

## Known gaps in this stage

- `RFPlotSurface` and `RFLineChart` remain two components. Unifying them
  would be the broad refactor this brief forbids; proportion, collision
  and responsive rules were applied to each in place.
- Trade Study's study-definition drawer (brief section 43) was addressed
  by the existing tab separation rather than a new collapsible rail.
- Only the three pilots were migrated. Every other Analysis module still
  carries its pre-R2 composition — that is Stage B, and it is deliberately
  not started.
- `design-space-science-deck` and `apply-design-tactics` are not installed
  in this environment; the former's principles were applied from the
  existing extraction, the latter is recorded as unavailable rather than
  claimed.
