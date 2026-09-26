import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../components/viewport"
import "../../data"

/*
 * The performance workspace: an instrument, not a form.
 *
 * Three zones. An INPUT RAIL on the left, the PROPULSION CANVAS in the middle,
 * a READOUT RAIL on the right, and a MODEL TRACE beneath all three. The
 * physical system is the centre of the page; the controls are quieter than the
 * science; the provenance is quieter still.
 *
 * There is no arithmetic in this file. Not a unit conversion, not a ratio, not
 * a gamma: every value arrives from the controller already formatted, and every
 * note beside a control was written in the service where it can be tested. The
 * canvas receives solved numbers and turns them into pixels; that is the only
 * computation here and it is geometry, not physics.
 *
 * Two things this view is careful about, and both are about the boundary with
 * the chemistry workspace:
 *
 *   - the chamber state it starts from is shown here, not left on another tab.
 *     A reader judging whether an Isp is plausible needs T_0 and both gammas in
 *     front of them, and sending them elsewhere is how the wrong gamma gets
 *     used.
 *   - when that chamber changes underneath, the result is marked as belonging
 *     to a superseded chamber. It is not recomputed, and it is not relabelled.
 *
 * The canvas and the readouts are driven by the SOLVED snapshot, never by the
 * live input fields, so an edited expansion ratio marks the result stale
 * instead of quietly redrawing the nozzle to a shape nobody has solved.
 */
