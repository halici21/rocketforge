# Compressible Flow — Theory Map

How the ten modules relate. Architectural, not a textbook: what each module
owns, what it is allowed to call, and which identity ties it to its neighbours.

---

## 1. The dependency spine

```
                        PerfectGas
                    gamma, R, cp, cv, a(T)
                             |
                             v
                        Isentropic
              T/T0  p/p0  rho/rho0  A/A*  mu(M)
                             |
              +--------------+--------------+
              |                             |
              v                             v
          Area-Mach                     Mass Flow
     two roots per A/A*            MFP, Gamma, mdot
              |                             |
              +--------------+--------------+
                             |
                             v
                    Choking / critical flow
                             |
                             v
                   C-D NOZZLE (integrating)
              thresholds, regimes, distribution
```

Independent families, each anchored to the spine by an identity rather than by
an import:

```
    Normal Shock  <----- the shock is a Fanno-Rayleigh intersection ----->  Fanno
         ^   ^                                                            Rayleigh
         |   |
         |   +---- Oblique Shock: the same jump at M1 sin(beta)
         |
         +-------- the nozzle's internal shock

    Prandtl-Meyer <---- an expansion is isentropic: same p0, same T0 ----> Isentropic
```

## 2. What each module owns

| Module | Owns | Calls |
| --- | --- | --- |
| `gas` | gamma, R, cp, cv, speed of sound | nothing |
| `isentropic` | the four ratios, A/A*, the Mach angle, three closed-form inverses, the two-branch area inverse | `gas` |
| `mass_flow` | MFP, Gamma, choked flow, the critical ratios | `gas` |
| `normal_shock` | the jump relations, the pitot ratio, four inverses | `gas` |
| `prandtl_meyer` | nu, nu_max, the inverse, expansion and compression turns | `gas`, `isentropic` (Mach angle, re-exported) |
| `oblique_shock` | theta-beta-M, theta_max, both roots, the curve | `gas`, `normal_shock` |
| `fanno` | five starred ratios, 4 f_F L*/D, both inverses, the duct problem | `gas` |
| `rayleigh` | five starred ratios, both critical points, the T0 inverse, the heat problem | `gas` |
| `geometry` | the supplied area distribution and its monotone interpolation | nothing |
| `nozzle` | thresholds, regimes, shock location, the distributed solution | `isentropic`, `normal_shock`, `mass_flow`, `geometry` |

**No module restates another's relation.** The reuse audit reads the source for
the formulas that must not appear in each one, and runtime spies confirm the
calls really happen.

## 3. The identities that hold the subsystem together

Each is a test in `test_cross_module_consistency.py`.

| Identity | Ties together |
| --- | --- |
| `p/p0 / (rho/rho0) = T/T0` | isentropic, internally |
| `mdot/mdot_choked = MFP/Gamma = A*/A` | mass flow to area-Mach |
| `choked_mass_flow = mass_flow(M=1)` | mass flow, internally |
| `T2/T1 = (p2/p1)/(rho2/rho1)` | normal shock to the ideal gas law |
| `p02/p01` rebuilt from the isentropic ratios | normal shock to isentropic |
| `A2*/A1* = p01/p02` | normal shock to the nozzle's downstream branch |
| the two shock states share one Fanno line | normal shock to Fanno |
| the two shock states share one Rayleigh line | normal shock to Rayleigh |
| `fanno.temperature_ratio == isentropic.temperature_ratio_star` | Fanno to isentropic |
| `fanno.stagnation_pressure_ratio == isentropic.area_ratio` | Fanno to isentropic |
| an expansion's ratios equal the isentropic ratios between M1 and M2 | PM to isentropic |
| `prandtl_meyer.mach_angle is isentropic.mach_angle` | one implementation, not two |
| an oblique shock equals `normal_shock.solve(M1 sin beta)` | oblique to normal |
| beta = 90 deg reduces oblique to normal exactly | oblique to normal |
| beta -> mu gives no jump at all | oblique to the Mach wave |
| `f_D = 4 f_F`, one duct two conventions | Fanno, internally |
| static T peaks at 1/sqrt(gamma), stagnation T at 1 | Rayleigh, internally |
| every nozzle station satisfies its own area relation | nozzle to area-Mach |
| nozzle mass flow is `mass_flow.choked_mass_flow` | nozzle to mass flow |
| the nozzle shock is `normal_shock.solve` | nozzle to normal shock |
| the three criticals are isentropic and shock relations | nozzle to both |
| every module agrees about M = 1 | all ten |

## 4. The three sonic references, which are not the same state

`*` marks a sonic reference in three families, and they differ:

* **isentropic / area-Mach / mass flow / nozzle** — reached isentropically from
  the same stagnation state. Shares p0 and T0 with the flow.
* **Fanno** — reached by friction along the same Fanno line. Shares T0 but not
  p0: friction is irreversible.
* **Rayleigh** — reached by heat exchange along the same Rayleigh line. Shares
  neither.

Two coincidences are exact and tested; three deliberate non-coincidences are
tested as well, so the families cannot quietly merge.

## 5. Where irreversibility lives

| Process | s changes? | p0 | T0 |
| --- | --- | --- | --- |
| isentropic passage | no | constant | constant |
| Prandtl-Meyer expansion | no | constant | constant |
| normal shock | yes, discontinuously | drops at the shock | constant |
| oblique shock | yes, discontinuously | drops at the shock | constant |
| Fanno | yes, continuously | falls along the duct | constant |
| Rayleigh | either sign | falls with heating | changes with heat |
| C-D nozzle, shock-free | no | constant | constant |
| C-D nozzle, internal shock | yes, at one station only | one discrete step | constant |

The last row is the model's whole statement about nozzle irreversibility: v1
contains exactly one loss mechanism, and it is located at the shock.

## 6. Where this layer stops

The map ends at the exit plane and at the wall. External plumes, boundary
layers, separation, chemistry and every performance quantity live above this
layer, in modules that will call it. Nothing in `physics.compressible` knows
what a rocket is.
