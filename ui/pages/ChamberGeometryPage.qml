import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * Combustion Chamber Geometry - the chamber upstream of the throat sized in
 * Thrust Chamber Sizing (LIQ-5).
 *
 * Nothing is computed until Compute is pressed. Opening the page, editing an
 * input and changes upstream only re-read the controller. Every number, label,
 * unit and reason comes from the ChamberGeometry controller; this file lays
 * them out, and the section sketch draws the controller's own profile points.
 *
 *   - The throat is LIQ-4's, shown as it was sized. Without an accepted,
 *     current sizing there is nothing to extend.
 *   - L*, Ac/At and the converging half-angle are stated. None has a default.
 *   - A converging section larger than L* · At is refused, never adjusted.
 */
Item {
    id: page

    component Note: Text {
        Layout.fillWidth: true
        visible: text !== ""
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        wrapMode: Text.WordWrap
    }

    component KeyValue: RowLayout {
        id: kv
        property string label
        property string value
        property string itemName: ""
        Layout.fillWidth: true
        spacing: Metrics.spacing.s
        Text {
            Layout.preferredWidth: 130
            text: kv.label
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            objectName: kv.itemName
            Layout.fillWidth: true
            text: kv.value
            color: Theme.text
            font.family: Typography.mono
            font.pixelSize: Typography.meta
            wrapMode: Text.WordWrap
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Combustion Chamber Geometry"
            subtitle: "Chamber volume, diameter and lengths upstream of the sized throat, from a stated L*"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Cylinder + cone · no injector, cooling or cycle"
                        showDot: false
                    }
                    RFStatusChip {
                        objectName: "geometryStatus"
                        anchors.verticalCenter: parent.verticalCenter
                        text: ChamberGeometry.statusLabel
                        tone: ChamberGeometry.statusTone
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.spacing.m

                // ---- throat and stated inputs --------------------------
                RFPanel {
                    Layout.fillWidth: true
                    title: "Throat and chamber inputs"

                    Note {
                        visible: !ChamberGeometry.hasThroat
                        text: "From Thrust Chamber Sizing: size a selected trade candidate first."
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: width > 760 ? 2 : 1
                        columnSpacing: Metrics.spacing.l
                        rowSpacing: Metrics.spacing.xs
                        Repeater {
                            model: ChamberGeometry.basisRows
                            delegate: KeyValue {
                                required property var modelData
                                itemName: "geometryBasis"
                                label: modelData.label
                                value: modelData.value
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.l
                        RFNumberField {
                            objectName: "geometryLStar"
                            Layout.fillWidth: false
                            Layout.preferredWidth: 170
                            label: "Characteristic length L*"
                            unit: "m"
                            step: 0.1
                            text: ChamberGeometry.characteristicLengthText
                            onEdited: ChamberGeometry.setCharacteristicLength(text)
                        }
                        RFNumberField {
                            objectName: "geometryContraction"
                            Layout.fillWidth: false
                            Layout.preferredWidth: 170
                            label: "Contraction ratio Ac/At"
                            step: 0.5
                            text: ChamberGeometry.contractionRatioText
                            onEdited: ChamberGeometry.setContractionRatio(text)
                        }
                        RFNumberField {
                            objectName: "geometryHalfAngle"
                            Layout.fillWidth: false
                            Layout.preferredWidth: 170
                            label: "Converging half-angle"
                            unit: "°"
                            step: 1
                            text: ChamberGeometry.halfAngleText
                            onEdited: ChamberGeometry.setHalfAngle(text)
                        }
                        Item { Layout.fillWidth: true }
                        RFButton {
                            objectName: "geometryRun"
                            Layout.alignment: Qt.AlignBottom
                            text: "Compute"
                            variant: "primary"
                            enabled: ChamberGeometry.canCompute
                            onClicked: ChamberGeometry.computeGeometry()
                        }
                    }

                    Repeater {
                        model: ChamberGeometry.issues
                        delegate: Text {
                            objectName: "geometryIssue"
                            required property var modelData
                            Layout.fillWidth: true
                            text: modelData.message
                            color: Theme.warning
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }
                    Note { objectName: "geometryMessage"; text: ChamberGeometry.message }
                }

                // ---- the geometry --------------------------------------
                RFPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    title: "Chamber"

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: !ChamberGeometry.hasResult
                        title: "Not computed yet"
                        body: "State L*, Ac/At and the converging half-angle, then press "
                              + "Compute. Nothing is computed until you do."
                    }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: ChamberGeometry.hasResult
                        clip: true
                        contentWidth: width
                        contentHeight: body.implicitHeight
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: RFScrollBar {}

                        ColumnLayout {
                            id: body
                            width: parent.width
                            spacing: Metrics.spacing.m

                            // Half-section, injector face (left) to throat
                            // (right), to scale. Drawn from the controller's
                            // profile points; nothing is computed here.
                            Canvas {
                                id: sketch
                                objectName: "geometrySketch"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 220
                                visible: ChamberGeometry.profile.length > 0
                                property var points: ChamberGeometry.profile
                                property color line: Theme.accent
                                property color axis: Theme.textMuted
                                onPointsChanged: requestPaint()
                                onLineChanged: requestPaint()
                                onWidthChanged: requestPaint()
                                onPaint: {
                                    var ctx = getContext("2d")
                                    ctx.reset()
                                    if (points.length < 4) return
                                    var xmax = points[3].x, rmax = points[1].r
                                    var pad = 12
                                    var s = Math.min((width - 2 * pad) / xmax,
                                                     (height - 2 * pad) / (2 * rmax))
                                    var cy = height / 2
                                    var x0 = (width - xmax * s) / 2
                                    function X(x) { return x0 + x * s }
                                    ctx.strokeStyle = axis
                                    ctx.lineWidth = 1
                                    ctx.setLineDash([4, 4])
                                    ctx.beginPath(); ctx.moveTo(X(0) - 6, cy); ctx.lineTo(X(xmax) + 6, cy)
                                    ctx.stroke()
                                    ctx.setLineDash([])
                                    ctx.strokeStyle = line
                                    ctx.lineWidth = 2
                                    for (var side = -1; side <= 1; side += 2) {
                                        ctx.beginPath()
                                        for (var i = 0; i < points.length; ++i) {
                                            var px = X(points[i].x), py = cy + side * points[i].r * s
                                            if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py)
                                        }
                                        ctx.stroke()
                                    }
                                }
                            }
                            Note {
                                visible: sketch.visible
                                text: "Half-sections to scale: injector face at left, throat at right. "
                                      + "Corner radii are neglected, as in the volume."
                            }

                            Flow {
                                Layout.fillWidth: true
                                spacing: Metrics.spacing.l

                                Repeater {
                                    model: ChamberGeometry.groups
                                    delegate: Column {
                                        id: group
                                        required property var modelData
                                        width: 420
                                        spacing: 2

                                        RFSectionLabel { text: group.modelData.title }
                                        Repeater {
                                            model: group.modelData.rows
                                            delegate: Item {
                                                id: line
                                                required property var modelData
                                                objectName: "geometryRow_" + modelData.key
                                                width: group.width
                                                height: 24
                                                HoverHandler { id: lineHover }
                                                RFTooltip {
                                                    visible: lineHover.hovered
                                                    text: line.modelData.reason !== ""
                                                          ? line.modelData.reason : line.modelData.note
                                                }
                                                Text {
                                                    anchors.left: parent.left
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    width: 210
                                                    text: line.modelData.label
                                                    elide: Text.ElideRight
                                                    color: Theme.textSecondary
                                                    font.family: Typography.sans
                                                    font.pixelSize: Typography.meta
                                                }
                                                Text {
                                                    objectName: "geometryValue_" + line.modelData.key
                                                    anchors.right: unit.left
                                                    anchors.rightMargin: Metrics.spacing.s
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    text: line.modelData.value
                                                    color: line.modelData.reason !== ""
                                                           ? Theme.textMuted : Theme.text
                                                    font.family: Typography.mono
                                                    font.pixelSize: Typography.meta
                                                }
                                                Text {
                                                    id: unit
                                                    anchors.right: parent.right
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    width: 48
                                                    text: line.modelData.unit
                                                    color: Theme.textMuted
                                                    font.family: Typography.sans
                                                    font.pixelSize: Typography.meta
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ---- advisories, model, provenance --------------------------
            RFPanel {
                Layout.preferredWidth: 380
                Layout.fillHeight: true
                title: "Geometry basis"

                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: width
                    contentHeight: side.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: RFScrollBar {}

                    ColumnLayout {
                        id: side
                        width: parent.width - Metrics.spacing.m
                        spacing: Metrics.spacing.m

                        Note {
                            visible: !ChamberGeometry.hasResult
                            text: "Shown with a result: advisories, the model and where the "
                                  + "throat came from."
                        }

                        RFSectionLabel { text: "Advisories"; visible: ChamberGeometry.noteRows.length > 0 }
                        Repeater {
                            model: ChamberGeometry.noteRows
                            delegate: Note {
                                required property var modelData
                                objectName: "geometryNote"
                                text: modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: ChamberGeometry.hasResult }
                        RFSectionLabel { text: "Model"; visible: ChamberGeometry.hasResult }
                        Repeater {
                            model: ChamberGeometry.modelAssumptions
                            delegate: Note {
                                required property var modelData
                                text: "· " + modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: ChamberGeometry.hasResult }
                        RFSectionLabel { text: "Provenance"; visible: ChamberGeometry.hasResult }
                        Repeater {
                            model: ChamberGeometry.provenanceRows
                            delegate: Note {
                                required property var modelData
                                text: modelData.label + ": " + modelData.value
                            }
                        }
                    }
                }
            }
        }
    }
}
