pragma Singleton
import QtQuick

/*
 * Navigation — the application's information architecture.
 *
 * `items` is the flat, ordered list of reachable pages; its index is the page
 * index used by the workspace.  `flowRows` is the render list for the sidebar
 * (group headings interleaved with item references), so adding a module means
 * adding one entry to each list and one file in pages/.
 */
QtObject {
    readonly property var items: [
        // `computed` marks a module whose numbers come from the engineering
        // backend rather than from MockData. Absent means not yet connected.
        { key: "isentropic",  label: "Isentropic Flow",  page: "IsentropicPage.qml", computed: true },
        { key: "massflow",    label: "Mass Flow",        page: "MassFlowPage.qml", computed: true },
        { key: "normalshock", label: "Normal Shock",     page: "NormalShockPage.qml", computed: true },
        { key: "obliqueshock",label: "Oblique Shock",    page: "ObliqueShockPage.qml", computed: true },
        { key: "prandtlmeyer",label: "Prandtl–Meyer", page: "PrandtlMeyerPage.qml", computed: true },
        { key: "fanno",       label: "Fanno Flow",       page: "FannoPage.qml", computed: true },
        { key: "rayleigh",    label: "Rayleigh Flow",    page: "RayleighPage.qml", computed: true },
        { key: "nozzlelab",   label: "Nozzle Lab",       page: "NozzleLabPage.qml", computed: true },
        { key: "compare",     label: "Compare",          page: "ComparePage.qml" },
        { key: "charts",      label: "Charts",           page: "ChartsPage.qml" },
        { key: "equations",   label: "Equation Library", page: "EquationLibraryPage.qml" },
        { key: "gases",       label: "Gas Properties",   page: "GasPropertiesPage.qml" },
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
          computedNote: "Straight circular liquid line, distributed wall friction only" }
    ]

    readonly property string flowDomain: "COMPRESSIBLE FLOW"

    readonly property var flowRows: [
        { kind: "group", label: "Fundamentals" },
        { kind: "item",  index: 0 },
        { kind: "item",  index: 1 },
        { kind: "group", label: "Wave systems" },
        { kind: "item",  index: 2 },
        { kind: "item",  index: 3 },
        { kind: "item",  index: 4 },
        { kind: "group", label: "Duct flow" },
        { kind: "item",  index: 5 },
        { kind: "item",  index: 6 },
        { kind: "group", label: "Applications" },
        { kind: "item",  index: 7 },
        { kind: "group", label: "Analysis" },
        { kind: "item",  index: 8 },
        { kind: "item",  index: 9 },
        { kind: "group", label: "Reference" },
        { kind: "item",  index: 10 },
        { kind: "item",  index: 11 }
    ]

    // The second analysis domain. One workspace with four views of one
    // chamber-equilibrium result, so it is a single navigation entry rather
    // than a group of pages.
    readonly property string chemistryDomain: "THERMOCHEMISTRY"

    readonly property var chemistryRows: [
        { kind: "item", index: 12 }
    ]

    // The third analysis domain. Separate from THERMOCHEMISTRY because it is a
    // different question answered by a different owner: chemistry states what
    // the products are, and this states what a nozzle does with them.
    readonly property string performanceDomain: "ROCKET PERFORMANCE"

    readonly property var performanceRows: [
        { kind: "item", index: 13 }
    ]

    // The fourth analysis domain, and the only one that computes no physics.
    // Separate from the three below it because it consumes them rather than
    // extending any one of them.
    readonly property string studyDomain: "TRADE STUDY"

    readonly property var studyRows: [
        { kind: "item", index: 14 }
    ]

    // Fluid properties. Its own domain rather than a member of another,
    // because it sits *beneath* the others: thermochemistry, performance and
    // trade study all start from a propellant state, and this is what a
    // propellant state is made of.
    readonly property string fluidDomain: "FLUIDS AND FEED"

    readonly property var fluidRows: [
        { kind: "item", index: 15 },
        { kind: "item", index: 16 }
    ]

    // Fifth domain of the product.  Present in the architecture, deliberately
    // inert until the engine modules are built. "Performance" is no longer
    // listed here: it exists, so advertising it as planned would be wrong.
    readonly property string engineDomain: "ROCKET ENGINE"
    readonly property var engineItems: [
        "Chamber", "Nozzle Contour", "Cooling", "Feed System", "Engine Cycles"
    ]

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
