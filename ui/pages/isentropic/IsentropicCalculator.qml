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
 */
Item {
    id: page

    readonly property var modes: Isentropic.solveModes
    readonly property var activeMode: modes[modeControl.currentIndex]

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    // Groups in the order an engineer reads them: what the flow is doing, then
    // the state ratios, then geometry.
    readonly property var groups: ["Flow", "Static / stagnation", "Sonic reference", "Geometric"]
    // Two columns of the same groups, named exactly as the service names them:
    // a group missing from here would silently vanish from the readout.
    readonly property var columns: [["Flow", "Geometric"],
                                    ["Static / stagnation", "Sonic reference"]]

    // M leads on its own (the hero row); every other row stays in its group.
    function rowsIn(group) {
        var out = []
        for (var i = 0; i < Isentropic.results.length; ++i)
            if (Isentropic.results[i].group === group && Isentropic.results[i].key !== "mach")
                out.push(Isentropic.results[i])
        return out
    }

    readonly property var machRow: {
        var list = Isentropic.results
        for (var i = 0; i < list.length; ++i)
            if (list[i].key === "mach")
                return list[i]
        return null
    }

    // The quantities the table and the chart carry are the readouts; the rest
    // -- reciprocals, sonic-reference ratios, the Mach angle -- are quieter.
    // Every row is still shown; only the weight changes.
    readonly property var plottedKeys: {
        var out = {}
        var cols = Isentropic.tableColumns
        for (var i = 0; i < cols.length; ++i)
            if (cols[i].key !== "mach")
                out[cols[i].key] = true
        return out
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- input rail ---------------------------------------------------
        RFPanel {
            title: "Solve from"
            Layout.preferredWidth: Metrics.railWidth - 20
            Layout.minimumWidth: 250
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.l

            // Scrolls when the window is shorter than the inputs and the model
            // statement together -- the 1366 floor, or the area-ratio branch
            // control -- so nothing is cut or runs past the panel. With room,
            // the model statement sits at the foot of the rail.
            Flickable {
                id: inputFlick
                Layout.fillWidth: true
                Layout.fillHeight: true
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
                    height: Math.max(inputFlick.height, implicitHeight)
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

                    Item { Layout.fillHeight: true }

                    RFSectionLabel { text: "Model" }

                    Text {
                        Layout.fillWidth: true
                        text: Isentropic.modelName
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }

                    Text {
                        Layout.fillWidth: true
                        readonly property string plainText: Isentropic.assumptions.join(" · ")
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

                // Sized to what it holds: a tall panel with nothing in its lower
                // half is a frame around empty space.
                RFPanel {
                    title: "Results"
                    Layout.fillWidth: true
                    contentSpacing: Metrics.spacing.m

                    trailing: Component {
                        Row {
                            spacing: Metrics.spacing.s

                            RFStatusChip {
                                anchors.verticalCenter: parent.verticalCenter
                                text: Isentropic.statusLabel
                                tone: Isentropic.statusTone
                            }
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

                    // The state that was solved: M, and the regime the controller
                    // classifies it in. Everything below is a consequence of it.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: Isentropic.valid && page.machRow !== null
                        spacing: Metrics.spacing.xl

                        RFResultValue {
                            Layout.alignment: Qt.AlignTop
                            label: page.machRow ? page.machRow.label + "  M" : ""
                            value: page.machRow ? page.machRow.value : "—"
                            scale: "hero"
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
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
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        visible: Isentropic.valid
                    }

                    // Two-column balanced results layout eliminating widescreen void
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xl
                        Layout.alignment: Qt.AlignTop

                        Repeater {
                            model: page.columns

                            delegate: ColumnLayout {
                                id: colLayout
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.m

                                Repeater {
                                    model: colLayout.modelData

                                    delegate: ColumnLayout {
                                        id: grpLayout
                                        required property var modelData
                                        readonly property var groupRows: page.rowsIn(modelData)

                                        Layout.fillWidth: true
                                        spacing: Metrics.spacing.xs
                                        visible: groupRows.length > 0

                                        RFSectionLabel { text: Notation.sectionRich(grpLayout.modelData); textFormat: Notation.textFormat(grpLayout.modelData) }

                                        Repeater {
                                            model: grpLayout.groupRows

                                            delegate: RowLayout {
                                                id: resultRow
                                                required property var modelData
                                                readonly property bool plotted:
                                                    page.plottedKeys[modelData.key] === true
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: plotted ? 26 : 22
                                                spacing: Metrics.spacing.m

                                                Text {
                                                    Layout.preferredWidth: 170
                                                    text: Notation.rich(modelData.label)
                                                    textFormat: Notation.textFormat(modelData.label)
                                                    color: resultRow.plotted ? Theme.text : Theme.textSecondary
                                                    font.family: Typography.sans
                                                    font.pixelSize: resultRow.plotted ? Typography.body
                                                                                      : Typography.bodySmall
                                                }

                                                Text {
                                                    Layout.fillWidth: true
                                                    text: modelData.value + (modelData.unit ? " " + modelData.unit : "")
                                                    color: !modelData.available ? Theme.textMuted
                                                         : resultRow.plotted ? Theme.text : Theme.textSecondary
                                                    font.family: Typography.mono
                                                    font.pixelSize: resultRow.plotted ? Typography.readoutMedium
                                                                                      : Typography.readoutSmall
                                                    font.weight: resultRow.plotted ? Typography.medium
                                                                                   : Typography.regular

                                                    TapHandler {
                                                        onSingleTapped: Isentropic.copyText(modelData.value)
                                                    }
                                                    HoverHandler { id: valueHover }
                                                }

                                                Text {
                                                    text: "copy"
                                                    opacity: valueHover.hovered ? 1 : 0
                                                    color: Theme.textMuted
                                                    font.family: Typography.sans
                                                    font.pixelSize: Typography.meta
                                                    Behavior on opacity { NumberAnimation { duration: 90 } }
                                                }
                                            }
                                        }
                                    }
                                }
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
                }

                // ---- reference check ------------------------------------------
                // Sized to its rows: four quantities and a citation are evidence,
                // not a region to reserve height for.
                RFPanel {
                    title: "Reference check"
                    Layout.fillWidth: true
                    contentSpacing: Metrics.spacing.xs

                    trailing: Component {
                        RFStatusChip {
                            text: check.rows.length > 0 ? "Published row available" : "No exact reference row"
                            tone: check.rows.length > 0 ? "success" : "neutral"
                            showDot: false
                        }
                    }

                    Item {
                        id: check
                        // A property made with the result, so a new result brings
                        // its own comparison and opening this view solves nothing.
                        // (The slot form re-ran the relations whenever a view
                        // first read it.)
                        readonly property var rows: Isentropic.currentMachComparison
                        Layout.fillWidth: true
                        Layout.preferredHeight: 0
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: check.rows.length === 0
                        text: "Anderson Appendix A tabulates γ = 1.4 at discrete Mach numbers. "
                              + "This Mach number is not one of them, and no value is interpolated."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    // Column headings, so each figure says what it is.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: check.rows.length > 0
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
                        model: check.rows

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
