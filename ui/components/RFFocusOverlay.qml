import QtQuick
import RocketForge 1.0
import "../theme"

/*
 * RFFocusOverlay — full focus on one plot of a small-multiple set.
 *
 * The plot is rebuilt at workspace size from the owner's `content` component
 * (the same series, the same solved data -- nothing is solved or resampled)
 * with the full analysis tools; the rest of the workspace recedes behind a
 * dimmed backdrop so the context is still there, and still the same. Built
 * only while open (Loader), destroyed on close.
 *
 * Esc is layered: the focused content may consume it first (its lens or zoom
 * returns to the full range), then Esc closes the focus. The content opts in
 * by defining `function handleEscape()` returning true when it used the key.
 *
 * Built on first use and then kept (the Inspector drawer's rule): building
 * the plot on every open and destroying it on every close cost about a third
 * of a megabyte per round trip that the engine did not return (measured,
 * acceptance/workspace_consolidation/audit/memory_split_focus.json). A kept
 * content is told it is being shown again (`reopened()`, if it defines one)
 * so it starts from the full range; it is destroyed with its page.
 */
Item {
    id: root

    property bool opened: false
    property string title: ""
    property string subtitle: ""
    property Component content: null
    // Anything the content needs to know which plot it is (an index, a key).
    property var context: ({})
    readonly property Item item: loader.item

    function show(title, subtitle, component, context) {
        root.title = title
        root.subtitle = subtitle || ""
        root.context = context !== undefined ? context : ({})
        var same = root.content === component
        root.content = component
        root.opened = true
        if (same && loader.item && loader.item.reopened)
            loader.item.reopened()
        exit.stop()
        if (Motion.animated) {
            root.arrive = 0
            enter.restart()
        } else {
            root.arrive = 1
        }
        root.forceActiveFocus()
    }
    function hide() {
        if (!root.opened)
            return
        root.opened = false
        enter.stop()
        if (Motion.animated)
            exit.restart()
        else
            root.arrive = 0
    }

    property real arrive: 0
    visible: root.opened || exit.running
    z: 40

    NumberAnimation {
        id: enter
        target: root
        property: "arrive"
        to: 1
        duration: Motion.focus
        easing.type: Motion.standard
    }
    NumberAnimation {
        id: exit
        target: root
        property: "arrive"
        to: 0
        duration: Motion.panel
        easing.type: Easing.InCubic
    }

    Shortcut {
        sequence: "Esc"
        enabled: root.opened
        onActivated: {
            var used = loader.item && loader.item.handleEscape ? loader.item.handleEscape() : false
            if (!used)
                root.hide()
        }
    }

    // The context, receded: dimmed, and not clickable through.
    Rectangle {
        objectName: "focusBackdrop"
        anchors.fill: parent
        color: Theme.background
        opacity: 0.8 * root.arrive
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            hoverEnabled: true
            onClicked: root.hide()
            onWheel: function (w) { w.accepted = true }
        }
    }

    Rectangle {
        id: card
        objectName: "focusCard"
        anchors.fill: parent
        anchors.margins: Metrics.spacing.l
        radius: Metrics.radius.l
        color: Theme.surface
        border.width: Metrics.hairline
        border.color: Theme.borderStrong
        opacity: root.arrive
        scale: 0.985 + 0.015 * root.arrive

        MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }   // clicks stay in the card

        Item {
            id: cardHead
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 44

            Column {
                anchors.left: parent.left
                anchors.leftMargin: Metrics.spacing.l
                anchors.verticalCenter: parent.verticalCenter
                spacing: 1
                Text {
                    text: Notation.rich(root.title)
                    textFormat: Notation.textFormat(root.title)
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                    font.weight: Typography.medium
                }
                Text {
                    visible: root.subtitle !== ""
                    text: root.subtitle
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFToolButton {
                objectName: "focusClose"
                anchors.right: parent.right
                anchors.rightMargin: Metrics.spacing.m
                anchors.verticalCenter: parent.verticalCenter
                text: "Close  ·  Esc"
                tooltip: "Back to the overview -- the plots behind are unchanged"
                onClicked: root.hide()
            }
        }

        Loader {
            id: loader
            anchors.top: cardHead.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: Metrics.spacing.m
            active: root.content !== null && (root.visible || loader.item !== null)
            sourceComponent: root.content
        }
    }
}
