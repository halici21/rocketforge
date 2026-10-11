import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "../data"
import "referenceengines"

/*
 * Reference Engines - the shipped reference-engine corpus, read-only (DB-3A).
 *
 * The workspace grammar every Analysis page uses: the library and its filters
 * in the left drawer, the selected engine configuration in the centre as the
 * object, provenance in the shell Inspector, and every recorded assertion and
 * connection in the bottom drawer. Nothing here is computed, edited or solved:
 * the page binds the ReferenceEngines controller, which reads the admitted
 * corpus and prepares every word, position and row shown. The page adds layout
 * and view state only -- which drawer is open, which table, which row is lit.
 */
Item {
    id: page

    readonly property string emptyState: ReferenceEngines.emptyState
    property int tableView: 0      // 0 = assertions, 1 = connections

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Reference Engines"
            subtitle: "A curated, source-backed reference engine database: values as printed, and what each record supports"

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
                        text: ReferenceEngines.configurationCount === 1
                              ? "1 configuration" : ReferenceEngines.configurationCount + " configurations"
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
                objectName: "engineLibraryDrawer"
                Layout.preferredWidth: libraryDrawer.implicitWidth
                Layout.fillHeight: true
                title: "Library"
                summary: ReferenceEngines.filterSummary
                drawerWidth: Math.max(260, Math.min(320, page.width * 0.2))

                EngineLibrary { anchors.fill: parent }
            }

            // ---- the selected configuration, and its rows -------------------
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
                        objectName: "engineRecordScroll"
                        anchors.fill: parent
                        visible: page.emptyState === ""
                        contentWidth: width
                        contentHeight: record.implicitHeight
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: RFScrollBar {}

                        EngineRecord {
                            id: record
                            width: recordScroll.width
                        }

                        Connections {
                            target: ReferenceEngines
                            function onSelectionChanged() { recordScroll.contentY = 0 }
                        }
                    }

                    // Nothing to show: say why, and offer the one way back.
                    RFPanel {
                        objectName: "engineEmptyState"
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
                                           ? "No engine configurations match"
                                           : page.emptyState === "no-records"
                                             ? "No shipped reference engines"
                                             : "The shipped reference-engine corpus could not be read"
                                    body: page.emptyState === "no-match"
                                          ? ReferenceEngines.filterSummary
                                          : page.emptyState === "no-records"
                                            ? "This build ships no reference-engine records, and nothing is shown in their place."
                                            : ReferenceEngines.loadError
                                }

                                RFButton {
                                    objectName: "engineClearFilters"
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    visible: page.emptyState === "no-match"
                                    text: "Clear filters"
                                    onClicked: ReferenceEngines.clearFilters()
                                }
                            }
                        }
                    }
                }

                // ---- every assertion and connection, in a bottom drawer ------
                RFBottomDrawer {
                    id: dataDrawer
                    objectName: "engineDataDrawer"
                    Layout.fillWidth: true
                    Layout.preferredHeight: dataDrawer.implicitHeight
                    visible: page.emptyState === ""
                    open: false
                    title: "Engine data"
                    summary: (ReferenceEngines.tableRowCount === 1 ? "1 assertion" : ReferenceEngines.tableRowCount + " assertions")
                             + "  ·  " + (ReferenceEngines.connectionRowCount === 1 ? "1 connection"
                                          : ReferenceEngines.connectionRowCount + " connections")
                             + "  ·  as printed"
                    drawerHeight: Math.max(240, Math.round(page.height * 0.4))

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: Metrics.spacing.s

                        RFSegmentedControl {
                            objectName: "engineTableSwitch"
                            model: ["Assertions", "Connections"]
                            currentIndex: page.tableView
                            onSelected: function (index) { page.tableView = index }
                        }

                        RFEngineeringTable {
                            objectName: "engineAssertionTable"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: page.tableView === 0 && ReferenceEngines.tableRowCount > 0
                            interactive: true
                            model: ReferenceEngines.tableModel
                            columns: ReferenceEngines.tableColumns
                            firstColumnWidth: 240
                            // Long printed excerpts end in an ellipsis and show
                            // whole on hover; every row opens in the Inspector.
                            columnWidth: 240
                            selectedRow: ReferenceEngines.selectedTableRow
                            onRowClicked: function (row) {
                                ReferenceEngines.inspectTableRow(row)
                                ShellContext.inspectorOpen = true
                            }
                            onEscapePressed: ReferenceEngines.inspectRecord()
                        }

                        RFEngineeringTable {
                            objectName: "engineConnectionTable"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: page.tableView === 1 && ReferenceEngines.connectionRowCount > 0
                            interactive: true
                            model: ReferenceEngines.connectionModel
                            columns: ReferenceEngines.connectionColumns
                            firstColumnWidth: 220
                            columnWidth: 200
                            selectedRow: ReferenceEngines.selectedConnectionRow
                            onRowClicked: function (row) {
                                ReferenceEngines.inspectConnectionRow(row)
                                ShellContext.inspectorOpen = true
                            }
                            onEscapePressed: ReferenceEngines.inspectRecord()
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: (page.tableView === 0 && ReferenceEngines.tableRowCount === 0)
                                     || (page.tableView === 1 && ReferenceEngines.connectionRowCount === 0)
                            text: page.tableView === 0
                                  ? "Nothing is recorded at the configuration itself."
                                  : "No topology ships for this configuration, so it has no recorded connections."
                            wrapMode: Text.WordWrap
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                    }
                }
            }
        }
    }
}
