import QtQuick
import "../../theme"

/*
 * The equilibrium-chamber schematic: reactants -> chamber -> products.
 *
 * WHAT THIS IS. A schematic of the reaction as an equilibrium STATE, per
 * rf-propulsion-visual-grammar's per-workspace object table: "oxidizer +
 * fuel -> equilibrium chamber -> products... the chamber as an equilibrium
 * state, not a combustion process." CEA solves a 0-D equilibrium state, not
 * a flow field, so there is no derived geometry here at all (unlike the
 * Rocket Performance nozzle canvas, whose throat radius comes from a
 * solved area ratio) -- every position below is fixed, chosen for
 * legibility, and carries no physical claim beyond "this is the right kind
 * of diagram."
 *
 * WHAT THIS IS NOT. Not a flame. Not a reaction-zone geometry. Not a
 * residence time or a mixing/combustion process of any kind -- CEA does
 * not solve one, so nothing here draws one. No gradient, particle, or glow
 * standing in for a flow field (rf-propulsion-visual-grammar: "no fake
 * CFD, ever").
 *
 * NO PHYSICS. Every string/number annotated here arrives already solved
 * and formatted from the controller. The only arithmetic below is
 * presentation geometry: pixel positions for boxes and arrows.
 *
 * Repaints only on state/theme/size change -- no timer, no idle animation,
 * consistent with rf-qml-architecture's Canvas discipline.
 */
Item {
    id: root

    property bool hasResult: false
    property bool stale: false
    property string oxidiserLabel: ""
    property string fuelLabel: ""
    property string ofText: ""
    property string chamberPressureText: ""
    property string providerLabel: ""
    property string productsSummary: ""
    property bool placeholder: false

    Canvas {
        id: canvas
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative

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

            var axis = h * 0.5
            var chamberLeft = w * 0.34
            var chamberRight = w * 0.62
            var chamberHalf = Math.min(h * 0.22, 52)
            var inletTopY = axis - chamberHalf * 0.55
            var inletBottomY = axis + chamberHalf * 0.55
            var leftX = w * 0.06
            var outletX = w * 0.92

            var active = root.hasResult && !root.stale

            // ---- reactant inlet lines ----------------------------------
            ctx.strokeStyle = canvas.wallColor
            ctx.lineWidth = 1.4
            ctx.beginPath()
            ctx.moveTo(leftX, inletTopY)
            ctx.lineTo(chamberLeft, inletTopY)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(leftX, inletBottomY)
            ctx.lineTo(chamberLeft, inletBottomY)
            ctx.stroke()

            // ---- chamber box --------------------------------------------
            ctx.beginPath()
            ctx.rect(chamberLeft, axis - chamberHalf, chamberRight - chamberLeft,
                     chamberHalf * 2)
            ctx.fillStyle = canvas.fillColor
            ctx.fill()
            ctx.strokeStyle = canvas.wallColor
            ctx.lineWidth = 1.6
            ctx.stroke()

            // ---- outlet to products ---------------------------------------
            ctx.strokeStyle = canvas.wallColor
            ctx.lineWidth = 1.4
            ctx.beginPath()
            ctx.moveTo(chamberRight, axis)
            ctx.lineTo(outletX, axis)
            ctx.stroke()

            // ---- flow direction, only when a real result is showing -------
            if (active) {
                ctx.strokeStyle = canvas.accentColor
                ctx.fillStyle = canvas.accentColor
                ctx.lineWidth = 1.4
                var tip = chamberRight + (outletX - chamberRight) * 0.72
                ctx.beginPath()
                ctx.moveTo(chamberRight + 8, axis)
                ctx.lineTo(tip, axis)
                ctx.stroke()
                ctx.beginPath()
                ctx.moveTo(tip + 9, axis)
                ctx.lineTo(tip - 2, axis - 4.5)
                ctx.lineTo(tip - 2, axis + 4.5)
                ctx.closePath()
                ctx.fill()

                // small arrowheads on the two reactant inlets too
                ctx.beginPath()
                ctx.moveTo(chamberLeft - 1, inletTopY)
                ctx.lineTo(chamberLeft - 11, inletTopY - 4.5)
                ctx.lineTo(chamberLeft - 11, inletTopY + 4.5)
                ctx.closePath()
                ctx.fill()
                ctx.beginPath()
                ctx.moveTo(chamberLeft - 1, inletBottomY)
                ctx.lineTo(chamberLeft - 11, inletBottomY - 4.5)
                ctx.lineTo(chamberLeft - 11, inletBottomY + 4.5)
                ctx.closePath()
                ctx.fill()
            }
        }
    }

    // ---- annotations, placed against the stations they describe -----------
    Item {
        id: stations
        anchors.fill: parent

        readonly property real chamberLeft: width * 0.34
        readonly property real chamberRight: width * 0.62
        readonly property real chamberHalf: Math.min(height * 0.22, 52)
        readonly property real axis: height * 0.5

        Column {
            x: 4
            y: stations.axis - stations.chamberHalf * 0.55 - implicitHeight - 6
            spacing: 1
            Text {
                text: "OXIDIZER"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.sectionLabel
                font.letterSpacing: Typography.sectionTracking
                font.weight: Typography.medium
            }
            Text {
                visible: root.hasResult
                text: root.oxidiserLabel
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }
        }

        Column {
            x: 4
            y: stations.axis + stations.chamberHalf * 0.55 + 6
            spacing: 1
            Text {
                text: "FUEL"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.sectionLabel
                font.letterSpacing: Typography.sectionTracking
                font.weight: Typography.medium
            }
            Text {
                visible: root.hasResult
                text: root.fuelLabel + (root.ofText !== "" ? "  ·  " + root.ofText : "")
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }
        }

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.horizontalCenterOffset: (stations.chamberLeft + stations.chamberRight) / 2 - stations.width / 2
            y: stations.axis - 11
            spacing: 1
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "EQUILIBRIUM CHAMBER"
                color: root.hasResult && !root.stale ? Theme.text : Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.sectionLabel
                font.letterSpacing: Typography.sectionTracking
                font.weight: Typography.medium
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: root.hasResult && root.chamberPressureText !== ""
                text: root.chamberPressureText
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }
        }

        Column {
            // A fixed, bounded width -- not sized from the summary text's
            // own implicitWidth -- so a long condensed-state sentence
            // ("No condensed phase above reporting threshold") wraps in
            // place instead of growing the column leftward over the
            // chamber box. Found by inspecting the 1366x768 capture, not
            // assumed: at that width the unbounded version overlapped.
            width: Math.min(stations.width * 0.32, 230)
            x: stations.width * 0.96 - width
            y: stations.axis - stations.chamberHalf * 0.55 - implicitHeight - 6
            spacing: 1
            Text {
                anchors.right: parent.right
                text: "PRODUCTS"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.sectionLabel
                font.letterSpacing: Typography.sectionTracking
                font.weight: Typography.medium
            }
            Text {
                width: parent.width
                visible: root.hasResult && root.productsSummary !== ""
                text: root.productsSummary
                wrapMode: Text.WordWrap
                lineHeight: 1.15
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
                horizontalAlignment: Text.AlignRight
            }
        }
    }

    // The honesty label -- not negotiable, per rf-propulsion-visual-grammar.
    Text {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: "EQUILIBRIUM STATE SCHEMATIC — NOT A REACTION-FLOW SOLUTION"
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: Typography.sectionTracking
    }
}
