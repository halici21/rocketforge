import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * Injector & Feed Pressure - each propellant branch's injector orifice and
 * pressure ledger at the flows sized in Thrust Chamber Sizing (LIQ-6).
 *
 * Nothing is computed until Compute is pressed. Opening the page, editing an
 * input and changes upstream only re-read the controller. Every number, label,
 * unit and reason comes from the Injector controller; this file lays them out.
 *
 *   - The flows, O/F and chamber pressure are LIQ-4's, shown as sized.
 *   - Δp, Cd and the density are stated per branch; none has a default.
 *   - A pressure term is stated, not applicable, or unresolved. Unresolved is
 *     shown as such and never counted as zero.
 *   - Δp/p1 is shown because it is stability-relevant. Stability is not
 *     evaluated here.
 */
Item {
    id: page

    function indexOfKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key) return i
        return 0
    }
    function labels(options) {
        return options.map(function (o) { return o.label })
    }

    component Note: Text {
        Layout.fillWidth: true
        visible: text !== ""
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        wrapMode: Text.WordWrap
    }

    component KeyValue: RowLayout {
        id: kv
        property string label
        property string value
        property string itemName: ""
        Layout.fillWidth: true
        spacing: Metrics.spacing.s
        Text {
            Layout.preferredWidth: 130
            text: kv.label
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            objectName: kv.itemName
            Layout.fillWidth: true
            text: kv.value
            color: Theme.text
            font.family: Typography.mono
            font.pixelSize: Typography.meta
            wrapMode: Text.WordWrap
        }
    }

    // One quantity row: label, value, unit; the note or the reason on hover.
    component ValueRow: Item {
        id: line
        property var row
        property string prefix: ""
        objectName: prefix + "Row_" + row.key
        Layout.fillWidth: true
        implicitHeight: 24
        HoverHandler { id: lineHover }
        RFTooltip {
            visible: lineHover.hovered && text !== ""
            text: line.row.reason !== "" ? line.row.reason : line.row.note
        }
        Text {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 170
            text: line.row.label
            elide: Text.ElideRight
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            objectName: line.prefix + "Value_" + line.row.key
            anchors.right: unitText.left
            anchors.rightMargin: Metrics.spacing.s
            anchors.verticalCenter: parent.verticalCenter
            text: line.row.value
            color: line.row.reason !== "" || line.row.status === "unresolved"
                   ? Theme.textMuted : Theme.text
            font.family: Typography.mono
            font.pixelSize: Typography.meta
        }
        Text {
            id: unitText
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            width: 44
            text: line.row.unit
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    // What the user states for one branch.
    component BranchInputs: ColumnLayout {
        id: inputs
        property var st
        readonly property string b: st.branch
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop
        spacing: Metrics.spacing.s

        RFSectionLabel { text: inputs.st.title + (inputs.st.propellant !== "" ? " · " + inputs.st.propellant : "") }
        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.m
            RFNumberField {
                objectName: "injector_" + inputs.b + "_dp"
                Layout.fillWidth: true
                label: "Injector Δp"
                unit: "bar"
                step: 1
                text: inputs.st.pressureDropText
                onEdited: Injector.setValue(inputs.b, "pressure_drop", text)
            }
            RFNumberField {
                objectName: "injector_" + inputs.b + "_cd"
                Layout.fillWidth: true
                label: "Discharge coefficient Cd"
                step: 0.01
                text: inputs.st.dischargeCoefficientText
                onEdited: Injector.setValue(inputs.b, "discharge_coefficient", text)
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.m
            RFComboBox {
                objectName: "injector_" + inputs.b + "_densitySource"
                Layout.fillWidth: true
                label: "Density source"
                model: page.labels(Injector.densityOptions)
                currentIndex: page.indexOfKey(Injector.densityOptions, inputs.st.densitySource)
                onActivated: function (index) {
                    Injector.setDensitySource(inputs.b, Injector.densityOptions[index].key)
                }
            }
            RFNumberField {
                objectName: "injector_" + inputs.b + "_density"
                Layout.fillWidth: true
                visible: inputs.st.densitySource === "stated"
                label: "Liquid density ρ"
                unit: "kg/m³"
                step: 1
                text: inputs.st.densityText
                onEdited: Injector.setValue(inputs.b, "density", text)
            }
            Item { Layout.fillWidth: true; visible: inputs.st.densitySource !== "stated" }
        }
        Note {
            text: inputs.st.densitySource === "fluid_model"
                  ? (inputs.st.fluidModelSupported
                     ? "Evaluated on Compute at the LIQ-3 stream temperature and the injector inlet, chamber pressure + Δp. Refused if that state is not liquid."
                     : "No validated fluid model for " + inputs.st.propellant + ": state the density.")
                  : ""
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.m
            RFComboBox {
                objectName: "injector_" + inputs.b + "_holeMode"
                Layout.fillWidth: true
                label: "Orifice split"
                model: page.labels(Injector.holeModeOptions)
                currentIndex: page.indexOfKey(Injector.holeModeOptions, inputs.st.holeMode)
                onActivated: function (index) {
                    Injector.setHoleMode(inputs.b, Injector.holeModeOptions[index].key)
                }
            }
            RFNumberField {
                objectName: "injector_" + inputs.b + "_holeCount"
                Layout.fillWidth: true
                visible: inputs.st.holeMode === "hole_count"
                label: "Hole count"
                step: 1
                decimals: 0
                text: inputs.st.holeCountText
                onEdited: Injector.setValue(inputs.b, "hole_count", text)
            }
            RFNumberField {
                objectName: "injector_" + inputs.b + "_holeDiameter"
                Layout.fillWidth: true
                visible: inputs.st.holeMode === "hole_diameter"
                label: "Hole diameter"
                unit: "mm"
                step: 0.1
                text: inputs.st.holeDiameterText
                onEdited: Injector.setValue(inputs.b, "hole_diameter", text)
            }
            Item { Layout.fillWidth: true; visible: inputs.st.holeMode === "area" }
        }

        RFSectionLabel { text: "Pressure terms · unresolved is never counted as zero" }
        GridLayout {
            Layout.fillWidth: true
            columns: width > 560 ? 2 : 1
            columnSpacing: Metrics.spacing.l
            rowSpacing: Metrics.spacing.s
            // A fixed count: the delegates are not recreated when a value changes.
            Repeater {
                model: inputs.st.losses.length
                delegate: RowLayout {
                    id: term
                    required property int index
                    readonly property var t: inputs.st.losses[index]
                    readonly property var options: t.key === "dynamic_head"
                                                    ? Injector.lossModeOptions
                                                    : Injector.lossModeOptions.slice(0, 3)
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    spacing: Metrics.spacing.s
                    RFComboBox {
                        objectName: "injector_" + inputs.b + "_mode_" + term.t.key
                        Layout.preferredWidth: 170
                        Layout.alignment: Qt.AlignBottom
                        label: term.t.label
                        model: page.labels(term.options)
                        currentIndex: page.indexOfKey(term.options, term.t.mode)
                        onActivated: function (i) {
                            Injector.setLossMode(inputs.b, term.t.key, term.options[i].key)
                        }
                    }
                    RFNumberField {
                        objectName: "injector_" + inputs.b + "_value_" + term.t.key
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignBottom
                        visible: term.t.editable
                        unit: term.t.unit
                        step: term.t.unit === "mm" ? 1 : 0.1
                        showSteppers: false
                        text: term.t.valueText
                        onEdited: Injector.setLossValue(inputs.b, term.t.key, text)
                    }
                    Item { Layout.fillWidth: true; visible: !term.t.editable }
                }
            }
        }
    }

    // One branch's result: its quantities and its ledger.
    component BranchResult: ColumnLayout {
        id: res
        property var view
        property string title
        property string b
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop
        spacing: 2

        RFSectionLabel { text: res.title }
        Text {
            objectName: "injector_" + res.b + "_refusal"
            Layout.fillWidth: true
            visible: !res.view.ok && res.view.message !== ""
            text: res.view.message
            color: Theme.warning
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            wrapMode: Text.WordWrap
        }
        Repeater {
            model: res.view.groups
            delegate: ColumnLayout {
                id: group
                required property var modelData
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: group.modelData.title
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    font.weight: Font.DemiBold
                }
                Repeater {
                    model: group.modelData.rows
                    delegate: ValueRow {
                        required property var modelData
                        prefix: "injector_" + res.b + "_"
                        row: modelData
                    }
                }
            }
        }
        Text {
            visible: res.view.ledger.length > 0
            text: "Ledger"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.weight: Font.DemiBold
        }
        Repeater {
            model: res.view.ledger
            delegate: ValueRow {
                required property var modelData
                prefix: "injector_" + res.b + "_ledger"
                row: ({ key: modelData.key, label: modelData.label, value: modelData.value,
                        unit: modelData.unit, status: modelData.status,
                        note: modelData.source, reason: modelData.reason })
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Injector & Feed Pressure"
            subtitle: "Injector orifice area, injection velocity and each branch's pressure ledger at the sized flows"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Orifice hydraulics · no stability, atomization, pump or cycle"
                        showDot: false
                    }
                    RFStatusChip {
                        objectName: "injectorStatus"
                        anchors.verticalCenter: parent.verticalCenter
                        text: Injector.statusLabel
                        tone: Injector.statusTone
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            Flickable {
                id: mainScroll
                objectName: "injectorScroll"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: width
                contentHeight: main.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: main
                    width: mainScroll.width - Metrics.spacing.m
                    spacing: Metrics.spacing.m

                    // ---- flows and stated inputs -----------------------------
                    RFPanel {
                        Layout.fillWidth: true
                        title: "Flows and branch inputs"

                        Note {
                            visible: !Injector.hasFlows
                            text: "From Thrust Chamber Sizing: size a selected trade candidate first."
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: width > 760 ? 2 : 1
                            columnSpacing: Metrics.spacing.l
                            rowSpacing: Metrics.spacing.xs
                            Repeater {
                                model: Injector.basisRows
                                delegate: KeyValue {
                                    required property var modelData
                                    itemName: "injectorBasis"
                                    label: modelData.label
                                    value: modelData.value
                                }
                            }
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: width > 900 ? 2 : 1
                            columnSpacing: Metrics.spacing.xl
                            rowSpacing: Metrics.spacing.l
                            BranchInputs { st: Injector.oxidiserState }
                            BranchInputs { st: Injector.fuelState }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            RFButton {
                                objectName: "injectorRun"
                                text: "Compute"
                                variant: "primary"
                                enabled: Injector.canCompute
                                onClicked: Injector.computeInjector()
                            }
                        }
                        Repeater {
                            model: Injector.issues
                            delegate: Text {
                                objectName: "injectorIssue"
                                required property var modelData
                                Layout.fillWidth: true
                                text: modelData.message
                                color: Theme.warning
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                wrapMode: Text.WordWrap
                            }
                        }
                        Note { objectName: "injectorMessage"; text: Injector.message }
                    }

                    // ---- the result ------------------------------------------
                    RFPanel {
                        Layout.fillWidth: true
                        title: "Branches"

                        RFEmptyState {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 160
                            visible: !Injector.hasResult
                            title: "Not computed yet"
                            body: "State Δp, Cd and the density for both branches, then press "
                                  + "Compute. Nothing is computed until you do."
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            visible: Injector.hasResult
                            columns: width > 900 ? 2 : 1
                            columnSpacing: Metrics.spacing.xl
                            rowSpacing: Metrics.spacing.l
                            BranchResult { b: "oxidiser"; title: "Oxidiser"; view: Injector.oxidiserResult }
                            BranchResult { b: "fuel"; title: "Fuel"; view: Injector.fuelResult }
                        }

                        RFSectionLabel { text: "Pair closure"; visible: Injector.hasResult }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Repeater {
                                model: Injector.pairRows
                                delegate: ValueRow {
                                    required property var modelData
                                    prefix: "injectorPair"
                                    row: modelData
                                }
                            }
                        }
                    }
                }
            }

            // ---- advisories, density, model, provenance -----------------
            RFPanel {
                Layout.preferredWidth: 380
                Layout.fillHeight: true
                title: "Study basis"

                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: width
                    contentHeight: side.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: RFScrollBar {}

                    ColumnLayout {
                        id: side
                        width: parent.width - Metrics.spacing.m
                        spacing: Metrics.spacing.m

                        Note {
                            visible: !Injector.hasResult
                            text: "Shown with a result: advisories, where each density came "
                                  + "from, the model and where the flows came from."
                        }

                        RFSectionLabel { text: "Advisories"; visible: Injector.noteRows.length > 0 }
                        Repeater {
                            model: Injector.noteRows
                            delegate: Note {
                                required property var modelData
                                objectName: "injectorNote"
                                text: modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: Injector.hasResult }
                        RFSectionLabel { text: "Density"; visible: Injector.hasResult }
                        Repeater {
                            model: Injector.hasResult
                                   ? [{ name: "Oxidiser", rows: Injector.oxidiserResult.density },
                                      { name: "Fuel", rows: Injector.fuelResult.density }] : []
                            delegate: Note {
                                required property var modelData
                                text: modelData.name + ": " + modelData.rows
                                      .filter(function (r) { return r.label === "source" })
                                      .map(function (r) { return r.value }).join("")
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: Injector.hasResult }
                        RFSectionLabel { text: "Model"; visible: Injector.hasResult }
                        Repeater {
                            model: Injector.modelAssumptions
                            delegate: Note {
                                required property var modelData
                                text: "· " + modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: Injector.hasResult }
                        RFSectionLabel { text: "Provenance"; visible: Injector.hasResult }
                        Repeater {
                            model: Injector.provenanceRows
                            delegate: Note {
                                required property var modelData
                                text: modelData.label + ": " + modelData.value
                            }
                        }
                    }
                }
            }
        }
    }
}
