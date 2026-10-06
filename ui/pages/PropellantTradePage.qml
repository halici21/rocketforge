import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * Propellant Trade - how the catalogue pairs compare for the current engine
 * requirement (LIQ-3).
 *
 * Nothing is solved until Run trade is pressed. Opening the page, editing a
 * study setting, sorting a column and selecting a row only re-read the
 * controller. Every number, label, unit and reason comes from the
 * PropellantTrade controller; this file lays them out.
 *
 *   - The operating point is stated, never filled in. Where the requirement
 *     leaves chamber pressure or O/F open, the study asks for it; until then
 *     the reasons are listed and Run trade stays disabled.
 *   - The nozzle is stated, never assumed. Chamber-only is the starting basis,
 *     and every quantity that needs a nozzle shows "—" with its reason.
 *   - Ordering follows one displayed column, chosen by the user. There is no
 *     score and no "best": choosing a pair is the user's act.
 */
Item {
    id: page

    readonly property var columns: PropellantTrade.metricColumns
    readonly property int pairWidth: 230
    readonly property int cellWidth: 118

    component Note: Text {
        Layout.fillWidth: true
        visible: text !== ""
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        wrapMode: Text.WordWrap
    }

    component Cell: Text {
        property bool head: false
        width: page.cellWidth
        rightPadding: Metrics.spacing.s
        wrapMode: head ? Text.WordWrap : Text.NoWrap
        maximumLineCount: 2
        horizontalAlignment: Text.AlignRight
        elide: Text.ElideRight
        color: head ? Theme.textSecondary : Theme.text
        font.family: head ? Typography.sans : Typography.mono
        font.pixelSize: Typography.meta
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Propellant Trade"
            subtitle: "Catalogue pairs compared for the current engine requirement, at a stated operating point"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "No score · no cycle analysis"
                        showDot: false
                    }
                    RFStatusChip {
                        objectName: "tradeStatus"
                        anchors.verticalCenter: parent.verticalCenter
                        text: PropellantTrade.statusLabel
                        tone: !PropellantTrade.hasResult ? "neutral"
                              : PropellantTrade.resultStale ? "warning" : "success"
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

                // ---- study setup ---------------------------------------
                RFPanel {
                    Layout.fillWidth: true
                    title: "Study"

                    Note {
                        objectName: "tradeCandidates"
                        text: PropellantTrade.candidateLabels.length + " candidate"
                              + (PropellantTrade.candidateLabels.length === 1 ? "" : "s")
                              + ": " + PropellantTrade.candidateLabels.join(", ")
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.l

                        RFNumberField {
                            objectName: "tradeStudyPressure"
                            Layout.fillWidth: false
                            Layout.preferredWidth: 190
                            Layout.alignment: Qt.AlignTop
                            visible: PropellantTrade.pressureNeeded
                            label: "Study chamber pressure"
                            unit: "MPa"
                            step: 0.5
                            text: PropellantTrade.studyPressureText
                            onEdited: PropellantTrade.setStudyPressure(text)
                        }

                        ColumnLayout {
                            Layout.fillWidth: false
                            Layout.alignment: Qt.AlignTop
                            visible: PropellantTrade.ratioNeeded
                            RFSectionLabel { text: "Study O/F" }
                            RowLayout {
                                spacing: Metrics.spacing.m
                                RFSegmentedControl {
                                    objectName: "tradeRatioMode"
                                    Layout.preferredWidth: 300
                                    model: ["Not chosen", "Catalogue", "Stated"]
                                    currentIndex: ["", "catalogue", "explicit"].indexOf(
                                                      PropellantTrade.ratioMode)
                                    onSelected: function (index) {
                                        PropellantTrade.setRatioMode(["", "catalogue", "explicit"][index])
                                    }
                                }
                                RFNumberField {
                                    objectName: "tradeStudyRatio"
                                    Layout.preferredWidth: 110
                                    visible: PropellantTrade.ratioMode === "explicit"
                                    label: "O/F (mass)"
                                    step: 0.1
                                    text: PropellantTrade.studyRatioText
                                    onEdited: PropellantTrade.setStudyRatio(text)
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.l
                        ColumnLayout {
                            Layout.fillWidth: false
                            RFSectionLabel { text: "Performance basis" }
                            RFSegmentedControl {
                                objectName: "tradeBasis"
                                Layout.preferredWidth: 320
                                model: ["Chamber only", "Ideal, stated Ae/At"]
                                currentIndex: PropellantTrade.performanceBasis === "chamber_only" ? 0 : 1
                                onSelected: function (index) {
                                    PropellantTrade.setPerformanceBasis(
                                        index === 0 ? "chamber_only" : "ideal_area_ratio")
                                }
                            }
                        }
                        RFNumberField {
                            objectName: "tradeAreaRatio"
                            Layout.fillWidth: false
                            Layout.preferredWidth: 130
                            visible: PropellantTrade.performanceBasis === "ideal_area_ratio"
                            label: "Area ratio Ae/At"
                            step: 1
                            text: PropellantTrade.areaRatioText
                            onEdited: PropellantTrade.setAreaRatio(text)
                        }
                        ColumnLayout {
                            Layout.fillWidth: false
                            RFSectionLabel { text: "Gamma basis" }
                            RFSegmentedControl {
                                objectName: "tradeGamma"
                                Layout.preferredWidth: 220
                                model: ["Frozen", "Equilibrium"]
                                currentIndex: PropellantTrade.gammaBasis === "frozen" ? 0 : 1
                                onSelected: function (index) {
                                    PropellantTrade.setGammaBasis(index === 0 ? "frozen" : "equilibrium")
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                        RFButton {
                            objectName: "tradeRun"
                            Layout.alignment: Qt.AlignBottom
                            text: PropellantTrade.busy ? PropellantTrade.progressText : "Run trade"
                            variant: "primary"
                            enabled: PropellantTrade.canRun
                            onClicked: PropellantTrade.runTrade()
                        }
                    }
                    Note { text: "Ambient: " + PropellantTrade.ambientText }

                    Repeater {
                        model: PropellantTrade.issues
                        delegate: Text {
                            objectName: "tradeIssue"
                            required property var modelData
                            Layout.fillWidth: true
                            text: modelData.message
                            color: Theme.warning
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }
                    Note { objectName: "tradeMessage"; text: PropellantTrade.message }
                }

                // ---- results -------------------------------------------
                RFPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    title: "Candidates"

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: !PropellantTrade.hasResult
                        title: "No trade yet"
                        body: "Resolve the study inputs above, then run the trade. "
                              + "Nothing is evaluated until you do."
                    }

                    Flickable {
                        id: grid
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: PropellantTrade.hasResult
                        clip: true
                        contentWidth: table.width
                        contentHeight: table.height
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.horizontal: RFScrollBar {}
                        ScrollBar.vertical: RFScrollBar {}

                        Column {
                            id: table
                            spacing: 2

                            Row {
                                spacing: 0
                                Text {
                                    width: page.pairWidth
                                    text: "Pair · O/F"
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Repeater {
                                    model: page.columns
                                    delegate: Cell {
                                        id: head
                                        required property var modelData
                                        objectName: "tradeHeader_" + modelData.key
                                        head: true
                                        text: modelData.label
                                              + (modelData.unit !== "" ? " [" + modelData.unit + "]" : "")
                                              + (PropellantTrade.sortKey === modelData.key
                                                 ? (PropellantTrade.sortDescending ? " ↓" : " ↑") : "")
                                        TapHandler { onTapped: PropellantTrade.sortBy(head.modelData.key) }
                                        HoverHandler { id: headHover }
                                        RFTooltip { visible: headHover.hovered; text: head.modelData.note }
                                    }
                                }
                            }

                            Repeater {
                                model: PropellantTrade.rows
                                delegate: Rectangle {
                                    id: row
                                    required property var modelData
                                    objectName: "tradeRow_" + modelData.key
                                    width: page.pairWidth + page.columns.length * page.cellWidth
                                    height: 30
                                    radius: Metrics.radius.s
                                    color: modelData.selected ? Theme.accentSubtle
                                         : rowHover.hovered ? Theme.surfaceSubtle : "transparent"

                                    HoverHandler { id: rowHover }
                                    RFTooltip {
                                        visible: rowHover.hovered && text !== ""
                                        text: row.modelData.message !== "" ? row.modelData.message
                                              : row.modelData.notes.length > 0 ? row.modelData.notes[0] : ""
                                    }
                                    TapHandler {
                                        enabled: row.modelData.ok
                                        onTapped: PropellantTrade.selectCandidate(
                                                      row.modelData.selected ? "" : row.modelData.key)
                                    }

                                    Row {
                                        anchors.verticalCenter: parent.verticalCenter
                                        Text {
                                            width: page.pairWidth
                                            text: row.modelData.label + " · " + row.modelData.ratio
                                                  + (row.modelData.status === "failed" ? "  (failed)"
                                                     : row.modelData.status === "warning" ? "  · note" : "")
                                            elide: Text.ElideRight
                                            color: row.modelData.ok ? Theme.text : Theme.warning
                                            font.family: Typography.sans
                                            font.pixelSize: Typography.meta
                                        }
                                        Repeater {
                                            model: page.columns
                                            delegate: Cell {
                                                required property var modelData
                                                text: row.modelData.values[modelData.key]
                                                color: row.modelData.unresolved[modelData.key] !== undefined
                                                       ? Theme.textMuted : Theme.text
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ---- assumptions, selection, provenance --------------------
            RFPanel {
                Layout.preferredWidth: 380
                Layout.fillHeight: true
                title: "Operating assumptions"

                Note {
                    visible: !PropellantTrade.hasResult
                    text: "Shown with a result: every row was computed at these."
                }
                Repeater {
                    model: PropellantTrade.assumptionRows
                    delegate: RowLayout {
                        id: assumption
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s
                        Text {
                            Layout.preferredWidth: 120
                            text: assumption.modelData.label
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        Text {
                            objectName: "tradeAssumption"
                            Layout.fillWidth: true
                            text: assumption.modelData.value
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                RFDivider { Layout.fillWidth: true }
                RFSectionLabel { text: "Selection" }
                Note {
                    objectName: "tradeSelection"
                    text: PropellantTrade.selectedKey === ""
                          ? "Click a successful row to choose it. Nothing is chosen for you."
                          : "Chosen: " + PropellantTrade.selectedLabel
                }
                RFButton {
                    objectName: "tradeApply"
                    text: "Use for Engine Requirement"
                    compact: true
                    enabled: PropellantTrade.selectedKey !== "" && !PropellantTrade.resultStale
                    onClicked: PropellantTrade.applySelectionToRequirement()
                }

                RFDivider { Layout.fillWidth: true }
                RFSectionLabel { text: "Provenance" }
                Repeater {
                    model: PropellantTrade.provenanceRows
                    delegate: Note {
                        required property var modelData
                        text: modelData.label + ": " + modelData.value
                    }
                }
                Item { Layout.fillHeight: true }
            }
        }
    }
}
