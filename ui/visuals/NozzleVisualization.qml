import QtQuick
import "../theme"
import "../components"
import "../data"

/*
 * NozzleVisualization - the signature drawing of the product.
 *
 * A converging-diverging contour drawn from a hand-authored wall profile, with
 * an axial pressure trace directly beneath it on the *same* axial axis, so a
 * station marker is a single vertical line crossing both. That shared axis is
 * the idea worth keeping when the real solver arrives.
 *
 * Nothing is computed here. The regime, its shock station, its plume style and
 * its trace are all authored constants selected by the back-pressure control;
 * the marker animates between authored stations, which is a transition, not a
 * calculation.
 */
Item {
    id: root

    property var regime: MockData.nozzleRegimes[3]
    property real ambient: MockData.backPressureDefault
    property var contour: MockData.nozzleContour

    // Gutters are shared with the trace plot so both panes use one axial axis.
    readonly property real axisGutter: 52
    readonly property real rightInset: 18
    readonly property real innerWidth: Math.max(1, width - axisGutter - rightInset)
    readonly property real nozzleHeight: Math.max(140, (height - 20) * 0.56)

    function mapAxial(x) {
        return axisGutter + x * innerWidth
    }

    // Linear interpolation of the authored wall profile, for drawing only.
    function wallRadius(x) {
        if (contour.length === 0)
            return 0
        for (var i = 1; i < contour.length; ++i) {
            if (x <= contour[i][0]) {
                var x0 = contour[i - 1][0], r0 = contour[i - 1][1]
                var x1 = contour[i][0], r1 = contour[i][1]
                var t = x1 > x0 ? (x - x0) / (x1 - x0) : 0
                return r0 + (r1 - r0) * t
            }
        }
        return contour[contour.length - 1][1]
    }

    // ================= nozzle pane =================

    Item {
        id: nozzlePane
        x: root.axisGutter
        y: 0
        width: root.innerWidth
        height: root.nozzleHeight

        readonly property real centreY: height / 2 + 6
        readonly property real maxRadius: height / 2 - 20

        function wallY(x, sign) {
            return centreY - sign * root.wallRadius(x) * maxRadius
        }

        Canvas {
            id: shape
            anchors.fill: parent
            antialiasing: true

            readonly property color wallColor: Theme.textSecondary
            readonly property color centreColor: Theme.border
            readonly property color washColor: Theme.accent
            readonly property color fillColor: Theme.surfaceSubtle
            readonly property string plume: root.regime.plume

            onWallColorChanged: requestPaint()
            onPlumeChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                var pts = root.contour
                var i

                // --- interior ---
                ctx.beginPath()
                ctx.moveTo(pts[0][0] * width, nozzlePane.wallY(pts[0][0], 1))
                for (i = 1; i < pts.length; ++i)
                    ctx.lineTo(pts[i][0] * width, nozzlePane.wallY(pts[i][0], 1))
                for (i = pts.length - 1; i >= 0; --i)
                    ctx.lineTo(pts[i][0] * width, nozzlePane.wallY(pts[i][0], -1))
                ctx.closePath()
                ctx.fillStyle = fillColor
                ctx.fill()

                // A barely-there wash from chamber to exit: enough to read as
                // gas, not enough to read as decoration.
                var wash = ctx.createLinearGradient(0, 0, width, 0)
                wash.addColorStop(0.0, Qt.rgba(washColor.r, washColor.g, washColor.b, 0.07))
                wash.addColorStop(0.45, Qt.rgba(washColor.r, washColor.g, washColor.b, 0.035))
                wash.addColorStop(1.0, Qt.rgba(washColor.r, washColor.g, washColor.b, 0.01))
                ctx.fillStyle = wash
                ctx.fill()

                // --- centreline ---
                ctx.strokeStyle = centreColor
                ctx.lineWidth = 1
                ctx.setLineDash([5, 5])
                ctx.beginPath()
                ctx.moveTo(0, nozzlePane.centreY)
                ctx.lineTo(width, nozzlePane.centreY)
                ctx.stroke()
                ctx.setLineDash([])

                // --- walls ---
                ctx.strokeStyle = wallColor
                ctx.lineWidth = 1.7
                ctx.lineJoin = "round"
                for (var s = 1; s >= -1; s -= 2) {
                    ctx.beginPath()
                    ctx.moveTo(pts[0][0] * width, nozzlePane.wallY(pts[0][0], s))
                    for (i = 1; i < pts.length; ++i)
                        ctx.lineTo(pts[i][0] * width, nozzlePane.wallY(pts[i][0], s))
                    ctx.stroke()
                }

                // --- exit plume hint ---
                if (plume !== "none") {
                    var exitR = root.wallRadius(1.0) * nozzlePane.maxRadius
                    var spread = plume === "expand" ? 0.34 : -0.30
                    ctx.strokeStyle = Qt.rgba(washColor.r, washColor.g, washColor.b, 0.55)
                    ctx.lineWidth = 1.2
                    ctx.setLineDash([4, 4])
                    for (var k = 0; k < 2; ++k) {
                        var dir = k === 0 ? 1 : -1
                        ctx.beginPath()
                        ctx.moveTo(width, nozzlePane.centreY - dir * exitR)
                        ctx.lineTo(width + root.rightInset * 0.9,
                                   nozzlePane.centreY - dir * exitR * (1 + spread))
                        ctx.stroke()
                    }
                    ctx.setLineDash([])
                }
            }
        }

        // ---- station labels ----
        Repeater {
            model: [
                { x: 0.075, label: "Chamber" },
                { x: MockData.throatX, label: "Throat" },
                { x: 0.995, label: "Exit" }
            ]

            delegate: Item {
                required property var modelData

                x: modelData.x * nozzlePane.width
                y: 0
                width: 1
                height: nozzlePane.height

                Rectangle {
                    width: Metrics.hairline
                    height: parent.height - 16
                    y: 8
                    color: Theme.divider
                    visible: modelData.label !== "Chamber"
                }

                RFSectionLabel {
                    readonly property string plainText: modelData.label
                    text: Notation.sectionRich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    x: modelData.x > 0.9 ? -implicitWidth - 6 : (modelData.x < 0.2 ? 0 : 6)
                    y: 0
                }
            }
        }

        // ---- sonic throat indicator ----
        Item {
            id: sonic
            x: MockData.throatX * nozzlePane.width
            y: nozzlePane.centreY
            opacity: root.regime.sonic ? 1 : 0
            visible: opacity > 0

            Behavior on opacity { NumberAnimation { duration: Motion.base } }

            Rectangle {
                x: -3
                y: -3
                width: 6
                height: 6
                radius: 1
                rotation: 45
                color: Theme.accent
            }

            Text {
                x: 8
                y: -7
                text: "M = 1"
                color: Theme.accent
                font.family: Typography.mono
                font.pixelSize: Typography.meta
                font.weight: Typography.medium
            }
        }
    }

    // ================= axial pressure trace =================

    RFPlotSurface {
        id: trace
        x: 0
        y: root.nozzleHeight
        width: root.width
        height: root.height - root.nozzleHeight

        leftGutter: root.axisGutter
        rightPadding: root.rightInset
        topPadding: 6
        xMin: 0; xMax: 1; yMin: 0; yMax: 1
        xTickCount: 6
        yTickCount: 3
        yTitle: "p / p₀"
        xFormat: function (v) { return v.toFixed(1) }
        yFormat: function (v) { return v.toFixed(1) }

        // Every authored regime, faint: the family the active curve belongs to.
        Repeater {
            model: MockData.nozzleRegimes

            delegate: MockLineSeries {
                required property var modelData
                plot: trace
                points: modelData.trace
                color: Theme.textMuted
                thickness: 1
                opacity: 0.28
            }
        }

        MockLineSeries {
            id: activeTrace
            plot: trace
            points: root.regime.trace
            color: Theme.accent
            thickness: 1.9
        }

        // Ambient level, driven straight from the back-pressure control.
        RFDashedLine {
            y: trace.mapY(root.ambient)
            implicitWidth: parent.width
            color: Theme.textSecondary
            opacity: 0.75

            Behavior on y { NumberAnimation { duration: Motion.base; easing.type: Motion.standard } }
        }

        Text {
            y: trace.mapY(root.ambient) - height - 2
            x: parent.width - width
            text: "p_b"
            color: Theme.textSecondary
            font.family: Typography.mono
            font.pixelSize: Typography.meta

            Behavior on y { NumberAnimation { duration: Motion.base; easing.type: Motion.standard } }
        }
    }

    // ================= shock station marker =================

    Item {
        id: shockMarker

        readonly property bool present: root.regime.shockX > 0
        readonly property real station: present ? root.regime.shockX : MockData.throatX

        x: root.mapAxial(station)
        y: 0
        width: 1
        height: root.height
        opacity: present ? 1 : 0
        visible: opacity > 0

        Behavior on x { NumberAnimation { duration: Motion.slow; easing.type: Motion.emphasized } }
        Behavior on opacity { NumberAnimation { duration: Motion.base } }

        // Full-height station line, crossing contour and trace alike.
        Rectangle {
            width: Metrics.hairline
            height: parent.height - 18
            color: Theme.accent
            opacity: 0.35
        }

        // Solid segment across the duct: this is the shock itself.
        Rectangle {
            y: nozzlePane.wallY(shockMarker.station, 1)
            width: 2
            height: Math.max(0, nozzlePane.wallY(shockMarker.station, -1)
                              - nozzlePane.wallY(shockMarker.station, 1))
            color: Theme.accent
        }

        Rectangle {
            id: shockTag
            x: 6
            y: nozzlePane.wallY(shockMarker.station, 1) - height - 6
            width: shockTagText.implicitWidth + Metrics.spacing.s * 2
            height: 18
            radius: Metrics.radius.xs
            color: Theme.surfaceElevated
            border.width: Metrics.hairline
            border.color: Theme.border

            Text {
                id: shockTagText
                anchors.centerIn: parent
                text: "Shock"
                color: Theme.accent
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.weight: Typography.medium
            }
        }
    }
}
