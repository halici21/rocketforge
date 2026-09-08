import QtQuick
import "../../theme"
import "../../components"
import "../visuals"

/*
 * The identity block every inspector state opens with: the schematic glyph,
 * the name of the thing being inspected, and a row of chips describing what it
 * is and how it stands. Declared once so that a component, a connection and the
 * engine itself all announce themselves in the same shape.
 */
Column {
    id: root

    property string title: ""
    property string glyph: ""
    property color glyphColor: Theme.accent

    // Chips are supplied by the caller: what qualifies a component is not what
    // qualifies a connection.
    default property alias chips: chipRow.data

    width: parent ? parent.width : 0
    spacing: Metrics.spacing.s

    Row {
        width: parent.width
        spacing: Metrics.spacing.s

        ComponentGlyph {
            id: glyphItem
            anchors.verticalCenter: parent.verticalCenter
            width: root.glyph !== "" ? 22 : 0
            height: 22
            visible: width > 0
            glyph: root.glyph
            color: root.glyphColor
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - glyphItem.width
                   - (glyphItem.visible ? Metrics.spacing.s : 0)
            text: root.title
            elide: Text.ElideRight
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.groupLabel + 3
            font.weight: Typography.semibold
        }
    }

    Row {
        id: chipRow
        spacing: Metrics.spacing.s
        visible: children.length > 0
    }
}
