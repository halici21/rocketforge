import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "fluidproperties"

/*
 * Fluid Properties - what a substance is doing at a temperature and a pressure.
 *
 * The fundamental layer beneath everything else in this program: a propellant
 * stream has a density and an enthalpy before it is a reactant, and those are
 * what the reactant-enthalpy correction and the density impulse are built on.
 *
 * The page is deliberately small. It inspects a property model; it does not
 * size a line, a valve or an orifice, and it computes nothing itself -- every
 * number and every string below came from the controller.
 *
 * Three things it insists on, because all three are easy to get wrong:
 *
 *   - Pressure is an input, never a default. The field starts at a value, that
 *     value is visible, and it travels into the request. Oxygen at 95 K is a
 *     liquid at 3 bar and a gas at 1 atm, so a page that supplied a pressure
 *     would be choosing the answer.
 *   - An unavailable property is a row with a reason, not an empty cell. A
 *     blank reads as zero, and a missing viscosity is not 0 Pa s. Every one of
 *     the seven reasons the property vocabulary defines keeps its own exact
 *     wording -- the row dims uniformly, but the reason text is never
 *     shortened to a generic "unavailable".
 *   - This page's specific enthalpy is CoolProp's own value on CoolProp's own
 *     datum. It is not, and is never presented as, NASA CEA's assigned
 *     reactant enthalpy -- the two differ by hundreds of kJ/kg per
 *     REACTANT_ENTHALPY_COUPLING_CONTRACT.md, and the Provenance panel below
 *     says so on every evaluated state, not only on hover.
 */
