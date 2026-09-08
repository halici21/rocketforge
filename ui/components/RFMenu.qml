import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * A popup surface for menus and small settings panels. Uses the elevated
 * surface plus one hairline - elevation is a colour step here, not a shadow.
 */
Popup {
    id: root

    property real cornerRadius: Metrics.radius.xl
    // Context menus opened over a large surface must close on any outside
    // press; a menu anchored to its own button closes on leaving that button.
    property bool dismissOnAnyOutsidePress: false

    padding: Metrics.spacing.xs + 2
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | (dismissOnAnyOutsidePress
                                        ? Popup.CloseOnPressOutside
                                        : Popup.CloseOnPressOutsideParent)

    background: Rectangle {
        color: Theme.surfaceElevated
        radius: root.cornerRadius
        border.width: Metrics.hairline
        border.color: Theme.border
    }

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Motion.fast }
            NumberAnimation { property: "y"; from: root.y - 4; to: root.y; duration: Motion.base; easing.type: Motion.standard }
        }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Motion.fast }
    }
}
