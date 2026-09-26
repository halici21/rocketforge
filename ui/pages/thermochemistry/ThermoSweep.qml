import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * O/F sweep - how the chamber chemistry changes with mixture ratio.
 *
 * An analysis visualisation, not an optimiser. Nothing on this page reports a
 * best, optimal or recommended O/F, and the peak markers say "maximum in
 * sweep" because that is the only claim the data supports: different
 * quantities peak at different mixture ratios, so there is no single peak to
 * recommend. Choosing between them is a decision layer this phase does not
 * build.
 *
 * The sweep runs on an explicit press, never on a keystroke - forty-one
 * equilibrium solves per character typed would be absurd - and every fixed
 * condition stays on screen beside the charts, because a trend without its
 * conditions is not a result.
 *
 * Composition: the setup in a left drawer whose handle still names the case
 * (O/F range, points, propellants); the four plots as small multiples that
 * fill the view -- rest on one to peek at it, Focus to open it at full size
 * with the analysis-lens tools; the sweep's table in a bottom drawer
 * ("Sweep data · N rows"). A point picked on a plot or in the table is the
 * one sweep selection, and reads in the Inspector from the solved record.
 */
Item {
    id: view

    // The conditions the handle names: the sweep's own case, as listed.
    function fixedValue(label) {
        var list = Thermochemistry.sweepFixedConditions
        for (var i = 0; i < list.length; ++i)
            if (list[i].label === label)
                return list[i].value
        return ""
    }
    readonly property string setupSummary:
        "O/F " + Number(Thermochemistry.sweepStart).toFixed(3) + "–" + Number(Thermochemistry.sweepEnd).toFixed(3)
        + "  ·  " + Thermochemistry.sweepPoints + " points  ·  "
        + view.fixedValue("Fuel") + " / " + view.fixedValue("Oxidiser")

    // Which small multiple is peeking (RFPlotPeek's shared group).
    QtObject { id: peekGroup; property Item current: null }

    function openFocus(title, quantity) {
        focusOverlay.show(title, "Same solved sweep, full size · wheel zoom, Shift-drag lens, Ctrl-click probe",
                          focusChart, { quantity: quantity })
    }
    Component {
        id: focusChart
        ThermoSweepFocus { quantity: focusOverlay.context.quantity }
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- setup drawer ---------------------------------------------------
        RFWorkspaceDrawer {
            id: setupDrawer
            objectName: "sweepSetupDrawer"
            Layout.preferredWidth: setupDrawer.implicitWidth
            Layout.fillHeight: true
            title: "Sweep setup"
            summary: view.setupSummary
            drawerWidth: Math.max(250, Metrics.railWidth - 24)

            ColumnLayout {
                anchors.fill: parent
                spacing: Metrics.spacing.m

                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: width
                    contentHeight: setup.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: RFScrollBar {}

                    ColumnLayout {
                        id: setup
                        width: parent.width
                        spacing: Metrics.spacing.m

                        RFSectionLabel { text: "Varied — O/F" }

                        RFBoundNumberField {
                            Layout.fillWidth: true
                            label: "O/F start"
                            value: Thermochemistry.sweepStart
                            digits: 3
                            decimals: 3
                            step: 0.1
                            onValueEdited: function (v) { Thermochemistry.sweepStart = v }
                        }

                        RFBoundNumberField {
                            Layout.fillWidth: true
                            label: "O/F end"
                            value: Thermochemistry.sweepEnd
                            digits: 3
                            decimals: 3
                            step: 0.1
                            onValueEdited: function (v) { Thermochemistry.sweepEnd = v }
                        }

                        RFBoundNumberField {
                            Layout.fillWidth: true
                            label: "Points"
                            value: Thermochemistry.sweepPoints
                            digits: 0
                            decimals: 0
                            step: 1
                            onValueEdited: function (v) { Thermochemistry.sweepPoints = v }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: Thermochemistry.sweepRangeValid
                                  ? "Step " + Thermochemistry.sweepStep.toFixed(4)
                                    + " · limit " + Thermochemistry.maxSweepPoints + " points"
                                  : Thermochemistry.sweepRangeMessage
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Thermochemistry.sweepRangeValid ? Theme.textMuted : Theme.warning
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        RFDivider {}

                        RFSectionLabel { text: "Held fixed" }

                        Repeater {
                            model: Thermochemistry.sweepFixedConditions

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.preferredWidth: 118
                                    text: Notation.rich(modelData.label)
                                    textFormat: Notation.textFormat(modelData.label)
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.value
                                    wrapMode: Text.WordWrap
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "Set on the Calculator tab. The sweep varies O/F only; every "
                                  + "other condition above is common to all points."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        RFDivider { visible: Thermochemistry.hasSweep }

                        RFSectionLabel {
                            visible: Thermochemistry.hasSweep
                            text: "Species to plot"
                        }

                        RFSegmentedControl {
                            Layout.fillWidth: true
                            visible: Thermochemistry.hasSweep
                            model: ["Mole  X", "Mass  Y"]
                            currentIndex: Thermochemistry.sweepSpeciesBasis === "mole" ? 0 : 1
                            onSelected: function (index) {
                                Thermochemistry.sweepSpeciesBasis = index === 0 ? "mole" : "mass"
                            }
                        }

                        Flow {
                            Layout.fillWidth: true
                            visible: Thermochemistry.hasSweep
                            spacing: Metrics.spacing.xs

                            Repeater {
                                model: Thermochemistry.sweepSpeciesOptions.slice(0, 16)

                                delegate: Rectangle {
                                    required property var modelData

                                    readonly property bool active:
                                        Thermochemistry.sweepSpecies.indexOf(modelData) >= 0

                                    height: Metrics.chipHeight
                                    width: chipText.implicitWidth + Metrics.spacing.m
                                    radius: Metrics.radius.s
                                    color: active ? Theme.accentSubtle : Theme.surfaceSubtle
                                    border.width: Metrics.hairline
                                    border.color: active ? Theme.accent : Theme.divider

                                    Text {
                                        id: chipText
                                        anchors.centerIn: parent
                                        // The label in chemical case; the chip still
                                        // toggles the species by its name.
                                        text: Notation.species(modelData)
                                        textFormat: Notation.speciesFormat(modelData)
                                        color: parent.active ? Theme.text : Theme.textMuted
                                        font.family: Typography.mono
                                        font.pixelSize: Typography.meta
                                    }

                                    HoverHandler { cursorShape: Qt.PointingHandCursor }
                                    TapHandler {
                                        onTapped: Thermochemistry.toggleSweepSpecies(modelData)
                                    }
                                }
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: Thermochemistry.hasSweep
                            text: "A drawing limit, not a data limit — every species stays in the "
                                  + "sweep result whether or not it is plotted."
                            wrapMode: Text.WordWrap
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }

                // Pinned outside the scroll region, for the same reason the
                // Calculator's Calculate button is.
                RFDivider { Layout.fillWidth: true }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    RFButton {
                        Layout.fillWidth: true
                        text: "Run sweep"
                        variant: "primary"
                        enabled: Thermochemistry.sweepRangeValid && !Thermochemistry.busy
                        onClicked: Thermochemistry.runSweep()
                    }
                    RFButton {
                        text: "Clear"
                        variant: "quiet"
                        enabled: Thermochemistry.hasSweep
                        onClicked: Thermochemistry.clearSweep()
                    }
                }
            }
        }

        // ---- results -------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            RFEmptyState {
                Layout.fillWidth: true
                Layout.topMargin: Metrics.spacing.h2
                visible: !Thermochemistry.hasSweep
                tag: "NO SWEEP"
                title: "No sweep run yet"
                body: "Set the O/F range in the setup drawer and press Run sweep. Each point is a "
                      + "separate chamber equilibrium; nothing is drawn until they have "
                      + "been solved."
            }

            Item { Layout.fillHeight: true; visible: !Thermochemistry.hasSweep }

            // ---- summary ----------------------------------------------------
            RowLayout {
                Layout.fillWidth: true
                visible: Thermochemistry.hasSweep
                spacing: Metrics.spacing.s

                RFStatusChip {
                    text: Thermochemistry.sweepSolvedCount + " solved"
                    tone: "success"
                }
                RFStatusChip {
                    visible: Thermochemistry.sweepFailedCount > 0
                    text: Thermochemistry.sweepFailedCount + " no solution"
                    tone: "error"
                }
                RFStatusChip {
                    visible: Thermochemistry.sweepStale
                    text: "Inputs changed"
                    tone: "warning"
                }
                RFStatusChip {
                    text: Thermochemistry.sweepElapsedMs.toFixed(0) + " ms"
                    showDot: false
                }
                Item { Layout.fillWidth: true }
                RFButton {
                    text: "Copy table"
                    variant: "quiet"
                    compact: true
                    onClicked: Thermochemistry.copySweep()
                }
            }

            Text {
                Layout.fillWidth: true
                visible: Thermochemistry.hasSweep && Thermochemistry.sweepStale
                text: "The conditions have changed since this sweep ran. The charts below "
                      + "are for the conditions listed in the setup drawer; run the sweep again to "
                      + "match the current case."
                wrapMode: Text.WordWrap
                color: Theme.warning
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            // ---- aggregated warnings ----------------------------------------
            Repeater {
                model: Thermochemistry.sweepWarnings

                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    RFStatusChip {
                        text: modelData.severity.toUpperCase()
                        tone: modelData.severity === "error" ? "error" : "warning"
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.range_text + " — " + modelData.message
                        wrapMode: Text.WordWrap
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }

            // ---- the overview: four small multiples that fill the view -------
            GridLayout {
                objectName: "sweepOverview"
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: Thermochemistry.hasSweep
                columns: width > 900 ? 2 : 1
                columnSpacing: Metrics.spacing.l
                rowSpacing: Metrics.spacing.l

                ThermoSweepChart {
                    objectName: "sweepChart_temperature"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 180
                    quantity: "temperature"
                    peekGroup: peekGroup
                    onFocusRequested: view.openFocus(title, "temperature")
                }
                ThermoSweepChart {
                    objectName: "sweepChart_molar_mass"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 180
                    quantity: "molar_mass"
                    peekGroup: peekGroup
                    onFocusRequested: view.openFocus(title, "molar_mass")
                }
                ThermoSweepChart {
                    objectName: "sweepChart_gamma"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 180
                    quantity: "gamma"
                    peekGroup: peekGroup
                    onFocusRequested: view.openFocus(title, "gamma")
                }
                ThermoSweepSpeciesChart {
                    objectName: "sweepChart_species"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 180
                    peekGroup: peekGroup
                    onFocusRequested: view.openFocus(title, "species")
                }
            }

            // ---- the sweep's data, in a bottom drawer -------------------------
            RFBottomDrawer {
                id: dataDrawer
                objectName: "sweepDataDrawer"
                Layout.fillWidth: true
                Layout.preferredHeight: dataDrawer.implicitHeight
                visible: Thermochemistry.hasSweep
                title: "Sweep data"
                summary: Thermochemistry.sweepModel.rowCount() >= 0
                         ? (Thermochemistry.sweepSolvedCount + Thermochemistry.sweepFailedCount) + " rows  ·  ascending O/F"
                         : ""
                drawerHeight: Math.max(220, Math.round(view.height * 0.42))

                ColumnLayout {
                    anchors.fill: parent
                    spacing: Metrics.spacing.s

                    RFTableToolbar {
                        Layout.fillWidth: true
                        table: sweepTable
                        canCopy: true
                        onCopyRequested: {
                            var a = sweepTable.hasRange ? sweepTable.rangeFirst
                                  : sweepTable.lensActive ? sweepTable.lensFirst : -1
                            var b = sweepTable.hasRange ? sweepTable.rangeLast
                                  : sweepTable.lensActive ? sweepTable.lensLast : -1
                            if (a < 0) {
                                Thermochemistry.copySweep()
                                return
                            }
                            var lines = [sweepTable.columns.map(function (c) { return c.label }).join("\t")]
                            for (var r = a; r <= b; ++r) {
                                var cells = []
                                for (var c = 0; c < sweepTable.columns.length; ++c)
                                    cells.push(sweepTable.cellText(r, c))
                                lines.push(cells.join("\t"))
                            }
                            AnalysisSession.copyText(lines.join("\n"))
                        }
                    }

                    RFEngineeringTable {
                        id: sweepTable
                        objectName: "sweepTable"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        interactive: true
                        model: Thermochemistry.sweepModel
                        columns: Thermochemistry.sweepColumns
                        firstColumnWidth: 96
                        columnWidth: 128
                        // A point that did not solve is annotated as well
                        // as carrying "no solution" in its Status column.
                        markedRow: Thermochemistry.sweepFailedRows.length > 0
                                   ? Thermochemistry.sweepFailedRows[0] : -1
                        markedLabel: "NO SOLUTION"
                        secondaryRow: Thermochemistry.sweepFailedRows.length > 1
                                      ? Thermochemistry.sweepFailedRows[1] : -1
                        secondaryLabel: "NO SOLUTION"
                        selectedRow: Thermochemistry.sweepSelection.kind === "tableRow"
                                     ? parseInt(Thermochemistry.sweepSelection.key) : -1
                        onRowClicked: function (row) {
                            Thermochemistry.selectSweepPoint(row)
                            ShellContext.inspectorOpen = true
                        }
                        onEscapePressed: Thermochemistry.sweepSelection.clear()
                    }
                }
            }
        }
    }

    // A point picked on a plot brings its row into view when the table is open.
    Connections {
        target: Thermochemistry.sweepSelection
        function onChanged() {
            if (Thermochemistry.sweepSelection.kind === "tableRow" && dataDrawer.open)
                sweepTable.scrollToRow(parseInt(Thermochemistry.sweepSelection.key))
        }
    }

    // ---- focus: one plot at full size, the rest receded behind it ---------
    RFFocusOverlay {
        id: focusOverlay
        objectName: "sweepFocusOverlay"
        anchors.fill: parent
    }
}
