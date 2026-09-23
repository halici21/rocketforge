import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"

/*
 * The propulsion canvas: chamber, throat, expansion, exit plane.
 *
 * WHAT THIS IS. A schematic of area expansion, drawn from the SOLVED area
 * ratio. The exit radius is fixed and the throat radius is derived as
 * r_t = r_e / sqrt(epsilon), so a larger expansion ratio visibly narrows the
 * throat against a constant exit — which is what an expansion ratio means.
 *
 * WHAT THIS IS NOT. It is not a nozzle contour. RocketForge has not solved a
 * bell, a Rao profile, a cone half-angle or any chamber dimension, so nothing
 * here claims one: the wall is a plain schematic curve, the axial scale is
 * arbitrary, and the drawing is labelled "schematic" on the canvas itself.
 *
 * NO PHYSICS. Every quantity annotated here arrives already solved, as a
 * formatted string or a plain number, from the controller. The only arithmetic
 * below is presentation geometry: pixels, radii and curve control points.
 *
 * It repaints on state, theme and size changes only. There is no timer and no
 * idle animation.
 */
Item {
    id: root

    // Solved state, supplied by the caller. Never the live input fields.
    property real radiusRatio: 0
    property bool hasResult: false
    property bool stale: false
    property string regime: ""
    property string exitMachText: ""
    property string exitPressureText: ""
    property string chamberPressureText: ""
    property string ambientText: ""

    // Placeholder mode, for the no-chamber state. Nothing has been solved, so
    // the outline is illustrative: the proportion below is arbitrary, chosen
    // to read as a nozzle, and means nothing. It is deliberately internal --
    // a caller cannot hand a number to a placeholder -- so an invented shape
    // can never occupy the property that carries a solved result.
    property bool placeholder: false
    readonly property real placeholderRatio: 6.3

    // The expansion actually drawn. Animated so a changed epsilon reads as a
    // change to the same object rather than as a different picture.
    property real drawnRatio: 1
    Behavior on drawnRatio {
        NumberAnimation { duration: Motion.slow; easing.type: Easing.OutCubic }
    }

    readonly property real targetRatio: placeholder
                                        ? placeholderRatio
                                        : Math.max(1.0, radiusRatio)
    onTargetRatioChanged: drawnRatio = targetRatio
    Component.onCompleted: drawnRatio = targetRatio

    Canvas {
        id: canvas
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative

        // Repaint only when something it draws has actually changed.
        // A stale wall is dimmed, not erased: textDisabled measured 2.43:1
        // against the page, below the 3:1 WCAG 2.1 asks of a graphic that
        // carries meaning, and the outline of the nozzle is the thing this
        // view is about.
        property color wallColor: root.hasResult && !root.stale
                                  ? Theme.text : Theme.textMuted
        property color fillColor: Theme.surfaceElevated
        property color axisColor: Theme.divider
        property color accentColor: Theme.accent

        onWallColorChanged: requestPaint()
        onFillColorChanged: requestPaint()
        onAxisColorChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        Connections {
            target: root
            function onDrawnRatioChanged() { canvas.requestPaint() }
            function onHasResultChanged() { canvas.requestPaint() }
            function onStaleChanged() { canvas.requestPaint() }
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()

            var w = width
            var h = height
            if (w <= 0 || h <= 0)
                return

            // A band through the middle, so the annotations above and below
            // always have room and never sit on the walls.
            var axis = h * 0.5
            var exitR = Math.min(h * 0.30, w * 0.20)
            // drawnRatio is r_e / r_t, supplied already rooted by the
            // controller. The view divides; it does not derive.
            var ratio = Math.max(1.0, root.drawnRatio)
            var throatR = Math.max(2.5, exitR / ratio)
            var chamberR = Math.min(throatR * 2.8, exitR * 0.80)

            var left = w * 0.08
            var chamberEnd = w * 0.22
            var throatX = w * 0.38
            var exitX = w * 0.90

            // ---- centre line ------------------------------------------
            ctx.strokeStyle = canvas.axisColor
            ctx.lineWidth = 1
            ctx.setLineDash([4, 5])
            ctx.beginPath()
            ctx.moveTo(left - 12, axis)
            ctx.lineTo(exitX + 22, axis)
            ctx.stroke()
            ctx.setLineDash([])

            // ---- the gas path, as one closed shape --------------------
            function wall(sign) {
                ctx.moveTo(left, axis + sign * chamberR)
                ctx.lineTo(chamberEnd, axis + sign * chamberR)
                ctx.bezierCurveTo(
                    chamberEnd + (throatX - chamberEnd) * 0.55,
                    axis + sign * chamberR,
                    throatX - (throatX - chamberEnd) * 0.35,
                    axis + sign * throatR,
                    throatX, axis + sign * throatR)
                ctx.bezierCurveTo(
                    throatX + (exitX - throatX) * 0.22,
                    axis + sign * throatR,
                    throatX + (exitX - throatX) * 0.45,
                    axis + sign * exitR * 0.86,
                    exitX, axis + sign * exitR)
            }

            ctx.beginPath()
            wall(-1)
            ctx.lineTo(exitX, axis + exitR)
            ctx.save()
            ctx.scale(1, 1)
            ctx.restore()
            // mirror path back along the lower wall
            ctx.bezierCurveTo(
                throatX + (exitX - throatX) * 0.45, axis + exitR * 0.86,
                throatX + (exitX - throatX) * 0.22, axis + throatR,
                throatX, axis + throatR)
            ctx.bezierCurveTo(
                throatX - (throatX - chamberEnd) * 0.35, axis + throatR,
                chamberEnd + (throatX - chamberEnd) * 0.55, axis + chamberR,
                chamberEnd, axis + chamberR)
            ctx.lineTo(left, axis + chamberR)
            ctx.closePath()
            ctx.fillStyle = canvas.fillColor
            ctx.fill()

            // ---- the walls themselves ---------------------------------
            ctx.strokeStyle = canvas.wallColor
            ctx.lineWidth = 1.6
            ctx.beginPath()
            wall(-1)
            ctx.stroke()
            ctx.beginPath()
            wall(1)
            ctx.stroke()

            // ---- closing lines: chamber head and exit plane -----------
            ctx.beginPath()
            ctx.moveTo(left, axis - chamberR)
            ctx.lineTo(left, axis + chamberR)
            ctx.stroke()

            ctx.strokeStyle = root.hasResult && !root.stale
                              ? canvas.accentColor : canvas.axisColor
            ctx.lineWidth = 2
            ctx.beginPath()
            ctx.moveTo(exitX, axis - exitR - 6)
            ctx.lineTo(exitX, axis + exitR + 6)
            ctx.stroke()

            // ---- throat station ---------------------------------------
            ctx.strokeStyle = canvas.axisColor
            ctx.lineWidth = 1
            ctx.setLineDash([3, 4])
            ctx.beginPath()
            ctx.moveTo(throatX, axis - exitR - 10)
            ctx.lineTo(throatX, axis + exitR + 10)
            ctx.stroke()
            ctx.setLineDash([])

            // ---- flow direction ---------------------------------------
            if (root.hasResult && !root.stale) {
                ctx.strokeStyle = canvas.accentColor
                ctx.fillStyle = canvas.accentColor
                ctx.lineWidth = 1.4
                var arrowY = axis
                var tip = throatX + (exitX - throatX) * 0.62
                ctx.beginPath()
                ctx.moveTo(left + 18, arrowY)
                ctx.lineTo(tip, arrowY)
                ctx.stroke()
                ctx.beginPath()
                ctx.moveTo(tip + 10, arrowY)
                ctx.lineTo(tip - 2, arrowY - 4.5)
                ctx.lineTo(tip - 2, arrowY + 4.5)
                ctx.closePath()
                ctx.fill()
            }
        }
    }

    // ---- station annotations, placed against the stations they describe ---
    Item {
        anchors.fill: parent

        readonly property real exitR: Math.min(height * 0.30, width * 0.20)

        PerfStationLabel {
            x: parent.width * 0.08
            y: parent.height * 0.5 - parent.exitR - 52
            title: "CHAMBER"
            detail: root.chamberPressureText
            visible: root.hasResult
        }

        PerfStationLabel {
            x: parent.width * 0.38 - 20
            y: parent.height * 0.5 + parent.exitR + 18
            title: "THROAT"
            detail: root.hasResult ? "<i>M</i> = 1" : ""
            visible: root.hasResult
        }

        PerfStationLabel {
            x: Math.min(parent.width * 0.90 + 10, parent.width - 120)
            y: parent.height * 0.5 - parent.exitR - 52
            title: "EXIT"
            detail: root.exitMachText !== "" ? "M_e " + root.exitMachText : ""
            visible: root.hasResult
        }
    }

    // The honesty label. Small, permanent, and not negotiable: the drawing is
    // a schematic of area expansion, not a solved contour.
    //
    // A placeholder says something different, and weaker on purpose. Its
    // expansion is invented, so it must not borrow the solved label's claim to
    // be showing a real area ratio.
    Text {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: root.placeholder
              ? "UNSOLVED OUTLINE — ILLUSTRATIVE, NOT AN AREA RATIO"
              : "SCHEMATIC — AREA EXPANSION ONLY, NOT A SOLVED CONTOUR"
        // The one label that stops the drawing being read as a solved
        // contour. It is quiet, but it is not allowed to be unreadable:
        // textDisabled measured 2.43:1, well under AA for body text.
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: Typography.sectionTracking
    }
}
