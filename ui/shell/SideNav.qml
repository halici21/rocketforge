import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"
import "../data"

/*
 * The Browser, Analysis Experience R2: a narrow family rail plus a
 * contextual module drawer, replacing the permanent all-pages list every
 * capture in docs/design/ANALYSIS_EXPERIENCE_R2_CURRENT_AUDIT.md flagged
 * as navigation noise (17 destinations shown at once, regardless of what
 * the user is doing).
 *
 * Progressive disclosure, not a redesign of what each row shows: a family
 * with exactly one module (Thermochemistry, Rocket Performance, Trade
 * Study, Reference) opens that module directly from the rail -- there is
 * no second click to a drawer with one row in it. A family with several
 * modules (Compressible Flow, Fluids and Feed) opens a contextual drawer
 * scoped to that family alone, never every family's modules at once.
 *
 * External API (currentIndex, engineModeActive, selected(index),
 * engineModeRequested()) is unchanged from the pre-R2 SideNav, so Main.qml
 * needed no edit for this swap. Engine Design's own entry point is the
 * TopBar's Analysis/Engine Design switch, already the primary route into
 * that mode -- this rail no longer duplicates it, and no longer shows
 * Engine Design's own future-module roadmap, which is that mode's own
 * concern (ui/engine/), not this one's.
 */
