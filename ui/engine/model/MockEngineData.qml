pragma Singleton
import QtQuick

/*
 * MockEngineData - every fixed string and number the engine workspace shows.
 *
 * Same policy as the analysis side of the application: nothing here is
 * computed, nothing is physically authoritative, and quantities that will one
 * day come from a solver are written as an em dash rather than invented. This
 * file is the seam a real configuration layer replaces.
 */
QtObject {
    // =====================================================================
    // demo architecture (gas-generator feed system, drawn by hand)
    // =====================================================================
    readonly property var demoEngine: {
        "engineName": "Engine-01",
        "architecture": "Gas generator",
        "propellants": "LOX / CH₄",
        "environment": "Vacuum",
        "nodes": [
            { key: "fuelTank", type: "tank", name: "Fuel Tank", x: 20, y: 40,
              subtitle: "CH₄",
              readout: [ { label: "P", value: "—", unit: "MPa" },
                         { label: "T", value: "—", unit: "K" } ] },
            { key: "fuelPump", type: "pump", name: "Fuel Pump", x: 232, y: 40,
              subtitle: "Centrifugal",
              readout: [ { label: "Δp", value: "—", unit: "MPa" },
                         { label: "η", value: "—", unit: "" } ] },
            { key: "oxTank", type: "tank", name: "Oxidiser Tank", x: 20, y: 296,
              subtitle: "LOX",
              readout: [ { label: "P", value: "—", unit: "MPa" },
                         { label: "T", value: "—", unit: "K" } ] },
            { key: "oxPump", type: "pump", name: "Oxidiser Pump", x: 232, y: 296,
              subtitle: "Centrifugal",
              readout: [ { label: "Δp", value: "—", unit: "MPa" },
                         { label: "η", value: "—", unit: "" } ] },
            { key: "injector", type: "injector", name: "Main Injector", x: 452, y: 164,
              subtitle: "Pintle",
              readout: [ { label: "Type", value: "Pintle", unit: "" },
                         { label: "Δp", value: "—", unit: "" } ] },
            { key: "chamber", type: "chamber", name: "Main Chamber", x: 664, y: 164,
              subtitle: "Regen cooled",
              readout: [ { label: "pc", value: "—", unit: "" },
                         { label: "L*", value: "—", unit: "" } ] },
            { key: "nozzle", type: "nozzle", name: "Main Nozzle", x: 876, y: 164,
              subtitle: "Bell",
              readout: [ { label: "ε", value: "—", unit: "" },
                         { label: "pe", value: "—", unit: "" } ] }
        ],
        "connections": [
            { from: "fuelTank", fromPort: "out", to: "fuelPump", toPort: "in" },
            { from: "fuelPump", fromPort: "out", to: "injector", toPort: "fuel" },
            { from: "oxTank", fromPort: "out", to: "oxPump", toPort: "in" },
            { from: "oxPump", fromPort: "out", to: "injector", toPort: "ox" },
            { from: "injector", fromPort: "out", to: "chamber", toPort: "in" },
            { from: "chamber", fromPort: "out", to: "nozzle", toPort: "in" }
        ]
    }

    // =====================================================================
    // project tree - the static scaffolding around the live component list
    // =====================================================================
    readonly property var cycleGroups: [
        "Fuel Feed", "Oxidiser Feed", "Power System", "Combustion", "Expansion"
    ]
    readonly property var studies: [
        "Nominal Case", "Sea-Level Case"
    ]

    // =====================================================================
    // engine overview (shown when nothing is selected)
    // =====================================================================
    readonly property string configurationState: "Incomplete"

    // =====================================================================
    // injector workspace
    // =====================================================================
    readonly property var injectorTabs: ["Overview", "Elements", "Hydraulics", "Geometry", "Pattern"]
    readonly property var injectorInputs: [
        { kind: "choice", label: "Element type", value: "Pintle",
          options: ["Pintle", "Coaxial swirl", "Impinging", "Showerhead"] },
        { kind: "number", label: "Pintle diameter", value: "38.00", unit: "mm", step: 0.5 },
        { kind: "number", label: "Fuel annulus gap", value: "1.150", unit: "mm", step: 0.01 },
        { kind: "number", label: "Oxidiser slot count", value: "24", unit: "", step: 1 },
        { kind: "number", label: "Slot width", value: "2.400", unit: "mm", step: 0.05 }
    ]
    readonly property var injectorSummary: [
        { label: "Δp fuel", value: "—", unit: "" },
        { label: "Δp ox", value: "—", unit: "" },
        { label: "Momentum ratio", value: "—", unit: "" },
        { label: "Cd fuel", value: "—", unit: "" },
        { label: "Cd ox", value: "—", unit: "" }
    ]
    readonly property string injectorNote:
        "Element sizing, discharge behaviour and pressure drop arrive with the injector " +
        "module. The geometry below is drawn from the fixed inputs on the left; nothing " +
        "on this page is evaluated."

    // =====================================================================
    // nozzle workspace
    // =====================================================================
    readonly property var nozzleTabs: ["Overview", "Performance", "Contour", "Flow", "Off-Design", "Thermal"]
    readonly property var nozzleInputs: [
        { kind: "choice", label: "Contour type", value: "Bell (80 %)",
          options: ["Bell (80 %)", "Bell (90 %)", "Conical 15°", "Aerospike (planned)"] },
        { kind: "number", label: "Area ratio  ε", value: "12.400", unit: "", step: 0.1 },
        { kind: "number", label: "Throat diameter", value: "120.00", unit: "mm", step: 1 },
        { kind: "number", label: "Divergence half-angle", value: "15.00", unit: "deg", step: 0.5 }
    ]
    readonly property var nozzleSummary: [
        { label: "Exit diameter", value: "—", unit: "mm" },
        { label: "Length", value: "—", unit: "" },
        { label: "Exit Mach", value: "—", unit: "" },
        { label: "Exit pressure", value: "—", unit: "" },
        { label: "Thrust coefficient", value: "—", unit: "" }
    ]
    readonly property string nozzleNote:
        "Contour generation and performance come from the nozzle module. The station " +
        "geometry below is the same hand-authored profile the Nozzle Lab draws."

    // =====================================================================
    // cycle templates for the new-engine dialog
    // =====================================================================
    readonly property var cycleTemplates: [
        {
            id: "pressure-fed", name: "Pressure-Fed",
            description: "Tank pressure feeds the injector directly. No turbomachinery.",
            boxes: [ { label: "F tank", col: 0, row: 0 }, { label: "O tank", col: 0, row: 1 },
                     { label: "Inj", col: 1, row: 0.5 }, { label: "Cc", col: 2, row: 0.5 },
                     { label: "Noz", col: 3, row: 0.5 } ],
            links: [ [0, 2], [1, 2], [2, 3], [3, 4] ]
        },
        {
            id: "gas-generator", name: "Gas Generator",
            description: "A small gas generator drives the turbopump and exhausts overboard.",
            boxes: [ { label: "F tank", col: 0, row: 0 }, { label: "O tank", col: 0, row: 1.6 },
                     { label: "Pump", col: 1, row: 0 }, { label: "Pump", col: 1, row: 1.6 },
                     { label: "GG", col: 1.9, row: 2.5 }, { label: "Turb", col: 2.8, row: 2.5 },
                     { label: "Inj", col: 2, row: 0.8 }, { label: "Cc", col: 2.9, row: 0.8 },
                     { label: "Noz", col: 3.8, row: 0.8 } ],
            links: [ [0, 2], [1, 3], [2, 6], [3, 6], [6, 7], [7, 8], [2, 4], [3, 4], [4, 5] ]
        },
        {
            id: "expander", name: "Expander",
            description: "Fuel heated in the cooling jacket drives the turbine before injection.",
            boxes: [ { label: "F tank", col: 0, row: 0 }, { label: "O tank", col: 0, row: 1.6 },
                     { label: "Pump", col: 1, row: 0 }, { label: "Pump", col: 1, row: 1.6 },
                     { label: "Jkt", col: 1.9, row: 0 }, { label: "Turb", col: 2.8, row: 0 },
                     { label: "Inj", col: 2.4, row: 1.6 }, { label: "Cc", col: 3.3, row: 1.6 },
                     { label: "Noz", col: 4.2, row: 1.6 } ],
            links: [ [0, 2], [1, 3], [2, 4], [4, 5], [5, 6], [3, 6], [6, 7], [7, 8] ]
        },
        {
            id: "staged", name: "Staged Combustion",
            description: "A fuel-rich preburner drives the turbine; its exhaust is burned in the chamber.",
            boxes: [ { label: "F tank", col: 0, row: 0 }, { label: "O tank", col: 0, row: 1.6 },
                     { label: "Pump", col: 1, row: 0 }, { label: "Pump", col: 1, row: 1.6 },
                     { label: "PB", col: 1.9, row: 0.4 }, { label: "Turb", col: 2.7, row: 0.4 },
                     { label: "Inj", col: 3.4, row: 1.1 }, { label: "Cc", col: 4.2, row: 1.1 },
                     { label: "Noz", col: 5, row: 1.1 } ],
            links: [ [0, 2], [1, 3], [2, 4], [3, 4], [4, 5], [5, 6], [3, 6], [6, 7], [7, 8] ]
        },
        {
            id: "full-flow", name: "Full-Flow Staged",
            description: "Two preburners drive separate turbopumps; both streams enter the chamber.",
            boxes: [ { label: "F tank", col: 0, row: 0 }, { label: "O tank", col: 0, row: 2 },
                     { label: "Pump", col: 1, row: 0 }, { label: "Pump", col: 1, row: 2 },
                     { label: "PB f", col: 1.9, row: 0 }, { label: "PB o", col: 1.9, row: 2 },
                     { label: "Trb", col: 2.7, row: 0 }, { label: "Trb", col: 2.7, row: 2 },
                     { label: "Inj", col: 3.5, row: 1 }, { label: "Cc", col: 4.3, row: 1 },
                     { label: "Noz", col: 5.1, row: 1 } ],
            links: [ [0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 8], [8, 9], [9, 10] ]
        },
        {
            id: "custom", name: "Custom",
            description: "Start from an empty canvas and place components yourself.",
            boxes: [],
            links: []
        }
    ]

    // =====================================================================
    // command palette entries
    // =====================================================================
    readonly property var commands: [
        { id: "engine.demo",      label: "Load demo engine",          group: "Engine" },
        { id: "engine.new",       label: "New engine…",               group: "Engine" },
        { id: "engine.fit",       label: "Fit engine layout to view", group: "Engine" },
        { id: "engine.fitselection", label: "Fit selection to view",   group: "Engine" },
        { id: "engine.problems",  label: "Show problems panel",       group: "Engine" },
        { id: "view.focus",       label: "Focus workspace",           group: "View" },
        { id: "view.project",     label: "Toggle project panel",      group: "View" },
        { id: "view.inspector",   label: "Toggle inspector",          group: "View" },
        { id: "add.tank",         label: "Add component: Tank",       group: "Components" },
        { id: "add.pump",         label: "Add component: Pump",       group: "Components" },
        { id: "add.injector",     label: "Add component: Injector",   group: "Components" },
        { id: "add.chamber",      label: "Add component: Chamber",    group: "Components" },
        { id: "add.nozzle",       label: "Add component: Nozzle",     group: "Components" },
        { id: "open.layout",      label: "Open Engine Layout",        group: "Workspaces" },
        { id: "mode.analysis",    label: "Switch to Analysis mode",   group: "Workspaces" },
        { id: "page.isentropic",  label: "Open Isentropic Flow",      group: "Analysis" },
        { id: "page.nozzlelab",   label: "Open Nozzle Lab",           group: "Analysis" },
        { id: "page.equations",   label: "Open Equation Library",     group: "Analysis" }
    ]
}
