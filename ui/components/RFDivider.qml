import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * A hairline separator. Thin enough to organise without drawing a box.
 * Fills its layout cell along its long axis so call sites stay quiet.
 */
Rectangle {
    property bool vertical: false

    implicitWidth: vertical ? Metrics.hairline : 0
    implicitHeight: vertical ? 0 : Metrics.hairline
    Layout.fillWidth: !vertical
    Layout.fillHeight: vertical
    color: Theme.divider

    Behavior on color {
        ColorAnimation { duration: Motion.fast }
    }
}
