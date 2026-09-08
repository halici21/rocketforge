import QtQuick
import "../theme"
import "../components"
import "visuals"
import "model"

/*
 * The open-document bar. Tabs answer "what is open"; the breadcrumb in the
 * application bar answers "where am I". Keeping those separate is what stops
 * this from turning into browser chrome: no tab shapes, no rounded shoulders,
 * just a row of documents with the current one marked by an accent rule.
 */
Item {
    id: root

    property var documents: []
    property int currentIndex: 0
    property bool focusMode: false

    signal selected(int index)
    signal closed(int index)
    signal focusModeToggled()

    implicitHeight: 30

    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: Metrics.hairline
        color: Theme.divider
    }

    /* Clearing the surrounding panels in one gesture. It lives on the document
     * bar because that is the line the workspace is framed by, and because a
     * floating control over a drawing is the kind of chrome this mode exists to
     * get rid of. */
    RFIconButton {
        id: focusButton
        anchors.right: parent.right
        anchors.rightMargin: Metrics.spacing.s
        anchors.verticalCenter: parent.verticalCenter
        size: 22
        iconSize: 13
        icon: "panel-left"
        active: root.focusMode
        tooltip: root.focusMode ? "Restore the side panels  (Ctrl+Shift+F)"
                                : "Focus the workspace  (Ctrl+Shift+F)"
        onClicked: root.focusModeToggled()
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: Metrics.spacing.s
        anchors.right: focusButton.left
        anchors.rightMargin: Metrics.spacing.xs
        height: parent.height
        clip: true

        Repeater {
            model: root.documents

            delegate: Item {
                id: tab
                required property var modelData
                required property int index

                readonly property bool current: index === root.currentIndex
                readonly property bool closable: modelData.kind !== "layout"
                readonly property string tabTitle: {
                    EngineModel.graphRevision
                    return modelData.nodeId ? EngineModel.nodeName(modelData.nodeId)
                                            : modelData.title
                }

                width: Math.min(200, label.implicitWidth + glyphItem.width + 54)
                height: root.height

                Rectangle {
                    anchors.fill: parent
                    anchors.topMargin: 2
                    anchors.bottomMargin: 1
                    radius: Metrics.radius.m
                    color: tab.current ? Theme.surface
                         : tabHover.hovered ? Theme.surfaceHover : "transparent"
                    Behavior on color { ColorAnimation { duration: Motion.fast } }
                }

                // Current document marker.
                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: tab.current ? parent.width - Metrics.spacing.m : 0
                    height: 2
                    color: Theme.accent
                    Behavior on width {
                        NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
                    }
                }

                ComponentGlyph {
                    id: glyphItem
                    x: Metrics.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    width: tab.modelData.glyph ? 16 : 0
                    height: 16
                    visible: width > 0
                    glyph: tab.modelData.glyph ? tab.modelData.glyph : ""
                    color: tab.current ? Theme.text : Theme.textMuted
                }

                Text {
                    id: label
                    anchors.left: glyphItem.visible ? glyphItem.right : parent.left
                    anchors.leftMargin: glyphItem.visible ? Metrics.spacing.s : Metrics.spacing.m
                    anchors.right: closeButton.left
                    anchors.rightMargin: Metrics.spacing.xs
                    anchors.verticalCenter: parent.verticalCenter
                    text: tab.tabTitle
                    elide: Text.ElideRight
                    color: tab.current ? Theme.text : Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                    font.weight: tab.current ? Typography.medium : Typography.regular
                    Behavior on color { ColorAnimation { duration: Motion.fast } }
                }

                RFIconButton {
                    id: closeButton
                    anchors.right: parent.right
                    anchors.rightMargin: Metrics.spacing.xs + 2
                    anchors.verticalCenter: parent.verticalCenter
                    visible: tab.closable
                    size: 18
                    iconSize: 11
                    icon: "close"
                    opacity: tabHover.hovered || tab.current ? 1 : 0
                    onClicked: root.closed(tab.index)

                    Behavior on opacity { NumberAnimation { duration: Motion.fast } }
                }

                HoverHandler { id: tabHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: root.selected(tab.index) }
            }
        }
    }
}
