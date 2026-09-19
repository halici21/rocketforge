import QtQuick
import "../../theme"

/*
 * The line schematic: inlet -> straight circular line -> outlet.
 *
 * WHAT THIS IS. A schematic of the physical object
 * `engineering.line` actually models: a straight circular pipe of constant
 * diameter, carrying steady single-phase liquid flow, with distributed wall
 * friction only. Per rf-propulsion-visual-grammar's per-workspace table:
 * "A straight schematic with solved flow direction, Re, Darcy f, and
 * delta-p annotated." Every position below is fixed for legibility, not
 * derived from length or diameter -- geometry honesty means this drawing
 * never claims to be to scale.
 *
 * WHAT THIS IS NOT. Not a bend, a valve, a fitting, a pump, an injector, an
 * elbow, cavitation, turbulence CFD, flow particles, a velocity profile, or
 * network routing -- none of them exist in the production model, so none
 * of them are drawn (rf-propulsion-visual-grammar's "Engine Design: no
 * fictional components" rule, applied here to a simpler workspace: the
 * same discipline, not just the same wording).
 *
 * TWO DISTINCT NOT-FULLY-SOLVED STATES, per rf-scientific-ui-contract:
 *   - `hasResult && !hasFriction` (the transitional regime): a REAL result
 *     exists -- velocity, Reynolds number, density are all solved -- but
 *     the Darcy friction factor and the pressure drop are explicitly
 *     withheld, never interpolated. The pipe still draws with its solved
 *     flow direction; only the pressure-drop annotation and outlet value
 *     read as withheld, not the whole object.
 *   - `!hasResult` (refused entirely -- insufficient inlet pressure,
 *     outside the transport envelope, or no solve yet): nothing was
 *     solved, so the pipe draws as a dimmed, unsolved outline, exactly
 *     the earlier accepted-workspace precedent for an empty state that
 *     still reads as an instrument waiting for an input, not a blank page.
 *
 * NO PHYSICS. Every string here arrives already solved and formatted from
 * the controller. The only arithmetic below is presentation geometry.
 *
 * Repaints only on state/theme/size change -- no timer, no idle animation.
 */
