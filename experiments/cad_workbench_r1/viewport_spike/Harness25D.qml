import QtQuick
import QtQuick.Controls
import "../../../ui/theme"

/*
 * Renders the same 7-component demo architecture (identical positions,
 * names, subtitles, readout data -- copied from MockEngineData.demoEngine)
 * using the Node25D "raised card" treatment, for a fair side-by-side
 * comparison against the accepted 2D EngineNode rendering of the exact
 * same data. Connections are drawn as simple straight lines (not the full
 * orthogonal router) since this spike is about node rendering, not
 * connection routing, which is unchanged from the accepted 2D candidate
 * either way.
 */
ApplicationWindow {
    id: root
    width: 1920
    height: 1080
    visible: true
    color: Theme.background

    Component.onCompleted: Theme.mode = initialTheme

    property var nodes: [
        { key: "fuelTank", name: "Fuel Tank", x: 40, y: 60, subtitle: "CH₄",
          readout: [ { label: "P", value: "—", unit: "MPa" }, { label: "T", value: "—", unit: "K" } ] },
        { key: "fuelPump", name: "Fuel Pump", x: 280, y: 60, subtitle: "Centrifugal",
          readout: [ { label: "Δp", value: "—", unit: "MPa" }, { label: "η", value: "—", unit: "" } ] },
        { key: "oxTank", name: "Oxidiser Tank", x: 40, y: 340, subtitle: "LOX",
          readout: [ { label: "P", value: "—", unit: "MPa" }, { label: "T", value: "—", unit: "K" } ] },
        { key: "oxPump", name: "Oxidiser Pump", x: 280, y: 340, subtitle: "Centrifugal",
          readout: [ { label: "Δp", value: "—", unit: "MPa" }, { label: "η", value: "—", unit: "" } ] },
        { key: "injector", name: "Main Injector", x: 540, y: 200, subtitle: "Pintle",
          readout: [ { label: "Type", value: "Pintle", unit: "" }, { label: "Δp", value: "—", unit: "" } ] },
        { key: "chamber", name: "Main Chamber", x: 800, y: 200, subtitle: "Regen cooled",
          readout: [ { label: "pc", value: "—", unit: "" }, { label: "L*", value: "—", unit: "" } ] },
        { key: "nozzle", name: "Main Nozzle", x: 1060, y: 200, subtitle: "Bell",
          readout: [ { label: "ε", value: "—", unit: "" }, { label: "pe", value: "—", unit: "" } ] }
    ]

    property var connections: [
        [0, 1], [1, 4], [2, 3], [3, 4], [4, 5], [5, 6]
    ]

    Text {
        x: 40; y: 16
        text: "VIEWPORT SPIKE -- OPTION B, 2.5D NODE RENDERING (comparison only, same data as Option A)"
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: 0.5
    }

    Canvas {
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = Theme.textMuted
            ctx.lineWidth = 1.5
            for (var i = 0; i < root.connections.length; ++i) {
                var a = root.nodes[root.connections[i][0]]
                var b = root.nodes[root.connections[i][1]]
                ctx.beginPath()
                ctx.moveTo(a.x + 188, a.y + 30)
                ctx.lineTo(b.x, b.y + 30)
                ctx.stroke()
            }
        }
    }

    Repeater {
        model: root.nodes
        delegate: Node25D {
            required property var modelData
            x: modelData.x
            y: modelData.y
            name: modelData.name
            subtitle: modelData.subtitle
            readout: modelData.readout
        }
    }
}
