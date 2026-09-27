import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * Normal-shock relation.
 *
 * Plotted from the same computed block the table renders (NormalShock
 * .chartData), so the two can never disagree about what the physics said.
 * RFLineChart draws points it is given and evaluates nothing.
 *
 * The published values can be overlaid as discrete dots. They are a *check*
 * drawn on top of the computed curve, never the curve itself, and they are
 * never joined into a line - Appendix B prints values at particular Mach
 * numbers and says nothing about what lies between them.
 *
 * The analysis layer is Isentropic's: a table row selected on the Table tab
 * is this chart's crosshair at that row's M1, a row range is a quiet band
 * (the view is never zoomed to it), and a click reads the nearest real sample
 * into the one shared selection. The solved shock is marked where it lies on
 * this curve -- only when the calculator and the table describe the same gas;
 * otherwise by its M1 alone, and the caption says why. Nothing here solves.
 */
Item {
    id: page

    readonly property var quantities: NormalShock.tableColumns.filter(function (c) {
        return c.key !== "mach1"
    })
    property int quantityIndex: 0
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    // A property of the controller, so a regenerated table redraws the curve.
    readonly property var points: active ? (NormalShock.chartData[active.key] || []) : []
    property bool logScale: true
    property bool showReference: false
    readonly property var referencePoints: (showReference && active)
                                           ? NormalShock.referenceSeries(active.key) : []

    // ---- the solved shock -------------------------------------------------
    readonly property var rows: {
        var out = {}
        var list = NormalShock.results
        for (var i = 0; i < list.length; ++i)
            out[list[i].key] = list[i]
        return out
    }
    readonly property var machRow: rows["mach1"] !== undefined ? rows["mach1"] : null
    readonly property var activeRow: active && rows[active.key] !== undefined ? rows[active.key] : null
    // Comparisons only: which curve this is, and whether the shock is on it.
    readonly property bool sameGas: NormalShock.gamma === NormalShock.plottedGamma
    readonly property bool inRange: NormalShock.valid && points.length > 1
                                    && NormalShock.mach >= points[0].x
                                    && NormalShock.mach <= points[points.length - 1].x
    readonly property bool onCurve: inRange && sameGas && page.activeRow !== null
    // Which way the plotted curve runs through the solved point, read off the
    // neighbouring table points -- only so the ring's label sits on the side
    // the curve leaves clear.
    readonly property int slope: {
        if (!page.inRange)
            return 1
        for (var i = 1; i < page.points.length; ++i)
            if (page.points[i].x >= NormalShock.mach)
                return page.points[i].y >= page.points[i - 1].y ? 1 : -1
        return 1
    }

    // The samples in view, as tab-separated text.
    function copyValues() {
        if (!page.active)
            return
        var e = chart.extent()
        var lines = ["M1\t" + page.active.key]
        for (var i = 0; i < page.points.length; ++i) {
            var p = page.points[i]
            if (p.x >= e.xmin && p.x <= e.xmax)
                lines.push(p.x + "\t" + p.y)
        }
        NormalShock.copyText(lines.join("\n"))
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.s

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.l

            RFSectionLabel {
                readonly property string plainText: page.active ? page.active.label + "  versus  M₁"
                                                                : "Relation"
                text: Notation.sectionRich(plainText)
                textFormat: Notation.textFormat(plainText)
            }

            Item { Layout.fillWidth: true }

            RFSegmentedControl {
                objectName: "normalShockQuantity"
                Layout.preferredWidth: Math.min(520, 74 * Math.max(1, page.quantities.length))
                model: page.quantities.map(function (q) { return q.label })
                currentIndex: page.quantityIndex
                useMonoFont: true
                onSelected: function (index) { page.quantityIndex = index }
            }

            RFToggle {
                text: "Logarithmic vertical axis"
                checked: page.logScale
                onToggled: page.logScale = checked
            }

            RFToggle {
                text: "Overlay Appendix B"
                checked: page.showReference
                enabled: NormalShock.referenceAvailable
                onToggled: page.showReference = checked
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            RFPlotToolbar {
                interaction: interact
                canCopy: true
                onCopyRequested: page.copyValues()
            }
            Item { Layout.fillWidth: true }
            Text {
                text: page.showReference ? "line: RocketForge · dots: Anderson Appendix B"
                                         : "computed by RocketForge"
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        RFLineChart {
            id: chart
            objectName: "normalShockRelationChart"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 240
            builtInHover: false
            dataKey: page.active ? page.active.key : ""

            points: page.points
            referencePoints: page.referencePoints
            logScale: page.logScale
            xLabel: "Upstream Mach number  M₁"
            yLabel: page.active ? page.active.label : ""

            // The solved shock, drawn only where it lies on this curve.
            markers: page.onCurve && page.activeRow !== null && page.machRow !== null
                     ? [{ x: NormalShock.mach, y: page.activeRow.raw, slope: page.slope,
                          label: "M₁ " + page.machRow.value + "   "
                                 + page.active.label + " " + page.activeRow.value }]
                     : []
            guides: {
                var out = []
                if (page.inRange)
                    out.push({ value: NormalShock.mach, axis: "x", label: "" })
                if (page.onCurve)
                    out.push({ value: page.activeRow.raw, axis: "y", label: "" })
                return out
            }

            // View, inspect, zoom. A click reads a real table sample into the
            // shared selection; a table row selected on the Table tab shows
            // here as the same crosshair, and a row range as a quiet interval.
            RFPlotInteraction {
                id: interact
                chart: chart
                readonly property bool rangeSelected: NormalShock.selection.kind === "tableRange"
                selectionX: NormalShock.selection.active && !rangeSelected ? NormalShock.selection.x : NaN
                selectionLabel: NormalShock.selection.kind === "tableRow" ? NormalShock.selection.label : ""
                highlightX0: rangeSelected ? NormalShock.selection.x : NaN
                highlightX1: rangeSelected ? NormalShock.selection.x1 : NaN
                xSymbol: "<i>M</i>₁"
                quantity: page.active ? page.active.key : ""
                unit: ""
                seriesLabels: [page.active ? page.active.label : ""]
                onPointSelected: function (x, y, s, label) {
                    if (s === 0 && page.active) {
                        NormalShock.selection.selectPoint("plotPoint", page.active.key, x, y,
                                                          page.active.label, "chart")
                        ShellContext.inspectorOpen = true
                    }
                }
                onSelectionCleared: NormalShock.selection.clear()
            }
        }

        // What the curve is, and what the ring is -- in words.
        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.l

            Text {
                objectName: "normalShockRelationCaption"
                Layout.fillWidth: true
                readonly property string plainText: {
                    if (page.points.length < 2)
                        return "No table is generated, so there is no curve to draw."
                    var curve = "Curve: the generated table, " + page.points.length
                                + " points at γ = " + NormalShock.plottedGamma.toFixed(3) + "."
                    if (!NormalShock.valid)
                        return curve + " No solved shock to mark."
                    if (!page.inRange)
                        return curve + " The solved M₁ = " + (page.machRow ? page.machRow.value : "—")
                               + " lies outside the plotted range."
                    if (!page.sameGas)
                        return curve + " The solved shock is at γ = " + NormalShock.gamma.toFixed(3)
                               + ", not on this curve, so it is marked by its M₁ only."
                    return curve + " Ring: the solved shock at the same γ."
                }
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                elide: Text.ElideRight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                // A toggle that silently does nothing is worse than one that
                // says why.
                visible: page.logScale && !chart.logScaleActive
                text: "range too narrow for a log axis"
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        Text {
            Layout.fillWidth: true
            visible: page.showReference && page.referencePoints.length > 0
            text: "The dots are printed values, plotted where they are printed and nowhere "
                  + "between. They check the curve; they never produce it."
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
