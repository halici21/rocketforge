"""Phase 5B-0 - experimental trade-study figures.

Experimental engineering plots, NOT RocketForge UI. Raw sweep points are drawn
as markers; no smoothing, no interpolation, nothing between computed points.

    <cantera env>\\Scripts\\python.exe make_plots.py <indir> <outdir>
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IN = sys.argv[1] if len(sys.argv) > 1 else "acceptance/phase_5b0"
OUT = sys.argv[2] if len(sys.argv) > 2 else "acceptance/phase_5b0"

CEA_CASE = ("NASA CEA v3.3.4 | LOX/CH4, LIQUID reactants at NBP "
            "(O2(L) 90.17 K, CH4(L) 111.643 K)\nPc = 100 bar, Ae/At = 40, "
            "equilibrium chamber")
CT_CASE = ("Cantera 3.2.0 | CH4/O2, GASEOUS reactants at 298.15 K "
           "(no liquid reactant data available)\nPc = 100 bar, HP equilibrium")


def load(name):
    p = os.path.join(IN, name)
    if not os.path.exists(p):
        return []
    with open(p) as fh:
        return list(csv.DictReader(fh))


def col(rows, key):
    out = []
    for r in rows:
        v = r.get(key, "")
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            out.append(float("nan"))
    return out


cea = load("cea_of_sweep.csv")
ct = load("cantera_of_sweep.csv")
made = []


def finish(fig, ax, fname, title, xlabel, ylabel, note=None):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=9)
    ax.grid(True, alpha=0.3)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=8)
    if note:
        fig.text(0.01, 0.01, note, fontsize=6.5, va="bottom", color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    p = os.path.join(OUT, fname)
    fig.savefig(p, dpi=140)
    plt.close(fig)
    made.append(fname)
    print("  wrote", fname)


DIFFERENT_CASES = ("NOTE: the two providers are solving DIFFERENT physical cases - "
                   "CEA uses liquid reactants at their normal boiling points, Cantera "
                   "uses gaseous reactants at 298.15 K because it has no liquid "
                   "reactant data. The offset between the curves is therefore expected "
                   "and is NOT a provider disagreement.")

# --- 01 Tc -----------------------------------------------------------------
if cea or ct:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    if cea:
        ax.plot(col(cea, "of"), col(cea, "Tc_K"), "o-", ms=3.2, lw=1.2,
                label="NASA CEA v3.3.4 - liquid reactants at NBP")
    if ct:
        ax.plot(col(ct, "of"), col(ct, "Tc_K"), "s--", ms=3.2, lw=1.2,
                label="Cantera 3.2.0 - gaseous reactants at 298.15 K")
    finish(fig, ax, "01_tc_vs_of.png",
           "Chamber temperature vs mixture ratio - LOX/CH4, Pc = 100 bar, "
           "equilibrium chemistry",
           "O/F mixture ratio by mass [-]", "Chamber temperature Tc [K]",
           DIFFERENT_CASES)

# --- 02 molar mass ---------------------------------------------------------
if cea or ct:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    if cea:
        ax.plot(col(cea, "of"), col(cea, "M_kg_per_kmol"), "o-", ms=3.2, lw=1.2,
                label="NASA CEA v3.3.4 - liquid reactants")
    if ct:
        ax.plot(col(ct, "of"), col(ct, "M_kg_per_kmol"), "s--", ms=3.2, lw=1.2,
                label="Cantera 3.2.0 - gaseous reactants")
    finish(fig, ax, "02_molar_mass_vs_of.png",
           "Chamber mean molar mass vs mixture ratio - LOX/CH4, Pc = 100 bar, "
           "equilibrium chemistry",
           "O/F mixture ratio by mass [-]",
           "Mean molar mass M [kg/kmol]", DIFFERENT_CASES)

# --- 03 gamma --------------------------------------------------------------
if cea or ct:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    if cea:
        ax.plot(col(cea, "of"), col(cea, "gamma_s"), "o-", ms=3.2, lw=1.2,
                label="CEA gamma_s (equilibrium isentropic exponent, native)")
    if ct:
        ax.plot(col(ct, "of"), col(ct, "gamma_s"), "s--", ms=3.2, lw=1.2,
                label="Cantera gamma_s (finite difference on an SP path)")
        ax.plot(col(ct, "of"), col(ct, "gamma_frozen_cp_cv"), "^:", ms=3.2, lw=1.2,
                label="Cantera cp/cv (FROZEN ratio - a different quantity)")
    finish(fig, ax, "03_gamma_vs_of.png",
           "Isentropic exponent vs mixture ratio - LOX/CH4, Pc = 100 bar\n"
           "the equilibrium exponent and the frozen cp/cv ratio are NOT the same "
           "quantity",
           "O/F mixture ratio by mass [-]", "gamma [-]", DIFFERENT_CASES)

# --- 04 species ------------------------------------------------------------
if cea:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for key, lab in (("X_H2O", "H2O"), ("X_CO", "CO"), ("X_CO2", "CO2"),
                     ("X_H2", "H2"), ("X_OH", "OH"), ("X_O2", "O2"),
                     ("X_H", "H"), ("X_O", "O")):
        ax.plot(col(cea, "of"), col(cea, key), "o-", ms=2.6, lw=1.1, label=lab)
    ax.set_yscale("log")
    ax.set_ylim(1e-4, 1.0)
    finish(fig, ax, "04_species_vs_of.png",
           "Chamber equilibrium composition vs mixture ratio\n" + CEA_CASE,
           "O/F mixture ratio by mass [-]", "Mole fraction [-] (log scale)")

# --- 05 c* -----------------------------------------------------------------
if cea:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ofs, cs = col(cea, "of"), col(cea, "cstar_m_per_s")
    ax.plot(ofs, cs, "o-", ms=3.2, lw=1.2, label="c* (CEA native)")
    i = max(range(len(cs)), key=lambda k: cs[k])
    ax.axvline(ofs[i], color="#888888", ls=":", lw=1)
    ax.annotate(f"max c* = {cs[i]:.1f} m/s at O/F = {ofs[i]:.2f}",
                (ofs[i], cs[i]), textcoords="offset points", xytext=(8, -14),
                fontsize=8)
    finish(fig, ax, "05_cea_cstar_vs_of.png",
           "Characteristic velocity c* vs mixture ratio\n" + CEA_CASE,
           "O/F mixture ratio by mass [-]", "c* [m/s]")

# --- 06 Isp equilibrium vs frozen ------------------------------------------
if cea:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ofs = col(cea, "of")
    eq = col(cea, "Isp_eq_m_per_s")
    frt = col(cea, "Isp_frozen_throat_m_per_s")
    frc = col(cea, "Isp_frozen_chamber_m_per_s")
    ax.plot(ofs, eq, "o-", ms=3.2, lw=1.3, label="equilibrium (shifting) - upper bound")
    ax.plot(ofs, frt, "s--", ms=3.2, lw=1.2, label="frozen at throat")
    ax.plot(ofs, frc, "^:", ms=3.2, lw=1.2, label="frozen at chamber - lower bound")
    i = max(range(len(eq)), key=lambda k: eq[k])
    ax.annotate(f"max equilibrium Isp = {eq[i]:.1f} m/s ({eq[i]/9.80665:.1f} s)\n"
                f"at O/F = {ofs[i]:.2f}", (ofs[i], eq[i]),
                textcoords="offset points", xytext=(-40, -34), fontsize=8)
    finish(fig, ax, "06_cea_isp_equilibrium_frozen_vs_of.png",
           "Specific impulse: equilibrium vs frozen chemistry\n" + CEA_CASE,
           "O/F mixture ratio by mass [-]",
           "Isp, effective exhaust velocity [m/s]",
           "Equilibrium and frozen BRACKET the real answer. Neither is 'the' "
           "performance; no average of them is shown, because an average has no "
           "physical basis.")

# --- 07 chemistry gap ------------------------------------------------------
if cea:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ofs = col(cea, "of")
    d = col(cea, "dIsp_eq_minus_frozen_throat")
    rel = [100.0 * v for v in col(cea, "dIsp_rel")]
    ax.plot(ofs, d, "o-", ms=3.2, lw=1.3, color="#1f77b4",
            label="dIsp = Isp_equilibrium - Isp_frozen-at-throat  [m/s]")
    ax.set_ylabel("dIsp [m/s]", color="#1f77b4")
    ax.tick_params(axis="y", labelcolor="#1f77b4")
    ax2 = ax.twinx()
    ax2.plot(ofs, rel, "s--", ms=3.2, lw=1.2, color="#d62728",
             label="dIsp / Isp_equilibrium  [%]")
    ax2.set_ylabel("dIsp / Isp_equilibrium [%]", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper left")
    ax.set_xlabel("O/F mixture ratio by mass [-]")
    ax.set_title("Chemistry-model gap vs mixture ratio\n" + CEA_CASE, fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.text(0.01, 0.01,
             "The gap is the engineering output: it says whether the chemistry "
             "assumption matters for this design point.", fontsize=6.5,
             va="bottom", color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    p = os.path.join(OUT, "07_cea_equilibrium_frozen_gap.png")
    fig.savefig(p, dpi=140)
    plt.close(fig)
    made.append("07_cea_equilibrium_frozen_gap.png")
    print("  wrote 07_cea_equilibrium_frozen_gap.png")

print(f"\n{len(made)} figures written to {OUT}")
