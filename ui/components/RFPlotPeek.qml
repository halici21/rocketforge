import QtQuick
import "../theme"

/*
 * RFPlotPeek — the shared plot peek/focus contract for small multiples.
 *
 *   near         the plot's edge lights (RFProximityEdge, as every control)
 *   rest ~280 ms  peek: the plot is outlined and its neighbours recede
 *                 (only with Settings > Plot hover preview On)
 *   click Focus  full focus in the owner's RFFocusOverlay, with the full
 *   or Return    analysis-lens tools
 *
 * A peek never starts while a button is held (a drag, a pan, a selection in
 * progress) and ends the moment the pointer leaves. Drop it last inside the
 * plot's panel; it takes no clicks of its own except its Focus button, so the
 * chart's own selection still works under it. Neighbours recede by binding
 * their opacity to `receded` through a shared `group`
 * (`QtObject { property Item current: null }`).
 */
Item {
    id: peek

    property QtObject group: null
    readonly property bool hovered: hover.hovered
    property bool peeking: false
    readonly property bool receded: peek.group !== null && peek.group.current !== null
                                    && peek.group.current !== peek

    signal focusRequested()

    anchors.fill: parent
    z: 5

    function endPeek() {
        dwell.stop()
        peek.peeking = false
    }

    onPeekingChanged: {
        if (peek.group === null)
            return
        if (peek.peeking)
            peek.group.current = peek
        else if (peek.group.current === peek)
            peek.group.current = null
    }
    Component.onDestruction: if (peek.group !== null && peek.group.current === peek) peek.group.current = null

    HoverHandler {
        id: hover
        onHoveredChanged: {
            if (hover.hovered)
                dwell.restart()
            else
                peek.endPeek()
        }
    }
    PointHandler {
        id: press
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
        onActiveChanged: if (press.active) peek.endPeek()
    }
    Timer {
        id: dwell
        interval: Motion.peekDwell
        onTriggered: {
            if (Motion.hoverPreview && hover.hovered && !press.active)
                peek.peeking = true
        }
    }

    // The peek: an outline, not a pop. The plot itself does not move.
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        radius: Metrics.radius.m
        border.width: 1
        border.color: Theme.accent
        opacity: peek.peeking ? 0.8 : 0
        Behavior on opacity { NumberAnimation { duration: Motion.fast } }
    }

    RFToolButton {
        objectName: "plotFocusButton"
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: Metrics.spacing.xs
        visible: peek.hovered || peek.peeking || activeFocus
        text: "Focus ⤢"
        tooltip: "Open this plot at full size with the analysis tools (Esc returns)"
        onClicked: peek.focusRequested()
    }
}
