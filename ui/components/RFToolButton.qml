import QtQuick
import "../theme"

/*
 * RFToolButton — a compact command for a context toolbar (3D view, plot).
 *
 * Text, not an icon, because the commands are words an engineer already
 * uses: ISO, Side, Fit, Cutaway, ROI. `checked` marks a mode that is on; the
 * button never flips it itself -- the owner decides what a click means, so
 * the state has exactly one writer.
 */
Rectangle {
    id: root

    property string text: ""
    property string tooltip: ""
    property bool checked: false
    property bool enabled: true

    signal clicked()

    activeFocusOnTab: root.enabled
    implicitHeight: Metrics.controlHeightSmall
    implicitWidth: Math.max(implicitHeight, label.implicitWidth + 2 * Metrics.spacing.s)
    radius: Metrics.radius.s
    color: root.checked ? Theme.accentSubtle
         : mouse.pressed ? Theme.surfaceHover
         : Theme.surface
    opacity: root.enabled ? 1 : 0.45

    Accessible.role: Accessible.Button
    Accessible.name: root.text
    Accessible.description: root.tooltip
    Accessible.checkable: root.checked
    Accessible.checked: root.checked

    RFProximityEdge { active: root.checked || root.activeFocus }

    Keys.onSpacePressed: if (root.enabled) root.clicked()
    Keys.onReturnPressed: if (root.enabled) root.clicked()

    Text {
        id: label
        anchors.centerIn: parent
        text: root.text
        color: root.checked ? Theme.accent : Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.weight: root.checked ? Typography.medium : Typography.regular
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        enabled: root.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    // Created only while the pointer is over the button: a tooltip is a
    // popup with its own text and transitions, and a toolbar of them built
    // up front is weight every page pays for nothing.
    Loader {
        anchors.fill: parent
        active: mouse.containsMouse && root.tooltip !== ""
        sourceComponent: RFTooltip {
            visible: true
            text: root.tooltip
        }
    }
}
