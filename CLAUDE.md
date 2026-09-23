# RocketForge — notes for Claude Code

## Repository essentials

- Python 3.13 + PySide6. The whole interface is QML under `ui/`; the backend is
  `rocketforge/`. `main.py:build_engine()` constructs every analysis controller
  and registers it as a QML singleton (`Isentropic`, `Nozzle`, `Thermochemistry`,
  `RocketPerformance`, `TradeStudy`, `FluidProperties`, `Line`, ...). QML binds
  to the controllers' `Property`/`Slot` members, e.g. `TradeStudy.hasResult`.
- Backend layers, lowest first: `core → physics → engineering → engine →
  providers → comparison → application`. Allowed imports, "Qt only in
  `application`", "CEA/CoolProp only in `providers`", and "no SciPy at runtime"
  are enforced by `tests/test_architecture.py` (spec:
  `docs/engineering/01_engineering_architecture.md` §2).
- Tests: `.venv\Scripts\python.exe -m pytest -q` (base) and
  `.venv-cea\Scripts\python.exe -m pytest -q` (adds NASA CEA provider tests).
  Never use a bare `python`/`pytest` — conda on PATH can resolve the wrong
  interpreter. Tests that read developer-machine evidence in the untracked
  `/acceptance/` folder skip themselves one by one when it is absent; CI runs
  everything else. Tracked freeze manifests and reference records live in
  `tests/acceptance/`.
- `main.configure_application()` sets `QV4_GC_TIMELIMIT=0` (one-pass QML
  garbage collection): Qt 6.10.2's incremental collector freed live objects
  and crashed Nozzle Lab → Thermochemistry. Keep it unless a Qt upgrade passes
  `tests/application/test_shell_navigation_smoke.py` and the session soak with
  it off; see `docs/engineering/implementation/NOTATION_NAVIGATION_CRASH.md`.

## Graphify — repository navigation and impact analysis

`graphify-out/graph.json` is a static graph of the Python backend, tests,
examples, and Markdown docs: imports, calls, containment, and backticked
symbol mentions in docs. It is a **discovery and impact-analysis layer; the
source code is the source of truth.** Never implement a change from the graph
alone — confirm every relationship you act on in the real files. This section
governs Graphify use; it overrides the tool-owned `## graphify` block at the end
of this file if that block is ever regenerated.

### Query it when the task needs

- ownership of a feature or where a physical model is implemented;
- reverse dependencies / blast radius before changing a shared type or contract
  (`PerfectGas`, `ChamberGas`, `Solution`, `Diagnostic`, `Status`,
  `MixtureRatio`, `PropellantStream`, `ToleranceSet`, `brent()`);
- a call chain from a controller down to a physics/engineering function;
- which tests exercise a function, including indirectly through a service;
- which spec/contract section in `docs/engineering/` describes a symbol;
- refactoring scope, cross-layer moves, or an unfamiliar subsystem.

### Skip it when

- the file or symbol is already known or named by the user;
- the edit is single-file, copy/text, formatting, or a QML style/layout tweak;
- the question is about QML — the graph contains no QML (see blind spots);
- a single targeted Grep answers the question faster.

### Non-trivial change protocol (internal discipline — do not narrate it)

1. Identify the subsystem and layer(s) involved.
2. Decide whether the dependency scope is already obvious. If it is, skip to 5.
3. Otherwise query Graphify before broad Glob/Grep exploration.
4. List likely upstream and downstream dependents, and the tests and spec that cover them.
5. Read the actual implementation files; verify each relationship you rely on.
6. Settle the expected change surface before editing.
7. Implement.
8. Run the focused tests for the touched modules.
9. If a shared type, contract, or layer boundary changed, run the full suite
   (both environments when thermochemistry/performance is involved) including
   `tests/test_architecture.py`.
10. If modules were added, moved, or renamed and you need to query again in this
    session, run `graphify update .` first.

### Commands (run the CLI via Bash; don't load the `/graphify` skill for lookups)

- `graphify affected "ChamberGas" --depth 2` — reverse dependencies. The most
  reliable command here; results matched Grep plus transitive consumers.
- `graphify path "NozzleController" "mach_from_area_ratio()"` — directed call
  chain. Treat "no directed path" as a hint to check the blind spots below;
  `--undirected` mostly routes through `main.py` imports and is rarely meaningful.
