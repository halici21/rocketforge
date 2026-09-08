import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Fanno charts.
 *
 * Plotted from the same computed block the table renders, so the two can never
 * disagree about what the physics said. RFLineChart draws points it is given
 * and evaluates nothing.
 *
 * The two branches are delivered as separate series rather than one array
 * containing M = 1. That is a specification requirement, and the reason is
 * visible the moment the friction parameter is selected: it runs to infinity
 * as M → 0 and to a finite 0.82 as M grows, so a single series invites an
 * autoscale that flattens the supersonic branch into the axis.
 */
Item {
    id: page

    readonly property var quantities: Fanno.tableColumns.filter(function (c) {
        return c.key !== "mach"
    })
    property int quantityIndex: 4
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var branches: active ? Fanno.branchSeries(active.key) : []
    property bool logScale: false

    readonly property bool isFriction: active !== null && active.key === "friction_parameter"

    readonly property var series: {
        var out = []
        for (var i = 0; i < branches.length; ++i) {
            out.push({
                points: branches[i].points,
                color: branches[i].label === "Subsonic" ? Theme.accent : Theme.textSecondary,
                dashed: branches[i].label !== "Subsonic",
                width: 1.8
            })
        }
        return out
    }

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
                    Layout.preferredWidth: 480
                    spacing: 3
                    RFSectionLabel { text: "Quantity" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: page.quantities.map(function (q) { return q.label })
                        currentIndex: page.quantityIndex
                        useMonoFont: true
                        onSelected: function (index) { page.quantityIndex = index }
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
                    text: "γ = " + Fanno.tableGamma.toFixed(3)
                          + "  ·  supersonic ceiling 4f_F L*/D = "
                          + Fanno.supersonicLimit.toFixed(6)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: page.active ? page.active.label + "  versus  M" : "Chart"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                RowLayout {
                    spacing: Metrics.spacing.l

                    Repeater {
                        model: [
                            { swatch: Theme.accent, text: "subsonic branch" },
                            { swatch: Theme.textSecondary, text: "supersonic branch" }
                        ]

                        delegate: RowLayout {
                            required property var modelData
                            spacing: Metrics.spacing.xs
                            Rectangle {
                                Layout.alignment: Qt.AlignVCenter
                                width: 18; height: 2
                                color: modelData.swatch
                            }
                            Text {
                                text: modelData.text
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
                logScale: page.logScale
                markerX: 1.0
                markerLabel: "M = 1  ·  choking"
                xLabel: "Mach number  M"
                yLabel: page.active ? page.active.label : ""

                Connections {
                    target: Fanno
                    function onTableChanged() { chart.repaint() }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: page.isFriction
                text: "This is the duct still available before the flow chokes, so it falls to "
                      + "zero at M = 1 from both sides: friction drives a subsonic duct up "
                      + "towards sonic and a supersonic duct down towards it. The supersonic "
                      + "branch is bounded — no supersonic Fanno duct longer than 4f_F L*/D = "
                      + Fanno.supersonicLimit.toFixed(6) + " can be run without a shock."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                visible: !page.isFriction
                text: "Both branches meet at the sonic state, which is where friction takes "
                      + "either of them. The two are drawn as separate series because their "
                      + "scales differ enough that one autoscale would hide the other."
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