Item {
    id: root

    property bool hasResult: false
    property bool hasFriction: false   // false in the transitional regime
    property bool stale: false
    property string regime: ""         // "Laminar" | "Transitional" | "Turbulent"
    property string inletPressureText: ""
    property string outletPressureText: ""

    readonly property color regimeColor: {
        if (!root.hasResult) return Theme.textMuted
        switch (root.regime) {
        case "Turbulent": return Theme.accent
        case "Laminar": return Theme.success
        case "Transitional": return Theme.warning
        default: return Theme.textMuted
        }
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative

        property color wallColor: root.hasResult && !root.stale
                                  ? Theme.text : Theme.textMuted
        property color fillColor: Theme.surfaceElevated
        property color flowColor: root.regimeColor

        // Local mirrors of root's state, purely so their auto-generated
        // on<Name>Changed signal handlers can request a repaint -- the same
        // plain-expression-handler idiom PerfNozzleCanvas.qml already uses
        // for wallColor/fillColor/axisColor, deliberately avoiding a
        // Connections block with a named handler (this workspace's own
        // static rule, tests/test_line_architecture.py, disallows that
        // JS keyword in Line's QML beyond one established input idiom).
        property bool paintHasResult: root.hasResult
        property bool paintHasFriction: root.hasFriction
        property bool paintStale: root.stale
        property string paintRegime: root.regime

        onWallColorChanged: requestPaint()
        onFillColorChanged: requestPaint()
        onFlowColorChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaintHasResultChanged: requestPaint()
        onPaintHasFrictionChanged: requestPaint()
        onPaintStaleChanged: requestPaint()
        onPaintRegimeChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()

            var w = width
            var h = height
            if (w <= 0 || h <= 0)
                return

            var axis = h * 0.52
            var pipeHalf = Math.min(h * 0.14, 30)
            var left = w * 0.08
            var right = w * 0.92

            var active = root.hasResult && !root.stale

            // ---- pipe walls, as one shape -------------------------------
            ctx.beginPath()
            ctx.rect(left, axis - pipeHalf, right - left, pipeHalf * 2)
            ctx.fillStyle = canvas.fillColor
            ctx.fill()
            ctx.strokeStyle = canvas.wallColor
            ctx.lineWidth = 1.6
            ctx.stroke()

            // ---- centreline, dashed -------------------------------------
            ctx.strokeStyle = Theme.divider
            ctx.lineWidth = 1
            ctx.setLineDash([4, 5])
            ctx.beginPath()
            ctx.moveTo(left - 10, axis)
            ctx.lineTo(right + 10, axis)
            ctx.stroke()
            ctx.setLineDash([])

            // ---- inlet / outlet planes ------------------------------------
            ctx.strokeStyle = canvas.wallColor
            ctx.lineWidth = 1.4
            ctx.beginPath()
            ctx.moveTo(left, axis - pipeHalf - 6)
            ctx.lineTo(left, axis + pipeHalf + 6)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(right, axis - pipeHalf - 6)
            ctx.lineTo(right, axis + pipeHalf + 6)
            ctx.stroke()

            // ---- flow direction, coloured by regime ------------------------
            if (active) {
                ctx.strokeStyle = canvas.flowColor
                ctx.fillStyle = canvas.flowColor
                ctx.lineWidth = 1.6
                var tip = right - (right - left) * 0.10
                ctx.beginPath()
                ctx.moveTo(left + (right - left) * 0.12, axis)
                ctx.lineTo(tip, axis)
                ctx.stroke()
                ctx.beginPath()
                ctx.moveTo(tip + 10, axis)
                ctx.lineTo(tip - 2, axis - 5)
                ctx.lineTo(tip - 2, axis + 5)
                ctx.closePath()
                ctx.fill()
            }
        }
    }

    // ---- station annotations -----------------------------------------------
    Item {
        id: stations
        anchors.fill: parent

        readonly property real axis: parent.height * 0.52
        readonly property real pipeHalf: Math.min(parent.height * 0.14, 30)

        Column {
            x: parent.width * 0.08
            y: stations.axis - stations.pipeHalf - 6 - implicitHeight - 6
            spacing: 1
            Text {
                text: "INLET"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.sectionLabel
                font.letterSpacing: Typography.sectionTracking
                font.weight: Typography.medium
            }
            Text {
                visible: root.inletPressureText !== ""
                text: root.inletPressureText
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }
        }

        // Regime only -- velocity used to duplicate here as a second line,
        // but it is already the "Mean velocity V" row in the STATE list
        // below, and the two-line version left no vertical room for the
        // honesty label at the 1366x768 floor (found by opening that
        // capture: the two collided). One line removes the crowding and
        // the duplication in the same fix.
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: stations.axis + stations.pipeHalf + 8
            text: root.hasResult ? root.regime.toUpperCase() : "UNSOLVED"
            color: root.stale ? Theme.textMuted : root.regimeColor
            font.family: Typography.sans
            font.pixelSize: Typography.sectionLabel
            font.letterSpacing: Typography.sectionTracking
            font.weight: Typography.medium
        }

        Column {
            x: parent.width * 0.92 - implicitWidth
            y: stations.axis - stations.pipeHalf - 6 - implicitHeight - 6
            spacing: 1
            Text {
                anchors.right: parent.right
                text: "OUTLET"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.sectionLabel
                font.letterSpacing: Typography.sectionTracking
                font.weight: Typography.medium
            }
            Text {
                anchors.right: parent.right
                visible: root.hasResult
                text: root.hasFriction ? root.outletPressureText
                                       : "— (no friction factor this regime)"
                color: root.hasFriction ? Theme.textSecondary : Theme.warning
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }
        }
    }

    // The honesty label -- not negotiable, per rf-propulsion-visual-grammar.
    Text {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: "SCHEMATIC — STRAIGHT LINE, NOT DRAWN TO SCALE"
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: Typography.sectionTracking
    }
}
