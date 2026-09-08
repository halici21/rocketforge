import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "fanno"

/*
 * Fanno Flow — adiabatic constant-area duct flow with wall friction.
 *
 * A host, exactly like the other analysis pages: header, internal section
 * selector, one of three workspaces. All three read the `Fanno` controller,
 * which is the application-layer adapter over the verified Fanno module.
 *
 * The header states the friction convention, because a duct parameter without
 * one is not a number an engineer can use.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: Fanno
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Fanno Flow"
            subtitle: "Adiabatic duct flow with wall friction, and the choking length"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + Fanno.gamma.toFixed(3)
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "4 f_F L/D"
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

            FannoCalculator {}
            FannoTable {}
            FannoCharts {}
        }
    }
}
