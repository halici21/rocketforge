import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Thermochemistry calculator.
 *
 * Answers one question: at this operating point, what ideal HP-equilibrium
 * chamber state does the selected provider predict? It does not answer "how
 * good is this engine" - there is no c*, no Cf, no Isp and no thrust here,
 * because RocketForge owns none of them yet.
 *
 * Every number on this page is computed by the provider, mapped by the
 * application layer and handed over already formatted. There is no arithmetic
 * in this file: not a unit conversion, not a ratio, not a gamma.
 *
 * Three things this page is careful about, all of them the difference between
 * an honest chemistry result and a misleading one:
 *
 *   - the chamber temperature carries its model on the same line;
 *   - the assigned-enthalpy warning is on the result, not in a log;
 *   - editing an input marks the displayed result stale rather than relabelling
 *     it with conditions that did not produce it.
 */
Item {
    id: view

    function indexOfKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key)
                return i
        return 0
    }

    // The provider's own name for a reactant, and the range it declares for
    // it. Detail rather than primary workflow: the user picks "LOX", and reads
    // here that NASA CEA calls it O2(L) and will accept 80.17 to 100.17 K.
    function reactantNote(providerName, rangeText) {
        var parts = []
        if (providerName !== "")
            parts.push("Provider reactant " + providerName)
        if (rangeText !== "")
            parts.push("valid " + rangeText)
        return parts.join(" · ")
    }

    // Reads the SOLVED case's own condition snapshot (Thermochemistry.
    // resultConditions, notify=resultChanged) -- never the live input form --
    // so the schematic's annotations can never relabel an unsolved edit as
    // though it were the result. Pure presentation lookup, not physics.
    function conditionValue(label) {
        var rows = Thermochemistry.resultConditions
        for (var i = 0; i < rows.length; ++i)
            if (rows[i].label === label)
                return rows[i].value
        return ""
    }

    // The emphasized primary rows (temperature, molar_mass, gamma) get a
    // tiered hero display above; everything else stays in the grid below.
    // Filtering by key, not removing them from the controller's own model.
    function isHeroRow(key) {
        return key === "temperature" || key === "molar_mass" || key === "gamma"
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- input rail ---------------------------------------------------
        RFPanel {
            Layout.preferredWidth: Metrics.railWidth
            Layout.minimumWidth: 268
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.m
            title: "Case"

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: inputs.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: inputs
                    width: parent.width
                    spacing: Metrics.spacing.m

                    // Which kind of propellant is in the chamber. Both modes
                    // answer the same question -- the equilibrium state of the
                    // chamber -- so they share every result surface below and
                    // differ only in what goes in.
                    RFComboBox {
                        Layout.fillWidth: true
                        label: "Propellant"
                        model: ["Bipropellant", "Solid"]
                        currentIndex: Thermochemistry.isSolid ? 1 : 0
                        onCurrentIndexChanged: {
                            Thermochemistry.formulationKind =
                                currentIndex === 1 ? "solid" : "bipropellant"
                        }
                    }

                    RFDivider {}

                    RFSectionLabel {
                        text: "Reactants"
                        visible: !Thermochemistry.isSolid
                    }

                    // Substance and its actual stream temperature on one line.
                    // The temperature is never hidden -- not even for a reactant
                    // whose temperature the provider will ignore, because the
                    // user has to be able to set it and see what happened to it.
                    RowLayout {
                        visible: !Thermochemistry.isSolid
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        RFComboBox {
                            id: oxidiserBox
                            Layout.fillWidth: true
                            label: "Oxidiser"
                            model: Thermochemistry.oxidiserOptions.map(function (o) { return o.label })
                            currentIndex: view.indexOfKey(Thermochemistry.oxidiserOptions,
                                                          Thermochemistry.oxidiser)
                            onCurrentIndexChanged: {
                                var options = Thermochemistry.oxidiserOptions
                                if (currentIndex >= 0 && currentIndex < options.length)
                                    Thermochemistry.oxidiser = options[currentIndex].key
                            }
                        }

                        RFBoundNumberField {
                            Layout.preferredWidth: 104
                            label: "T  [K]"
                            value: Thermochemistry.oxidiserTemperature
                            digits: 3
                            decimals: 3
                            step: 1
                            showSteppers: false
                            onValueEdited: function (v) { Thermochemistry.oxidiserTemperature = v }
                        }
                    }

                    Text {
                        visible: !Thermochemistry.isSolid
                        Layout.fillWidth: true
                        text: view.reactantNote(Thermochemistry.oxidiserProviderName,
                                                Thermochemistry.oxidiserRangeText)
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RowLayout {
                        visible: !Thermochemistry.isSolid
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        RFComboBox {
                            id: fuelBox
                            Layout.fillWidth: true
                            label: "Fuel"
                            model: Thermochemistry.fuelOptions.map(function (o) { return o.label })
                            currentIndex: view.indexOfKey(Thermochemistry.fuelOptions,
                                                          Thermochemistry.fuel)
                            onCurrentIndexChanged: {
                                var options = Thermochemistry.fuelOptions
                                if (currentIndex >= 0 && currentIndex < options.length)
                                    Thermochemistry.fuel = options[currentIndex].key
                            }
                        }

                        RFBoundNumberField {
                            Layout.preferredWidth: 104
                            label: "T  [K]"
                            value: Thermochemistry.fuelTemperature
                            digits: 3
                            decimals: 3
                            step: 1
                            showSteppers: false
                            onValueEdited: function (v) { Thermochemistry.fuelTemperature = v }
                        }
                    }

                    Text {
                        visible: !Thermochemistry.isSolid
                        Layout.fillWidth: true
                        text: view.reactantNote(Thermochemistry.fuelProviderName,
                                                Thermochemistry.fuelRangeText)
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFDivider { visible: !Thermochemistry.isSolid }

                    // ---- solid formulation ----------------------------
                    //
                    // Mass percent is what a propellant chemist writes, so it
                    // is what the editor shows. The division by 100 happens
                    // once, at the controller boundary; no percent reaches a
                    // solver.

                    RFSectionLabel {
                        text: "Formulation"
                        visible: Thermochemistry.isSolid
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: Thermochemistry.isSolid
                        spacing: Metrics.spacing.xs

                        Text {
                            Layout.fillWidth: true
                            text: Thermochemistry.solidFormulationLabel
                            wrapMode: Text.WordWrap
                            color: Theme.text
                            font.family: Typography.sans
                            font.pixelSize: Typography.body
                        }

                        // A validation case and a design starting point are
                        // different things, and a reader who mistakes one for
                        // the other will draw the wrong conclusion from
                        // editing it. So the reference is stated, not implied.
                        Text {
                            Layout.fillWidth: true
                            visible: Thermochemistry.solidReferenceNote !== ""
                            text: Thermochemistry.solidReferenceNote
                            wrapMode: Text.WordWrap
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }

                    // The grain, as editable mass percents. Editing one row
                    // does not rescale the others -- that would silently change
                    // inputs the user did not touch. The running total is shown
                    // instead, and a grain that does not close refuses to solve.
                    Repeater {
                        model: Thermochemistry.isSolid
                               ? Thermochemistry.solidIngredients : []

                        delegate: RowLayout {
                            id: ingredientRow

                            required property var modelData

                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0

                                Text {
                                    Layout.fillWidth: true
                                    text: ingredientRow.modelData.name
                                    elide: Text.ElideRight
                                    color: Theme.text
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.meta
                                }

                                // Where the thermochemistry comes from: a
                                // thermo.lib record, or a custom definition
                                // carried verbatim from its source.
                                Text {
                                    Layout.fillWidth: true
                                    text: ingredientRow.modelData.representation
                                    elide: Text.ElideRight
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }

                                // The temperature CEA is given for this
                                // reactant -- and, for an assigned-enthalpy
                                // reactant, the one it actually uses. Stated in
                                // words, not only by colour.
                                Text {
                                    Layout.fillWidth: true
                                    text: ingredientRow.modelData.temperatureIgnored
                                          ? "T " + ingredientRow.modelData.temperatureText
                                            + " · held at "
                                            + ingredientRow.modelData.assignedTemperatureText
                                          : "T " + ingredientRow.modelData.temperatureText
                                    wrapMode: Text.WordWrap
                                    color: ingredientRow.modelData.temperatureIgnored
                                           ? Theme.warning : Theme.textMuted
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.meta
                                }
                            }

                            RFBoundNumberField {
                                Layout.preferredWidth: 92
                                label: "mass %"
                                value: ingredientRow.modelData.percent
                                digits: 3
                                decimals: 3
                                step: 0.1
                                onValueEdited: function (v) {
                                    Thermochemistry.setSolidMassPercent(
                                        ingredientRow.modelData.index, v)
                                }
                            }

                            RFIconButton {
                                Layout.alignment: Qt.AlignBottom
                                icon: "close"
                                iconSize: 12
                                tooltip: "Remove " + ingredientRow.modelData.name
                                enabled: Thermochemistry.solidIngredients.length > 1
                                onClicked: Thermochemistry.removeSolidIngredient(
                                               ingredientRow.modelData.index)
                            }
                        }
                    }

                    // Add an ingredient from what this build can actually
                    // model: thermo.lib records it holds, and sourced custom
                    // definitions. Added at 0 %, so the total never moves by
                    // itself.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: Thermochemistry.isSolid
                                 && Thermochemistry.solidAddableIngredients.length > 0
                        spacing: Metrics.spacing.s

                        RFComboBox {
                            id: addBox
                            Layout.fillWidth: true
                            label: "Add ingredient"
                            model: Thermochemistry.solidAddableIngredients.map(
                                       function (o) { return o.label })
                        }

                        RFIconButton {
                            Layout.alignment: Qt.AlignBottom
                            icon: "plus"
                            tooltip: "Add at 0 %"
                            onClicked: {
                                var options = Thermochemistry.solidAddableIngredients
                                if (addBox.currentIndex >= 0
                                        && addBox.currentIndex < options.length)
                                    Thermochemistry.addSolidIngredient(
                                        options[addBox.currentIndex].key)
                            }
                        }
                    }

                    // Total mass, always visible. An unbalanced grain is
                    // refused rather than normalised, so the number that
                    // decides that is not hidden behind a validation message.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: Thermochemistry.isSolid
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.fillWidth: true
                            text: "Total mass"
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        Text {
                            text: Thermochemistry.solidMassTotalText
                            color: Thermochemistry.solidMassBalanced
                                   ? Theme.text : Theme.warning
                            font.family: Typography.mono
                            font.pixelSize: Typography.body
                        }
                    }

                    // Colour is never the only carrier: the state is spelled
                    // out in words as well.
                    Text {
                        Layout.fillWidth: true
                        visible: Thermochemistry.isSolid
                                 && !Thermochemistry.solidMassBalanced
                        text: "Does not close at 100 %. Refused rather than "
                              + "normalised: a grain that does not sum to one "
                              + "is more often a missing ingredient than a "
                              + "deliberate basis."
                        wrapMode: Text.WordWrap
                        color: Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RFButton {
                        Layout.alignment: Qt.AlignLeft
                        visible: Thermochemistry.isSolid
                                 && Thermochemistry.solidEdited
                        text: "Restore published composition"
                        variant: "quiet"
                        onClicked: Thermochemistry.resetSolidFormulation()
                    }

                    RFDivider { visible: Thermochemistry.isSolid }

                    RFSectionLabel { text: "Operating conditions" }

                    RFBoundNumberField {
                        id: ofField
                        visible: !Thermochemistry.isSolid
                        Layout.fillWidth: true
                        label: "Mixture ratio  O/F"
                        value: Thermochemistry.mixtureRatio
                        digits: 4
                        decimals: 4
                        step: 0.05
                        onValueEdited: function (v) { Thermochemistry.mixtureRatio = v }

                        HoverHandler { id: ofHover }
                        RFTooltip {
                            visible: ofHover.hovered
                            text: "Oxidiser mass divided by fuel mass."
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        // One field, both modes. The unit selector beside it
                        // is shared too, so a pressure unit chosen in one mode
                        // still means the same thing in the other.
                        RFBoundNumberField {
                            Layout.fillWidth: true
                            label: "Chamber pressure  p_c"
                            value: Thermochemistry.isSolid
                                   ? Thermochemistry.solidChamberPressureDisplay
                                   : Thermochemistry.chamberPressureDisplay
                            digits: Thermochemistry.pressureUnitInfo.decimals
                            decimals: Thermochemistry.pressureUnitInfo.decimals
                            step: Thermochemistry.pressureUnitInfo.step
                            onValueEdited: function (v) {
                                if (Thermochemistry.isSolid)
                                    Thermochemistry.solidChamberPressureDisplay = v
                                else
                                    Thermochemistry.chamberPressureDisplay = v
                            }
                        }

                        RFComboBox {
                            Layout.preferredWidth: 84
                            label: "Unit"
                            model: Thermochemistry.pressureUnits.map(function (u) { return u.label })
                            currentIndex: view.indexOfKey(Thermochemistry.pressureUnits,
                                                          Thermochemistry.pressureUnit)
                            onCurrentIndexChanged: {
                                var units = Thermochemistry.pressureUnits
                                if (currentIndex >= 0 && currentIndex < units.length)
                                    Thermochemistry.pressureUnit = units[currentIndex].key
                            }
                        }
                    }

                    // The grain's bulk temperature before ignition, which
                    // sets the reactant enthalpy the chamber balance starts
                    // from. Not hidden at a default 298 K: a conditioned motor
                    // is a different case and the user has to be able to say so.
                    RFBoundNumberField {
                        Layout.fillWidth: true
                        visible: Thermochemistry.isSolid
                        label: "Grain temperature  T_grain"
                        value: Thermochemistry.solidGrainTemperature
                        digits: 4
                        decimals: 2
                        step: 5.0
                        onValueEdited: function (v) {
                            Thermochemistry.solidGrainTemperature = v
                        }
                    }

                    RFDivider {}

                    RFSectionLabel { text: "Model" }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xs

                        Repeater {
                            model: [
                                { label: "Provider", value: Thermochemistry.providerHeadline },
                                { label: "Constraint", value: Thermochemistry.constraintLabel },
                                { label: "Chemistry", value: Thermochemistry.chemistryMode },
                                { label: "Heat loss", value: "Adiabatic — none, in this ideal model" }
                            ]

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.preferredWidth: 76
                                    text: modelData.label
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
                    }

                }
            }

            // The primary action is pinned outside the scroll region. At
            // 1366x768 the input column is taller than the panel, and a
            // Calculate button that has to be scrolled to is a clipped primary
            // action.
            RFDivider { Layout.fillWidth: true }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.s

                RFButton {
                    Layout.fillWidth: true
                    text: "Calculate"
                    variant: "primary"
                    enabled: !Thermochemistry.busy
                    onClicked: Thermochemistry.calculate()
                }

                RFButton {
                    id: resetButton
                    text: "Reset"
                    variant: "quiet"
                    onClicked: Thermochemistry.resetInputs()

                    HoverHandler { id: resetHover }
                    RFTooltip {
                        visible: resetHover.hovered
                        text: "Restores the validated demonstration case — the operating "
                              + "point Phase 5C checked end to end. An example, not a "
                              + "recommended design."
                    }
                }
            }
        }

        // ---- results --------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            RFPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "Chamber state"
                chromeless: true
                contentSpacing: Metrics.spacing.m

                trailing: Component {
                    Row {
                        spacing: Metrics.spacing.s

                        RFStatusChip {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: Thermochemistry.resultStale
                            text: "Inputs changed"
                            tone: "warning"
                        }
                        RFStatusChip {
                            anchors.verticalCenter: parent.verticalCenter
                            text: Thermochemistry.statusLabel
                            tone: Thermochemistry.statusTone
                        }
                    }
                }

                // ---- nothing calculated yet ------------------------------
                //
                // Analysis Experience R2, section 37: the unsolved state is
                // not a void with a sentence in it. ThermoChamberSchematic
                // already renders an honest, dimmed, unannotated structure
                // when hasResult is false -- it was simply never shown,
                // because the whole result column was gated behind
                // hasResult. It is shown here instead, so the workspace
                // reads as an instrument waiting for an input. No solved
                // value is invented: every annotation inside the schematic
                // stays hidden until there is a real result to annotate.
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: Thermochemistry.statusKind === "empty"
                    spacing: Metrics.spacing.l

                    ThermoChamberSchematic {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 210
                        Layout.minimumHeight: 150
                        Layout.topMargin: Metrics.spacing.l
                        hasResult: false
                        stale: false
                        // The unsolved outline must not claim a feed topology
                        // either: a grain is one charge, not two streams.
                        singleStream: Thermochemistry.isSolid
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: Metrics.spacing.xl
                        spacing: Metrics.spacing.xs

                        Text {
                            text: "Not solved yet"
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.body + 1
                            font.weight: Typography.medium
                        }

                        Text {
                            Layout.fillWidth: true
                            Layout.maximumWidth: 560
                            text: "The chamber above is the structure this workspace solves, "
                                  + "not a result. Set the reactants and operating conditions, "
                                  + "then press Calculate."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                    }

                    Item { Layout.fillHeight: true }
                }

                // ---- a refusal, with no numbers --------------------------
                ColumnLayout {
                    Layout.fillWidth: true
                    visible: Thermochemistry.statusKind !== "empty" && !Thermochemistry.hasResult
                    spacing: Metrics.spacing.s

                    RFDashedFrame {
                        Layout.fillWidth: true
                        Layout.preferredHeight: refusal.implicitHeight + Metrics.spacing.xl * 2

                        ColumnLayout {
                            id: refusal
                            anchors.centerIn: parent
                            width: parent.width - Metrics.spacing.xl * 2
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                text: Thermochemistry.statusLabel
                                horizontalAlignment: Text.AlignHCenter
                                color: Theme.warning
                                font.family: Typography.sans
                                font.pixelSize: Typography.groupLabel + 2
                                font.weight: Typography.medium
                            }

                            Text {
                                Layout.fillWidth: true
                                text: Thermochemistry.statusMessage
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                                lineHeight: Typography.proseLineHeight
                                lineHeightMode: Text.ProportionalHeight
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }

                            Text {
                                Layout.fillWidth: true
                                visible: Thermochemistry.statusField !== ""
                                text: "Concerns: " + Thermochemistry.statusField
                                horizontalAlignment: Text.AlignHCenter
                                color: Theme.textMuted
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                            }
                        }
                    }
                }

                // ---- a result --------------------------------------------
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: Thermochemistry.hasResult
                    spacing: Metrics.spacing.m

                    // ---- the object: reactants -> equilibrium chamber -> products
                    ThermoChamberSchematic {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 210
                        Layout.minimumHeight: 150
                        hasResult: Thermochemistry.hasResult
                        stale: Thermochemistry.resultStale
                        singleStream: Thermochemistry.isSolid
                        streamLabel: Thermochemistry.isSolid
                                     ? view.conditionValue("Formulation") : ""
                        oxidiserLabel: view.conditionValue("Oxidiser")
                        fuelLabel: view.conditionValue("Fuel")
                        // No O/F for a solid: CEA reports 0.000, and the
                        // absence of a ratio is the honest representation.
                        ofText: Thermochemistry.isSolid
                                ? "" : "O/F " + view.conditionValue("O/F")
                        chamberPressureText: "p_c " + view.conditionValue("Chamber pressure")
                        productsSummary: Thermochemistry.condensed.headline
                    }

                    // ---- the primary hero: Tc, then the two secondary
                    // emphasized quantities (mean molar mass, gamma) -- the
                    // same three rows the controller already marks
                    // `emphasis: true`, given an actual size tier instead of
                    // three equally-large numbers with no single lead.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xl

                        Repeater {
                            model: Thermochemistry.resultRows.filter(
                                       function (r) { return view.isHeroRow(r.key) })

                            delegate: RFResultValue {
                                required property var modelData
                                label: modelData.label
                                value: modelData.value
                                unit: modelData.unit
                                scale: modelData.key === "temperature" ? "hero" : "medium"
                                highlighted: modelData.key === "temperature"

                                HoverHandler { id: heroHover }
                                RFTooltip {
                                    visible: heroHover.hovered && modelData.help !== ""
                                    text: modelData.help
                                }
                            }
                        }

                        Item { Layout.fillWidth: true }
                    }

                    RFDivider {}

                    ThermoResultHeader { Layout.fillWidth: true }

                    ThermoWarnings { Layout.fillWidth: true }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: width
                        contentHeight: readouts.implicitHeight
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: RFScrollBar {}

                        ColumnLayout {
                            id: readouts
                            width: parent.width
                            spacing: Metrics.spacing.l

                            GridLayout {
                                Layout.fillWidth: true
                                columns: Math.max(2, Math.floor(width / 220))
                                columnSpacing: Metrics.spacing.xl
                                rowSpacing: Metrics.spacing.l

                                Repeater {
                                    // The three hero rows (temperature,
                                    // molar_mass, gamma) already have their
                                    // own tiered display above -- shown here
                                    // too would be the same number twice.
                                    model: Thermochemistry.resultRows.filter(
                                               function (r) { return !view.isHeroRow(r.key) })

                                    delegate: ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 1

                                        RFResultValue {
                                            Layout.fillWidth: true
                                            label: modelData.label
                                            value: modelData.value
                                            unit: modelData.unit
                                            scale: "medium"
                                            highlighted: false

                                            HoverHandler { id: rowHover }
                                            RFTooltip {
                                                visible: rowHover.hovered && modelData.help !== ""
                                                text: modelData.help
                                            }
                                        }

                                        Text {
                                            visible: modelData.qualifier !== ""
                                            text: modelData.qualifier
                                            color: Theme.textMuted
                                            font.family: Typography.sans
                                            font.pixelSize: Typography.meta
                                        }
                                    }
                                }
                            }

                            RFDivider {}

                            RFSectionLabel { text: "Advanced" }

                            Text {
                                Layout.fillWidth: true
                                text: "Quantities whose meaning depends on which chemistry "
                                      + "assumption they were taken under. They are here rather "
                                      + "than hidden, and each says which one it is."
                                wrapMode: Text.WordWrap
                                lineHeight: Typography.proseLineHeight
                                lineHeightMode: Text.ProportionalHeight
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: Math.max(2, Math.floor(width / 220))
                                columnSpacing: Metrics.spacing.xl
                                rowSpacing: Metrics.spacing.l

                                Repeater {
                                    model: Thermochemistry.advancedRows

                                    delegate: ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 1

                                        RFResultValue {
                                            Layout.fillWidth: true
                                            label: modelData.label
                                            value: modelData.value
                                            unit: modelData.unit
                                            scale: "small"

                                            HoverHandler { id: advHover }
                                            RFTooltip {
                                                visible: advHover.hovered && modelData.help !== ""
                                                text: modelData.help
                                            }
                                        }

                                        Text {
                                            visible: modelData.qualifier !== ""
                                            text: modelData.qualifier
                                            color: Theme.textMuted
                                            font.family: Typography.sans
                                            font.pixelSize: Typography.meta
                                        }
                                    }
                                }
                            }

                            RFDivider {}

                            ThermoProvenance { Layout.fillWidth: true }

                            RFDivider {}

                            ThermoDiagnostics { Layout.fillWidth: true }
                        }
                    }
                }
            }
        }
    }
}
