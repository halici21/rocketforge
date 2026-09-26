import QtQuick
import "../theme"

/*
 * RFWorkspaceDrawer — the input drawer of the shared workspace grammar.
 *
 * Holds a workspace's inputs (solve-from mode, setup, filters) at the side of
 * the object it drives. Closed, it leaves an RFDrawerHandle that still names
 * the case -- `summary` is the owner's one-line reading of the inputs the
 * result was solved from ("Mach · 2.000 · γ 1.4") -- so collapsing the inputs
 * never hides which case is on screen. Open, it pushes the layout (the owner
 * binds `Layout.preferredWidth: drawer.implicitWidth`); the width changes at
 * once and only the panel's opacity and a few pixels of travel animate, so
 * the plots beside it re-lay out once, not every frame.
 *
 * The drawer owns `open` (one writer): the handle and the collapse button set
 * it, and an owner that must open it writes `drawer.open = true`.
 *
 * Default versus choice: an owner may bind `defaultOpen` (e.g. "open while
 * there is no valid result"). Until the reader opens or closes the drawer
 * themselves, `open` follows that default; after the first explicit choice
 * (handle, collapse button -- `setOpenByUser`), the choice wins for the life
 * of this drawer (the page's lifecycle). Owners that never set
 * `defaultOpen` see no change.
 */
Item {
    id: root

    property bool open: true
    // undefined: no default policy (the owner sets `open` itself)
    property var defaultOpen: undefined
    property bool userChosen: false
    function setOpenByUser(value) {
        root.userChosen = true
        root.open = value
    }
    function applyDefault() {
        if (!root.userChosen && root.defaultOpen !== undefined && root.open !== !!root.defaultOpen)
            root.open = !!root.defaultOpen
    }
    onDefaultOpenChanged: root.applyDefault()
    Component.onCompleted: root.applyDefault()
    property string title: "Inputs"
    property string summary: ""
    property string edge: "left"            // left | right
    property real drawerWidth: 300
    readonly property real handleWidth: 34
    default property alias content: panelBody.data

    implicitWidth: root.open ? root.drawerWidth : root.handleWidth

    onOpenChanged: {
        if (root.open && Motion.animated) {
            panel.arrive = 0
            arrival.restart()
        } else {
            panel.arrive = 1
        }
    }

    RFDrawerHandle {
        objectName: "workspaceDrawerHandle"
        anchors.fill: parent
        visible: !root.open
        title: root.title
        summary: root.summary
        edge: root.edge
        open: false
        onToggled: root.setOpenByUser(true)
    }

    Rectangle {
        id: panel
        objectName: "workspaceDrawerPanel"
        anchors.fill: parent
        visible: root.open
        radius: Metrics.radius.m
        color: Theme.surface
        border.width: Metrics.hairline
        border.color: Theme.border

        property real arrive: 1
        opacity: arrive
        transform: Translate {
            x: (1 - panel.arrive) * (root.edge === "left" ? -Motion.panelShift : Motion.panelShift)
        }
        NumberAnimation {
            id: arrival
            target: panel
            property: "arrive"
            to: 1
            duration: Motion.panel
            easing.type: Motion.standard
        }

        Item {
            id: head
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 38

            Text {
                anchors.left: parent.left
                anchors.leftMargin: Metrics.spacing.m
                anchors.right: collapse.left
                anchors.rightMargin: Metrics.spacing.s
                anchors.verticalCenter: parent.verticalCenter
                text: root.title.toUpperCase()
                elide: Text.ElideRight
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.weight: Typography.medium
                font.letterSpacing: Typography.sectionTracking
            }

            RFToolButton {
                id: collapse
                objectName: "workspaceDrawerCollapse"
                anchors.right: parent.right
                anchors.rightMargin: Metrics.spacing.s
                anchors.verticalCenter: parent.verticalCenter
                text: root.edge === "left" ? "‹" : "›"
                tooltip: "Hide " + root.title.toLowerCase() + " -- the handle keeps the case in view"
                onClicked: root.setOpenByUser(false)
            }
        }

        Item {
            id: panelBody
            anchors.top: head.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: Metrics.spacing.m
            anchors.rightMargin: Metrics.spacing.m
            anchors.bottomMargin: Metrics.spacing.m
        }
    }
}
