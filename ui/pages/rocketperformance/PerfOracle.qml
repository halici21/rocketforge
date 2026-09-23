import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The provider's own performance, in its own panel.
 *
 * NASA CEA computes c*, Cf and Isp itself. Those numbers are worth seeing, and
 * they are shown here - separated from RocketForge's by a panel boundary, a
 * heading and a run button, because they are a different program's answer and
 * nothing on the Performance tab is derived from them.
 *
 * The panel is deliberately awkward to confuse with a result. It has to be
 * asked for; it names the provider on every row; and the comparison table
 * calls each residual a model difference rather than an error, because that is
 * what it is. RocketForge holds gamma and R constant through the expansion and
 * the provider is calorically imperfect in every mode it offers, so no setting
 * of either makes them the same calculation.
 *
 * The comparison also matches the reference condition on both sides. CEA
 * quotes Cf and Isp at optimum expansion; putting a vacuum figure beside one
 * of those would be wrong by the whole pressure term, which is larger than any
 * model difference this table exists to show.
 *
 * With no chemistry library installed this panel says so and nothing else on
 * the workspace is affected - RocketForge's own numbers never needed it.
 */
Item {
    id: view

    function indexOfKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key)
                return i
        return 0
    }

    function noteForKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key)
                return options[i].note
        return ""
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: body.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: RFScrollBar {}

        ColumnLayout {
            id: body
            width: parent.width
            spacing: Metrics.spacing.l

            RFPanel {
                Layout.fillWidth: true
                title: "Provider performance — an independent answer"
                contentSpacing: Metrics.spacing.m

                trailing: Component {
                    Row {
                        spacing: Metrics.spacing.s

                        RFStatusChip {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: RocketPerformance.oracleStale
                            text: "Case changed"
                            tone: "warning"
                        }
                        RFStatusChip {
                            anchors.verticalCenter: parent.verticalCenter
                            text: RocketPerformance.oracleStatusLabel
                            tone: RocketPerformance.oracleStatus === "ok" ? "success"
                                : RocketPerformance.oracleStatus === "empty" ? "neutral"
                                : "warning"
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    readonly property string plainText: "The provider computes c*, Cf and Isp itself. Those values "
                          + "are shown here to compare against — nothing on the "
                          + "Performance tab is derived from them, and running this "
                          + "does not change a single number there."
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.m

                    RFComboBox {
                        Layout.preferredWidth: 260
                        label: "Expansion chemistry"
                        model: RocketPerformance.oracleModes.map(
                                   function (o) { return o.label })
                        currentIndex: view.indexOfKey(RocketPerformance.oracleModes,
                                                      RocketPerformance.oracleMode)
                        onCurrentIndexChanged: {
                            var options = RocketPerformance.oracleModes
                            if (currentIndex >= 0 && currentIndex < options.length)
                                RocketPerformance.oracleMode = options[currentIndex].key
                        }
                    }

                    RFButton {
                        text: "Run provider"
                        variant: "default"
                        enabled: RocketPerformance.hasChamber
                                 && !RocketPerformance.oracleBusy
                        onClicked: RocketPerformance.runOracle()
                    }

                    RFButton {
                        text: "Clear"
                        variant: "quiet"
                        enabled: RocketPerformance.oracleStatus !== "empty"
                        onClicked: RocketPerformance.clearOracle()
                    }

                    Item { Layout.fillWidth: true }
                }

                Text {
                    Layout.fillWidth: true
                    text: view.noteForKey(RocketPerformance.oracleModes,
                                          RocketPerformance.oracleMode)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    visible: RocketPerformance.oracleStatus === "empty"
                             && RocketPerformance.hasChamber
                    tag: "NOT RUN"
                    title: "The provider has not been asked"
                    body: "This runs a separate chemistry solve, so it happens only "
                          + "when you press Run provider. Changing a nozzle input "
                          + "never triggers it."
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    visible: !RocketPerformance.hasChamber
                    tag: "NO CHAMBER"
                    title: "No chamber state to run"
                    body: "The comparison uses the same operating point as the "
                          + "chamber equilibrium. Solve one on the Thermochemistry "
                          + "tab first."
                }

                Text {
                    Layout.fillWidth: true
                    visible: RocketPerformance.oracleMessage !== ""
                    text: RocketPerformance.oracleMessage
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            // ---- the provider's numbers, labelled as the provider's -------
            RFPanel {
                Layout.fillWidth: true
                visible: RocketPerformance.oracleStatus === "ok"
                title: "Computed by " + RocketPerformance.oracleProvider
                contentSpacing: Metrics.spacing.xs

                Repeater {
                    model: RocketPerformance.oracleModel

                    delegate: RowLayout {
                        id: oracleRow
                        required property string label
                        required property string value
                        required property string unit
                        Layout.fillWidth: true
                        Layout.preferredHeight: 26
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.preferredWidth: 260
                            text: Notation.rich(oracleRow.label)
                            textFormat: Notation.textFormat(oracleRow.label)
                            elide: Text.ElideRight
                            clip: true              // RichText does not elide
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.body
                        }
                        Text {
                            Layout.preferredWidth: 128
                            horizontalAlignment: Text.AlignRight
                            text: oracleRow.value
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.body
                        }
                        Text {
                            Layout.fillWidth: true
                            text: oracleRow.unit
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    topPadding: Metrics.spacing.s
                    text: "Reference condition: " + RocketPerformance.oracleReferenceCondition
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            // ---- side by side, with the residual named honestly -----------
            RFPanel {
                Layout.fillWidth: true
                visible: RocketPerformance.oracleStatus === "ok"
                         && RocketPerformance.hasResult
                title: "RocketForge against the provider"
                contentSpacing: Metrics.spacing.s

                Text {
                    Layout.fillWidth: true
                    text: RocketPerformance.oracleComparisonNote
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
                    spacing: Metrics.spacing.s

                    Text {
                        Layout.preferredWidth: 236
                        text: "Quantity"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 116
                        horizontalAlignment: Text.AlignRight
                        text: "RocketForge"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 116
                        horizontalAlignment: Text.AlignRight
                        text: RocketPerformance.oracleProvider
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 92
                        horizontalAlignment: Text.AlignRight
                        text: "Difference"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Item { Layout.fillWidth: true }
                }

                RFDivider { Layout.fillWidth: true }

                Repeater {
                    model: RocketPerformance.oracleComparisonModel

                    delegate: ColumnLayout {
                        id: cmpRow
                        required property string label
                        required property string rocketforge
                        required property string provider
                        required property string difference
                        required property string kind
                        required property string reference
                        Layout.fillWidth: true
                        spacing: 1

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 26
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 236
                                text: Notation.rich(cmpRow.label)
                                textFormat: Notation.textFormat(cmpRow.label)
                                elide: Text.ElideRight
                                clip: true              // RichText does not elide
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                            }
                            Text {
                                Layout.preferredWidth: 116
                                horizontalAlignment: Text.AlignRight
                                text: cmpRow.rocketforge
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.body
                            }
                            Text {
                                Layout.preferredWidth: 116
                                horizontalAlignment: Text.AlignRight
                                text: cmpRow.provider
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.body
                            }
                            Text {
                                Layout.preferredWidth: 92
                                horizontalAlignment: Text.AlignRight
                                text: cmpRow.difference
                                color: Theme.textSecondary
                                font.family: Typography.mono
                                font.pixelSize: Typography.body
                            }
                            Text {
                                Layout.fillWidth: true
                                text: cmpRow.kind
                                color: Theme.textDisabled
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            Layout.bottomMargin: Metrics.spacing.xs
                            text: cmpRow.reference
                            wrapMode: Text.WordWrap
                            color: Theme.textDisabled
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }
        }
    }
}
