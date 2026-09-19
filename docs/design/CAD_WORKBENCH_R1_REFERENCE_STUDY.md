# CAD/CAE Workbench R1 — reference study

## Sunumatik audit (§11-16 of the brief)

Source: `github.com/ayberkdt/sunumatik`, `main` branch, fetched live via
`gh api` (not assumed from memory). Repository is **public, no declared
license** — no `LICENSE`/`LICENSE.md`/`COPYING` at the repo root and the
GitHub API reports `license: null`. Recorded as an open item: this program
uses the repository only as a read-only design reference (hex values and
discipline principles re-typed into RocketForge's own `Theme.qml`,
translated conceptually into QML), never by copying its files or code into
this repository, which is the lowest-risk use of an unlicensed public repo
but is not the same as zero risk. Flagged for the user's own judgment
rather than decided unilaterally.

### Transitive dependency map

`skills/design-space-science-deck/` (required skill):

```
design-space-science-deck
├── SKILL.md                              — read in full
├── references/
│   ├── theme-obsidian-champagne.md       — USE (required, read in full)
│   ├── color-composition.md              — USE (required, read in full)
│   ├── alignment-and-grid.md             — USE (required, read in full)
│   ├── typography-and-layout.md          — NOT NEEDED (deck-specific font/Turkish-glyph rules; RocketForge's own Typography.qml is authoritative)
│   ├── card-treatments.md, table-treatments.md, space-motifs.md,
│   │   decor-layering.md, theme-selection.md, user-palette-pairs.md,
│   │   14 other theme-*.md files                — NOT NEEDED (deck-component and other-theme specific)
├── presets/color_themes/
│   ├── palette-library.json              — USE (canonical Obsidian/Champagne token values — source of truth)
│   ├── palette-library.css               — REFERENCE ONLY (CSS custom-property mirror of the same JSON; RocketForge has no CSS layer, so the JSON is what was actually read)
│   └── components/*.css, space-motifs.svg — NOT NEEDED (HTML/CSS deck components)
├── scripts/validate-palette-library.mjs  — REFERENCE ONLY (read in full for security review; pure local JSON/contrast validation, no network, no filesystem writes beyond stdout — safe, but it validates Sunumatik's own JSON schema, which RocketForge does not maintain, so it is not run directly; RocketForge's own contrast audit is written against `Theme.qml` instead, same WCAG 4.5:1 math)
└── agents/openai.yaml                    — NOT NEEDED (unrelated agent-runtime config)
```

Sibling Sunumatik skills (repo root `skills/`, 18 total) — **not** imported,
per the brief's explicit exclusion list and confirmed by inspection rather
than assumed:

`orchestrate-science-presentation`, `design-scientific-motion`,
`create-scientific-visuals`, `write-assertive-slide-copy`,
`write-english-slide-copy`, `write-turkish-slide-copy`,
`enforce-slide-copy-density`, `build-html-science-deck`,
`convert-science-presentation`, `import-figma-science-deck`,
`audit-export-science-deck`, `distill-scientific-insights`,
`craft-scientific-storytelling`, `structure-scientific-narrative`,
`typeset-tex-equations`, `verify-scientific-evidence` — all
**PROHIBITED_BY_CURRENT_SCOPE**: presentation/deck/narrative/Figma/export
tooling, none of it applicable to a desktop Qt Quick engineering
application.

`skills/apply-design-tactics/` — **REFERENCE ONLY**, not invoked in this
pass. No rendered defect has yet demonstrated a need for it (weak
hierarchy, poor alignment, inconsistent radii, etc. — see brief §13). Will
be invoked, and the reason logged, only if the shell-prototype captures
actually show one of those specific symptoms.

### What was actually extracted and used

