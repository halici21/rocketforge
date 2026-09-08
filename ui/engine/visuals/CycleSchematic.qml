import QtQuick
import "../../theme"

/*
 * A thumbnail of an engine cycle: boxes on a coarse grid with links between
 * them. Enough to recognise a gas generator from a staged combustion cycle at
 * a glance, and nothing more - it is a picture of an architecture, not a model
 * of one.
 */
Item {
    id: root

    property var boxes: []
    property var links: []

    readonly property real boxWidth: 46
    readonly property real boxHeight: 20
    readonly property real colStep: 62
    readonly property real rowStep: 30

    readonly property real maxCol: {
        var m = 0
        for (var i = 0; i < boxes.length; ++i)
            m = Math.max(m, boxes[i].col)
        return m
    }
    readonly property real maxRow: {
        var m = 0
        for (var i = 0; i < boxes.length; ++i)
            m = Math.max(m, boxes[i].row)
        return m
    }

    readonly property real contentWidth: maxCol * colStep + boxWidth
    readonly property real contentHeight: maxRow * rowStep + boxHeight
    readonly property real originX: (width - contentWidth) / 2
    readonly property real originY: (height - contentHeight) / 2

    function boxX(box) { return originX + box.col * colStep }
    function boxY(box) { return originY + box.row * rowStep }

    Canvas {
        id: drawing
        anchors.fill: parent
        antialiasing: true

        readonly property color lineColor: Theme.border
        readonly property color boxColor: Theme.surfaceSubtle
        readonly property color boxBorder: Theme.borderStrong

        onLineColorChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        Connections {
            target: root
            function onBoxesChanged() { drawing.requestPaint() }
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (!root.boxes || root.boxes.length === 0)
                return

            // Links first, so boxes sit on top of them.
            ctx.strokeStyle = lineColor
            ctx.lineWidth = 1.2
            for (var i = 0; i < root.links.length; ++i) {
                var a = root.boxes[root.links[i][0]]
                var b = root.boxes[root.links[i][1]]
                if (!a || !b)
                    continue
                var ax = root.boxX(a) + root.boxWidth
                var ay = root.boxY(a) + root.boxHeight / 2
                var bx = root.boxX(b)
                var by = root.boxY(b) + root.boxHeight / 2
                var mid = (ax + bx) / 2
                ctx.beginPath()
                ctx.moveTo(ax, ay)
                ctx.lineTo(mid, ay)
                ctx.lineTo(mid, by)
                ctx.lineTo(bx, by)
                ctx.stroke()
            }

            ctx.fillStyle = boxColor
            ctx.strokeStyle = boxBorder
            for (var j = 0; j < root.boxes.length; ++j) {
                var box = root.boxes[j]
                var x = root.boxX(box)
                var y = root.boxY(box)
                ctx.beginPath()
                ctx.roundedRect(x, y, root.boxWidth, root.boxHeight, 4, 4)
                ctx.fill()
                ctx.stroke()
            }
        }
    }

    Repeater {
        model: root.boxes

        delegate: Text {
            required property var modelData
            x: root.boxX(modelData)
            y: root.boxY(modelData)
            width: root.boxWidth
            height: root.boxHeight
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: modelData.label
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
