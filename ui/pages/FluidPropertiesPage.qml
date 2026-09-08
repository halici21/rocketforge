import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * Fluid Properties - what a substance is doing at a temperature and a pressure.
 *
 * The fundamental layer beneath everything else in this program: a propellant
 * stream has a density and an enthalpy before it is a reactant, and those are
 * what the reactant-enthalpy correction and the density impulse are built on.
 *
 * The page is deliberately small. It inspects a property model; it does not
 * size a line, a valve or an orifice, and it computes nothing itself -- every
 * number and every string below came from the controller.
 *
 * Two things it insists on, because both are easy to get wrong:
 *
 *   - Pressure is an input, never a default. The field starts at a value, that
 *     value is visible, and it travels into the request. Oxygen at 95 K is a
 *     liquid at 3 bar and a gas at 1 atm, so a page that supplied a pressure
 *     would be choosing the answer.
 *   - An unavailable property is a row with a reason, not an empty cell. A
 *     blank reads as zero, and a missing viscosity is not 0 Pa s.
 */
Item {
    id: page

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Fluid Properties"
            subtitle: "Density, enthalpy, specific heat, viscosity and thermal "
                      + "conductivity at an explicit temperature and pressure"

            trailing: Component {
                RFStatusChip {
                    text: FluidProperties.providerAvailable
                          ? FluidProperties.providerLabel
                          : "Provider unavailable"
                    tone: FluidProperties.providerAvailable ? "positive" : "neutral"
                }
            }
        }

        // ---- provider missing --------------------------------------------
        RFEmptyState {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !FluidProperties.providerAvailable
            title: "High-fidelity fluid properties are not installed"
            body: FluidProperties.providerDetail
        }

        // ---- inputs ------------------------------------------------------
        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 108
            visible: FluidProperties.providerAvailable
            title: "State"

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: false
                spacing: Metrics.spacing.m

                RFComboBox {
                    Layout.preferredWidth: 220
                    label: "Fluid"
                    model: FluidProperties.fluidOptions.map(
                               function (o) { return o.label })
                    currentIndex: {
                        var options = FluidProperties.fluidOptions
                        for (var i = 0; i < options.length; ++i)
                            if (options[i].name === FluidProperties.fluidName)
                                return i
                        return 0
                    }
                    onActivated: function (index) {
                        var options = FluidProperties.fluidOptions
                        if (index >= 0 && index < options.length)
                            FluidProperties.setFluid(options[index].name)
                    }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 190
                    label: "Temperature  [K]"
                    value: FluidProperties.temperature
                    digits: 3
                    step: 1
                    onValueEdited: function (v) { FluidProperties.setTemperature(v) }
                }

                RFBoundNumberField {
                    id: pressureField
                    Layout.preferredWidth: 210
                    label: "Pressure  [Pa]"
                    value: FluidProperties.pressure
                    digits: 0
                    step: 10000
                    onValueEdited: function (v) { FluidProperties.setPressure(v) }

                    HoverHandler { id: pressureHover }
                    RFTooltip {
                        visible: pressureHover.hovered
                        text: "This state's own pressure. There is no default: "
                              + "the phase, and therefore every property, "
                              + "depends on it."
                    }
                }

                Item { Layout.fillWidth: true }

                RFButton {
                    text: "Evaluate"
                    variant: "primary"
                    onClicked: FluidProperties.calculate()
                }
            }
        }

        // ---- results -----------------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: FluidProperties.providerAvailable
            spacing: Metrics.spacing.m

            RFPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "Properties"

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: Metrics.spacing.s

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        spacing: Metrics.spacing.s

                        RFStatusChip {
                            text: FluidProperties.statusLabel
                            tone: FluidProperties.statusTone
                        }
                        RFStatusChip {
                            visible: FluidProperties.phase !== ""
                            text: "Phase: " + FluidProperties.phase
                            tone: "neutral"
                        }
                        Item { Layout.fillWidth: true }
                    }

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: !FluidProperties.hasResult
                        title: "No result yet"
                        body: FluidProperties.message !== ""
                              ? FluidProperties.message
                              : "Choose a fluid, a temperature and a pressure, "
                                + "then evaluate."
                    }

                    Repeater {
                        model: FluidProperties.hasResult
                               ? FluidProperties.resultRows : []
                        delegate: RowLayout {
                            id: propertyRow
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: false
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 190
                                text: propertyRow.modelData.label
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.preferredWidth: 150
                                horizontalAlignment: Text.AlignRight
                                text: propertyRow.modelData.value
                                color: propertyRow.modelData.available
                                       ? Theme.text : Theme.textMuted
                                font.family: Typography.mono
                                font.pixelSize: Typography.body
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.preferredWidth: 96
                                text: propertyRow.modelData.unit
                                color: Theme.textMuted
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: !propertyRow.modelData.available
                                text: propertyRow.modelData.status
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            RFPanel {
                Layout.preferredWidth: 380
                Layout.fillHeight: true
                title: "Provenance"

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: Metrics.spacing.xs

                    Repeater {
                        model: FluidProperties.provenanceRows
                        delegate: RowLayout {
                            id: provenanceRow
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: false
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 140
                                text: provenanceRow.modelData.label
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: provenanceRow.modelData.value
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                                wrapMode: Text.WordWrap
                            }
                        }
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        visible: FluidProperties.diagnosticRows.length > 0
                    }

                    Repeater {
                        model: FluidProperties.diagnosticRows
                        delegate: Text {
                            id: diagnosticRow
                            required property var modelData
                            Layout.fillWidth: true
                            text: diagnosticRow.modelData.message
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }
    }
}
