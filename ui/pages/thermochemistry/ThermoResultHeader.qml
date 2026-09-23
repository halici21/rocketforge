import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * What the displayed result is for.
 *
 * Every field here comes from the *result's own* condition snapshot, never
 * from the input form. Editing an input after solving therefore cannot
 * relabel the result: the header keeps saying O/F 3.4 while the form says
 * 3.6, and the stale chip beside the status says the two have diverged.
 *
 * That is the whole point of the component. A result detached from its
 * conditions is the easiest way for a chemistry number to be read as an
 * answer to a question nobody asked.
 */
ColumnLayout {
    id: header

    spacing: Metrics.spacing.s

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        Text {
            text: Notation.rich(Thermochemistry.resultHeadline)
            textFormat: Notation.textFormat(Thermochemistry.resultHeadline)
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.groupLabel + 2
            font.weight: Typography.medium
        }

        RFStatusChip {
            text: Thermochemistry.provenanceSummary.provider
            showDot: false
        }

        RFStatusChip {
            text: Thermochemistry.provenanceSummary.model
            showDot: false
        }

        Item { Layout.fillWidth: true }
    }

    Text {
        Layout.fillWidth: true
        visible: Thermochemistry.resultStale
        text: "The inputs have changed since this result was calculated. "
              + "The conditions above are the ones that produced it; press Calculate "
              + "to solve the current case."
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.warning
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }

    Flow {
        Layout.fillWidth: true
        spacing: Metrics.spacing.l

        Repeater {
            model: Thermochemistry.resultConditions

            delegate: Row {
                required property var modelData
                spacing: Metrics.spacing.xs

                Text {
                    text: Notation.rich(modelData.label)
                    textFormat: Notation.textFormat(modelData.label)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: modelData.value
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    visible: modelData.note !== ""
                    text: "(" + modelData.note + ")"
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
