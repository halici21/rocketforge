import QtQuick
import RocketForge 1.0

/*
 * The solved expansion in three dimensions -- the same schematic the 2D
 * canvas draws, revolved: a fixed exit radius with the throat set by the
 * solved area ratio. Labelled schematic, because no contour is solved.
 *
 * Loaded only while shown and only where 3D can run. It draws the result's
 * own snapshot (RocketPerformance.viewport), so an edited input marks it
 * stale rather than reshaping it, and a superseded chamber is said so.
 * Flow cues: gas through the nozzle; liquid feed at the chamber face when
 * the reactants are liquids. No spray, no droplets, no combustion zone.
 */
Item {
    id: host

    property bool active: false
    readonly property bool loaded: loader.status === Loader.Ready
    property string selectedKey: ""

    Loader {
        id: loader
        anchors.fill: parent
        active: host.active
        source: Qt.resolvedUrl("../../components/viewport/RFEngineeringViewport3D.qml")
        onLoaded: {
            item.objectName = "performanceViewport3D"
            // Opened as a cutaway: the axis, the stations and the flow cues
            // inside the wall are the reason to look in 3D.
            item.cutaway = true
            item.snapshot = Qt.binding(function () { return RocketPerformance.viewport })
            item.stale = Qt.binding(function () {
                return RocketPerformance.resultStale || RocketPerformance.chamberSuperseded
            })
            item.staleText = Qt.binding(function () {
                return RocketPerformance.chamberSuperseded
                       ? "Superseded chamber — showing the result it produced"
                       : "Stale — showing the last solved state; recalculate"
            })
            item.emptyText = Qt.binding(function () {
                return RocketPerformance.message !== "" ? RocketPerformance.message
                       : RocketPerformance.hasChamber
                         ? "Calculate to draw the solved expansion in 3D."
                         : "No chamber state yet — nothing is drawn until one is solved and expanded."
            })
            item.selectedKey = Qt.binding(function () { return host.selectedKey })
        }
    }

    Connections {
        target: loader.item
        ignoreUnknownSignals: true
        function onStationPicked(key, x, title) { host.selectedKey = key }
        function onSelectionCleared() { host.selectedKey = "" }
    }
}
