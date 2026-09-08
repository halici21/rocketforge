import QtQuick
import "../../theme"
import "../../data"

/*
 * The nozzle in section, drawn from the same hand-authored wall profile the
 * Nozzle Lab uses in analysis mode. Reusing the profile is the point: the two
 * modes are views of one product, not two products.
 *
 * The contour is a drawing. No area ratio, exit condition or contour
 * generation is computed here.
 */
Item {
    id: root

    property var contour: MockData.nozzleContour
    property real throatX: MockData.throatX

    readonly property real padLeft: 34
    readonly property real padRight: 34
    readonly property real innerWidth: Math.max(1, width - padLeft - padRight)

    function ax(fraction) { return padLeft + fraction * innerWidth }

    Canvas {
        id: drawing
        anchors.fill: parent
        antialiasing: true

        readonly property color wall: Theme.textSecondary
        readonly property color centre: Theme.border
        readonly property color fill: Theme.surfaceSunken
        readonly property color hot: Theme.accent

        onWallChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var pts = root.contour
            if (!pts || pts.length < 2)
                return

            var centreY = height / 2 + 4
            var maxRadius = height / 2 - 26

            function wallY(i, sign) {
                return centreY - sign * pts[i][1] * maxRadius
            }

            // Interior.
            ctx.beginPath()
            ctx.moveTo(root.ax(pts[0][0]), wallY(0, 1))
            var i
            for (i = 1; i < pts.length; ++i)
                ctx.lineTo(root.ax(pts[i][0]), wallY(i, 1))
            for (i = pts.length - 1; i >= 0; --i)
                ctx.lineTo(root.ax(pts[i][0]), wallY(i, -1))
            ctx.closePath()
            ctx.fillStyle = fill
            ctx.fill()

            var wash = ctx.createLinearGradient(root.ax(0), 0, root.ax(1), 0)
            wash.addColorStop(0, Qt.rgba(hot.r, hot.g, hot.b, 0.07))
            wash.addColorStop(1, Qt.rgba(hot.r, hot.g, hot.b, 0.01))
            ctx.fillStyle = wash
            ctx.fill()

            // Centreline.
            ctx.strokeStyle = centre
            ctx.lineWidth = 1
            ctx.setLineDash([5, 5])
            ctx.beginPath()
            ctx.moveTo(root.ax(0), centreY)
            ctx.lineTo(root.ax(1), centreY)
            ctx.stroke()
            ctx.setLineDash([])

            // Walls.
            ctx.strokeStyle = wall
            ctx.lineWidth = 1.7
            ctx.lineJoin = "round"
            for (var s = 1; s >= -1; s -= 2) {
                ctx.beginPath()
                ctx.moveTo(root.ax(pts[0][0]), wallY(0, s))
                for (i = 1; i < pts.length; ++i)
                    ctx.lineTo(root.ax(pts[i][0]), wallY(i, s))
                ctx.stroke()
            }
        }
    }

    // ---- station markers -------------------------------------------------

    Repeater {
        model: [
            { fraction: 0.06, label: "Chamber" },
            { fraction: root.throatX, label: "Throat" },
            { fraction: 0.995, label: "Exit" }
        ]

        delegate: Item {
            required property var modelData

            x: root.ax(modelData.fraction)
            y: 0
            width: 1
            height: root.height

            Rectangle {
                width: Metrics.hairline
                height: parent.height - 30
                y: 14
                color: Theme.divider
                visible: modelData.label !== "Chamber"
            }

            Text {
                x: modelData.fraction > 0.9 ? -implicitWidth - 4
                                            : (modelData.fraction < 0.2 ? 0 : 5)
                y: 0
                text: modelData.label
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.letterSpacing: 0.5
                font.capitalization: Font.AllUppercase
            }
        }
    }

    // Sonic mark at the throat.
    Rectangle {
        x: root.ax(root.throatX) - 3
        y: root.height / 2 + 1
        width: 6
        height: 6
        radius: 1
        rotation: 45
        color: Theme.accent
    }
}
