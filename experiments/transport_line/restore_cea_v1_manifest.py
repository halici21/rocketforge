"""Restore the historical NASA CEA Provider v1.0 manifest, and prove it.

**What happened.** Running the Phase 5G freeze-manifest generator during this
session regenerated `freeze_cea_provider_v1.json` from the *current* working
tree. That tree holds v1.1, so the historical record was overwritten with 12
files under a "1.0" label. The supersession tests written during the fluids
foundation caught it immediately -- which is the only reason this is a
recoverable mistake and not a silent falsification.

**Why this is not fabrication.** The v1.0 overall digest

    0a46b5f089a9cc7a47278eecd0868b8d68730aa1abbf9c5775e35cb70eb9285a

is published in four documents that were *not* overwritten. That digest is a
SHA-256 over all eleven files, so a reconstruction either reproduces it exactly
or it does not. This script reconstructs the two files v1.1 changed by
inverting the exact edits that changed them, and **refuses to write anything
unless the digest matches the published value**.

Nine of the eleven files were never touched by v1.1, so their bytes on disk are
still the v1.0 bytes. `enthalpy_coupling.py` did not exist at v1.0 and is
excluded.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

PUBLISHED_DIGEST = ("0a46b5f089a9cc7a47278eecd0868b8d68730aa1abbf9c5775e35cb70"
                    "eb9285a")
PUBLISHED_FILE_COUNT = 11

CEA = ROOT / "rocketforge" / "providers" / "cea"
OUT = ROOT / "acceptance" / "phase_5g"

# Every edit as (v1.1 text, v1.0 text). Newlines are "\n" because the files are
# read with universal newlines; the CRLF layout is restored before hashing.

MAPPING_EDITS = [
    ('''        pressure_bar: Chamber pressure in CEA's native unit.
        product_species: The product set the solve is restricted to.
        enthalpy_correction: J/kg of propellant mixture, added to the enthalpy
            CEA computes for the reactants before it becomes the HP constraint.
            **Added in NASA CEA Provider v1.1**, defaulted to 0.0 so that every
            v1.0 caller and every v1.0 result is unchanged. Non-zero only under
            ``ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION``; see
            ``enthalpy_coupling.py`` for what the number means and why it is a
            difference rather than an absolute enthalpy.
    """
