import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The relation, and where the solved state sits on it.
 *
 * An analytical workspace in two parts. On the left, the context: what is
 * being solved from, the solved state and its regime, and the plotted
 * quantities at that state -- the one on the chart first. On the right, the
 * relation itself, with the solved state marked on it: a ring at the solved
 * Mach number and value, and a guide down to each axis.
 *
 * Nothing here is evaluated. The curve is the generated table (the same block
 * the Table view renders); the point is the calculator's solved result, read
 * from its rows. The two are only drawn together when they describe the same
 * gas: the table is generated at its own gamma, and a result solved at another
 * one does not lie on that curve -- so it is then marked by its Mach number
 * alone, and the caption says why. Invalid input has no solved state, so no
 * point is drawn: the chart never keeps a previous result's marker.
 *
 * Plotted from the same computed block the table renders, one quantity at a
 * time: p0/p spans four decades over this Mach range while T0/T spans one,
 * and overlaying them on a shared axis would flatten the smaller curve.
 */
Item {
    id: page

    readonly property bool compact: width < 1500 || height < 640

    // ---- the relation ---------------------------------------------------
    readonly property var quantities: Isentropic.tableColumns.filter(function (c) {
        return c.key !== "mach"
    })
    property int quantityIndex: 0
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)]
                                  : null
    // A property of the controller, so a regenerated table redraws the curve.
    readonly property var points: active ? (Isentropic.chartData[active.key] || []) : []
    property bool logScale: true

    // ---- the solved state -----------------------------------------------
    readonly property var modes: Isentropic.solveModes
    readonly property var activeMode: modes[modeControl.currentIndex]

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    // The backend's own word for a quantity, from the solve-mode registry
    // keyed by the same key the table column and result row carry.
    function captionFor(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return modes[i].label
        return ""
    }

    // The third layer: every other solved value, quietly. Nothing discarded,
    // nothing competing with M or with the plotted quantities.
    readonly property var otherRows: {
        var plotted = {}
        for (var i = 0; i < quantities.length; ++i)
            plotted[quantities[i].key] = true
        var out = []
        var list = Isentropic.results
        for (var j = 0; j < list.length; ++j)
            if (list[j].key !== "mach" && plotted[list[j].key] !== true)
                out.push(list[j])
        return out
    }

    // The solved rows by key -- the frozen output, formatted by the backend.
    readonly property var rows: {
        var out = {}
        var list = Isentropic.results
        for (var i = 0; i < list.length; ++i)
            out[list[i].key] = list[i]
        return out
    }
    readonly property var machRow: rows["mach"] !== undefined ? rows["mach"] : null
    readonly property var activeRow: active && rows[active.key] !== undefined
                                     ? rows[active.key] : null

    // Comparisons only: which curve this is, and whether the point is on it.
    readonly property bool sameGas: Isentropic.gamma === Isentropic.plottedGamma
    readonly property bool inRange: Isentropic.valid && points.length > 1
                                    && Isentropic.mach >= points[0].x
                                    && Isentropic.mach <= points[points.length - 1].x
    readonly property bool onCurve: inRange && sameGas && page.activeRow !== null
    // Which way the plotted curve runs through the solved point, read off
    // the neighbouring table points -- only so the ring's label can sit on
    // the side the curve leaves clear.
    readonly property int slope: {
        if (!page.inRange)
            return 1
        for (var i = 1; i < page.points.length; ++i)
            if (page.points[i].x >= Isentropic.mach)
                return page.points[i].y >= page.points[i - 1].y ? 1 : -1
        return 1
    }
    readonly property var otherRoot: {
        var both = Isentropic.bothBranches
        return both.length === 2 ? both[0] : null      // the subsonic root
    }

    RowLayout {
        anchors.fill: parent
        spacing: page.compact ? Metrics.spacing.l : Metrics.spacing.xl

        // =================================================================
        // CONTEXT — inputs, the solved state, and the numbers on the chart
        // =================================================================
        Flickable {
            id: rail
            Layout.preferredWidth: Math.max(400, Math.min(820, page.width * 0.36))
            Layout.maximumWidth: Math.max(400, Math.min(820, page.width * 0.36))
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: context.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: RFScrollBar {
                policy: rail.contentHeight > rail.height ? ScrollBar.AlwaysOn
                                                         : ScrollBar.AsNeeded
            }

            ColumnLayout {
                id: context
                width: rail.width - (rail.contentHeight > rail.height ? 12 : 0)
                spacing: page.compact ? Metrics.spacing.s : Metrics.spacing.m

                // ---- solve from ------------------------------------------
                RFSectionLabel { text: "Solve from" }

                RFComboBox {
                    id: modeControl
                    Layout.fillWidth: true
                    label: "Known quantity"
                    model: page.modes.map(function (m) { return m.label + "   " + m.symbol })
                    // Bound to the controller, written back only when a person
                    // picks: the mode also changes from the other views and
                    // the presets, and a selector showing the wrong quantity
                    // would mislabel the value beneath it.
                    currentIndex: page.indexOfMode(Isentropic.mode)
                    onActivated: function (index) {
                        if (index >= 0 && index < page.modes.length)
                            Isentropic.mode = page.modes[index].key
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.l

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        label: page.activeMode ? page.activeMode.symbol : ""
                        value: Isentropic.inputValue
                        digits: 6
                        decimals: 6
                        step: 0.01
                        onValueEdited: function (v) { Isentropic.inputValue = v }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        label: "Specific heat ratio  γ"
                        value: Isentropic.gamma
                        digits: 4
                        decimals: 4
                        step: 0.005
                        onValueEdited: function (v) { Isentropic.gamma = v }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: !page.compact
                    readonly property string plainText: page.activeMode
                                                        ? "Valid range: " + page.activeMode.hint : ""
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                // Only the area ratio has two roots. The backend refuses to
                // guess one, and so does the interface.
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
                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: !page.compact
                    spacing: Metrics.spacing.xs

                    Repeater {
                        model: [0.5, 1.0, 2.0]

                        delegate: RFButton {
                            required property var modelData
                            Layout.fillWidth: true
                            text: "M " + modelData
                            variant: "quiet"
                            compact: true
                            // The controller switches the mode to M itself,
                            // and the selector above follows its binding.
                            onClicked: Isentropic.setMachAndSolve(modelData)
                        }
                    }
                }

                RFDivider { Layout.fillWidth: true; Layout.topMargin: Metrics.spacing.xs }

                // ---- the solved state --------------------------------------
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s
                    RFSectionLabel { text: "Solved state" }
                    Item { Layout.fillWidth: true }
                    RFStatusChip {
                        text: Isentropic.statusLabel
                        tone: Isentropic.statusTone
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.xl
                    visible: Isentropic.valid

                    RFResultValue {
                        Layout.alignment: Qt.AlignTop
                        label: "Mach number  M"
                        value: page.machRow ? page.machRow.value : "—"
                        scale: page.compact ? "large" : "hero"
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        spacing: Metrics.spacing.xs

                        RFStatusChip {
                            visible: Isentropic.flowRegime !== ""
                            text: Isentropic.flowRegime
                            tone: Isentropic.flowRegimeTone
                        }
                        Text {
                            Layout.fillWidth: true
                            readonly property string plainText: Isentropic.flowRegimeNote
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
                            wrapMode: Text.WordWrap
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                    }
                }

                // Both roots, when both were asked for.
                Repeater {
                    model: Isentropic.bothBranches

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.m
                        Text {
                            Layout.preferredWidth: 130
                            text: modelData.label
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            text: modelData.value
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.readoutSmall
                        }
                    }
                }

                // No solved state: the reason, in the backend's words -- and
                // nothing else, so no earlier result can pass for this one.
                Text {
                    Layout.fillWidth: true
                    visible: !Isentropic.valid
                    readonly property string plainText: Isentropic.statusMessage
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                RFDivider {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xs
                    visible: Isentropic.valid
                }

                // ---- layer 2: the plotted quantities at this state ---------
                // The four the table and chart carry, each with the backend's
                // word for it. The one on the chart is marked, not enlarged:
                // it is the view's choice, not the answer. Choosing a row
                // plots it -- a view selection, so nothing is solved.
                RFSectionLabel {
                    visible: Isentropic.valid
                    text: "At this Mach number"
                }

                Repeater {
                    model: Isentropic.valid ? page.quantities : []

                    delegate: Item {
                        id: quantityRow
                        required property var modelData
                        required property int index
                        readonly property bool current: index === page.quantityIndex
                        readonly property var row: page.rows[modelData.key] !== undefined
                                                   ? page.rows[modelData.key] : null

                        Layout.fillWidth: true
                        implicitHeight: page.compact ? 24 : 32

                        Rectangle {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            width: 2
                            height: parent.height - 8
                            color: Theme.accent
                            visible: quantityRow.current
                        }

                        Row {
                            anchors.left: parent.left
                            anchors.leftMargin: Metrics.spacing.m
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: Metrics.spacing.s
                            Text {
                                id: symbolText
                                width: 56
                                text: Notation.rich(quantityRow.modelData.label)
                                textFormat: Notation.textFormat(quantityRow.modelData.label)
                                color: quantityRow.current ? Theme.text : Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                            }
                            Text {
                                anchors.baseline: symbolText.baseline
                                text: page.captionFor(quantityRow.modelData.key)
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }

                        Text {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: quantityRow.row ? quantityRow.row.value : "—"
                            color: quantityRow.current ? Theme.accent : Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.readoutMedium
                            font.weight: Typography.medium
                        }

                        TapHandler {
                            onTapped: page.quantityIndex = quantityRow.index
                        }
                        HoverHandler { cursorShape: Qt.PointingHandCursor }
                    }
                }

                // ---- layer 3: the rest of the solved state -----------------
                RFDivider {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xs
                    visible: Isentropic.valid && page.otherRows.length > 0
                }

                RFSectionLabel {
                    visible: Isentropic.valid && page.otherRows.length > 0
                    text: "Also at this state"
                }

                GridLayout {
                    Layout.fillWidth: true
                    visible: Isentropic.valid && page.otherRows.length > 0
                    columns: 2
                    columnSpacing: Metrics.spacing.xl
                    rowSpacing: page.compact ? 0 : Metrics.spacing.xxs

                    Repeater {
                        model: page.otherRows

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                text: Notation.rich(modelData.label)
                                textFormat: Notation.textFormat(modelData.label)
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                            Text {
                                text: modelData.value + (modelData.unit ? " " + modelData.unit : "")
                                color: modelData.available ? Theme.textSecondary : Theme.textMuted
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutSmall
                            }
                        }
                    }
                }

                // A pointer to the tabs above; at the 1366 floor the solved
                // state keeps the height instead.
                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xs
                    visible: Isentropic.valid && !page.compact
                    text: "The published reference check is on Calculator; the tabulated "
                          + "block is on Table."
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Item { Layout.fillHeight: true }
            }
        }

        RFDivider {
            Layout.fillHeight: true
            Layout.preferredWidth: Metrics.hairline
            vertical: true
        }

        // =================================================================
        // THE RELATION — the chart, with the solved state on it
        // =================================================================
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.s

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                RFSectionLabel {
                    readonly property string plainText: page.active
                                                        ? page.active.label + "  versus  M" : "Relation"
                    text: Notation.sectionRich(plainText)
                    textFormat: Notation.textFormat(plainText)
                }

                Item { Layout.fillWidth: true }

                // Named with the backend's words: as symbols, p0/p and
                // rho0/rho differ by one glyph and read as the same button.
                RFSegmentedControl {
                    Layout.preferredWidth: page.compact ? 440 : 540
                    model: page.quantities.map(function (q) { return page.captionFor(q.key) })
                    currentIndex: page.quantityIndex
                    onSelected: function (index) { page.quantityIndex = index }
                }

                RFToggle {
                    text: page.compact ? "Log axis" : "Logarithmic vertical axis"
                    checked: page.logScale
                    onToggled: page.logScale = checked
                }
            }

            RFLineChart {
                id: plot
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240

                points: page.points
                logScale: page.logScale
                // The one Mach number every reader looks for. RFLineChart
                // draws it only when it falls inside the plotted range.
                markerX: 1
                markerLabel: "M = 1"
                xLabel: "Mach number"
                yLabel: page.active ? page.active.label : ""

                // The solved state, drawn only where it lies on this curve.
                markers: page.onCurve
                         ? [{ x: Isentropic.mach, y: page.activeRow.raw, slope: page.slope,
                              label: "M " + page.machRow.value + "   "
                                     + page.active.label + " " + page.activeRow.value }]
                         : []
                guides: {
                    var out = []
                    if (page.inRange)
                        out.push({ value: Isentropic.mach, axis: "x", label: "" })
                    if (page.onCurve)
                        out.push({ value: page.activeRow.raw, axis: "y", label: "" })
                    if (page.otherRoot && page.points.length > 1
                            && page.otherRoot.raw >= page.points[0].x
                            && page.otherRoot.raw <= page.points[page.points.length - 1].x)
                        out.push({ value: page.otherRoot.raw, axis: "x", label: "" })
                    return out
                }
            }

            // What the curve is, and what the point is -- in words, because a
            // ring on a curve reads as "this state lies on this relation".
            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                Text {
                    Layout.fillWidth: true
                    readonly property string plainText: {
                        if (page.points.length < 2)
                            return "No table is generated, so there is no curve to draw."
                        var curve = "Curve: the generated table, " + page.points.length
                                    + " points at γ = " + Isentropic.plottedGamma.toFixed(3) + "."
                        if (!Isentropic.valid)
                            return curve + " No solved state to mark."
                        if (!page.inRange)
                            return curve + " The solved M = " + page.machRow.value
                                   + " lies outside the plotted range."
                        if (!page.sameGas)
                            return curve + " The solved state is at γ = "
                                   + Isentropic.gamma.toFixed(3)
                                   + ", not on this curve, so it is marked by its Mach number only."
                        var ring = curve + " Ring: the solved state at the same γ."
                        return page.otherRoot
                               ? ring + " The second dashed line is the subsonic root, M = "
                                 + page.otherRoot.value + "."
                               : ring
                    }
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    elide: Text.ElideRight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Text {
                    // A toggle that silently does nothing is worse than one
                    // that says why.
                    visible: page.logScale && !plot.logScaleActive
                    text: "range too narrow for a log axis"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }
}
