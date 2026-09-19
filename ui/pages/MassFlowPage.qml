import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "massflow"

/*
 * Mass Flow - throughput, the choked condition, and what limits it.
 *
 * A host, exactly like the Isentropic page: header, internal section selector,
 * one of three workspaces. All three read the `MassFlow` controller, which is
 * the application-layer adapter over the verified mass-flow module.
 *
 * Nothing on this page computes anything.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: MassFlow
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Mass Flow"
            subtitle: "Throughput, the choked limit, and the mass-flow parameter"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + MassFlow.gamma.toFixed(3)
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
            model: ["Relation", "Calculator", "Table"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            MassFlowCharts {}
            MassFlowCalculator {}
            MassFlowTable {}
        }
    }
}
