import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "tradestudy"

/*
 * Trade Study - the design-space and decision layer.
 *
 * The fourth analysis domain, and the first that computes no physics of its
 * own. Thermochemistry says what the products are; Rocket Performance says
 * what a nozzle does with them; this evaluates a grid of both and helps a
 * person choose. The chain it preserves, one way only:
 *
 *     DESIGN VARIABLE -> PHYSICS -> RAW RESULT -> CONSTRAINT -> FEASIBILITY
 *                     -> OBJECTIVE -> PARETO / OPTIONAL SCORE -> DECISION
 *
 * Four views of one study. They share the controller's single current result,
 * so switching never re-evaluates and two views cannot disagree.
 *
 * What this workspace refuses to do is the design of it:
 *
 *   - it never claims a global optimum. A finite sampled grid cannot
 *     establish one, and nothing here searches for one.
 *   - a constraint is satisfied or violated, never a score deduction.
 *   - a score is optional, off by default, and never moves a Pareto front.
 *   - a failed point keeps its row. A hole in a design space is information.
 *   - changing an objective, a constraint or a weight re-analyses; it never
 *     re-solves chemistry.
 */
Item {
    id: page

    property int section: 0

    Connections {
        target: TradeStudy
        function onRequestTab(index) { page.section = index }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Trade Study"
            subtitle: "Design variables, evaluated physics, hard constraints, "
                      + "objectives and Pareto analysis"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Evaluated sample — not an optimiser"
                        showDot: false
                    }
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: TradeStudy.hasResult ? TradeStudy.studyStatusLabel
                                                   : "No study yet"
                        tone: TradeStudy.hasResult
                              ? (TradeStudy.resultComplete ? "success" : "warning")
                              : "neutral"
                    }
                }
            }
        }

        RFSegmentedControl {
            Layout.preferredWidth: 460
            model: ["Setup", "Results", "Pareto", "Compare"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            StudySetup {}
            StudyResults {}
            StudyPareto {}
            StudyCompare {}
        }
    }
}
