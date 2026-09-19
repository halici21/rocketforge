import QtQuick
import "../theme"
import "../components"

/*
 * The contextual Inspector -- on demand, never permanently visible.
 *
 * Per the shell-prototype decision (docs/design/CAD_WORKBENCH_R1_DESIGN_DECISION.md),
 * the accepted shell direction deliberately does NOT give every workspace a
 * persistent Inspector: the accepted Rocket Performance pilot's own result
 * rail already carries that role for its own workspace, and forcing a
 * second, permanent panel next to it would duplicate work and cost
 * viewport width for nothing. This component exists so a *future*
 * workspace whose own audit calls for one has real shell infrastructure to
 * open into, without every workspace paying its width cost by default.
 *
 * Loader-instantiated, lazily: nothing is created until the drawer opens
 * for the first time (`active: root.open || loader.item !== null`), so a
 * workspace that never opens it never pays for a live item tree -- this is
 * the "on-demand" reading of the brief's "not permanently visible"
 * instruction, not merely visually hidden. Once opened, the item is kept
 * (not destroyed on every close) deliberately: `active: root.open` alone
 * would destroy the item the instant `open` goes false, and a destroyed
 * item cannot run the closing slide -- `Behavior on x` would have nothing
 * left to animate. Keeping it after first use is the same one-time-cost
 * trade a popup/settings-panel component makes everywhere else in Qt.
 */
Item {
    id: root

    property bool open: false
    property real drawerWidth: Metrics.inspectorWidth
    default property alias content: loader.sourceComponent

    signal closeRequested()

    implicitWidth: 0
    clip: false

    Loader {
        id: loader
        active: root.open || item !== null
        width: root.drawerWidth
        height: root.height
        x: root.open ? root.width - root.drawerWidth : root.width
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Behavior on x {
            NumberAnimation { duration: Motion.base; easing.type: Motion.emphasized }
        }
    }

    // Scrim: click-away closes the drawer without a modal block on the
    // rest of the workspace -- the drawer is a contextual look-up, not a
    // dialog the user must dismiss before continuing.
    MouseArea {
        anchors.fill: parent
        anchors.rightMargin: root.drawerWidth
        visible: root.open
        onClicked: root.closeRequested()
    }

    Rectangle {
        anchors.top: loader.top
        anchors.bottom: loader.bottom
        anchors.left: loader.left
        width: Metrics.hairline
        color: Theme.border
        visible: root.open
    }

    Rectangle {
        anchors.left: loader.left
        anchors.right: loader.right
        anchors.top: loader.top
        anchors.bottom: loader.bottom
        color: Theme.surfaceSubtle
        visible: root.open
        z: -1
    }
}
