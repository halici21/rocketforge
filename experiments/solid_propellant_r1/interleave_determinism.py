"""Gate items 6 and 7: does a solid solve disturb the bipropellant path?

``cea`` holds process-global state, so the question is not rhetorical. A solid
solve builds a different reactant mixture, a different product set derived from
reactants, and a custom ``Reactant`` object -- any of which could leave the
library in a state the next bipropellant solve inherits.

The shape of the check is A / solid / A:

* Solve the canonical LOX/LCH4 case.
* Solve RP-1311 Example 5.
* Solve the canonical case again.

The first and third must be **bit identical**, and both must match the digest
recorded in ``opening_baseline.json`` before any of this work began. A single
run of A would not catch contamination; comparing only against the baseline
would not distinguish contamination from ordinary run-to-run variation.
"""

from __future__ import annotations

import json
import pathlib
import sys

import cea

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from baseline import (  # noqa: E402
    CANONICAL,
    digest,
    solve_canonical,
)

from rocketforge.providers.cea import CEAThermochemistryProvider  # noqa: E402
from example5_rocketforge import base_provenance, build_request  # noqa: E402
from rocketforge.providers.cea_solid import solve_solid_chamber  # noqa: E402


def main() -> int:
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here))

    opening = json.loads(
        (ROOT / "acceptance" / "solid_propellant_r1" / "opening_baseline.json")
        .read_text(encoding="utf-8"))
    recorded = opening["chamber_digest"]

    provider = CEAThermochemistryProvider()

    first = solve_canonical(provider)
    d1 = digest(first)

    solid = solve_solid_chamber(cea, build_request(), provenance=base_provenance())

    third = solve_canonical(provider)
    d3 = digest(third)

    print(f"canonical case          : {CANONICAL['fuel']}/{CANONICAL['oxidiser']} "
          f"O/F {CANONICAL['oxidiser_fuel_ratio']} @ "
          f"{CANONICAL['chamber_pressure_Pa']:.3g} Pa")
    print(f"solid interleaved       : Tc {solid.temperature!r} K")
    print()
    print(f"A  digest               : {d1}")
    print(f"A' digest (after solid) : {d3}")
    print(f"opening baseline digest : {recorded}")
    print()

    same = d1 == d3
    matches_baseline = d1 == recorded
    print(f"A == A'                 : {same}")
    print(f"A == opening baseline   : {matches_baseline}")

    if not same:
        for key in sorted(set(first) | set(third)):
            if first.get(key) != third.get(key):
                print(f"   DRIFT {key}: {first.get(key)!r} -> {third.get(key)!r}")

    # A negative control, so a passing result means the check can actually fail.
    mutated = json.loads(json.dumps(third, default=str))
    mutated["temperature"] = float(mutated["temperature"]) + 1e-9
    control_detects = digest(mutated) != d3
    print(f"negative control fires  : {control_detects}"
          "   (a 1e-9 K change must change the digest)")

    verdict = same and matches_baseline and control_detects
    print(f"\nVERDICT: {'PASS' if verdict else 'FAIL'}")

    (here / "interleave_determinism.json").write_text(json.dumps({
        "digest_A": d1,
        "digest_A_after_solid": d3,
        "opening_baseline_digest": recorded,
        "A_equals_A_prime": same,
        "A_equals_opening_baseline": matches_baseline,
        "negative_control_detects_change": control_detects,
        "solid_temperature_k": solid.temperature,
        "verdict": "PASS" if verdict else "FAIL",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
