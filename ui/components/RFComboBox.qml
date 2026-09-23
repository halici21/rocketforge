import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * A selector that reads as a field, not as a button: the same label-and-rule
 * anatomy as RFNumberField, so a column of mixed inputs shares one silhouette.
 * The Qt ComboBox underneath supplies keyboard handling and the popup; every
 * painted part of it is replaced.
 */
Item {
    id: root

    property string label: ""
    property alias model: box.model
    property alias currentIndex: box.currentIndex
    readonly property alias currentText: box.currentText

    /*
     * Raised only when a person picks an item, never by a programmatic index
     * change. That distinction is what lets a caller bind `currentIndex` to a
     * backend property *and* write back to it: binding plus a write from
     * `onCurrentIndexChanged` loops through the binding, and this does not.
     */
    signal activated(int index)

    implicitWidth: 180
    implicitHeight: labelText.implicitHeight + Metrics.spacing.xs
                    + box.implicitHeight + Metrics.spacing.xs + 2

    Text {
        id: labelText
        text: Notation.rich(root.label)
        textFormat: Notation.textFormat(root.label)
        visible: root.label !== ""
        color: root.enabled ? Theme.textSecondary : Theme.textDisabled
        font.family: Typography.sans
        font.pixelSize: Typography.inputLabel
        elide: Text.ElideRight
        clip: true              // RichText does not elide
        width: root.width
    }

    ComboBox {
        id: box
        anchors.top: labelText.visible ? labelText.bottom : parent.top
        anchors.topMargin: labelText.visible ? Metrics.spacing.xs : 0
        width: root.width
        implicitHeight: Metrics.touchTarget
        padding: 0
        font.family: Typography.sans
        font.pixelSize: Typography.body

        onActivated: function (index) { root.activated(index) }

        background: Item {}

        contentItem: Text {
            // The selected option can be a quantity ("Specific impulse  Isp"),
            // so it gets the same notation as the list below.
            text: Notation.rich(box.displayText)
            textFormat: Notation.textFormat(box.displayText)
            clip: true
            color: root.enabled ? Theme.text : Theme.textDisabled
            font: box.font
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            rightPadding: 20
        }

        indicator: RFIcon {
            x: box.width - width
            y: (box.height - height) / 2
            name: "chevron-down"
            width: 14
            height: 14
            color: box.popup.visible ? Theme.accent : Theme.textMuted
            rotation: box.popup.visible ? 180 : 0
            Behavior on rotation { NumberAnimation { duration: Motion.base; easing.type: Motion.standard } }
        }

        popup: Popup {
            y: box.height + Metrics.spacing.s
            width: box.width
            implicitHeight: Math.min(contentItem.implicitHeight + 8, 260)
            padding: 4

            background: Rectangle {
                color: Theme.surfaceElevated
                radius: Metrics.radius.l
                border.width: Metrics.hairline
                border.color: Theme.border
            }

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: box.popup.visible ? box.delegateModel : null
                currentIndex: box.highlightedIndex
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}
            }

            enter: Transition {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Motion.fast }
            }
            exit: Transition {
                NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Motion.fast }
            }
        }

        delegate: ItemDelegate {
            required property var modelData
            required property int index

            width: ListView.view ? ListView.view.width : 0
            height: 30
            padding: 0

            background: Rectangle {
                radius: Metrics.radius.m
                color: box.highlightedIndex === index ? Theme.surfaceHover : "transparent"
            }

            contentItem: Row {
                spacing: Metrics.spacing.s
                leftPadding: Metrics.spacing.s

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: Notation.rich(modelData)
                    textFormat: Notation.textFormat(modelData)
                    clip: true
                    color: box.currentIndex === index ? Theme.text : Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                    width: parent.width - 30
                    elide: Text.ElideRight
                }
            }

            RFIcon {
                anchors.right: parent.right
                anchors.rightMargin: Metrics.spacing.s
                anchors.verticalCenter: parent.verticalCenter
                visible: box.currentIndex === index
                name: "check"
                width: 13
                height: 13
                color: Theme.accent
            }
        }
    }

    Rectangle {
        anchors.top: box.bottom
        anchors.topMargin: Metrics.spacing.xs
        width: root.width
        height: box.activeFocus || box.popup.visible ? 1.5 : Metrics.hairline
        color: !root.enabled ? Theme.divider
             : (box.activeFocus || box.popup.visible) ? Theme.accent
             : hover.hovered ? Theme.borderStrong
             : Theme.border

        Behavior on color { ColorAnimation { duration: Motion.fast } }
        Behavior on height { NumberAnimation { duration: Motion.fast } }
    }

    HoverHandler {
        id: hover
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}
