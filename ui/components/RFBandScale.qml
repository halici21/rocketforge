import QtQuick
import "../theme"

/*
 * RFBandScale - a labelled range scale with one active band.
 *
 * Band widths are proportional to the range they cover, so the scale reads as
 * a measurement axis rather than as a row of tabs. The active band is found by
 * hit-testing the current value against the authored band edges - the scale
 * reports where the marker sits, it does not decide anything.
 */
Item {
    id: root

    property var bands: []      // [{ from, to, label }]
    property real from: 0
    property real to: 1
    property real value: 0
    property bool showMarker: true

    readonly property int activeIndex: {
        for (var i = 0; i < bands.length; ++i) {
            if (value >= bands[i].from && (value < bands[i].to || i === bands.length - 1))
                return i
        }
        return -1
    }

    implicitHeight: 30

    Rectangle {
        id: track
        anchors.fill: parent
        anchors.topMargin: root.showMarker ? 6 : 0
        radius: Metrics.radius.m
        color: Theme.surfaceSubtle
        border.width: Metrics.hairline
        border.color: Theme.border
        clip: true

        Row {
            anchors.fill: parent

            Repeater {
                model: root.bands

                delegate: Item {
                    id: band
                    required property var modelData
                    required property int index

                    readonly property bool active: index === root.activeIndex

                    // A band is labelled with whatever actually fits it: the
                    // full name, else the short form, else nothing. Measuring
                    // beats guessing at a pixel threshold, and it keeps two
                    // equally narrow bands from disagreeing with each other.
                    readonly property real labelRoom: width - Metrics.spacing.s

                    width: track.width * (modelData.to - modelData.from) / (root.to - root.from)
                    height: track.height

                    Rectangle {
                        anchors.fill: parent
                        color: band.active ? Theme.accentSubtle : "transparent"
                        Behavior on color { ColorAnimation { duration: Motion.base } }
                    }

                    // Active band is marked by a rule as well as by colour.
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 2
                        color: Theme.accent
                        opacity: band.active ? 1 : 0
                        Behavior on opacity { NumberAnimation { duration: Motion.base } }
                    }

                    Rectangle {
                        anchors.right: parent.right
                        width: Metrics.hairline
                        height: parent.height
                        color: Theme.divider
                        visible: band.index < root.bands.length - 1
                    }

                    TextMetrics {
                        id: fullMetrics
                        font: bandLabel.font
                        text: band.modelData.label
                    }

                    TextMetrics {
                        id: shortMetrics
                        font: bandLabel.font
                        text: band.modelData.short !== undefined ? band.modelData.short : ""
                    }

                    Text {
                        id: bandLabel
                        anchors.centerIn: parent
                        width: band.labelRoom
                        horizontalAlignment: Text.AlignHCenter
                        text: fullMetrics.width <= band.labelRoom ? fullMetrics.text
                            : shortMetrics.width <= band.labelRoom ? shortMetrics.text
                            : ""
                        color: band.active ? Theme.accent : Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.weight: band.active ? Typography.semibold : Typography.regular
                        font.letterSpacing: 0.5
                        font.capitalization: Font.AllUppercase

                        Behavior on color { ColorAnimation { duration: Motion.base } }
                    }
                }
            }
        }
    }

    // Position marker, aligned with the control that drives the value.
    Canvas {
        id: marker
        visible: root.showMarker
        width: 11
        height: 6
        y: 0
        x: (root.value - root.from) / (root.to - root.from) * root.width - width / 2

        readonly property color fill: Theme.accent
        onFillChanged: requestPaint()

        Behavior on x { NumberAnimation { duration: Motion.fast } }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.fillStyle = fill
            ctx.beginPath()
            ctx.moveTo(width / 2, height)
            ctx.lineTo(0, 0)
            ctx.lineTo(width, 0)
            ctx.closePath()
            ctx.fill()
        }
    }
}
