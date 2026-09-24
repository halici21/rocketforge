import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "rocketperformance"

/*
 * Rocket Performance - the ideal rocket model, computed by RocketForge.
 *
 * The third analysis domain, and the first whose numbers this program produces
 * itself. Thermochemistry says what the combustion products are; this says
 * what a nozzle does with them. The two are separate workspaces because they
 * are separate questions with separate owners, and merging them would make the
 * provenance of an Isp impossible to state.
 *
 * Three views of one calculation: the performance itself, the model behind it,
 * and an independent answer from the provider for the same case. They share
 * the controller's single current result, so switching view never recomputes
 * and two views can never disagree.
 *
 * What this workspace refuses to do is the design of it:
 *
 *   - no chamber state, no numbers. Nothing is estimated in place of one.
 *   - no engine size, no thrust. Withheld, never defaulted to zero.
 *   - a nozzle regime outside the ideal model is refused by name rather than
 *     reported with this model's authority attached.
 *   - the provider's own c*, Cf and Isp live in their own panel, are run only
 *     when asked, and never reach a RocketForge field.
 *
 * It works with no chemistry library installed as soon as a chamber state
 * exists, because none of the equations here need one.
 */
Item {
    id: page

    property int section: 0

    // Passed up to the shell, which owns navigation (WorkspaceHost relays it).
    signal workspaceRequested(int index)

    Connections {
        target: RocketPerformance
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Rocket Performance"
            subtitle: "Ideal rocket model — c*, thrust coefficient, thrust, "
                      + "effective exhaust velocity and specific impulse"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Ideal — no efficiency factors"
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: RocketPerformance.hasChamber ? "Chamber state available"
                                                           : "No chamber state"
                        tone: RocketPerformance.hasChamber ? "success" : "warning"
                    }
                }
            }
        }

        RFSegmentedControl {
            Layout.preferredWidth: 420
            model: ["Performance", "Model", "Provider comparison"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            PerfCalculator {
                onWorkspaceRequested: function (index) { page.workspaceRequested(index) }
            }
            PerfModel {}
            PerfOracle {}
        }
    }
}
