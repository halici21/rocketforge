import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * What the result says about condensed products.
 *
 * It sits with the composition rather than with the display controls, because
 * it is a statement about the result and not a setting - and because at
 * 1366x768 a verdict in a scrolling control rail is a verdict nobody reads.
 *
 * Four states, not two. The two "not present" ones are kept apart on purpose:
 *
 *   none reported      the fraction is exactly zero
 *   below threshold    0 < fraction < the reporting threshold
 *
 * A measured 6.24e-08 is not zero. Reporting it as "none detected" claimed the
 * mixture contained no condensed material, which is a stronger statement than
 * the number supports. So the second state says what it is, and shows both the
 * exact fraction and the threshold it was judged against.
 *
 * The threshold is a REPORTING threshold. It decides which sentence appears.
 * It changes no composition, removes no species and never reaches the provider.
 *
 * Layout note: the metadata is a Flow and the column asks for no width of its
 * own. Both matter - a row of fixed-width pairs here made the whole panel
 * wider than the window at 1366x768 and clipped the table beside it.
 */
RowLayout {
    id: summary

    readonly property var condensed: Thermochemistry.condensed

    spacing: Metrics.spacing.m
    visible: Thermochemistry.hasComposition

    RFStatusChip {
        Layout.alignment: Qt.AlignTop
        text: summary.condensed.state === "unknown" ? "NOT REPORTED"
            : summary.condensed.state === "present" ? "PRESENT"
            : summary.condensed.state === "below_threshold" ? "BELOW THRESHOLD"
            : "NONE REPORTED"
        tone: summary.condensed.state === "unknown" ? "warning"
            : summary.condensed.state === "present" ? "accent" : "neutral"
    }

    ColumnLayout {
        Layout.fillWidth: true
        Layout.preferredWidth: 0
        spacing: 2

        Text {
            Layout.fillWidth: true
            text: Notation.rich(summary.condensed.headline)
            textFormat: Notation.textFormat(summary.condensed.headline)
            wrapMode: Text.WordWrap
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
            font.weight: Typography.medium
        }

        // The numbers the verdict is about, beside it rather than instead of
        // it: a sentence about a measurement should never be the only thing
        // on screen.
        Flow {
            Layout.fillWidth: true
            spacing: Metrics.spacing.l

            Row {
                visible: summary.condensed.known
                spacing: Metrics.spacing.xs

                Text {
                    text: "exact fraction"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: summary.condensed.fractionText
                    color: Theme.text
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                visible: summary.condensed.known
                spacing: Metrics.spacing.xs

                Text {
                    text: "reporting threshold"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: summary.condensed.thresholdText
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                visible: summary.condensed.species.length > 0
                spacing: Metrics.spacing.xs

                Text {
                    text: summary.condensed.state === "present"
                          ? "species" : "in the composition, below it"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: summary.condensed.species.join(", ")
                    color: summary.condensed.state === "present"
                           ? Theme.textSecondary : Theme.textMuted
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: summary.condensed.detail
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
