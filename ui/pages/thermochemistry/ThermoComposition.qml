import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Composition explorer - what the equilibrium chamber mixture is made of.
 *
 * It reads the Calculator's result. It never solves anything of its own, so
 * the composition on this page and the temperature on that one are always the
 * same calculation.
 *
 * Two distinctions this page exists to keep visible:
 *
 *   - The threshold control is a DISPLAY threshold. It hides rows; it changes
 *     no physics, and the hidden species stay in the result. The label says
 *     "display" for that reason, and the count and summed fraction of what was
 *     hidden are stated rather than left implicit.
 *
 *   - Condensed *candidates* are not condensed *material*, and a measured
 *     6.24e-08 is not zero either. The verdict lives with the composition it
 *     describes rather than in the control rail, and it distinguishes four
 *     states; see ThermoCondensedSummary.qml.
 */
Item {
    id: view

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- controls ------------------------------------------------------
        RFPanel {
            Layout.preferredWidth: Metrics.railWidth - 24
            Layout.minimumWidth: 248
            Layout.fillHeight: true
            title: "Display"
            contentSpacing: Metrics.spacing.m


            // The condensed panel gained two rows -- the exact fraction and
            // the reporting threshold -- and at 1366x768 that pushed them
            // below the panel. The controls scroll; the copy action stays
            // pinned, the same arrangement the Calculator uses for Calculate.
            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: controls.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: controls
                    width: parent.width
                    spacing: Metrics.spacing.m

                    RFSectionLabel { text: "Basis" }

                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["Mole  X", "Mass  Y"]
                        currentIndex: Thermochemistry.compositionBasis === "mole" ? 0 : 1
                        onSelected: function (index) {
                            Thermochemistry.compositionBasis = index === 0 ? "mole" : "mass"
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Both bases are carried on every row. Switching between them changes "
                              + "what is shown and what the sort is on; it does not recalculate "
                              + "anything and does not change the stored composition."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Display threshold" }

                    RFComboBox {
                        Layout.fillWidth: true
                        model: Thermochemistry.traceThresholds.map(function (t) { return t.label })
                        currentIndex: Thermochemistry.traceThresholdIndex
                        onCurrentIndexChanged: Thermochemistry.traceThresholdIndex = currentIndex
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Hides rows below the chosen fraction. The result keeps every species "
                              + "the provider returned — this is a display filter, not a composition "
                              + "cutoff, and nothing is recalculated when it changes."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    // Deliberately not two-way bound: binding `text` to the property
                    // this field writes is the classic QML loop.
                    RFTextField {
                        Layout.fillWidth: true
                        label: "Find species"
                        placeholder: "OH, CO, H2O, C(gr)"
                        onTextChanged: Thermochemistry.speciesFilter = text
                    }

                }
            }

            RFDivider { Layout.fillWidth: true }

            RFButton {
                Layout.fillWidth: true
                text: "Copy table"
                variant: "quiet"
                enabled: Thermochemistry.hasComposition
                onClicked: Thermochemistry.copyComposition()
            }
        }

        // ---- table ---------------------------------------------------------
        RFPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            title: "Product composition"
            contentSpacing: Metrics.spacing.s

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: Thermochemistry.hasComposition
                        text: Thermochemistry.speciesShown + " of "
                              + Thermochemistry.speciesTotal + " species"
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: Thermochemistry.hasComposition
                        text: Thermochemistry.resultHeadline
                        showDot: false
                    }
                }
            }

            RFEmptyState {
                Layout.fillWidth: true
                Layout.topMargin: Metrics.spacing.h1
                visible: !Thermochemistry.hasComposition
                tag: "NO COMPOSITION"
                title: "No composition available"
                body: "Composition comes from a solved chamber equilibrium. Run a "
                      + "calculation on the Calculator tab and the mixture will appear here."
            }

            ThermoCondensedSummary { Layout.fillWidth: true }

            RFDivider {
                Layout.fillWidth: true
                visible: Thermochemistry.hasComposition
            }

            ThermoCompositionBars {
                Layout.fillWidth: true
                visible: Thermochemistry.hasComposition
            }

            RFEngineeringTable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: Thermochemistry.hasComposition
                model: Thermochemistry.compositionModel
                columns: Thermochemistry.compositionColumns
                firstColumnWidth: 132
                columnWidth: 152
                // Condensed species are annotated in the gutter, the same way
                // the compressible tables annotate the sonic line: they change
                // what the result means, so "solid" in a column is not enough
                // on its own.
                markedRow: Thermochemistry.condensedRows.length > 0
                           ? Thermochemistry.condensedRows[0] : -1
                markedLabel: "CONDENSED"
                secondaryRow: Thermochemistry.condensedRows.length > 1
                              ? Thermochemistry.condensedRows[1] : -1
                secondaryLabel: "CONDENSED"
            }

            Text {
                Layout.fillWidth: true
                visible: Thermochemistry.hasComposition
                text: Thermochemistry.compositionSums
                color: Theme.textMuted
                font.family: Typography.mono
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                visible: Thermochemistry.hiddenSummary !== ""
                text: Thermochemistry.hiddenSummary
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }
}
