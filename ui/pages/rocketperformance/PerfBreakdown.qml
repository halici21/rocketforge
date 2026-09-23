import QtQuick
import QtQuick.Layouts
import "../../theme"

/*
 * A two-term breakdown under a headline readout: momentum and pressure.
 *
 * The pressure term carries its sign as a **character**, not as a colour, so a
 * negative contribution is legible without relying on hue. An overexpanded
 * nozzle is an ordinary engineering situation and is not styled as an alarm.
 */
ColumnLayout {
    id: root

    property string title: ""
    // A stable row model, not a list: a QVariantList re-read on every
    // publication retains memory neither collector reclaims. See
    // docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md.
    property var rowModel: null
    property bool stale: false

    spacing: 2

    Text {
        Layout.fillWidth: true
        text: Notation.rich(root.title)
        textFormat: Notation.textFormat(root.title)
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.sectionLabel
        font.letterSpacing: Typography.sectionTracking
        font.weight: Typography.medium
    }

    Repeater {
        model: root.rowModel
        delegate: RowLayout {
            id: term
            required property string label
            required property string sign
            required property string value
            Layout.fillWidth: true
            spacing: Metrics.spacing.xs

            Text {
                Layout.fillWidth: true
                text: Notation.rich(term.label)
                textFormat: Notation.textFormat(term.label)
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
                elide: Text.ElideRight
                clip: true              // RichText does not elide
            }
            Text {
                text: term.sign
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }
            Text {
                text: term.value
                // Dimmed, not made illegible: staleness is carried by the
                // chip and the header, and this is still the last
                // value that was actually solved.
                color: root.stale ? Theme.textMuted
                                  : Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }
        }
    }
}