- `graphify explain "CEAThermochemistryProvider"` — callers, importers, docs
  that mention it. Ambiguous names (e.g. `MixtureRatio` also matches the
  controller's `mixtureRatio` property) need the file-qualified form:
  `graphify explain "rocketforge/physics/thermochemistry/propellants.py::MixtureRatio"`.
- `graphify query "<ExactSymbol OtherSymbol>" --budget 1500 [--context call]` —
  BFS seeded by label matching. Use exact identifiers; prose words such as
  "get", "state", "points", "chamber", or "evaluate" seed unrelated nodes.
- `graphify god-nodes --top 20` and `graphify-out/GRAPH_REPORT.md` (130+ KB —
  grep it, don't read it whole) — broad architecture review only.

Labels: functions `name()`, methods `.name()`, classes bare (`ChamberGas`).
Edges marked `INFERRED` (mostly doc→code) are hints, not facts.

### Blind spots — check these by hand

- **QML is not parsed.** No `ui/**/*.qml` node exists. To find UI consumers of a
  controller member, Grep `ui/` with glob `*.qml` for `TradeStudy.hasResult`
  (singleton names are in `main.py:build_engine()`).
- **Aliased-module calls made inside methods or lambdas are dropped.** The
  `RocketPerformance`, `TradeStudy`, `FluidProperties`, and `Line` controllers
  call their service as `service.x()`, and `ThermochemistryController` calls
  `sweep.x()`/`reference.x()`, so the controller→service hop is missing for
  them; the eight classic compressible controllers import service functions
  directly and are linked. Start from the service function (for example
  `solve_performance()`) or read the controller's `service.` calls.
- **Controller-to-controller wiring is duck-typed.**
  `RocketPerformanceController` reads the chamber via
  `chamber_source.chamber_outcome()` and `TradeStudyController` takes both
  upstream controllers; the graph links them only through `main.py`.
- **Runtime provider binding.** Services reach CEA/CoolProp through the lazy
  gateways `application/analysis/thermochemistry_provider.py` and
  `fluid_property_provider.py`; calls on the returned object resolve to the
  protocol in `physics/*/protocols.py`, not to a guaranteed concrete provider.
- **"Import Cycles" in GRAPH_REPORT are false positives**: `from . import
  submodule` is read as importing the package `__init__`.
- Community names are auto-derived from hub nodes, not real subsystem names.
- Not indexed on purpose (`.graphifyignore`): `experiments/`, `.claude/`,
  `.github/`, `packaging/`, repository meta files.

### High-value queries in this repository

- `graphify affected "ChamberGas" --depth 2` — before touching the chamber-state
  contract: CEA and solid providers, `engineering/chamber/handshake.py`,
  `comparison/extract.py`, tests, and `09_…` spec §7.
- `graphify affected "PerfectGas" --depth 1` — every compressible module and service.
- `graphify affected "Diagnostic" --depth 1` (or `Solution`, `Status`) — the
  result/diagnostic contract shared by every solver and controller.
- `graphify affected "brent()" --depth 1` — every model that depends on the
  in-house root solver.
- `graphify affected "reduce_chamber_gas()" --depth 3` — tests covering gamma
  reduction, including indirectly via `solve_performance()`.
- `graphify path "NozzleController" "mach_from_area_ratio()"` — UI controller →
  service → physics chain for the nozzle back-pressure sweep.
- `graphify explain "solve_performance()"` — performance chain: who calls it
  (trade study, tests, docs) and what it calls (`reduce_chamber_gas`,
  `solve_ideal_performance`).
- `graphify affected "colebrook_darcy_friction_factor()" --depth 2` — Line
  friction model consumers and tests.
- `graphify explain "pareto_membership()"` — where Pareto membership is
  decided (`engine/studies/analysis.py:analyse()`), not inside `run_study()`.
- `graphify explain "CEAThermochemistryProvider"` — provider adapter, its lazy
  import in the gateway, and the contracts it returns.
- `graphify explain "rocketforge/physics/compressible/nozzle.py::classify()"` —
  code plus the spec section (`04_…` §7) that defines its domain.

### Keeping the graph current

- `graphify-out/` is gitignored and local. On a fresh clone, or if it is
  missing, run `graphify update .` once (~30 s, AST-only, no API cost).
- Git `post-commit`/`post-checkout` hooks rebuild it in the background after
  every commit and branch switch (log: `~/.cache/graphify-rebuild.log`); this
  covers code and Markdown structure. Hooks do not run in linked worktrees.
- Uncommitted edits are not in the graph. Don't rebuild at session start or
  after every edit; rebuild only per step 10 above, or after committing a large
  docs/spec change you want to query immediately.
- LLM-based semantic extraction (`/graphify` skill, `graphify extract`) is not
  used here; the deterministic Markdown pass already links docs to symbols.

## graphify

Tool-owned block: `graphify install --project` and `graphify claude install`
rewrite everything from this heading to the next `##` heading. The Graphify
policy above governs when and how to use the graph.

- Graph: `graphify-out/graph.json`; build or refresh with `graphify update .`.
- Full-pipeline skill (not needed for lookups): `.claude/skills/graphify/SKILL.md`, invoked with `/graphify`.
