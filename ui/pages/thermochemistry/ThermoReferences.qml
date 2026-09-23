import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Reference comparison - does this pipeline reproduce an accepted external case?
 *
 * The direction is always
 *
 *     published value  --compare-->  RocketForge + provider value
 *
 * and never a lookup. Nothing in RocketForge reads these numbers to produce a
 * result, and none of them is editable: a reference that could be adjusted
 * would stop being evidence.
 *
 * The tolerance is the source's own rounding box, derived from the precision
 * it was printed to, not a constant chosen to make a value pass.
 *
 * The published source also carries c*, Isp and an exit gamma. They are not
 * compared here and no value for them is loaded, because RocketForge does not
 * own a characteristic velocity or a specific impulse yet. That omission is
 * stated on the page rather than left as a silent gap.
 */
Item {
    id: view

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: sheet.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: RFScrollBar {}

        ColumnLayout {
            id: sheet
            width: parent.width
            spacing: Metrics.spacing.l

            RFPanel {
                Layout.fillWidth: true
                title: Thermochemistry.referenceTitle
                contentSpacing: Metrics.spacing.m

                trailing: Component {
                    Row {
                        spacing: Metrics.spacing.s

                        RFStatusChip {
                            anchors.verticalCenter: parent.verticalCenter
                            text: Thermochemistry.referenceLevel
                            showDot: false
                        }
                        RFStatusChip {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: Thermochemistry.referenceHasRun
                            text: Thermochemistry.referenceVerdict
                            tone: Thermochemistry.referenceVerdict === "PASS"
                                  ? "success" : "error"
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: Thermochemistry.referenceCitation
                    wrapMode: Text.WordWrap
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    RFButton {
                        text: "Run reference case"
                        variant: "primary"
                        enabled: !Thermochemistry.busy
                        onClicked: Thermochemistry.runReference()
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Runs the stored conditions exactly as published. The Calculator "
                              + "form is not consulted, so nothing you typed can stand in for "
                              + "the reference case."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }

            // ---- the comparison ------------------------------------------
            RFPanel {
                Layout.fillWidth: true
                title: "Comparison"
                contentSpacing: Metrics.spacing.s

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xl
                    Layout.bottomMargin: Metrics.spacing.xl
                    visible: !Thermochemistry.referenceHasRun
                    tag: "NOT RUN"
                    title: "Reference case not run"
                    body: "Press Run reference case to solve the published conditions through "
                          + "the current provider and compare, value by value."
                }

                Text {
                    Layout.fillWidth: true
                    visible: Thermochemistry.referenceHasRun
                             && Thermochemistry.referenceStatusMessage !== ""
                    text: Thermochemistry.referenceStatusMessage
                    wrapMode: Text.WordWrap
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                // header
                RowLayout {
                    Layout.fillWidth: true
                    visible: Thermochemistry.referenceHasRun
                    spacing: Metrics.spacing.m

                    Text {
                        Layout.preferredWidth: 196
                        text: "Quantity"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: 0.6
                    }
                    Text {
                        Layout.preferredWidth: 132
                        horizontalAlignment: Text.AlignRight
                        text: "PUBLISHED"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: 0.6
                    }
                    Text {
                        Layout.preferredWidth: 132
                        horizontalAlignment: Text.AlignRight
                        text: "ROCKETFORGE"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: 0.6
                    }
                    Text {
                        Layout.preferredWidth: 92
                        horizontalAlignment: Text.AlignRight
                        text: "DIFFERENCE"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: 0.6
                    }
                    Text {
                        Layout.preferredWidth: 108
                        horizontalAlignment: Text.AlignRight
                        text: "SOURCE BOX"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: 0.6
                    }
                    Text {
                        Layout.preferredWidth: 62
                        horizontalAlignment: Text.AlignRight
                        text: "VERDICT"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: 0.6
                    }
                    Item { Layout.fillWidth: true }
                }

                Repeater {
                    model: Thermochemistry.referenceRows

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.m

                        Text {
                            Layout.preferredWidth: 196
                            text: Notation.rich(modelData.label)
                            textFormat: Notation.textFormat(modelData.label)
                            elide: Text.ElideRight
                            clip: true              // RichText does not elide
                            color: Theme.text
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 132
                            horizontalAlignment: Text.AlignRight
                            text: modelData.published
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 132
                            horizontalAlignment: Text.AlignRight
                            text: modelData.computed
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 92
                            horizontalAlignment: Text.AlignRight
                            text: modelData.difference
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 108
                            horizontalAlignment: Text.AlignRight
                            text: modelData.tolerance
                            color: Theme.textMuted
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 62
                            horizontalAlignment: Text.AlignRight
                            text: modelData.verdict
                            color: modelData.passed ? Theme.success : Theme.error
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.medium
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.unit
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
                    visible: Thermochemistry.referenceHasRun
                    text: "The source box is the interval the printed value stands for, from "
                          + "its own significant figures. A value inside it agrees with the "
                          + "source as precisely as the source was stated."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            // ---- what is deliberately not compared ------------------------
            RFPanel {
                Layout.fillWidth: true
                title: "Published but not compared"
                contentSpacing: Metrics.spacing.s

                Text {
                    Layout.fillWidth: true
                    text: "The source carries these as well. RocketForge does not own them "
                          + "yet, so no value for them is loaded and none is shown."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Repeater {
                    model: Thermochemistry.referenceNotCompared

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.m

                        Text {
                            Layout.preferredWidth: 196
                            Layout.alignment: Qt.AlignTop
                            text: Notation.rich(modelData.label)
                            textFormat: Notation.textFormat(modelData.label)
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.fillWidth: true
                            readonly property string plainText: modelData.reason
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
            }

            // ---- source ---------------------------------------------------
            RFPanel {
                Layout.fillWidth: true
                title: "Source and conditions"
                contentSpacing: Metrics.spacing.xs

                Repeater {
                    model: Thermochemistry.referenceSourceRows

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.m

                        Text {
                            Layout.preferredWidth: 176
                            Layout.alignment: Qt.AlignTop
                            text: Notation.rich(modelData.label)
                            textFormat: Notation.textFormat(modelData.label)
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                        Text {
                            Layout.fillWidth: true
                            readonly property string plainText: modelData.value
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
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
}
