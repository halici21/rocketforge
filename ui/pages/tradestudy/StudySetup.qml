import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Defining a study: what is fixed, what varies, what is reported, what is
 * wanted, what is required, and - only if asked for - how it is scored.
 *
 * The workload line is the most important thing on this page. It says how many
 * design points the current definition contains and how many chamber solves
 * they will cost, and it updates as a range is edited, without running
 * anything. A user who can see that 410 points cost 41 chamber solves learns
 * the dependency planner; one who only meets a progress bar will build the
 * study that costs 410.
 *
 * Scoring starts off. It is never enabled by a study happening to have two
 * objectives: collapsing several objectives into one number is a decision, and
 * making it silently would hide it behind a column heading.
 *
 * There is no arithmetic here. Not a normalisation, not a dominance test, not
 * a unit conversion.
 */
Item {
    id: view

    function metricLabel(key) {
        var options = TradeStudy.metricOptions
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key)
                return options[i].label
        return key
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- what is fixed --------------------------------------------
        RFPanel {
            Layout.preferredWidth: Metrics.railWidth
            Layout.minimumWidth: 268
            Layout.fillHeight: true
            title: "Baseline and model"
            contentSpacing: Metrics.spacing.m

            Text {
                Layout.fillWidth: true
                visible: !TradeStudy.baselineAvailable
                text: "A study starts from a chamber case and a nozzle "
                      + "configuration. Set them on the Thermochemistry and "
                      + "Rocket Performance tabs first — nothing here is "
                      + "invented in their place."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.warning
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: TradeStudy.baselineAvailable
                contentWidth: width
                contentHeight: baseline.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: baseline
                    width: parent.width
                    spacing: Metrics.spacing.s

                    Text {
                        Layout.fillWidth: true
                        text: TradeStudy.baselineHeadline
                        wrapMode: Text.WordWrap
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    Repeater {
                        model: TradeStudy.baselineRows

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: false
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 118
                                text: modelData.label
                                wrapMode: Text.WordWrap
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

                    RFDivider {}

                    RFSectionLabel { text: "Held constant by design" }

                    Repeater {
                        model: TradeStudy.deferredVariables

                        delegate: ColumnLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: false
                            spacing: 1

                            Text {
                                text: modelData.label
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.reason
                                wrapMode: Text.WordWrap
                                lineHeight: Typography.proseLineHeight
                                lineHeightMode: Text.ProportionalHeight
                                color: Theme.textDisabled
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                bottomPadding: Metrics.spacing.xs
                            }
                        }
                    }
                }
            }
        }

        // ---- the definition -------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: body.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: body
                    width: parent.width
                    spacing: Metrics.spacing.l

                    // ---- design variables -----------------------------
                    RFPanel {
                        Layout.fillWidth: true
                        title: "Design variables"
                        contentSpacing: Metrics.spacing.s

                        Repeater {
                            model: TradeStudy.variableRows

                            delegate: StudyVariableRow {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spec: modelData
                            }
                        }
                    }

                    // ---- outputs ---------------------------------------
                    RFPanel {
                        Layout.fillWidth: true
                        title: "Reported outputs"
                        contentSpacing: Metrics.spacing.xs

                        Text {
                            Layout.fillWidth: true
                            text: "Objectives and constraints add their own "
                                  + "columns; these are the extra ones. Only "
                                  + "the physics stages a requested metric "
                                  + "needs are evaluated."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            bottomPadding: Metrics.spacing.xs
                        }

                        Flow {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Repeater {
                                model: TradeStudy.metricOptions

                                delegate: RFToggle {
                                    required property var modelData
                                    text: modelData.label
                                    checked: TradeStudy.selectedOutputs
                                                .indexOf(modelData.key) >= 0
                                    onToggled: TradeStudy.setOutputSelected(
                                                   modelData.key, checked)

                                    HoverHandler { id: metricHover }
                                    RFTooltip {
                                        visible: metricHover.hovered
                                        text: modelData.help
                                    }
                                }
                            }
                        }
                    }

                    // ---- objectives ------------------------------------
                    RFPanel {
                        Layout.fillWidth: true
                        title: "Objectives"
                        contentSpacing: Metrics.spacing.s

                        Text {
                            Layout.fillWidth: true
                            text: "Every objective states its own direction. "
                                  + "Nothing here assumes that more of a "
                                  + "quantity is better — that stops being "
                                  + "true the moment it is traded against "
                                  + "another."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        Repeater {
                            model: TradeStudy.objectiveRows

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.label
                                    elide: Text.ElideRight
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.body
                                }
                                // The flow is one-way in each direction, as in
                                // RFBoundNumberField. Binding currentIndex to
                                // the controller while the handler writes back
                                // makes each write reset this Repeater's model
                                // and re-fire the handler; comparing first
                                // breaks the cycle.
                                RFComboBox {
                                    Layout.preferredWidth: 132
                                    model: ["Maximize", "Minimize"]
                                    currentIndex: modelData.direction === "maximize" ? 0 : 1
                                    onActivated: function (index) {
                                        TradeStudy.setObjectiveDirection(
                                            modelData.metric,
                                            index === 0 ? "maximize" : "minimize")
                                    }
                                }
                                RFButton {
                                    text: "Remove"
                                    variant: "quiet"
                                    onClicked: TradeStudy.removeObjective(
                                                   modelData.metric)
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            RFComboBox {
                                id: objectiveMetric
                                Layout.fillWidth: true
                                label: "Add objective"
                                model: TradeStudy.metricOptions.map(
                                           function (m) { return m.label })
                            }
                            RFComboBox {
                                id: objectiveDirection
                                Layout.preferredWidth: 132
                                label: "Direction"
                                model: ["Maximize", "Minimize"]
                            }
                            RFButton {
                                text: "Add"
                                Layout.alignment: Qt.AlignBottom
                                onClicked: {
                                    var options = TradeStudy.metricOptions
                                    if (objectiveMetric.currentIndex < 0
                                        || objectiveMetric.currentIndex >= options.length)
                                        return
                                    TradeStudy.addObjective(
                                        options[objectiveMetric.currentIndex].key,
                                        objectiveDirection.currentIndex === 0
                                            ? "maximize" : "minimize")
                                }
                            }
                        }
                    }

                    // ---- constraints -----------------------------------
                    RFPanel {
                        Layout.fillWidth: true
                        title: "Hard constraints"
                        contentSpacing: Metrics.spacing.s

                        Text {
                            Layout.fillWidth: true
                            text: "A constraint is satisfied or violated. A "
                                  + "point that violates one stays in the "
                                  + "table with every number it produced, and "
                                  + "is excluded from the Pareto front — it is "
                                  + "never turned into a score deduction."
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        Repeater {
                            model: TradeStudy.constraintRows

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.label + "  "
                                          + modelData.operator + "  "
                                          + modelData.limit
                                          + (modelData.unit !== ""
                                             ? " " + modelData.unit : "")
                                    elide: Text.ElideRight
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.body
                                }
                                RFButton {
                                    text: "Remove"
                                    variant: "quiet"
                                    onClicked: TradeStudy.removeConstraint(
                                                   modelData.index)
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            RFComboBox {
                                id: constraintMetric
                                Layout.fillWidth: true
                                label: "Add constraint"
                                model: TradeStudy.metricOptions.map(
                                           function (m) { return m.label })
                            }
                            RFComboBox {
                                id: constraintOperator
                                Layout.preferredWidth: 76
                                label: "Limit"
                                model: TradeStudy.operatorOptions.map(
                                           function (o) { return o.label })
                            }
                            RFNumberField {
                                id: constraintLimit
                                Layout.preferredWidth: 132
                                label: "Value"
                                text: "0"
                                showSteppers: false
                            }
                            RFButton {
                                text: "Add"
                                Layout.alignment: Qt.AlignBottom
                                onClicked: {
                                    var options = TradeStudy.metricOptions
                                    var operators = TradeStudy.operatorOptions
                                    if (constraintMetric.currentIndex < 0
                                        || constraintMetric.currentIndex >= options.length)
                                        return
                                    var value = parseFloat(constraintLimit.text)
                                    if (isNaN(value))
                                        return
                                    TradeStudy.addConstraint(
                                        options[constraintMetric.currentIndex].key,
                                        operators[Math.max(0, constraintOperator.currentIndex)].key,
                                        value)
                                }
                            }
                        }
                    }

                    // ---- optional scoring ------------------------------
                    RFPanel {
                        Layout.fillWidth: true
                        title: "Weighted score — optional"
                        contentSpacing: Metrics.spacing.s

                        trailing: Component {
                            RFStatusChip {
                                text: TradeStudy.scoringEnabled ? "On" : "Off"
                                tone: TradeStudy.scoringEnabled ? "accent" : "neutral"
                                showDot: false
                            }
                        }

                        RFToggle {
                            text: "Combine the objectives into one score"
                            checked: TradeStudy.scoringEnabled
                            onToggled: TradeStudy.scoringEnabled = checked
                        }

                        Text {
                            Layout.fillWidth: true
                            text: TradeStudy.scoringNote
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }

                        Repeater {
                            model: TradeStudy.scoringEnabled
                                   ? TradeStudy.weightRows : []

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.label
                                    elide: Text.ElideRight
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.body
                                }
                                RFBoundNumberField {
                                    Layout.preferredWidth: 110
                                    label: "Weight"
                                    value: modelData.weight
                                    digits: 3
                                    decimals: 3
                                    step: 0.5
                                    onValueEdited: function (v) {
                                        TradeStudy.setWeight(modelData.metric, v)
                                    }
                                }
                                Text {
                                    Layout.preferredWidth: 110
                                    text: "applied " + modelData.effective
                                    color: Theme.textMuted
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }
                    }
                }
            }

            // The run controls are pinned outside the scroll region. At
            // 1366x768 the definition is taller than the panel, and a Run
            // Study button that has to be scrolled to is a clipped primary
            // action.
            RFDivider { Layout.fillWidth: true }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.xs

                Text {
                    Layout.fillWidth: true
                    text: TradeStudy.workloadNote
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: TradeStudy.studyIsLarge ? Theme.warning
                                                   : Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Text {
                    Layout.fillWidth: true
                    visible: !TradeStudy.definitionValid
                    text: TradeStudy.definitionMessage
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Text {
                    Layout.fillWidth: true
                    visible: TradeStudy.busy
                    text: TradeStudy.progressText
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    RFButton {
                        Layout.fillWidth: true
                        text: TradeStudy.busy ? "Running…" : "Run Study"
                        variant: "primary"
                        enabled: TradeStudy.definitionValid && !TradeStudy.busy
                        onClicked: TradeStudy.runStudy()
                    }

                    RFButton {
                        text: "Cancel"
                        variant: "quiet"
                        enabled: TradeStudy.busy
                        onClicked: TradeStudy.cancelStudy()
                    }
                }
            }
        }
    }
}
