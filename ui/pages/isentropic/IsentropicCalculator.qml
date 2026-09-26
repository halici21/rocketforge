import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Isentropic calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the input, and lays
 * out what comes back. There is no arithmetic in it - not a ratio, not a
 * reciprocal, not a unit conversion.
 *
 * Reading order: the solved state (M and its regime) first, then the two
 * quantities that describe it geometrically (Mach angle, A/A*), then the
 * ratios by physical family -- pressure, temperature, density -- each led by
 * the direction the table and chart carry, its inverse quieter beneath, and
 * the sonic-reference ratios as compact context at the foot. The inputs live
 * in a drawer whose handle still names the case when it is closed; the
 * Anderson check is one line that says how many rows passed, and opens.
 */
Item {
    id: page

    readonly property var modes: Isentropic.solveModes
    readonly property var activeMode: modes[Math.max(0, page.indexOfMode(Isentropic.mode))]

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    // ---- where every result row goes ---------------------------------------
    // Secondary: the geometry of the solved state. Families: the ratios, by
    // physical quantity. Each family lists its static/stagnation pair and its
    // sonic-reference ratio. A row the service returns that is not named here
    // is not dropped: it appears under "Other" (see otherRows).
    readonly property var secondaryKeys: ["mach_angle", "area_ratio"]
    readonly property var families: [
        { name: "Pressure", pair: ["p_over_p0", "p0_over_p"], sonic: "p_over_pstar" },
        { name: "Temperature", pair: ["T_over_T0", "T0_over_T"], sonic: "T_over_Tstar" },
        { name: "Density", pair: ["rho_over_rho0", "rho0_over_rho"], sonic: "rho_over_rhostar" }
    ]

    function row(key) {
        var list = Isentropic.results
        for (var i = 0; i < list.length; ++i)
            if (list[i].key === key)
                return list[i]
        return null
    }

    readonly property var machRow: { Isentropic.results; return page.row("mach") }

    // The direction the table and the chart carry leads its family; the
    // inverse follows, quieter. Every row is still shown; only the weight and
    // the order change.
    readonly property var plottedKeys: {
        var out = {}
        var cols = Isentropic.tableColumns
        for (var i = 0; i < cols.length; ++i)
            if (cols[i].key !== "mach")
                out[cols[i].key] = true
        return out
    }
    function familyOrder(pair) {
        return page.plottedKeys[pair[1]] === true && page.plottedKeys[pair[0]] !== true
               ? [pair[1], pair[0]] : [pair[0], pair[1]]
    }

    readonly property var placedKeys: {
        var out = { "mach": true }
        for (var i = 0; i < secondaryKeys.length; ++i)
            out[secondaryKeys[i]] = true
        for (var f = 0; f < families.length; ++f) {
            out[families[f].pair[0]] = true
            out[families[f].pair[1]] = true
            out[families[f].sonic] = true
        }
        return out
    }
    readonly property var otherRows: {
        var list = Isentropic.results, out = []
        for (var i = 0; i < list.length; ++i)
            if (page.placedKeys[list[i].key] !== true)
                out.push(list[i])
        return out
    }

    // The Anderson check, counted: "4/4 PASS", or the failures named. Any
    // row that is not PASS counts as a failure in the one-line summary; it is
    // never averaged away or left for the details to reveal.
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
    readonly property var checkRows: Isentropic.currentMachComparison
    readonly property var checkCount: page.summarizeCheck(page.checkRows)
    readonly property int checkPassed: page.checkCount.passed
    readonly property bool checkAllPass: page.checkCount.allPass
    readonly property string checkSummary: page.checkCount.text
    property bool checkOpen: false

    // The case, in one line, for the collapsed drawer's handle.
    readonly property string caseSummary: {
        var symbol = page.activeMode ? page.activeMode.symbol : ""
        return symbol + " = " + (+Number(Isentropic.inputValue).toPrecision(6))
               + "  ·  γ " + (+Number(Isentropic.gamma).toPrecision(4))
               + (Isentropic.branchRequired ? "  ·  " + Isentropic.branch : "")
    }

    // One ratio row: label, value, unit; click copies the value as shown.
    component RatioRow: RowLayout {
        id: ratio
        property var entry: null
        property string weight: "primary"         // primary | inverse | sonic
        readonly property bool primary: weight === "primary"
        Layout.fillWidth: true
        Layout.preferredHeight: primary ? 30 : weight === "inverse" ? 24 : 21
        spacing: Metrics.spacing.m
        visible: entry !== null

        Text {
            Layout.preferredWidth: 150
            text: ratio.entry ? Notation.rich(ratio.entry.label) : ""
            textFormat: ratio.entry ? Notation.textFormat(ratio.entry.label) : Text.PlainText
            color: ratio.primary ? Theme.text : Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: ratio.primary ? Typography.body : Typography.bodySmall
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            text: ratio.entry ? ratio.entry.value + (ratio.entry.unit ? " " + ratio.entry.unit : "") : ""
            color: ratio.entry && !ratio.entry.available ? Theme.textMuted
                 : ratio.primary ? Theme.text : Theme.textSecondary
            font.family: Typography.mono
            font.pixelSize: ratio.primary ? Typography.readoutMedium
                          : ratio.weight === "inverse" ? Typography.readoutSmall : Typography.bodySmall
            font.weight: ratio.primary ? Typography.medium : Typography.regular

            TapHandler { onSingleTapped: if (ratio.entry) Isentropic.copyText(ratio.entry.value) }
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
            objectName: "isentropicInputDrawer"
            Layout.preferredWidth: inputs.implicitWidth
            Layout.fillHeight: true
            title: "Solve from"
            summary: page.caseSummary
            // The solved state first: closed while there is a valid result,
            // open when there is none to show (the inputs need attention).
            // An explicit open or close by the reader wins from then on.
            defaultOpen: !Isentropic.valid
            drawerWidth: Math.max(250, Metrics.railWidth - 20)

            // Scrolls when the window is shorter than the inputs (the 1366
            // floor, or the area-ratio branch control): nothing is cut.
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
                        Layout.fillWidth: true
                        label: "Known quantity"
                        model: page.modes.map(function (m) { return m.label + "   " + m.symbol })
                        // Bound both ways: the mode can also change from the table, and
                        // a selector showing the wrong quantity would mislabel the
                        // input beneath it.
                        currentIndex: page.indexOfMode(Isentropic.mode)
                        // RFComboBox exposes the index, not an activation signal, so the
                        // change handler is where the mode is applied.
                        onCurrentIndexChanged: {
                            if (currentIndex < 0 || currentIndex >= page.modes.length)
                                return
                            // The value field mirrors the controller through its own
                            // binding, so nothing needs to be pushed into it here.
                            Isentropic.mode = page.modes[currentIndex].key
                        }
                    }

                    RFBoundNumberField {
                        id: valueField
                        Layout.fillWidth: true
                        label: page.activeMode ? page.activeMode.symbol : ""
                        value: Isentropic.inputValue
                        digits: 6
                        decimals: 6
                        step: 0.01
                        onValueEdited: function (v) { Isentropic.inputValue = v }
                    }

                    Text {
                        Layout.fillWidth: true
                        readonly property string plainText: page.activeMode ? "Valid range: " + page.activeMode.hint : ""
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
                        value: Isentropic.gamma
                        digits: 4
                        decimals: 4
                        step: 0.005
                        onValueEdited: function (v) { Isentropic.gamma = v }
                    }

                    // Only the area ratio has two roots, so the branch control appears
                    // only for it. It is never defaulted away: the backend refuses to
                    // guess, and so does the interface.
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: Isentropic.branchRequired
                        spacing: Metrics.spacing.xs

                        RFSectionLabel { text: "Branch" }

                        RFSegmentedControl {
                            Layout.fillWidth: true
                            model: ["Subsonic", "Supersonic", "Both"]
                            currentIndex: Isentropic.branch === "subsonic" ? 0
                                        : Isentropic.branch === "supersonic" ? 1 : 2
                            onSelected: function (index) {
                                Isentropic.branch = ["subsonic", "supersonic", "both"][index]
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "A/A* above 1 is reached by one subsonic and one supersonic Mach number."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Presets" }

                    // Buttons rather than a segmented control: presets are actions, not
                    // a persistent selection, and a segmented control with no current
                    // index draws its indicator outside itself.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xs

                        Repeater {
                            model: [0.5, 1.0, 2.0]

                            delegate: RFButton {
                                required property var modelData
                                Layout.fillWidth: true
                                text: "M " + modelData
                                variant: "quiet"
                                compact: true
                                onClicked: {
                                    modeControl.currentIndex = 0
                                    Isentropic.setMachAndSolve(modelData)
                                }
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
                    objectName: "isentropicResults"
                    title: "Solved state"
                    Layout.fillWidth: true
                    contentSpacing: Metrics.spacing.m

                    trailing: Component {
                        RFStatusChip {
                            text: Isentropic.statusLabel
                            tone: Isentropic.statusTone
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: Isentropic.statusMessage !== ""
                        readonly property string plainText: Isentropic.statusMessage
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Isentropic.valid ? Theme.textMuted : Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    // Both roots, when the user asked for both.
                    Repeater {
                        model: Isentropic.bothBranches

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.m

                            Text {
                                Layout.preferredWidth: 170
                                text: Notation.rich(modelData.label)
                                textFormat: Notation.textFormat(modelData.label)
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.value
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutMedium
                                font.weight: Typography.medium
                            }
                        }
                    }

                    // Primary: M and the regime it is classified in. Secondary,
                    // beside it: the Mach angle and the area ratio.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: Isentropic.valid && page.machRow !== null
                        spacing: Metrics.spacing.xl

                        RFResultValue {
                            objectName: "isentropicHeroMach"
                            Layout.alignment: Qt.AlignTop
                            label: page.machRow ? page.machRow.label + "  M" : ""
                            value: page.machRow ? page.machRow.value : "—"
                            scale: "hero"
                        }

                        ColumnLayout {
                            Layout.preferredWidth: 260
                            Layout.alignment: Qt.AlignVCenter
                            spacing: Metrics.spacing.xs
                            visible: Isentropic.flowRegime !== ""

                            RFStatusChip {
                                text: Isentropic.flowRegime
                                tone: Isentropic.flowRegimeTone
                            }
                            Text {
                                Layout.fillWidth: true
                                text: Notation.rich(Isentropic.flowRegimeNote)
                                textFormat: Notation.textFormat(Isentropic.flowRegimeNote)
                                wrapMode: Text.WordWrap
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                        }

                        Item { Layout.fillWidth: true }

                        Repeater {
                            model: page.secondaryKeys

                            delegate: RFResultValue {
                                id: secondary
                                required property var modelData
                                readonly property var entry: { Isentropic.results; return page.row(modelData) }
                                objectName: "isentropicSecondary_" + modelData
                                Layout.alignment: Qt.AlignTop
                                visible: entry !== null
                                label: entry ? entry.label : ""
                                value: entry ? entry.value : "—"
                                unit: entry && entry.unit ? entry.unit : ""
                                scale: "medium"
                                TapHandler { onSingleTapped: if (secondary.entry) Isentropic.copyText(secondary.entry.value) }
                            }
                        }
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        visible: Isentropic.valid
                    }

                    // The ratios, by physical family. One column per family at
                    // any width this page reaches; the pair leads, the sonic
                    // reference sits quietly at the foot of its family.
                    GridLayout {
                        Layout.fillWidth: true
                        visible: Isentropic.valid
                        columns: resultsColumn.width > 760 ? 3 : 1
                        columnSpacing: Metrics.spacing.xl
                        rowSpacing: Metrics.spacing.l

                        Repeater {
                            model: page.families

                            delegate: ColumnLayout {
                                id: family
                                required property var modelData
                                readonly property var order: page.familyOrder(modelData.pair)
                                objectName: "isentropicFamily_" + modelData.name
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.xs

                                RFSectionLabel { text: family.modelData.name }

                                RatioRow {
                                    entry: { Isentropic.results; return page.row(family.order[0]) }
                                    weight: "primary"
                                }
                                RatioRow {
                                    entry: { Isentropic.results; return page.row(family.order[1]) }
                                    weight: "inverse"
                                }
                                Item { Layout.preferredHeight: Metrics.spacing.xs; Layout.fillWidth: true }
                                RatioRow {
                                    entry: { Isentropic.results; return page.row(family.modelData.sonic) }
                                    weight: "sonic"
                                }
                            }
                        }
                    }

                    // Anything the service returns that has no family here is
                    // shown, not dropped.
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: Isentropic.valid && page.otherRows.length > 0
                        spacing: Metrics.spacing.xs

                        RFSectionLabel { text: "Other" }
                        Repeater {
                            model: page.otherRows
                            delegate: RatioRow {
                                required property var modelData
                                entry: modelData
                                weight: "inverse"
                            }
                        }
                    }

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.xl
                        visible: !Isentropic.valid
                        tag: "Input"
                        title: "No result for this input"
                        body: Isentropic.statusMessage
                    }

                    // The model, as the quietest line of the panel -- still in
                    // view when the input drawer is closed.
                    Text {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.s
                        readonly property string plainText: Isentropic.modelName
                                                            + "  ·  " + Isentropic.assumptions.join(" · ")
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
                // One line: how many published rows this state was checked
                // against and how many passed. A failure is named in the line
                // itself, never only inside the details.
                Rectangle {
                    objectName: "isentropicReferenceCheck"
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
                                text: "Anderson Appendix A"
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            RFStatusChip {
                                objectName: "isentropicCheckSummary"
                                text: page.checkSummary
                                tone: page.checkRows.length === 0 ? "neutral"
                                    : page.checkAllPass ? "success" : "warning"
                                showDot: page.checkRows.length > 0
                            }
                            Item { Layout.fillWidth: true }
                            RFToolButton {
                                objectName: "isentropicCheckDetails"
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
                            text: "Anderson Appendix A tabulates γ = 1.4 at discrete Mach numbers. "
                                  + "This Mach number is not one of them, and no value is interpolated."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        // The details: column headings, then one row per quantity.
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
                            text: Isentropic.referenceCitation + " — published reference, not an exact value."
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
