import QtQuick
import "../theme"

/*
 * RFPlotToolbar — the context tools of an interactive plot.
 *
 * Select, Pan, ROI and Probe are modes of one RFPlotInteraction; Reset
 * returns to the full range; Pin and Copy are offered only where the page
 * wires them. Compact and quiet: a plot's tools, not a ribbon.
 */
Row {
    id: bar

    required property Item interaction
    property bool canPin: false
    property bool canCopy: false

    signal pinRequested()
    signal copyRequested()

    objectName: "plotToolbar"
    spacing: Metrics.spacing.xs

    Repeater {
        model: [
            { tool: "select", text: "Select", tip: "Click a sample to select it; Shift + drag for a region" },
            { tool: "pan", text: "Pan", tip: "Drag to pan (middle drag works in any mode)" },
            { tool: "roi", text: "ROI", tip: "Drag a region: it becomes the analysis lens" },
            { tool: "probe", text: "Probe", tip: "Click to pin a probe (up to three); Ctrl + click in any mode" }
        ]
        delegate: RFToolButton {
            required property var modelData
            text: modelData.text
            tooltip: modelData.tip
            checked: bar.interaction.tool === modelData.tool
            onClicked: bar.interaction.tool = modelData.tool
        }
    }

    Item { width: Metrics.spacing.s; height: 1 }

    RFToolButton {
        text: "Reset"
        tooltip: "Back to the full range (double-click, or Esc)"
        enabled: bar.interaction.chart.zoomed
        onClicked: bar.interaction.resetView(true)
    }
    RFToolButton {
        text: "Clear probes"
        visible: bar.interaction.probes.length > 0
        onClicked: bar.interaction.clearProbes()
    }
    RFToolButton {
        visible: bar.canPin
        text: "Pin snapshot"
        tooltip: "Keep this analytical view -- range, quantity, solved state -- for comparison"
        onClicked: bar.pinRequested()
    }
    RFToolButton {
        visible: bar.canCopy
        text: "Copy values"
        tooltip: "Copy the samples inside the current range as tab-separated text"
        onClicked: bar.copyRequested()
    }
}
