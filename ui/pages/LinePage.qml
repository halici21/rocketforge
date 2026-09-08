import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * Line - distributed wall friction in a straight circular liquid line.
 *
 * The first hydraulic component in this program, and the first consumer of a
 * transport property. It takes a fluid state, a flow and a pipe, and answers
 * with a velocity, a Reynolds number, a Darcy friction factor and a friction
 * pressure drop.
 *
 * Three things this page is careful about:
 *
 *   - The pressure field is the LINE INLET / fluid-property pressure. It is a
 *     feed-system state and is labelled as one, because reading a chamber
 *     pressure into it would evaluate liquid methane at 100 bar.
 *   - The friction factor is named DARCY every time it appears. The Fanning
 *     factor is a different quantity, smaller by exactly four, and one label
 *     for both is how a pressure drop comes out four times too small.
 *   - In the transitional band no friction factor is shown at all. Not zero,
 *     not interpolated: between 64/Re and Colebrook there is no correlation
 *     this model will stand behind, and a number there would be invented.
 */
Item {
    id: page

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Line"
            subtitle: "Steady single-phase liquid flow in a straight circular "
                      + "line — Darcy friction factor and distributed friction "
                      + "pressure drop"

            trailing: Component {
                RFStatusChip {
                    text: Line.providerAvailable ? Line.providerLabel
                                                 : "Provider unavailable"
                    tone: Line.providerAvailable ? "positive" : "neutral"
                }
            }
        }

        RFEmptyState {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !Line.providerAvailable
            title: "High-fidelity fluid properties are not installed"
            body: Line.providerDetail
        }

        // ---- inputs ------------------------------------------------------
        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 178
            visible: Line.providerAvailable
            title: "Fluid state and line"

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: false
                spacing: Metrics.spacing.m

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: Metrics.spacing.m

                    RFComboBox {
                        Layout.preferredWidth: 200
                        label: "Fluid"
                        model: Line.fluidOptions.map(function (o) { return o.label })
                        currentIndex: {
                            var options = Line.fluidOptions
                            for (var i = 0; i < options.length; ++i)
                                if (options[i].name === Line.fluidName)
                                    return i
                            return 0
                        }
                        onActivated: function (index) {
                            var options = Line.fluidOptions
                            if (index >= 0 && index < options.length)
                                Line.setFluid(options[index].name)
                        }
                    }

                    RFBoundNumberField {
                        Layout.preferredWidth: 175
                        label: "Temperature  [K]"
                        value: Line.temperature
                        digits: 3
                        step: 1
                        onValueEdited: function (v) { Line.setTemperature(v) }
                    }

                    RFBoundNumberField {
                        id: pressureField
                        Layout.preferredWidth: 230
                        label: "Line inlet pressure  [Pa]"
                        value: Line.pressure
                        digits: 0
                        step: 50000
                        onValueEdited: function (v) { Line.setPressure(v) }

                        HoverHandler { id: pressureHover }
                        RFTooltip {
                            visible: pressureHover.hovered
                            text: "The feed-system pressure the fluid "
                                  + "properties are evaluated at, and the "
                                  + "pressure the friction loss is subtracted "
                                  + "from. This is not a chamber pressure."
                        }
                    }

                    RFBoundNumberField {
                        Layout.preferredWidth: 175
                        label: "Mass flow  [kg/s]"
                        value: Line.massFlow
                        digits: 4
                        step: 0.1
                        onValueEdited: function (v) { Line.setMassFlow(v) }
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: Metrics.spacing.m

                    RFBoundNumberField {
                        Layout.preferredWidth: 175
                        label: "Length  L  [m]"
                        value: Line.length
                        digits: 3
                        step: 0.5
                        onValueEdited: function (v) { Line.setLength(v) }
                    }

                    RFBoundNumberField {
                        Layout.preferredWidth: 200
                        label: "Inner diameter  D  [m]"
                        value: Line.innerDiameter
                        digits: 5
                        step: 0.005
                        onValueEdited: function (v) { Line.setInnerDiameter(v) }
                    }

                    RFBoundNumberField {
                        Layout.preferredWidth: 230
                        label: "Absolute roughness  ε  [m]"
                        value: Line.absoluteRoughness
                        digits: 8
                        step: 0.000001
                        onValueEdited: function (v) { Line.setAbsoluteRoughness(v) }
                    }

                    Item { Layout.fillWidth: true }

                    RFButton {
                        text: "Solve"
                        variant: "primary"
                        onClicked: Line.calculate()
                    }
                }
            }
        }

        // ---- results -----------------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: Line.providerAvailable
            spacing: Metrics.spacing.m

            RFPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "Result"

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: Metrics.spacing.s

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        spacing: Metrics.spacing.s

                        RFStatusChip {
                            text: Line.statusLabel
                            tone: Line.statusTone
                        }
                        RFStatusChip {
                            visible: Line.flowRegime !== ""
                            text: Line.flowRegime
                            tone: Line.isTransitional ? "caution" : "neutral"
                        }
                        RFStatusChip {
                            visible: Line.hasResult
                            text: Line.transportValidated
                                  ? "Viscosity validated"
                                  : "Viscosity not validated here"
                            tone: Line.transportValidated ? "positive" : "caution"
                        }
                        Item { Layout.fillWidth: true }
                    }

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: !Line.hasResult
                        title: "No result yet"
                        body: Line.message !== ""
                              ? Line.message
                              : "Set a fluid state, a mass flow and a line "
                                + "geometry, then solve."
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: Line.isTransitional
                        text: Line.message
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        wrapMode: Text.WordWrap
                    }

                    Repeater {
                        model: Line.hasResult ? Line.resultRows : []
                        delegate: RowLayout {
                            id: resultRow
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: false
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 230
                                text: resultRow.modelData.label
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.preferredWidth: 150
                                horizontalAlignment: Text.AlignRight
                                text: resultRow.modelData.value
                                color: resultRow.modelData.available
                                       ? Theme.text : Theme.textMuted
                                font.family: Typography.mono
                                font.pixelSize: Typography.body
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: resultRow.modelData.unit
                                color: Theme.textMuted
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            RFPanel {
                Layout.preferredWidth: 400
                Layout.fillHeight: true
                title: "Provenance and assumptions"

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: Metrics.spacing.xs

                    Repeater {
                        model: Line.provenanceRows
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
                        visible: Line.assumptionRows.length > 0
                    }

                    Repeater {
                        model: Line.assumptionRows
                        delegate: Text {
                            id: assumptionRow
                            required property var modelData
                            Layout.fillWidth: true
                            text: "· " + assumptionRow.modelData.text
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
