import QtQuick
import "../../theme"
import ".."

/*
 * RFViewSwitch — the 2D engineering view or the 3D view of the same object.
 *
 * The 2D view stays the precision surface; 3D adds spatial understanding.
 * Where 3D cannot run -- Qt Quick 3D not installed, or a window rendered by
 * the software renderer -- the 3D choice is disabled and says why.
 */
RFSegmentedControl {
    id: control

    property string mode: "2d"
    property string flatLabel: "2D"
    readonly property bool threeDAvailable: avail.available
    readonly property string unavailableReason: avail.reason
    readonly property bool show3D: control.mode === "3d" && avail.available

    signal modeRequested(string mode)

    implicitWidth: 220
    model: [control.flatLabel, "3D view"]
    currentIndex: control.show3D ? 1 : 0
    disabledIndices: avail.available ? [] : [1]
    disabledNote: avail.reason
    onSelected: function (index) { control.modeRequested(index === 1 ? "3d" : "2d") }

    RFViewportAvailability { id: avail }
}