Item {
    id: page

    // FluidProperties.statusTone returns "positive"/"caution"/"negative"/
    // "neutral" (fluid_property_service.py's FluidOutcome.status_tone), but
    // RFStatusChip only recognizes "success"/"warning"/"error"/"accent"/
    // "neutral" -- both chips on this page silently fell through to the
    // neutral/muted dot regardless of actual state. Presentation-only fix
    // (a string mapping in QML, no Python touched), same as Line's.
    function chipTone(statusTone) {
        switch (statusTone) {
        case "positive": return "success"
        case "caution": return "warning"
        case "negative": return "error"
        default: return "neutral"
        }
    }

    // Density leads: it is the property a feed-system or tank calculation
    // reaches for first at a stated (T, p), and it is the one number that
    // changes the design rather than describing it. The audit captured this
    // page with density and specific enthalpy at the same weight inside a
    // block called "Primary", which names a hierarchy without showing one.
    readonly property var heroLabels: ["Density"]
    readonly property var primaryLabels: ["Specific enthalpy"]
    readonly property var thermodynamicLabels: ["Specific heat, cp"]

    function rowTier(label) {
        if (page.heroLabels.indexOf(label) !== -1) return "hero"
        if (page.primaryLabels.indexOf(label) !== -1) return "primary"
        if (page.thermodynamicLabels.indexOf(label) !== -1) return "thermodynamic"
        return "transport"
    }

    function rowsForTier(tier) {
        if (!FluidProperties.hasResult)
            return []
        return FluidProperties.resultRows.filter(function (r) {
            return page.rowTier(r.label) === tier
        })
    }

    function provenanceValue(label) {
        var rows = FluidProperties.provenanceRows
        for (var i = 0; i < rows.length; ++i)
            if (rows[i].label === label)
                return rows[i].value
        return ""
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Fluid Properties"
            subtitle: "Density, enthalpy, specific heat, viscosity and thermal "
                      + "conductivity at an explicit temperature and pressure"

            trailing: Component {
                RFStatusChip {
                    text: FluidProperties.providerAvailable
                          ? FluidProperties.providerLabel
                          : "Provider unavailable"
                    tone: FluidProperties.providerAvailable ? "success" : "neutral"
                }
            }
        }

        // ---- provider missing --------------------------------------------
        RFEmptyState {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !FluidProperties.providerAvailable
            title: "High-fidelity fluid properties are not installed"
            body: FluidProperties.providerDetail
        }

        // ---- inputs ------------------------------------------------------
        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 108
            visible: FluidProperties.providerAvailable
            title: "State"

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: false
                spacing: Metrics.spacing.m

                RFComboBox {
                    Layout.preferredWidth: 220
                    label: "Fluid"
                    model: FluidProperties.fluidOptions.map(
                               function (o) { return o.label })
                    currentIndex: {
                        var options = FluidProperties.fluidOptions
                        for (var i = 0; i < options.length; ++i)
                            if (options[i].name === FluidProperties.fluidName)
                                return i
                        return 0
                    }
                    onActivated: function (index) {
                        var options = FluidProperties.fluidOptions
                        if (index >= 0 && index < options.length)
                            FluidProperties.setFluid(options[index].name)
                    }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 190
                    label: "Temperature  [K]"
                    value: FluidProperties.temperature
                    digits: 3
                    step: 1
                    onValueEdited: function (v) { FluidProperties.setTemperature(v) }
                }

                RFBoundNumberField {
                    id: pressureField
                    Layout.preferredWidth: 210
                    label: "Pressure  [Pa]"
                    value: FluidProperties.pressure
                    digits: 0
                    step: 10000
                    onValueEdited: function (v) { FluidProperties.setPressure(v) }

                    HoverHandler { id: pressureHover }
                    RFTooltip {
                        visible: pressureHover.hovered
                        text: "This state's own pressure. There is no default: "
                              + "the phase, and therefore every property, "
                              + "depends on it."
                    }
                }

                Item { Layout.fillWidth: true }

                RFButton {
                    text: "Evaluate"
                    variant: "primary"
                    onClicked: FluidProperties.calculate()
                }
            }
        }

        // ---- results -----------------------------------------------------
        // A single (T, p) query has no sweep and no analytical question
        // beyond "what is this state", so this page genuinely has little to
        // show -- and stretching two panels to the full viewport height to
        // hide that produced the ~40% framed void the audit measured. Both
        // panels size to their own content and sit at the top instead: the
        // leftover is honest page background rather than a frame drawn
        // around nothing. The filler below keeps them there.
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.alignment: Qt.AlignTop
            visible: FluidProperties.providerAvailable
            spacing: Metrics.spacing.m

            RFPanel {
                Layout.fillWidth: true
                Layout.fillHeight: false
                Layout.alignment: Qt.AlignTop
                title: "Properties"
                chromeless: true

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: Metrics.spacing.s

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        spacing: Metrics.spacing.s

                        RFStatusChip {
                            text: FluidProperties.statusLabel
                            tone: page.chipTone(FluidProperties.statusTone)
                        }
                        RFStatusChip {
                            visible: FluidProperties.hasResult && FluidProperties.resultStale
                            text: "Stale — recalculate"
                            tone: "warning"
                        }
                        Item { Layout.fillWidth: true }
                    }

                    // ---- the object: the fluid state itself -----------------
                    FluidStateBlock {
                        Layout.fillWidth: true
                        hasResult: FluidProperties.hasResult
                        stale: FluidProperties.resultStale
                        fluidLabel: page.provenanceValue("Fluid")
                        phase: FluidProperties.phase
                        temperatureText: page.provenanceValue("Temperature")
                        pressureText: page.provenanceValue("Pressure")
                    }

                    RFEmptyState {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: !FluidProperties.hasResult
                        title: "No result yet"
                        body: FluidProperties.message !== ""
                              ? FluidProperties.message
                              : "Choose a fluid, a temperature and a pressure, "
                                + "then evaluate."
                    }

                    RFDivider { visible: FluidProperties.hasResult }

                    // Tier 1. Six properties stacked in one 460px-wide
                    // column left roughly 40% of this workspace empty in the
                    // audit capture while the column itself stayed cramped.
                    // The hero leads, and the three supporting groups sit
                    // side by side across the width the page already has.
                    Repeater {
                        model: page.rowsForTier("hero")
                        delegate: PropertyRow {
                            required property var modelData
                            row: modelData
                            tier: "hero"
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: Metrics.spacing.m
                        spacing: Metrics.spacing.xl
                        visible: FluidProperties.hasResult

                        Repeater {
                            model: [
                                { tier: "primary", label: "Primary" },
                                { tier: "thermodynamic", label: "Thermodynamic" },
                                { tier: "transport", label: "Transport" }
                            ]

                            delegate: ColumnLayout {
                                id: tierColumn
                                required property var modelData
                                readonly property var tierRows: page.rowsForTier(modelData.tier)

                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.xs
                                visible: tierRows.length > 0

                                RFSectionLabel { text: tierColumn.modelData.label }

                                Repeater {
                                    model: tierColumn.tierRows
                                    delegate: PropertyRow {
                                        required property var modelData
                                        row: modelData
                                        tier: tierColumn.modelData.tier
                                    }
                                }

                                Item { Layout.fillHeight: true }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            RFPanel {
                Layout.preferredWidth: 380
                Layout.fillHeight: false
                Layout.alignment: Qt.AlignTop
                title: "Provenance"

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: Metrics.spacing.xs

                    Repeater {
                        model: FluidProperties.provenanceRows
                        delegate: RowLayout {
                            id: provenanceRow
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: false
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 140
                                text: provenanceRow.modelData.label
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: provenanceRow.modelData.value
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                                wrapMode: Text.WordWrap
                            }
                        }
                    }

                    // Not a hover-only tooltip: the same always-visible
                    // treatment Line gives its Darcy/Fanning distinction.
                    // This page's enthalpy is CoolProp's own datum, never
                    // NASA CEA's assigned reactant enthalpy -- see
                    // REACTANT_ENTHALPY_COUPLING_CONTRACT.md.
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        visible: FluidProperties.hasResult
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.preferredWidth: 140
                            text: "Enthalpy datum"
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "This provider's own reference state, not "
                                  + "NASA CEA's assigned reactant enthalpy. "
                                  + "The two differ by hundreds of kJ/kg and "
                                  + "are never interchangeable."
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }

                    RFDivider {
                        Layout.fillWidth: true
                        visible: FluidProperties.diagnosticRows.length > 0
                    }

                    Repeater {
                        model: FluidProperties.diagnosticRows
                        delegate: Text {
                            id: diagnosticRow
                            required property var modelData
                            Layout.fillWidth: true
                            text: diagnosticRow.modelData.message
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
