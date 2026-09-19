import QtQuick
import "../theme"
import "../data"

/*
 * Holds the current module page. One page is instantiated at a time, and each
 * arrival is a short rise and fade - enough to register that the workspace
 * changed, short enough not to be waited on.
 */
Item {
    id: root

    property int currentIndex: 0

    // Bubbled from whichever page is loaded, when it has one -- today only
    // HomePage.qml requests navigation of its own accord. A generic
    // pass-through rather than special-casing Home by name, so a future
    // workspace overview page needs no change here.
    signal workspaceRequested(int index)
    signal engineRequested()

    Loader {
        id: loader
        width: root.width
        height: root.height
        source: Qt.resolvedUrl("../pages/" + Navigation.pageSource(root.currentIndex))
        onLoaded: enter.restart()
    }

    Connections {
        target: loader.item
        ignoreUnknownSignals: true
        function onWorkspaceRequested(index) { root.workspaceRequested(index) }
        function onEngineRequested() { root.engineRequested() }
    }

    ParallelAnimation {
        id: enter

        NumberAnimation {
            target: loader
            property: "opacity"
            from: 0
            to: 1
            duration: Motion.base
            easing.type: Motion.standard
        }
        NumberAnimation {
            target: loader
            property: "y"
            from: 6
            to: 0
            duration: Motion.slow
            easing.type: Motion.standard
        }
    }
}