* `theme-obsidian-champagne.md`: the CSS custom-property block (`--bg
  #0F1013`, `--surface #1A1C21`, `--text #F4EEE1`, `--muted #A9A296`,
  `--accent #D3B26A`, `--signal #5590C9`) — matches the brief's own
  anchor-color list exactly, confirmed rather than assumed. **Also its own
  explicit warning, which the brief does not quote**: this is documented in
  Sunumatik as a "luxury keynote theme for milestone celebrations... low
  density by design... avoid... using this theme for dense technical
  review — it will fight the content." This is the source material *itself*
  stating the exact risk the brief spends its §18-32 warning against
  (`OBSIDIAN ENGINEERING WORKSTATION`, not `black-and-gold software`). It is
  not a reason to reject the palette — it is why the brief's insistence on
  restraint, semantic-token discipline and a strict application-state-only
  role for gold is load-bearing, not decorative caution.
* `palette-library.json`, `obsidian-champagne` entry (`id`,
  `character: [luxury, keynote, warm-metallic, celebratory]`,
  `origin: premium-app-study-2026`): the complete semantic token set —
  `canvas #0F1013`, `surface #1A1C21`, `ink #F4EEE1`, `muted #A9A296`,
  `accent #D3B26A`, `accentInk #191307`, `data1..6` (`#5590C9` steel blue,
  `#C86A40` copper, `#6FBF9A` mint, `#A88BD9` violet, `#D9C36A` pale gold,
  `#C95F6A` rose), `rule #2E3037`, a 5-step sequential ramp, a 5-step
  diverging ramp, and a CVD note (gold/blue is deuteranopia-safe;
  data3/data5 sit close in lightness and need a non-hue cue). This is the
  exact set that will be mapped onto RocketForge's existing semantic token
  names in `Theme.qml` during the shell-prototype phase — not re-typed from
  memory.
* `color-composition.md`: the transferable discipline actually carried
  forward — 70/20/10 canvas/surface/accent distribution, the "dirty deck"
  neutral-temperature diagnostic (neutrals stay on one temperature family;
  every literal comes from tokens, never hand-picked), WCAG 4.5:1 floor /
  7:1 preference, "never encode a category by hue alone." The deck-specific
  material (glow/gradient rules for *slide* backgrounds, projector
  conditions) was read but is not applicable and was not carried forward.
* `alignment-and-grid.md`: the transferable *principle* — one dominant
  shared edge per view, a fixed spacing scale where two gaps are either
  identical or differ by a full step, peer panels get equal heights. The
  literal grid (12-column, 1920×1080 stage, 64px margins) is a slide-deck
  geometry and does **not** transfer — RocketForge already has its own
  fixed spacing scale (`Metrics.spacing`: 2/4/8/12/16/20/24/32/40) and
  panel-width system (`Metrics`: nav/rail/inspector/project-panel widths),
  which remains authoritative.

### Security/license review summary

| Check | Result |
| --- | --- |
| Scripts | One: `validate-palette-library.mjs`. Read in full. Pure local file read + JSON/contrast math, no network calls, no `child_process`, no writes outside stdout. Safe. |
| Network behavior | None found in anything read (skill markdown is prose; the one script makes no requests). |
| Hidden dependencies | `agents/openai.yaml` exists but is unrelated to this use and was not read in detail — not invoked, not a dependency of anything used here. |
| License | **None declared.** Flagged above; used read-only/reference-only per the brief's own instruction, never vendored. |
| Ownership conflicts | None — Sunumatik is not asked to and does not govern RocketForge product, scientific, or QML architecture decisions anywhere in what was extracted. |

## CAD/CAE reference products (§16 of the brief)

Not a new research program — the shell-prototype comparison (next phase)
is grounded in the pattern every mainstream parametric/schematic CAD tool
already converges on, and in what Engine Design mode already builds
(previous section): a persistent object tree on one side, a dominant
viewport in the center, a context-sensitive property panel on the other
side, and a collapsible bottom log/output panel — SolidWorks' FeatureManager
tree + graphics area + PropertyManager, Fusion 360's browser tree +
viewport + inspector, KiCad's schematic/symbol tree + canvas + properties.
The common thread relevant here: **the tree and the inspector both take
their meaning from the same selection**, and the viewport is never
squeezed to make room for permanently-visible auxiliary panels — logs,
BOM tables, and cut-lists collapse. Engine Design mode already follows this
shape; Analysis mode does not. That gap is the actual design question for
shell prototypes A/B/C, not a blank-page reinvention of the pattern.
