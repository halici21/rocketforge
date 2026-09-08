import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "prandtlmeyer"

/*
 * Prandtl–Meyer — supersonic expansion around a convex corner.
 *
 * A host, exactly like the other analysis pages: header, internal section
 * selector, one of three workspaces. All three read the `PrandtlMeyer`
 * controller, which is the application-layer adapter over the verified
 * Prandtl–Meyer module.
 *
 * Angles are shown in degrees throughout. The backend works in radians and
 * the service converts at the boundary; nothing here does arithmetic of any
 * kind.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: PrandtlMeyer
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Prandtl–Meyer"
            subtitle: "Supersonic expansion, the turning function, and the Mach angle"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + PrandtlMeyer.gamma.toFixed(3)
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "ν_max " + PrandtlMeyer.nuMax.toFixed(3) + "°"
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

            PrandtlMeyerCalculator {}
            PrandtlMeyerTable {}
            PrandtlMeyerCharts {}
        }
    }
}
