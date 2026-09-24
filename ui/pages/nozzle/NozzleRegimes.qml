import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The nozzle at its operating point, and the back-pressure map around it.
 *
 * The page's default view, and object-first: the dominant region is the
 * nozzle itself -- the solved area distribution drawn to scale, with the
 * throat and, while there is one, the normal shock at their solved stations
 * -- beside the regime the backend classified it in and the handful of
 * numbers that regime is about. Below it, the back pressure that sets the
 * operating point, on the map whose every band edge is a computed critical,
 * and the shock-station curve as supporting evidence rather than the subject.
 *
 * Nothing is evaluated here. The regime, its words and its tone come from the
 * backend registry; the thresholds, the bands and the shock curve are solved
 * with the operating point, only when the nozzle or the gas changes, and read
 * here as properties -- so opening this view, switching to it or changing the
 * theme solves nothing. Every other number the solve produced is one tab
 * away, on Operating point.
 *
 * Ideal expansion is a single point on the map, not a range, and it is drawn
 * as a point. Widening it to something clickable would be the one dishonest
 * thing the map could do, so the three exact conditions are reachable by the
 * preset buttons instead -- each sets the back pressure to the threshold the
 * backend computed.
 */
Item {
    id: page

    // 1366x768 gives this view about 1250x500: the object and the map share
    // that height, and the prose that explains the map yields first.
    readonly property bool compact: width < 1500 || height < 640
    readonly property bool roomy: width > 2200 && height > 1000
    readonly property bool railChart: !page.compact && !page.roomy

    // Where the shock stands against back pressure: supporting evidence for
    // the regime, never the subject. Beside the regime in the rail at 1920;
    // beside the nozzle at the 1366 floor, where the rail has no height to
    // spare and the drawing, scaled by height, leaves width unused; in the
    // map beside the back-pressure control at 2560, where there is room for
    // it to be read as a chart.
    component ShockCurveChart: RFLineChart {
        // Solved with the operating point whenever the nozzle or the gas
        // changes -- the same shock solver the calculator uses -- and read
        // here, never re-solved by the view.
        series: [{ points: Nozzle.shockCurve, color: Theme.accent, width: 1.8 }]
        // The solved operating point, while it lies on the curve.
        markers: {
            var shock = page.readout("shock_area_ratio")
            return Nozzle.hasShock && shock
                   ? [{ x: Nozzle.backPressureRatio, y: shock.raw,
                        label: "operating point" }]
                   : []
        }
        logScale: false
        xLabel: "back pressure  p_b/p₀"
        yLabel: "A_s/A_t"
    }

    component ShockCurveCaption: Text {
        readonly property string plainText: Nozzle.hasShock
              ? "Internal-shock interval only; lower back pressure, larger A_s."
              : "Internal-shock interval only; no internal shock at this point."
        text: Notation.rich(plainText)
        textFormat: Notation.textFormat(plainText)
        clip: true                  // RichText does not elide
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }

    readonly property var bands: Nozzle.regimeBands
    readonly property real current: Nozzle.backPressureRatio

    // The solved rows by key. Selection only -- the rows are the frozen
    // output of nozzle_service._rows_for, formatted by the backend.
    readonly property var rows: {
        var out = {}
        var list = Nozzle.results
        for (var i = 0; i < list.length; ++i)
            out[list[i].key] = list[i]
        return out
    }

    // With a shock inside the diverging section the subject is where it
    // stands; without one, what comes out of the exit. The same choice the
    // Operating point view makes, so the two never disagree about the answer.
    readonly property string heroKey: Nozzle.hasShock ? "shock_area_ratio" : "mach_exit"
    readonly property var readoutKeys: Nozzle.hasShock
        ? ["shock_mach_upstream", "shock_mach_downstream", "shock_stagnation_ratio",
           "shock_x", "mach_exit", "mass_flow"]
        : ["pressure_ratio_exit", "pressure_ratio_exit_over_back", "mass_flow",
           "mach_throat", "velocity_exit", "pressure_exit"]

    function readout(key) {
        var row = page.rows[key]
        return row ? row : null
    }

    // The solved wall and the solved stations, as properties: the drawing
    // follows every solve because the binding re-reads them when the result
    // changes, and reading them solves nothing.
    readonly property var wall: {
        var parts = Nozzle.contour
        for (var i = 0; i < parts.length; ++i)
            if (parts[i].label === "wall")
                return parts[i].points
        return []
    }

    readonly property var stationNotes: {
        var notes = {}
        var throat = page.readout("mach_throat")
        if (throat)
            notes["throat"] = "M_t " + throat.value
        var shock = page.readout("shock_area_ratio")
        if (shock)
            notes["shock"] = "A_s/A_t " + shock.value
        return notes
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: page.compact ? Metrics.spacing.m : Metrics.spacing.l

        // =================================================================
        // THE NOZZLE — the object, and the state it is in
        // =================================================================
        // Below 2560 the nozzle takes every row the map does not need. At
        // 2560 it stops at about five eighths of the workspace height -- a
        // proportion of this view, not a pixel cap -- and the rest goes to
        // the map and a readable shock-position chart: more analytical area,
        // not a larger illustration.
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: !page.roomy
            Layout.preferredHeight: page.roomy ? Math.round(page.height * 0.62) : -1
            spacing: page.compact ? Metrics.spacing.m : Metrics.spacing.xl

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.spacing.s

                // The operating point is in the field below; at the 1366
                // floor this line is what yields to the drawing.
                RowLayout {
                    Layout.fillWidth: true
                    visible: !page.compact
                    spacing: Metrics.spacing.s

                    RFSectionLabel { text: "Nozzle" }
                    Text {
                        readonly property string plainText: "operating at  p_b/p₀ = "
                              + Nozzle.backPressureRatio.toFixed(6)
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        color: Theme.textMuted
                        font.family: Typography.mono
                        font.pixelSize: Typography.meta
                    }
                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: Nozzle.valid
                    spacing: Metrics.spacing.l

                    NozzleObject {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 200
                        hasResult: Nozzle.valid
                        wall: page.wall
                        stations: Nozzle.stationMarkers
                        annotations: page.stationNotes
                        labelSize: page.compact ? Typography.chartAnnotation
                                                : Typography.axisTitle
                    }

                    // The 1366 floor: the chart of the station the drawing
                    // marks, beside it, whole -- axes and caption included.
                    ColumnLayout {
                        Layout.preferredWidth: 320
                        Layout.maximumWidth: 320
                        Layout.alignment: Qt.AlignVCenter
                        visible: page.compact
                        spacing: Metrics.spacing.xs

                        RFSectionLabel { text: "Shock station against back pressure" }

                        ShockCurveChart {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 210
                        }

                        ShockCurveCaption { Layout.fillWidth: true }
                    }
                }

                // No solution, no drawing: the reason instead, in the
                // backend's own words.
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: !Nozzle.valid

                    Text {
                        anchors.centerIn: parent
                        width: Math.min(parent.width, 560)
                        readonly property string plainText: Nozzle.statusMessage
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        color: Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.body
                    }
                }
            }

            RFDivider {
                Layout.fillHeight: true
                Layout.preferredWidth: Metrics.hairline
                vertical: true
            }

            // ---- the state it is in --------------------------------------
            Flickable {
                id: stateRail
                Layout.preferredWidth: page.compact ? 330 : (page.roomy ? 520 : 440)
                Layout.minimumWidth: page.compact ? 330 : (page.roomy ? 520 : 440)
                Layout.maximumWidth: page.compact ? 330 : (page.roomy ? 520 : 440)
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: stateColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {
                    policy: stateRail.contentHeight > stateRail.height
                            ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
                }

                ColumnLayout {
                    id: stateColumn
                    width: stateRail.width - (stateRail.contentHeight > stateRail.height ? 10 : 0)
                    // At least the rail's height, so the chart at the end can
                    // take whatever the readouts leave; taller only when the
                    // rail must scroll (the 1366 floor).
                    height: Math.max(stateRail.height, implicitHeight)
                    spacing: page.compact ? Metrics.spacing.s : Metrics.spacing.m

                    // The regime's tone is carried by the page header's chip;
                    // here it is the headline, once.
                    RFSectionLabel { text: "Regime" }

                    Text {
                        Layout.fillWidth: true
                        visible: Nozzle.valid
                        text: Nozzle.regimeLabel
                        color: Theme.text
                        font.family: Typography.sans
                        font.pixelSize: page.compact ? Typography.readoutMedium
                                                     : Typography.readoutLarge
                        font.weight: Typography.medium
                        wrapMode: Text.WordWrap
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: Nozzle.valid
                        readonly property string plainText: Nozzle.regimeNote
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }

                    // Only where a jet actually needs adjusting outside the exit.
                    Text {
                        Layout.fillWidth: true
                        visible: Nozzle.valid && !page.compact && Nozzle.externalContext !== ""
                        text: Nozzle.externalContext
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.xs
                        visible: Nozzle.valid
                    }

                    // Tier 1: the one number this operating point is about.
                    RFResultValue {
                        Layout.fillWidth: true
                        visible: page.readout(page.heroKey) !== null
                        readonly property var row: page.readout(page.heroKey)
                        label: row ? row.label : ""
                        value: row ? row.value : "—"
                        unit: row ? row.unit : ""
                        scale: page.compact ? "large" : "hero"
                    }

                    // Tier 2: what the regime is about, two abreast.
                    GridLayout {
                        Layout.fillWidth: true
                        visible: Nozzle.valid
                        columns: page.compact ? 3 : 2
                        columnSpacing: Metrics.spacing.l
                        rowSpacing: page.compact ? Metrics.spacing.s : Metrics.spacing.m

                        Repeater {
                            model: page.readoutKeys

                            delegate: RFResultValue {
                                id: readoutCell
                                required property string modelData
                                readonly property var row: page.readout(readoutCell.modelData)
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                                visible: row !== null
                                label: row ? row.label : ""
                                value: row ? row.value : "—"
                                unit: row ? row.unit : ""
                                scale: "medium"
                            }
                        }
                    }

                    // A pointer to the tab above; only where the rail has
                    // height to spare for it.
                    Text {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.xs
                        visible: Nozzle.valid && page.roomy
                        text: "Every solved value, the exit state and the shock jump "
                              + "are on Operating point."
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    // ---- supporting evidence: where the shock stands ------
                    // Beside the regime it explains rather than under the
                    // nozzle, so the nozzle keeps the height.
                    RFDivider {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.s
                        visible: page.railChart
                    }

                    RFSectionLabel {
                        visible: page.railChart
                        text: "Shock station against back pressure"
                    }

                    // Fills what the readouts leave. Its floor is low enough
                    // that the rail at 1920 fits without scrolling.
                    ShockCurveChart {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredHeight: 120
                        Layout.minimumHeight: page.railChart ? 120 : 0
                        visible: page.railChart
                    }

                    ShockCurveCaption {
                        Layout.fillWidth: true
                        visible: page.railChart
                    }

                    // Where the chart is elsewhere (beside the nozzle at the
                    // floor, in the map at 2560) the rail's groups keep their
                    // spacing instead of spreading apart.
                    Item {
                        Layout.fillHeight: true
                        visible: !page.railChart
                    }
                }
            }
        }

        RFDivider { Layout.fillWidth: true }

        // =================================================================
        // THE MAP — back pressure and the regimes around the operating point
        // =================================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: page.roomy
            spacing: Metrics.spacing.xl

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: page.roomy
                Layout.preferredWidth: 3
                Layout.alignment: Qt.AlignTop
                spacing: page.compact ? Metrics.spacing.s : Metrics.spacing.m

                RowLayout {
                    Layout.fillWidth: true
                    visible: !page.compact
                    spacing: Metrics.spacing.m

                    RFSectionLabel { text: "Back pressure and regime map" }
                    Text {
                        Layout.fillWidth: true
                        readonly property string plainText: "every edge computed from A_e/A_t and γ; "
                              + "ideal expansion is a point, reached by its preset"
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        elide: Text.ElideRight
                        clip: true
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.l

                    RFBoundNumberField {
                        Layout.preferredWidth: page.compact ? 160 : 200
                        label: "p_b/p₀"
                        value: Nozzle.backPressureRatio
                        digits: 8
                        decimals: 8
                        step: 0.005
                        onValueEdited: function (v) { Nozzle.backPressureRatio = v }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        RFSlider {
                            Layout.fillWidth: true
                            from: 0.001
                            to: 0.999
                            value: Nozzle.backPressureRatio
                            stepSize: 0.001
                            tickCount: 11
                            onMoved: Nozzle.backPressureRatio = value
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: !page.compact
                            text: "The field is authoritative — a slider cannot land on an "
                                  + "exact threshold, and the presets can."
                            elide: Text.ElideRight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }

                    RowLayout {
                        spacing: Metrics.spacing.xs

                        RFButton {
                            text: "Choking onset"
                            variant: "quiet"
                            compact: true
                            onClicked: Nozzle.applyPreset("choking")
                        }
                        RFButton {
                            text: "Shock at exit"
                            variant: "quiet"
                            compact: true
                            onClicked: Nozzle.applyPreset("shock_exit")
                        }
                        RFButton {
                            text: "Ideal expansion"
                            variant: "quiet"
                            compact: true
                            onClicked: Nozzle.applyPreset("ideal")
                        }
                    }
                }

                // The map, across the full width: every band edge a computed
                // critical, and at this width every band carries its name.
                RFBandScale {
                    Layout.fillWidth: true
                    bands: page.bands
                    from: 0
                    to: 1
                    value: page.current
                }

                // The three thresholds, printed as well as drawn, under the band
                // whose edges they are: on one line, or at 2560 one per line,
                // where the map has the height for it.
                GridLayout {
                    Layout.fillWidth: true
                    columns: page.roomy ? 1 : 4
                    columnSpacing: page.compact ? Metrics.spacing.l : Metrics.spacing.xl
                    rowSpacing: Metrics.spacing.s

                    Repeater {
                        model: [
                            { label: "Choking onset   p_b/p₀", value: Nozzle.firstCritical,
                              hint: "throat reaches M = 1" },
                            { label: "Shock at exit   p_b/p₀", value: Nozzle.secondCritical,
                              hint: "the shock stands in the exit plane" },
                            { label: "Ideal expansion  p_b/p₀", value: Nozzle.thirdCritical,
                              hint: "p_e = p_b, no external adjustment" }
                        ]

                        delegate: RowLayout {
                            id: threshold
                            required property var modelData
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.alignment: Qt.AlignBaseline
                                text: Notation.rich(threshold.modelData.label)
                                textFormat: Notation.textFormat(threshold.modelData.label)
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                            Text {
                                Layout.alignment: Qt.AlignBaseline
                                text: threshold.modelData.value.toFixed(8)
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutMedium
                                font.weight: Typography.medium
                            }
                            Text {
                                Layout.alignment: Qt.AlignBaseline
                                visible: !page.compact
                                readonly property string plainText: threshold.modelData.hint
                                text: Notation.rich(plainText)
                                textFormat: Notation.textFormat(plainText)
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }
                    }

                    Item { Layout.fillWidth: true }
                }

                Item { Layout.fillHeight: true; visible: page.roomy }
            }

            RFDivider {
                Layout.fillHeight: true
                Layout.preferredWidth: Metrics.hairline
                vertical: true
                visible: page.roomy
            }

            // At 2560: the shock-position chart, beside the control that
            // moves the operating point along it.
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 2
                visible: page.roomy
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: "Shock station against back pressure" }

                ShockCurveChart {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                ShockCurveCaption { Layout.fillWidth: true }
            }
        }
    }
}
