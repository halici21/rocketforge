import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Nozzle calculator.
 *
 * Every number here is computed by the verified backend and handed over
 * already formatted; this file collects inputs, sends them, and lays out what
 * comes back. There is no arithmetic in it — no area-Mach relation, no
 * threshold, no shock search, not even a pressure ratio: the two input modes
 * are converted by the controller, one layer down, where they are tested
 * without Qt.
 *
 * The regime is the headline, because on this page the regime *is* the answer.
 * The shock block exists only while a shock does, so moving the back pressure
 * out of that interval removes it rather than leaving it stranded on screen.
 */
Item {
    id: page

    // TIER 1 is the hero below. TIER 2 (Regime, Flow) and TIER 3 (Exit
    // state, Thresholds) are the four groups here.
    //
    // Roomy: two columns of two groups, which is the approved 1920/2560
    // composition and is unchanged.
    //
    // Compact: the same four groups, side by side. At 1366x768 the Solution
    // panel is 241px tall and the 2x2 arrangement needs ~301px, so Mass flow,
    // Throat Mach, Exit Mach and all four Thresholds were clipped. Laying the
    // groups out in one row halves the stack height and spends the 935px of
    // width the workspace already has. No quantity is removed, nothing is
    // scrolled, and no type size changes.
    readonly property var columns: page.compact
        ? [["Regime"], ["Flow"], ["Exit state"], ["Thresholds"]]
        : [["Regime", "Flow"], ["Exit state", "Thresholds"]]

    // At the 1366x768 floor the object row, the solution grid and the shock
    // strip ask for more height than the workspace has, and a ColumnLayout
    // handed less than its children's minimums lets them overlap rather than
    // shrinking them -- the capture showed the shock strip printed straight
    // across the REGIME and EXIT STATE columns. Reflow, not shrink: the
    // numbers are what this tab is for, and the nozzle is drawn full size on
    // the Charts tab, so the object is what yields.
    readonly property bool compact: page.height < 620

    // ---- result hierarchy ----------------------------------------------
    // The audit captured this page as 22 numbers at one weight, which is the
    // same as no answer at all. The rows are frozen scientific output
    // (nozzle_service._rows_for) and are untouched -- this only decides which
    // of them is read FIRST, and which regime it belongs to.
    //
    // Read straight off the raw rows, never through rowsIn(): rowsIn filters
    // BY heroKey, so asking it would make this depend on itself.
    readonly property bool shockPresent: {
        for (var i = 0; i < Nozzle.results.length; ++i)
            if (Nozzle.results[i].group === "Shock")
                return true
        return false
    }

    // With a shock inside the diverging section the whole subject is where it
    // stands. Without one, nothing is happening inside the nozzle and the
    // answer is what comes out of it.
    readonly property string heroKey:
        page.shockPresent ? "shock_area_ratio" : "mach_exit"

    readonly property var heroRow: {
        for (var i = 0; i < Nozzle.results.length; ++i)
            if (Nozzle.results[i].key === page.heroKey)
                return Nozzle.results[i]
        return null
    }

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < Nozzle.results.length; ++i)
            if (Nozzle.results[i].group === group
                    && Nozzle.results[i].key !== page.heroKey)
                out.push(Nozzle.results[i])
        return out
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- input rail ---------------------------------------------------
        RFPanel {
            title: "Operating point"
            Layout.preferredWidth: Metrics.railWidth - 10
            Layout.minimumWidth: 260
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.m

            RFSectionLabel { text: "Gas" }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Specific heat ratio  γ"
                value: Nozzle.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { Nozzle.gamma = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Gas constant  R   [J/(kg K)]"
                value: Nozzle.gasConstant
                digits: 5
                decimals: 2
                step: 1.0
                onValueEdited: function (v) { Nozzle.gasConstant = v }
            }

            RFDivider {}
            RFSectionLabel { text: "Reservoir" }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Stagnation pressure  p₀   [Pa]"
                value: Nozzle.stagnationPressure
                digits: 9
                decimals: 0
                step: 50000
                onValueEdited: function (v) { Nozzle.stagnationPressure = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Stagnation temperature  T₀   [K]"
                value: Nozzle.stagnationTemperature
                digits: 6
                decimals: 1
                step: 25
                onValueEdited: function (v) { Nozzle.stagnationTemperature = v }
            }

            RFDivider {}
            RFSectionLabel { text: "Nozzle given as" }

            RFSegmentedControl {
                Layout.fillWidth: true
                model: ["<i>A</i><sub>t</sub> & <i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>", "<i>A</i><sub>t</sub> & <i>A</i><sub>e</sub>"]
                currentIndex: Nozzle.areaMode === "ratio" ? 0 : 1
                onSelected: function (index) {
                    Nozzle.areaMode = index === 0 ? "ratio" : "areas"
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Throat area  <i>A</i><sub>t</sub>   [m²]"
                value: Nozzle.throatArea
                digits: 8
                decimals: 5
                step: 0.001
                onValueEdited: function (v) { Nozzle.throatArea = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.areaMode === "ratio"
                label: "Area ratio  <i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>"
                value: Nozzle.areaRatio
                digits: 6
                decimals: 4
                step: 0.1
                onValueEdited: function (v) { Nozzle.areaRatio = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.areaMode === "areas"
                label: "Exit area  <i>A</i><sub>e</sub>   [m²]"
                value: Nozzle.exitArea
                digits: 8
                decimals: 5
                step: 0.001
                onValueEdited: function (v) { Nozzle.exitArea = v }
            }

            RFDivider {}
            RFSectionLabel { text: "Back pressure given as" }

            RFSegmentedControl {
                Layout.fillWidth: true
                model: ["<i>p</i><sub>b</sub>/<i>p</i>₀", "<i>p</i><sub>b</sub>   [Pa]"]
                currentIndex: Nozzle.pressureMode === "ratio" ? 0 : 1
                onSelected: function (index) {
                    Nozzle.pressureMode = index === 0 ? "ratio" : "absolute"
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.pressureMode === "ratio"
                label: "Back pressure  <i>p</i><sub>b</sub>/<i>p</i>₀"
                value: Nozzle.backPressureRatio
                digits: 6
                decimals: 6
                step: 0.01
                onValueEdited: function (v) { Nozzle.backPressureRatio = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.pressureMode === "absolute"
                label: "Back pressure  <i>p</i><sub>b</sub>   [Pa]"
                value: Nozzle.backPressure
                digits: 9
                decimals: 0
                step: 10000
                onValueEdited: function (v) { Nozzle.backPressure = v }
            }

            Text {
                Layout.fillWidth: true
                text: "Switching how the pressure is stated does not move it: the "
                      + "controller converts once, and the nozzle sees the same "
                      + "operating point either way."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Item { Layout.fillHeight: true }

            RFSectionLabel { text: "Model" }

            Text {
                Layout.fillWidth: true
                readonly property string plainText: "Steady · Quasi-one-dimensional · Inviscid · Adiabatic · "
                      + "Isentropic except across an infinitely thin normal shock · "
                      + "Calorically perfect gas: constant γ, constant R. No thrust, "
                      + "no performance coefficients, no plume."
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

        // ---- results ------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            // Drawn to scale this nozzle is short and wide, so the object
            // occupies a modest box however much room it is given -- and a
            // to-scale drawing centred in a 1480px panel is just the dead
            // space this phase removes. The regime sentence and the object it
            // describes share one row: two statements about the same thing.
            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.m

                RFPanel {
                        title: "Flow regime"
                        Layout.fillWidth: true
                        // Only stretches to match the object beside it; alone at
                        // the floor it takes the height its sentence needs.
                        Layout.fillHeight: !page.compact
                        contentSpacing: Metrics.spacing.s

                    trailing: Component {
                        RFStatusChip {
                            text: Nozzle.regimeLabel
                            tone: Nozzle.regimeTone
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: Nozzle.regimeNote
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Nozzle.valid ? Theme.textSecondary : Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }

                    // Only where a jet actually needs adjusting outside the exit.
                    Text {
                        Layout.fillWidth: true
                        visible: Nozzle.externalContext !== ""
                        text: Nozzle.externalContext
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: !Nozzle.valid
                        readonly property string plainText: Nozzle.statusMessage
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        wrapMode: Text.WordWrap
                        color: Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                }

                // The object this workspace computes. The audit's finding on
                // this page was that it analyses a converging-diverging
                // nozzle and an internal shock and never shows either one --
                // 22 numbers and no nozzle. Everything drawn is solver output
                // (contourSeries is r(x) from the station distribution,
                // markers are the throat and shock at their own axial
                // stations), so the drawing claims nothing the module has not
                // computed.
                RFPanel {
                    title: "Nozzle"
                    Layout.preferredWidth: page.compact ? 0 : 420
                    Layout.preferredHeight: page.compact ? 0 : 250
                    visible: Nozzle.valid && !page.compact
                    chromeless: true

                    NozzleObject {
                        id: nozzleObject
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        hasResult: Nozzle.valid
                        wall: {
                            var parts = Nozzle.contourSeries()
                            for (var i = 0; i < parts.length; ++i)
                                if (parts[i].label === "wall")
                                    return parts[i].points
                            return []
                        }
                        stations: Nozzle.markers()
                    }
                }
            }

            RFPanel {
                title: "Solution"
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: Nozzle.valid

                // Tier 1: the one number this operating point exists to
                // produce, at the hero size, above the grid rather than
                // inside it.
                GridLayout {
                    Layout.fillWidth: true
                    Layout.bottomMargin: page.compact ? Metrics.spacing.xs
                                                      : Metrics.spacing.s
                    // Stacked when there is height for it; on one line when
                    // there is not. Either way it leads the panel.
                    columns: page.compact ? 2 : 1
                    columnSpacing: Metrics.spacing.m
                    rowSpacing: 2
                    visible: page.heroRow !== null

                    Text {
                        Layout.alignment: Qt.AlignVCenter
                        text: page.heroRow ? Notation.rich(page.heroRow.label) : ""
                        textFormat: page.heroRow ? Notation.textFormat(page.heroRow.label) : Text.PlainText
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }

                    RowLayout {
                        Layout.alignment: Qt.AlignVCenter
                        spacing: Metrics.spacing.xs

                        Text {
                            text: page.heroRow ? page.heroRow.value : ""
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: page.compact
                                ? Typography.readoutLarge
                                : Typography.readoutHero
                            font.weight: Typography.medium

                            TapHandler {
                                onSingleTapped: Nozzle.copyText(page.heroRow.value)
                            }
                        }

                        Text {
                            Layout.alignment: Qt.AlignBottom
                            Layout.bottomMargin: 5
                            visible: page.heroRow && page.heroRow.unit !== ""
                            text: page.heroRow ? page.heroRow.unit : ""
                            color: Theme.textMuted
                            font.family: Typography.mono
                            font.pixelSize: Typography.readoutSmall
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    spacing: page.compact ? Metrics.spacing.m
                                          : Metrics.spacing.xl

                    Repeater {
                        model: page.columns

                        delegate: ColumnLayout {
                            id: column
                            required property var modelData

                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            spacing: Metrics.spacing.m

                            Repeater {
                                model: column.modelData

                                delegate: ColumnLayout {
                                    id: group
                                    required property var modelData
                                    readonly property var groupRows: page.rowsIn(modelData)

                                    Layout.fillWidth: true
                                    spacing: page.compact ? 0
                                                          : Metrics.spacing.xs
                                    visible: groupRows.length > 0

                                    RFSectionLabel { text: Notation.sectionRich(group.modelData); textFormat: Notation.textFormat(group.modelData) }

                                    Repeater {
                                        model: group.groupRows

                                        delegate: GridLayout {
                                            id: cell

                                            required property var modelData

                                            Layout.fillWidth: true
                                            // Explicit so four groups abreast
                                            // land inside the measured 209px
                                            // of content height rather than
                                            // near it.
                                            Layout.preferredHeight:
                                                page.compact ? 32 : 24
                                            // Side by side when there is room
                                            // for both on one line; stacked
                                            // when there is not.
                                            columns: page.compact ? 1 : 2
                                            columnSpacing: Metrics.spacing.m
                                            rowSpacing: 0

                                            Text {
                                                Layout.preferredWidth:
                                                    page.compact ? -1 : 190
                                                Layout.fillWidth: page.compact
                                                text: Notation.rich(cell.modelData.label)
                                                textFormat: Notation.textFormat(cell.modelData.label)
                                                elide: Text.ElideRight
                                                color: Theme.textSecondary
                                                font.family: Typography.sans
                                                font.pixelSize: page.compact
                                                    ? Typography.inputLabel
                                                    : Typography.body
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: cell.modelData.value
                                                      + (cell.modelData.unit
                                                         ? " " + cell.modelData.unit : "")
                                                color: cell.modelData.available
                                                    ? Theme.text : Theme.textMuted
                                                font.family: Typography.mono
                                                font.pixelSize: cell.modelData.emphasis
                                                    ? Typography.readoutMedium
                                                    : Typography.readoutSmall
                                                font.weight: cell.modelData.emphasis
                                                    ? Typography.medium : Typography.regular

                                                TapHandler {
                                                    onSingleTapped:
                                                        Nozzle.copyText(cell.modelData.value)
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // The shock card exists only while a shock does.
            RFPanel {
                title: "Internal normal shock"
                Layout.fillWidth: true
                visible: Nozzle.hasShock

                trailing: Component {
                    RFStatusChip {
                        text: "Solved"
                        tone: "warning"
                        showDot: false
                    }
                }

                GridLayout {
                    // Four columns need ~250px each to hold a 160px label and
                    // its value; at 1366 the workspace gives about 215, and a
                    // GridLayout cell smaller than its content does not shrink
                    // it -- the capture showed "0.0481882 Upstream M1" and
                    // "0.603072 p2/p1" printed into each other. The column
                    // count comes from the width actually available.
                    Layout.fillWidth: true
                    columns: Math.max(1, Math.min(4, Math.floor(width / 250)))
                    columnSpacing: Metrics.spacing.xl
                    rowSpacing: Metrics.spacing.xs

                    Repeater {
                        model: page.rowsIn("Shock")

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 160
                                Layout.maximumWidth: 160
                                text: Notation.rich(modelData.label)
                                textFormat: Notation.textFormat(modelData.label)
                                elide: Text.ElideRight
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.value
                                      + (modelData.unit ? " " + modelData.unit : "")
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutSmall
                                font.weight: modelData.emphasis ? Typography.medium
                                                                : Typography.regular
                            }
                        }
                    }
                }
            }
        }
    }
}
