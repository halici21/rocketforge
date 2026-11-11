import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "referencecases"

/*
 * Reference Cases - DB-4C's ideal reference points, compared, never judged.
 *
 * Four points from two 1985 TDK documents: what each printout prints, and,
 * after an explicit Run, step A (the printout beside NASA CEA) and step B
 * (RocketForge's constant-gamma reduction beside CEA), in separate panels,
 * one point at a time (DB4C_IDEAL_REFERENCE_DISPLAY.md). Nothing is computed
 * on opening the page or on choosing a point, and a run keeps nothing from the
 * last. The point list shows inputs and run state only, never a difference,
 * so no screen sets two points side by side.
 *
 * Every word and number comes from the ReferenceCases controller. The page
 * places text; it computes, rounds and colours nothing by its value.
 */
Item {
    id: page

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Reference Cases"
            subtitle: "Published 1985 TDK printouts beside NASA CEA, and RocketForge's reduction beside CEA: compared, never judged"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        objectName: "referenceCasesProviderChip"
                        anchors.verticalCenter: parent.verticalCenter
                        text: ReferenceCases.providerUsable ? "NASA CEA available" : "NASA CEA unavailable"
                        tone: ReferenceCases.providerUsable ? "neutral" : "warning"
                    }
                    RFButton {
                        objectName: "referenceCasesRun"
                        anchors.verticalCenter: parent.verticalCenter
                        variant: "primary"
                        text: ReferenceCases.busy ? "Running…" : "Run all four points"
                        enabled: ReferenceCases.providerUsable && !ReferenceCases.busy
                        onClicked: ReferenceCases.run()
                    }
                }
            }
        }

        // What the last run did, or that there has been none; and, with no
        // provider, why the Run button is off.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.xs

            Text {
                objectName: "referenceCasesRunSummary"
                Layout.fillWidth: true
                text: ReferenceCases.runSummary
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
            Text {
                objectName: "referenceCasesProviderLine"
                Layout.fillWidth: true
                visible: !ReferenceCases.providerUsable
                text: ReferenceCases.providerLine
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            RFWorkspaceDrawer {
                id: listDrawer
                objectName: "referenceCasesListDrawer"
                Layout.preferredWidth: listDrawer.implicitWidth
                Layout.fillHeight: true
                title: "Points"
                summary: "4 points from two 1985 documents"
                drawerWidth: Math.max(260, Math.min(320, page.width * 0.2))

                CaseList { anchors.fill: parent }
            }

            Flickable {
                id: recordScroll
                objectName: "referenceCasesRecordScroll"
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: record.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                CaseRecord {
                    id: record
                    width: recordScroll.width
                }
            }
        }
    }
}
