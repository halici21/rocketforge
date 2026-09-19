import QtQuick
import QtQuick.Layouts
import "../../ui/theme"
import "../../ui/components"

Rectangle {
    width: 980
    height: 320
    color: Theme.background

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 22

        Repeater {
            model: [64, 24, 17]

            RowLayout {
                id: sizeRow
                required property int modelData
                spacing: 36

                Text {
                    Layout.preferredWidth: 46
                    text: sizeRow.modelData + "px"
                    color: Theme.textMuted
                    font.family: Typography.mono
                    font.pixelSize: 12
                }

                Repeater {
                    model: ["home", "flow", "chem", "prop", "trade", "fluid",
                            "reference", "nozzle"]

                    ColumnLayout {
                        id: cellCol
                        required property string modelData
                        spacing: 6

                        RFIcon {
                            Layout.alignment: Qt.AlignHCenter
                            name: cellCol.modelData
                            Layout.preferredWidth: sizeRow.modelData
                            Layout.preferredHeight: sizeRow.modelData
                            width: sizeRow.modelData
                            height: sizeRow.modelData
                            strokeWidth: sizeRow.modelData >= 64 ? 1.1 : 1.4
                            color: Theme.text
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            visible: sizeRow.modelData === 64
                            text: cellCol.modelData
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: 11
                        }
                    }
                }
            }
        }
    }
}
