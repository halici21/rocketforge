# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project does not yet follow strict Semantic Versioning (Engine Design mode
is not feature-complete, so a 1.0.0 would overstate it — see
[Known limitations](README.md#known-limitations)).

## [v0.1.0] — 2026-09-14

First downloadable build.

### Added
- Analysis mode: classic gas dynamics (Fanno, Rayleigh, isentropic,
  normal/oblique shock, Prandtl-Meyer, mass flow), NASA CEA-backed
  thermochemistry, CoolProp-backed fluid properties, line/transport, and a
  chamber+nozzle performance chain (c*, Cf, Isp) — all frozen, documented
  contracts (see [docs/README.md](docs/README.md)).
- Trade Study: design-space evaluation with Pareto-front visualization.
- Engine Design mode: an interactive canvas, component palette, and
  inspector — presentation-only, no component is solved end to end (see
  [Known limitations](README.md#known-limitations)).
- CI (GitHub Actions) running the full test suite, both with and without
  the NASA CEA provider installed.
- Prebuilt Windows executable, self-contained (NASA CEA and CoolProp
  bundled).

### Verified
- NASA CEA and Cantera thermochemistry providers, cross-checked against
  each other and against independent published references — see
  [docs/engineering/verification/CEA_CANTERA_VERIFICATION_R1.md](docs/engineering/verification/CEA_CANTERA_VERIFICATION_R1.md).

[v0.1.0]: https://github.com/halici21/rocketforge/releases/tag/v0.1.0
