import QtQuick
import QtQuick.Layouts
import "../../theme"

/*
 * The equilibrium chamber as a station band: what went in -> the equilibrium
 * chamber -> what the solved state holds. One line of stations, not a figure.
 *
 * WHAT THIS IS. A zero-dimensional state, per rf-propulsion-visual-grammar's
 * per-workspace object table: "oxidizer + fuel -> equilibrium chamber ->
 * products... the chamber as an equilibrium state, not a combustion process."
 * CEA solves one equilibrium state, not a flow field, so nothing here is
 * geometry: every position is layout, chosen for legibility, and the band is
 * kept short so it frames the solved state beneath it instead of standing in
 * for it. (It was a 210 px drawing of a box and two lines, which read as the
 * answer and pushed the answer down the page.)
 *
 * WHAT THIS IS NOT. Not a flame, a reaction zone, a residence time or a flow.
 * No injector, no nozzle, no gradient, no particles (rf-propulsion-visual-
 * grammar: "no fake CFD, ever"). The honesty label says so, set directly under
 * the chamber it qualifies rather than as a block of its own.
 *
 * NO PHYSICS. Every string arrives solved and formatted from the controller,
 * from the RESULT's own conditions -- never the live form. A solid grain is one
 * stream and carries no O/F: CEA reports 0.000 for it, and the absence of a
 * ratio is the honest representation.
 */
Item {
    id: root

    property bool hasResult: false
    property bool stale: false
    property bool singleStream: false
    property string streamLabel: ""
    property string oxidiserLabel: ""
    property string fuelLabel: ""
    property string ofText: ""
    property string chamberPressureText: ""
    property string productsSummary: ""

    // Values are drawn only for a current result; a stale one dims with the
    // rest of the chamber state, and an unsolved band names its stations only.
    readonly property bool active: root.hasResult && !root.stale
    readonly property color lineColor: root.active ? Theme.textSecondary : Theme.textMuted

    implicitHeight: band.implicitHeight + Metrics.spacing.xs + honesty.implicitHeight

    component StationTag: Row {
        property string tag: ""
        property string value: ""
        spacing: Metrics.spacing.s
        Text {
            anchors.baseline: valueText.baseline
            text: parent.tag
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.sectionLabel
            font.letterSpacing: Typography.sectionTracking
            font.weight: Typography.medium
        }
        Text {
            id: valueText
            visible: root.hasResult && parent.value !== ""
            text: parent.value
            color: Theme.textSecondary
            font.family: Typography.mono
            font.pixelSize: Typography.readoutSmall
        }
    }

    // A connector: one or two hairlines, with an arrowhead only when a solved
    // state is showing -- direction is a claim about a result.
    component Connector: Canvas {
        id: connector
        property int streams: 1
        property color stroke: root.lineColor
        property bool arrows: root.active
        implicitHeight: 24
        onStrokeChanged: requestPaint()
        onArrowsChanged: requestPaint()
        onStreamsChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (width <= 0 || height <= 0)
                return
            var mid = height / 2
            var ys = streams === 2 ? [mid - 6, mid + 6] : [mid]
            ctx.strokeStyle = stroke
            ctx.fillStyle = arrows ? Theme.accent : stroke
            ctx.lineWidth = 1.2
            for (var i = 0; i < ys.length; ++i) {
                ctx.beginPath()
                ctx.moveTo(0, ys[i])
                ctx.lineTo(width - (arrows ? 8 : 0), ys[i])
                ctx.stroke()
                if (arrows) {
                    ctx.beginPath()
                    ctx.moveTo(width, ys[i])
                    ctx.lineTo(width - 9, ys[i] - 4)
                    ctx.lineTo(width - 9, ys[i] + 4)
                    ctx.closePath()
                    ctx.fill()
                }
            }
        }
        Connections {
            target: Theme
            function onModeChanged() { connector.requestPaint() }
        }
    }

    RowLayout {
        id: band
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: Metrics.spacing.m

        // ---- what went in ------------------------------------------------
        ColumnLayout {
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: Math.max(implicitWidth, root.width * 0.24)
            spacing: 4

            StationTag {
                tag: root.singleStream ? "GRAIN" : "OXIDIZER"
                value: root.singleStream ? root.streamLabel : root.oxidiserLabel
            }
            StationTag {
                visible: !root.singleStream
                tag: "FUEL"
                value: root.fuelLabel + (root.ofText !== "" ? "  ·  " + root.ofText : "")
            }
        }

        Connector {
            Layout.fillWidth: true
            Layout.minimumWidth: 36
            Layout.alignment: Qt.AlignVCenter
            streams: root.singleStream ? 1 : 2
        }

        // ---- the equilibrium chamber ---------------------------------------
        Rectangle {
            id: chamber
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: Math.max(chamberText.implicitWidth + 2 * Metrics.spacing.l, 200)
            Layout.preferredHeight: chamberText.implicitHeight + 2 * Metrics.spacing.s
            color: Theme.surfaceElevated
            border.width: 1
            border.color: root.active ? Theme.textSecondary : Theme.textMuted
            radius: Metrics.radius.s

            Column {
                id: chamberText
                anchors.centerIn: parent
                spacing: 2
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "EQUILIBRIUM CHAMBER"
                    color: root.active ? Theme.text : Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.sectionLabel
                    font.letterSpacing: Typography.sectionTracking
                    font.weight: Typography.medium
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    visible: root.hasResult && root.chamberPressureText !== ""
                    text: root.chamberPressureText
                    textFormat: Text.RichText
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.readoutSmall
                }
            }
        }

        Connector {
            Layout.fillWidth: true
            Layout.minimumWidth: 36
            Layout.alignment: Qt.AlignVCenter
            streams: 1
        }

        // ---- what the solved state holds -----------------------------------
        ColumnLayout {
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: Math.max(160, root.width * 0.26)
            Layout.maximumWidth: Math.max(160, root.width * 0.26)
            spacing: 2

            Text {
                text: "PRODUCTS"
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.sectionLabel
                font.letterSpacing: Typography.sectionTracking
                font.weight: Typography.medium
            }
            Text {
                Layout.fillWidth: true
                visible: root.hasResult && root.productsSummary !== ""
                text: root.productsSummary
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }
    }

    // The honesty label -- not negotiable, per rf-propulsion-visual-grammar --
    // set under the chamber it qualifies. Muted text, not the dimmest token:
    // a statement about what the band claims, not a footnote.
    Text {
        id: honesty
        anchors.top: band.bottom
        anchors.topMargin: Metrics.spacing.xs
        x: Math.max(0, Math.min(root.width - width,
                                chamber.x + chamber.width / 2 - width / 2))
        text: "EQUILIBRIUM STATE SCHEMATIC — NOT A REACTION-FLOW SOLUTION"
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: 0.6
    }
}
