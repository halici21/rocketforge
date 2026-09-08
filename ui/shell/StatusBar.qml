import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "../data"

/*
 * A single quiet line of context. Text separated by middots rather than a row
 * of chips: the state matters, but it is not the work.
 */
Item {
    id: root

    property var items: MockData.statusChips
    property string trailing: MockData.solverStatus
    // Whether the page currently shown computes its numbers. The status bar
    // used to state flatly that everything was mock data; that stopped being
    // true when the first analysis module was connected, and a status bar
    // that misreports the trustworthiness of what is on screen is worse than
    // no status bar at all.
    property bool computed: false
    // Where the numbers on screen came from. Overridable, because the default
    // is not true everywhere: the chemistry workspace's values are solved by
    // NASA CEA and then mapped and validated by RocketForge, and on a machine
    // with no provider it shows no values at all. A status bar that
    // misreports the origin of what is on screen is worse than no status bar.
    property string originNote: computed ? "Values computed by RocketForge"
                                         : "All values are mock data"

    implicitHeight: Metrics.statusBarHeight

    // Shell chrome sits one step off the workspace so the two read as
    // different layers without a border between them.
    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Metrics.spacing.m + Metrics.spacing.xs
        anchors.rightMargin: Metrics.spacing.m + Metrics.spacing.xs
        spacing: Metrics.spacing.s

        Repeater {
            model: root.items

            delegate: RowLayout {
                required property var modelData
                required property int index
                spacing: Metrics.spacing.s

                Text {
                    visible: index > 0
                    text: "·"
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.status
                }

                Rectangle {
                    visible: modelData.tone === "accent"
                    Layout.alignment: Qt.AlignVCenter
                    width: 5
                    height: 5
                    radius: 2.5
                    color: Theme.accent
                }

                Text {
                    text: modelData.label
                    color: modelData.tone === "accent" ? Theme.textSecondary : Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.status
                }
            }
        }

        Item { Layout.fillWidth: true }

        Text {
            text: root.trailing
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.status
        }

        Text {
            text: "·"
            color: Theme.textDisabled
            font.family: Typography.sans
            font.pixelSize: Typography.status
        }

        Text {
            text: root.originNote
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.status
        }

        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: Metrics.spacing.xs
            width: 5
            height: 5
            radius: 2.5
            color: Theme.warning
            opacity: 0.8
        }
    }
}
