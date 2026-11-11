import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * A small fixed table: column heads, then one row per model row. Cells are the
 * controller's text, unchanged. Every cell uses the same text colour: no
 * difference is styled by its size or sign (display review §6).
 */
ColumnLayout {
    id: root

    property var heads: []
    property var roles: []
    // Relative column widths; the cells fill the table's width in these shares.
    property var shares: []
    property var model: null

    spacing: Metrics.spacing.xs

    function widthOf(column) {
        var total = 0
        for (var i = 0; i < root.shares.length; ++i)
            total += root.shares[i]
        return total > 0 ? root.width * root.shares[column] / total : 0
    }

    Row {
        Layout.fillWidth: true
        Repeater {
            model: root.heads
            delegate: Text {
                required property int index
                required property string modelData
                width: root.widthOf(index)
                rightPadding: Metrics.spacing.s
                text: modelData
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.weight: Typography.medium
            }
        }
    }

    RFDivider { Layout.fillWidth: true }

    Repeater {
        model: root.model
        delegate: Row {
            id: tableRow
            // The model's own role values, by name: `model` is the row's role map.
            property var cells: model
            Layout.fillWidth: true

            Repeater {
                model: root.roles
                delegate: Text {
                    required property int index
                    required property string modelData
                    width: root.widthOf(index)
                    rightPadding: Metrics.spacing.s
                    topPadding: Metrics.spacing.xs
                    bottomPadding: Metrics.spacing.xs
                    text: tableRow.cells[modelData]
                    wrapMode: Text.WordWrap
                    color: index === 0 ? Theme.textSecondary : Theme.text
                    font.family: index === 0 ? Typography.sans : Typography.mono
                    font.pixelSize: Typography.bodySmall
                }
            }
        }
    }
}
