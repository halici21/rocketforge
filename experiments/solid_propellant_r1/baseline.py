"""Sections 8 / 36 / 76: freeze the bipropellant contract.

Runs the canonical LOX/LCH4 chamber solve through the production provider and
records the serialised result plus a digest. The closure re-runs this and
requires the digest to be identical -- that is the bit-identical legacy gate.
"""
from __future__ import annotations
import hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "solid_propellant_r1"

from rocketforge.physics.thermochemistry import (          # noqa: E402
    ChamberEquilibriumRequest, MixtureRatio, Phase, PropellantStream,
    to_jsonable)
from rocketforge.providers.cea.propellants import LOX, LIQUID_METHANE   # noqa: E402
from rocketforge.providers.cea import CEAThermochemistryProvider  # noqa: E402

#: The canonical case the existing suite uses (test_provider_contract.py:137).
CANONICAL = {
    "fuel": "LCH4", "oxidiser": "LOX",
    "fuel_temperature_K": 111.643, "oxidiser_temperature_K": 90.17,
    "oxidiser_fuel_ratio": 3.4, "chamber_pressure_Pa": 10.0e6,
}


def canonical_request() -> ChamberEquilibriumRequest:
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_METHANE, CANONICAL["fuel_temperature_K"],
                              phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, CANONICAL["oxidiser_temperature_K"],
                                  phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(CANONICAL["oxidiser_fuel_ratio"]),
        chamber_pressure=CANONICAL["chamber_pressure_Pa"])


def solve_canonical(provider: CEAThermochemistryProvider) -> dict:
    result = provider.solve_chamber(canonical_request()).unwrap()
    return to_jsonable(result)


def digest(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def main() -> int:
    provider = CEAThermochemistryProvider()
    if not provider.is_available:
        print("FAIL: CEA provider unavailable; run under .venv-cea")
        return 1

    payload = solve_canonical(provider)
    record = {
        "case": CANONICAL,
        "provider_provenance": to_jsonable(provider.provenance()),
        "chamber_result": payload,
        "chamber_digest": digest(payload),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (sys.argv[1] if len(sys.argv) > 1 else "opening_baseline.json")
    target.write_text(json.dumps(record, indent=2, sort_keys=True, default=str)
                      + "\n", encoding="utf-8")

    print("canonical LOX/LCH4 chamber solve captured")
    print("  digest :", record["chamber_digest"][:16])
    for key in ("temperature", "pressure", "mean_molar_mass"):
        if key in payload:
            print("  %-16s %s" % (key, payload[key]))
    print("written:", target.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
