import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "thermochemistry"

/*
 * Thermochemistry - ideal adiabatic HP chamber equilibrium.
 *
 * The second analysis domain. Four views of one calculation: the chamber
 * state, what the mixture is made of, how it changes with O/F, and whether the
 * pipeline reproduces an accepted external case. They share the controller's
 * single current result, so switching view never re-solves and two views can
 * never show different calculations.
 *
 * Everything before the views is the honest framing: the model summary is in
 * the header, beside the title, because a chamber temperature without
 * "adiabatic HP equilibrium" attached is a number a user will read as a
 * prediction of a real engine.
 *
 * With no provider installed the whole workspace collapses to one honest
 * screen. That is a supported configuration - the base environment ships no
 * chemistry library - and not an error.
 */
Item {
    id: page

    property int section: 0

    readonly property bool available: Thermochemistry.providerAvailable

    Connections {
        target: Thermochemistry
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Thermochemistry"
            subtitle: "Ideal adiabatic HP chamber equilibrium, solved by a thermochemistry provider"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: page.available
                        text: Thermochemistry.modelSummary
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: page.available ? Thermochemistry.providerHeadline
                                             : "Provider unavailable"
                        tone: page.available ? "success" : "warning"
                    }
                }
            }
        }

        RFSegmentedControl {
            Layout.preferredWidth: 460
            visible: page.available
            model: ["Calculator", "Composition", "Sweep", "References"]
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
            currentIndex: page.available ? page.section : 4

            ThermoCalculator {}
            ThermoComposition {}
            ThermoSweep {}
            ThermoReferences {}
            ThermoProviderUnavailable {}
        }
    }
}
