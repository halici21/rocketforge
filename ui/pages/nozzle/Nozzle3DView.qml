import QtQuick
import RocketForge 1.0

/*
 * Nozzle Lab's object in three dimensions -- the shared engineering viewport
 * (the one Rocket Performance uses) over the solved supplied cone: the
 * profile revolved, throat and exit rings, and the quasi-1D shock station
 * only while the solution has one. Labelled a supplied cone, because no
 * contour is designed here.
 *
 * Loaded only while shown and only where 3D can run. It draws
 * Nozzle.playbackViewport: the solved viewport itself, or -- while the
 * operating-state samples are stepping -- the same viewport with its shock
 * station taken from the sample shown. No sample is solved for it.
 */
Item {
    id: host

    property bool active: false
    readonly property bool loaded: loader.status === Loader.Ready
    property string selectedKey: ""

    signal stationPicked(string key)
    signal cleared()

    Loader {
        id: loader
        anchors.fill: parent
        active: host.active
        source: Qt.resolvedUrl("../../components/viewport/RFEngineeringViewport3D.qml")
        onLoaded: {
            item.objectName = "nozzleViewport3D"
            item.cutaway = true
            item.snapshot = Qt.binding(function () { return Nozzle.playbackViewport })
            item.stale = false
            item.emptyText = Qt.binding(function () {
                return Nozzle.statusMessage !== "" ? Nozzle.statusMessage
                                                   : "No solved nozzle to draw."
            })
            item.selectedKey = Qt.binding(function () { return host.selectedKey })
        }
    }

    Connections {
        target: loader.item
        ignoreUnknownSignals: true
        function onStationPicked(key, x, title) { host.stationPicked(key) }
        function onSelectionCleared() { host.cleared() }
    }
}
