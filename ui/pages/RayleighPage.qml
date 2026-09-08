import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "rayleigh"

/*
 * Rayleigh Flow — frictionless constant-area duct flow with heat exchange.
 *
 * A host, exactly like the other analysis pages: header, internal section
 * selector, one of three workspaces. All three read the `Rayleigh` controller,
 * which is the application-layer adapter over the verified Rayleigh module.
 *
 * The header carries both critical Mach numbers, because the whole point of
 * this page is that they are not the same point: the static temperature peaks
 * at M = 1/√γ and the stagnation temperature at M = 1.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: Rayleigh
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Rayleigh Flow"
            subtitle: "Heat exchange in a constant-area duct, and thermal choking"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + Rayleigh.gamma.toFixed(3)
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "T max  M " + Rayleigh.staticTemperatureMaxMach.toFixed(4)
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Calculated"
                        tone: "success"
                        showDot: false
                    }
                }
            }
        }

        RFSegmentedControl {
            Layout.preferredWidth: 340
            model: ["Calculator", "Table", "Charts"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            RayleighCalculator {}
            RayleighTable {}
            RayleighCharts {}
        }
    }
}
