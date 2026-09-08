import QtQuick
import QtQuick.Layouts
import "../../theme"

/*
 * The exit-plane / ambient relation, and the exit state beside it.
 *
 * A restrained engineering indicator rather than a plume: it states the regime
 * in words, shows the sign of the pressure contribution as a character, and
 * lists the solved exit state. Nothing here is a CFD result and nothing
 * pretends to be one.
 */
ColumnLayout {
    id: root

    property string regimeLabel: ""
    property int sign: 0
    property string relationText: ""
    property string ambientLabel: ""
    // A stable row model, not a list -- see QML_MEMORY_ROOT_CAUSE.md.
    property var exitModel: null
    property bool stale: false

    spacing: Metrics.spacing.xs

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.m

        Text {
            text: root.regimeLabel
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.groupLabel
            font.weight: Typography.medium
        }

        Text {
            text: root.relationText
            color: Theme.textMuted
            font.family: Typography.mono
            font.pixelSize: Typography.meta
        }

        Text {
            text: root.ambientLabel
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        Item { Layout.fillWidth: true }
    }

    Flow {
        Layout.fillWidth: true
        spacing: Metrics.spacing.l

        Repeater {
            model: root.exitModel
            delegate: Row {
                id: exitItem
                required property string symbol
                required property string value
                required property string unit
                spacing: Metrics.spacing.xs

                Text {
                    text: exitItem.symbol
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    font.letterSpacing: Typography.sectionTracking
                }
                // The exit state is solved physics, not a footnote: its
                // values sit one step above their own symbols and units.
                Text {
                    text: exitItem.value
                    // Dimmed, not made illegible: staleness is carried by the
                    // chip and the header, and this is still the last
                    // value that was actually solved.
                    color: root.stale ? Theme.textMuted
                                      : Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.bodySmall
                }
                Text {
                    text: exitItem.unit
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }
}
