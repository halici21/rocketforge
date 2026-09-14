# Contributing to RocketForge

This is a solo-maintained project. Issues and small, focused pull requests
are welcome; there is no formal review board or roadmap process, but a few
project conventions are load-bearing and worth knowing before you send a
change.

## Before you start

* **Read [README.md](README.md) first**, especially
  [Verification and freeze status](README.md#verification-and-freeze-status)
  and [Known limitations](README.md#known-limitations) — they say precisely
  what is real physics, what is frozen, and what is still a UI mockup.
* **Frozen means frozen.** `rocketforge/physics/compressible/` and the
  thermochemistry/fluids/line/performance contracts documented under
  `docs/engineering/` were verified in gated campaigns
  (`docs/engineering/verification/`, `docs/engineering/implementation/`).
  Changing their outputs, tolerances, or public API is a scientific decision,
  not a refactor — open an issue and explain the defect *before* sending a
  PR that touches them.
* **No new thermochemistry/physics features via drive-by PR.** Adding a
  relation, provider, or solver is a project-level decision (see the ADRs
  referenced throughout `docs/engineering/`), not something to bundle into
  an unrelated fix.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python main.py
```

See [Testing](README.md#testing) for the full test commands, including the
optional CEA-backed environment. Every push and PR runs the same two suites
in CI (badge at the top of the README) — a PR that fails CI will not be
merged.

## Making a change

1. Open an issue first for anything beyond a trivial fix (typo, obvious bug,
   docs) — for behavioral changes, a short discussion up front saves a
   rewritten PR later.
2. Keep the change scoped. A bug fix doesn't need an accompanying refactor.
3. Add or update a test. `tests/test_architecture.py` enforces several
   structural rules (no SciPy import outside the cross-validation oracle, no
   pandas dependency, etc.) — read it if your change touches imports.
4. Run the full base suite locally before opening the PR:
   `.venv\Scripts\python.exe -m pytest -q`.
5. If your change touches QML, mention which page(s) you tested manually —
   automated Qt tests cover controller/model logic, not visual regressions.

## What not to send

* Changes to `rocketforge/physics/compressible/` without an accompanying
  defect report and regression test (see
  [Known limitations](README.md#known-limitations) — this module is frozen).
* Tolerance widening to make a failing test pass. If a test is wrong, say so
  explicitly and explain why; don't loosen the assertion to get green CI.
* Engine Design mode features that render a *solved-looking* result for a
  component the codebase cannot actually solve — see the component inventory
  referenced in [Known limitations](README.md#known-limitations). Presenting
  fabricated results as real ones is the one thing this project treats as a
  hard line, not a style preference.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
