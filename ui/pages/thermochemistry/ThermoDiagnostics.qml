import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Every message the provider and RocketForge's own validation produced,
 * including the ones that passed.
 *
 * The informational rows matter: "element conservation, reactants = products:
 * residual 1.6e-08 within 1.0e-06" is the check that would have rejected this
 * result had it failed, and seeing it pass is what makes the result
 * trustworthy rather than merely returned.
 *
 * Each row carries its stable code. A code this build does not recognise still
 * reaches the screen, with a neutral title and its own name attached, rather
 * than being dropped.
 */
ColumnLayout {
    id: panel

    spacing: Metrics.spacing.s

    property bool expanded: false

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        RFSectionLabel { text: "Diagnostics" }

        RFStatusChip {
            text: Thermochemistry.diagnostics.length + " checks"
            showDot: false
        }

        RFStatusChip {
            visible: Thermochemistry.warningCount > 0
            text: Thermochemistry.warningCount + " to read"
            tone: "warning"
        }

        Item { Layout.fillWidth: true }

        RFButton {
            text: panel.expanded ? "Hide detail" : "Show detail"
            variant: "quiet"
            compact: true
            onClicked: panel.expanded = !panel.expanded
        }
    }

    Text {
        Layout.fillWidth: true
        visible: Thermochemistry.diagnostics.length === 0
        text: "No diagnostics were reported for this result."
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }

    ColumnLayout {
        Layout.fillWidth: true
        visible: panel.expanded
        spacing: Metrics.spacing.xs

        Repeater {
            model: Thermochemistry.diagnostics

            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: Metrics.spacing.s

                // Severity is carried by a word as well as a colour, so the
                // row is readable without relying on hue.
                Text {
                    Layout.preferredWidth: 54
                    Layout.alignment: Qt.AlignTop
                    text: modelData.severity.toUpperCase()
                    color: modelData.severity === "error" ? Theme.error
                         : modelData.severity === "warning" ? Theme.warning
                         : Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    font.letterSpacing: 0.6
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xs

                        Text {
                            text: modelData.title
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.weight: Typography.medium
                        }
                        Text {
                            visible: !modelData.known
                            text: "· unrecognised code, shown as reported"
                            color: Theme.textDisabled
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        Item { Layout.fillWidth: true }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: modelData.message
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
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
}
