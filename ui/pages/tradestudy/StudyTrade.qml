import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The evaluated trade, in whichever of its two honest shapes this study
 * actually has:
 *
 * - **Sweep** -- one design variable was varied. The primary Trade Study
 *   grammar: response curves against the thing that was swept.
 * - **Design space** -- two or more design variables were varied, so a
 *   single sweep curve cannot represent the study; a 2D scatter/Pareto
 *   projection (StudyPareto.qml, itself generic over any two registered
 *   axes) is the honest picture instead.
 *
 * Defaults to whichever shape the just-evaluated study actually has
 * (TradeStudy.isParametricSweep); a person who picks the other view
 * explicitly keeps seeing it until the next study evaluation changes the
 * shape of the result, the same explicit-overrides-automatic discipline
 * StudyPareto.qml's own axis defaults already use.
 */
Item {
    id: view

    property int mode: TradeStudy.isParametricSweep ? 0 : 1

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            visible: TradeStudy.hasResult
            spacing: Metrics.spacing.m

            RFSegmentedControl {
                model: ["Sweep", "Design space"]
                currentIndex: view.mode
                onSelected: function (index) { view.mode = index }
            }

            RFStatusChip {
                Layout.alignment: Qt.AlignVCenter
                visible: TradeStudy.resultStale
                text: "Setup changed"
                tone: "warning"
            }

            Item { Layout.fillWidth: true }
        }

        StudySweep {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: view.mode === 0
        }

        StudyPareto {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: view.mode === 1
        }
    }
}
