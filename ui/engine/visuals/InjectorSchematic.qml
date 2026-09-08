import QtQuick
import "../../theme"
import "../model"

/*
 * A pintle injector in section: oxidiser down the central post, fuel through
 * the surrounding annulus, both meeting at the tip. Drawn rather than
 * illustrated, so it recolours with the theme and can later be driven by the
 * real geometry instead of by fixed proportions.
 *
 * The proportions are a drawing. Nothing here is dimensioned from the inputs
 * and nothing is computed.
 */
Item {
    id: root

    readonly property real viewWidth: 260
    readonly property real viewHeight: 200
    readonly property real scaleFactor: Math.min(width / viewWidth, height / viewHeight)
    readonly property real originX: (width - viewWidth * scaleFactor) / 2
    readonly property real originY: (height - viewHeight * scaleFactor) / 2

    /* Line weight is deliberately not tied to the drawing scale. Once the
     * workspace gives this panel most of the page the drawing runs at three or
     * four times its authored size, and a stroke that scales with it arrives at
     * five or six pixels - which reads as a marker sketch, not a section
     * through a component. The geometry scales; the pen does not. */
    readonly property real pen: Math.max(1.1, Math.min(2.0, scaleFactor * 0.62))

    function vx(x) { return originX + x * scaleFactor }
    function vy(y) { return originY + y * scaleFactor }

    Canvas {
        id: drawing
        anchors.fill: parent
        antialiasing: true

        readonly property color wall: Theme.textSecondary
        readonly property color guide: Theme.border
        readonly property color fuel: ComponentRegistry.subtypeColor("fuel")
        readonly property color oxidiser: ComponentRegistry.subtypeColor("oxidiser")
        readonly property color face: Theme.surfaceSubtle

        onWallChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        function arrow(ctx, x1, y1, x2, y2) {
            ctx.beginPath()
            ctx.moveTo(root.vx(x1), root.vy(y1))
            ctx.lineTo(root.vx(x2), root.vy(y2))
            ctx.stroke()
            var angle = Math.atan2(y2 - y1, x2 - x1)
            var head = 5
            ctx.beginPath()
            ctx.moveTo(root.vx(x2), root.vy(y2))
            ctx.lineTo(root.vx(x2 - head * Math.cos(angle - 0.5)),
                       root.vy(y2 - head * Math.sin(angle - 0.5)))
            ctx.moveTo(root.vx(x2), root.vy(y2))
            ctx.lineTo(root.vx(x2 - head * Math.cos(angle + 0.5)),
                       root.vy(y2 - head * Math.sin(angle + 0.5)))
            ctx.stroke()
        }

        function line(ctx, x1, y1, x2, y2) {
            ctx.beginPath()
            ctx.moveTo(root.vx(x1), root.vy(y1))
            ctx.lineTo(root.vx(x2), root.vy(y2))
            ctx.stroke()
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.lineCap = "round"
            ctx.lineJoin = "round"

            // ---- injector body ----
            ctx.fillStyle = face
            ctx.strokeStyle = wall
            ctx.lineWidth = root.pen * 1.15
            ctx.beginPath()
            ctx.moveTo(root.vx(52), root.vy(94))
            ctx.lineTo(root.vx(52), root.vy(30))
            ctx.quadraticCurveTo(root.vx(52), root.vy(16), root.vx(70), root.vy(16))
            ctx.lineTo(root.vx(190), root.vy(16))
            ctx.quadraticCurveTo(root.vx(208), root.vy(16), root.vx(208), root.vy(30))
            ctx.lineTo(root.vx(208), root.vy(94))
            ctx.closePath()
            ctx.fill()
            ctx.stroke()

            // ---- chamber walls ----
            ctx.strokeStyle = guide
            ctx.lineWidth = root.pen
            line(ctx, 52, 94, 52, 196)
            line(ctx, 208, 94, 208, 196)

            // ---- face plate ----
            ctx.strokeStyle = wall
            ctx.lineWidth = root.pen * 1.15
            line(ctx, 52, 94, 118, 94)
            line(ctx, 142, 94, 208, 94)

            // ---- central post (oxidiser) ----
            ctx.lineWidth = root.pen * 1.15
            line(ctx, 118, 30, 118, 132)
            line(ctx, 142, 30, 142, 132)
            ctx.beginPath()
            ctx.moveTo(root.vx(118), root.vy(132))
            ctx.lineTo(root.vx(130), root.vy(146))
            ctx.lineTo(root.vx(142), root.vy(132))
            ctx.stroke()

            // ---- annular fuel gap ----
            ctx.strokeStyle = guide
            ctx.lineWidth = root.pen * 0.85
            line(ctx, 106, 60, 106, 94)
            line(ctx, 154, 60, 154, 94)

            // ---- feeds ----
            ctx.strokeStyle = oxidiser
            ctx.lineWidth = root.pen
            arrow(ctx, 130, 2, 130, 26)
            arrow(ctx, 130, 46, 130, 104)

            ctx.strokeStyle = fuel
            arrow(ctx, 30, 62, 100, 62)
            arrow(ctx, 230, 62, 160, 62)
            arrow(ctx, 112, 74, 112, 100)
            arrow(ctx, 148, 74, 148, 100)

            // ---- spray ----
            ctx.strokeStyle = oxidiser
            ctx.lineWidth = root.pen * 0.9
            ctx.globalAlpha = 0.75
            line(ctx, 130, 148, 86, 190)
            line(ctx, 130, 148, 174, 190)
            ctx.globalAlpha = 0.4
            line(ctx, 130, 148, 106, 192)
            line(ctx, 130, 148, 154, 192)
            ctx.globalAlpha = 1
        }
    }

    // ---- labels ----------------------------------------------------------

    Repeater {
        model: [
            { text: "Oxidiser", x: 136, y: 4, colour: "ox" },
            { text: "Fuel", x: 8, y: 48, colour: "fuel" },
            { text: "Pintle post", x: 150, y: 118, colour: "muted" },
            { text: "Face", x: 60, y: 78, colour: "muted" },
            { text: "Chamber", x: 60, y: 176, colour: "muted" }
        ]

        delegate: Text {
            required property var modelData
            x: root.vx(modelData.x)
            y: root.vy(modelData.y)
            text: modelData.text
            color: modelData.colour === "ox" ? ComponentRegistry.subtypeColor("oxidiser")
                 : modelData.colour === "fuel" ? ComponentRegistry.subtypeColor("fuel")
                 : Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.letterSpacing: 0.3
        }
    }
}
