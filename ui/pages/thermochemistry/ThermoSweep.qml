import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * O/F sweep - how the chamber chemistry changes with mixture ratio.
 *
 * An analysis visualisation, not an optimiser. Nothing on this page reports a
 * best, optimal or recommended O/F, and the peak markers say "maximum in
 * sweep" because that is the only claim the data supports: different
 * quantities peak at different mixture ratios, so there is no single peak to
 * recommend. Choosing between them is a decision layer this phase does not
 * build.
 *
 * The sweep runs on an explicit press, never on a keystroke - forty-one
 * equilibrium solves per character typed would be absurd - and every fixed
 * condition stays on screen beside the charts, because a trend without its
 * conditions is not a result.
 */
Item {
    id: view

    readonly property real chartHeight: 230

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- setup ---------------------------------------------------------
        RFPanel {
            Layout.preferredWidth: Metrics.railWidth - 24
            Layout.minimumWidth: 250
            Layout.fillHeight: true
            title: "Sweep"
            contentSpacing: Metrics.spacing.m

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: setup.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: setup
                    width: parent.width
                    spacing: Metrics.spacing.m

                    RFSectionLabel { text: "Varied — O/F" }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "O/F start"
                        value: Thermochemistry.sweepStart
                        digits: 3
                        decimals: 3
                        step: 0.1
                        onValueEdited: function (v) { Thermochemistry.sweepStart = v }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "O/F end"
                        value: Thermochemistry.sweepEnd
                        digits: 3
                        decimals: 3
                        step: 0.1
                        onValueEdited: function (v) { Thermochemistry.sweepEnd = v }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "Points"
                        value: Thermochemistry.sweepPoints
                        digits: 0
                        decimals: 0
                        step: 1
                        onValueEdited: function (v) { Thermochemistry.sweepPoints = v }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: Thermochemistry.sweepRangeValid
                              ? "Step " + Thermochemistry.sweepStep.toFixed(4)
                                + " · limit " + Thermochemistry.maxSweepPoints + " points"
                              : Thermochemistry.sweepRangeMessage
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Thermochemistry.sweepRangeValid ? Theme.textMuted : Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Held fixed" }

                    Repeater {
                        model: Thermochemistry.sweepFixedConditions

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 118
                                text: Notation.rich(modelData.label)
                                textFormat: Notation.textFormat(modelData.label)
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.value
                                wrapMode: Text.WordWrap
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Set on the Calculator tab. The sweep varies O/F only; every "
                              + "other condition above is common to all points."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFDivider { visible: Thermochemistry.hasSweep }

                    RFSectionLabel {
                        visible: Thermochemistry.hasSweep
                        text: "Species to plot"
                    }

                    RFSegmentedControl {
                        Layout.fillWidth: true
                        visible: Thermochemistry.hasSweep
                        model: ["Mole  X", "Mass  Y"]
                        currentIndex: Thermochemistry.sweepSpeciesBasis === "mole" ? 0 : 1
                        onSelected: function (index) {
                            Thermochemistry.sweepSpeciesBasis = index === 0 ? "mole" : "mass"
                        }
                    }

                    Flow {
                        Layout.fillWidth: true
                        visible: Thermochemistry.hasSweep
                        spacing: Metrics.spacing.xs

                        Repeater {
                            model: Thermochemistry.sweepSpeciesOptions.slice(0, 16)

                            delegate: Rectangle {
                                required property var modelData

                                readonly property bool active:
                                    Thermochemistry.sweepSpecies.indexOf(modelData) >= 0

                                height: Metrics.chipHeight
                                width: chipText.implicitWidth + Metrics.spacing.m
                                radius: Metrics.radius.s
                                color: active ? Theme.accentSubtle : Theme.surfaceSubtle
                                border.width: Metrics.hairline
                                border.color: active ? Theme.accent : Theme.divider

                                Text {
                                    id: chipText
                                    anchors.centerIn: parent
                                    text: modelData
                                    color: parent.active ? Theme.text : Theme.textMuted
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.meta
                                }

                                HoverHandler { cursorShape: Qt.PointingHandCursor }
                                TapHandler {
                                    onTapped: Thermochemistry.toggleSweepSpecies(modelData)
                                }
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: Thermochemistry.hasSweep
                        text: "A drawing limit, not a data limit — every species stays in the "
                              + "sweep result whether or not it is plotted."
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }

            // Pinned outside the scroll region, for the same reason the
            // Calculator's Calculate button is.
            RFDivider { Layout.fillWidth: true }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.s

                RFButton {
                    Layout.fillWidth: true
                    text: "Run sweep"
                    variant: "primary"
                    enabled: Thermochemistry.sweepRangeValid && !Thermochemistry.busy
                    onClicked: Thermochemistry.runSweep()
                }
                RFButton {
                    text: "Clear"
                    variant: "quiet"
                    enabled: Thermochemistry.hasSweep
                    onClicked: Thermochemistry.clearSweep()
                }
            }
        }

        // ---- results -------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            RFEmptyState {
                Layout.fillWidth: true
                Layout.topMargin: Metrics.spacing.h2
                visible: !Thermochemistry.hasSweep
                tag: "NO SWEEP"
                title: "No sweep run yet"
                body: "Set the O/F range on the left and press Run sweep. Each point is a "
                      + "separate chamber equilibrium; nothing is drawn until they have "
                      + "been solved."
            }

            Item { Layout.fillHeight: true; visible: !Thermochemistry.hasSweep }

            // ---- summary ----------------------------------------------------
            RowLayout {
                Layout.fillWidth: true
                visible: Thermochemistry.hasSweep
                spacing: Metrics.spacing.s

                RFStatusChip {
                    text: Thermochemistry.sweepSolvedCount + " solved"
                    tone: "success"
                }
                RFStatusChip {
                    visible: Thermochemistry.sweepFailedCount > 0
                    text: Thermochemistry.sweepFailedCount + " no solution"
                    tone: "error"
                }
                RFStatusChip {
                    visible: Thermochemistry.sweepStale
                    text: "Inputs changed"
                    tone: "warning"
                }
                RFStatusChip {
                    text: Thermochemistry.sweepElapsedMs.toFixed(0) + " ms"
                    showDot: false
                }
                Item { Layout.fillWidth: true }
                RFButton {
                    text: "Copy table"
                    variant: "quiet"
                    compact: true
                    onClicked: Thermochemistry.copySweep()
                }
            }

            Text {
                Layout.fillWidth: true
                visible: Thermochemistry.hasSweep && Thermochemistry.sweepStale
                text: "The conditions have changed since this sweep ran. The charts below "
                      + "are for the conditions listed on the left; run the sweep again to "
                      + "match the current case."
                wrapMode: Text.WordWrap
                color: Theme.warning
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            // ---- aggregated warnings ----------------------------------------
            Repeater {
                model: Thermochemistry.sweepWarnings

                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        text: modelData.severity.toUpperCase()
                        tone: modelData.severity === "error" ? "error" : "warning"
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.range_text + " — " + modelData.message
                        wrapMode: Text.WordWrap
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }

            // ---- charts and table -------------------------------------------
            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: Thermochemistry.hasSweep
                contentWidth: width
                contentHeight: sheet.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: sheet
                    width: parent.width
                    spacing: Metrics.spacing.l

                    GridLayout {
                        Layout.fillWidth: true
                        columns: width > 900 ? 2 : 1
                        columnSpacing: Metrics.spacing.l
                        rowSpacing: Metrics.spacing.l

                        ThermoSweepChart {
                            Layout.fillWidth: true
                            Layout.preferredHeight: view.chartHeight
                            quantity: "temperature"
                        }
                        ThermoSweepChart {
                            Layout.fillWidth: true
                            Layout.preferredHeight: view.chartHeight
                            quantity: "molar_mass"
                        }
                        ThermoSweepChart {
                            Layout.fillWidth: true
                            Layout.preferredHeight: view.chartHeight
                            quantity: "gamma"
                        }
                        ThermoSweepSpeciesChart {
                            Layout.fillWidth: true
                            Layout.preferredHeight: view.chartHeight
                        }
                    }

                    RFPanel {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 340
                        title: "Sweep data"
                        contentSpacing: Metrics.spacing.s

                        trailing: Component {
                            RFStatusChip {
                                text: "ascending O/F"
                                showDot: false
                            }
                        }

                        RFEngineeringTable {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: Thermochemistry.sweepModel
                            columns: Thermochemistry.sweepColumns
                            firstColumnWidth: 96
                            columnWidth: 128
                            // A point that did not solve is annotated as well
                            // as carrying "no solution" in its Status column.
                            markedRow: Thermochemistry.sweepFailedRows.length > 0
                                       ? Thermochemistry.sweepFailedRows[0] : -1
                            markedLabel: "NO SOLUTION"
                            secondaryRow: Thermochemistry.sweepFailedRows.length > 1
                                          ? Thermochemistry.sweepFailedRows[1] : -1
                            secondaryLabel: "NO SOLUTION"
                            selectedRow: inspector.row
                            onRowClicked: function (row) { inspector.row = row }
                        }
                    }

                    ThermoSweepPoint {
                        id: inspector
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }
}
