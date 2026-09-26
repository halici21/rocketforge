import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"
import "../../components/viewport"

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
 *
 * The object can be drawn as the 2D engineering drawing (default) or in the
 * shared 3D viewport, from the same solved snapshot. The right rail is a
 * compact summary -- regime, the one number it is about, valid or not --
 * and the rest of the operating point reads in the Inspector. The
 * operating-state samples of the solved shock curve can be stepped through:
 * a presentation of what the map already solved, never a new solve.
 */
Item {
    id: page

    // 1366x768 gives this view about 1250x500: the object and the map share
    // that height, and the prose that explains the map yields first.
    readonly property bool compact: width < 1500 || height < 640
    readonly property bool roomy: width > 2200 && height > 1000
    readonly property bool railChart: !page.compact && !page.roomy

    // A station clicked on the drawing is the shared selection: the
    // inspector reads it, and the Charts section marks it.
    NozzleLinks { id: links }

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
        // The solved operating point, while it lies on the curve, and the
        // sample being shown while the samples are stepping.
        markers: {
            var out = []
            var shock = page.readout("shock_area_ratio")
            if (Nozzle.hasShock && shock)
                out.push({ x: Nozzle.backPressureRatio, y: shock.raw, label: "operating point" })
            if (page.playbackOn && page.sample.pb !== undefined)
                out.push({ x: page.sample.pb, y: page.sample.areaRatio,
                           label: "sample " + (page.sample.index + 1) })
            return out
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

    // ---- playback: cached operating-state samples -----------------------
    // Steps through the shock-curve samples the regime map already solved;
    // the operating point, the field and every solved value stay as they
    // are. A presentation, never a solve, and not a time history.
    readonly property var samples: Nozzle.playbackSamples
    readonly property bool playbackOn: Nozzle.playbackIndex >= 0
    readonly property var sample: Nozzle.playbackSample
    property bool playing: false
    function play() {
        if (page.samples.length === 0)
            return
        if (Nozzle.playbackIndex < 0 || Nozzle.playbackIndex >= page.samples.length - 1)
            Nozzle.playbackIndex = 0
        page.playing = true
    }
    function stopPlayback() {
        page.playing = false
        Nozzle.playbackIndex = -1
    }
    Timer {
        id: stepper
        interval: 110
        repeat: true
        running: page.playing
        onTriggered: {
            if (Nozzle.playbackIndex >= page.samples.length - 1) {
                page.playing = false
                return
            }
            Nozzle.playbackIndex = Nozzle.playbackIndex + 1
        }
    }
    // A new map (another nozzle or gas) ends the playback: its samples are
    // of another curve.
    Connections {
        target: Nozzle
        function onShockCurveChanged() { page.playing = false }
    }
    Component.onDestruction: if (Nozzle.playbackIndex >= 0) Nozzle.playbackIndex = -1

    // The 2D drawing's stations: solved, or with the sample's shock.
    readonly property var drawnStations: {
        var list = Nozzle.stationMarkers
        if (!page.playbackOn || page.sample.x === undefined)
            return list
        var out = []
        for (var i = 0; i < list.length; ++i)
            if (list[i].label !== "shock")
                out.push(list[i])
        out.push({ value: page.sample.x, axis: "x", label: "shock" })
        return out
    }
    readonly property var drawnNotes: {
        if (!page.playbackOn || page.sample.areaRatio === undefined)
            return page.stationNotes
        var notes = {}
        var throat = page.readout("mach_throat")
        if (throat)
            notes["throat"] = "M_t " + throat.value
        notes["shock"] = "A_s/A_t " + Number(page.sample.areaRatio).toPrecision(6)
                         + "  ·  sample " + (page.sample.index + 1) + "/" + page.sample.count
        return notes
    }

    // The view the object is drawn in: the engineering drawing (default) or
    // the shared 3D viewport. View state only.
    property string objectView: "2d"

    ColumnLayout {
        anchors.fill: parent
        spacing: page.compact ? Metrics.spacing.m : Metrics.spacing.l

        // =================================================================
        // THE NOZZLE — the object, and the state it is in
        // =================================================================
        // The object takes every row the map does not need; at 2560 it stops
        // at about five eighths of the workspace height and the rest goes to
        // the map and a readable shock-position chart.
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: !page.roomy
            Layout.preferredHeight: page.roomy ? Math.round(page.height * 0.62) : -1
            spacing: page.compact ? Metrics.spacing.m : Metrics.spacing.xl

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.spacing.s

                // The object's own toolbar: what it is operating at, the
                // view it is drawn in, and the sample playback.
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    RFSectionLabel { text: "Nozzle" }
                    RFViewSwitch {
                        id: objectSwitch
                        objectName: "nozzleViewSwitch"
                        implicitWidth: page.compact ? 150 : 230
                        flatLabel: page.compact ? "2D" : "2D engineering"
                        mode: page.objectView
                        onModeRequested: function (mode) { page.objectView = mode }
                    }
                    Text {
                        visible: !page.compact
                        readonly property string plainText: "operating at  p_b/p₀ = "
                              + Nozzle.backPressureRatio.toFixed(6)
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        color: Theme.textMuted
                        font.family: Typography.mono
                        font.pixelSize: Typography.meta
                    }
                    Item { Layout.fillWidth: true }

                    // Playback of the solved shock curve's samples.
                    Row {
                        objectName: "nozzlePlayback"
                        visible: Nozzle.valid && page.samples.length > 0
                        spacing: Metrics.spacing.xs

                        RFToolButton {
                            objectName: "nozzlePlaybackPlay"
                            text: page.playing ? "Pause" : (page.playbackOn ? "Resume" : "Step samples")
                            tooltip: "Step through the operating-state samples of the solved shock "
                                     + "curve: where the shock stands at other back pressures. "
                                     + "Nothing is solved; the operating point is unchanged."
                            checked: page.playing
                            onClicked: page.playing ? (page.playing = false) : page.play()
                        }
                        RFSlider {
                            objectName: "nozzlePlaybackScrub"
                            visible: page.playbackOn
                            width: page.compact ? 120 : 180
                            anchors.verticalCenter: parent.verticalCenter
                            from: 0
                            to: Math.max(1, page.samples.length - 1)
                            stepSize: 1
                            value: Math.max(0, Nozzle.playbackIndex)
                            onMoved: { page.playing = false; Nozzle.playbackIndex = Math.round(value) }
                        }
                        RFToolButton {
                            visible: page.playbackOn
                            text: "Operating point"
                            tooltip: "Back to the solved operating point"
                            onClicked: page.stopPlayback()
                        }
                    }
                }

                // While samples are shown, say so -- in words, above the object.
                Text {
                    Layout.fillWidth: true
                    visible: page.playbackOn
                    readonly property string plainText: page.playbackOn && page.sample.pb !== undefined
                          ? "Sample " + (page.sample.index + 1) + " of " + page.sample.count
                            + "  ·  p_b/p₀ " + Number(page.sample.pb).toFixed(6)
                            + "  ·  A_s/A_t " + Number(page.sample.areaRatio).toPrecision(6)
                            + "  —  a cached operating state of the solved shock curve, not a new solve; "
                            + "the operating point (p_b/p₀ " + Nozzle.backPressureRatio.toFixed(6) + ") is unchanged"
                          : ""
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    elide: Text.ElideRight
                    clip: true
                    color: Theme.accent
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
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
                        visible: !objectSwitch.show3D
                        selectedKey: links.highlightStation
                        onStationClicked: function (key, x) { links.selectStation(key, "drawing") }
                        hasResult: Nozzle.valid
                        wall: page.wall
                        stations: page.drawnStations
                        annotations: page.drawnNotes
                        labelSize: page.compact ? Typography.chartAnnotation
                                                : Typography.axisTitle
                    }

                    Nozzle3DView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 200
                        visible: objectSwitch.show3D
                        active: objectSwitch.show3D
                        selectedKey: links.highlightStation
                        onStationPicked: function (key) { links.selectStation(key, "viewport") }
                        onCleared: links.clear()
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

            // ---- the state it is in: a compact summary ---------------------
            // The regime, the one number it is about, and whether it is
            // valid. Everything else the rail used to carry -- the regime's
            // explanation, the external context, the six readouts -- is the
            // Inspector's operating-point reading (open it, or select nothing).
            ColumnLayout {
                id: summary
                objectName: "nozzleStateSummary"
                Layout.preferredWidth: page.compact ? 280 : (page.roomy ? 440 : 340)
                Layout.maximumWidth: page.compact ? 280 : (page.roomy ? 440 : 340)
                Layout.fillHeight: true
                spacing: page.compact ? Metrics.spacing.s : Metrics.spacing.m

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s
                    RFSectionLabel { text: "Regime" }
                    Item { Layout.fillWidth: true }
                    // Valid or not (the nozzle is solved live, so it is never
                    // stale); a model warning is counted here, never hidden.
                    RFStatusChip {
                        objectName: "nozzleStateStatus"
                        text: Nozzle.valid ? "Valid" : "No solution"
                        tone: Nozzle.valid ? "success" : "warning"
                    }
                    RFStatusChip {
                        readonly property int warnings: Nozzle.diagnostics.filter(function (d) {
                            return d.severity === "warning" }).length
                        visible: warnings > 0
                        text: warnings + (warnings === 1 ? " model warning" : " model warnings")
                        tone: "warning"
                    }
                }

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

                // Tier 1: the one number this operating point is about -- the
                // solved one, also while samples are stepping.
                RFResultValue {
                    objectName: "nozzleHeroValue"
                    Layout.fillWidth: true
                    visible: page.readout(page.heroKey) !== null
                    readonly property var row: page.readout(page.heroKey)
                    label: row ? row.label + (page.playbackOn ? "  ·  operating point" : "") : ""
                    value: row ? row.value : "—"
                    unit: row ? row.unit : ""
                    scale: page.compact ? "large" : "hero"
                }

                RFToolButton {
                    objectName: "nozzleOpenInspector"
                    visible: Nozzle.valid
                    text: ShellContext.inspectorOpen ? "Details in the Inspector  ›" : "Show details  ›"
                    tooltip: "The regime's explanation, the external context and every readout "
                             + "of this operating point, in the Inspector"
                    checked: ShellContext.inspectorOpen
                    onClicked: ShellContext.inspectorOpen = !ShellContext.inspectorOpen
                }

                // ---- supporting evidence: where the shock stands ----------
                RFDivider {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
                    visible: page.railChart
                }

                RFSectionLabel {
                    visible: page.railChart
                    text: "Shock station against back pressure"
                }

                ShockCurveChart {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 160
                    Layout.minimumHeight: page.railChart ? 140 : 0
                    visible: page.railChart
                }

                ShockCurveCaption {
                    Layout.fillWidth: true
                    visible: page.railChart
                }

                Item {
                    Layout.fillHeight: true
                    visible: !page.railChart
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
                // While samples step, the marker follows the sample shown (the
                // line above the object says so); otherwise the operating point.
                RFBandScale {
                    Layout.fillWidth: true
                    bands: page.bands
                    from: 0
                    to: 1
                    value: page.playbackOn && page.sample.pb !== undefined ? page.sample.pb : page.current
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
