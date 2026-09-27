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
 * A host, exactly like the Isentropic page: header, internal section
 * selector, one of three workspaces. All three read the `ObliqueShock`
 * controller, which is the application-layer adapter over the verified
 * oblique-shock module — which in turn takes every property ratio from the
 * verified normal-shock module.
 *
 *   Calculator  the solved shock: the inputs drawer, β (or both branches),
 *               the jumps, the detached state, and the θ–β–M diagram.
 *   Study       the θ–β–M relation for M₁, and the generated deflection
 *               sweep plotted against θ.
 *   Table       that sweep as an engineering table: rows, ranges, the lens,
 *               pinned blocks, each row on the branch it was generated on.
 *
 * Angles are shown in degrees. The backend works in radians and the service
 * converts at the boundary; nothing here does arithmetic of any kind. The
 * header states the current result, not a constant: a detached request has
 * no calculated shock to claim.
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
                    // The state of the current result, as on Isentropic.
                    RFStatusChip {
                        objectName: "obliqueShockHeaderStatus"
                        anchors.verticalCenter: parent.verticalCenter
                        text: ObliqueShock.valid ? "Calculated" : ObliqueShock.statusLabel
                        tone: ObliqueShock.valid ? "success" : "warning"
                        showDot: false
                    }
                }
            }
        }

        RFSegmentedControl {
            objectName: "obliqueShockSections"
            Layout.preferredWidth: 340
            model: ["Calculator", "Study", "Table"]
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

            ObliqueShockCalculator {}
            ObliqueShockCharts {}
            ObliqueShockTable {}
        }
    }
}
