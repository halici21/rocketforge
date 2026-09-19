import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Diagnostics and provenance, reachable from the Analysis Dock without
 * leaving whichever Trade Study tab is showing the design space.
 *
 * Reuses TradeStudy.diagnosticRows/provenanceRows -- the exact same
 * per-study data StudyResults.qml's own "Diagnostics and provenance" panel
 * already renders -- rather than a second query path, so the two can never
 * disagree. That panel is left exactly as it was; this is an additional
 * place to reach the same evidence, not a replacement for it.
 */
Item {
    id: view

    RFEmptyState {
        anchors.fill: parent
        anchors.margins: Metrics.spacing.m
        visible: !TradeStudy.hasResult
        tag: "NO STUDY"
        title: "No study has been run"
        body: "Diagnostics and provenance appear here once a study has been "
              + "evaluated."
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: Metrics.spacing.m
        visible: TradeStudy.hasResult
        contentWidth: width
        contentHeight: notes.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: RFScrollBar {}

        ColumnLayout {
            id: notes
            width: parent.width
            spacing: 2

            RFSectionLabel {
                text: "Diagnostics"
                visible: TradeStudy.diagnosticRows.length > 0
            }

            Repeater {
                model: TradeStudy.diagnosticRows

                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: Metrics.spacing.s

                    Text {
                        Layout.fillWidth: true
                        text: modelData.code
                        elide: Text.ElideRight
                        color: modelData.severity === "warning"
                               ? Theme.warning : Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        text: modelData.summary
                        color: Theme.textDisabled
                        font.family: Typography.mono
                        font.pixelSize: Typography.meta
                    }
                }
            }

            RFSectionLabel {
                text: "Provenance"
                Layout.topMargin: Metrics.spacing.s
            }

            Repeater {
                model: TradeStudy.provenanceRows

                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: Metrics.spacing.s

                    Text {
                        Layout.preferredWidth: 180
                        text: modelData.label
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.value
                        wrapMode: Text.WordWrap
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }
        }
    }
}
