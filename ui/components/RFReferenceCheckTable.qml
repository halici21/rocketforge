import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * RFReferenceCheckTable - a calculator's published-reference check, row by
 * row: column headings, then one row per quantity with the calculated value,
 * the published one, their difference and a PASS / REVIEW chip.
 *
 * `rows` comes from the controller unchanged (label, computed, reference,
 * difference, status); nothing here compares or rounds. Used by the
 * Isentropic and Normal Shock calculators, which show it when the check is
 * open and their state has a published row.
 */
ColumnLayout {
    id: root

    property var rows: []

    spacing: Metrics.spacing.xs

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.m

        Repeater {
            model: [
                { text: "Quantity", width: 70 },
                { text: "Calculated", width: 120 },
                { text: "Published", width: 120 },
                { text: "Difference", width: -1 },
                { text: "Status", width: 54 }
            ]
            delegate: Text {
                required property var modelData
                Layout.preferredWidth: modelData.width
                Layout.fillWidth: modelData.width < 0
                text: modelData.text
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }

    Repeater {
        model: root.rows

        delegate: RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: Metrics.spacing.m

            Text {
                Layout.preferredWidth: 70
                text: Notation.rich(modelData.label)
                textFormat: Notation.textFormat(modelData.label)
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
            Text {
                Layout.preferredWidth: 120
                text: modelData.computed
                color: Theme.text
                font.family: Typography.mono
                font.pixelSize: Typography.bodySmall
            }
            Text {
                Layout.preferredWidth: 120
                text: modelData.reference
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.bodySmall
            }
            Text {
                Layout.fillWidth: true
                text: modelData.difference
                color: Theme.textMuted
                font.family: Typography.mono
                font.pixelSize: Typography.bodySmall
            }
            RFStatusChip {
                Layout.preferredWidth: 54
                text: modelData.status
                tone: modelData.status === "PASS" ? "success" : "warning"
                showDot: false
            }
        }
    }
}
