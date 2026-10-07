import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * Thrust Chamber Sizing - the ideal throat and nozzle exit at the candidate
 * selected in the Propellant Trade (LIQ-4).
 *
 * Nothing is solved until Size is pressed. Opening the page, editing the area
 * ratio and changes in the trade or the requirement only re-read the
 * controller. Every number, label, unit and reason comes from the
 * ChamberSizing controller; this file lays them out.
 *
 *   - The operating point is the trade's, shown as the trade resolved it.
 *     Without a selected, current trade candidate there is nothing to size.
 *   - The nozzle design input is stated: the trade's Ae/At, or one typed here.
 *     No optimum expansion is assumed.
 *   - A refusal of the ideal model (an internal shock at the design ambient)
 *     is shown as the reason on every quantity, never as a number.
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
            title: "Thrust Chamber Sizing"
            subtitle: "Ideal throat and nozzle exit at the operating point selected in the Propellant Trade"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Ideal · no chamber geometry or cycle"
                        showDot: false
                    }
                    RFStatusChip {
                        objectName: "sizingStatus"
                        anchors.verticalCenter: parent.verticalCenter
                        text: ChamberSizing.statusLabel
                        tone: ChamberSizing.statusTone
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

                // ---- operating point and nozzle input ------------------
                RFPanel {
                    Layout.fillWidth: true
                    title: "Operating point"

                    Note {
                        visible: !ChamberSizing.hasOperatingPoint
                        text: "From the Propellant Trade: run it and select a candidate."
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: width > 760 ? 2 : 1
                        columnSpacing: Metrics.spacing.l
                        rowSpacing: Metrics.spacing.xs
                        Repeater {
                            model: ChamberSizing.operatingRows
                            delegate: KeyValue {
                                required property var modelData
                                itemName: "sizingOperating"
                                label: modelData.label
                                value: modelData.value
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.l
                        RFNumberField {
                            objectName: "sizingAreaRatio"
                            Layout.fillWidth: false
                            Layout.preferredWidth: 160
                            Layout.alignment: Qt.AlignTop
                            label: "Expansion ratio Ae/At"
                            step: 1
                            text: ChamberSizing.areaRatioText
                            onEdited: ChamberSizing.setAreaRatio(text)
                        }
                        Note {
                            Layout.alignment: Qt.AlignVCenter
                            text: ChamberSizing.tradeAreaRatioText
                        }
                        RFButton {
                            objectName: "sizingRun"
                            Layout.alignment: Qt.AlignBottom
                            text: "Size"
                            variant: "primary"
                            enabled: ChamberSizing.canSize
                            onClicked: ChamberSizing.runSizing()
                        }
                    }

                    Repeater {
                        model: ChamberSizing.issues
                        delegate: Text {
                            objectName: "sizingIssue"
                            required property var modelData
                            Layout.fillWidth: true
                            text: modelData.message
                            color: Theme.warning
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }
                    Note { objectName: "sizingMessage"; text: ChamberSizing.message }
                }

                // ---- the design point ----------------------------------
                RFPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    title: "Design point"

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: !ChamberSizing.hasResult
                        title: "Not sized yet"
                        body: "Select a trade candidate, state the nozzle if the trade had "
                              + "none, then press Size. Nothing is solved until you do."
                    }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: ChamberSizing.hasResult
                        clip: true
                        contentWidth: width
                        contentHeight: groups.height
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: RFScrollBar {}

                        Flow {
                            id: groups
                            width: parent.width
                            spacing: Metrics.spacing.l

                            Repeater {
                                model: ChamberSizing.groups
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
                                            objectName: "sizingRow_" + modelData.key
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
                                                objectName: "sizingValue_" + line.modelData.key
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

            // ---- basis, notes, provenance -------------------------------
            // The operating point is shown once, beside the inputs; this side
            // holds what the result adds to it. It scrolls: the solver notes
            // and the model's assumptions are long and are never cut.
            RFPanel {
                Layout.preferredWidth: 380
                Layout.fillHeight: true
                title: "Sizing basis"

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
                            visible: !ChamberSizing.hasResult
                            text: "Shown with a result: the nozzle it was sized at, the "
                                  + "regime, the solver's notes and the model."
                        }
                        KeyValue {
                            visible: ChamberSizing.hasResult
                            itemName: "sizingAssumption"
                            label: "Nozzle basis"
                            value: ChamberSizing.nozzleBasisText
                        }
                        KeyValue {
                            visible: ChamberSizing.regime !== ""
                            itemName: "sizingRegime"
                            label: "Nozzle regime"
                            value: ChamberSizing.regime + " at the design ambient"
                        }

                        RFDivider { Layout.fillWidth: true; visible: ChamberSizing.noteRows.length > 0 }
                        RFSectionLabel { text: "Solver notes"; visible: ChamberSizing.noteRows.length > 0 }
                        Repeater {
                            model: ChamberSizing.noteRows
                            delegate: Note {
                                required property var modelData
                                objectName: "sizingNote"
                                text: modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: ChamberSizing.hasResult }
                        RFSectionLabel { text: "Model"; visible: ChamberSizing.hasResult }
                        Repeater {
                            model: ChamberSizing.modelAssumptions
                            delegate: Note {
                                required property var modelData
                                text: "· " + modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: ChamberSizing.hasResult }
                        RFSectionLabel { text: "Provenance"; visible: ChamberSizing.hasResult }
                        Repeater {
                            model: ChamberSizing.provenanceRows
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
