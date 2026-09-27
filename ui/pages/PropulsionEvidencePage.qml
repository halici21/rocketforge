import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "../data"
import "propulsionevidence"

/*
 * Propulsion Database - the shipped evidence corpus, read-only.
 *
 * The workspace grammar every Analysis page uses: the library and its filters
 * in the left drawer, the selected record in the centre as the object, its
 * provenance in the shell Inspector, and every stored value in the bottom
 * drawer. Nothing here is computed and nothing is solved: the page binds the
 * PropulsionEvidence controller, which reads the shipped records and prepares
 * every word and number shown. The page adds layout and view state only --
 * which drawer is open, which row is highlighted.
 */
Item {
    id: page

    readonly property string emptyState: PropulsionEvidence.emptyState

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Propulsion Database"
            subtitle: "Shipped propulsion evidence: source values as stored, where they are printed, and what each record can support"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Read-only · nothing is solved"
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: PropulsionEvidence.recordCount === 1
                              ? "1 record" : PropulsionEvidence.recordCount + " records"
                        showDot: false
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            // ---- library and filters ---------------------------------------
            RFWorkspaceDrawer {
                id: libraryDrawer
                objectName: "evidenceLibraryDrawer"
                Layout.preferredWidth: libraryDrawer.implicitWidth
                Layout.fillHeight: true
                title: "Library"
                summary: PropulsionEvidence.filterSummary
                drawerWidth: Math.max(260, Math.min(320, page.width * 0.2))

                EvidenceLibrary { anchors.fill: parent }
            }

            // ---- the selected record, and its values -----------------------
            ColumnLayout {
                id: centerColumn
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.spacing.m

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Flickable {
                        id: recordScroll
                        objectName: "evidenceRecordScroll"
                        anchors.fill: parent
                        visible: page.emptyState === ""
                        contentWidth: width
                        contentHeight: record.implicitHeight
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: RFScrollBar {}

                        EvidenceRecord {
                            id: record
                            width: recordScroll.width
                        }
                    }

                    // No record to show: say why, and offer the one way back.
                    RFPanel {
                        objectName: "evidenceEmptyState"
                        anchors.fill: parent
                        visible: page.emptyState !== ""

                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true

                            Column {
                                anchors.centerIn: parent
                                width: Math.min(560, parent.width - Metrics.spacing.xl * 2)
                                spacing: Metrics.spacing.l

                                RFEmptyState {
                                    width: parent.width
                                    tag: page.emptyState === "no-match" ? "No match"
                                       : page.emptyState === "no-records" ? "Empty corpus"
                                       : "Not loaded"
                                    title: page.emptyState === "no-match"
                                           ? "No records match the current filters"
                                           : page.emptyState === "no-records"
                                             ? "No shipped evidence records"
                                             : "The shipped evidence could not be read"
                                    body: page.emptyState === "no-match"
                                          ? PropulsionEvidence.filterSummary
                                          : page.emptyState === "no-records"
                                            ? "This build ships no evidence records, and nothing is shown in their place."
                                            : PropulsionEvidence.loadError
                                }

                                RFButton {
                                    objectName: "evidenceClearFilters"
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    visible: page.emptyState === "no-match"
                                    text: "Clear filters"
                                    onClicked: PropulsionEvidence.clearFilters()
                                }
                            }
                        }
                    }
                }

                // ---- every stored value, in a bottom drawer ------------------
                RFBottomDrawer {
                    id: dataDrawer
                    objectName: "evidenceDataDrawer"
                    Layout.fillWidth: true
                    Layout.preferredHeight: dataDrawer.implicitHeight
                    visible: page.emptyState === ""
                    // Where the screen has room for both (1440p and up), the
                    // stored values fill the space below the record instead
                    // of leaving it empty; elsewhere they wait behind the
                    // handle. A click on the handle replaces this default.
                    open: page.height >= 1200
                    title: "Evidence data"
                    summary: PropulsionEvidence.tableRowCount === 1 ? "1 row" : PropulsionEvidence.tableRowCount + " rows  ·  stored values, units as printed"
                    // On a tall screen, the room the record leaves (the record
                    // stays whole, the values fill the rest); where the record
                    // cannot fit anyway, the usual 40 % of the page.
                    readonly property real leftover: centerColumn.height - record.implicitHeight
                                                     - centerColumn.spacing
                    drawerHeight: leftover >= 220 ? Math.min(Math.round(page.height * 0.45), leftover)
                                                  : Math.max(220, Math.round(page.height * 0.4))

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: Metrics.spacing.s

                        Text {
                            objectName: "evidencePayloadNote"
                            Layout.fillWidth: true
                            visible: PropulsionEvidence.tableRowCount === 0
                            text: PropulsionEvidence.payloadNote
                            wrapMode: Text.WordWrap
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }

                        RFEngineeringTable {
                            id: evidenceTable
                            objectName: "evidenceTable"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: PropulsionEvidence.tableRowCount > 0
                            interactive: true
                            model: PropulsionEvidence.tableModel
                            columns: PropulsionEvidence.tableColumns
                            firstColumnWidth: 250
                            // A floor wide enough for the longest stored unit
                            // and source id ("atoms per formula unit"): the
                            // table scrolls sideways inside its own surface
                            // rather than letting a cell run into the next.
                            // Full locators are in the Inspector.
                            columnWidth: 200
                            selectedRow: PropulsionEvidence.selectedTableRow
                            onRowClicked: function (row) {
                                PropulsionEvidence.inspectTableRow(row)
                                ShellContext.inspectorOpen = true
                            }
                            onEscapePressed: PropulsionEvidence.inspectRecord()
                        }
                    }
                }
            }
        }
    }
}
