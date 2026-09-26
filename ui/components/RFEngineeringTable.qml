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
 *
 * Interaction (opt-in, `interactive: true`) -- the shared table contract:
 *
 *   click            select a row (rowClicked)
 *   Shift + click    extend a row range from the last selected row
 *   drag (Range)     select a range; ranges snap to whole rows
 *   Ctrl + wheel     visual zoom 0.8x - 1.6x (row height, figures, widths)
 *   middle drag      pan
 *   Up / Down        move the selected row; with Shift, grow the range
 *   Return           open the analysis lens on the range
 *   Esc              leave the lens, else clear the range
 *
 * The lens shows only the chosen rows, a little larger, between two quiet
 * strips that count what is outside it; RFTableToolbar names it in a
 * breadcrumb ("Full table > M 1.80 - 2.20"). All of it is view state over the
 * model's rows: nothing is recomputed, reformatted or re-solved.
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

    function isSpeciesColumn(column) {
        return column >= 0 && column < columns.length
               && columns[column].key === "species"
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

    // ---- interaction (opt-in) ------------------------------------------------
    property bool interactive: false
    property string tool: "select"          // select | range
    property real zoom: 1.0
    readonly property real minZoom: 0.8
    readonly property real maxZoom: 1.6
    property int rangeFirst: -1
    property int rangeLast: -1
    property int lensFirst: -1
    property int lensLast: -1
    property int anchorRow: -1
    property int hoverRow: -1
    readonly property bool hasRange: rangeFirst >= 0 && rangeLast >= rangeFirst
    readonly property bool lensActive: lensFirst >= 0 && lensLast >= lensFirst
    // The lens reads a little larger than the table it came from.
    readonly property real viewZoom: lensActive ? Math.min(maxZoom, zoom * 1.15) : zoom
    readonly property real effRowHeight: Math.round(rowHeight * viewZoom)
    readonly property real cellFont: Math.round(Typography.bodySmall * viewZoom * 10) / 10
    readonly property real firstWidth: firstColumnWidth * viewZoom
    readonly property real stripHeight: 24
    readonly property int modelRows: { root.modelEpoch; return model ? model.rowCount() : 0 }
    // What the view shows: every row, or the lens's rows from lensFirst.
    readonly property int rowOffset: lensActive ? lensFirst : 0
    readonly property int shownRows: lensActive ? lensLast - lensFirst + 1 : modelRows

    signal rangeSelected(int first, int last)
    signal escapePressed()

    function setZoom(z) {
        root.zoom = Math.max(root.minZoom, Math.min(root.maxZoom, Math.round(z * 20) / 20))
    }
    function selectRange(first, last) {
        var n = root.modelRows
        if (n <= 0)
            return
        var a = Math.max(0, Math.min(n - 1, Math.min(first, last)))
        var b = Math.max(0, Math.min(n - 1, Math.max(first, last)))
        root.rangeFirst = a
        root.rangeLast = b
        root.rangeSelected(a, b)
    }
    function clearRange() { root.rangeFirst = -1; root.rangeLast = -1 }
    function enterLens(first, last) {
        if (first < 0 || last < first)
            return
        root.lensFirst = first
        root.lensLast = last
        lensArrival.restart()
        body.forceLayout()
        body.positionViewAtBeginning()
    }
    function exitLens() {
        if (!root.lensActive)
            return
        var keep = root.lensFirst
        root.lensFirst = -1
        root.lensLast = -1
        lensArrival.restart()
        root.scrollToRow(root.selectedRow >= 0 ? root.selectedRow : keep)
    }
    // The model row under a point of the view's content (a lens strip, or
    // nothing, is -1), and bringing a row into view.
    function rowAtContent(x, y) {
        var i = body.indexAt(x, y)
        return i < 0 ? -1 : root.rowOffset + i
    }
    function showRow(row, mode) {
        if (row < root.rowOffset || row >= root.rowOffset + root.shownRows)
            return
        body.positionViewAtIndex(row - root.rowOffset, mode)
    }

    // A column may also carry `caption`: a word under its symbol ("Density
    // ratio" under "ρ₀/ρ"). Symbols that differ by one glyph -- p and ρ in
    // an italic at header size -- read as the same column; the word does not
    // depend on the glyph. The header grows a line only when a column has one.
    readonly property bool hasCaptions: {
        for (var i = 0; i < columns.length; ++i)
            if (columns[i].caption)
                return true
        return false
    }
    readonly property real headerHeight: hasCaptions ? 48 : 34
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
            + markedCellMetrics.width + Metrics.spacing.m - root.firstWidth)
    }

    // What is left for the value columns once the first column and any marker
    // gutter have taken their share. Pages size their columns from this, so a
    // gutter can never push the last column out of view.
    readonly property real valueAreaWidth: Math.max(0, width - root.firstWidth - markerGutter)

    // `columnWidth` is the FLOOR, which is what its own comment always said
    // and what widthFor() never did: it returned the floor as the exact
    // width, so seven 132px columns used 1020 of 1800 available pixels while
    // "Chamber temperature T_c" elided to "Chamber temperatur..." -- a table
    // truncating its own headers beside 800px of empty space (captured in
    // acceptance/analysis_experience_r2_implementation/trade_study/).
    //
    // Leftover width is now shared out across the value columns. When the
    // columns genuinely do not fit, the floor wins and the table scrolls
    // horizontally exactly as before.
    readonly property int valueColumnCount: Math.max(0, columnCount - 1)
    readonly property real distributedColumnWidth:
        valueColumnCount <= 0 ? columnWidth * root.viewZoom
                              : Math.max(columnWidth * root.viewZoom, valueAreaWidth / valueColumnCount)

    function widthFor(column) {
        return column === 0 ? root.firstWidth : distributedColumnWidth
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
        if (root.lensActive && (row < root.lensFirst || row > root.lensLast)) {
            // a row outside the lens: leave the lens rather than hide the row
            root.lensFirst = -1
            root.lensLast = -1
        }
        // the row and the rows around it -- the context is usually the point
        body.forceLayout()
        root.showRow(row, ListView.Center)
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
                        Column {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.rightMargin: Metrics.spacing.m
                            anchors.leftMargin: Metrics.spacing.m
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 1

                            Text {
                                width: parent.width
                                horizontalAlignment: modelData.align === "left"
                                                     ? Text.AlignLeft
                                                     : Text.AlignRight
                                elide: Text.ElideRight
                                // RichText does not elide; a label carrying notation is clipped
                                // to its width instead of running into its neighbour.
                                clip: true
                                text: Notation.rich(modelData.label)
                                textFormat: Notation.textFormat(modelData.label)
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.medium
                            }
                            Text {
                                width: parent.width
                                visible: !!modelData.caption
                                horizontalAlignment: modelData.align === "left"
                                                     ? Text.AlignLeft
                                                     : Text.AlignRight
                                elide: Text.ElideRight
                                text: modelData.caption ? modelData.caption : ""
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
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
    // Virtualized: a ListView over the row indices builds only the rows in
    // view (and a small cache), and recycles them as they scroll. A Repeater
    // of every row made a 20 000-point study (MAX_STUDY_POINTS) into some
    // 200 000 text items. The lens is an offset and a count over the same
    // rows -- rows outside it are not hidden delegates, they are not built.
    ListView {
        id: body
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        clip: true
        model: root.shownRows
        reuseItems: true
        cacheBuffer: Math.round(8 * root.effRowHeight)
        contentWidth: Math.max(width, root.totalWidth())
        flickableDirection: Flickable.AutoFlickIfNeeded
        boundsBehavior: Flickable.StopAtBounds
        // a range drag is not a flick
        interactive: !(root.interactive && (root.tool === "range" || pointer.dragging))

        // Entering or leaving the lens: the rows arrive rather than jump.
        NumberAnimation on opacity {
            id: lensArrival
            running: false
            from: 0.35; to: 1
            duration: Motion.focus
            easing.type: Motion.standard
        }

        ScrollBar.vertical: RFScrollBar {}
        ScrollBar.horizontal: RFScrollBar { orientation: Qt.Horizontal }

        // The lens's context: what lies above and below it, counted, quiet.
        header: RFTableLensStrip {
            table: root
            visible: root.lensActive && root.lensFirst > 0
            width: body.contentWidth
            height: visible ? root.stripHeight : 0
            count: root.lensFirst
            edgeRow: root.lensFirst - 1
            direction: "above"
        }
        footer: RFTableLensStrip {
            table: root
            visible: root.lensActive && root.lensLast < root.modelRows - 1
            width: body.contentWidth
            height: visible ? root.stripHeight : 0
            count: root.modelRows - 1 - root.lensLast
            edgeRow: root.lensLast + 1
            direction: "below"
        }

        delegate: Rectangle {
            id: line
            // `index` is the position in the view; `row` is the model row
            // (the lens starts at lensFirst).
            required property int index
            readonly property int row: root.rowOffset + index

            width: body.contentWidth
            height: root.effRowHeight

            readonly property bool isMarked: row === root.markedRow
            readonly property bool isSecondary: row === root.secondaryRow
                                                && row !== root.markedRow
            readonly property bool isSelected: row === root.selectedRow
            readonly property bool inRange: root.hasRange && row >= root.rangeFirst
                                            && row <= root.rangeLast
            readonly property bool hovered: root.interactive ? row === root.hoverRow
                                                             : hover.hovered

            // A range is a quiet tint with a rule at each end: an
            // interval, not a block of selections.
            color: isSelected ? Theme.accentSubtle
                 : inRange ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.07)
                 : (hovered ? Theme.surfaceHover : "transparent")

            Rectangle {
                visible: line.inRange && line.row === root.rangeFirst
                anchors.top: parent.top
                width: parent.width
                height: 1
                color: Theme.accent
                opacity: 0.6
            }
            Rectangle {
                visible: line.inRange && line.row === root.rangeLast
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Theme.accent
                opacity: 0.6
            }

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
                            // Only a species column gets formula
                            // subscripts; every other cell is a number
                            // or a word and is shown exactly as given.
                            readonly property bool speciesCell: root.isSpeciesColumn(index)
                            // re-read when the model is rebuilt (a recycled
                            // row is told only its index)
                            readonly property string raw: { root.modelEpoch; return root.cellText(line.row, index) }
                            text: speciesCell ? Notation.species(raw) : raw
                            textFormat: speciesCell ? Notation.speciesFormat(raw) : Text.PlainText
                            color: (line.isMarked || line.isSecondary)
                                   ? Theme.text : Theme.textSecondary
                            // Tabular figures: digits share a width, so
                            // decimal points line up down the column.
                            font.family: Typography.mono
                            font.pixelSize: root.cellFont
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
                text: Notation.rich(line.isMarked ? root.markedLabel : root.secondaryLabel)
                textFormat: Notation.textFormat(line.isMarked ? root.markedLabel : root.secondaryLabel)
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

            HoverHandler { id: hover; enabled: !root.interactive }

            TapHandler {
                enabled: !root.interactive
                onSingleTapped: root.rowClicked(line.row)
                onDoubleTapped: root.rowActivated(line.row)
            }
        }

        // One pointer surface for every row of an interactive table (instead
        // of a handler per row): select, Shift-extend, range drag, pan. It
        // lies over the whole content, lens strips included, and asks the
        // view which row is under the pointer.
        MouseArea {
            id: pointer
            parent: body.contentItem
            enabled: root.interactive
            visible: root.interactive
            x: 0
            y: body.originY
            z: 10
            width: body.contentWidth
            height: Math.max(body.contentHeight, body.height)
            hoverEnabled: root.interactive
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
            cursorShape: panning ? Qt.ClosedHandCursor
                       : root.tool === "range" ? Qt.SplitVCursor : Qt.ArrowCursor
            property bool dragging: false
            property bool panning: false
            property int dragAnchor: -1
            property point last

            function rowUnder(m) { return root.rowAtContent(m.x + pointer.x, m.y + pointer.y) }

            onPressed: function (m) {
                root.forceActiveFocus()
                last = Qt.point(m.x, m.y)
                if (m.button === Qt.MiddleButton) {
                    panning = true
                    return
                }
                var row = rowUnder(m)
                if (row < 0) {
                    // a lens context strip: leave the lens
                    if (root.lensActive)
                        root.exitLens()
                    return
                }
                if (root.tool === "range" || (m.modifiers & Qt.ShiftModifier)) {
                    dragging = true
                    preventStealing = true
                    dragAnchor = (m.modifiers & Qt.ShiftModifier) && root.anchorRow >= 0
                                 ? root.anchorRow : row
                    root.rangeFirst = Math.min(dragAnchor, row)
                    root.rangeLast = Math.max(dragAnchor, row)
                }
            }
            onPositionChanged: function (m) {
                if (panning) {
                    var maxX = Math.max(0, body.contentWidth - body.width)
                    var minY = body.originY
                    var maxY = body.originY + Math.max(0, body.contentHeight - body.height)
                    body.contentX = Math.max(0, Math.min(maxX, body.contentX - (m.x - last.x)))
                    body.contentY = Math.max(minY, Math.min(maxY, body.contentY - (m.y - last.y)))
                    return
                }
                var row = rowUnder(m)
                root.hoverRow = row
                if (dragging && row >= 0) {
                    root.rangeFirst = Math.min(dragAnchor, row)
                    root.rangeLast = Math.max(dragAnchor, row)
                }
            }
            onExited: root.hoverRow = -1
            onReleased: function (m) {
                if (panning) {
                    panning = false
                    return
                }
                if (dragging) {
                    dragging = false
                    preventStealing = false
                    if (root.rangeLast > root.rangeFirst) {
                        root.selectRange(root.rangeFirst, root.rangeLast)
                    } else {
                        // a drag that never left its row is a click
                        var single = root.rangeFirst
                        root.clearRange()
                        root.anchorRow = single
                        root.rowClicked(single)
                    }
                    return
                }
                var row = rowUnder(m)
                if (row >= 0 && m.button === Qt.LeftButton) {
                    root.clearRange()
                    root.anchorRow = row
                    root.rowClicked(row)
                }
            }
            onDoubleClicked: function (m) {
                var row = rowUnder(m)
                if (row >= 0)
                    root.rowActivated(row)
            }
            onWheel: function (w) {
                if (w.modifiers & Qt.ControlModifier) {
                    root.setZoom(root.zoom + (w.angleDelta.y > 0 ? 0.1 : -0.1))
                    w.accepted = true
                } else {
                    w.accepted = false
                }
            }
        }
    }

    // Keyboard: the table's own focus, shown as a hairline accent edge so a
    // keyboard user can see which surface the arrows will move.
    Rectangle {
        anchors.fill: parent
        z: 3
        visible: root.interactive && root.activeFocus
        color: "transparent"
        border.width: 1
        border.color: Theme.accent
        opacity: 0.6
    }
    activeFocusOnTab: root.interactive
    Keys.enabled: root.interactive
    Keys.onPressed: function (event) {
        var n = root.modelRows
        if (n <= 0)
            return
        var current = root.selectedRow >= 0 ? root.selectedRow : root.anchorRow
        if (event.key === Qt.Key_Down || event.key === Qt.Key_Up) {
            var step = event.key === Qt.Key_Down ? 1 : -1
            if (event.modifiers & Qt.ShiftModifier) {
                var anchor = root.anchorRow >= 0 ? root.anchorRow : Math.max(0, current)
                var far = root.hasRange ? (root.rangeFirst === anchor ? root.rangeLast : root.rangeFirst)
                                        : anchor
                far = Math.max(0, Math.min(n - 1, far + step))
                root.anchorRow = anchor
                root.selectRange(anchor, far)
                root.showRow(far, ListView.Contain)
            } else {
                var next = Math.max(0, Math.min(n - 1, (current < 0 ? -step : current) + step))
                if (root.lensActive)
                    next = Math.max(root.lensFirst, Math.min(root.lensLast, next))
                root.clearRange()
                root.anchorRow = next
                root.rowClicked(next)
                root.showRow(next, ListView.Contain)
            }
            event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            if (root.hasRange) {
                root.enterLens(root.rangeFirst, root.rangeLast)
                event.accepted = true
            }
        } else if (event.key === Qt.Key_Escape) {
            if (root.lensActive)
                root.exitLens()
            else if (root.hasRange)
                root.clearRange()
            else
                root.escapePressed()
            event.accepted = true
        } else if ((event.modifiers & Qt.ControlModifier)
                   && (event.key === Qt.Key_Plus || event.key === Qt.Key_Equal)) {
            root.setZoom(root.zoom + 0.1); event.accepted = true
        } else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_Minus) {
            root.setZoom(root.zoom - 0.1); event.accepted = true
        } else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_0) {
            root.setZoom(1.0); event.accepted = true
        }
    }
}
