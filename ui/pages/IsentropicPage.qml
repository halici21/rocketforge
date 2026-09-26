import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "isentropic"

/*
 * Isentropic Flow - the first analysis page backed by real physics.
 *
 * The page itself is a host: a header, an internal section selector, and one
 * of three workspaces. All three read the `Isentropic` controller, which is
 * the application-layer adapter over the verified compressible-flow module.
 *
 * Nothing on this page computes anything. The mock values this page used to
 * display are gone rather than kept as a fallback, because a placeholder that
 * looks like a result is worse than an empty field.
 *
 * The section selector is an internal control, not a second level of global
 * navigation: the left rail still owns where you are in the application.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: Isentropic
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Isentropic Flow"
            subtitle: "Perfect-gas compressible-flow relations"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "γ " + Isentropic.gamma.toFixed(3)
                        showDot: false
                    }
                    // The state of the current result, not a constant: with
                    // invalid input there is no calculated state to claim.
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: Isentropic.valid ? "Calculated" : Isentropic.statusLabel
                        tone: Isentropic.valid ? "success" : "warning"
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

        // A section switch fades in from the side it came from (Motion).
        RFSectionTransition { stack: sections }

        StackLayout {
            id: sections
            objectName: "sectionStack"
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            IsentropicCharts {}
            IsentropicCalculator {}
            IsentropicTable {}
        }
    }
}