Item {
    id: view

    // Asks the shell for another workspace -- the chamber state this one
    // needs is solved in Thermochemistry. Navigation only; nothing is solved.
    signal workspaceRequested(int index)

    readonly property bool compact: width < 1250
    readonly property bool roomy: width > 1700
    // The solved expansion as the 2D schematic or in 3D -- view state only.
    property string objectView: "2d"

    function indexOfKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key)
                return i
        return 0
    }

    function noteForKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key)
                return options[i].note !== undefined ? options[i].note : ""
        return ""
    }

    // =====================================================================
    // no chamber state: the workspace refuses rather than estimating one
    // =====================================================================
    // Shown in the workspace itself, not a card in front of it: the input
    // rail says where the chamber comes from and opens Thermochemistry, the
    // canvas holds its labelled unsolved outline, the readout rail says what
    // it will hold, and Calculate waits. No number, contour or annotation
    // stands in for the chamber state -- there is nothing to expand, and a
    // plausible reading would be an invention.
    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        // =================================================================
        // the three zones
        // =================================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: view.compact ? Metrics.spacing.m : Metrics.spacing.xl

            // -------------------------------------------------------------
            // INPUT RAIL
            // -------------------------------------------------------------
            ColumnLayout {
                Layout.preferredWidth: view.compact ? 236 : 268
                Layout.minimumWidth: view.compact ? 236 : 268
                Layout.maximumWidth: view.compact ? 236 : 268
                Layout.fillHeight: true
                spacing: Metrics.spacing.s

              Flickable {
                id: inputRail
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: inputColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                // The workspace scrollbar is quiet by design: invisible until
                // touched. That is right for a rail whose content fits and
                // wrong for one whose content does not -- at 1366x768 this
                // rail scrolls to Ambient and Engine size, and at rest nothing
                // said they were there. The old design clipped them outright,
                // which the audit recorded as RESPONSIVE_LAYOUT_BLOCKER;
                // reaching them by a scroll nobody can see is the quieter
                // version of the same failure. So while, and only while, there
                // is more than fits, the bar stays visible -- and its thumb
                // says how much more.
                ScrollBar.vertical: RFScrollBar {
                    policy: inputRail.contentHeight > inputRail.height
                            ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
                }

                ColumnLayout {
                    id: inputColumn
                    width: inputRail.width - (inputRail.contentHeight > inputRail.height ? 10 : 0)
                    spacing: Metrics.spacing.m

                    // ---- chamber source ----------------------------------
                    RFSectionLabel { text: "Chamber source" }

                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: !RocketPerformance.hasChamber
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.fillWidth: true
                            text: "No chamber state"
                            color: Theme.warning
                            font.family: Typography.sans
                            font.pixelSize: Typography.body
                            font.weight: Typography.medium
                        }
                        Text {
                            Layout.fillWidth: true
                            text: RocketPerformance.chamberMissingMessage
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        RFButton {
                            Layout.fillWidth: true
                            Layout.topMargin: Metrics.spacing.xs
                            text: "Open Thermochemistry"
                            variant: "primary"
                            onClicked: view.workspaceRequested(Navigation.indexOfKey("thermochem"))
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: Notation.rich(RocketPerformance.chamberHeadline)
                        textFormat: Notation.textFormat(RocketPerformance.chamberHeadline)
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                        wrapMode: Text.WordWrap
                    }

                    Repeater {
                        model: RocketPerformance.chamberModel
                        delegate: RowLayout {
                            id: chamberRow
                            required property string label
                            required property string value
                            required property string unit
                            Layout.fillWidth: true
                            Layout.fillHeight: false
                            spacing: Metrics.spacing.xs

                            Text {
                                Layout.fillWidth: true
                                text: Notation.rich(chamberRow.label)
                                textFormat: Notation.textFormat(chamberRow.label)
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                elide: Text.ElideRight
                                clip: true              // RichText does not elide
                            }
                            Text {
                                readonly property string plainText: chamberRow.value
                                text: Notation.rich(plainText)
                                textFormat: Notation.textFormat(plainText)
                                color: Theme.textSecondary
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                text: chamberRow.unit
                                color: Theme.textDisabled
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }
                    }

                    RFDivider { Layout.fillWidth: true }

                    // ---- gas reduction -----------------------------------
                    RFSectionLabel { text: "Gas model" }

                    RFComboBox {
                        Layout.fillWidth: true
                        label: "Gamma basis"
                        model: RocketPerformance.gammaBasisOptions.map(
                                   function (o) { return o.label })
                        currentIndex: view.indexOfKey(RocketPerformance.gammaBasisOptions,
                                                      RocketPerformance.gammaBasis)
                        onActivated: function (index) {
                            var options = RocketPerformance.gammaBasisOptions
                            if (index >= 0 && index < options.length)
                                RocketPerformance.gammaBasis = options[index].key
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: !view.compact
                        text: RocketPerformance.gammaBasisNote
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFComboBox {
                        Layout.fillWidth: true
                        label: "Gamma taken at"
                        model: RocketPerformance.gammaStrategyOptions.map(
                                   function (o) { return o.label })
                        currentIndex: view.indexOfKey(RocketPerformance.gammaStrategyOptions,
                                                      RocketPerformance.gammaStrategy)
                        onActivated: function (index) {
                            var options = RocketPerformance.gammaStrategyOptions
                            if (index >= 0 && index < options.length)
                                RocketPerformance.gammaStrategy = options[index].key
                        }
                    }

                    RFDivider { Layout.fillWidth: true }

                    // ---- nozzle ------------------------------------------
                    RFSectionLabel { text: "Nozzle" }

                    RFBoundNumberField {
                        id: areaRatioField
                        Layout.fillWidth: true
                        label: "Expansion ratio  <i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>"
                        value: RocketPerformance.areaRatio
                        digits: 3
                        step: 1
                        onValueEdited: function (v) { RocketPerformance.areaRatio = v }

                        HoverHandler { id: areaRatioHover }
                        RFTooltip {
                            visible: areaRatioHover.hovered
                            text: "Exit area over throat area, above 1. It fixes the exit "
                                  + "Mach number and the exit pressure by itself — the "
                                  + "ambient pressure does not enter them."
                        }
                    }

                    RFDivider { Layout.fillWidth: true }

                    // ---- ambient -----------------------------------------
                    RFSectionLabel { text: "Ambient" }

                    RFComboBox {
                        Layout.fillWidth: true
                        label: "Condition"
                        model: RocketPerformance.ambientOptions.map(
                                   function (o) { return o.label })
                        currentIndex: view.indexOfKey(RocketPerformance.ambientOptions,
                                                      RocketPerformance.ambientMode)
                        onActivated: function (index) {
                            var options = RocketPerformance.ambientOptions
                            if (index >= 0 && index < options.length)
                                RocketPerformance.ambientMode = options[index].key
                        }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        visible: RocketPerformance.ambientMode === "custom"
                        label: "Ambient pressure  <i>p</i><sub>a</sub>  [Pa]"
                        value: RocketPerformance.ambientPressure
                        digits: 1
                        step: 1000
                        onValueEdited: function (v) { RocketPerformance.ambientPressure = v }
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: !view.compact
                        readonly property string plainText: view.noteForKey(RocketPerformance.ambientOptions,
                                              RocketPerformance.ambientMode)
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFDivider { Layout.fillWidth: true }

                    // ---- engine size -------------------------------------
                    RFSectionLabel { text: "Engine size" }

                    RFComboBox {
                        Layout.fillWidth: true
                        label: "Scale by"
                        model: RocketPerformance.scaleOptions.map(
                                   function (o) { return o.label })
                        currentIndex: view.indexOfKey(RocketPerformance.scaleOptions,
                                                      RocketPerformance.scaleMode)
                        onActivated: function (index) {
                            var options = RocketPerformance.scaleOptions
                            if (index >= 0 && index < options.length)
                                RocketPerformance.scaleMode = options[index].key
                        }
                    }

                    RFBoundNumberField {
                        Layout.fillWidth: true
                        visible: RocketPerformance.scaleNeedsValue
                        label: RocketPerformance.scaleLabel
                        value: RocketPerformance.scaleValue
                        digits: 6
                        step: 0.001
                        onValueEdited: function (v) { RocketPerformance.scaleValue = v }
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: !RocketPerformance.scaled
                        text: RocketPerformance.unscaledNote
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    Item { Layout.preferredHeight: Metrics.spacing.xs }
                }
              }

              // Pinned outside the scrolling body. At 1366 the rail no longer
              // fits its own content, and the one control that must never
              // scroll out of reach is the one that produces a result.
              RFDivider { Layout.fillWidth: true }

              RowLayout {
                  Layout.fillWidth: true
                  Layout.fillHeight: false
                  spacing: Metrics.spacing.s

                  RFButton {
                      Layout.fillWidth: true
                      text: "Calculate"
                      variant: RocketPerformance.hasChamber ? "primary" : "default"
                      enabled: RocketPerformance.hasChamber
                      onClicked: RocketPerformance.calculate()
                  }
                  RFButton {
                      text: "Reset"
                      variant: "quiet"
                      onClicked: RocketPerformance.resetInputs()
                  }
              }
            }

            RFDivider {
                Layout.fillHeight: true
                Layout.preferredWidth: Metrics.hairline
                vertical: true
            }

            // -------------------------------------------------------------
            // PROPULSION CANVAS — the centre of gravity
            // -------------------------------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.spacing.s

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: Metrics.spacing.s

                    RFSectionLabel { text: "Propulsion" }
                    RFViewSwitch {
                        id: objectSwitch
                        objectName: "performanceViewSwitch"
                        implicitWidth: view.compact ? 150 : 210
                        flatLabel: view.compact ? "2D" : "2D schematic"
                        mode: view.objectView
                        onModeRequested: function (mode) { view.objectView = mode }
                    }
                    Item { Layout.fillWidth: true }
                    RFStatusChip {
                        text: RocketPerformance.statusLabel
                        tone: RocketPerformance.statusTone
                    }
                    RFStatusChip {
                        visible: RocketPerformance.resultStale
                        text: "Stale — recalculate"
                        tone: "warning"
                    }
                    RFStatusChip {
                        visible: RocketPerformance.chamberSuperseded
                        text: "Superseded chamber"
                        tone: "warning"
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: RocketPerformance.hasResult
                    // The result's own case, not the live form. Editing an
                    // input must not relabel the drawing beneath this line.
                    text: Notation.rich(RocketPerformance.resultHeadline)
                    textFormat: Notation.textFormat(RocketPerformance.resultHeadline)
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                    elide: Text.ElideRight
                    clip: true              // RichText does not elide
                }

                // Before the first Calculate there is a chamber and no
                // expansion: the canvas draws its own illustrative outline,
                // under its own weaker label, dimmed. Handing it the unsolved
                // radius ratio (0) drew a throat wider than the chamber under
                // the solved-schematic label.
                PerfNozzleCanvas {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 190
                    visible: !objectSwitch.show3D
                    placeholder: !RocketPerformance.hasResult
                    opacity: RocketPerformance.hasResult ? 1 : 0.7
                    radiusRatio: RocketPerformance.solvedRadiusRatio
                    hasResult: RocketPerformance.hasResult
                    stale: RocketPerformance.resultStale
                    regime: RocketPerformance.solvedRegime
                    exitMachText: RocketPerformance.solvedExitMach > 0
                                  ? RocketPerformance.solvedExitMach.toFixed(3) : ""
                    chamberPressureText: RocketPerformance.solvedChamberPressureText
                }

                // The same schematic, revolved: the result's own snapshot,
                // loaded only while shown. Before a solve it says so rather
                // than drawing an outline.
                Perf3DView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 190
                    visible: objectSwitch.show3D
                    active: objectSwitch.show3D
                }

                // ---- the exit / ambient relation -------------------------
                PerfPressureRelation {
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    visible: RocketPerformance.hasResult
                    regimeLabel: RocketPerformance.regimeLabel
                    sign: RocketPerformance.pressureThrustSign
                    relationText: RocketPerformance.pressureRelationText
                    ambientLabel: RocketPerformance.ambientLabel
                    exitModel: RocketPerformance.exitStateModel
                    stale: RocketPerformance.resultStale
                }

                Text {
                    Layout.fillWidth: true
                    visible: !RocketPerformance.hasResult
                    // A refusal speaks for itself; before the first solve
                    // there is no message, so say what the next step is.
                    text: RocketPerformance.message !== ""
                          ? RocketPerformance.message
                          : RocketPerformance.hasChamber
                            ? "Chamber state ready. Set the nozzle and the ambient on the "
                              + "left, then Calculate to expand it."
                            : "No chamber state to expand. Solve one in Thermochemistry; "
                              + "nothing is estimated in its place."
                    color: RocketPerformance.statusTone === "danger"
                           ? Theme.error : Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                    wrapMode: Text.WordWrap
                }
            }

            RFDivider {
                Layout.fillHeight: true
                Layout.preferredWidth: Metrics.hairline
                vertical: true
            }

            // -------------------------------------------------------------
            // READOUT RAIL
            // -------------------------------------------------------------
            Flickable {
                id: resultRail
                Layout.preferredWidth: view.compact ? 250 : (view.roomy ? 320 : 290)
                Layout.minimumWidth: view.compact ? 250 : (view.roomy ? 320 : 290)
                Layout.maximumWidth: view.compact ? 250 : (view.roomy ? 320 : 290)
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: resultColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {
                    policy: resultRail.contentHeight > resultRail.height
                            ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
                }

                ColumnLayout {
                    id: resultColumn
                    width: resultRail.width - (resultRail.contentHeight > resultRail.height ? 10 : 0)
                    spacing: Metrics.spacing.m

                    Repeater {
                        model: RocketPerformance.headlineModel
                        delegate: PerfMetricReadout {
                            // `id` is not decoration here: the role names
                            // match this component's own property names, so
                            // an unqualified `value: value` binds the
                            // property to itself and Qt reports a binding
                            // loop.
                            id: metricRow
                            required property string rowSymbol
                            required property string rowValue
                            required property string rowUnit
                            required property string rowLabel
                            required property bool rowPrimary
                            Layout.fillWidth: true
                            symbol: metricRow.rowSymbol
                            value: metricRow.rowValue
                            unit: metricRow.rowUnit
                            label: metricRow.rowLabel
                            primary: metricRow.rowPrimary
                            stale: RocketPerformance.resultStale
                        }
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        visible: RocketPerformance.cfTermsCount > 0
                    }

                    // Until something is solved the rail says what it will
                    // hold, rather than showing an empty heading.
                    Text {
                        Layout.fillWidth: true
                        visible: !RocketPerformance.hasResult
                        readonly property string plainText: "Not calculated yet. I_sp, C_f, c* and "
                              + "c_eff appear here, with the C_f terms."
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }

                    PerfBreakdown {
                        Layout.fillWidth: true
                        visible: RocketPerformance.cfTermsCount > 0
                        title: "Cf terms"
                        rowModel: RocketPerformance.cfTermsModel
                        stale: RocketPerformance.resultStale
                    }

                    PerfBreakdown {
                        Layout.fillWidth: true
                        visible: RocketPerformance.thrustTermsCount > 0
                        title: "Thrust terms  [N]"
                        rowModel: RocketPerformance.thrustTermsModel
                        stale: RocketPerformance.resultStale
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }

        // =================================================================
        // MODEL TRACE — tertiary, one strip, never six surfaces
        // =================================================================
        RFDivider { Layout.fillWidth: true }

        Flow {
            Layout.fillWidth: true
            visible: RocketPerformance.hasResult
            spacing: Metrics.spacing.l

            Repeater {
                model: RocketPerformance.traceModel
                delegate: Row {
                    id: traceItem
                    required property string label
                    required property string value
                    spacing: Metrics.spacing.xs

                    Text {
                        text: Notation.rich(traceItem.label)
                        textFormat: Notation.textFormat(traceItem.label)
                        color: Theme.textDisabled
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: Typography.sectionTracking
                    }
                    Text {
                        readonly property string plainText: traceItem.value
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }

            Row {
                spacing: Metrics.spacing.xs
                visible: RocketPerformance.warningCount > 0

                Text {
                    text: "Warnings"
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    font.letterSpacing: Typography.sectionTracking
                }
                Text {
                    text: RocketPerformance.warningCount + " — see Model tab"
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }
}
