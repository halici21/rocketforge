"""LIQ-2: the Engine Requirement service, controller and their boundaries.

The service checks a requirement's propellant key against the LIQ-1 catalogue
and names its options; the controller holds one immutable requirement and
republishes it. Neither solves anything. The no-solve claim is proved at
runtime in ``test_engine_requirement_runtime.py``; here it is held statically:
neither module imports a provider, a physics or engineering function, or the
thermochemistry gateway.
"""

from __future__ import annotations

import ast
import json
import pathlib
import re

import pytest

from rocketforge.application.analysis import engine_requirement_service as service
from rocketforge.application.analysis import thermochemistry_presets as presets
from rocketforge.application.analysis.engine_requirement_controller import (
    EngineRequirementController,
)
from rocketforge.engine.requirement import (
    ChamberPressureMode,
    ChamberPressurePreference,
    CyclePreference,
    EngineRequirement,
    FeedArchitecture,
    MixtureRatioMode,
    MixtureRatioPreference,
    PropellantMode,
    PropellantPreference,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "rocketforge" / "application" / "analysis"
MODULES = (ANALYSIS / "engine_requirement_service.py",
           ANALYSIS / "engine_requirement_controller.py")
DOMAIN = ROOT / "rocketforge" / "engine" / "requirement.py"
PAGE = ROOT / "ui" / "pages" / "EngineRequirementPage.qml"


def explicit(key: str, **changes) -> EngineRequirement:
    return EngineRequirement(
        thrust=1e5, burn_time=100.0,
        propellant=PropellantPreference(PropellantMode.EXPLICIT, key)).replace(**changes)


# ===========================================================================
# the catalogue reference
# ===========================================================================


def test_every_catalogue_pair_is_offered_by_key_with_blocked_ones_named():
    options = service.pair_options()
    assert [o["key"] for o in options] == [p.key for p in presets.preset_catalogue()]
    blocked = [o for o in options if not o["executable"]]
    assert {o["key"] for o in blocked} == {"sutton-rfna-rp1", "sutton-rfna-a50"}
    assert all(o["blocker"] == presets.RFNA_BLOCKER for o in blocked)


def test_an_explicit_pair_resolves_to_the_catalogue_entry_itself():
    """Referenced, not copied: the very object the catalogue holds."""
    preset = service.resolved_pair(explicit("sutton-o2-ch4"))
    assert preset is presets.preset_named("sutton-o2-ch4")
    assert service.resolved_pair(EngineRequirement()) is None


def test_the_requirement_record_carries_no_chemistry():
    record = explicit("sutton-nto-a50").to_dict()
    text = json.dumps(record)
    for chemistry in ("N2O4", "UDMH", "N2H4", "2.0", "Sutton"):
        assert chemistry not in text, chemistry
    assert record["propellant"] == {"mode": "explicit", "pair_key": "sutton-nto-a50"}


def test_unknown_and_blocked_pairs_are_issues():
    unknown = service.requirement_issues(explicit("sutton-o2-xenon"))
    assert [i.code for i in unknown] == ["PROPELLANT_PAIR_UNKNOWN"]
    blocked = service.requirement_issues(explicit("sutton-rfna-rp1"))
    assert [i.code for i in blocked] == ["PROPELLANT_PAIR_BLOCKED"]
    assert "Red fuming nitric acid" in blocked[0].message
    assert service.requirement_issues(explicit("sutton-o2-h2")) == ()


def test_the_reference_mixture_ratio_is_read_from_the_catalogue():
    requirement = explicit("sutton-o2-rp1", mixture_ratio=MixtureRatioPreference(
        MixtureRatioMode.PAIR_REFERENCE))
    assert service.reference_mixture_ratio(requirement) == \
        presets.preset_named("sutton-o2-rp1").oxidiser_fuel_ratio
    assert service.reference_mixture_ratio(explicit("sutton-o2-rp1")) is None
    blocked = explicit("sutton-rfna-rp1", mixture_ratio=MixtureRatioPreference(
        MixtureRatioMode.PAIR_REFERENCE))
    assert service.reference_mixture_ratio(blocked) is None


def test_every_cycle_option_is_marked_unmodelled_and_ffsc_says_so():
    assert [o["key"] for o in service.CYCLE_OPTIONS] == [c.value for c in CyclePreference]
    assert all(o["modelled"] is False for o in service.CYCLE_OPTIONS)
    ffsc = next(o for o in service.CYCLE_OPTIONS
                if o["key"] == "full_flow_staged_combustion")
    assert "future-modelled intent" in ffsc["note"]
    assert "no full-flow" in ffsc["note"].lower()


def test_option_keys_are_plain_strings_matching_the_domain():
    for options, enum in ((service.FEED_OPTIONS, FeedArchitecture),
                          (service.CHAMBER_PRESSURE_OPTIONS, ChamberPressureMode),
                          (service.MIXTURE_RATIO_OPTIONS, MixtureRatioMode)):
        assert [o["key"] for o in options] == [m.value for m in enum]
        assert all(type(o["key"]) is str for o in options)


def test_units_convert_at_the_boundary_only():
    assert service.from_display("thrust", 2.5) == 2500.0
    assert service.to_display("chamber_pressure", 7.0e6) == 7.0
    assert service.to_display("ambient_pressure", 101325.0) == 101.325
    assert service.from_display("burn_time", None) is None


def test_the_summary_states_open_decisions_and_derives_nothing():
    rows = {row["key"]: row["value"] for row in service.summary_rows(EngineRequirement())}
    assert rows["thrust"] == "Not stated" and rows["burn_time"] == "Not stated"
    assert rows["propellant"] == "Auto · open"
    assert rows["cycle"] == "Not applicable"
    assert rows["environment"].startswith("Sea level")
    pump = EngineRequirement().with_feed(FeedArchitecture.PUMP_FED).replace(
        cycle=CyclePreference.FULL_FLOW_STAGED_COMBUSTION)
    assert {r["key"]: r["value"] for r in service.summary_rows(pump)}["cycle"] == \
        "Full-flow staged combustion"
    keys = [row["key"] for row in service.summary_rows(EngineRequirement())]
    assert not set(keys) & {"mass_flow", "throat_area", "isp", "expansion_ratio"}


# ===========================================================================
# the controller
# ===========================================================================


@pytest.fixture()
def controller(qt_app):
    return EngineRequirementController()


def test_the_controller_starts_from_an_empty_requirement(controller):
    assert controller.requirement() == EngineRequirement()
    assert controller.property("thrustText") == ""
    assert controller.property("isComplete") is False
    assert controller.property("statusLabel") == "2 items to resolve"
    assert controller.property("openDecisions") == [
        "Propellant pair", "Chamber pressure", "O/F", "Feed architecture"]


def test_fields_convert_display_units_to_si(controller):
    controller.setThrust("2500")
    controller.setBurnTime("380")
    assert controller.requirement().thrust == 2.5e6
    assert controller.property("thrustText") == "2500"
    controller.setAmbientPressure("2.5")
    assert controller.requirement().environment.ambient_pressure == 2500.0
    assert controller.property("ambientMode") == "custom"
    controller.setAmbientMode("vacuum")
    assert controller.property("ambientPressureText") == "0"
    assert controller.requirement().environment.custom_pressure == 2500.0   # kept
    assert controller.property("isComplete") is True


def test_unparseable_text_changes_nothing_and_empty_clears(controller):
    controller.setThrust("100")
    controller.setThrust("lots")
    controller.setThrust("inf")
    assert controller.requirement().thrust == 1e5
    controller.setThrust("")
    assert controller.requirement().thrust is None


def test_choosing_a_pair_and_its_reference_ratio(controller):
    controller.setMixtureRatioMode("pair_reference")            # no pair: refused
    assert controller.property("mixtureRatioMode") == "auto"
    controller.setPair("sutton-nto-mmh")
    controller.setMixtureRatioMode("pair_reference")
    assert controller.property("pairLabel") == "Nitrogen tetroxide / MMH"
    assert controller.property("referenceMixtureRatioText") == "2.15"
    assert controller.requirement().mixture_ratio.value is None
    controller.setPair("")                                      # back to Auto
    codes = [issue["code"] for issue in controller.property("issues")]
    assert "MIXTURE_RATIO_REFERENCE_WITHOUT_PAIR" in codes      # reported, not reset


def test_explicit_ratio_and_chamber_pressure(controller):
    controller.setMixtureRatio("3.1")                           # mode is Auto: ignored
    assert controller.requirement().mixture_ratio.value is None
    controller.setMixtureRatioMode("explicit")
    controller.setMixtureRatio("3.1")
    assert controller.requirement().mixture_ratio == MixtureRatioPreference(
        MixtureRatioMode.EXPLICIT, 3.1)
    controller.setChamberPressureMode("upper_limit")
    controller.setChamberPressure("12.5")
    assert controller.requirement().chamber_pressure == ChamberPressurePreference(
        ChamberPressureMode.UPPER_LIMIT, 12.5e6)
    controller.setChamberPressureMode("auto")
    assert controller.requirement().chamber_pressure == ChamberPressurePreference()


def test_feed_and_cycle_stay_consistent_through_the_controller(controller):
    controller.setCycle("expander")                             # not pump-fed: refused
    assert controller.requirement().cycle is None
    assert controller.property("cycleApplicable") is False
    controller.setFeed("pump_fed")
    assert controller.property("cycle") == "auto"
    controller.setCycle("full_flow_staged_combustion")
    assert controller.requirement().cycle is CyclePreference.FULL_FLOW_STAGED_COMBUSTION
    assert "future-modelled intent" in controller.property("cycleNote")
    controller.setFeed("pressure_fed")
    assert controller.requirement().cycle is None and controller.property("cycle") == ""


def test_bad_enumeration_text_changes_nothing(controller):
    before = controller.requirement()
    for slot in ("setFeed", "setCycle", "setAmbientMode", "setPriority",
                 "setChamberPressureMode", "setMixtureRatioMode"):
        getattr(controller, slot)("not-a-member")
    assert controller.requirement() == before


def test_each_edit_emits_one_change_and_a_no_op_emits_none(controller):
    seen = []
    controller.requirementChanged.connect(lambda: seen.append(1))
    controller.setThrust("100")
    controller.setThrust("100")
    controller.setFeed("auto")
    assert seen == [1]


def test_state_round_trips_through_json(controller):
    controller.setName("Booster")
    controller.setThrust("845")
    controller.setBurnTime("162")
    controller.setPair("sutton-o2-rp1")
    controller.setFeed("pump_fed")
    controller.setCycle("gas_generator")
    controller.setPriority("simplicity")
    text = controller.property("stateJson")
    other = EngineRequirementController()
    assert other.loadStateJson(text) is True
    assert other.requirement() == controller.requirement()
    assert other.property("fingerprint") == controller.property("fingerprint")
    assert other.property("message") == "Requirement loaded"


def test_a_malformed_record_changes_nothing(controller):
    controller.setThrust("10")
    before = controller.requirement()
    assert controller.loadStateJson('{"schema": "other"}') is False
    assert controller.loadStateJson("not json") is False
    assert controller.requirement() == before
    assert controller.property("message").startswith("Not loaded")


def test_file_persistence(controller, tmp_path):
    """Files only. The clipboard round trip is proved in the offscreen runtime
    test: here the session's application may be on the real platform, and a
    unit test must not race for -- or overwrite -- the user's clipboard."""
    controller.setThrust("50")
    controller.setFeed("pressure_fed")
    path = tmp_path / "requirement.json"
    assert controller.saveToFile(str(path)) is True
    assert json.loads(path.read_text(encoding="utf-8"))["feed"] == "pressure_fed"
    other = EngineRequirementController()
    assert other.loadFromFile(path.as_uri()) is True             # a QML file URL too
    assert other.requirement() == controller.requirement()
    assert other.loadFromFile(str(tmp_path / "missing.json")) is False


def test_reset_returns_to_the_empty_requirement(controller):
    controller.setThrust("10")
    controller.reset()
    assert controller.requirement() == EngineRequirement()


# ===========================================================================
# boundaries
# ===========================================================================


def _imports(path: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(("." * node.level) + (node.module or ""))
    return names


def test_the_domain_imports_nothing_but_the_standard_library():
    for name in _imports(DOMAIN):
        assert not name.startswith(("rocketforge", ".")), name
        assert name.split(".")[0] not in ("numpy", "PySide6"), name


def test_the_requirement_modules_reach_no_solver_and_no_provider():
    allowed = {"rocketforge.engine.requirement", ".", ".thermochemistry_presets"}
    for path in MODULES:
        for name in _imports(path):
            if name.startswith("rocketforge") or name.startswith("."):
                assert name in allowed, f"{path.name} imports {name}"


def test_the_page_binds_and_computes_nothing():
    code = re.sub(r"/\*.*?\*/|//[^\n]*", " ", PAGE.read_text(encoding="utf-8"), flags=re.S)
    code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', code)          # labels are not code
    assert set(re.findall(r"Math\.([a-zA-Z]+)", code)) <= {"max", "min"}
    for banned in ("Thermochemistry.", "RocketPerformance.", "TradeStudy.",
                   "calculate", "solve", "101325", "1000"):
        assert banned not in code, banned
    singletons = set(re.findall(r"\b([A-Z][A-Za-z0-9]+)\.[a-z]", code))
    assert "EngineRequirement" in singletons
    assert not singletons & {"Thermochemistry", "RocketPerformance", "TradeStudy",
                             "Nozzle", "Line", "FluidProperties"}


def test_the_page_is_reachable_from_the_rail():
    navigation = (ROOT / "ui" / "data" / "Navigation.qml").read_text(encoding="utf-8")
    assert 'key: "requirement"' in navigation and "EngineRequirementPage.qml" in navigation
    families = navigation[navigation.index("readonly property var families:"):]
    assert 'key: "liquidengine"' in families
