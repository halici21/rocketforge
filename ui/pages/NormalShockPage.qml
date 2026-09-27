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
 * A host, exactly like the Isentropic page: header, internal section
 * selector, one of three workspaces. All three read the `NormalShock`
 * controller, which is the application-layer adapter over the verified
 * normal-shock module.
 *
 * Nothing on this page computes anything. The header states the current
 * result, not a constant: with no valid shock there is no calculated state
 * to claim.
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
                    // The state of the current result, as on Isentropic.
                    RFStatusChip {
                        objectName: "normalShockHeaderStatus"
                        anchors.verticalCenter: parent.verticalCenter
                        text: NormalShock.valid ? "Calculated" : NormalShock.statusLabel
                        tone: NormalShock.valid ? "success" : "warning"
                        showDot: false
                    }
                }
            }
        }

        RFSegmentedControl {
            objectName: "normalShockSections"
            Layout.preferredWidth: 340
            model: ["Relation", "Calculator", "Table"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        // A section switch fades in from the side it came from (Motion).
        RFSectionTransition { stack: sections }

        StackLayout {
            id: sections
            objectName: "sectionStack"
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            NormalShockCharts {}
            NormalShockCalculator {}
            NormalShockTable {}
        }
    }
}
