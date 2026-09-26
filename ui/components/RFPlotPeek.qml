import QtQuick
import "../theme"

/*
 * RFPlotPeek — the shared plot peek/focus contract for small multiples.
 *
 * Three levels:
 *
 *   TILE   the plot in its place in the overview
 *   PEEK   rest the pointer on it for Motion.peekDwell (280 ms): the plot
 *          itself -- the same item, the same series, re-rendered sharp at the
 *          larger size -- is lifted onto the owner's stage at about 1.35x
 *          its tile, anchored at the tile and biased inward so it never runs
 *          off the plot area. Its neighbours recede (45 %). The overview does
 *          not move: the tile's slot stays in the layout, outlined, so the
 *          enlarged plot still reads as "this tile, closer".
 *   FOCUS  the Focus button (on the tile or on the peek), or Return on it:
 *          the owner's RFFocusOverlay with the full analysis tools.
 *
 * Presentation only. Nothing is copied or resampled: the owner's `content`
 * (the tile's panel) is reparented into one reusable frame, built on the
 * first peek and kept, and handed back to the tile when the peek ends. No
 * object is created per hover.
 *
 * A peek never starts, and does not stay, while a button is held on the
 * tile or on the peek (a pan, a zoom, a selection, a drag). It needs
 * Settings > Plot hover preview On; with it Off the Focus button still
 * works. Motion: the enlargement eases in over Motion.focus and out over
 * Motion.fast; with motion Off it appears and goes at once.
 *
 * Owners give: `content` (the item to lift, filling the tile), `stage` (an
 * ancestor the peek may draw on) and `area` (the region it must stay inside,
 * e.g. the grid of plots). Without them the peek only outlines the tile.
 */
