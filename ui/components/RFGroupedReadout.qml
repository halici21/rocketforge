import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * RFGroupedReadout - a calculator's solved state as columns of labelled
 * groups, each a list of "label   value unit" rows.
 *
 * Placed inside the page's own RowLayout: the root is a Repeater, so each
 * column is laid out by that row exactly as before. `results` is the
 * controller's list unchanged (label, value, unit, group, available,
 * emphasis); a row joins the group it names, and an empty group is hidden.
 * Clicking a value asks for it to be copied (`copyRequested`), which the page
 * passes to its controller. Used by the Fanno, Rayleigh, Prandtl-Meyer and
 * Mass Flow calculators; the Nozzle and Oblique Shock readouts are laid out
 * differently and keep their own.
 */
Repeater {
    id: root

    // Group names, column by column: [["Flow", "Starred state"], ["Choking limit"]].
    property var columns: []
    property var results: []
    property int labelWidth: 210
    property int rowHeight: 25
    // Clip a label that does not fit; RichText does not elide.
    property bool clipLabels: false
    // An optional note under one group's heading.
    property string noteGroup: ""
    property bool noteVisible: false
    property string noteText: ""

    signal copyRequested(string value)

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < root.results.length; ++i)
            if (root.results[i].group === group)
                out.push(root.results[i])
        return out
    }

    model: root.columns

    delegate: ColumnLayout {
        id: column
        required property var modelData

        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop
        spacing: Metrics.spacing.m

        Repeater {
            model: column.modelData

            delegate: ColumnLayout {
                id: group
                required property var modelData
                readonly property var groupRows: root.rowsIn(modelData)

                Layout.fillWidth: true
                spacing: Metrics.spacing.xs
                visible: groupRows.length > 0

                RFSectionLabel { text: Notation.sectionRich(group.modelData); textFormat: Notation.textFormat(group.modelData) }

                Text {
                    Layout.fillWidth: true
                    visible: root.noteGroup !== "" && group.modelData === root.noteGroup && root.noteVisible
                    readonly property string plainText: root.noteText
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Repeater {
                    model: group.groupRows

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.rowHeight
                        spacing: Metrics.spacing.m

                        Text {
                            Layout.preferredWidth: root.labelWidth
                            text: Notation.rich(modelData.label)
                            textFormat: Notation.textFormat(modelData.label)
                            elide: Text.ElideRight
                            clip: root.clipLabels
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.body
                        }

                        Text {
                            Layout.fillWidth: true
                            text: modelData.value
                                  + (modelData.unit ? " " + modelData.unit : "")
                            color: modelData.available ? Theme.text
                                                       : Theme.textMuted
                            font.family: Typography.mono
                            font.pixelSize: modelData.emphasis
                                ? Typography.readoutMedium
                                : Typography.readoutSmall
                            font.weight: modelData.emphasis
                                ? Typography.medium : Typography.regular

                            TapHandler {
                                onSingleTapped: root.copyRequested(modelData.value)
                            }
                        }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
