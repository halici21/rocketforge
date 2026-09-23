import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Rayleigh charts.
 *
 * Plotted from the same computed block the table renders, so the two can never
 * disagree about what the physics said. RFLineChart draws points it is given
 * and evaluates nothing.
 *
 * The Temperatures view is the reason this section exists. Putting T/T* and
 * T₀/T₀* on one axis makes the whole counter-intuitive part of Rayleigh flow
 * visible at a glance: the static temperature peaks at M = 1/√γ and is already
 * *falling* by the time the stagnation temperature reaches its own maximum at
 * M = 1. Both critical Mach numbers are marked, and marked differently.
 */
Item {
    id: page

    readonly property var quantities: Rayleigh.tableColumns.filter(function (c) {
        return c.key !== "mach"
    })
    // One extra entry beyond the table's columns: the two temperature curves
    // together, which is the view worth arriving at this page for.
    readonly property var choices: ["T/T*  and  T₀/T₀*"].concat(
        quantities.map(function (q) { return q.label }))
    property int choiceIndex: 0
    property bool logScale: false

    readonly property bool isComparison: choiceIndex === 0
    readonly property var active: (!isComparison && quantities.length > 0)
                                  ? quantities[Math.min(choiceIndex - 1, quantities.length - 1)]
                                  : null

    readonly property var series: {
        if (isComparison) {
            var pair = Rayleigh.temperatureComparisonSeries()
            var out = []
            for (var i = 0; i < pair.length; ++i)
                out.push({
                    points: pair[i].points,
                    color: pair[i].label === "T/T*" ? Theme.accent : Theme.textSecondary,
                    dashed: pair[i].label !== "T/T*",
                    width: 1.8
                })
            return out
        }
        if (!active)
            return []
        var branches = Rayleigh.branchSeries(active.key)
        var lines = []
        for (var b = 0; b < branches.length; ++b)
            lines.push({
                points: branches[b].points,
                color: branches[b].label === "Subsonic" ? Theme.accent : Theme.textSecondary,
                dashed: branches[b].label !== "Subsonic",
                width: 1.8
            })
        return lines
    }

    readonly property var legend: isComparison
        ? [{ swatch: Theme.accent, text: "T/T*  — static, peaks at M = 1/√γ" },
           { swatch: Theme.textSecondary, text: "T₀/T₀*  — stagnation, peaks at M = 1" }]
        : [{ swatch: Theme.accent, text: "subsonic branch" },
           { swatch: Theme.textSecondary, text: "supersonic branch" }]

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 78

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                ColumnLayout {
                    Layout.preferredWidth: 560
                    spacing: 3
                    RFSectionLabel { text: "Quantity" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: page.choices
                        currentIndex: page.choiceIndex
                        useMonoFont: true
                        onSelected: function (index) { page.choiceIndex = index }
                    }
                }

                ColumnLayout {
                    spacing: 1
                    RFToggle {
                        text: "Logarithmic vertical axis"
                        checked: page.logScale
                        onToggled: page.logScale = checked
                    }
                    // A log axis cannot show zero, and this curve reaches
                    // exactly zero at the sonic point. Saying so beats a
                    // toggle that appears to do nothing.
                    Text {
                        visible: page.logScale && !chart.logScaleActive
                        text: "not applied — the data reaches zero"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    readonly property string plainText: "γ = " + Rayleigh.tableGamma.toFixed(3)
                          + "  ·  T₀/T₀* floor as M → ∞ = "
                          + Rayleigh.supersonicT0Floor.toFixed(6)
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: page.isComparison ? "Static and stagnation temperature versus M"
                                     : (page.active ? page.active.label + "  versus  M" : "Chart")
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                RowLayout {
                    spacing: Metrics.spacing.l

                    Repeater {
                        model: page.legend

                        delegate: RowLayout {
                            required property var modelData
                            spacing: Metrics.spacing.xs
                            Rectangle {
                                Layout.alignment: Qt.AlignVCenter
                                width: 18; height: 2
                                color: modelData.swatch
                            }
                            Text {
                                readonly property string plainText: modelData.text
                                text: Notation.rich(plainText)
                                textFormat: Notation.textFormat(plainText)
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }
                    }
                }
            }

            RFLineChart {
                id: chart
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240

                series: page.series
                // The two critical Mach numbers, supplied by the controller and
                // labelled differently because they mean different things.
                guides: Rayleigh.criticalGuides()
                logScale: page.logScale
                xLabel: "Mach number  M"
                yLabel: page.isComparison ? "temperature ratio"
                                          : (page.active ? page.active.label : "")

                Connections {
                    target: Rayleigh
                    function onTableChanged() { chart.repaint() }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: page.isComparison
                readonly property string plainText: "The two curves peak in different places, and that is the whole point. "
                      + "T/T* is greatest at M = 1/√γ = "
                      + Rayleigh.staticTemperatureMaxMach.toFixed(6)
                      + " with a value of "
                      + Rayleigh.staticTemperatureMaxValue.toFixed(6)
                      + ", while T₀/T₀* keeps rising to exactly 1 at M = 1. Between the two "
                      + "the static temperature falls while heat is still being added: the "
                      + "flow is accelerating fast enough that the kinetic-energy rise "
                      + "outruns the heat put in. Heat addition drives either branch towards "
                      + "M = 1, and the sonic state is the thermal choking limit."
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                visible: !page.isComparison
                readonly property string plainText: "Subsonic and supersonic are drawn as separate series because their "
                      + "scales differ enough that one autoscale would hide the other. Both "
                      + "meet at the sonic state, which is where heat addition takes either "
                      + "of them."
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }
}
