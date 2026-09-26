import QtQuick
import RocketForge 1.0
import "../theme"
import "../components"
import "../data"
import "../pages/tradestudy"

/*
 * The contextual Inspector's content, for whichever workspace is open.
 *
 * One shell drawer (InspectorDrawer), one content per workspace: Trade Study
 * keeps its own study inspector; Nozzle Lab and Isentropic show the shared
 * selection readout their controllers publish. A workspace that has no
 * inspector never opens the drawer.
 */
Item {
    id: root

    readonly property string pageKey: {
        var i = ShellContext.currentPageIndex
        return i >= 0 && i < Navigation.items.length ? Navigation.items[i].key : ""
    }

    signal closeRequested()

    Loader {
        anchors.fill: parent
        sourceComponent: root.pageKey === "tradestudy" ? study
                       : root.pageKey === "nozzlelab" ? nozzle
                       : root.pageKey === "isentropic" ? isentropic
                       : null
    }

    Component { id: study; StudyInspector {} }

    Component {
        id: nozzle
        RFInspectorPanel {
            objectName: "nozzleInspector"
            readout: Nozzle.selectionReadout
            sourceName: "Nozzle Lab"
            emptyHint: "Select a station on the drawing or on a chart: "
                       + "throat, shock or exit."
            onClearRequested: Nozzle.selection.clear()
            onCloseRequested: root.closeRequested()
        }
    }

    Component {
        id: isentropic
        RFInspectorPanel {
            objectName: "isentropicInspector"
            readout: Isentropic.selectionReadout
            sourceName: "Isentropic Flow"
            emptyHint: "Click a point on the curve, or a row of the table, to inspect it."
            onClearRequested: Isentropic.selection.clear()
            onCloseRequested: root.closeRequested()
        }
    }
}
