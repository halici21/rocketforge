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

    // 1366x768 leaves the result column about 900x500: the band and the
    // tiers tighten there rather than pushing the species below the fold.
    readonly property bool compact: width < 1500 || height < 640

    // The hero row and its context rows, read off the result's own rows by
    // key -- selection only; every value is the controller's, formatted.
    function resultRow(key) {
        var rows = Thermochemistry.resultRows
        for (var i = 0; i < rows.length; ++i)
            if (rows[i].key === key)
                return rows[i]
        return null
    }
    readonly property var heroRow: {
        Thermochemistry.resultRows          // re-read when the result changes
        return view.resultRow("temperature")
    }
    readonly property var contextCells: {
        var out = []
        var keys = ["molar_mass", "gamma"]
        for (var i = 0; i < keys.length; ++i) {
            var row = view.resultRow(keys[i])
            if (row === null)
                continue
            out.push({ kind: "label", text: row.label })
            out.push({ kind: "value", text: row.value })
            out.push({ kind: "unit", text: row.unit })
        }
        return out
    }

    // A secondary readout: label, value, unit on one line, the qualifier
    // beneath. For the chamber properties and the advanced quantities, so
    // neither reads as a wall of hero-sized numbers.
    component PropertyRow: ColumnLayout {
        id: propertyRow
        property var row: ({})
        spacing: 1

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            Text {
                Layout.fillWidth: true
                readonly property string plainText: propertyRow.row.label || ""
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                elide: Text.ElideRight
                clip: true                  // RichText does not elide
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
            Text {
                text: propertyRow.row.value !== undefined ? propertyRow.row.value : "—"
                color: Theme.text
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
                font.weight: Typography.medium
            }
            Text {
                visible: text !== ""
                text: propertyRow.row.unit || ""
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        Text {
            Layout.fillWidth: true
            visible: plainText !== ""
            readonly property string plainText: propertyRow.row.qualifier || ""
            text: Notation.rich(plainText)
            textFormat: Notation.textFormat(plainText)
            elide: Text.ElideRight
            clip: true
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        HoverHandler { id: propertyHover }
        RFTooltip {
            visible: propertyHover.hovered && (propertyRow.row.help || "") !== ""
            text: propertyRow.row.help || ""
        }
    }

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
                            text: Notation.rich(Thermochemistry.solidFormulationLabel)
                            textFormat: Notation.textFormat(Thermochemistry.solidFormulationLabel)
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
                                    text: Notation.species(ingredientRow.modelData.name)
                                    textFormat: Notation.speciesFormat(ingredientRow.modelData.name)
                                    elide: Text.ElideRight
                                    clip: true              // RichText does not elide
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
                            label: "Chamber pressure  <i>p</i><sub>c</sub>"
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
        //
        // The chamber state is the object, read in tiers: the station band
        // (what went in, the equilibrium chamber, what came out), then Tc,
        // then M̄ and γ -- and c* where this workspace carries one, a solid
        // result's CEA equilibrium c* -- then the leading species and the
        // condensed-phase state with the other chamber properties, and last
        // the case, the advanced quantities, provenance and diagnostics.
        // Every value is the result's own; an edited input dims all of it and
        // relabels none of it.
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
                // Not a void with a sentence in it, and not a borrowed answer:
                // the one published reference this workspace ships (NASA CEA
                // 2002, LOX/LH2) exists to check the pipeline and is never
                // shown as a result. What is shown is the structure a solve
                // fills -- the band, unannotated, and the tiers in the order
                // they will be read, each holding a dash rather than a number.
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: Thermochemistry.statusKind === "empty"
                    spacing: Metrics.spacing.l

                    ThermoChamberSchematic {
                        Layout.fillWidth: true
                        hasResult: false
                        stale: false
                        // The unsolved outline must not claim a feed topology
                        // either: a grain is one charge, not two streams.
                        singleStream: Thermochemistry.isSolid
                    }

                    RFDivider { Layout.fillWidth: true }

                    ColumnLayout {
                        Layout.fillWidth: true
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
                            Layout.maximumWidth: 640
                            text: "The band above is the structure this workspace solves, "
                                  + "not a result. Set the reactants and operating conditions, "
                                  + "then press Calculate. Nothing is estimated before a solve."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }

                        // What the form describes -- labelled as the form, so
                        // it cannot be read as a result.
                        Text {
                            Layout.fillWidth: true
                            Layout.topMargin: Metrics.spacing.xs
                            visible: !Thermochemistry.isSolid
                                     && Thermochemistry.caseHeadline !== ""
                            readonly property string plainText: "Case in the form:  "
                                                                + Thermochemistry.caseHeadline
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
                            elide: Text.ElideRight
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                        }
                    }

                    // The tiers a solve fills, in the shape they will have:
                    // Tc alone, its context beside it. Labels only; every
                    // value is a dash -- unavailable, not zero.
                    RowLayout {
                        Layout.fillWidth: true
                        // A divider inside fills height, which would make this
                        // row fill the page and sink to its bottom.
                        Layout.fillHeight: false
                        Layout.topMargin: Metrics.spacing.s
                        spacing: Metrics.spacing.h1
                        opacity: 0.55

                        RFResultValue {
                            label: "Chamber temperature  T₀"
                            value: "—"
                            unit: "K"
                            scale: "hero"
                        }
                        RFDivider {
                            Layout.fillHeight: true
                            Layout.preferredWidth: Metrics.hairline
                            vertical: true
                        }
                        GridLayout {
                            Layout.alignment: Qt.AlignVCenter
                            columns: 2
                            columnSpacing: Metrics.spacing.m
                            rowSpacing: Metrics.spacing.xs
                            Repeater {
                                model: ["Mean molar mass  M̄", "—",
                                        "Isentropic exponent  γ_s", "—"]
                                delegate: Text {
                                    required property string modelData
                                    required property int index
                                    text: index % 2 === 0 ? Notation.rich(modelData) : modelData
                                    textFormat: index % 2 === 0 ? Notation.textFormat(modelData)
                                                                : Text.PlainText
                                    color: index % 2 === 0 ? Theme.textSecondary : Theme.text
                                    font.family: index % 2 === 0 ? Typography.sans : Typography.mono
                                    font.pixelSize: index % 2 === 0 ? Typography.bodySmall
                                                                    : Typography.readoutMedium
                                }
                            }
                        }
                        // Under its qualifying title, as when solved.
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            visible: Thermochemistry.isSolid
                            spacing: Metrics.spacing.xs
                            RFSectionLabel { text: "CEA equilibrium characteristic velocity" }
                            RFResultValue {
                                label: "c*"
                                value: "—"
                                unit: "m/s"
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }

                    Text {
                        Layout.fillWidth: true
                        opacity: 0.8
                        text: "Then the leading product species and the condensed-phase state, "
                              + "the other chamber properties, and the provenance of the solve."
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
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
                                text: Notation.rich(Thermochemistry.statusLabel)
                                textFormat: Notation.textFormat(Thermochemistry.statusLabel)
                                horizontalAlignment: Text.AlignHCenter
                                color: Theme.warning
                                font.family: Typography.sans
                                font.pixelSize: Typography.groupLabel + 2
                                font.weight: Typography.medium
                            }

                            Text {
                                Layout.fillWidth: true
                                readonly property string plainText: Thermochemistry.statusMessage
                                text: Notation.rich(plainText)
                                textFormat: Notation.textFormat(plainText)
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
                Flickable {
                    id: resultView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: Thermochemistry.hasResult
                    contentWidth: width
                    contentHeight: readouts.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    // Shown whenever there is more below, so a tier cut at
                    // the fold reads as the top of a column, not its end.
                    ScrollBar.vertical: RFScrollBar {
                        policy: resultView.contentHeight > resultView.height
                                ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
                    }

                    ColumnLayout {
                        id: readouts
                        width: resultView.width - (resultView.contentHeight > resultView.height ? 12 : 0)
                        spacing: view.compact ? Metrics.spacing.m : Metrics.spacing.l

                        // ---- the object: reactants -> chamber -> products --
                        ThermoChamberSchematic {
                            Layout.fillWidth: true
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
                            chamberPressureText: "<i>p</i><sub>c</sub> = " + view.conditionValue("Chamber pressure")
                            productsSummary: Thermochemistry.condensed.headline
                        }

                        // ---- 1  the chamber temperature, and 2  its context -
                        //
                        // Tc alone at hero size; M̄ and γ a quiet list beside
                        // it, never cells of the same weight; c* -- a solid
                        // result's CEA equilibrium c*, the one c* this
                        // workspace may show (Solid Propellant Phase 1, D2) --
                        // under its qualifying title, with what it is not.
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.topMargin: view.compact ? Metrics.spacing.s : Metrics.spacing.l
                            Layout.bottomMargin: view.compact ? Metrics.spacing.xs : Metrics.spacing.m
                            spacing: view.compact ? Metrics.spacing.xl : Metrics.spacing.h1
                            opacity: Thermochemistry.resultStale ? 0.55 : 1

                            ColumnLayout {
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.xs
                                visible: view.heroRow !== null

                                Text {
                                    readonly property string plainText: view.heroRow ? view.heroRow.label : ""
                                    text: Notation.rich(plainText)
                                    textFormat: Notation.textFormat(plainText)
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.body
                                }
                                Row {
                                    spacing: Metrics.spacing.s
                                    Text {
                                        id: heroValue
                                        text: view.heroRow ? view.heroRow.value : "—"
                                        color: Theme.accent
                                        font.family: Typography.mono
                                        font.pixelSize: Typography.readoutHero
                                        font.weight: Typography.medium

                                        HoverHandler { id: heroHover }
                                        RFTooltip {
                                            visible: heroHover.hovered && view.heroRow
                                                     && view.heroRow.help !== ""
                                            text: view.heroRow ? view.heroRow.help : ""
                                        }
                                    }
                                    Text {
                                        anchors.baseline: heroValue.baseline
                                        text: view.heroRow ? view.heroRow.unit : ""
                                        color: Theme.textMuted
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

                            // The thermodynamic context of that temperature.
                            GridLayout {
                                Layout.alignment: Qt.AlignVCenter
                                columns: 3
                                columnSpacing: Metrics.spacing.m
                                rowSpacing: Metrics.spacing.xs

                                Repeater {
                                    model: view.contextCells
                                    delegate: Text {
                                        required property var modelData
                                        Layout.alignment: modelData.kind === "value"
                                                          ? Qt.AlignRight | Qt.AlignBaseline
                                                          : Qt.AlignLeft | Qt.AlignBaseline
                                        text: modelData.kind === "label"
                                              ? Notation.rich(modelData.text) : modelData.text
                                        textFormat: modelData.kind === "label"
                                                    ? Notation.textFormat(modelData.text)
                                                    : Text.PlainText
                                        color: modelData.kind === "value" ? Theme.text
                                             : modelData.kind === "label" ? Theme.textSecondary
                                             : Theme.textMuted
                                        font.family: modelData.kind === "value"
                                                     ? Typography.mono : Typography.sans
                                        font.pixelSize: modelData.kind === "value"
                                                        ? Typography.readoutMedium
                                                        : Typography.bodySmall
                                        font.weight: modelData.kind === "value"
                                                     ? Typography.medium : Typography.regular
                                    }
                                }
                            }

                            RFDivider {
                                Layout.fillHeight: true
                                Layout.preferredWidth: Metrics.hairline
                                vertical: true
                                visible: Thermochemistry.solidCStarShown
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignTop
                                visible: Thermochemistry.solidCStarShown
                                spacing: Metrics.spacing.xs

                                RFSectionLabel {
                                    text: "CEA equilibrium characteristic velocity"
                                }

                                RFResultValue {
                                    label: "c*"
                                    value: Thermochemistry.solidCStarText
                                    unit: Thermochemistry.solidCStarAvailable ? "m/s" : ""
                                    scale: "medium"
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                                visible: !Thermochemistry.solidCStarShown
                            }
                        }

                        // What that c* is not, every time it is shown: a compact
                        // row of its own under the tier it belongs to, so the
                        // top of the page is Tc, not a strip of small print.
                        RowLayout {
                            Layout.fillWidth: true
                            visible: Thermochemistry.solidCStarShown
                            spacing: Metrics.spacing.m
                            opacity: Thermochemistry.resultStale ? 0.55 : 1

                            Text {
                                Layout.alignment: Qt.AlignTop
                                text: "c*"
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                                font.italic: true
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    Layout.fillWidth: true
                                    visible: !Thermochemistry.solidCStarAvailable
                                    text: "Not available. " + Thermochemistry.solidCStarRefusal
                                    wrapMode: Text.WordWrap
                                    color: Theme.warning
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: Thermochemistry.solidCStarLimitations.join(" ")
                                          + (Thermochemistry.solidCStarCondensedNote !== ""
                                             ? " " + Thermochemistry.solidCStarCondensedNote : "")
                                    wrapMode: Text.WordWrap
                                    lineHeight: Typography.proseLineHeight
                                    lineHeightMode: Text.ProportionalHeight
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }

                        ThermoWarnings { Layout.fillWidth: true }

                        RFDivider { Layout.fillWidth: true }

                        // ---- 3  composition --------------------------------
                        // The species that make up most of the mixture, on an
                        // absolute 0-1 scale so a bar's length is the mole
                        // fraction itself, beside the condensed-phase state.
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: view.compact ? Metrics.spacing.l : Metrics.spacing.xl
                            opacity: Thermochemistry.resultStale ? 0.55 : 1

                            ColumnLayout {
                                id: leaders
                                Layout.fillWidth: true
                                Layout.preferredWidth: 3
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.xs

                                readonly property var leading: Thermochemistry.leadingSpecies

                                RowLayout {
                                    Layout.fillWidth: true
                                    RFSectionLabel { text: "Composition" }
                                    Text {
                                        Layout.leftMargin: Metrics.spacing.s
                                        text: "leading species"
                                        color: Theme.textMuted
                                        font.family: Typography.sans
                                        font.pixelSize: Typography.meta
                                    }
                                    Item { Layout.fillWidth: true }
                                    Text {
                                        readonly property string plainText: "mole fraction X"
                                        text: Notation.rich(plainText)
                                        textFormat: Notation.textFormat(plainText)
                                        color: Theme.textMuted
                                        font.family: Typography.sans
                                        font.pixelSize: Typography.meta
                                    }
                                }

                                Repeater {
                                    model: leaders.leading.rows

                                    delegate: RowLayout {
                                        id: speciesRow
                                        required property var modelData
                                        required property int index
                                        Layout.fillWidth: true
                                        spacing: Metrics.spacing.m

                                        RowLayout {
                                            Layout.preferredWidth: view.compact ? 120 : 150
                                            Layout.maximumWidth: view.compact ? 120 : 150
                                            spacing: Metrics.spacing.xs
                                            Text {
                                                text: Notation.species(speciesRow.modelData.label)
                                                textFormat: Notation.speciesFormat(speciesRow.modelData.label)
                                                color: Theme.text
                                                font.family: Typography.mono
                                                font.pixelSize: speciesRow.index === 0
                                                                ? Typography.readoutMedium
                                                                : Typography.readoutSmall
                                                font.weight: speciesRow.index === 0
                                                             ? Typography.medium : Typography.regular
                                            }
                                            Text {
                                                visible: speciesRow.modelData.condensed
                                                text: speciesRow.modelData.phase
                                                color: Theme.textMuted
                                                font.family: Typography.sans
                                                font.pixelSize: Typography.meta
                                            }
                                        }

                                        Item {
                                            Layout.fillWidth: true
                                            implicitHeight: 14

                                            Rectangle {
                                                anchors.verticalCenter: parent.verticalCenter
                                                width: parent.width
                                                height: 1
                                                color: Theme.divider
                                            }
                                            Rectangle {
                                                anchors.verticalCenter: parent.verticalCenter
                                                width: Math.max(1, parent.width
                                                                   * Math.min(1, speciesRow.modelData.fraction))
                                                height: speciesRow.index === 0 ? 8 : 6
                                                radius: 1
                                                // Condensed material in the
                                                // secondary tone; the phase is
                                                // also written beside the name.
                                                color: speciesRow.modelData.condensed
                                                       ? Theme.textSecondary : Theme.accent
                                                opacity: 0.85
                                            }
                                        }

                                        Text {
                                            Layout.preferredWidth: 96
                                            horizontalAlignment: Text.AlignRight
                                            text: speciesRow.modelData.text
                                            color: Theme.text
                                            font.family: Typography.mono
                                            font.pixelSize: speciesRow.index === 0
                                                            ? Typography.readoutMedium
                                                            : Typography.readoutSmall
                                        }
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    visible: leaders.leading.shown > 0
                                    readonly property string plainText: leaders.leading.shown + " of "
                                          + leaders.leading.total + " species, ΣX = "
                                          + leaders.leading.sumText
                                          + ". Every species, on either basis, is on Composition."
                                    text: Notation.rich(plainText)
                                    textFormat: Notation.textFormat(plainText)
                                    wrapMode: Text.WordWrap
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                            }

                            RFDivider {
                                Layout.fillHeight: true
                                Layout.preferredWidth: Metrics.hairline
                                vertical: true
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 2
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.s

                                RFSectionLabel { text: "Condensed products" }

                                Text {
                                    Layout.fillWidth: true
                                    text: Thermochemistry.condensed.headline
                                    wrapMode: Text.WordWrap
                                    color: Theme.text
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.body
                                }
                                Text {
                                    Layout.fillWidth: true
                                    visible: Thermochemistry.condensed.detail !== ""
                                    readonly property string plainText: Thermochemistry.condensed.detail
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

                        RFDivider { Layout.fillWidth: true }

                        // ---- 4  chamber properties, then the rest ------------
                        // Secondary on purpose: compact label-value rows, not
                        // another row of hero numbers.
                        RFSectionLabel { text: "Chamber properties" }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: view.compact ? 2 : 3
                            columnSpacing: Metrics.spacing.xl
                            rowSpacing: Metrics.spacing.s
                            opacity: Thermochemistry.resultStale ? 0.55 : 1

                            Repeater {
                                // The hero and context rows are shown above;
                                // here they would be the same number twice.
                                model: Thermochemistry.resultRows.filter(
                                           function (r) { return !view.isHeroRow(r.key) })
                                delegate: PropertyRow {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                    row: modelData
                                }
                            }
                        }

                        RFDivider { Layout.fillWidth: true }

                        ThermoResultHeader {
                            Layout.fillWidth: true
                            opacity: Thermochemistry.resultStale ? 0.55 : 1
                        }

                        RFDivider { Layout.fillWidth: true }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.m
                            RFSectionLabel { text: "Advanced" }
                            Text {
                                Layout.fillWidth: true
                                text: "Quantities whose meaning depends on the chemistry assumption "
                                      + "they were taken under; each says which one."
                                elide: Text.ElideRight
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: view.compact ? 2 : 3
                            columnSpacing: Metrics.spacing.xl
                            rowSpacing: Metrics.spacing.s
                            opacity: Thermochemistry.resultStale ? 0.55 : 1

                            Repeater {
                                model: Thermochemistry.advancedRows
                                delegate: PropertyRow {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                    row: modelData
                                }
                            }
                        }

                        RFDivider { Layout.fillWidth: true }

                        ThermoProvenance { Layout.fillWidth: true }

                        RFDivider { Layout.fillWidth: true }

                        ThermoDiagnostics { Layout.fillWidth: true }
                    }
                }
            }
        }
    }
}
