import QtQuick
import QtQuick.Layouts
import "../../theme"

/*
 * One engineering readout in the result rail.
 *
 * The grammar the visual pilot introduces, and the reason there are no KPI
 * cards: a micro label, a large monospace number with a subordinate unit, and
 * a quiet name beneath. Hierarchy comes from type size and weight, not from a
 * rounded rectangle around each value.
 *
 * `primary` raises one readout above its neighbours. It is used sparingly --
 * specific impulse, and total thrust when an engine size exists.
 */
ColumnLayout {
    id: root

    property string symbol: ""
    property string value: ""
    property string unit: ""
    property string label: ""
    property bool primary: false
    property bool stale: false

    spacing: 1

    Text {
        Layout.fillWidth: true
        text: root.symbol
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.sectionLabel
        font.letterSpacing: Typography.sectionTracking
        font.weight: Typography.medium
        elide: Text.ElideRight
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 5

        Text {
            // A stale value is the last one that was actually solved, so it
            // is dimmed and not hidden. textDisabled measured 2.43:1 against
            // the page, which is not a readable number by any standard.
            text: root.value
            color: root.stale ? Theme.textMuted
                              : (root.primary ? Theme.text : Theme.textSecondary)
            font.family: Typography.mono
            font.pixelSize: root.primary ? Typography.readoutLarge * 1.5
                                         : Typography.readoutLarge
            font.weight: root.primary ? Typography.medium : Typography.regular

            Behavior on color {
                ColorAnimation { duration: Motion.base }
            }
        }

        Text {
            Layout.alignment: Qt.AlignBottom
            Layout.bottomMargin: root.primary ? 5 : 3
            visible: root.unit !== ""
            text: root.unit
            color: Theme.textSecondary
            font.family: Typography.mono
            font.pixelSize: Typography.readoutSmall
        }

        Item { Layout.fillWidth: true }
    }

    Text {
        Layout.fillWidth: true
        text: root.label
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.bodySmall
        elide: Text.ElideRight
    }
}
