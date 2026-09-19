import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "nozzle"

/*
 * Nozzle Lab - quasi-1D converging-diverging flow across the back-pressure range.
 *
 * A host, like the other analysis pages, but with four sections rather than
 * three: the regime map earns its own place, because moving the back pressure
 * and watching the shock migrate is the thing this page exists for.
 *
 * The header states the regime, and states it in the tone the regime deserves:
 * an internal shock is a warning, ideal expansion is a success, and everything
 * else is neutral. That decision belongs to the backend registry, not here.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: Nozzle
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Nozzle Lab"
            subtitle: "Converging-diverging operation, back-pressure regimes and the internal shock"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + Nozzle.gamma.toFixed(3)
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "A_e/A_t " + Nozzle.areaRatio.toFixed(3)
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: Nozzle.regimeLabel
                        tone: Nozzle.regimeTone
                    }
                }
            }
        }

        RFSegmentedControl {
            Layout.preferredWidth: 420
            model: ["Regime map", "Operating point", "Distribution", "Charts"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            NozzleRegimes {}
            NozzleCalculator {}
            NozzleDistribution {}
            NozzleCharts {}
        }
    }
}
