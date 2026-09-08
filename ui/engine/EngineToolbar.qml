import QtQuick
import "../theme"
import "../components"
import "model"

/*
 * A short bar over the canvas: the pointer tool, the view the canvas is
 * showing, and the view controls. Deliberately not a CAD toolbar - the canvas
 * is the tool, and everything here is either a mode or a way of framing it.
 */
Item {
    id: root

    property Item canvas: null
    property int viewIndex: 0

    implicitHeight: 38

    component ToolChip: Item {
        id: chip
        property string label: ""
        property bool active: false
        property string tooltip: ""
        signal toggled()

        implicitWidth: chipText.implicitWidth + Metrics.spacing.m
        implicitHeight: Metrics.controlHeightSmall
        width: implicitWidth
        height: implicitHeight

        Rectangle {
            anchors.fill: parent
            radius: Metrics.radius.m
            color: chip.active ? Theme.surfaceHover
                 : chipHover.hovered ? Theme.surfaceSubtle : "transparent"
            border.width: Metrics.hairline
            border.color: chip.active ? Theme.border : "transparent"
            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }

        Text {
            id: chipText
            anchors.centerIn: parent
            text: chip.label
            color: chip.active ? Theme.text : Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }

        HoverHandler { id: chipHover; cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: chip.toggled() }

        RFTooltip {
            text: chip.tooltip
            visible: chip.tooltip !== "" && chipHover.hovered
            x: (chip.width - width) / 2
            y: chip.height + 6
        }
    }

    // ---- left: pointer tool ---------------------------------------------

    RFSegmentedControl {
        id: toolSelector
        x: 0
        anchors.verticalCenter: parent.verticalCenter
        width: 152
        height: Metrics.controlHeightSmall + 2
        model: ["Select", "Connect"]
        currentIndex: root.canvas && root.canvas.tool === "connect" ? 1 : 0
        onSelected: function (index) {
            if (root.canvas)
                root.canvas.tool = index === 1 ? "connect" : "select"
        }
    }

    // ---- centre: canvas view --------------------------------------------

    RFSegmentedControl {
        id: viewSelector
        // Grouped with the pointer tool rather than centred: a centred control
        // needs twice the clearance, and the canvas keeps the width when the
        // workspace gets narrow. Below that width the selector is dropped -
        // two of its three views are not available yet anyway.
        visible: root.width > toolSelector.width + width + rightControls.width + 60
        anchors.left: toolSelector.right
        anchors.leftMargin: Metrics.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        width: 210
        height: Metrics.controlHeightSmall + 2
        model: ["Design", "Results", "Flow"]
        currentIndex: root.viewIndex
        disabledIndices: [1, 2]
        disabledNote: "Available after solver implementation"
        onSelected: function (index) { root.viewIndex = index }
    }

    // ---- right: view controls -------------------------------------------

    Row {
        id: rightControls
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.spacing.xs

        ToolChip {
            visible: root.width > 460
            anchors.verticalCenter: parent.verticalCenter
            label: "Grid"
            active: root.canvas ? root.canvas.gridVisible : true
            tooltip: "Show the alignment grid"
            onToggled: if (root.canvas) root.canvas.gridVisible = !root.canvas.gridVisible
        }

        ToolChip {
            visible: root.width > 460
            anchors.verticalCenter: parent.verticalCenter
            label: "Snap"
            active: root.canvas ? root.canvas.snapEnabled : true
            tooltip: "Snap components to the grid"
            onToggled: if (root.canvas) root.canvas.snapEnabled = !root.canvas.snapEnabled
        }

        ToolChip {
            visible: root.width > 520
            anchors.verticalCenter: parent.verticalCenter
            label: "Compact"
            active: EngineModel.detailLevel === "compact"
            tooltip: "Collapse components to a single row"
            onToggled: EngineModel.detailLevel =
                       EngineModel.detailLevel === "compact" ? "normal" : "compact"
        }

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: Metrics.hairline
            height: 16
            color: Theme.divider
        }

        RFIconButton {
            anchors.verticalCenter: parent.verticalCenter
            icon: "minus"
            tooltip: "Zoom out"
            onClicked: if (root.canvas) root.canvas.zoomOut()
        }

        Item {
            anchors.verticalCenter: parent.verticalCenter
            width: 46
            height: Metrics.controlHeightSmall

            Rectangle {
                anchors.fill: parent
                radius: Metrics.radius.m
                color: zoomHover.hovered ? Theme.surfaceSubtle : "transparent"
                Behavior on color { ColorAnimation { duration: Motion.fast } }
            }

            Text {
                anchors.centerIn: parent
                text: root.canvas ? Math.round(root.canvas.zoom * 100) + "%" : "100%"
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall
            }

            HoverHandler { id: zoomHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: if (root.canvas) root.canvas.resetZoom() }

            RFTooltip {
                text: "Reset to 100 %"
                visible: zoomHover.hovered
                x: (parent.width - width) / 2
                y: parent.height + 6
            }
        }

        RFIconButton {
            anchors.verticalCenter: parent.verticalCenter
            icon: "plus"
            tooltip: "Zoom in"
            onClicked: if (root.canvas) root.canvas.zoomIn()
        }

        /* One framing control, reading the selection. With something picked it
         * frames that; with nothing picked it frames the engine. A second
         * permanent button for the other case would spend bar width on a
         * distinction the user has already made by selecting. */
        ToolChip {
            anchors.verticalCenter: parent.verticalCenter
            label: root.canvas && root.canvas.hasSelection ? "Fit selection" : "Fit engine"
            tooltip: root.canvas && root.canvas.hasSelection
                     ? "Frame the selected components  (F)"
                     : "Frame the whole architecture  (Ctrl+0)"
            onToggled: if (root.canvas) root.canvas.fitSelection()
        }
    }
}