''', '''        pressure_bar: Chamber pressure in CEA's native unit.
        product_species: The product set the solve is restricted to.
    """
'''),
    ('''    product_species: tuple[str, ...]
    enthalpy_correction: float = 0.0
''', '''    product_species: tuple[str, ...]
'''),
    ('''                f"chamber pressure must be positive and finite, got {self.pressure_bar!r} bar")
        if not math.isfinite(self.enthalpy_correction):
            raise CEAMappingError(
                f"enthalpy correction must be finite, got "
                f"{self.enthalpy_correction!r} J/kg")
''', '''                f"chamber pressure must be positive and finite, got {self.pressure_bar!r} bar")
'''),
    ('''        # v1.1: a sensible-enthalpy increment, in J/kg of mixture, on CEA's own
        # mass basis. Zero under the v1.0 native policy, which is why every
        # accepted Phase 5 number is reproduced bit for bit. The addition
        # happens here, before the division by CEA's own R, so the corrected
        # constraint stays in the units CEA posed its solver in.
        corrected = float(mixture_enthalpy) + float(
            chamber_input.enthalpy_correction)
        constraint = enthalpy_argument(corrected, cea_module.R)''',
     '''        constraint = enthalpy_argument(mixture_enthalpy, cea_module.R)'''),
    ('''    molar_masses: Mapping[str, float] | None = None,
    enthalpy_correction: float = 0.0,
) -> CEAChamberInput:''',
     '''    molar_masses: Mapping[str, float] | None = None,
) -> CEAChamberInput:'''),
    ('''        product_species=select_product_species(request),
        # v1.1, defaulted to zero: a caller that says nothing gets exactly the
        # v1.0 description, byte for byte.
        enthalpy_correction=float(enthalpy_correction),
    )''', '''        product_species=select_product_species(request),
    )'''),
]

PROVIDER_EDITS = [
    ('''from .enthalpy_coupling import (
    CEA_REFERENCE_PRESSURE,
    ReactantEnthalpyCorrection,
    ReactantEnthalpyPolicy,
    ReactantFluidBinding,
    mixture_enthalpy_correction,
    reactant_mass_fractions,
    sensible_enthalpy_increment,
)
from .mapping import (''', '''from .mapping import ('''),
    ("from collections.abc import Iterable, Mapping",
     "from collections.abc import Iterable"),
    ("from dataclasses import dataclass, field, replace",
     "from dataclasses import dataclass, field"),
    ('''                   reactant_conditions: dict[str, float] | None = None,
                   enthalpy_policy: ReactantEnthalpyPolicy =
                       ReactantEnthalpyPolicy.PROVIDER_NATIVE,
                   corrections: tuple[ReactantEnthalpyCorrection, ...] = (),
                   ) -> ThermochemistryProvenance:''',
     '''                   reactant_conditions: dict[str, float] | None = None,
                   ) -> ThermochemistryProvenance:'''),
    ('''                "thermo_lib_path": resources.thermo_path if resources else "",
                # v1.1. Always recorded, under both policies, so that a result
                # can never be silent about which reactant-energy model made it.
                "reactant_enthalpy_policy": enthalpy_policy.value,
                "reactant_enthalpy_corrections": repr(
                    [c.as_mapping() for c in corrections]) if corrections else "",
                "cea_reference_pressure_Pa": repr(CEA_REFERENCE_PRESSURE)
                    if corrections else "",
            },''', '''                "thermo_lib_path": resources.thermo_path if resources else "",
            },'''),
    ('''    def solve_chamber(
        self,
        request: ChamberEquilibriumRequest,
        *,
        enthalpy_policy: ReactantEnthalpyPolicy =
            ReactantEnthalpyPolicy.PROVIDER_NATIVE,
        fluid_provider: object | None = None,
        reactant_bindings: Mapping[str, ReactantFluidBinding] | None = None,
    ) -> Solution[ChamberGas]:''', '''    def solve_chamber(
        self, request: ChamberEquilibriumRequest
    ) -> Solution[ChamberGas]:'''),
    ('''        ``Solution``. Those are three different things and stay that way.

        **NASA CEA Provider v1.1.** The three keyword arguments are additive
        and default to the v1.0 behaviour exactly: ``PROVIDER_NATIVE`` applies
        no correction, produces a zero-valued correction field, and reproduces
        every accepted Phase 5 result bit for bit. The policy that was used is
        recorded in provenance either way, so no result is ever silent about
        which model produced it.

        Under ``FLUID_SENSIBLE_CORRECTION`` a reactant whose CEA entry carries
        an *assigned* enthalpy -- one CEA does not vary with temperature --
        receives ``h_fluid(T, p) - h_fluid(T_ref, p_ref)`` from the supplied
        fluid provider. A reactant CEA already treats as temperature-dependent
        receives nothing, which is what stops the sensible term being counted
        twice.
        """''', '''        ``Solution``. Those are three different things and stay that way.
        """'''),
    ('''        chamber_input = build_chamber_input(request, molar_masses=molar_masses)

        corrections: tuple[ReactantEnthalpyCorrection, ...] = ()
        if enthalpy_policy is ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION:
            corrections, chamber_input = self._apply_enthalpy_correction(
                chamber_input, fluid_provider, reactant_bindings)

        raw = solve_chamber_raw(module, chamber_input)''',
     '''        chamber_input = build_chamber_input(request, molar_masses=molar_masses)

        raw = solve_chamber_raw(module, chamber_input)'''),
    ('''            reactant_conditions=request.reactant_conditions,
            enthalpy_policy=enthalpy_policy,
            corrections=corrections)

        diagnostics: list[Diagnostic] = list(
            self._assigned_enthalpy_diagnostics(chamber_input,
                                                corrections=corrections))''',
     '''            reactant_conditions=request.reactant_conditions)

        diagnostics: list[Diagnostic] = list(
            self._assigned_enthalpy_diagnostics(chamber_input))'''),
    ('''        module = self._cea()
        corrected = {c.reactant_name: c for c in corrections}
        found: list[Diagnostic] = []''', '''        module = self._cea()
        found: list[Diagnostic] = []'''),
    ('''            if name in corrected:
                # v1.1: the limitation was corrected rather than merely
                # reported, so the warning is superseded by a record of what
                # was done. It is replaced, never quietly dropped.
                correction = corrected[name]
                found.append(Diagnostic(
                    code="REACTANT_ENTHALPY_FLUID_CORRECTED",
                    severity=Severity.INFO,
                    message=(
                        f"NASA CEA models reactant {name!r} with an assigned "
                        f"enthalpy at {assigned} K. The stream temperature of "
                        f"{temperature} K was represented by adding a sensible "
                        f"enthalpy increment of {correction.delta_h:.6g} J/kg "
                        f"from {correction.provider_label}, evaluated at "
                        f"{correction.requested_pressure} Pa. CEA keeps "
                        "ownership of the chemical reference; only the "
                        "difference between two states of the same fluid was "
                        "supplied."),
                    field="reactant_temperature",
                    detail=dict(correction.as_mapping())))
                continue
            if abs(temperature - assigned) <= 1.0e-9:''',
     '''            if abs(temperature - assigned) <= 1.0e-9:'''),
    ('''    def _assigned_enthalpy_diagnostics(
            self, chamber_input: CEAChamberInput,
            corrections: tuple[ReactantEnthalpyCorrection, ...] = (),
            ) -> list[Diagnostic]:''',
     '''    def _assigned_enthalpy_diagnostics(
            self, chamber_input: CEAChamberInput) -> list[Diagnostic]:'''),
]

#: The whole v1.1 method, removed by locating its boundaries rather than by
#: reproducing sixty lines of it verbatim here -- retyping that block would be
#: its own source of error. At v1.0 neither the method nor the blank line
#: before it existed.
METHOD_START = "    def _apply_enthalpy_correction(\n"
METHOD_END = "    def _assigned_enthalpy_diagnostics(\n"


def remove_method(text: str) -> str:
    start = text.index(METHOD_START)
    end = text.index(METHOD_END)
    if not start < end:
        raise SystemExit("the v1.1 method does not sit where expected")
    return text[:start] + text[end:]


def invert(text: str, edits, label: str) -> str:
    for index, (after, before) in enumerate(edits, start=1):
        if after not in text:
            raise SystemExit(f"{label} edit {index}: v1.1 text not found:\n"
                             f"{after[:160]!r}")
        text = text.replace(after, before, 1)
    return text


print("Restoring NASA CEA Provider v1.0 manifest")

mapping_v10 = invert((CEA / "mapping.py").read_text(encoding="utf-8"),
                     MAPPING_EDITS, "mapping.py")
provider_v10 = remove_method(
    invert((CEA / "provider.py").read_text(encoding="utf-8"),
           PROVIDER_EDITS, "provider.py"))
print("  both files inverted")

LEFTOVER_MARKERS = ("v1.1", "enthalpy_correction", "ReactantEnthalpy",
                    "enthalpy_coupling", "corrections", "reactant_bindings",
                    "fluid_provider", "_apply_enthalpy_correction",
                    "mixture_enthalpy_correction", "reactant_mass_fractions",
                    "sensible_enthalpy_increment")
for label, body in (("mapping.py", mapping_v10), ("provider.py", provider_v10)):
    found = [(m, body.count(m)) for m in LEFTOVER_MARKERS if body.count(m)]
    if found:
        raise SystemExit(f"{label} still contains v1.1 material: {found}")
print("  no v1.1 material remains in either reconstruction")

# The files on disk are CRLF; restore that layout before hashing.
RECONSTRUCTED = {
    "mapping.py": mapping_v10.replace("\n", "\r\n").encode("utf-8"),
    "provider.py": provider_v10.replace("\n", "\r\n").encode("utf-8"),
}

FILES_V10 = ["__init__.py", "availability.py", "errors.py", "mapping.py",
             "naming.py", "oracle.py", "propellants.py", "provider.py",
             "resources.py", "species.py", "units.py"]

entries = []
for name in FILES_V10:
    data = RECONSTRUCTED.get(name) or (CEA / name).read_bytes()
    entries.append((f"rocketforge/providers/cea/{name}",
                    hashlib.sha256(data).hexdigest()))

text = "".join(f"{digest}  {path}\n" for path, digest in sorted(entries))
digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

print(f"  files: {len(entries)} (published {PUBLISHED_FILE_COUNT})")
print(f"  reconstructed: {digest}")
print(f"  published:     {PUBLISHED_DIGEST}")
match = digest == PUBLISHED_DIGEST
print(f"  MATCH: {match}")

if not match:
    print("\n  Reconstruction does not reproduce the published digest.")
    print("  Nothing written. The historical per-file record is not recoverable")
    print("  by this route and must be reported as lost.")
    sys.exit(1)

record = {
    "contract": "NASA CEA PROVIDER",
    "version": "1.0",
    "algorithm": "rocketforge-freeze-manifest/1",
    "roots": ["rocketforge/providers/cea"],
    "note": "the provider as accepted at the Phase 5G propulsion freeze",
    "file_count": len(entries),
    "digest": digest,
    "restored": (
        "This file was overwritten in error during the transport/line work by "
        "running the Phase 5G generator against a v1.1 tree, and restored by "
        "inverting the v1.1 edits. The restoration was accepted only because "
        "it reproduces the digest published in PHASE_5G_INTEGRATED_PROPULSION_"
        "ACCEPTANCE.md, CEA_PROVIDER_CONTRACT.md and two checkpoints -- a "
        "SHA-256 over all eleven files, which cannot be matched by accident."),
    "files": [{"path": p, "sha256": d} for p, d in sorted(entries)],
}
(OUT / "freeze_cea_provider_v1.json").write_text(json.dumps(record, indent=2),
                                                 encoding="utf-8")
(OUT / "freeze_cea_provider_v1.sha256").write_text(text, encoding="utf-8")
print("  restored, and verified against the published digest")
