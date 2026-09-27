import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Oblique shock calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and
 * lays out what comes back. There is no arithmetic in it — no θ–β–M relation,
 * no wave-angle root, no shock ratio, and no degree conversion.
 *
 * Two things this page is careful about, because both are ways of being
 * quietly dishonest:
 *
 *   a deflection past the attachment limit clears the result rather than
 *   leaving the last wave angle on screen looking current;
 *
 *   the branch control appears only in the mode that has a branch to choose.
 *   Given a wave angle, which branch it is on is a fact, not a choice.
 *
 * Layout (the Isentropic grammar): the inputs live in a drawer whose handle
 * still names the case when it is closed; the solved shock leads -- β at
 * hierarchy Level 1, or the weak and the strong β side by side when both were
 * asked for (two answers, never one invented) -- then the backend's groups,
 * the detached state when there is no attached shock, and the θ–β–M diagram
 * drawn from the same service. The whole column scrolls rather than clipping
 * at the 1366 floor.
 */
Item {
    id: page

    readonly property var modes: ObliqueShock.solveModes
    readonly property var activeMode: modes[Math.max(0, page.indexOfMode(ObliqueShock.mode))]

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    function isHeroKey(key) {
        return key === "beta" || key === "weak_beta" || key === "strong_beta"
    }

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < ObliqueShock.results.length; ++i) {
            var row = ObliqueShock.results[i]
            if (row.group === group && !page.isHeroKey(row.key))
                out.push(row)
        }
        return out
    }

    // Analysis Experience R2: the one number this workspace exists to
    // produce is the shock angle, at hierarchy Level 1. Both-branches mode
    // genuinely has two answers, so it gets two heroes rather than an
    // invented single one.
    readonly property var heroRows: {
        var out = []
        for (var i = 0; i < ObliqueShock.results.length; ++i) {
            var row = ObliqueShock.results[i]
            if (page.isHeroKey(row.key))
                out.push(row)
        }
        return out
    }

    // The groups come from the controller, because they differ between the
    // single-branch and both-branches results (the weak and the strong
    // solution are separate groups, never interleaved). A row with no group
    // is shown under "Other", never dropped.
    readonly property var groups: {
        var out = ObliqueShock.resultGroups.slice()
        var list = ObliqueShock.results
        for (var i = 0; i < list.length; ++i)
            if (list[i].group === "" && !page.isHeroKey(list[i].key)) {
                out.push("")
                break
            }
        return out
    }

    // The case, in one line, for the collapsed drawer's handle.
    readonly property string caseSummary: {
        var symbol = page.activeMode ? page.activeMode.symbol : ""
        return "M₁ " + (+Number(ObliqueShock.mach1).toPrecision(6))
               + "  ·  " + symbol + " = " + (+Number(ObliqueShock.inputValue).toPrecision(6)) + "°"
               + "  ·  γ " + (+Number(ObliqueShock.gamma).toPrecision(4))
               + (ObliqueShock.branchRequired ? "  ·  " + ObliqueShock.branch : "")
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- input drawer -------------------------------------------------
        RFWorkspaceDrawer {
            id: inputs
            objectName: "obliqueShockInputDrawer"
            Layout.preferredWidth: inputs.implicitWidth
            Layout.fillHeight: true
            title: "Solve from"
            summary: page.caseSummary
            // The solved shock first: closed while there is an attached
            // solution, open when there is none (a detached or refused
            // request needs its inputs). An explicit open or close by the
            // reader wins from then on.
            defaultOpen: !ObliqueShock.valid
            drawerWidth: Math.max(250, Metrics.railWidth - 20)

            Flickable {
                id: inputFlick
                anchors.fill: parent
                contentWidth: width
                contentHeight: inputColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {
                    policy: inputFlick.contentHeight > inputFlick.height
                            ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
                }

                ColumnLayout {
                    id: inputColumn
                    width: inputFlick.width - (inputFlick.contentHeight > inputFlick.height ? 12 : 0)
                    spacing: Metrics.spacing.l

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "Upstream Mach  M₁"
                        value: ObliqueShock.mach1
                        digits: 6
                        decimals: 6
                        step: 0.1
                        onValueEdited: function (v) { ObliqueShock.mach1 = v }
                    }

                    RFComboBox {
                        id: modeControl
                        objectName: "obliqueShockModeControl"
                        Layout.fillWidth: true
                        label: "Known quantity"
                        model: page.modes.map(function (m) { return m.label + "   " + m.symbol })
                        // Bound to the controller, written back only when a
                        // person picks: the presets and the table also change
                        // the mode, and a selector showing the wrong quantity
                        // would mislabel the angle beneath it.
                        currentIndex: page.indexOfMode(ObliqueShock.mode)
                        onActivated: function (index) {
                            if (index >= 0 && index < page.modes.length)
                                ObliqueShock.mode = page.modes[index].key
                        }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: ObliqueShock.inputSymbol + "   [°]"
                        value: ObliqueShock.inputValue
                        digits: 6
                        decimals: 6
                        step: 1
                        onValueEdited: function (v) { ObliqueShock.inputValue = v }
                    }

                    Text {
                        Layout.fillWidth: true
                        readonly property string plainText: "Valid range: " + ObliqueShock.inputHint
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "Specific heat ratio  γ"
                        value: ObliqueShock.gamma
                        digits: 4
                        decimals: 4
                        step: 0.005
                        onValueEdited: function (v) { ObliqueShock.gamma = v }
                    }

                    // Only the deflection mode has two roots. Given a wave
                    // angle, the branch is a consequence rather than a choice,
                    // and offering a control would imply otherwise.
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: ObliqueShock.branchRequired
                        spacing: Metrics.spacing.xs

                        RFSectionLabel { text: "Branch" }

                        RFSegmentedControl {
                            objectName: "obliqueShockBranchControl"
                            Layout.fillWidth: true
                            model: ["Weak", "Strong", "Both"]
                            currentIndex: ObliqueShock.branch === "weak" ? 0
                                        : ObliqueShock.branch === "strong" ? 1 : 2
                            onSelected: function (index) {
                                ObliqueShock.branch = ["weak", "strong", "both"][index]
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "Every attainable deflection has a weak and a strong wave angle. An "
                                  + "unconstrained external flow takes the weak one."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Limits at this Mach number" }

                    Repeater {
                        model: [
                            { k: "Mach angle  μ", v: "machAngle" },
                            { k: "Maximum deflection  θ_max", v: "thetaMax" },
                            { k: "β at θ_max", v: "betaAtThetaMax" },
                            { k: "β for sonic M₂", v: "betaSonic" }
                        ]

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                readonly property string plainText: modelData.k
                                text: Notation.rich(plainText)
                                textFormat: Notation.textFormat(plainText)
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                            Text {
                                text: ObliqueShock.limits[modelData.v] !== undefined
                                      ? ObliqueShock.limits[modelData.v].toFixed(4) + "°" : "—"
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.bodySmall
                            }
                        }
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Presets" }

                    // Actions, not a persistent selection. The controller
                    // switches the mode to θ itself; the selector follows.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xs

                        Repeater {
                            model: [5, 10, 20]

                            delegate: RFButton {
                                required property var modelData
                                Layout.fillWidth: true
                                text: "θ " + modelData + "°"
                                variant: "quiet"
                                compact: true
                                onClicked: ObliqueShock.setDeflectionAndSolve(modelData)
                            }
                        }
                    }
                }
            }
        }

        // ---- results ------------------------------------------------------
        Flickable {
            id: resultsFlick
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: resultsColumn.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: RFScrollBar {
                policy: resultsFlick.contentHeight > resultsFlick.height
                        ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
            }

            ColumnLayout {
                id: resultsColumn
                width: resultsFlick.width - (resultsFlick.contentHeight > resultsFlick.height ? 12 : 0)
                spacing: Metrics.spacing.l

                RFPanel {
                    objectName: "obliqueShockResults"
                    title: "Solved shock"
                    Layout.fillWidth: true
                    contentSpacing: Metrics.spacing.m

                    trailing: Component {
                        RFStatusChip {
                            objectName: "obliqueShockResultStatus"
                            text: ObliqueShock.statusLabel
                            tone: ObliqueShock.statusTone
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        // The detached block below states the same thing at
                        // length, so saying it twice would just be noise.
                        visible: ObliqueShock.statusMessage !== "" && !ObliqueShock.detached
                        readonly property string plainText: ObliqueShock.statusMessage
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: ObliqueShock.valid ? Theme.textMuted : Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    // ---- the answer, at hierarchy Level 1 ---------------------
                    RowLayout {
                        objectName: "obliqueShockHero"
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.h1
                        visible: ObliqueShock.valid && page.heroRows.length > 0

                        Repeater {
                            model: page.heroRows

                            delegate: RFResultValue {
                                id: hero
                                required property var modelData
                                objectName: "obliqueShockHero_" + modelData.key
                                Layout.alignment: Qt.AlignTop
                                // Two heroes are two branches, each named.
                                label: page.heroRows.length > 1
                                       ? modelData.label + "   ("
                                         + (modelData.key === "weak_beta" ? "weak" : "strong") + ")"
                                       : modelData.label
                                value: modelData.value
                                unit: modelData.unit
                                scale: "hero"
                                TapHandler { onSingleTapped: ObliqueShock.copyText(hero.modelData.value) }
                            }
                        }

                        Item { Layout.fillWidth: true }

                        // Which branch the single answer is on, as a fact.
                        RFStatusChip {
                            Layout.alignment: Qt.AlignVCenter
                            visible: page.heroRows.length === 1 && ObliqueShock.branchUsed !== ""
                            text: ObliqueShock.branchUsed + " branch"
                            tone: "neutral"
                            showDot: false
                        }
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        visible: ObliqueShock.valid && page.heroRows.length > 0
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        visible: ObliqueShock.valid
                        columns: resultsColumn.width > 760 ? 2 : 1
                        columnSpacing: Metrics.spacing.xl
                        rowSpacing: Metrics.spacing.l

                        Repeater {
                            model: page.groups

                            delegate: ColumnLayout {
                                id: group
                                required property var modelData
                                readonly property string name: modelData !== "" ? modelData : "Other"
                                readonly property var groupRows: page.rowsIn(modelData)
                                objectName: "obliqueShockGroup_" + group.name.replace(/ /g, "_")
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.xs
                                visible: groupRows.length > 0

                                RFSectionLabel {
                                    text: Notation.sectionRich(group.name)
                                    textFormat: Notation.textFormat(group.name)
                                }

                                Repeater {
                                    model: group.groupRows

                                    delegate: RowLayout {
                                        id: line
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: modelData.emphasis ? 30 : 24
                                        spacing: Metrics.spacing.m

                                        Text {
                                            Layout.preferredWidth: 176
                                            text: Notation.rich(line.modelData.label)
                                            textFormat: Notation.textFormat(line.modelData.label)
                                            elide: Text.ElideRight
                                            clip: true
                                            color: line.modelData.emphasis ? Theme.text : Theme.textSecondary
                                            font.family: Typography.sans
                                            font.pixelSize: line.modelData.emphasis ? Typography.body
                                                                                    : Typography.bodySmall
                                        }

                                        Text {
                                            Layout.fillWidth: true
                                            text: line.modelData.value
                                                  + (line.modelData.unit ? " " + line.modelData.unit : "")
                                            color: line.modelData.available ? Theme.text : Theme.textMuted
                                            font.family: Typography.mono
                                            font.pixelSize: line.modelData.emphasis
                                                ? Typography.readoutMedium
                                                : Typography.readoutSmall
                                            font.weight: line.modelData.emphasis
                                                ? Typography.medium : Typography.regular

                                            TapHandler {
                                                onSingleTapped: ObliqueShock.copyText(line.modelData.value)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // ---- the detached state --------------------------------------
                    //
                    // No wave angle, no ratios, and nothing left over from the
                    // last valid answer: the request has no attached solution
                    // and the page says only that.
                    ColumnLayout {
                        objectName: "obliqueShockDetached"
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.s
                        spacing: Metrics.spacing.m
                        visible: ObliqueShock.detached

                        RFStatusChip {
                            text: "DETACHED SHOCK REQUIRED"
                            tone: "warning"
                            showDot: false
                        }

                        Text {
                            Layout.fillWidth: true
                            readonly property string plainText: ObliqueShock.statusMessage
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.body
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.xl

                            ColumnLayout {
                                spacing: 2
                                RFSectionLabel { text: Notation.sectionRich("Requested θ"); textFormat: Notation.textFormat("Requested θ") }
                                Text {
                                    text: ObliqueShock.inputValue.toFixed(4) + "°"
                                    color: Theme.warning
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.readoutMedium
                                }
                            }

                            ColumnLayout {
                                spacing: 2
                                RFSectionLabel { text: Notation.sectionRich("Maximum attached θ_max"); textFormat: Notation.textFormat("Maximum attached θ_max") }
                                Text {
                                    text: ObliqueShock.limits.thetaMax !== undefined
                                          ? ObliqueShock.limits.thetaMax.toFixed(4) + "°" : "—"
                                    color: Theme.text
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.readoutMedium
                                }
                            }

                            Item { Layout.fillWidth: true }
                        }

                        Text {
                            Layout.fillWidth: true
                            readonly property string plainText: "RocketForge does not solve the detached bow shock: its shape needs "
                                  + "a numerical field solution, and substituting a normal shock or "
                                  + "the θ_max solution here would be a different answer to a "
                                  + "different question."
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.xl
                        visible: !ObliqueShock.valid && !ObliqueShock.detached
                        tag: "Input"
                        title: "No shock for this input"
                        body: ObliqueShock.statusMessage
                    }

                    // The model, as the quietest line of the panel -- still in
                    // view when the input drawer is closed.
                    Text {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.s
                        readonly property string plainText: ObliqueShock.modelName
                                                            + "  ·  " + ObliqueShock.assumptions.join(" · ")
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                // ---- the diagram, alongside the numbers -----------------------
                RFPanel {
                    objectName: "obliqueShockCalculatorDiagramPanel"
                    title: "θ–β–M"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 320
                    contentSpacing: Metrics.spacing.xs

                    trailing: Component {
                        Text {
                            text: "the same solver that produced the numbers"
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }

                    ObliqueShockDiagram {
                        chartName: "obliqueShockCalculatorDiagram"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        compact: true
                    }
                }

                // ---- reference check ------------------------------------------
                // Said, not left out: there is no printed oblique-shock table
                // to check against, and none is invented.
                Rectangle {
                    objectName: "obliqueShockReferenceCheck"
                    Layout.fillWidth: true
                    implicitHeight: refColumn.implicitHeight + 2 * Metrics.spacing.m
                    radius: Metrics.radius.m
                    color: Theme.surface
                    border.width: Metrics.hairline
                    border.color: Theme.border

                    ColumnLayout {
                        id: refColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: Metrics.spacing.m
                        spacing: Metrics.spacing.s

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.m
                            Text {
                                text: "Reference check"
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.medium
                            }
                            RFStatusChip {
                                text: "No published table"
                                tone: "neutral"
                                showDot: false
                            }
                            Item { Layout.fillWidth: true }
                        }

                        Text {
                            Layout.fillWidth: true
                            readonly property string plainText: ObliqueShock.referenceMessage
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }
        }
    }
}
