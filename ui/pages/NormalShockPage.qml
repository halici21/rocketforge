import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "normalshock"

/*
 * Normal Shock - the property jumps across a stationary shock.
 *
 * A host, exactly like the Isentropic and Mass Flow pages: header, internal
 * section selector, one of three workspaces. All three read the `NormalShock`
 * controller, which is the application-layer adapter over the verified
 * normal-shock module.
 *
 * Nothing on this page computes anything.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: NormalShock
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Normal Shock"
            subtitle: "Property jumps across a stationary normal shock"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + NormalShock.gamma.toFixed(3)
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

            NormalShockCalculator {}
            NormalShockTable {}
            NormalShockCharts {}
        }
    }
}
