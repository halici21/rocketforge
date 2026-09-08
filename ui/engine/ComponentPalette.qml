import QtQuick
import QtQuick.Controls
import "../theme"
import "../components"
import "model"
import "visuals"

/*
 * The component palette: every physical part the canvas can hold, grouped the
 * way a propulsion engineer would look for them, with a filter across names
 * and categories.
 *
 * The list is generated from ComponentRegistry, so a new component type
 * appears here without touching this file.
 */
Item {
    id: root

    property Item dragLayer: null
    property Item canvas: null

    readonly property string query: search.text.trim().toLowerCase()

    function matches(definition) {
        if (query === "")
            return true
        return definition.displayName.toLowerCase().indexOf(query) >= 0
                || definition.type.indexOf(query) >= 0
                || ComponentRegistry.categoryLabel(definition.category).toLowerCase().indexOf(query) >= 0
    }

    readonly property int matchCount: {
        var n = 0
        for (var i = 0; i < ComponentRegistry.types.length; ++i) {
            if (matches(ComponentRegistry.types[i]))
                ++n
        }
        return n
    }

    // ---- search ----------------------------------------------------------

    Item {
        id: searchRow
        x: Metrics.spacing.m
        width: parent.width - Metrics.spacing.m * 2
        height: 40

        RFTextField {
            id: search
            width: parent.width
            anchors.verticalCenter: parent.verticalCenter
            placeholder: "Search components…"
        }
    }

    // ---- catalogue -------------------------------------------------------

    Flickable {
        anchors.top: searchRow.bottom
        anchors.topMargin: Metrics.spacing.xs
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: legend.top
        contentWidth: width
        contentHeight: column.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        ScrollBar.vertical: RFScrollBar {}

        Column {
            id: column
            width: parent.width

            Repeater {
                model: ComponentRegistry.categories

                delegate: Column {
                    id: group
                    required property var modelData

                    readonly property var items: {
                        var all = ComponentRegistry.typesInCategory(modelData.id)
                        return all.filter(function (d) { return root.matches(d) })
                    }

                    width: column.width
                    visible: items.length > 0

                    Item {
                        width: parent.width
                        height: Metrics.navGroupHeight + Metrics.spacing.s

                        RFSectionLabel {
                            x: Metrics.spacing.m + Metrics.spacing.xs
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: Metrics.spacing.xs
                            text: group.modelData.label
                            font.pixelSize: Typography.navGroup
                            font.letterSpacing: Typography.navGroupTracking
                        }
                    }

                    Repeater {
                        model: group.items

                        delegate: ComponentPaletteItem {
                            required property var modelData
                            width: column.width
                            definition: modelData
                            dragLayer: root.dragLayer
                            canvas: root.canvas
                        }
                    }

                    Item { width: 1; height: Metrics.spacing.s }
                }
            }

            // ---- no matches -------------------------------------------------
            Item {
                width: column.width
                height: root.matchCount === 0 ? 120 : 0
                visible: root.matchCount === 0

                Column {
                    anchors.centerIn: parent
                    spacing: Metrics.spacing.xs

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "No components match"
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Try a different term."
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }
        }
    }

    // ---- port legend -----------------------------------------------------
    // The physical domain is carried by shape, so the shapes are named once
    // here rather than being guessed at on the canvas.

    Item {
        id: legend
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: legendColumn.implicitHeight + Metrics.spacing.m * 2

        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: Metrics.hairline
            color: Theme.divider
        }

        Column {
            id: legendColumn
            x: Metrics.spacing.m + Metrics.spacing.xs
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - Metrics.spacing.m * 2
            spacing: Metrics.spacing.s

            RFSectionLabel { text: "Port types" }

            Flow {
                width: parent.width
                spacing: Metrics.spacing.m

                Repeater {
                    model: [
                        { label: "Fluid", domain: "fluid" },
                        { label: "Mech", domain: "mechanical" },
                        { label: "Thermal", domain: "thermal" },
                        { label: "Signal", domain: "signal" }
                    ]

                    delegate: Row {
                        required property var modelData
                        spacing: Metrics.spacing.xs + 2

                        PortShape {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 9
                            height: 9
                            domain: modelData.domain
                            strokeColor: Theme.textMuted
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.label
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }
        }
    }
}
