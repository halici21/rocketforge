import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "../data"
import "../pages/tradestudy"
import "../pages/thermochemistry"

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
                       : root.pageKey === "thermochem" ? sweepPoint
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

    // A sweep point, read from the solved sweep record (Thermochemistry
    // .sweepPoint): the O/F solved, the state it gave, its own diagnostics.
    Component {
        id: sweepPoint
        Item {
            id: sweepHost
            objectName: "sweepInspector"
            readonly property int row: Thermochemistry.sweepSelection.kind === "tableRow"
                                       ? parseInt(Thermochemistry.sweepSelection.key) : -1

            RFToolButton {
                id: sweepClose
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.margins: Metrics.spacing.m
                text: "Close"
                onClicked: root.closeRequested()
            }
            Text {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: Metrics.spacing.m
                anchors.topMargin: Metrics.spacing.m + 4
                text: "INSPECTOR  ·  O/F SWEEP"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.letterSpacing: Typography.sectionTracking
            }
            Flickable {
                anchors.top: sweepClose.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: Metrics.spacing.m
                contentWidth: width
                contentHeight: pointColumn.implicitHeight
                clip: true
                ColumnLayout {
                    id: pointColumn
                    width: parent.width
                    spacing: Metrics.spacing.s
                    ThermoSweepPoint {
                        Layout.fillWidth: true
                        row: sweepHost.row
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: sweepHost.row < 0
                        text: "Click a point on a sweep plot, or a row of Sweep data, to inspect it."
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                    RFToolButton {
                        visible: sweepHost.row >= 0
                        text: "Clear selection"
                        onClicked: Thermochemistry.sweepSelection.clear()
                    }
                }
            }
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
