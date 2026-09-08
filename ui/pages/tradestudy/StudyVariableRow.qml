import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * One design variable: whether it varies, over what, and what that costs.
 *
 * The `effect` line is the point of this component. A user who does not know
 * that an area ratio cannot change a chamber temperature will build the study
 * that produces a hundred identical rows, and the definition validator will
 * refuse it after the fact. Saying so on the control is cheaper and kinder.
 *
 * The stage chip is the same information in one word, so a reader scanning the
 * list can see at a glance which variables are the expensive ones.
 */
ColumnLayout {
    id: row

    property var spec: ({})

    spacing: Metrics.spacing.xs

    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: false
        spacing: Metrics.spacing.s

        RFToggle {
            checked: row.spec.enabled
            onToggled: TradeStudy.setVariableEnabled(row.spec.key, checked)
        }

        Text {
            Layout.preferredWidth: 188
            text: row.spec.label
            elide: Text.ElideRight
            color: row.spec.enabled ? Theme.text : Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.body
        }

        RFStatusChip {
            text: row.spec.stageLabel
            tone: row.spec.affectsChemistry ? "warning" : "neutral"
            showDot: false
        }

        Item { Layout.fillWidth: true }

        RFBoundNumberField {
            Layout.preferredWidth: 108
            visible: row.spec.enabled
            label: "From" + (row.spec.unit !== "" ? "  [" + row.spec.unit + "]" : "")
            value: row.spec.start
            digits: 4
            decimals: 4
            step: 0.1
            showSteppers: false
            onValueEdited: function (v) {
                TradeStudy.setVariableRange(row.spec.key, v, row.spec.end,
                                            row.spec.count)
            }
        }

        RFBoundNumberField {
            Layout.preferredWidth: 108
            visible: row.spec.enabled
            label: "To"
            value: row.spec.end
            digits: 4
            decimals: 4
            step: 0.1
            showSteppers: false
            onValueEdited: function (v) {
                TradeStudy.setVariableRange(row.spec.key, row.spec.start, v,
                                            row.spec.count)
            }
        }

        RFBoundNumberField {
            Layout.preferredWidth: 84
            visible: row.spec.enabled
            label: "Values"
            value: row.spec.count
            digits: 0
            decimals: 0
            step: 1
            onValueEdited: function (v) {
                TradeStudy.setVariableRange(row.spec.key, row.spec.start,
                                            row.spec.end, v)
            }
        }

        Text {
            Layout.preferredWidth: 300
            visible: !row.spec.enabled
            text: row.spec.summary
            elide: Text.ElideRight
            color: Theme.textDisabled
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    Text {
        Layout.fillWidth: true
        Layout.leftMargin: 46
        Layout.bottomMargin: Metrics.spacing.xs
        text: row.spec.effect
              + (row.spec.note !== "" ? "  " + row.spec.note : "")
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }
}
