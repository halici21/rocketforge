# Design Skill Foundation R1 — License review

Every skill copied into this repository, with its exact license, the option
chosen where dual-licensed, and what that requires of this repository.

## Installed, copied verbatim

| Skill | Local path | Source | License | Notice requirement | Modification |
| --- | --- | --- | --- | --- | --- |
| `qt-qml` | `.claude/skills/qt-qml/` | `TheQtCompanyRnD/agent-skills` | `LicenseRef-Qt-Commercial OR BSD-3-Clause` — **BSD-3-Clause option used** | Retain the copyright notice, the license text, and the disclaimer; do not use "The Qt Company" name to endorse a derived product without permission. `LICENSE.txt` copied unmodified alongside the skill. | Copied verbatim, unmodified. |
| `qt-ui-design` | `.claude/skills/qt-ui-design/` | `TheQtCompanyRnD/agent-skills` | Same as above (BSD-3-Clause option) | Same as above. `LICENSE.txt` copied unmodified. | Copied verbatim, unmodified. |
| `qt-qml-review` | `.claude/skills/qt-qml-review/` | `TheQtCompanyRnD/agent-skills` | Same as above (BSD-3-Clause option) | Same as above. `LICENSE.txt` copied unmodified, including for the bundled `qt_qml_lint.py`. | Copied verbatim, unmodified. |
| `design-review` | `.claude/skills/design-review/` | `humbleteam/design-review` | MIT | Retain copyright notice and permission notice in copies/substantial portions. `LICENSE` copied unmodified. | Copied verbatim, unmodified. |

All four `LICENSE`/`LICENSE.txt` files were copied alongside their skill
directories and are present in this repository at the paths above — they
were not summarized or omitted. `README.md`/`CHANGELOG.md` files were kept
alongside `design-review` and the three Qt Company skills where present, so
attribution and version provenance travel with the skill rather than being
stripped for brevity.

## Why BSD-3-Clause was chosen for the Qt Company skills

The Qt Company dual-licenses this repository under
`LicenseRef-Qt-Commercial OR BSD-3-Clause`. RocketForge has no commercial
Qt license relationship of its own to invoke, and the BSD-3-Clause option is
a standard permissive license requiring only attribution and non-endorsement
— it imposes no obligation on RocketForge's own (separately licensed)
source code, and using it rather than asserting a commercial license
RocketForge does not hold is the only correct choice here.

## Reference-only material — attribution without redistribution

Nothing from a reference-only candidate was copied into this repository's
`.claude/skills/` tree. Where a reference-only skill's *ideas* (not text)
were folded into a custom RocketForge skill, the custom skill's `SKILL.md`
names the source skill by its actual name in prose (e.g. "`frontend-design`'s
calibration notes," "distilled in the `tufte` skill," "the `better-*`
family's ownership-boundary architecture") rather than presenting the idea
as original. No verbatim text from any reference-only skill was
reproduced in a custom skill file — every reference-only citation in this
project's custom skills is a paraphrase-and-attribute, checked against the
source content read during research.

- `frontend-design` (Apache-2.0) — cited by name in
  `rf-engineering-workbench`'s `RF_WORKBENCH_GRAMMAR.md`.
- `tufte-claude-skill` (MIT) — cited by name in
  `rf-scientific-visualization`'s `SKILL.md` and `RF_PLOT_TABLE_GRAMMAR.md`.
- `better-*` family (MIT) — its structural pattern (not its content) is
  credited in `DESIGN_SKILL_FOUNDATION_R1_OWNERSHIP.md`.
- `qt-qml-profiler` (BSD-3-Clause option) — its conceptual anti-patterns
  reference is cited in `rf-qml-architecture`'s `SKILL.md`; its script was
  not copied since it was never installed.

Since none of these were copied, no `LICENSE` file for them exists in this
repository, and none is required — citation of an idea in original prose is
not redistribution.

## Rejected candidates

No license obligation exists for any rejected candidate: nothing was
copied, adapted, or redistributed from `dawitlabs/ui-skills`,
`violet-hgy/agent-skills-qt-quick-qml`, `bigzhuodan/claude-skill-qt-design`,
`AJpon/qt-python-ai-skills`, `liueggy/qt5-skills`, `Cai-aa/CAD-Agent-Hub`,
`Cai-aa/CAE-Agent-Hub`, `NVIDIA/skills`, `LambdaTest/agent-skills`, or
`Bbasche/design-review`. Two of the Qt-specific rejects
(`violet-hgy`, `bigzhuodan`) carried no license at all at the time of
research (`"license": null` from the GitHub API) — a second, independent
reason they were correctly not installed even before the relevance and
adoption concerns already documented in the matrix.

## Outcome

Every installed or copied file's license is accounted for, every notice
requirement is satisfied by copying the license file unmodified alongside
the skill, and no reference-only citation reproduces source text verbatim.
