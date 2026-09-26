import QtQuick
import "../theme"

/*
 * RFSectionTransition — a section switch that says which way it went.
 *
 * Placed beside a page's StackLayout, never inside it (a StackLayout's
 * children are its sections). When the stack's current index changes, the
 * section that arrives fades in over Motion.section and, in Full motion,
 * travels Motion.sectionShift pixels in from the side it came from: a tab to
 * the right arrives from the right. Opacity and a Translate only -- no
 * geometry, and nothing is created: a StackLayout keeps every section alive,
 * so a transition builds, destroys and solves nothing.
 *
 * Reduced motion: a shorter fade, no travel. Off: the switch is immediate.
 * A switch during a switch first snaps the arriving section to its final
 * state, so rapid switching always ends exactly where a slow one does.
 */
Item {
    id: root

    property Item stack: null
    // The section that is arriving, while it arrives.
    property Item arriving: null
    readonly property bool running: anim.running
    property int last: -1
    property bool shifted: false

    visible: false
    width: 0
    height: 0

    Translate { id: shift }

    function settle() {
        anim.stop()
        if (root.arriving !== null) {
            root.arriving.opacity = 1
            if (root.shifted)
                root.arriving.transform = []
        }
        shift.x = 0
        root.shifted = false
        root.arriving = null
    }

    function play() {
        var index = root.stack ? root.stack.currentIndex : -1
        var from = root.last
        root.last = index
        root.settle()
        if (from < 0 || index < 0 || from === index || Motion.section <= 0)
            return
        var item = index < root.stack.children.length ? root.stack.children[index] : null
        if (item === null)
            return
        root.arriving = item
        if (Motion.sectionShift > 0 && item.transform.length === 0) {
            shift.x = (index > from ? 1 : -1) * Motion.sectionShift
            item.transform = [shift]
            root.shifted = true
        }
        item.opacity = 0
        anim.restart()
    }

    ParallelAnimation {
        id: anim
        NumberAnimation {
            target: root.arriving
            property: "opacity"
            to: 1
            duration: Motion.section
            easing.type: Motion.standard
        }
        NumberAnimation {
            target: shift
            property: "x"
            to: 0
            duration: Motion.section
            easing.type: Motion.standard
        }
        onFinished: root.settle()
    }

    Connections {
        target: root.stack
        function onCurrentIndexChanged() { root.play() }
    }

    Component.onCompleted: root.last = root.stack ? root.stack.currentIndex : -1
}
