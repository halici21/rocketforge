import QtQuick
import RocketForge 1.0
import "../theme"

/*
 * RFTableToolbar — the context toolbar of an interactive RFEngineeringTable.
 *
 * The table's own grammar in words: Select / Range tools, visual zoom, the
 * analysis lens with its breadcrumb ("Full table › M 1.80 – 2.20"), and the
 * owner's Pin and Copy for the chosen rows. Like RFPlotToolbar it never owns
 * state: the table holds tool, zoom, range and lens; the owner decides what
 * Pin and Copy mean.
 */
Row {
    id: bar

    required property Item table
    property bool canPin: false
    property bool canCopy: false
    property string pinText: "Pin rows"
    property string copyText: "Copy rows"

    signal pinRequested()
    signal copyRequested()

    objectName: "tableToolbar"
    spacing: Metrics.spacing.xs

    // "M 1.80 – 2.20": the key column's symbol and the lens's first and last
    // values exactly as the table shows them.
    function spanText(first, last) {
        if (!bar.table || first < 0 || last < first)
            return ""
        var head = bar.table.columns.length > 0 ? bar.table.columns[0].label : ""
        return head + " " + bar.table.cellText(first, 0) + " – " + bar.table.cellText(last, 0)
    }

    Repeater {
        model: [
            { tool: "select", text: "Select", tip: "Click a row; Shift + click extends a range; ↑ ↓ move" },
            { tool: "range", text: "Range", tip: "Drag across rows to select a range (whole rows)" }
        ]
        delegate: RFToolButton {
            required property var modelData
            text: modelData.text
            tooltip: modelData.tip
            checked: bar.table.tool === modelData.tool
            onClicked: bar.table.tool = modelData.tool
        }
    }

    Item { width: Metrics.spacing.s; height: 1 }

    RFToolButton {
        text: "−"
        tooltip: "Smaller rows (Ctrl + wheel, Ctrl + −)"
        enabled: bar.table.zoom > bar.table.minZoom + 0.001
        onClicked: bar.table.setZoom(bar.table.zoom - 0.1)
    }
    RFToolButton {
        objectName: "tableZoomReset"
        text: Math.round(bar.table.zoom * 100) + "%"
        tooltip: "Visual zoom only -- the values do not change. Click for 100% (Ctrl + 0)"
        onClicked: bar.table.setZoom(1.0)
    }
    RFToolButton {
        text: "+"
        tooltip: "Larger rows (Ctrl + wheel, Ctrl + +)"
        enabled: bar.table.zoom < bar.table.maxZoom - 0.001
        onClicked: bar.table.setZoom(bar.table.zoom + 0.1)
    }

    Item { width: Metrics.spacing.s; height: 1 }

    RFToolButton {
        objectName: "tableLensButton"
        text: "Lens"
        tooltip: "Show only the selected range, larger (Return). Esc returns to the full table"
        enabled: bar.table.hasRange && !bar.table.lensActive
        onClicked: bar.table.enterLens(bar.table.rangeFirst, bar.table.rangeLast)
    }

    // The breadcrumb, only while a lens is open.
    Loader {
        anchors.verticalCenter: parent.verticalCenter
        active: bar.table.lensActive
        visible: active
        sourceComponent: Row {
            objectName: "tableBreadcrumb"
            spacing: 6
            leftPadding: Metrics.spacing.xs
            rightPadding: Metrics.spacing.xs

            Text {
                text: "Full table"
                color: crumb.containsMouse ? Theme.accent : Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.underline: crumb.containsMouse
                MouseArea {
                    id: crumb
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: bar.table.exitLens()
                }
            }
            Text { text: "›"; color: Theme.textMuted; font.pixelSize: Typography.meta }
            Text {
                text: Notation.rich(bar.spanText(bar.table.lensFirst, bar.table.lensLast))
                textFormat: Text.RichText
                color: Theme.accent
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }

    RFToolButton {
        visible: bar.canPin
        text: bar.pinText
        tooltip: "Keep these rows exactly as shown, with the table they came from, for comparison"
        enabled: bar.table.hasRange || bar.table.lensActive || bar.table.selectedRow >= 0
        onClicked: bar.pinRequested()
    }
    RFToolButton {
        visible: bar.canCopy
        text: bar.copyText
        tooltip: "Copy the selected rows (else the lens, else the whole table) as tab-separated text"
        onClicked: bar.copyRequested()
    }
}
