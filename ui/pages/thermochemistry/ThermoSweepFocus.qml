import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * One sweep plot in focus -- the same solved series as its small multiple,
 * at workspace size, with the full analysis-lens tools (zoom, pan, ROI lens,
 * probes, the linked selection). Built by RFFocusOverlay while open.
 *
 * `quantity` is a property key (temperature, molar_mass, gamma) or
 * "species". For species, the legend isolates: clicking a species shows only
 * the isolated ones -- a presentation filter, nothing is removed from the
 * sweep result -- and "Show all" restores every plotted species.
 */
Item {
    // Not `focus`: that name is every Item's own focus property, and a
    // delegate would read its own flag instead of this view.
    id: sweepFocus

    property string quantity: "temperature"
    readonly property bool species: sweepFocus.quantity === "species"

    property var axisValue: ({ label: "", raw: "", unit: "", qualifier: "" })
    property var seriesValue: []
    property var peakValue: ({})
    property var speciesValue: []
    property var isolated: []            // species names shown alone; [] = all

    function refresh() {
        if (sweepFocus.species) {
            sweepFocus.speciesValue = Thermochemistry.sweepSpeciesSeries
        } else {
            sweepFocus.axisValue = Thermochemistry.sweepAxis(sweepFocus.quantity)
            sweepFocus.seriesValue = Thermochemistry.sweepSeries(sweepFocus.quantity)
            sweepFocus.peakValue = Thermochemistry.sweepMaximum(sweepFocus.quantity)
        }
    }
    Component.onCompleted: refresh()
    // Kept by the overlay between opens: another plot is another quantity,
    // and every open starts from the full range with every species shown.
    onQuantityChanged: { sweepFocus.isolated = []; refresh() }
    function reopened() {
        sweepFocus.isolated = []
        interact.clearProbes()
        interact.resetView(false)
        refresh()
    }
    Connections {
        target: Thermochemistry
        function onSweepChanged() { sweepFocus.refresh() }
    }

    function isShown(name) {
        return sweepFocus.isolated.length === 0 || sweepFocus.isolated.indexOf(name) >= 0
    }
    function toggleIsolation(name) {
        var next = sweepFocus.isolated.slice()
        var at = next.indexOf(name)
        if (at >= 0) next.splice(at, 1)
        else next.push(name)
        sweepFocus.isolated = next
    }

    // Esc: the lens (or zoom) first, then the overlay closes.
    function handleEscape() {
        if (interact.lensActive || plot.zoomed) {
            interact.resetView(true)
            return true
        }
        return false
    }

    readonly property var palette: Theme.series

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.s

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.s
            RFPlotToolbar { interaction: interact }
            Item { Layout.fillWidth: true }
            RFStatusChip {
                visible: sweepFocus.species
                text: Thermochemistry.sweepSpeciesBasis === "mole" ? "mole fraction" : "mass fraction"
                showDot: false
            }
            RFStatusChip {
                visible: !sweepFocus.species && sweepFocus.axisValue.qualifier !== ""
                text: sweepFocus.axisValue.qualifier
                showDot: false
            }
        }

        RFLineChart {
            id: plot
            objectName: "sweepFocusChart"
            Layout.fillWidth: true
            Layout.fillHeight: true
            logScale: sweepFocus.species
            showPoints: true
            xLabel: "Mixture ratio  O/F   (oxidiser mass / fuel mass)"
            yLabel: sweepFocus.species ? Thermochemistry.sweepSpeciesAxis : sweepFocus.axisValue.label
            guides: Thermochemistry.sweepFailedRatios
            series: {
                var out = []
                if (sweepFocus.species) {
                    for (var i = 0; i < sweepFocus.speciesValue.length; ++i) {
                        var entry = sweepFocus.speciesValue[i]
                        if (!sweepFocus.isShown(entry.name))
                            continue
                        var colour = sweepFocus.palette[i % sweepFocus.palette.length]
                        for (var s = 0; s < entry.segments.length; ++s)
                            out.push({ points: entry.segments[s], color: colour, width: 1.8,
                                       label: entry.name })
                    }
                } else {
                    for (var k = 0; k < sweepFocus.seriesValue.length; ++k)
                        out.push({ points: sweepFocus.seriesValue[k], color: Theme.accent, width: 1.8 })
                }
                return out
            }
            markers: !sweepFocus.species && sweepFocus.peakValue.of !== undefined
                     ? [{ x: sweepFocus.peakValue.of, y: sweepFocus.peakValue.value, label: "max in sweep" }]
                     : []

            RFPlotInteraction {
                id: interact
                chart: plot
                selectionX: Thermochemistry.sweepSelection.active ? Thermochemistry.sweepSelection.x : NaN
                selectionLabel: Thermochemistry.sweepSelection.label
                xSymbol: "O/F"
                quantity: sweepFocus.quantity
                unit: sweepFocus.species ? "" : (sweepFocus.axisValue.unit || "")
                onPointSelected: function (x, y, s, label) {
                    Thermochemistry.selectSweepNear(x)
                    ShellContext.inspectorOpen = true
                }
                onSelectionCleared: Thermochemistry.sweepSelection.clear()
            }
        }

        // Species: the legend isolates (presentation only).
        Flow {
            Layout.fillWidth: true
            visible: sweepFocus.species
            spacing: Metrics.spacing.s

            Repeater {
                model: sweepFocus.speciesValue
                delegate: Row {
                    required property var modelData
                    required property int index
                    spacing: Metrics.spacing.xs
                    opacity: sweepFocus.isShown(modelData.name) ? 1 : 0.45
                    // the series' own colour, beside its name
                    Rectangle {
                        width: 12; height: 3; radius: 1
                        anchors.verticalCenter: parent.verticalCenter
                        color: sweepFocus.palette[index % sweepFocus.palette.length]
                    }
                    RFToolButton {
                        text: modelData.name
                        tooltip: "Show this species alone (click others to add them); nothing is removed from the sweep"
                        checked: sweepFocus.isolated.indexOf(modelData.name) >= 0
                        onClicked: sweepFocus.toggleIsolation(modelData.name)
                    }
                }
            }
            RFToolButton {
                objectName: "sweepShowAllSpecies"
                visible: sweepFocus.isolated.length > 0
                text: "Show all"
                tooltip: "Every plotted species again"
                onClicked: sweepFocus.isolated = []
            }
        }

        Text {
            Layout.fillWidth: true
            visible: text !== ""
            text: !sweepFocus.species && sweepFocus.peakValue.text !== undefined ? sweepFocus.peakValue.text : ""
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
