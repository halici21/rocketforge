import QtQuick
import QtQuick.Layouts
import "../theme"
import "../components"
import "../data"
import "../engine/model"

/*
 * Home, Analysis Experience R2 -- a start surface, not a module list.
 *
 * The pre-R2 Home listed every analysis workspace with its state, which
 * in a fresh session meant five consecutive rows reading "No result yet"
 * and one reading "Not configured": an apologetic inventory of things the
 * user has not done, presented as the product's front door. That was
 * rejected outright by this phase's brief (section 19).
 *
 * What replaces it follows that section's own Option B: continue what is
 * actually in progress, and otherwise offer the families rather than the
 * modules. A workspace appears under Continue only when it genuinely has
 * something to continue -- its own controller says so (WorkspaceState,
 * resultChanged-scoped, never a live input) -- so the list is short, true,
 * and never padded with absence. Families come from the same
 * Navigation.families the rail renders, so the two can never disagree
 * about what this application is made of.
 */
Item {
    id: page

    signal workspaceRequested(int index)
    signal engineRequested()

    readonly property var continuable: {
        var out = []
        var keys = ["thermochem", "performance", "tradestudy",
                    "fluidproperties", "line"]
        for (var i = 0; i < keys.length; ++i) {
            var state = WorkspaceState.stateFor(keys[i])
            if (state.hasResult) {
                var index = Navigation.indexOfKey(keys[i])
                out.push({ key: keys[i], index: index,
                           label: Navigation.items[index].label,
                           text: state.text, stale: state.stale })
            }
        }
        return out
    }

    readonly property bool engineStarted: EngineModel.nodes.count > 0

    readonly property var familyBlurbs: ({
        "compressible": "Isentropic, shock, duct and nozzle relations",
        "thermochem": "Chamber equilibrium from a thermochemistry provider",
        "propulsion": "Ideal rocket performance from a solved chamber",
        "tradestudy": "Parametric sweeps and evaluated design spaces",
        "fluids": "Fluid states and distributed line friction",
        "reference": "Relations the modules implement"
    })

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: column.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        // Two lists of rows, not two columns of prose: the 880px cap that
        // keeps a paragraph readable left roughly half of a 1920 workspace
        // empty and the lists themselves cramped. Side by side when there is
        // room, stacked when there is not, and each side still capped so a
        // row never stretches to the full width of the window.
        GridLayout {
            id: column
            readonly property bool wide: parent.width >= 1400
            width: Math.min(wide ? 1360 : 880,
                            parent.width - Metrics.spacing.h2 * 2)
            x: Metrics.spacing.h2
            y: Metrics.spacing.h2
            columns: wide ? 2 : 1
            columnSpacing: Metrics.spacing.h2
            rowSpacing: Metrics.spacing.xl

            // ---- continue: only what genuinely has something to continue
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                visible: page.continuable.length > 0 || page.engineStarted
                spacing: Metrics.spacing.s

                Text {
                    text: "Continue"
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.pageTitle - 4
                    font.weight: Typography.medium
                }

                Repeater {
                    model: page.continuable

                    delegate: Item {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: 54

                        Rectangle {
                            anchors.fill: parent
                            anchors.leftMargin: -Metrics.spacing.s
                            anchors.rightMargin: -Metrics.spacing.s
                            radius: Metrics.radius.m
                            color: rowHover.hovered ? Theme.surface : "transparent"
                            Behavior on color { ColorAnimation { duration: Motion.fast } }
                        }

                        RowLayout {
                            anchors.fill: parent
                            spacing: Metrics.spacing.l

                            Text {
                                Layout.preferredWidth: 180
                                text: modelData.label
                                color: Theme.text
                                font.family: Typography.sans
                                font.pixelSize: Typography.body + 1
                                font.weight: Typography.medium
                            }

                            Text {
                                Layout.fillWidth: true
                                // Elides rather than running over the "Open"
                                // affordance to its right: the two-column
                                // layout halves the room this had.
                                elide: Text.ElideRight
                                text: modelData.text
                                color: modelData.stale ? Theme.warning : Theme.textSecondary
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutSmall
                            }

                            Text {
                                text: "Open"
                                color: rowHover.hovered ? Theme.accent : Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                                Behavior on color { ColorAnimation { duration: Motion.fast } }
                            }
                        }

                        HoverHandler { id: rowHover; cursorShape: Qt.PointingHandCursor }
                        TapHandler { onTapped: page.workspaceRequested(modelData.index) }
                    }
                }

                Item {
                    Layout.fillWidth: true
                    visible: page.engineStarted
                    implicitHeight: 54

                    Rectangle {
                        anchors.fill: parent
                        anchors.leftMargin: -Metrics.spacing.s
                        anchors.rightMargin: -Metrics.spacing.s
                        radius: Metrics.radius.m
                        color: engineHover.hovered ? Theme.surface : "transparent"
                        Behavior on color { ColorAnimation { duration: Motion.fast } }
                    }

                    RowLayout {
                        anchors.fill: parent
                        spacing: Metrics.spacing.l

                        Text {
                            Layout.preferredWidth: 180
                            text: "Engine Design"
                            color: Theme.text
                            font.family: Typography.sans
                            font.pixelSize: Typography.body + 1
                            font.weight: Typography.medium
                        }

                        Text {
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            text: EngineModel.nodes.count + " component"
                                  + (EngineModel.nodes.count === 1 ? "" : "s") + " · "
                                  + EngineModel.connections.count + " connection"
                                  + (EngineModel.connections.count === 1 ? "" : "s")
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.readoutSmall
                        }

                        Text {
                            text: "Open"
                            color: engineHover.hovered ? Theme.accent : Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                            Behavior on color { ColorAnimation { duration: Motion.fast } }
                        }
                    }

                    HoverHandler { id: engineHover; cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: page.engineRequested() }
                }
            }

            // Separates the two sections only when they are stacked; side
            // by side, the gutter already does that job and a rule between
            // two columns would read as a table border.
            RFDivider {
                Layout.fillWidth: true
                visible: !column.wide
                         && (page.continuable.length > 0 || page.engineStarted)
                Layout.preferredHeight: visible ? implicitHeight : 0
            }

            // ---- start: the families, not the modules ------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                spacing: Metrics.spacing.s

                Text {
                    text: page.continuable.length > 0 || page.engineStarted
                          ? "Start something else" : "Start"
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.pageTitle - 4
                    font.weight: Typography.medium
                }

                Repeater {
                    model: Navigation.families

                    delegate: Item {
                        required property var modelData
                        required property int index
                        readonly property int direct: Navigation.directTargetOf(modelData)

                        Layout.fillWidth: true
                        implicitHeight: 52

                        Rectangle {
                            anchors.fill: parent
                            anchors.leftMargin: -Metrics.spacing.s
                            anchors.rightMargin: -Metrics.spacing.s
                            radius: Metrics.radius.m
                            color: famHover.hovered ? Theme.surface : "transparent"
                            Behavior on color { ColorAnimation { duration: Motion.fast } }
                        }

                        RowLayout {
                            anchors.fill: parent
                            spacing: Metrics.spacing.l

                            Text {
                                Layout.preferredWidth: 180
                                text: modelData.label
                                color: famHover.hovered ? Theme.text : Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                                Behavior on color { ColorAnimation { duration: Motion.fast } }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: page.familyBlurbs[modelData.key] !== undefined
                                      ? page.familyBlurbs[modelData.key] : ""
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                        }

                        HoverHandler { id: famHover; cursorShape: Qt.PointingHandCursor }
                        TapHandler {
                            onTapped: {
                                if (direct !== -1)
                                    page.workspaceRequested(direct)
                                else
                                    page.workspaceRequested(modelData.groups[0].items[0])
                            }
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: Metrics.spacing.h2 }
        }
    }
}
