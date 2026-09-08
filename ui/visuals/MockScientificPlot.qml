import QtQuick
import "../theme"
import "../components"
import "../data"

/*
 * The isentropic chart: three ratio curves against Mach number, one inspected
 * operating point, and a cursor that reads the curves as it moves.
 *
 * All curves are hand-authored constants from MockData. The inspector snaps to
 * the nearest stored sample - it looks up an array, it does not evaluate a
 * relation. This component exists to fix the visual language of scientific
 * plotting for the modules that come later.
 */
Item {
    id: root

    property real markerMach: MockData.markerMach
    property int markerSeriesIndex: MockData.markerSeriesIndex
    property var seriesData: MockData.isentropicSeries

    readonly property int sampleCount: seriesData.length > 0 ? seriesData[0].values.length : 0
    readonly property int markerIndex: MockData.nearestSampleIndex(markerMach, sampleCount)

    RFPlotSurface {
        id: surface
        anchors.fill: parent

        xMin: 0
        xMax: 4
        yMin: 0
        yMax: 1
        xTickCount: 5
        yTickCount: 6
        xTitle: "Mach number"
        yTitle: "static / stagnation ratio"
        xFormat: function (v) { return v.toFixed(1) }
        yFormat: function (v) { return v.toFixed(1) }

        legend: [
            { name: root.seriesData[0].name, color: Theme.series[0] },
            { name: root.seriesData[1].name, color: Theme.series[1] },
            { name: root.seriesData[2].name, color: Theme.series[2] }
        ]

        // ---- curves ------------------------------------------------------
        Repeater {
            model: root.seriesData

            delegate: MockLineSeries {
                required property var modelData
                required property int index

                plot: surface
                values: modelData.values
                xStep: MockData.curveMachStep
                color: Theme.series[index]
                thickness: index === root.markerSeriesIndex ? 1.8 : 1.4
                opacity: inspector.active ? 0.55 : (index === root.markerSeriesIndex ? 1 : 0.8)

                Behavior on opacity { NumberAnimation { duration: Motion.base } }
            }
        }

        // ---- inspected operating point -----------------------------------
        Item {
            id: marker
            anchors.fill: parent
            opacity: inspector.active ? 0.25 : 1

            Behavior on opacity { NumberAnimation { duration: Motion.base } }

            Rectangle {
                x: surface.mapX(root.markerMach)
                width: Metrics.hairline
                height: parent.height
                color: Theme.accent
                opacity: 0.45
            }

            Rectangle {
                width: 9
                height: 9
                radius: 4.5
                x: surface.mapX(root.markerMach) - width / 2
                y: surface.mapY(root.seriesData[root.markerSeriesIndex].values[root.markerIndex]) - height / 2
                color: Theme.plotBackground
                border.width: 2
                border.color: Theme.accent
            }

            Rectangle {
                id: markerTag
                x: Math.min(surface.mapX(root.markerMach) + 8, parent.width - width)
                // Sits below the legend row so the two never collide.
                y: 22
                width: tagText.implicitWidth + Metrics.spacing.m
                height: 20
                radius: Metrics.radius.s
                color: Theme.surfaceElevated
                border.width: Metrics.hairline
                border.color: Theme.border

                Text {
                    id: tagText
                    anchors.centerIn: parent
                    text: "M " + root.markerMach.toFixed(3)
                    color: Theme.accent
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                    font.weight: Typography.medium
                }
            }
        }

        // ---- cursor inspector --------------------------------------------
        Item {
            id: inspector
            anchors.fill: parent

            readonly property bool active: hover.hovered
            readonly property int sample: MockData.nearestSampleIndex(
                                              surface.unmapX(hover.point.position.x), root.sampleCount)
            readonly property real sampleMach: sample * MockData.curveMachStep

            HoverHandler { id: hover }

            Rectangle {
                visible: inspector.active
                x: surface.mapX(inspector.sampleMach)
                width: Metrics.hairline
                height: parent.height
                color: Theme.textMuted
            }

            Repeater {
                model: root.seriesData

                delegate: Rectangle {
                    required property var modelData
                    required property int index

                    visible: inspector.active
                    width: 7
                    height: 7
                    radius: 3.5
                    x: surface.mapX(inspector.sampleMach) - width / 2
                    y: surface.mapY(modelData.values[inspector.sample]) - height / 2
                    color: Theme.series[index]
                }
            }

            // Reading card
            Rectangle {
                id: card
                visible: inspector.active
                width: 150
                height: cardColumn.implicitHeight + Metrics.spacing.m
                radius: Metrics.radius.l
                color: Theme.surfaceElevated
                border.width: Metrics.hairline
                border.color: Theme.border
                x: Math.min(surface.mapX(inspector.sampleMach) + 12, parent.width - width)
                y: Math.min(Math.max(0, hover.point.position.y - height / 2), parent.height - height)

                Column {
                    id: cardColumn
                    anchors.centerIn: parent
                    width: parent.width - Metrics.spacing.m
                    spacing: 3

                    Row {
                        width: parent.width
                        Text {
                            text: "M"
                            width: parent.width / 2
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        Text {
                            text: inspector.sampleMach.toFixed(2)
                            width: parent.width / 2
                            horizontalAlignment: Text.AlignRight
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: Metrics.hairline
                        color: Theme.divider
                    }

                    Repeater {
                        model: root.seriesData

                        delegate: Row {
                            required property var modelData
                            required property int index

                            width: cardColumn.width
                            spacing: 6

                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                width: 8
                                height: 2
                                radius: 1
                                color: Theme.series[index]
                            }
                            Text {
                                text: modelData.name
                                width: parent.width / 2 - 14
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                text: modelData.values[inspector.sample].toFixed(3)
                                width: parent.width / 2
                                horizontalAlignment: Text.AlignRight
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                            }
                        }
                    }
                }
            }
        }
    }
}
