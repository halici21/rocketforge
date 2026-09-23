import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Scientific caveats that belong beside the result, not in a log.
 *
 * The assigned-enthalpy warning is the one this component exists for. Several
 * of NASA CEA's reactant entries - the cryogenic liquids among them - carry a
 * single assigned enthalpy at one reference condition instead of a
 * temperature-dependent fit. CEA accepts a different temperature and then
 * ignores it. A user who sets liquid oxygen to 95 K and is shown the 90.17 K
 * answer without being told has been misled by the interface, not by the
 * provider: the provider said so.
 *
 * So it shows all three numbers - the reactant, what was requested, what the
 * model used - because "temperature ignored" on its own is not something
 * anyone can act on.
 *
 * The result stays visible throughout. This is a warning, not a refusal: the
 * answer is correct for the reactant the provider modelled.
 */
ColumnLayout {
    id: warnings

    spacing: Metrics.spacing.s
    visible: Thermochemistry.assignedEnthalpyNotes.length > 0
             || Thermochemistry.warnings.length > 0

    // ---- assigned enthalpy, with its numbers ---------------------------
    Repeater {
        model: Thermochemistry.assignedEnthalpyNotes

        delegate: Rectangle {
            required property var modelData

            Layout.fillWidth: true
            implicitHeight: note.implicitHeight + Metrics.spacing.m * 2
            radius: Metrics.radius.m
            color: Theme.surfaceSubtle
            border.width: Metrics.hairline
            border.color: Theme.warning

            // A left edge rather than a filled panel: this is a caveat on a
            // valid result, not an error, and it must not read as one.
            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.margins: Metrics.hairline
                width: 2
                color: Theme.warning
            }

            ColumnLayout {
                id: note
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.leftMargin: Metrics.spacing.m
                anchors.rightMargin: Metrics.spacing.m
                anchors.topMargin: Metrics.spacing.m
                spacing: Metrics.spacing.xs

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    Text {
                        text: "Reactant temperature not used by the provider"
                        color: Theme.text
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                        font.weight: Typography.medium
                    }

                    RFStatusChip {
                        text: "WARNING"
                        tone: "warning"
                    }

                    Item { Layout.fillWidth: true }
                }

                Text {
                    Layout.fillWidth: true
                    text: Thermochemistry.providerLabel + " models reactant "
                          + modelData.reactant + " with an assigned enthalpy rather than a "
                          + "temperature-dependent fit, so the stream temperature you set "
                          + "did not enter this calculation."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                Flow {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xxs
                    spacing: Metrics.spacing.xl

                    Column {
                        spacing: 1
                        Text {
                            text: "REACTANT"
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.letterSpacing: 0.6
                        }
                        Text {
                            text: modelData.reactant
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                    }

                    Column {
                        spacing: 1
                        Text {
                            text: "REQUESTED"
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.letterSpacing: 0.6
                        }
                        Text {
                            text: modelData.requestedText
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                    }

                    Column {
                        spacing: 1
                        Text {
                            text: "USED BY THE MODEL"
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.letterSpacing: 0.6
                        }
                        Text {
                            text: modelData.assignedText
                            color: Theme.warning
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xxs
                    text: "The chamber state shown is the one for this reactant at "
                          + modelData.assignedText + ". The result is usable; the limitation "
                          + "belongs to the provider's reactant data."
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

    // ---- every other warning or error carried by the result -------------
    Repeater {
        model: Thermochemistry.warnings

        delegate: RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: Metrics.spacing.s
            // The assigned-enthalpy case is rendered in full above; showing it
            // twice would be noise.
            visible: modelData.code !== "PROVIDER_ASSIGNED_ENTHALPY_REACTANT"

            Rectangle {
                Layout.preferredWidth: 5
                Layout.preferredHeight: 5
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 6
                radius: 2.5
                color: modelData.severity === "error" ? Theme.error : Theme.warning
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                Text {
                    Layout.fillWidth: true
                    text: Notation.rich(modelData.title)
                    textFormat: Notation.textFormat(modelData.title)
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.medium
                }
                Text {
                    Layout.fillWidth: true
                    text: modelData.message
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            Text {
                Layout.alignment: Qt.AlignTop
                text: modelData.code
                color: Theme.textDisabled
                font.family: Typography.mono
                font.pixelSize: Typography.meta
            }
        }
    }
}
