pragma Singleton
import QtQuick
import "../../theme"

/*
 * ComponentRegistry - what kinds of physical components exist.
 *
 * This is the extension point of the whole engine workspace: adding a new
 * component type (heat exchanger, throttle valve, tank pressurisation set) is
 * one entry in `types` plus one glyph, with no change to the palette, the
 * canvas, the node renderer or the inspector.
 *
 * The registry describes *editor* metadata only - display name, category,
 * glyph, node geometry, port topology and the placeholder readout rows. It
 * holds no engineering behaviour, and nothing here computes anything. The
 * numbers in `readout` are static placeholders; quantities that will need a
 * solver are written as an em dash so the interface never implies a result it
 * does not have.
 */
QtObject {
    id: registry

    // ---- node geometry ---------------------------------------------------
    // Node size is registry-owned so that the canvas, the node item and the
    // connection router all derive port positions from one source.
    //
    // Two densities, because the same canvas has to serve two jobs. `normal` is
    // the working size: the name, the type and a couple of quantities are meant
    // to be read without leaning in. `compact` drops to the identity strip
    // alone and is what makes a forty-component architecture legible at once.
    readonly property real nodeWidth: 188
    readonly property real compactWidth: 164
    readonly property real headerHeight: 41
    readonly property real compactHeaderHeight: 34
    readonly property real rowHeight: 19
    readonly property real bodyPadding: 10

    // The mark is small so the canvas stays quiet; the target is not.
    readonly property real portShapeSize: 10
    readonly property real portHitSize: 26
    readonly property real portHitRadius: 15

    readonly property var categories: [
        // `label` names the group in the palette, where the user is shopping for
        // a part; `subsystem` names it in the project tree, where the same group
        // is a region of the engine.
        { id: "fluid",      label: "Fluid / feed",  subsystem: "Feed System" },
        { id: "combustion", label: "Combustion",    subsystem: "Combustion" },
        { id: "expansion",  label: "Expansion",     subsystem: "Expansion" },
        { id: "power",      label: "Power / cycle", subsystem: "Power System" },
        { id: "thermal",    label: "Thermal",       subsystem: "Thermal" }
    ]

    // ---- component catalogue --------------------------------------------
    readonly property var types: [
        {
            type: "tank", displayName: "Tank", category: "fluid", glyph: "tank",
            defaultName: "Tank", subtitle: "Propellant", workspace: "placeholder",
            readout: [
                { label: "P", value: "4.20", unit: "MPa" },
                { label: "T", value: "92", unit: "K" }
            ],
            ports: [
                { id: "out", label: "Outlet", type: "fluid", direction: "out",
                  subtype: "propellant", side: "right" }
            ]
        },
        {
            type: "pump", displayName: "Pump", category: "fluid", glyph: "pump",
            defaultName: "Pump", subtitle: "Centrifugal", workspace: "placeholder",
            readout: [
                { label: "Δp", value: "8.40", unit: "MPa" },
                { label: "η", value: "0.71", unit: "" }
            ],
            ports: [
                { id: "in", label: "Inlet", type: "fluid", direction: "in",
                  subtype: "propellant", side: "left", required: true },
                { id: "out", label: "Outlet", type: "fluid", direction: "out",
                  subtype: "propellant", side: "right" },
                { id: "drive", label: "Drive", type: "mechanical", direction: "in",
                  subtype: "shaft", side: "top", required: true }
            ]
        },
        {
            type: "valve", displayName: "Valve", category: "fluid", glyph: "valve",
            defaultName: "Valve", subtitle: "Shut-off", workspace: "placeholder",
            readout: [
                { label: "Cv", value: "12.5", unit: "" },
                { label: "State", value: "Open", unit: "" }
            ],
            ports: [
                { id: "in", label: "Inlet", type: "fluid", direction: "in",
                  subtype: "propellant", side: "left", required: true },
                { id: "out", label: "Outlet", type: "fluid", direction: "out",
                  subtype: "propellant", side: "right" }
            ]
        },
        {
            type: "regulator", displayName: "Regulator", category: "fluid", glyph: "regulator",
            defaultName: "Regulator", subtitle: "Dome loaded", workspace: "placeholder",
            readout: [
                { label: "p set", value: "5.60", unit: "MPa" }
            ],
            ports: [
                { id: "in", label: "Inlet", type: "fluid", direction: "in",
                  subtype: "pressurant", side: "left", required: true },
                { id: "out", label: "Outlet", type: "fluid", direction: "out",
                  subtype: "pressurant", side: "right" }
            ]
        },
        {
            type: "orifice", displayName: "Orifice", category: "fluid", glyph: "orifice",
            defaultName: "Orifice", subtitle: "Fixed", workspace: "placeholder",
            readout: [
                { label: "d", value: "3.20", unit: "mm" }
            ],
            ports: [
                { id: "in", label: "Inlet", type: "fluid", direction: "in",
                  subtype: "propellant", side: "left", required: true },
                { id: "out", label: "Outlet", type: "fluid", direction: "out",
                  subtype: "propellant", side: "right" }
            ]
        },
        {
            type: "injector", displayName: "Injector", category: "combustion", glyph: "injector",
            defaultName: "Injector", subtitle: "Pintle", workspace: "injector",
            readout: [
                { label: "Type", value: "Pintle", unit: "" },
                { label: "Δp", value: "—", unit: "" }
            ],
            ports: [
                { id: "fuel", label: "Fuel inlet", type: "fluid", direction: "in",
                  subtype: "fuel", side: "left", required: true },
                { id: "ox", label: "Oxidiser inlet", type: "fluid", direction: "in",
                  subtype: "oxidiser", side: "left", required: true },
                { id: "out", label: "Face outlet", type: "fluid", direction: "out",
                  subtype: "mixture", side: "right" }
            ]
        },
        {
            type: "chamber", displayName: "Combustion Chamber", category: "combustion", glyph: "chamber",
            defaultName: "Chamber", subtitle: "Regen cooled", workspace: "placeholder",
            readout: [
                { label: "pc", value: "—", unit: "" },
                { label: "L*", value: "—", unit: "" }
            ],
            ports: [
                { id: "in", label: "Mixture inlet", type: "fluid", direction: "in",
                  subtype: "mixture", side: "left", required: true },
                { id: "out", label: "Gas outlet", type: "fluid", direction: "out",
                  subtype: "hot gas", side: "right" },
                { id: "heat", label: "Wall heat load", type: "thermal", direction: "out",
                  subtype: "wall", side: "bottom" }
            ]
        },
        {
            type: "igniter", displayName: "Igniter", category: "combustion", glyph: "igniter",
            defaultName: "Igniter", subtitle: "Torch", workspace: "placeholder",
            readout: [
                { label: "Mode", value: "Torch", unit: "" }
            ],
            ports: [
                { id: "out", label: "Torch outlet", type: "fluid", direction: "out",
                  subtype: "hot gas", side: "right" }
            ]
        },
        {
            type: "nozzle", displayName: "Nozzle", category: "expansion", glyph: "nozzle",
            defaultName: "Nozzle", subtitle: "Bell", workspace: "nozzle",
            readout: [
                { label: "ε", value: "12.40", unit: "" },
                { label: "pe", value: "—", unit: "" }
            ],
            ports: [
                { id: "in", label: "Gas inlet", type: "fluid", direction: "in",
                  subtype: "hot gas", side: "left", required: true },
                { id: "heat", label: "Wall heat load", type: "thermal", direction: "in",
                  subtype: "wall", side: "bottom" }
            ]
        },
        {
            type: "turbine", displayName: "Turbine", category: "power", glyph: "turbine",
            defaultName: "Turbine", subtitle: "Single stage", workspace: "placeholder",
            readout: [
                { label: "PR", value: "1.85", unit: "" },
                { label: "P", value: "—", unit: "" }
            ],
            ports: [
                { id: "in", label: "Gas inlet", type: "fluid", direction: "in",
                  subtype: "hot gas", side: "left", required: true },
                { id: "out", label: "Exhaust", type: "fluid", direction: "out",
                  subtype: "exhaust", side: "right" },
                { id: "drive", label: "Shaft power", type: "mechanical", direction: "out",
                  subtype: "shaft", side: "top" }
            ]
        },
        {
            type: "shaft", displayName: "Shaft", category: "power", glyph: "shaft",
            defaultName: "Shaft", subtitle: "Direct drive", workspace: "placeholder",
            readout: [
                { label: "N", value: "36 000", unit: "rpm" }
            ],
            ports: [
                { id: "in", label: "Power in", type: "mechanical", direction: "in",
                  subtype: "shaft", side: "left", required: true },
                { id: "out", label: "Power out", type: "mechanical", direction: "out",
                  subtype: "shaft", side: "right" }
            ]
        },
        {
            type: "gasgenerator", displayName: "Gas Generator", category: "power", glyph: "gasgenerator",
            defaultName: "Gas Generator", subtitle: "Fuel rich", workspace: "placeholder",
            readout: [
                { label: "MR", value: "0.35", unit: "" },
                { label: "Tg", value: "900", unit: "K" }
            ],
            ports: [
                { id: "fuel", label: "Fuel inlet", type: "fluid", direction: "in",
                  subtype: "fuel", side: "left", required: true },
                { id: "ox", label: "Oxidiser inlet", type: "fluid", direction: "in",
                  subtype: "oxidiser", side: "left", required: true },
                { id: "out", label: "Gas outlet", type: "fluid", direction: "out",
                  subtype: "hot gas", side: "right" }
            ]
        },
        {
            type: "preburner", displayName: "Preburner", category: "power", glyph: "preburner",
            defaultName: "Preburner", subtitle: "Ox rich", workspace: "placeholder",
            readout: [
                { label: "MR", value: "0.60", unit: "" },
                { label: "Tg", value: "780", unit: "K" }
            ],
            ports: [
                { id: "fuel", label: "Fuel inlet", type: "fluid", direction: "in",
                  subtype: "fuel", side: "left", required: true },
                { id: "ox", label: "Oxidiser inlet", type: "fluid", direction: "in",
                  subtype: "oxidiser", side: "left", required: true },
                { id: "out", label: "Gas outlet", type: "fluid", direction: "out",
                  subtype: "hot gas", side: "right" }
            ]
        },
        {
            type: "coolingjacket", displayName: "Cooling Jacket", category: "thermal", glyph: "coolingjacket",
            defaultName: "Cooling Jacket", subtitle: "Milled channel", workspace: "placeholder",
            readout: [
                { label: "Channels", value: "120", unit: "" },
                { label: "Δp", value: "—", unit: "" }
            ],
            ports: [
                { id: "in", label: "Coolant inlet", type: "fluid", direction: "in",
                  subtype: "coolant", side: "left", required: true },
                { id: "out", label: "Coolant outlet", type: "fluid", direction: "out",
                  subtype: "coolant", side: "right" },
                { id: "heat", label: "Heat load", type: "thermal", direction: "in",
                  subtype: "wall", side: "bottom" }
            ]
        },
        {
            type: "heatexchanger", displayName: "Heat Exchanger", category: "thermal", glyph: "heatexchanger",
            defaultName: "Heat Exchanger", subtitle: "Counter flow", workspace: "placeholder",
            readout: [
                { label: "Q", value: "—", unit: "" }
            ],
            ports: [
                { id: "hotin", label: "Hot inlet", type: "fluid", direction: "in",
                  subtype: "hot gas", side: "left", required: true },
                { id: "coldin", label: "Cold inlet", type: "fluid", direction: "in",
                  subtype: "coolant", side: "left", required: true },
                { id: "hotout", label: "Hot outlet", type: "fluid", direction: "out",
                  subtype: "hot gas", side: "right" },
                { id: "coldout", label: "Cold outlet", type: "fluid", direction: "out",
                  subtype: "coolant", side: "right" }
            ]
        },
        {
            type: "filmcooling", displayName: "Film Cooling", category: "thermal", glyph: "filmcooling",
            defaultName: "Film Cooling", subtitle: "Wall film", workspace: "placeholder",
            readout: [
                { label: "Fraction", value: "3.0", unit: "%" }
            ],
            ports: [
                { id: "in", label: "Coolant inlet", type: "fluid", direction: "in",
                  subtype: "coolant", side: "left", required: true },
                { id: "heat", label: "Wall relief", type: "thermal", direction: "out",
                  subtype: "wall", side: "bottom" }
            ]
        }
    ]

    // ---- lookups ---------------------------------------------------------

    function definition(type) {
        for (var i = 0; i < types.length; ++i) {
            if (types[i].type === type)
                return types[i]
        }
        return null
    }

    function displayName(type) {
        var def = definition(type)
        return def ? def.displayName : type
    }

    function glyphFor(type) {
        var def = definition(type)
        return def ? def.glyph : ""
    }

    function typesInCategory(categoryId) {
        return types.filter(function (t) { return t.category === categoryId })
    }

    function categoryLabel(categoryId) {
        for (var i = 0; i < categories.length; ++i) {
            if (categories[i].id === categoryId)
                return categories[i].label
        }
        return categoryId
    }

    function subsystemLabel(categoryId) {
        for (var i = 0; i < categories.length; ++i) {
            if (categories[i].id === categoryId)
                return categories[i].subsystem
        }
        return categoryId
    }

    function categoryOf(type) {
        var def = definition(type)
        return def ? def.category : ""
    }

    function ports(type) {
        var def = definition(type)
        return def ? def.ports : []
    }

    function port(type, portId) {
        var list = ports(type)
        for (var i = 0; i < list.length; ++i) {
            if (list[i].id === portId)
                return list[i]
        }
        return null
    }

    // ---- geometry --------------------------------------------------------

    function headerHeightFor(detail) {
        return detail === "compact" ? compactHeaderHeight : headerHeight
    }

    function nodeSize(type, detail) {
        if (detail === "compact")
            return { width: compactWidth, height: compactHeaderHeight }
        var def = definition(type)
        if (!def)
            return { width: nodeWidth, height: headerHeight }
        var rows = def.readout ? def.readout.length : 0
        var body = rows > 0 ? bodyPadding * 2 + rows * rowHeight : 0
        return { width: nodeWidth, height: headerHeight + body }
    }

    /* Port offset inside a node, in node-local coordinates.
     * Inlets sit on the left and outlets on the right so that flow reads left
     * to right; mechanical drive enters from the top and thermal interfaces
     * leave from the bottom. That convention is what makes a cycle legible at
     * a glance, so it lives here rather than in each node. */
    function portOffset(type, portId, detail) {
        var size = nodeSize(type, detail)
        var list = ports(type)
        var side = "left"
        var sameSide = []
        var i
        for (i = 0; i < list.length; ++i) {
            if (list[i].id === portId)
                side = list[i].side
        }
        for (i = 0; i < list.length; ++i) {
            if (list[i].side === side)
                sameSide.push(list[i].id)
        }
        var index = Math.max(0, sameSide.indexOf(portId))
        var fraction = (index + 1) / (sameSide.length + 1)

        /* Side ports hang off the body in normal density, which keeps them clear
         * of the name. A compact node has no body, so they spread over its whole
         * height instead - otherwise every one of them lands on the corner. */
        var top = detail === "compact" ? 0 : headerHeight

        if (side === "left")
            return { x: 0, y: top + (size.height - top) * fraction }
        if (side === "right")
            return { x: size.width, y: top + (size.height - top) * fraction }
        if (side === "top")
            return { x: size.width * fraction, y: 0 }
        return { x: size.width * fraction, y: size.height }
    }

    // ---- port presentation ----------------------------------------------

    function portTypeLabel(portType) {
        switch (portType) {
        case "fluid": return "Fluid"
        case "mechanical": return "Mechanical"
        case "thermal": return "Thermal"
        case "signal": return "Signal"
        }
        return portType
    }

    /* Fluid subtypes get a desaturated tint so that a fuel line and an
     * oxidiser line can be told apart at a glance. The tint is secondary
     * information: port *type* is always carried by shape as well. */
    function subtypeColor(subtype) {
        switch (subtype) {
        case "fuel":       return Theme.series[3]
        case "oxidiser":   return Theme.series[0]
        case "coolant":    return Theme.series[4]
        case "hot gas":    return Theme.series[5]
        case "mixture":    return Theme.series[2]
        case "exhaust":    return Theme.series[6]
        case "pressurant": return Theme.series[6]
        case "propellant": return Theme.textSecondary
        case "shaft":      return Theme.series[2]
        case "wall":       return Theme.series[5]
        }
        return Theme.textMuted
    }
}
