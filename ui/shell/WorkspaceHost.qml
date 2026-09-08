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

    Loader {
        id: loader
        width: root.width
        height: root.height
        source: Qt.resolvedUrl("../pages/" + Navigation.pageSource(root.currentIndex))
        onLoaded: enter.restart()
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
