import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Who computed this result, in what model, against which data.
 *
 * Read from the result's own provenance record - not from what happens to be
 * installed now. If the library were upgraded under a displayed result, the
 * result would keep saying which version made it, because that is the fact
 * that makes it reproducible.
 *
 * A compact summary with the whole record one click away: the provider and the
 * model belong in front of the user at all times, the database hash belongs
 * within reach.
 *
 * Nothing here is editable. A database hash and an adapter version are facts
 * about a result, not settings.
 */
ColumnLayout {
    id: panel

    spacing: Metrics.spacing.s

    property bool expanded: false

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        RFSectionLabel { text: "Provenance" }

        RFStatusChip {
            text: Thermochemistry.provenanceSummary.provider
            showDot: false
        }
        RFStatusChip {
            text: Thermochemistry.provenanceSummary.model
            showDot: false
        }
        RFStatusChip {
            visible: Thermochemistry.provenanceSummary.database !== ""
            text: Thermochemistry.provenanceSummary.database + "  "
                  + Thermochemistry.provenanceSummary.sha
            showDot: false
        }

        Item { Layout.fillWidth: true }

        RFButton {
            text: panel.expanded ? "Hide detail" : "Show detail"
            variant: "quiet"
            compact: true
            onClicked: panel.expanded = !panel.expanded
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        visible: panel.expanded
        spacing: Metrics.spacing.xs

        Repeater {
            model: Thermochemistry.provenanceRows

            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: Metrics.spacing.m

                Text {
                    Layout.preferredWidth: 176
                    Layout.alignment: Qt.AlignTop
                    text: modelData.label
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
                Text {
                    Layout.fillWidth: true
                    text: modelData.value
                    wrapMode: Text.WrapAnywhere
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                }
            }
        }

        Item { Layout.preferredHeight: Metrics.spacing.xs }

        Text {
            Layout.fillWidth: true
            text: "Product species set (" + Thermochemistry.speciesSet.length + ")"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        Text {
            Layout.fillWidth: true
            text: Thermochemistry.speciesSet.join("  ")
            wrapMode: Text.WordWrap
            color: Theme.textSecondary
            font.family: Typography.mono
            font.pixelSize: Typography.meta
        }
    }
}
