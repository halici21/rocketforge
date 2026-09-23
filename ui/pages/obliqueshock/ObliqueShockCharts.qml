import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Oblique shock charts.
 *
 * The θ–β–M diagram is the reason this section exists, so it gets the room.
 * The secondary curves below it — how the downstream Mach number and the
 * stagnation-pressure loss vary with deflection — are read from the same
 * generated study the table renders, so the three views cannot disagree.
 */
Item {
    id: page

    // At the 1366x768 floor there is not enough height for a full-size
    // primary plot, an explanatory paragraph AND a fixed-height secondary
    // plot. Opening the real 1366 capture showed the consequence: the
    // primary chart collapsed to ~120px and the paragraph printed straight
    // across it, while the secondary chart kept its full 250px. Reflow
    // rather than shrink (section 55): the paragraph goes, the secondary
    // chart gives up part of its allocation, and the primary plot -- the
    // reason this view exists -- keeps a floor it cannot fall below.
    readonly property bool compact: page.height < 720

    // Sweep-table drawer, closed by default (audit section 49).
    property bool tableOpen: false

    readonly property var quantities: ObliqueShock.tableColumns.filter(function (c) {
        return c.key !== "theta"
    })
    property int quantityIndex: 1
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var points: active ? ObliqueShock.chartSeries(active.key) : []

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 78

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                RFBoundNumberField {
                    Layout.preferredWidth: 140
                    label: "Upstream Mach  M₁"
                    value: ObliqueShock.mach1
                    digits: 4
                    decimals: 4
                    step: 0.1
                    // Drives the sweep as well as the diagram: two charts on
                    // one page showing two different Mach numbers, neither of
                    // them labelled, is how a reader is misled.
                    onValueEdited: function (v) {
                        ObliqueShock.mach1 = v
                        ObliqueShock.tableMach1 = v
                        ObliqueShock.regenerateTable()
                    }
                }

                RFToggle {
                    text: "Overlay other Mach numbers"
                    checked: diagram.showComparison
                    onToggled: diagram.showComparison = checked
                }

                RFToggle {
                    text: "Mark the sonic wave angle"
                    checked: diagram.showSonicGuide
                    onToggled: diagram.showSonicGuide = checked
                }

                Item { Layout.fillWidth: true }

                Text {
                    readonly property string plainText: ObliqueShock.limits.thetaMax !== undefined
                          ? "θ_max = " + ObliqueShock.limits.thetaMax.toFixed(4) + "°"
                          : ""
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: "Shock angle β versus flow deflection θ"
            Layout.fillWidth: true
            // The relation owns the leftover height while it is the only
            // thing being read. Opening the sweep drawer moves that claim to
            // the drawer -- the relation stays on screen as context at a
            // fixed height rather than competing for space it can no longer
            // have. Opening the real capture with the drawer expanded showed
            // what the previous arithmetic did: a 280px floor plus a 420px
            // drawer plus a 250px secondary exceeded the viewport, and the
            // plot's own axis labels and caption printed straight through
            // the panel below it.
            Layout.fillHeight: !page.tableOpen
            Layout.preferredHeight: page.tableOpen ? 300 : -1
            Layout.minimumHeight: 280

            trailing: Component {
                Text {
                    text: "computed by RocketForge · the same solver as the Calculator"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            ObliqueShockDiagram {
                id: diagram
                Layout.fillWidth: true
                Layout.fillHeight: true
                // The diagram asks for 300px of its own; with the sweep
                // drawer open the panel cannot grant that and still leave
                // the drawer room to be worth opening. Same reflow rule as
                // the 1366 floor: the relation stays whole at a smaller
                // size rather than being allowed to overrun its panel.
                compact: page.compact || page.tableOpen
            }

            Text {
                Layout.fillWidth: true
                visible: !page.compact && !page.tableOpen
                readonly property string plainText: "The curve rises from a Mach wave at β = μ to the maximum deflection and "
                      + "falls back to a normal shock at β = 90°, which is why every attainable "
                      + "deflection has two wave angles. Past θ_max the body cannot turn the "
                      + "flow at all and the shock detaches."
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

        // The generated sweep table used to be a peer tab of the two
        // analysis modes, which put a 47-row grid at the same level as the
        // relation itself. It is evidence for the chart above, so it lives
        // here as a drawer that is closed until asked for.
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: tableHeader.implicitHeight

            RowLayout {
                id: tableHeader
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                spacing: Metrics.spacing.s

                RFIcon {
                    name: "chevron-down"
                    width: 12
                    height: 12
                    color: Theme.textMuted
                    rotation: page.tableOpen ? 0 : -90
                    Behavior on rotation {
                        NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
                    }
                }
                Text {
                    text: "Sweep table"
                    color: page.tableOpen ? Theme.text : Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
                Text {
                    text: ObliqueShock.tableRowCount + " rows"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            HoverHandler { cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: page.tableOpen = !page.tableOpen }
        }

        ObliqueShockStudy {
            Layout.fillWidth: true
            Layout.fillHeight: page.tableOpen
            Layout.preferredHeight: page.tableOpen ? 420 : 0
            Layout.minimumHeight: page.tableOpen ? 260 : 0
            visible: page.tableOpen
            clip: true
        }

        RFPanel {
            title: (page.active ? page.active.label + "  versus  θ" : "Secondary")
                   + "   ·   M₁ = " + ObliqueShock.tableMach1.toFixed(2)
                   + " (" + ObliqueShock.tableBranch + " branch)"
            Layout.fillWidth: true
            // At the floor this secondary curve was rendering with its own
            // x axis clipped by the workspace edge. Secondary evidence
            // yields entirely rather than showing half of itself: the
            // primary theta-beta-M surface is the reason this view exists,
            // and the same quantities remain available in the Study table.
            // Also yields to the sweep drawer: the drawer is opened to read
            // exact numbers, and this curve plots the same sweep the drawer
            // is now showing in full.
            visible: !page.compact && !page.tableOpen
            Layout.preferredHeight: visible ? 250 : 0

            trailing: Component {
                RFSegmentedControl {
                    width: 320
                    model: page.quantities.map(function (q) { return q.label })
                    currentIndex: page.quantityIndex
                    useMonoFont: true
                    onSelected: function (index) { page.quantityIndex = index }
                }
            }

            RFLineChart {
                id: secondary
                Layout.fillWidth: true
                Layout.fillHeight: true

                points: page.points
                logScale: false
                xLabel: "Flow deflection  θ  [deg]"
                yLabel: page.active ? page.active.label : ""

                Connections {
                    target: ObliqueShock
                    function onTableChanged() { secondary.repaint() }
                }
            }
        }
    }
}
