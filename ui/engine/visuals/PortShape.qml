import QtQuick
import "../../theme"

/*
 * PortShape - the outline that says which physical domain a port belongs to.
 *
 * Shape carries the domain, colour only ever carries the subtype on top of it:
 *
 *     circle    fluid
 *     diamond   mechanical / shaft
 *     triangle  thermal
 *     square    signal / control
 *
 * That split is what lets the vocabulary grow. A new coolant or pressurant is a
 * new tint inside an existing shape; a genuinely new physics domain is a new
 * shape. It also survives the three cases colour alone does not: a greyscale
 * screenshot, a colour-blind reader, and a line seen at 40 % zoom.
 *
 * Drawn on a 12x12 grid so the four shapes carry the same optical weight - a
 * triangle and a square with identical bounding boxes do not look the same
 * size, so each has its own inset.
 */
Canvas {
    id: root

    property string domain: "fluid"
    property color fillColor: "transparent"
    property color strokeColor: Theme.border
    property real strokeWidth: 1.4

    implicitWidth: 10
    implicitHeight: 10
    antialiasing: true

    onDomainChanged: requestPaint()
    onFillColorChanged: requestPaint()
    onStrokeColorChanged: requestPaint()
    onStrokeWidthChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.save()
        ctx.scale(width / 12, height / 12)

        ctx.fillStyle = root.fillColor
        ctx.strokeStyle = root.strokeColor
        // The stroke is specified in device pixels, so undo the grid scale.
        ctx.lineWidth = root.strokeWidth * 12 / Math.max(1, width)
        ctx.lineJoin = "round"
        ctx.beginPath()

        var inset = ctx.lineWidth / 2

        switch (root.domain) {
        case "mechanical":
            // Diamond: a square on its corner, grown to match the circle.
            ctx.moveTo(6, 0.2 + inset)
            ctx.lineTo(11.8 - inset, 6)
            ctx.lineTo(6, 11.8 - inset)
            ctx.lineTo(0.2 + inset, 6)
            ctx.closePath()
            break

        case "thermal":
            // Triangle, raised off the baseline so it reads centred.
            ctx.moveTo(6, 0.8 + inset)
            ctx.lineTo(11.6 - inset, 10.6 - inset)
            ctx.lineTo(0.4 + inset, 10.6 - inset)
            ctx.closePath()
            break

        case "signal":
            // Square, inset so it does not out-weigh the circle.
            ctx.rect(1.3 + inset, 1.3 + inset,
                     9.4 - inset * 2, 9.4 - inset * 2)
            break

        default:
            // Fluid.
            ctx.arc(6, 6, 5.1 - inset, 0, Math.PI * 2)
            break
        }

        ctx.fill()
        ctx.stroke()
        ctx.restore()
    }
}