Item {
    id: root

    property int currentIndex: 0
    property bool engineSectionExpanded: false
    property bool engineModeActive: false

    signal selected(int index)
    signal engineModeRequested()

    function stateFor(key) {
        return WorkspaceState.stateFor(key)
    }

    // -1 = no drawer open.
    //
    // The drawer only ever opens from an explicit rail click. An earlier
    // revision of this file auto-opened it whenever currentIndex moved
    // into a drawer-owning family, on the theory that it restored context
    // -- opening the real capture showed it instead parked a 176px panel
    // on top of the workspace's own input rail every time the user landed
    // on a compressible-flow module. Navigation only ever CLOSES it now.
    property int openDrawerFamily: -1

    function familyNeedsDrawer(family) {
        return Navigation.directTargetOf(family) === -1
    }

    function syncDrawerToIndex(index) {
        openDrawerFamily = -1
    }

    onCurrentIndexChanged: syncDrawerToIndex(currentIndex)
    Component.onCompleted: syncDrawerToIndex(currentIndex)

    function activateFamily(familyIndex) {
        var family = Navigation.families[familyIndex]
        var direct = Navigation.directTargetOf(family)
        if (direct !== -1) {
            openDrawerFamily = -1
            root.selected(direct)
            return
        }
        openDrawerFamily = (openDrawerFamily === familyIndex) ? -1 : familyIndex
    }

    clip: true
    activeFocusOnTab: true

    Keys.onUpPressed: {
        var next = Math.max(0, currentIndex - 1)
        if (next !== currentIndex) root.selected(next)
    }
    Keys.onDownPressed: {
        var next = Math.min(Navigation.items.length - 1, currentIndex + 1)
        if (next !== currentIndex) root.selected(next)
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ==== the family rail: always visible, fixed width ================
        Item {
            id: rail
            Layout.preferredWidth: 64
            Layout.fillHeight: true

            Rectangle {
                anchors.right: parent.right
                width: Metrics.hairline
                height: parent.height
                color: Theme.divider
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: Metrics.spacing.m
                spacing: Metrics.spacing.xs

                RailCell {
                    Layout.fillWidth: true
                    label: "HOME"
                    icon: "home"
                    current: root.currentIndex === 0 && !root.engineModeActive
                    onActivated: { root.openDrawerFamily = -1; root.selected(0) }
                }

                Item { Layout.preferredHeight: Metrics.spacing.s }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.leftMargin: Metrics.spacing.s
                    Layout.rightMargin: Metrics.spacing.s
                    Layout.preferredHeight: Metrics.hairline
                    color: Theme.divider
                }

                Item { Layout.preferredHeight: Metrics.spacing.s }

                Repeater {
                    model: Navigation.families

                    delegate: RailCell {
                        required property var modelData
                        required property int index

                        Layout.fillWidth: true
                        label: modelData.short
                        icon: modelData.icon !== undefined ? modelData.icon : ""
                        familyKey: modelData.key !== undefined ? modelData.key : ""
                        current: !root.engineModeActive && (
                                     root.openDrawerFamily === index
                                     || Navigation.familyOfIndex(root.currentIndex) === index)
                        onActivated: root.activateFamily(index)
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }


    }

    // ==== the contextual module drawer: a floating popup, not a layout
    // participant -- it must not permanently reserve width the way the
    // old permanent rail did, so it overlays the workspace instead of
    // pushing it. Opens only for a multi-module family (Compressible
    // Flow, Fluids and Feed); every other rail entry navigates directly
    // and this stays closed.
    Popup {
        id: drawerPopup
        parent: root
        x: 64
        y: 0
        width: 176
        height: root.height
        visible: root.openDrawerFamily !== -1
        padding: 0
        closePolicy: Popup.CloseOnEscape

        background: Rectangle {
            color: Theme.surfaceElevated
            border.width: Metrics.hairline
            border.color: Theme.border
        }

        Flickable {
            anchors.fill: parent
            contentWidth: width
            contentHeight: drawerColumn.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: RFScrollBar {}

            ColumnLayout {
                id: drawerColumn
                width: parent.width
                spacing: 0

                readonly property var family: root.openDrawerFamily !== -1
                    ? Navigation.families[root.openDrawerFamily] : null

                Item { Layout.preferredHeight: Metrics.spacing.m }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: Metrics.spacing.m
                    Layout.rightMargin: Metrics.spacing.m

                    Text {
                        Layout.fillWidth: true
                        text: drawerColumn.family ? drawerColumn.family.label : ""
                        elide: Text.ElideRight
                        color: Theme.text
                        font.family: Typography.sans
                        font.pixelSize: Typography.groupLabel + 1
                        font.weight: Typography.medium
                    }

                    RFIconButton {
                        icon: "close"
                        size: 22
                        iconSize: 12
                        onClicked: root.openDrawerFamily = -1
                    }
                }

                Item { Layout.preferredHeight: Metrics.spacing.m }

                Repeater {
                    model: drawerColumn.family ? drawerColumn.family.groups : []

                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 0

                        RFSectionLabel {
                            visible: modelData.label !== ""
                            text: modelData.label
                            Layout.leftMargin: Metrics.spacing.m
                            Layout.rightMargin: Metrics.spacing.m
                            Layout.topMargin: Metrics.spacing.s
                            Layout.bottomMargin: Metrics.spacing.xs
                        }

                        Repeater {
                            model: modelData.items

                            delegate: Loader {
                                required property var modelData
                                Layout.fillWidth: true
                                readonly property var itemData: Navigation.items[modelData]
                                readonly property bool hasStatus:
                                    drawerColumn.family ? drawerColumn.family.hasStatus : false
                                sourceComponent: hasStatus ? statusRow : plainRow

                                Component {
                                    id: plainRow
                                    RFNavItem {
                                        width: parent ? parent.width : 200
                                        label: itemData ? itemData.label : ""
                                        current: modelData === root.currentIndex
                                        onActivated: {
                                            root.selected(modelData)
                                            root.openDrawerFamily = -1
                                        }
                                    }
                                }
                                Component {
                                    id: statusRow
                                    RFBrowserItem {
                                        width: parent ? parent.width : 200
                                        readonly property var state: root.stateFor(itemData ? itemData.key : "")
                                        label: itemData ? itemData.label : ""
                                        stateText: state.text
                                        stale: state.stale
                                        current: modelData === root.currentIndex
                                        onActivated: {
                                            root.selected(modelData)
                                            root.openDrawerFamily = -1
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Item { Layout.preferredHeight: Metrics.spacing.l }
            }
        }
    }

    // One rail cell: icon, label, status dot, hover tooltip. The
    // family-rail analogue of RFNavItem, sized for a 64px column.
    // Phase 1: aerospace-grade status indicators and refined ergonomics.
    component RailCell: Item {
        id: cell
        property string label: ""
        property string icon: ""
        property string familyKey: ""
        property bool current: false
        signal activated()

        // Live family state from WorkspaceState -- drives the status dot
        // and the tooltip summary line. Re-evaluated reactively whenever
        // a controller emits resultsChanged, so no polling and no cost.
        readonly property var familyStatus: cell.familyKey !== ""
            ? WorkspaceState.familyState(cell.familyKey)
            : { hasResult: false, stale: false, summary: "" }

        implicitHeight: 56

        Rectangle {
            anchors.fill: parent
            anchors.leftMargin: Metrics.spacing.xs
            anchors.rightMargin: Metrics.spacing.xs
            radius: Metrics.radius.m
            color: cell.current ? Theme.surfaceHover
                 : cellMouse.containsMouse ? Theme.surface : "transparent"
            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }

        // Active indicator bar -- wider and rounded for aerospace-console feel.
        Rectangle {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: 3
            height: cell.current ? 22 : 0
            radius: 1.5
            color: Theme.accent
            opacity: cell.current ? 1 : 0
            Behavior on height { NumberAnimation { duration: Motion.base; easing.type: Motion.standard } }
            Behavior on opacity { NumberAnimation { duration: Motion.base } }
        }

        Column {
            anchors.centerIn: parent
            spacing: 3

            // Icon + status dot overlay
            Item {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: cell.icon !== ""
                width: 20
                height: 20

                RFIcon {
                    anchors.centerIn: parent
                    name: cell.icon
                    width: 20
                    height: 20
                    strokeWidth: cell.current ? 1.8 : 1.5
                    color: cell.current ? Theme.text
                         : cellMouse.containsMouse ? Theme.textSecondary : Theme.textMuted

                    Behavior on color { ColorAnimation { duration: Motion.fast } }
                }

                // Status dot: top-right corner of the icon, 5px diameter.
                // Visible only when a family has a persistent solved result.
                Rectangle {
                    width: 5; height: 5; radius: 2.5
                    x: parent.width - 1
                    y: -1
                    visible: cell.familyStatus.hasResult
                    color: cell.familyStatus.stale ? Theme.warning : Theme.success
                    Behavior on color { ColorAnimation { duration: Motion.base } }
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: cell.label
                color: cell.current ? Theme.text
                     : cellMouse.containsMouse ? Theme.textSecondary : Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.weight: cell.current ? Typography.semibold : Typography.medium
                font.letterSpacing: 0.6
                font.capitalization: Font.AllUppercase

                Behavior on color { ColorAnimation { duration: Motion.fast } }
            }
        }

        MouseArea {
            id: cellMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: cell.activated()
        }

        // Tooltip: family name and live solve summary on hover.
        RFTooltip {
            text: {
                var t = cell.label
                if (cell.familyStatus.hasResult && cell.familyStatus.summary !== "")
                    t += " \u2014 " + cell.familyStatus.summary
                return t
            }
            visible: cellMouse.containsMouse
            x: cell.width + Metrics.spacing.xs
            y: (cell.height - height) / 2
        }
    }
}
