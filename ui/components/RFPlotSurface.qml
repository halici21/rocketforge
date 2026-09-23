import QtQuick
import "../theme"

/*
 * RFPlotSurface - the frame every chart in the application is drawn on.
 *
 * It owns the axes, the grid, the tick labels and the data-to-pixel mapping;
 * it owns no data. Children are placed inside the plot area and position
 * themselves with mapX()/mapY(), so a series never has to know about gutters.
 *
 * Deliberately frameless: two hairline axes, a grid one step quieter than the
 * dividers, and nothing else. No boxed border, no filled plot background beyond
 * the surface it sits on.
 *
 * The legend lives in its own reserved strip above the plot area, not
 * floated inside it -- found by opening a real capture of a dense scatter
 * consumer at 1366x768: a legend anchored inside the data region collided
 * directly with the points it was labelling. A `Flow` here instead of a
 * fixed `Row` also wraps rather than overflowing at that width.
 *
 * `hoverX`/`hoverY` (data-space, NaN when nothing is highlighted) draw a
 * light crosshair. RFPlotSurface still owns no data -- a caller with its
 * own notion of "the nearest point" (a marker's own HoverHandler, for
 * example) sets these two numbers; the surface only maps and draws them.
 */
Item {
    id: root

    property real xMin: 0
    property real xMax: 1
    property real yMin: 0
    property real yMax: 1

    // Tick TARGETS, not exact counts: the surface places ticks at nice
    // numbers inside the range and lands near this many. Equal fractions of
    // the range produced axes reading 0.52 / 0.60 / 0.68 / 0.77 / 0.85 in
    // the audit captures -- see RFLineChart.niceTicks for the full argument;
    // this is the same rule so the two chart systems cannot disagree.
    property int xTickCount: 6
    property int yTickCount: 5

    function niceStep(raw) {
        if (!(raw > 0))
            return 1
        var exp = Math.floor(Math.log(raw) / Math.LN10)
        var pow = Math.pow(10, exp)
        var frac = raw / pow
        var nice = frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 2.5 ? 2.5 : frac <= 5 ? 5 : 10
        return nice * pow
    }

    function niceTicks(lo, hi, target) {
        if (!(hi > lo) || !isFinite(lo) || !isFinite(hi))
            return [lo]
        var step = niceStep((hi - lo) / Math.max(1, target))
        var out = []
        var first = Math.ceil(lo / step - 1e-9) * step
        for (var v = first; v <= hi + step * 1e-9; v += step)
            out.push(Math.abs(v) < step * 1e-9 ? 0 : v)
        return out.length >= 2 ? out : [lo, hi]
    }

    readonly property var xTicks: niceTicks(xMin, xMax, xTickCount)
    readonly property var yTicks: niceTicks(yMin, yMax, yTickCount)

    property string xTitle: ""
    property string yTitle: ""

    // Tick formatting is a presentation choice, so it lives with the plot.
    // Defaults format from the tick STEP, so a narrow axis does not print
    // five copies of the same rounded number. A caller with a unit-specific
    // format still overrides these.
    function stepDecimals(ticks) {
        if (!ticks || ticks.length < 2)
            return 1
        var step = Math.abs(ticks[1] - ticks[0])
        return Math.min(6, Math.max(0, -Math.floor(Math.log(step) / Math.LN10 + 1e-9)))
    }
    property var xFormat: function (v) { return v.toFixed(stepDecimals(xTicks)) }
    property var yFormat: function (v) { return v.toFixed(stepDecimals(yTicks)) }

    // The rotated axis title needs its own column to the left of the ticks.
    property real leftGutter: yTitle !== "" ? 66 : 50
    // The axis title gets its own line under the tick labels.
    property real bottomGutter: xTitle !== "" ? 48 : 32
    readonly property real legendHeight: legend.length > 0 ? 22 : 0
    property real topPadding: 12 + legendHeight
    property real rightPadding: 16

    // [{ name: "p/p0", color: <color>, dashed: bool, shape: <string> }]
    //
    // `shape` is one of "line" (the default), "diamond", "circle", "ring"
    // or "cross", and makes the swatch look like the mark it names. A
    // scatter legend that draws a dash for a diamond forces the entry to
    // carry its shape in the TEXT instead -- which is what this one did,
    // as "Infeasible or failed U+2715", and the capture showed the glyph
    // landing as tofu in the shipped font stack. A drawn swatch cannot
    // fail to render, and it satisfies the colour-is-never-alone rule
    // (rf-scientific-ui-contract) with a shape rather than a character.
    property var legend: []

    // Data-space crosshair, driven by a caller's own hover detection.
    property real hoverX: NaN
    property real hoverY: NaN
    readonly property bool hoverActive: !isNaN(hoverX) && !isNaN(hoverY)

    readonly property alias plotArea: area
    default property alias content: area.data

    function tickValue(i, count, lo, hi) {
        return lo + (hi - lo) * i / Math.max(1, count - 1)
    }
    function mapX(v) {
        return (v - xMin) / (xMax - xMin) * area.width
    }
    function mapY(v) {
        return area.height - (v - yMin) / (yMax - yMin) * area.height
    }
    function unmapX(px) {
        return xMin + (px / Math.max(1, area.width)) * (xMax - xMin)
    }

    // ---- y axis ----------------------------------------------------------

    Text {
        id: yTitleText
        visible: root.yTitle !== ""
        text: Notation.rich(root.yTitle)
        textFormat: Notation.textFormat(root.yTitle)
        rotation: -90
        transformOrigin: Item.Center
        // Rotating about the centre swaps the visual extents, so the left edge
        // of the painted glyphs is x + width/2 - height/2.
        x: 2 - width / 2 + height / 2
        y: area.y + area.height / 2 - height / 2
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.axisTitle
        font.letterSpacing: 0.4
    }

    Repeater {
        model: root.yTicks
        delegate: Text {
            required property var modelData
            readonly property real value: modelData

            visible: value >= root.yMin && value <= root.yMax
            x: root.leftGutter - width - 10
            y: area.y + root.mapY(value) - height / 2
            text: root.yFormat(value)
            color: Theme.textMuted
            font.family: Typography.mono
            font.pixelSize: Typography.axisTick
        }
    }

    // ---- x axis ----------------------------------------------------------

    Repeater {
        model: root.xTicks
        delegate: Text {
            required property var modelData
            readonly property real value: modelData

            visible: value >= root.xMin && value <= root.xMax
            x: area.x + root.mapX(value) - width / 2
            y: area.y + area.height + 10
            text: root.xFormat(value)
            color: Theme.textMuted
            font.family: Typography.mono
            font.pixelSize: Typography.axisTick
        }
    }

    Text {
        visible: root.xTitle !== ""
        text: Notation.rich(root.xTitle)
        textFormat: Notation.textFormat(root.xTitle)
        x: area.x + (area.width - width) / 2
        y: area.y + area.height + 28
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.axisTitle
        font.letterSpacing: 0.4
    }

    // ---- legend ------------------------------------------------------
    // Lives in its own reserved strip above the plot area (see topPadding),
    // never inside it -- a legend anchored inside the data region collided
    // with dense scatter data at 1366x768 in the pre-redesign layout.
    Flow {
        id: legendFlow
        visible: root.legend.length > 0
        x: area.x
        y: 2
        width: area.width
        spacing: Metrics.spacing.l

        Repeater {
            model: root.legend

            delegate: Row {
                required property var modelData
                spacing: Metrics.spacing.xs + 2

                Item {
                    anchors.verticalCenter: parent.verticalCenter
                    width: 14
                    height: 10

                    readonly property string shape:
                        modelData.shape !== undefined ? modelData.shape : "line"
                    readonly property real dim: 7

                    // A line series: the hairline swatch this legend has
                    // always drawn.
                    Rectangle {
                        visible: parent.shape === "line"
                        anchors.centerIn: parent
                        width: 14
                        height: 2
                        radius: 1
                        color: modelData.color
                        opacity: modelData.dashed !== undefined && modelData.dashed ? 0.55 : 1
                    }

                    // A filled diamond: a square on its corner.
                    Rectangle {
                        visible: parent.shape === "diamond"
                        anchors.centerIn: parent
                        width: parent.dim
                        height: parent.dim
                        rotation: 45
                        color: modelData.color
                    }

                    Rectangle {
                        visible: parent.shape === "circle" || parent.shape === "ring"
                        anchors.centerIn: parent
                        width: parent.dim
                        height: parent.dim
                        radius: parent.dim / 2
                        color: parent.shape === "ring" ? "transparent" : modelData.color
                        border.width: parent.shape === "ring" ? 1.5 : 0
                        border.color: modelData.color
                    }

                    // A cross, drawn as two rotated bars so it needs no glyph.
                    Item {
                        visible: parent.shape === "cross"
                        anchors.centerIn: parent
                        width: parent.dim
                        height: parent.dim
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width; height: 1.5
                            rotation: 45
                            color: modelData.color
                        }
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width; height: 1.5
                            rotation: -45
                            color: modelData.color
                        }
                    }
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: Notation.rich(modelData.name)
                    textFormat: Notation.textFormat(modelData.name)
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }

    // ---- plot area -------------------------------------------------------

    Item {
        id: area
        x: root.leftGutter
        y: root.topPadding
        width: Math.max(1, root.width - root.leftGutter - root.rightPadding)
        height: Math.max(1, root.height - root.topPadding - root.bottomGutter)

        // Grid and axes, painted below any series added by the caller.
        Canvas {
            id: grid
            anchors.fill: parent
            z: -1
            antialiasing: false

            readonly property color gridColor: Theme.gridLine
            readonly property color axisColor: Theme.axisLine
            // Local mirrors so a change to the tick arrays repaints the grid:
            // a gridline that no longer sits under its own label is worse
            // than no gridline at all.
            property var paintXTicks: root.xTicks
            property var paintYTicks: root.yTicks

            onPaintXTicksChanged: requestPaint()
            onPaintYTicksChanged: requestPaint()
            onGridColorChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.lineWidth = 1
                ctx.strokeStyle = gridColor
                ctx.beginPath()
                var i
                for (i = 0; i < paintYTicks.length; ++i) {
                    if (paintYTicks[i] < root.yMin || paintYTicks[i] > root.yMax)
                        continue
                    var gy = Math.round(root.mapY(paintYTicks[i])) + 0.5
                    ctx.moveTo(0, gy)
                    ctx.lineTo(width, gy)
                }
                for (i = 0; i < paintXTicks.length; ++i) {
                    if (paintXTicks[i] < root.xMin || paintXTicks[i] > root.xMax)
                        continue
                    var gx = Math.round(root.mapX(paintXTicks[i])) + 0.5
                    ctx.moveTo(gx, 0)
                    ctx.lineTo(gx, height)
                }
                ctx.stroke()

                // Axes sit one step stronger than the grid.
                ctx.strokeStyle = axisColor
                ctx.beginPath()
                ctx.moveTo(0.5, 0)
                ctx.lineTo(0.5, height)
                ctx.moveTo(0, height - 0.5)
                ctx.lineTo(width, height - 0.5)
                ctx.stroke()
            }
        }

        // Crosshair for the caller-driven hover state. A separate Canvas
        // from `grid` on purpose (rf-qml-architecture): this one repaints
        // on every hover move, `grid` must not.
        Canvas {
            id: crosshair
            anchors.fill: parent
            z: -1
            antialiasing: false
            visible: root.hoverActive

            // Local mirrors -- an onXChanged handler only resolves against
            // properties this same Item declares, not an ancestor's.
            property real paintHoverX: root.hoverX
            property real paintHoverY: root.hoverY
            readonly property color lineColor: Theme.textMuted

            onPaintHoverXChanged: requestPaint()
            onPaintHoverYChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                if (isNaN(paintHoverX) || isNaN(paintHoverY))
                    return
                var px = Math.round(root.mapX(paintHoverX)) + 0.5
                var py = Math.round(root.mapY(paintHoverY)) + 0.5
                ctx.strokeStyle = lineColor
                ctx.globalAlpha = 0.5
                ctx.lineWidth = 1
                ctx.setLineDash([3, 3])
                ctx.beginPath()
                ctx.moveTo(px, 0)
                ctx.lineTo(px, height)
                ctx.moveTo(0, py)
                ctx.lineTo(width, py)
                ctx.stroke()
            }
        }
    }
}
