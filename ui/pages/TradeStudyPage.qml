import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "../data"
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

    // A finished study lands on its results, not back on the form that
    // produced them. Setup stays the landing view while there is nothing to
    // show -- configuring IS the task then -- but once a run completes, the
    // answer is what the reader came back for. The capture of a completed
    // 30-point study opening on the Setup tab is the argument: the study had
    // run, and the workspace still showed the questionnaire.
    //
    // It moves the view once per completed run and never fights the user: a
    // later manual return to Setup stays put, because this only fires on the
    // transition into a completed state.
    function landOnResults() {
        if (TradeStudy.hasResult && page.section === 0)
            page.section = 1
    }

    Connections {
        target: TradeStudy
        function onResultChanged() { page.landOnResults() }
    }

    // Also on arrival, not only on the signal: the workspace is created the
    // first time it is opened, so a study run before that -- or one left
    // complete while the reader worked elsewhere and came back -- would
    // otherwise still open on the form. The page is built fresh each time it
    // is reached, so this is the arrival case, not a duplicate of the signal.
    Component.onCompleted: page.landOnResults()

    Connections {
        target: TradeStudy
        function onRequestTab(index) { page.section = index }
        // Selecting a design (from the plot or the best-points list) is
        // the point of opening the Inspector; this only opens it on the
        // way from zero selected to one, so a person who deliberately
        // closes it while comparing several designs is not fought with it
        // reopening on every further tap.
        function onSelectionChanged() {
            if (TradeStudy.selectedIndices.length === 1)
                ShellContext.inspectorOpen = true
        }
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
            model: ["Setup", "Results", "Trade", "Compare"]
            currentIndex: page.section
            onSelected: function (index) { page.section = index }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: page.section

            StudySetup {}
            StudyResults {}
            StudyTrade {}
            StudyCompare {}
        }
    }
}
