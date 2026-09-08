import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * What produced the numbers, and what they are not.
 *
 * The assumption list is the point of this view. An ideal figure is an upper
 * bound on a real engine, and a user who reads one as a prediction is out by
 * several per cent - which is exactly the number they would copy into a
 * spreadsheet. So the assumptions are a first-class panel here rather than a
 * footnote under the results, and they are present before any result exists.
 *
 * The reduction panel exists for a narrower reason. A chamber state carries
 * two different gammas that differ by several per cent, and picking one is a
 * modelling decision rather than a detail. Which one was used, where it came
 * from, and what condensed fraction was accepted are the three facts that
 * decide whether these numbers are comparable with anyone else's.
 *
 * The identity panel says what it checks and, more importantly, what it does
 * not: internal consistency is not agreement with reality.
 */
Item {
    id: view

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

            // ---- what the model claims ----------------------------------
            RFPanel {
                Layout.fillWidth: true
                title: "Model assumptions"
                contentSpacing: Metrics.spacing.s

                trailing: Component {
                    RFStatusChip {
                        text: "Ideal"
                        tone: "warning"
                        showDot: false
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "Read this list as what is absent. Every figure on the "
                          + "Performance tab is an upper bound on a real engine of "
                          + "these dimensions, and the gap is several per cent."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                }

                // Grouped by the layer that made each claim. The two lists
                // overlap - both say the gas is single-phase and
                // constant-property - and concatenating them reads as a list
                // with duplicates in it.
                Repeater {
                    model: RocketPerformance.assumptionGroups

                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        Layout.topMargin: Metrics.spacing.s
                        spacing: Metrics.spacing.xs

                        RFSectionLabel { text: modelData.title }

                        Text {
                            Layout.fillWidth: true
                            text: modelData.note
                            wrapMode: Text.WordWrap
                            color: Theme.textDisabled
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            bottomPadding: Metrics.spacing.xs
                        }

                        Repeater {
                            model: modelData.items

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.alignment: Qt.AlignTop
                                    text: "—"
                                    color: Theme.textDisabled
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData
                                    wrapMode: Text.WordWrap
                                    lineHeight: Typography.proseLineHeight
                                    lineHeightMode: Text.ProportionalHeight
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }
                    }
                }
            }

            // ---- the gas reduction --------------------------------------
            RFPanel {
                Layout.fillWidth: true
                visible: RocketPerformance.hasResult
                title: "Gas reduction and operating point"
                contentSpacing: Metrics.spacing.xs

                Text {
                    Layout.fillWidth: true
                    text: "A chamber state carries two different isentropic "
                          + "exponents. Choosing one is a modelling decision, so the "
                          + "choice and its consequences are recorded here rather "
                          + "than assumed."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    bottomPadding: Metrics.spacing.s
                }

                Repeater {
                    model: RocketPerformance.reductionModel

                    delegate: RowLayout {
                        id: reductionRow
                        required property string label
                        required property string value
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.preferredWidth: 268
                            text: reductionRow.label
                            elide: Text.ElideRight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        Text {
                            Layout.fillWidth: true
                            text: reductionRow.value
                            wrapMode: Text.WordWrap
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }

            // ---- internal consistency -----------------------------------
            RFPanel {
                Layout.fillWidth: true
                visible: RocketPerformance.hasResult
                title: "Internal identities"
                contentSpacing: Metrics.spacing.xs

                trailing: Component {
                    RFStatusChip {
                        text: RocketPerformance.identitiesPassed ? "All closed" : "Failed"
                        tone: RocketPerformance.identitiesPassed ? "success" : "warning"
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: RocketPerformance.identitySummary
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    bottomPadding: Metrics.spacing.s
                }

                Repeater {
                    model: RocketPerformance.identityModel

                    delegate: RowLayout {
                        id: identityRow
                        required property string name
                        required property bool passed
                        required property string residual
                        required property bool scaled
                        required property string tolerance
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.fillWidth: true
                            text: identityRow.name
                            elide: Text.ElideRight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        Text {
                            Layout.preferredWidth: 96
                            horizontalAlignment: Text.AlignRight
                            text: identityRow.residual
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                        }
                        Text {
                            Layout.preferredWidth: 68
                            text: identityRow.passed ? "closed" : "FAILED"
                            color: identityRow.passed ? Theme.success : Theme.error
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }

            // ---- who computed what --------------------------------------
            RFPanel {
                Layout.fillWidth: true
                title: "Provenance"
                contentSpacing: Metrics.spacing.m

                Text {
                    Layout.fillWidth: true
                    text: "Two claims, kept apart. RocketForge computed the "
                          + "performance; a provider computed the chamber state it "
                          + "started from. Merging them into one line would credit "
                          + "these equations to a library that did not run them."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Repeater {
                    model: RocketPerformance.provenanceModel

                    delegate: ColumnLayout {
                        id: provRow
                        required property string computed_by
                        required property string detail
                        required property string model
                        required property string role
                        Layout.fillWidth: true
                        spacing: 2

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                text: provRow.role
                                elide: Text.ElideRight
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                            }
                            RFStatusChip {
                                text: provRow.computed_by
                                showDot: false
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: provRow.model !== ""
                            text: provRow.model
                            wrapMode: Text.WordWrap
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: provRow.detail !== ""
                            text: provRow.detail
                            wrapMode: Text.WordWrap
                            color: Theme.textDisabled
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }
        }
    }
}
