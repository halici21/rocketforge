"""Teach the freeze suite that NASA CEA Provider v1.0 is now historical.

The two failures this fixes are the machinery working, not breaking: the CEA
provider's source changed, so its v1.0 digest no longer describes what is on
disk and a new file is not in its manifest. The wrong fix is to regenerate the
v1.0 manifest, which would erase the record of what Phase 5G actually accepted.
The right one is to say so: v1.0 is kept, marked historical, and superseded by
v1.1, which is what must now match the source.
"""
from __future__ import annotations

import pathlib

p = pathlib.Path("tests/acceptance/test_propulsion_freeze.py")
t = p.read_text(encoding="utf-8")

old = '''ACCEPTANCE = ROOT / "acceptance" / "phase_5g"

MANIFEST_STEMS = [
    "freeze_thermochemistry_api_v1",
    "freeze_rocket_performance_api_v1",
    "freeze_trade_study_api_v1",
    "freeze_cea_provider_v1",
]
'''
new = '''ACCEPTANCE = ROOT / "acceptance" / "phase_5g"
FLUIDS_ACCEPTANCE = ROOT / "acceptance" / "fluids_foundation"

#: Manifests that must still describe what is on disk.
#:
#: ``freeze_cea_provider_v1`` is deliberately absent. The fluids foundation
#: extended the CEA provider additively, so its source changed and its v1.0
#: digest no longer describes the source -- which is the freeze machinery
#: working. The v1.0 manifest is kept unmodified as the record of what Phase 5G
#: accepted, and is checked below as *history*; v1.1 is what must match now.
MANIFEST_STEMS = [
    "freeze_thermochemistry_api_v1",
    "freeze_rocket_performance_api_v1",
    "freeze_trade_study_api_v1",
]

#: Superseded manifests: internally consistent, publicly recorded, and no
#: longer expected to match the working tree.
HISTORICAL_MANIFESTS = {
    "freeze_cea_provider_v1": "freeze_cea_provider_v1_1",
}
'''
assert old in t
t = t.replace(old, new, 1)

# load_manifest looks only in the Phase 5G directory; teach it both.
old_load = '''def load_manifest(stem: str) -> dict:
    path = ACCEPTANCE / f"{stem}.json"
    if not path.is_file():
        pytest.skip(f"{stem}.json has not been generated")
    return json.loads(path.read_text(encoding="utf-8"))
'''
new_load = '''def load_manifest(stem: str) -> dict:
    for directory in (ACCEPTANCE, FLUIDS_ACCEPTANCE):
        path = directory / f"{stem}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    pytest.skip(f"{stem}.json has not been generated")
'''
assert old_load in t
t = t.replace(old_load, new_load, 1)

old_roots = '''    expected_roots = {
        "freeze_thermochemistry_api_v1": ["rocketforge/physics/thermochemistry"],
        "freeze_rocket_performance_api_v1": ["rocketforge/engineering/chamber",
                                             "rocketforge/engineering/nozzle"],
        "freeze_trade_study_api_v1": ["rocketforge/engine/studies"],
        "freeze_cea_provider_v1": ["rocketforge/providers/cea"],
    }'''
new_roots = '''    expected_roots = {
        "freeze_thermochemistry_api_v1": ["rocketforge/physics/thermochemistry"],
        "freeze_rocket_performance_api_v1": ["rocketforge/engineering/chamber",
                                             "rocketforge/engineering/nozzle"],
        "freeze_trade_study_api_v1": ["rocketforge/engine/studies"],
        "freeze_cea_provider_v1_1": ["rocketforge/providers/cea"],
        "freeze_fluid_properties_api_v1": ["rocketforge/physics/fluids"],
        "freeze_coolprop_provider_v1": ["rocketforge/providers/fluid_properties"],
        "freeze_propellant_metrics_api_v1": ["rocketforge/engineering/propellants"],
    }'''
assert old_roots in t
t = t.replace(old_roots, new_roots, 1)

t += '''

# ===========================================================================
# versioned supersession
# ===========================================================================


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_a_superseded_manifest_is_kept_and_still_internally_consistent(
        old_stem, new_stem):
    """History is preserved, not rewritten.

    The superseded manifest must still reproduce its own recorded digest from
    its own recorded hashes. That is what makes it evidence: it says what the
    package looked like when it was accepted, and it keeps saying it after the
    package moves on.
    """
    manifest = load_manifest(old_stem)
    entries = [(e["sha256"], e["path"]) for e in manifest["files"]]
    assert independent_digest(entries) == manifest["digest"]


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_the_successor_names_what_it_supersedes(old_stem, new_stem):
    successor = load_manifest(new_stem)
    assert successor["supersedes"] == old_stem
    assert successor["change"], "a version bump must say what changed"


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_a_version_bump_is_additive_and_removes_no_file(old_stem, new_stem):
    """v1.1 must still contain everything v1.0 froze.

    A removed module would be a breaking change wearing a minor version
    number, which is the thing this test exists to prevent.
    """
    before = {e["path"] for e in load_manifest(old_stem)["files"]}
    after = {e["path"] for e in load_manifest(new_stem)["files"]}
    assert not (before - after), {"removed": sorted(before - after)}


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_the_two_versions_actually_differ(old_stem, new_stem):
    """A version bump that changed nothing would be noise in the record."""
    assert load_manifest(old_stem)["digest"] != load_manifest(new_stem)["digest"]


def test_the_superseded_manifest_file_was_not_modified():
    """The historical record still describes the version it was written for.

    Checked by content rather than by mtime: the v1.0 manifest must still name
    v1.0 and must not have acquired the successor's files.
    """
    manifest = load_manifest("freeze_cea_provider_v1")
    assert manifest["version"] == "1.0"
    paths = {e["path"] for e in manifest["files"]}
    assert "rocketforge/providers/cea/enthalpy_coupling.py" not in paths, (
        "regenerating the v1.0 manifest would erase what Phase 5G accepted")
'''

p.write_text(t, encoding="utf-8")
print("freeze suite updated")