Item {
    id: peek

    property QtObject group: null
    property Item content: null
    property Item stage: null
    property Item area: null
    // the enlargement, before it is clamped to the area
    property real peekScale: 1.35

    readonly property bool hovered: hover.hovered || (frameLoader.item !== null && frameLoader.item.hovered)
    property bool peeking: false
    readonly property bool lifted: peek.peeking && frameLoader.item !== null && peek.canLift
    readonly property bool canLift: peek.content !== null && peek.stage !== null
    readonly property bool receded: peek.group !== null && peek.group.current !== null
                                    && peek.group.current !== peek

    signal focusRequested()

    anchors.fill: parent
    z: 5

    function endPeek(animated) {
        dwell.stop()
        if (!peek.peeking)
            return
        peek.peeking = false
        if (frameLoader.item !== null)
            frameLoader.item.close(animated === undefined ? true : animated)
    }
    function startPeek() {
        if (!Motion.hoverPreview || press.active || peek.peeking)
            return
        peek.peeking = true
        if (peek.canLift) {
            frameLoader.active = true                // built once, then kept
            frameLoader.item.open()
        }
    }
    // Focus from the tile or from the peek: straight on, no collapse first.
    function requestFocus() {
        peek.endPeek(false)
        peek.focusRequested()
    }

    onPeekingChanged: {
        if (peek.group === null)
            return
        if (peek.peeking)
            peek.group.current = peek
        else if (peek.group.current === peek)
            peek.group.current = null
    }
    Component.onDestruction: {
        if (peek.group !== null && peek.group.current === peek)
            peek.group.current = null
    }
    Connections {
        target: Motion
        function onHoverPreviewChanged() { if (!Motion.hoverPreview) peek.endPeek(false) }
    }

    // Leaving the tile and the peek ends it; checked a turn later so the
    // pointer can cross from the tile onto the enlarged plot.
    function checkLeave() {
        Qt.callLater(function () {
            if (peek.peeking && !peek.hovered)
                peek.endPeek(true)
        })
    }

    HoverHandler {
        id: hover
        onHoveredChanged: {
            if (hover.hovered && !peek.peeking)
                dwell.restart()
            else if (!hover.hovered) {
                dwell.stop()
                peek.checkLeave()
            }
        }
    }
    PointHandler {
        id: press
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
        onActiveChanged: if (press.active) peek.endPeek(false)
    }
    Timer {
        id: dwell
        interval: Motion.peekDwell
        onTriggered: {
            if (hover.hovered && !press.active)
                peek.startPeek()
        }
    }

    // The tile's slot while its plot is lifted: an outline, so the peek
    // stays visibly tied to where it came from.
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        radius: Metrics.radius.m
        border.width: 1
        border.color: Theme.accent
        opacity: peek.peeking ? 0.8 : 0
        Behavior on opacity { NumberAnimation { duration: Motion.fast } }
    }

    // Bottom-right: the panel's own header (title, qualifier chip) stays clear.
    RFToolButton {
        objectName: "plotFocusButton"
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: Metrics.spacing.xs
        visible: !peek.lifted && (hover.hovered || peek.peeking || activeFocus)
        text: "Focus ⤢"
        tooltip: "Open this plot at full size with the analysis tools (Esc returns)"
        onClicked: peek.requestFocus()
    }

    // ---- the peek surface: one frame, built on the first peek, reused ------
    Loader {
        id: frameLoader
        active: false
        sourceComponent: Item {
            id: frame
            objectName: "plotPeekFrame"
            parent: peek.stage
            z: 30
            visible: frame.shown || grow.running || shrink.running

            property bool shown: false
            readonly property bool hovered: frameHover.hovered
            property real arrive: 0
            // the tile and the peek rectangles, in stage coordinates
            property rect tileRect: Qt.rect(0, 0, 0, 0)
            property rect peekRect: Qt.rect(0, 0, 0, 0)

            function place() {
                var tile = peek.mapToItem(peek.stage, 0, 0, peek.width, peek.height)
                var box = peek.area !== null
                          ? peek.area.mapToItem(peek.stage, 0, 0, peek.area.width, peek.area.height)
                          : Qt.rect(0, 0, peek.stage.width, peek.stage.height)
                // only the part of the area that is on the stage (an area can
                // run past it -- a one-column overview at 1366 with the
                // inspector open)
                var bx0 = Math.max(box.x, 0), by0 = Math.max(box.y, 0)
                var bx1 = Math.min(box.x + box.width, peek.stage.width)
                var by1 = Math.min(box.y + box.height, peek.stage.height)
                box = Qt.rect(bx0, by0, Math.max(0, bx1 - bx0), Math.max(0, by1 - by0))
                var w = Math.min(tile.width * peek.peekScale, box.width)
                var h = Math.min(tile.height * peek.peekScale, box.height)
                // grow about the tile's centre, then pull back inside the area
                var x = tile.x + tile.width / 2 - w / 2
                var y = tile.y + tile.height / 2 - h / 2
                x = Math.max(box.x, Math.min(x, box.x + box.width - w))
                y = Math.max(box.y, Math.min(y, box.y + box.height - h))
                frame.tileRect = tile
                frame.peekRect = Qt.rect(x, y, w, h)
            }
            function open() {
                shrink.stop()
                // Loader parents its item to itself; the peek draws on the stage
                if (frame.parent !== peek.stage)
                    frame.parent = peek.stage
                frame.place()
                frame.x = frame.peekRect.x
                frame.y = frame.peekRect.y
                frame.width = frame.peekRect.width
                frame.height = frame.peekRect.height
                // the plot itself moves up here; the tile keeps its slot
                if (peek.content.parent !== inner) {
                    peek.content.anchors.fill = undefined
                    peek.content.parent = inner
                    peek.content.anchors.fill = inner
                }
                frame.shown = true
                if (Motion.animated) {
                    frame.arrive = 0
                    grow.restart()
                } else {
                    frame.arrive = 1
                }
            }
            function close(animated) {
                grow.stop()
                frame.shown = false
                if (animated && Motion.animated)
                    shrink.restart()
                else
                    frame.handBack()
            }
            function handBack() {
                frame.arrive = 0
                if (peek.content !== null && peek.content.parent === inner) {
                    peek.content.anchors.fill = undefined
                    peek.content.parent = peek.parent
                    peek.content.anchors.fill = peek.parent
                }
            }

            NumberAnimation {
                id: grow
                target: frame; property: "arrive"; to: 1
                duration: Motion.focus; easing.type: Motion.standard
            }
            NumberAnimation {
                id: shrink
                target: frame; property: "arrive"; to: 0
                duration: Motion.fast; easing.type: Easing.InCubic
                onFinished: if (!frame.shown) frame.handBack()
            }

            // From the tile's footprint to the peek's: a scale about the
            // point where the two rectangles meet, and a fade. The plot is
            // laid out once, at the peek size, so it is sharp when it lands.
            transform: Scale {
                origin.x: frame.peekRect.width > 0 ? (frame.tileRect.x + frame.tileRect.width / 2 - frame.peekRect.x) : 0
                origin.y: frame.peekRect.height > 0 ? (frame.tileRect.y + frame.tileRect.height / 2 - frame.peekRect.y) : 0
                readonly property real sx: frame.peekRect.width > 0 ? frame.tileRect.width / frame.peekRect.width : 1
                readonly property real sy: frame.peekRect.height > 0 ? frame.tileRect.height / frame.peekRect.height : 1
                xScale: sx + (1 - sx) * frame.arrive
                yScale: sy + (1 - sy) * frame.arrive
            }
            opacity: 0.6 + 0.4 * frame.arrive

            Rectangle {
                anchors.fill: parent
                radius: Metrics.radius.m
                color: Theme.surface
                border.width: 1
                border.color: Theme.accent
            }
            Item {
                id: inner
                anchors.fill: parent
                anchors.margins: 1
            }

            HoverHandler {
                id: frameHover
                onHoveredChanged: if (!frameHover.hovered) peek.checkLeave()
            }
            PointHandler {
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
                // a press on the plot (a pan, a drag, a selection) ends the
                // peek; the Focus button's own press does not
                onActiveChanged: if (active && !focusHover.hovered) Qt.callLater(function () { peek.endPeek(false) })
            }

            RFToolButton {
                objectName: "plotPeekFocusButton"
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.margins: Metrics.spacing.xs
                z: 2
                text: "Focus ⤢"
                tooltip: "Open this plot at full size with the analysis tools (Esc returns)"
                onClicked: peek.requestFocus()
                HoverHandler { id: focusHover }
            }
        }
    }
}
