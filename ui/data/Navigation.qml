pragma Singleton
import QtQuick

/*
 * Navigation — the application's information architecture.
 *
 * `items` is the flat, ordered list of reachable pages; its index is the page
 * index used by the workspace. `families` is what the rail shows, naming its
 * pages by key, so adding a module means adding one entry to `items`, its key
 * to a family, and one file in pages/.
 */
QtObject {
    readonly property var items: [
        // The workbench overview. Index 0, so Main.qml's default
        // currentPageIndex lands here rather than on a calculator module --
        // the structural-recovery finding that the app previously had no
        // Home at all and opened on legacy IsentropicPage.qml instead.
        { key: "home", label: "Home", page: "HomePage.qml" },
        // `computed` marks a module whose numbers come from the engineering
        // backend rather than from MockData. Absent means a reference page
        // (Home, Equation Library) that solves nothing.
        { key: "isentropic",  label: "Isentropic Flow",  page: "IsentropicPage.qml", computed: true },
        { key: "massflow",    label: "Mass Flow",        page: "MassFlowPage.qml", computed: true },
        { key: "normalshock", label: "Normal Shock",     page: "NormalShockPage.qml", computed: true },
        { key: "obliqueshock",label: "Oblique Shock",    page: "ObliqueShockPage.qml", computed: true },
        { key: "prandtlmeyer",label: "Prandtl–Meyer", page: "PrandtlMeyerPage.qml", computed: true },
        { key: "fanno",       label: "Fanno Flow",       page: "FannoPage.qml", computed: true },
        { key: "rayleigh",    label: "Rayleigh Flow",    page: "RayleighPage.qml", computed: true },
        { key: "nozzlelab",   label: "Nozzle Lab",       page: "NozzleLabPage.qml", computed: true },
        // A reference page: it solves nothing, so its notes say so and the
        // status bar shows them instead of a solver.
        { key: "equations",   label: "Equation Library", page: "EquationLibraryPage.qml",
          solverNote: "Reference relations",
          computedNote: "The relations the compressible-flow modules implement; nothing is solved" },
        // Chemistry. A second analysis domain, not a compressible module: its
        // numbers come from a thermochemistry provider rather than from
        // rocketforge.physics.compressible.
        // `solverNote` overrides the status bar's default wording. It exists
        // because "Verified perfect-gas model" is true of every compressible
        // page and false of this one: these numbers come from a chemical
        // equilibrium provider, not from the frozen perfect-gas model.
        { key: "thermochem",  label: "Thermochemistry",  page: "ThermochemistryPage.qml",
          computed: true, solverNote: "NASA CEA · HP equilibrium provider",
          computedNote: "Solved by the provider, mapped and validated by RocketForge" },
        // Rocket performance. A third analysis domain, and the first one whose
        // numbers RocketForge computes itself from a chamber state a provider
        // supplied. The solver note says so, because "NASA CEA" would be wrong
        // here in both directions: CEA did not compute these, and the chamber
        // state they start from is not RocketForge's.
        { key: "performance", label: "Rocket Performance", page: "RocketPerformancePage.qml",
          computed: true, solverNote: "RocketForge ideal rocket model",
          computedNote: "Computed by RocketForge from a provider chamber state" },
        // Trade study. A decision layer rather than a physics one: it evaluates
        // the accepted thermochemistry and performance stack over a grid and
        // helps a person choose. The solver note says so, because naming a
        // provider here would credit the chemistry library with the ranking.
        { key: "tradestudy", label: "Trade Study", page: "TradeStudyPage.qml",
          computed: true, solverNote: "Design-space evaluation over the accepted stack",
          computedNote: "Evaluated samples, constraints and Pareto analysis" },
        // Fluid properties. The fundamental layer beneath the propellant
        // states everything else starts from: what a substance is doing at a
        // temperature and a pressure. The solver note names the provider
        // because, unlike performance, these numbers are the provider's own.
        { key: "fluidproperties", label: "Fluid Properties", page: "FluidPropertiesPage.qml",
          computed: true, solverNote: "CoolProp reference equations of state",
          computedNote: "Provider property evaluation at an explicit T and p" },
        // Line. The first hydraulic component, and the first consumer of a
        // transport property. The solver note names RocketForge because the
        // friction factor and the pressure drop are this program's own; the
        // density and viscosity behind them are the provider's, which is what
        // the provenance panel is for.
        { key: "line", label: "Line", page: "LinePage.qml",
          computed: true, solverNote: "RocketForge Darcy-Weisbach with Colebrook-White",
          computedNote: "Straight circular liquid line, distributed wall friction only" },
        // Propulsion Database. Evidence, not a calculation: shipped source
        // records read as they are stored. `computed` in this list's own sense
        // -- its numbers come from the backend, not from MockData -- so the
        // status bar shows the page's own notes instead of the mock chips; the
        // notes say the numbers are the sources', and that nothing is solved.
        { key: "evidence", label: "Propulsion Database", page: "PropulsionEvidencePage.qml",
          computed: true, solverNote: "Shipped evidence records, read-only",
          computedNote: "Source values as stored, with their locators; nothing is solved" },
        // Engine Requirement (LIQ-2). Design intent for a liquid engine, not a
        // calculation: `computed` because its content comes from the backend
        // rather than from MockData, and the notes say nothing is solved.
        { key: "requirement", label: "Engine Requirement", page: "EngineRequirementPage.qml",
          computed: true, solverNote: "Design intent only, nothing solved",
          computedNote: "Target, environment and preferences; no sizing or cycle analysis" },
        // Propellant Trade (LIQ-3). Compares catalogue pairs for the current
        // requirement through the accepted chamber and ideal-performance chain;
        // solves only on its explicit Run action. No score, no cycle analysis.
        { key: "propellanttrade", label: "Propellant Trade", page: "PropellantTradePage.qml",
          computed: true, solverNote: "NASA CEA chamber · RocketForge ideal performance",
          computedNote: "Candidate pairs at a stated operating point; no sizing or cycle analysis" },
        // Thrust Chamber Sizing (LIQ-4). Sizes the ideal throat and nozzle exit
        // at the candidate selected in the trade, for a stated Ae/At; solves
        // only on its explicit Size action. No chamber geometry or cycle.
        { key: "chambersizing", label: "Thrust Chamber Sizing", page: "ChamberSizingPage.qml",
          computed: true, solverNote: "NASA CEA chamber · RocketForge ideal performance",
          computedNote: "Ideal throat and exit at the selected operating point; no chamber geometry or cycle" },
        // Combustion Chamber Geometry (LIQ-5). Extends the sized throat upstream
        // to a cylinder + conical convergent from stated L*, Ac/At and
        // half-angle; computes only on its explicit Compute action.
        { key: "chambergeometry", label: "Combustion Chamber Geometry", page: "ChamberGeometryPage.qml",
          computed: true, solverNote: "RocketForge chamber geometry · Sutton §8.2",
          computedNote: "Chamber volume, diameter and lengths from stated L*, Ac/At and half-angle; no injector, cooling or cycle" },
        // Injector & Feed Pressure (LIQ-6). Sizes each branch's total injector
        // orifice from the sized flows and adds its pressure ledger; computes
        // only on its explicit Compute action.
        { key: "injector", label: "Injector & Feed Pressure", page: "InjectorPage.qml",
          computed: true, solverNote: "RocketForge injector hydraulics · Sutton §8.1, §11.5",
          computedNote: "Orifice area, injection velocity and branch pressure ledger; no stability, atomization, pump or cycle" },
        // Propulsion System (SYS gates): what the stage carries and delivers to
        // the engine. Each computes only on its explicit Compute action.
        { key: "propellantinventory", label: "Propellant Inventory", page: "PropellantInventoryPage.qml",
          computed: true, solverNote: "RocketForge propellant inventory · Sutton §6.2, §11.1",
          computedNote: "Usable, residual, reserved and loaded propellant per branch; no tanks or cycle flows" },
        { key: "tankgeometry", label: "Tank Geometry & Packaging", page: "TankGeometryPage.qml",
          computed: true, solverNote: "RocketForge tank geometry · Sutton §6.2",
          computedNote: "Liquid, ullage and tank volume and internal sphere or capsule geometry; no wall, mass or insulation" },
        { key: "propellantmanagement", label: "Propellant Management", page: "PropellantManagementPage.qml",
          computed: true, solverNote: "RocketForge propellant management · Sutton §6.2",
          computedNote: "Management intent, outlet-coverage declaration and liquid/gas volumes; no slosh dynamics" },
        { key: "tankpressurization", label: "Tank Pressurization", page: "TankPressurizationPage.qml",
          computed: true, solverNote: "RocketForge tank pressurization · Sutton §6.4, §6.5",
          computedNote: "Regulated stored gas and blowdown with a perfect gas; autogenous and warm gas are intent only" },
        { key: "feednetwork", label: "Feed Network", page: "FeedNetworkPage.qml",
          computed: true, solverNote: "RocketForge feed network · engineering.line, Sutton Eqs. 11-6, 11-7",
          computedNote: "Series line losses from tank outlet to injector inlet; no cavitation, transients or pumps" },
        // Reference (DB-3A): the shipped reference-engine corpus, read-only.
        { key: "engines", label: "Reference Engines", page: "ReferenceEnginesPage.qml",
          computed: true, solverNote: "Shipped reference-engine records, read-only",
          computedNote: "Values as printed, capabilities, topology and sources; nothing is solved" }
    ]

    // ---- Analysis Experience R2: progressive-disclosure families --------
    // A family is what the narrow rail shows permanently; its groups are
    // what the contextual drawer reveals once that family is active. Group
    // members are named by key and resolved to page indices here, so adding
    // or removing a page never shifts a family. `hasStatus: true` marks a
    // family whose members carry persistent solve state (rendered with
    // RFBrowserItem, two lines); false means the compressible-flow/reference
    // treatment (RFNavItem, one line, no persistent state to show).
    readonly property var families: [
        {
            key: "compressible", label: "Compressible Flow", short: "FLOW", icon: "flow",
            hasStatus: false,
            groups: [
                { label: "Fundamentals", items: keys(["isentropic", "massflow"]) },
                { label: "Wave systems", items: keys(["normalshock", "obliqueshock", "prandtlmeyer"]) },
                { label: "Duct flow", items: keys(["fanno", "rayleigh"]) },
                { label: "Nozzle", items: keys(["nozzlelab"]) }
            ]
        },
        {
            key: "thermochem", label: "Thermochemistry", short: "CHEM", icon: "chem",
            hasStatus: true,
            groups: [ { label: "", items: keys(["thermochem"]) } ]
        },
        {
            key: "propulsion", label: "Rocket Performance", short: "PROP", icon: "prop",
            hasStatus: true,
            groups: [ { label: "", items: keys(["performance"]) } ]
        },
        {
            key: "tradestudy", label: "Trade Study", short: "TRADE", icon: "trade",
            hasStatus: true,
            groups: [ { label: "", items: keys(["tradestudy"]) } ]
        },
        {
            key: "fluids", label: "Fluids and Feed", short: "FLUID", icon: "fluid",
            hasStatus: true,
            groups: [ { label: "", items: keys(["fluidproperties", "line"]) } ]
        },
        {
            // The liquid engine being designed, starting from what is wanted
            // of it. No persistent solve state: a requirement is not a result.
            key: "liquidengine", label: "Liquid Engine", short: "ENG", icon: "target",
            hasStatus: false,
            groups: [ { label: "", items: keys(["requirement", "propellanttrade", "chambersizing",
                                                 "chambergeometry", "injector"]) } ]
        },
        {
            // The stage around the engine: inventory, tanks, propellant
            // management, pressurization and feed lines (SYS gates).
            key: "propulsionsystem", label: "Propulsion System", short: "SYS", icon: "tank",
            hasStatus: false,
            groups: [ { label: "", items: keys(["propellantinventory", "tankgeometry", "propellantmanagement",
                                                 "tankpressurization", "feednetwork"]) } ]
        },
        {
            key: "reference", label: "Reference", short: "REF", icon: "reference",
            hasStatus: false,
            groups: [ { label: "", items: keys(["equations", "evidence", "engines"]) } ]
        }
    ]

    // The one item a single-module family opens directly, or -1 for a
    // family whose rail click must open the contextual drawer instead.
    function directTargetOf(family) {
        var total = 0
        for (var g = 0; g < family.groups.length; ++g)
            total += family.groups[g].items.length
        if (total !== 1)
            return -1
        return family.groups[0].items[0]
    }

    // Which family owns a given page index, for the rail's own current-
    // family highlight. Returns -1 for Home (index 0), which is not a
    // member of any family.
    function familyOfIndex(index) {
        for (var f = 0; f < families.length; ++f) {
            var groups = families[f].groups
            for (var g = 0; g < groups.length; ++g)
                if (groups[g].items.indexOf(index) !== -1)
                    return f
        }
        return -1
    }

    // The page an issue code points at, for the issue codes that mean "an
    // upstream page has not been solved, is stale, was refused, or does not
    // match": in every case the fix is on that page. The backend's message
    // names the same page or its study; tests/application/test_issue_links.py
    // checks that the two agree. A code that is not here has no link.
    readonly property var upstreamPageOfIssue: ({
        "REQUIREMENT_INCOMPLETE": "requirement",
        "BURN_TIME_UNRESOLVED": "requirement",
        "NO_TRADE": "propellanttrade",
        "TRADE_STALE": "propellanttrade",
        "TRADE_MISMATCH": "propellanttrade",
        "NO_SELECTION": "propellanttrade",
        "SELECTION_FAILED": "propellanttrade",
        "SELECTION_INCOMPLETE": "propellanttrade",
        "NO_SIZING": "chambersizing",
        "SIZING_STALE": "chambersizing",
        "SIZING_REFUSED": "chambersizing",
        "SIZING_INCOMPLETE": "chambersizing",
        "REQUIREMENT_MISMATCH": "chambersizing",
        "NO_INJECTOR": "injector",
        "INJECTOR_STALE": "injector",
        "INJECTOR_REFUSED": "injector",
        "INJECTOR_MISMATCH": "injector",
        "NO_INVENTORY": "propellantinventory",
        "INVENTORY_INCOMPLETE": "propellantinventory",
        "INVENTORY_STALE": "propellantinventory",
        "INVENTORY_REFUSED": "propellantinventory",
        "NO_TANKS": "tankgeometry",
        "TANKS_STALE": "tankgeometry",
        "TANKS_REFUSED": "tankgeometry",
        "TANKS_MISMATCH": "tankgeometry",
        "NO_MANAGEMENT": "propellantmanagement",
        "MANAGEMENT_STALE": "propellantmanagement",
        "MANAGEMENT_REFUSED": "propellantmanagement",
        "NO_PRESSURIZATION": "tankpressurization",
        "PRESSURIZATION_STALE": "tankpressurization",
        "PRESSURIZATION_REFUSED": "tankpressurization"
    })

    function upstreamPageOf(code) {
        var key = upstreamPageOfIssue[code]
        return key === undefined ? -1 : indexOfKey(key)
    }

    // Page indices of the given keys, in order. A key that names no page is a
    // programming error, so it fails loudly instead of yielding -1.
    function keys(list) {
        var out = []
        for (var i = 0; i < list.length; ++i) {
            var index = indexOfKey(list[i])
            if (index < 0)
                throw new Error("Navigation: no page with key " + list[i])
            out.push(index)
        }
        return out
    }

    function indexOfKey(key) {
        for (var i = 0; i < items.length; ++i) {
            if (items[i].key === key)
                return i
        }
        return -1
    }

    function pageSource(index) {
        if (index < 0 || index >= items.length)
            return ""
        return items[index].page
    }
}
