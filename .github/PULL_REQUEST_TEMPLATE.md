**What does this change, and why?**

**Which mode/area does it touch?**
- [ ] Analysis mode physics (`rocketforge/physics/`, `rocketforge/engineering/`)
- [ ] Analysis mode UI (`ui/pages/`)
- [ ] Engine Design (`ui/engine/`)
- [ ] Shell / theme / infrastructure
- [ ] Tests / CI / docs only

**If this touches physics:** does it change a frozen contract's output or
tolerance? (See [Known limitations](../README.md#known-limitations) and
[Verification and freeze status](../README.md#verification-and-freeze-status).)
If yes, link the issue where this was discussed first — see
[CONTRIBUTING.md](../CONTRIBUTING.md).

**Testing**
- [ ] `pytest -q` passes locally (base suite)
- [ ] `pytest -q` passes against the CEA-enabled environment, if this touches
      thermochemistry/performance
- [ ] Added or updated a test covering this change
- [ ] If QML/UI: which page(s) were checked manually, and how

**Checklist**
- [ ] No tolerance was widened to make a test pass
- [ ] No `rocketforge/physics/compressible/` change without a linked defect
      report
- [ ] CI is green
