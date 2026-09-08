import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * RFEngineeringTable - a dense numeric table for engineering data.
 *
 * Knows nothing about compressible flow, or about any physics. It is handed a
 * Qt table model and a column width policy and it renders rows; the same
 * component is meant to serve the normal-shock, Prandtl-Meyer, Fanno and
 * Rayleigh tables when those arrive, without modification.
 *
 * Design intent: an aerospace tool, not a spreadsheet. Numbers are right
 * aligned in tabular figures so digits line up down the column, the header
 * stays put while the body scrolls, and the only colour in the grid is the
 * hairline rule. A physically special row - the sonic line - is marked with a
 * thin accent edge rather than a filled highlight, so it reads as an
 * annotation rather than a selection.
 */
Item {
    id: root

    // The QAbstractTableModel to render.
    property var model: null
    // [{ key, label }] - only used for header text, alignment and width hints.
    // A column may carry `align: "left"`; anything else keeps the right
    // alignment a numeric column needs. Added for the composition table, whose
    // first two columns are a species name and a phase: right-aligning "H2O"
    // against "CO2" reads as a numeric column that has lost its digits.
    property var columns: []

    function alignsLeft(column) {
        return column >= 0 && column < columns.length
               && columns[column].align === "left"
    }
    // Row index to mark as physically special, or -1.
    property int markedRow: -1
    property string markedLabel: "SONIC"
    // A second critical row, for a table that has one. Rayleigh flow does: the
    // static temperature peaks at M = 1/sqrt(gamma) and the stagnation
    // temperature at M = 1, and labelling them identically would be the single
    // most misleading thing such a table could do. Drawn more quietly than the
    // primary marker, because it is a landmark rather than a limit.
    property int secondaryRow: -1
    property string secondaryLabel: ""
    property int selectedRow: -1
    // Minimum width for a value column; the first column is narrower.
    property real columnWidth: 132
    property real firstColumnWidth: 96
    property real rowHeight: 26
    property bool showRegionEdge: true

    signal rowClicked(int row)
    signal rowActivated(int row)

    readonly property real headerHeight: 34
    readonly property int columnCount: columns.length

    // ---- marker gutter --------------------------------------------------
    // A marker label is drawn in the row's left margin. Short ones - "SONIC",
    // "CHOKED" - fit in the space the first column's own padding already
    // leaves. Longer ones do not, and a label printed across a Mach number is
    // worse than no label at all. So the grid is offset by exactly what the
    // longest marker needs beyond the room already there, measured against the
    // marked row's own first cell rather than guessed. Tables whose labels
    // already fit get a gutter of zero and do not move.
    property int modelEpoch: 0

    Connections {
        target: root.model
        ignoreUnknownSignals: true
        function onModelReset() { root.modelEpoch += 1 }
        function onLayoutChanged() { root.modelEpoch += 1 }
    }

    TextMetrics {
        id: markedMetrics
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: Typography.sectionTracking
        text: root.markedRow >= 0 ? root.markedLabel : ""
    }

    TextMetrics {
        id: secondaryMetrics
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: Typography.sectionTracking
        text: root.secondaryRow >= 0 ? root.secondaryLabel : ""
    }

    TextMetrics {
        id: markedCellMetrics
        font.family: Typography.mono
        font.pixelSize: Typography.bodySmall
        text: {
            root.modelEpoch          // recompute when the model is rebuilt
            var primary = root.markedRow >= 0 ? root.cellText(root.markedRow, 0) : ""
            var second = root.secondaryRow >= 0 ? root.cellText(root.secondaryRow, 0) : ""
            return second.length > primary.length ? second : primary
        }
    }

    readonly property real markerLabelWidth: Math.max(markedMetrics.width, secondaryMetrics.width)
    readonly property real markerGutter: {
        if (markerLabelWidth <= 0)
            return 0
        // A right-aligned first column parks its text at the column's right
        // edge, so the label can borrow the padding already there and only the
        // shortfall becomes gutter. A LEFT-aligned first column starts its
        // text at the left edge -- exactly where the label is drawn -- so the
        // whole label needs room of its own, or the two print on top of each
        // other. That is what happened to "CONDENSED" over "C(gr)".
        if (alignsLeft(0))
            return Metrics.spacing.s + markerLabelWidth + Metrics.spacing.m
        return Math.max(
            0,
            Metrics.spacing.s + markerLabelWidth + Metrics.spacing.m
            + markedCellMetrics.width + Metrics.spacing.m - firstColumnWidth)
    }

    // What is left for the value columns once the first column and any marker
    // gutter have taken their share. Pages size their columns from this, so a
    // gutter can never push the last column out of view.
    readonly property real valueAreaWidth: Math.max(0, width - firstColumnWidth - markerGutter)

    function widthFor(column) {
        return column === 0 ? firstColumnWidth : columnWidth
    }

    // The model returns undefined between a reset and the delegate rebuild,
    // and assigning that to a string property warns once per visible cell.
    function cellText(row, column) {
        if (!model)
            return ""
        var value = model.data(model.index(row, column), Qt.DisplayRole)
        return (value === undefined || value === null) ? "" : String(value)
    }

    // Bring a row into view, roughly a third of the way down so the rows
    // around it are visible too - the context is usually the point.
    function scrollToRow(row) {
        if (!model || row < 0)
            return
        var target = row * rowHeight - body.height / 3
        body.contentY = Math.max(0, Math.min(target, Math.max(0, body.contentHeight - body.height)))
    }

    function totalWidth() {
        var total = markerGutter
        for (var i = 0; i < columnCount; ++i)
            total += widthFor(i)
        return total
    }

    // ---- header ---------------------------------------------------------
    Rectangle {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: root.headerHeight
        color: Theme.surfaceSubtle
        z: 2

        Item {
            anchors.fill: parent
            anchors.leftMargin: root.markerGutter - body.contentX
            clip: false

            Row {
                height: parent.height

                Repeater {
                    model: root.columns

                    delegate: Item {
                        required property var modelData
                        required property int index

                        width: root.widthFor(index)
                        height: header.height

                        // Both sides anchored, so the text has the column's
                        // width and can elide. Anchored on one side only it
                        // renders at its natural width and a long label prints
                        // across its neighbour -- legible neither as itself nor
                        // as the header it covers.
                        Text {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.rightMargin: Metrics.spacing.m
                            anchors.leftMargin: Metrics.spacing.m
                            anchors.verticalCenter: parent.verticalCenter
                            horizontalAlignment: modelData.align === "left"
                                                 ? Text.AlignLeft
                                                 : Text.AlignRight
                            elide: Text.ElideRight
                            text: modelData.label
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.medium
                        }
                    }
                }
            }
        }

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: Metrics.hairline
            color: Theme.borderStrong
        }
    }

    // ---- body -----------------------------------------------------------
    Flickable {
        id: body
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        clip: true
        contentWidth: Math.max(width, root.totalWidth())
        contentHeight: rows.height
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: RFScrollBar {}
        ScrollBar.horizontal: RFScrollBar { orientation: Qt.Horizontal }

        Column {
            id: rows
            width: body.contentWidth

            Repeater {
                model: root.model

                delegate: Rectangle {
                    id: line
                    required property int index

                    width: rows.width
                    height: root.rowHeight

                    readonly property bool isMarked: index === root.markedRow
                    readonly property bool isSecondary: index === root.secondaryRow
                                                        && index !== root.markedRow
                    readonly property bool isSelected: index === root.selectedRow

                    color: isSelected ? Theme.accentSubtle
                                      : (hover.hovered ? Theme.surfaceHover : "transparent")

                    // The sonic row is annotated, not filled: a bright band
                    // across a numeric table destroys the reading rhythm.
                    Rectangle {
                        visible: line.isMarked && root.showRegionEdge
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 2
                        color: Theme.accent
                    }

                    Rectangle {
                        visible: line.isSecondary && root.showRegionEdge
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 2
                        color: Theme.textSecondary
                    }

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: root.markerGutter

                        Repeater {
                            model: root.columnCount

                            delegate: Item {
                                required property int index
                                width: root.widthFor(index)
                                height: line.height

                                Text {
                                    anchors.right: root.alignsLeft(index)
                                                   ? undefined : parent.right
                                    anchors.left: root.alignsLeft(index)
                                                  ? parent.left : undefined
                                    anchors.rightMargin: Metrics.spacing.m
                                    anchors.leftMargin: Metrics.spacing.m
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: root.cellText(line.index, index)
                                    color: (line.isMarked || line.isSecondary)
                                           ? Theme.text : Theme.textSecondary
                                    // Tabular figures: digits share a width, so
                                    // decimal points line up down the column.
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: (line.isMarked || line.isSecondary)
                                                 ? Typography.medium : Typography.regular
                                }
                            }
                        }
                    }

                    Text {
                        visible: line.isMarked || line.isSecondary
                        anchors.left: parent.left
                        anchors.leftMargin: Metrics.spacing.s
                        anchors.verticalCenter: parent.verticalCenter
                        text: line.isMarked ? root.markedLabel : root.secondaryLabel
                        color: line.isMarked ? Theme.accent : Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.letterSpacing: Typography.sectionTracking
                    }

                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: Metrics.hairline
                        color: Theme.divider
                        opacity: 0.5
                    }

                    HoverHandler { id: hover }

                    TapHandler {
                        onSingleTapped: root.rowClicked(line.index)
                        onDoubleTapped: root.rowActivated(line.index)
                    }
                }
            }
        }
    }
}
