import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "obliqueshock"

/*
 * Oblique Shock — a straight attached wave over a planar wedge.
 *
 * A host, exactly like the other analysis pages: header, internal section
 * selector, one of three workspaces. All three read the `ObliqueShock`
 * controller, which is the application-layer adapter over the verified
 * oblique-shock module — which in turn takes every property ratio from the
 * verified normal-shock module.
 *
 * Angles are shown in degrees. The backend works in radians and the service
 * converts at the boundary; nothing here does arithmetic of any kind.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: ObliqueShock
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Oblique Shock"
            subtitle: "Wave angle, deflection, and the attachment limit"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "M₁ " + ObliqueShock.mach1.toFixed(2)
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + ObliqueShock.gamma.toFixed(3)
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
            Layout.preferredWidth: 240
            model: ["Calculator", "Study"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            ObliqueShockCalculator {}
            ObliqueShockCharts {}
        }
    }
}
