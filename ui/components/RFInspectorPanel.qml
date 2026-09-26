import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * RFInspectorPanel — what is selected, its values, and where they came from.
 *
 * The shared inspector content for a workspace's selection: a station, a
 * plotted point, a table row. It shows only the rows the readout carries --
 * the backend's own formatted values -- and says which solved state produced
 * them and what the picture of it claims. It never computes a value.
 *
 *   readout = { title, note, rows: [{label, value, unit}], identity,
 *               fidelity, stale }
 */
Rectangle {
    id: root

    property var readout: ({})
    property string sourceName: ""
    property string emptyHint: "Select a station, a point or a row to inspect it."

    signal clearRequested()
    signal closeRequested()

    readonly property bool hasReadout: root.readout !== undefined && root.readout !== null
                                       && root.readout.rows !== undefined
                                       && root.readout.rows.length > 0

    color: Theme.surfaceSubtle
    implicitWidth: Metrics.inspectorWidth

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.spacing.l
        spacing: Metrics.spacing.m

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            RFSectionLabel { text: "Inspector" }
            Item { Layout.fillWidth: true }
            RFToolButton { text: "Close"; tooltip: "Close the inspector"; onClicked: root.closeRequested() }
        }

        Text {
            Layout.fillWidth: true
            visible: root.hasReadout
            text: root.hasReadout ? root.readout.title : ""
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.readoutLarge
            font.weight: Typography.medium
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.fillWidth: true
            visible: root.hasReadout && (root.readout.note || "") !== ""
            text: root.hasReadout ? Notation.rich(root.readout.note || "") : ""
            textFormat: root.hasReadout ? Notation.textFormat(root.readout.note || "") : Text.PlainText
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
            wrapMode: Text.WordWrap
        }

        RFStatusChip {
            visible: root.hasReadout && root.readout.stale === true
            text: "Stale — values of the last solved state"
            tone: "warning"
        }

        RFDivider { Layout.fillWidth: true; visible: root.hasReadout }

        Repeater {
            model: root.hasReadout ? root.readout.rows : []
            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: Metrics.spacing.m

                Text {
                    Layout.preferredWidth: 96
                    text: Notation.rich(modelData.label)
                    textFormat: Notation.textFormat(modelData.label)
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                }
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignRight
                    text: modelData.value
                    color: Theme.text
                    font.family: Typography.mono
                    font.pixelSize: Typography.readoutMedium
                }
                Text {
                    Layout.preferredWidth: 30
                    text: modelData.unit || ""
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: !root.hasReadout
            text: root.emptyHint
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
            wrapMode: Text.WordWrap
        }

        Item { Layout.fillHeight: true }

        RFDivider { Layout.fillWidth: true; visible: root.hasReadout }

        // Provenance: which solved state, which workspace, what the picture claims.
        Text {
            Layout.fillWidth: true
            visible: root.hasReadout
            text: root.hasReadout
                  ? root.sourceName + " · solved state #" + root.readout.identity
                    + (root.readout.fidelity ? "\n" + root.readout.fidelity : "")
                  : ""
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            wrapMode: Text.WordWrap
        }

        RFToolButton {
            visible: root.hasReadout
            text: "Clear selection"
            onClicked: root.clearRequested()
        }
    }
}
