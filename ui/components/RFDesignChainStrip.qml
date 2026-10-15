import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../data"

/*
 * RFDesignChainStrip - where this page sits in its design chain, and the state
 * of every step (U2(b) of the R3 audit).
 *
 * Two chains: the Liquid Engine (requirement, trade, sizing, chamber geometry,
 * injector) and the Propulsion System (inventory, tanks, management,
 * pressurization, feed network). Each step reads its controller's existing
 * state and nothing else:
 *   - the requirement is "Stated" when it is complete, otherwise "Incomplete";
 *   - every other step is "Done" (a current, usable result), "Stale" (a result
 *     whose inputs have changed since), "Not run", or -- for a result that is
 *     refused, incomplete, or a trade with no candidate that solved -- a label
 *     in the warning colour: the page's own ("Refused", "Computed · incomplete")
 *     or, for the trade, "No usable candidate". None of these is shown as done.
 * A step opens its page. It never runs, solves or changes anything; the page
 * forwards `openRequested` to the shell as it does for an issue's link.
 *
 * objectNames: chainStrip (the root), chainStep_<page key> for each step, whose
 * `stepState` is "stated", "incomplete", "done", "stale", "issue" or "none".
 */
Item {
    id: root

    // "liquidengine" or "propulsionsystem", as the Navigation family keys.
    property string chain: ""
    // The page this strip sits on.
    property string currentKey: ""

    signal openRequested(int index)

    // `resultOk` is false for a refused result, and for a trade in which no
    // candidate solved (nothing can be selected). A Propulsion System study can
    // also be ok (not refused) yet "incomplete" (`resultStatus`); its page shows
    // it in the warning tone, so it is an issue too.
    function resultState(controller) {
        if (!controller.hasResult)
            return "none"
        if (controller.resultStale)
            return "stale"
        if (controller.resultOk === false || controller.resultStatus === "incomplete")
            return "issue"
        return "done"
    }

    // `issueText` replaces the page's label where the page has none for the
    // issue (the trade calls any evaluated trade "Evaluated").
    function stepOf(key, controller, issueText) {
        var state = resultState(controller)
        var note = state !== "issue" ? "" : (issueText !== undefined ? issueText : controller.statusLabel)
        return { key: key, state: state, note: note }
    }

    readonly property var steps: root.chain === "liquidengine" ? [
        { key: "requirement", state: EngineRequirement.isComplete ? "stated" : "incomplete", note: "" },
        stepOf("propellanttrade", PropellantTrade, "No usable candidate"),
        stepOf("chambersizing", ChamberSizing),
        stepOf("chambergeometry", ChamberGeometry),
        stepOf("injector", Injector)
    ] : root.chain === "propulsionsystem" ? [
        stepOf("propellantinventory", PropellantInventory),
        stepOf("tankgeometry", PropellantTanks),
        stepOf("propellantmanagement", PropellantManagement),
        stepOf("tankpressurization", TankPressurization),
        stepOf("feednetwork", FeedNetwork)
    ] : []

    readonly property var stateText: ({ stated: "Stated", incomplete: "Incomplete", done: "Done",
                                        stale: "Stale", none: "Not run" })

    objectName: "chainStrip"
    implicitHeight: row.implicitHeight

    RowLayout {
        id: row
        width: root.width
        spacing: Metrics.spacing.xs

        Repeater {
            // A count, not the array: the delegates stay when a state changes,
            // so a focused step keeps its focus.
            model: root.steps.length

            delegate: RowLayout {
                id: cell
                required property int index
                readonly property var modelData: root.steps[cell.index]
                // Equal shares: every step gets the same width whatever its label.
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                spacing: Metrics.spacing.xs

                Text {
                    visible: cell.index > 0
                    text: "›"
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Rectangle {
                    id: step
                    objectName: "chainStep_" + cell.modelData.key
                    readonly property string stepState: cell.modelData.state
                    readonly property string stateLabel: step.stepState === "issue" ? cell.modelData.note
                                                                                    : root.stateText[step.stepState]
                    readonly property bool current: cell.modelData.key === root.currentKey
                    readonly property int pageIndex: Navigation.indexOfKey(cell.modelData.key)

                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    implicitHeight: content.implicitHeight + 2 * Metrics.spacing.xs
                    radius: Metrics.radius.s
                    color: step.current ? Theme.accentSubtle : (hover.hovered ? Theme.surfaceHover : "transparent")
                    border.width: 1
                    border.color: step.current ? Theme.accent
                                               : (hover.hovered || step.activeFocus ? Theme.border : "transparent")

                    activeFocusOnTab: !step.current
                    Accessible.role: step.current ? Accessible.StaticText : Accessible.Button
                    Accessible.name: Navigation.items[step.pageIndex].label + ", " + step.stateLabel
                    Accessible.onPressAction: step.open()
                    Keys.onReturnPressed: step.open()
                    Keys.onEnterPressed: step.open()
                    Keys.onSpacePressed: step.open()

                    function open() {
                        if (!step.current)
                            root.openRequested(step.pageIndex)
                    }

                    HoverHandler { id: hover; enabled: !step.current; cursorShape: Qt.PointingHandCursor }
                    TapHandler { enabled: !step.current; onTapped: step.open() }

                    RowLayout {
                        id: content
                        anchors.fill: parent
                        anchors.leftMargin: Metrics.spacing.s
                        anchors.rightMargin: Metrics.spacing.s
                        spacing: Metrics.spacing.xs

                        Text {
                            text: (cell.index + 1) + "  " + Navigation.items[step.pageIndex].label
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            elide: Text.ElideRight
                            color: step.current ? Theme.text : Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.weight: step.current ? Typography.medium : Typography.regular
                        }
                        Rectangle {
                            width: 5
                            height: 5
                            radius: 2.5
                            Layout.alignment: Qt.AlignVCenter
                            color: step.stepState === "done" || step.stepState === "stated" ? Theme.success
                                 : step.stepState === "stale" || step.stepState === "issue" ? Theme.warning
                                 : Theme.textDisabled
                        }
                        Text {
                            text: step.stateLabel
                            color: step.stepState === "issue" ? Theme.warning : Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }
        }
    }
}
