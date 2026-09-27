import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Normal shock calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and lays
 * out what comes back. There is no arithmetic in it - not a jump relation, not
 * a Rayleigh pitot formula, not an entropy expression.
 *
 * Five ways in, because an engineer rarely knows M1 directly: they know what a
 * probe read. Four of the five are closed form and one iterates, and the page
 * says which, since that is a real and useful distinction.
 *
 * Reading order (the Isentropic grammar): the shock itself first -- upstream
 * M1 and downstream M2 side by side, one pair, never one without the other --
 * then the jumps across it by family, in the backend's own groups: the static
 * jump, the stagnation change, and the dimensional downstream state when
 * upstream conditions are given. Each family is led by its emphasised row.
 * A row whose group has no family here is shown under "Other", never dropped.
 * The inputs live in a drawer whose handle still names the case when it is
 * closed; the Appendix B check is one counted line that opens.
 */
Item {
    id: page

    readonly property var modes: NormalShock.solveModes
    readonly property var activeMode: modes[Math.max(0, page.indexOfMode(NormalShock.mode))]

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    function row(key) {
        var list = NormalShock.results
        for (var i = 0; i < list.length; ++i)
            if (list[i].key === key)
                return list[i]
        return null
    }

    // ---- where every result row goes ---------------------------------------
    // The pair: upstream and downstream Mach number, read together.
    readonly property var pairKeys: ["mach1", "mach2"]
    readonly property var upstreamRow: { NormalShock.results; return page.row("mach1") }
    readonly property var downstreamRow: { NormalShock.results; return page.row("mach2") }

    // The families, in the order and with the names the service gives them.
    // Every row that is not one of the pair lands in exactly one family;
    // a row with no group is collected under "Other".
    readonly property var families: {
        var list = NormalShock.results, order = [], byName = {}
        for (var i = 0; i < list.length; ++i) {
            var r = list[i]
            if (page.pairKeys.indexOf(r.key) >= 0)
                continue
            var name = r.group !== "" && r.group !== "Flow" ? r.group : "Other"
            if (byName[name] === undefined) {
                byName[name] = []
                order.push(name)
            }
            byName[name].push(r)
        }
        return order.map(function (n) { return { name: n, rows: byName[n] } })
    }

    // The Appendix B check, counted: "6/6 PASS", or the failures named.
    function summarizeCheck(rows) {
        var passed = 0
        for (var i = 0; i < rows.length; ++i)
            if (rows[i].status === "PASS")
                passed += 1
        var all = rows.length > 0 && passed === rows.length
        var text = rows.length === 0 ? "No exact reference row"
                 : all ? passed + "/" + rows.length + " PASS"
                 : passed + "/" + rows.length + " PASS  ·  " + (rows.length - passed) + " FAIL"
        return { passed: passed, allPass: all, text: text }
    }
    // Made with the result (NormalShock.currentMachComparison): opening the
    // page, or coming back to it, re-runs nothing.
    readonly property var checkRows: NormalShock.currentMachComparison
    readonly property var checkCount: page.summarizeCheck(page.checkRows)
    readonly property bool checkAllPass: page.checkCount.allPass
    readonly property string checkSummary: page.checkCount.text
    property bool checkOpen: false

    // The case, in one line, for the collapsed drawer's handle.
    readonly property string caseSummary: {
        var symbol = page.activeMode ? page.activeMode.symbol : ""
        var text = symbol + " = " + (+Number(NormalShock.inputValue).toPrecision(6))
                   + "  ·  γ " + (+Number(NormalShock.gamma).toPrecision(4))
        if (NormalShock.dimensionalAvailable)
            text += "  ·  p₁ " + (+Number(NormalShock.upstreamPressure).toPrecision(6)) + " Pa"
                    + "  ·  T₁ " + (+Number(NormalShock.upstreamTemperature).toPrecision(6)) + " K"
        return text
    }

    // One jump row: label, value, unit; click copies the value as shown.
    component JumpRow: RowLayout {
        id: jump
        property var entry: null
        readonly property bool primary: entry !== null && entry.emphasis === true
        Layout.fillWidth: true
        Layout.preferredHeight: primary ? 30 : 24
        spacing: Metrics.spacing.m
        visible: entry !== null

        Text {
            Layout.preferredWidth: 150
            text: jump.entry ? Notation.rich(jump.entry.label) : ""
            textFormat: jump.entry ? Notation.textFormat(jump.entry.label) : Text.PlainText
            color: jump.primary ? Theme.text : Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: jump.primary ? Typography.body : Typography.bodySmall
            elide: Text.ElideRight
            clip: true
        }
        Text {
            Layout.fillWidth: true
            text: jump.entry ? jump.entry.value + (jump.entry.unit ? " " + jump.entry.unit : "") : ""
            color: jump.entry && !jump.entry.available ? Theme.textMuted
                 : jump.primary ? Theme.text : Theme.textSecondary
            font.family: Typography.mono
            font.pixelSize: jump.primary ? Typography.readoutMedium : Typography.readoutSmall
            font.weight: jump.primary ? Typography.medium : Typography.regular

            TapHandler { onSingleTapped: if (jump.entry) NormalShock.copyText(jump.entry.value) }
            HoverHandler { id: valueHover }
        }
        Text {
            text: "copy"
            opacity: valueHover.hovered ? 1 : 0
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            Behavior on opacity { NumberAnimation { duration: Motion.micro } }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- input drawer -------------------------------------------------
        RFWorkspaceDrawer {
            id: inputs
            objectName: "normalShockInputDrawer"
            Layout.preferredWidth: inputs.implicitWidth
            Layout.fillHeight: true
            title: "Solve from"
            summary: page.caseSummary
            // The solved shock first: closed while there is a valid result,
            // open when there is none (the inputs need attention). An
            // explicit open or close by the reader wins from then on.
            defaultOpen: !NormalShock.valid
            drawerWidth: Math.max(250, Metrics.railWidth - 20)

            // Scrolls when the window is shorter than the inputs (the 1366
            // floor with the upstream conditions): nothing is cut.
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

                    RFComboBox {
                        id: modeControl
                        objectName: "normalShockModeControl"
                        Layout.fillWidth: true
                        label: "Known quantity"
                        model: page.modes.map(function (m) { return m.label + "   " + m.symbol })
                        // Bound to the controller, written back only when a
                        // person picks: the mode also changes from the table
                        // and the presets, and a selector showing the wrong
                        // quantity would mislabel the value beneath it.
                        currentIndex: page.indexOfMode(NormalShock.mode)
                        onActivated: function (index) {
                            if (index >= 0 && index < page.modes.length)
                                NormalShock.mode = page.modes[index].key
                        }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: NormalShock.inputSymbol
                        value: NormalShock.inputValue
                        digits: 6
                        decimals: 6
                        step: 0.01
                        onValueEdited: function (v) { NormalShock.inputValue = v }
                    }

                    Text {
                        Layout.fillWidth: true
                        readonly property string plainText: "Valid range: " + NormalShock.inputHint
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: NormalShock.modeIsIterative
                        text: "This one has no closed-form inverse, so it is solved with RocketForge's "
                              + "own bracketed root finder. The other four are exact rearrangements."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "Specific heat ratio  γ"
                        value: NormalShock.gamma
                        digits: 4
                        decimals: 4
                        step: 0.005
                        onValueEdited: function (v) { NormalShock.gamma = v }
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Upstream conditions" }

                    Text {
                        Layout.fillWidth: true
                        text: "Optional. Supplying them turns every ratio into a downstream value "
                              + "in Pa and K; the ratios do not need them."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "Static pressure  p₁   [Pa]"
                        value: NormalShock.upstreamPressure
                        digits: 0
                        decimals: 0
                        step: 1000
                        onValueEdited: function (v) { NormalShock.upstreamPressure = v }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        label: "Static temperature  T₁   [K]"
                        value: NormalShock.upstreamTemperature
                        digits: 2
                        decimals: 2
                        step: 5
                        onValueEdited: function (v) { NormalShock.upstreamTemperature = v }
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Presets" }

                    // Buttons rather than a segmented control: presets are
                    // actions, not a persistent selection. The controller
                    // switches the mode to M₁ itself; the selector follows.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xs

                        Repeater {
                            model: [1.5, 2.0, 3.0]

                            delegate: RFButton {
                                required property var modelData
                                Layout.fillWidth: true
                                text: "M₁ " + modelData
                                variant: "quiet"
                                compact: true
                                onClicked: NormalShock.setMachAndSolve(modelData)
                            }
                        }
                    }
                }
            }
        }

        // ---- results ------------------------------------------------------
        // Scrolls when the window is shorter than the results and the
        // reference check together (the 1366 floor); never clips either.
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
                    objectName: "normalShockResults"
                    title: "Solved shock"
                    Layout.fillWidth: true
                    contentSpacing: Metrics.spacing.m

                    trailing: Component {
                        RFStatusChip {
                            objectName: "normalShockResultStatus"
                            text: NormalShock.statusLabel
                            tone: NormalShock.statusTone
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: NormalShock.statusMessage !== ""
                        readonly property string plainText: NormalShock.statusMessage
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: NormalShock.valid ? Theme.textMuted : Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    // The pair: upstream and downstream of the one shock, at
                    // the same weight -- the shock is the pair, not either end.
                    RowLayout {
                        objectName: "normalShockMachPair"
                        Layout.fillWidth: true
                        visible: NormalShock.valid && page.upstreamRow !== null
                                 && page.downstreamRow !== null
                        spacing: Metrics.spacing.xl

                        RFResultValue {
                            objectName: "normalShockHeroMach1"
                            Layout.alignment: Qt.AlignTop
                            label: page.upstreamRow ? page.upstreamRow.label : ""
                            value: page.upstreamRow ? page.upstreamRow.value : "—"
                            scale: "hero"
                            TapHandler { onSingleTapped: if (page.upstreamRow) NormalShock.copyText(page.upstreamRow.value) }
                        }

                        Text {
                            Layout.alignment: Qt.AlignBottom
                            Layout.bottomMargin: Metrics.spacing.s
                            text: "→"
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.readoutLarge
                        }

                        RFResultValue {
                            objectName: "normalShockHeroMach2"
                            Layout.alignment: Qt.AlignTop
                            label: page.downstreamRow ? page.downstreamRow.label : ""
                            value: page.downstreamRow ? page.downstreamRow.value : "—"
                            scale: "hero"
                            TapHandler { onSingleTapped: if (page.downstreamRow) NormalShock.copyText(page.downstreamRow.value) }
                        }

                        Item { Layout.fillWidth: true }

                        // The ceiling a strong shock approaches, beside the
                        // pair it bounds.
                        Text {
                            Layout.preferredWidth: 300
                            Layout.alignment: Qt.AlignVCenter
                            readonly property string plainText: NormalShock.strongShockLimits.caption !== undefined
                                  ? NormalShock.strongShockLimits.caption : ""
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        visible: NormalShock.valid
                    }

                    // The jumps, by the backend's own families.
                    GridLayout {
                        Layout.fillWidth: true
                        visible: NormalShock.valid
                        columns: resultsColumn.width > 760 ? Math.max(1, Math.min(3, page.families.length)) : 1
                        columnSpacing: Metrics.spacing.xl
                        rowSpacing: Metrics.spacing.l

                        Repeater {
                            model: page.families

                            delegate: ColumnLayout {
                                id: family
                                required property var modelData
                                readonly property bool downstream: modelData.name === "Downstream state"
                                objectName: "normalShockFamily_" + modelData.name.replace(/ /g, "_")
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.xs

                                RFSectionLabel {
                                    text: Notation.sectionRich(family.modelData.name)
                                    textFormat: Notation.textFormat(family.modelData.name)
                                }

                                Text {
                                    Layout.fillWidth: true
                                    visible: family.downstream && !NormalShock.dimensionalAvailable
                                    readonly property string plainText: NormalShock.dimensionalMessage
                                    text: Notation.rich(plainText)
                                    textFormat: Notation.textFormat(plainText)
                                    wrapMode: Text.WordWrap
                                    lineHeight: Typography.proseLineHeight
                                    lineHeightMode: Text.ProportionalHeight
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }

                                Repeater {
                                    model: family.modelData.rows
                                    delegate: JumpRow {
                                        required property var modelData
                                        entry: modelData
                                    }
                                }
                            }
                        }
                    }

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.xl
                        visible: !NormalShock.valid
                        tag: "Input"
                        title: "No shock for this input"
                        body: NormalShock.statusMessage
                    }

                    // The model, as the quietest line of the panel -- still in
                    // view when the input drawer is closed.
                    Text {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.s
                        readonly property string plainText: NormalShock.modelName
                                                            + "  ·  " + NormalShock.assumptions.join(" · ")
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

                // ---- reference check ------------------------------------------
                // One line: how many published values this shock was checked
                // against and how many passed. A failure is named in the line
                // itself, never only inside the details.
                Rectangle {
                    objectName: "normalShockReferenceCheck"
                    Layout.fillWidth: true
                    implicitHeight: checkColumn.implicitHeight + 2 * Metrics.spacing.m
                    radius: Metrics.radius.m
                    color: Theme.surface
                    border.width: Metrics.hairline
                    border.color: page.checkRows.length > 0 && !page.checkAllPass ? Theme.warning : Theme.border

                    ColumnLayout {
                        id: checkColumn
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
                            Text {
                                text: "Anderson Appendix B"
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            RFStatusChip {
                                objectName: "normalShockCheckSummary"
                                text: page.checkSummary
                                tone: page.checkRows.length === 0 ? "neutral"
                                    : page.checkAllPass ? "success" : "warning"
                                showDot: page.checkRows.length > 0
                            }
                            Item { Layout.fillWidth: true }
                            RFToolButton {
                                objectName: "normalShockCheckDetails"
                                visible: page.checkRows.length > 0
                                text: page.checkOpen ? "Hide details" : "Details"
                                tooltip: "Each quantity: calculated, published, difference, status"
                                checked: page.checkOpen
                                onClicked: page.checkOpen = !page.checkOpen
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: page.checkRows.length === 0
                            text: "Anderson Appendix B tabulates γ = 1.4 at discrete Mach numbers. "
                                  + "This M₁ is not one of them, and no value is interpolated."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: page.checkOpen && page.checkRows.length > 0
                            spacing: Metrics.spacing.xs

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.spacing.m

                                Repeater {
                                    model: [
                                        { text: "Quantity", width: 70 },
                                        { text: "Calculated", width: 120 },
                                        { text: "Published", width: 120 },
                                        { text: "Difference", width: -1 },
                                        { text: "Status", width: 54 }
                                    ]
                                    delegate: Text {
                                        required property var modelData
                                        Layout.preferredWidth: modelData.width
                                        Layout.fillWidth: modelData.width < 0
                                        text: modelData.text
                                        color: Theme.textMuted
                                        font.family: Typography.sans
                                        font.pixelSize: Typography.meta
                                    }
                                }
                            }

                            Repeater {
                                model: page.checkRows

                                delegate: RowLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    spacing: Metrics.spacing.m

                                    Text {
                                        Layout.preferredWidth: 70
                                        text: Notation.rich(modelData.label)
                                        textFormat: Notation.textFormat(modelData.label)
                                        color: Theme.textSecondary
                                        font.family: Typography.sans
                                        font.pixelSize: Typography.bodySmall
                                    }
                                    Text {
                                        Layout.preferredWidth: 120
                                        text: modelData.computed
                                        color: Theme.text
                                        font.family: Typography.mono
                                        font.pixelSize: Typography.bodySmall
                                    }
                                    Text {
                                        Layout.preferredWidth: 120
                                        text: modelData.reference
                                        color: Theme.textSecondary
                                        font.family: Typography.mono
                                        font.pixelSize: Typography.bodySmall
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.difference
                                        color: Theme.textMuted
                                        font.family: Typography.mono
                                        font.pixelSize: Typography.bodySmall
                                    }
                                    RFStatusChip {
                                        Layout.preferredWidth: 54
                                        text: modelData.status
                                        tone: modelData.status === "PASS" ? "success" : "warning"
                                        showDot: false
                                    }
                                }
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: NormalShock.referenceCitation + " — published reference, not an exact value."
                            wrapMode: Text.WordWrap
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
