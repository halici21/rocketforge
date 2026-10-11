import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * The selected engine configuration, as the object of the page.
 *
 * Identity first; then the five capabilities, each its own cell with its own
 * status word and shape, never counted or combined; then what the performance
 * reference lacks, in the backend's words; then the configuration's own
 * recorded values, grouped so that a design value, a limit or a qualification
 * life never sits among the operating values; then the topology; then what is
 * recorded only for the variant or family (context, not this configuration's
 * value); then the sources. Every word is the controller's; clicking any row
 * inspects it.
 */
ColumnLayout {
    id: root

    spacing: Metrics.spacing.l

    function inspectAssertion(id) { ReferenceEngines.inspectAssertion(id); ShellContext.inspectorOpen = true }

    // ---- identity ----------------------------------------------------------
    RFPanel {
        Layout.fillWidth: true
        contentSpacing: Metrics.spacing.s

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.m

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: "Engine configuration" }

                Text {
                    objectName: "engineRecordTitle"
                    Layout.fillWidth: true
                    text: ReferenceEngines.recordTitle
                    wrapMode: Text.WordWrap
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.readoutLarge
                    font.weight: Typography.medium
                }
                Text {
                    objectName: "engineRecordId"
                    text: ReferenceEngines.selectedConfigurationId
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.bodySmall
                }
            }

            RFToolButton {
                objectName: "engineProvenanceButton"
                Layout.alignment: Qt.AlignTop
                text: "Identity and sources  ›"
                tooltip: "Open the configuration's lineage, operating points and cited sources in the Inspector"
                checked: ShellContext.inspectorOpen && ReferenceEngines.inspectionKind === ""
                onClicked: {
                    ReferenceEngines.inspectRecord()
                    ShellContext.inspectorOpen = true
                }
            }
        }

        Text {
            objectName: "engineLineage"
            Layout.fillWidth: true
            text: ReferenceEngines.lineage
                  + (ReferenceEngines.aliases !== "" ? "  ·  also called " + ReferenceEngines.aliases : "")
            wrapMode: Text.WordWrap
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.body
        }
        Text {
            objectName: "engineEffective"
            Layout.fillWidth: true
            text: "Applies: " + ReferenceEngines.effective
            wrapMode: Text.WordWrap
            color: ReferenceEngines.effectiveKnown ? Theme.textSecondary : Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }
        Text {
            Layout.fillWidth: true
            visible: ReferenceEngines.recordNotes !== ""
            text: ReferenceEngines.recordNotes
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
        }
        Repeater {
            model: ReferenceEngines.operatingPoints
            delegate: Text {
                required property string pointId
                required property string pointLabel
                Layout.fillWidth: true
                text: "Operating point  ·  " + pointLabel + "  (" + pointId + ")"
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }
    }

    // ---- the five capabilities, independently ------------------------------
    ColumnLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        RFSectionLabel { text: "What this record can support, per capability" }

        GridLayout {
            objectName: "engineCapabilityStrip"
            Layout.fillWidth: true
            // Five cells in a row while each keeps a readable width; below that
            // a deliberate 3 + 2, then 2 + 2 + 1 -- never smaller type.
            columns: root.width >= 1150 ? 5 : root.width >= 760 ? 3 : 2
            columnSpacing: Metrics.spacing.s
            rowSpacing: Metrics.spacing.s

            Repeater {
                model: ReferenceEngines.capabilities

                delegate: Rectangle {
                    id: cell
                    required property string capability
                    required property string name
                    required property string status
                    required property string statusLabel
                    required property string glyph
                    required property string summary
                    required property int more

                    readonly property bool inspected: ReferenceEngines.inspectionKind === "capability"
                                                      && ReferenceEngines.inspectionKey === cell.capability

                    objectName: "capability_" + cell.capability
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 1
                    implicitHeight: cellColumn.implicitHeight + Metrics.spacing.m * 2
                    radius: Metrics.radius.m
                    // Evidence states, not errors: one neutral surface for all three.
                    color: cell.inspected ? Theme.surfaceHover : cellArea.containsMouse ? Theme.surfaceSubtle : Theme.surface
                    border.width: cell.inspected ? 1.5 : Metrics.hairline
                    border.color: cell.inspected ? Theme.accent : Theme.border
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Button
                    Accessible.name: cell.name + ": " + cell.statusLabel
                    Keys.onReturnPressed: cellArea.clicked(null)
                    Keys.onSpacePressed: cellArea.clicked(null)

                    RFProximityEdge { active: parent.activeFocus }

                    ColumnLayout {
                        id: cellColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: Metrics.spacing.m
                        spacing: Metrics.spacing.xs

                        Text {
                            Layout.fillWidth: true
                            text: cell.name
                            elide: Text.ElideRight
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.weight: Typography.medium
                            font.letterSpacing: Typography.sectionTracking
                        }
                        RowLayout {
                            spacing: Metrics.spacing.s
                            Text {
                                // The status as a shape too, never by colour alone.
                                text: cell.glyph
                                color: Theme.text
                                font.pixelSize: Typography.readoutLarge
                                Layout.alignment: Qt.AlignVCenter
                            }
                            Text {
                                objectName: "capabilityStatus_" + cell.capability
                                text: cell.statusLabel
                                color: Theme.text
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                                font.weight: cell.status === "SUPPORTED" ? Typography.medium : Typography.regular
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: cell.summary !== ""
                            text: cell.summary + (cell.more > 0 ? "  (+" + cell.more + " more)" : "")
                            wrapMode: Text.WordWrap
                            maximumLineCount: 4
                            elide: Text.ElideRight
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                        }
                    }

                    MouseArea {
                        id: cellArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            ReferenceEngines.inspectCapability(cell.capability)
                            ShellContext.inspectorOpen = true
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: "■ Supported   ◧ Partial   □ Not supported  —  evidence states, evaluated one by one. "
                  + "Regression candidate is eligibility only: nothing here is validated or accepted."
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    // ---- what the performance reference lacks --------------------------------
    RFPanel {
        objectName: "engineMissing"
        Layout.fillWidth: true
        visible: ReferenceEngines.missingCount > 0
        title: "Not in this record  ·  performance reference"
        contentSpacing: Metrics.spacing.xs

        Repeater {
            model: ReferenceEngines.missing
            delegate: RowLayout {
                required property string quantity
                required property string reason
                Layout.fillWidth: true
                spacing: Metrics.spacing.m
                Text {
                    Layout.preferredWidth: 170
                    text: quantity !== "" ? quantity : "Gap"
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.medium
                }
                Text {
                    Layout.fillWidth: true
                    text: reason
                    wrapMode: Text.WordWrap
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
            }
        }
        Text {
            Layout.fillWidth: true
            text: "Absent from the shipped record: not zero, not estimated. A value a source withholds is not shown."
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    // ---- the configuration's own recorded values ----------------------------
    RFPanel {
        objectName: "engineFacts"
        Layout.fillWidth: true
        title: "Recorded for this configuration"
        contentSpacing: 0

        Text {
            Layout.fillWidth: true
            visible: ReferenceEngines.factCount === 0
            text: "Nothing is recorded at the configuration itself. Anything recorded for its variant or family is listed below as context."
            wrapMode: Text.WordWrap
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }

        Repeater {
            model: ReferenceEngines.facts

            delegate: ColumnLayout {
                id: fact
                required property string assertionId
                required property string groupTitle
                required property string groupNote
                required property bool groupStart
                required property string field
                required property string valueText
                required property string kind
                required property bool nominal
                required property string conditions
                required property bool hasConditions
                required property string point
                required property bool hasPoint
                required property string recorded
                required property string unitNote

                readonly property bool inspected: ReferenceEngines.inspectionKind === "assertion"
                                                  && ReferenceEngines.inspectionKey === fact.assertionId

                Layout.fillWidth: true
                spacing: 0

                ColumnLayout {
                    visible: fact.groupStart
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.m
                    Layout.bottomMargin: Metrics.spacing.xs
                    spacing: 1
                    RFSectionLabel { text: fact.groupTitle }
                    Text {
                        Layout.fillWidth: true
                        visible: fact.groupNote !== ""
                        text: fact.groupNote
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                Rectangle {
                    objectName: "fact_" + fact.assertionId
                    Layout.fillWidth: true
                    implicitHeight: factRow.implicitHeight + Metrics.spacing.s * 2
                    radius: Metrics.radius.s
                    color: fact.inspected ? Theme.surfaceHover : factArea.containsMouse ? Theme.surfaceSubtle : "transparent"
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Button
                    Accessible.name: fact.field + ": " + fact.valueText
                    Keys.onReturnPressed: root.inspectAssertion(fact.assertionId)
                    Keys.onSpacePressed: root.inspectAssertion(fact.assertionId)
                    RFProximityEdge { active: parent.activeFocus }

                    RowLayout {
                        id: factRow
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: Metrics.spacing.s
                        anchors.rightMargin: Metrics.spacing.s
                        spacing: Metrics.spacing.m

                        Text {
                            readonly property real fieldWidth: Math.min(260, root.width * 0.26)
                            Layout.preferredWidth: fieldWidth
                            Layout.maximumWidth: fieldWidth
                            Layout.alignment: Qt.AlignTop
                            text: fact.field
                            wrapMode: Text.WrapAnywhere
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                Layout.fillWidth: true
                                text: fact.valueText
                                wrapMode: Text.WordWrap
                                color: Theme.text
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: fact.recorded !== ""
                                text: "Recorded as: " + fact.recorded
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: fact.unitNote !== ""
                                text: fact.unitNote
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: fact.hasConditions
                                text: fact.conditions
                                wrapMode: Text.WordWrap
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: fact.hasPoint
                                text: "At " + fact.point
                                wrapMode: Text.WordWrap
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }
                        Text {
                            Layout.alignment: Qt.AlignTop
                            Layout.preferredWidth: 96
                            horizontalAlignment: Text.AlignRight
                            text: fact.kind
                            color: fact.nominal ? Theme.textMuted : Theme.text
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.weight: fact.nominal ? Typography.regular : Typography.medium
                        }
                    }
                    MouseArea {
                        id: factArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.inspectAssertion(fact.assertionId)
                    }
                }
            }
        }
    }

    // ---- topology --------------------------------------------------------------
    RFPanel {
        objectName: "engineTopology"
        Layout.fillWidth: true
        title: "Topology"
        contentSpacing: Metrics.spacing.s
        trailing: Component {
            Row {
                spacing: Metrics.spacing.s
                RFToolButton {
                    visible: ReferenceEngines.graphCount > 0
                    text: "About this graph  ›"
                    tooltip: "Its drawings, text sources, omissions and layout in the Inspector"
                    checked: ShellContext.inspectorOpen && ReferenceEngines.inspectionKind === "graph"
                    onClicked: { ReferenceEngines.inspectGraph(); ShellContext.inspectorOpen = true }
                }
            }
        }

        RFSegmentedControl {
            visible: ReferenceEngines.graphCount > 1
            model: {
                var labels = []
                for (var i = 0; i < ReferenceEngines.graphCount; ++i) labels.push("Graph " + (i + 1))
                return labels
            }
            currentIndex: ReferenceEngines.graphIndex
            onSelected: function (index) { ReferenceEngines.selectGraph(index) }
        }

        Text {
            objectName: "engineTopologyTitle"
            Layout.fillWidth: true
            visible: ReferenceEngines.graphCount > 0
            text: ReferenceEngines.graphTitle + "  ·  " + ReferenceEngines.graphId
            wrapMode: Text.WordWrap
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.body
            font.weight: Typography.medium
        }

        EngineTopologyView {
            Layout.fillWidth: true
            visible: ReferenceEngines.graphCount > 0
        }

        // No graph ships: said plainly, with nothing drawn in its place.
        Item {
            objectName: "engineNoTopology"
            Layout.fillWidth: true
            visible: ReferenceEngines.graphCount === 0
            implicitHeight: 96
            RFDashedFrame { anchors.fill: parent; radius: Metrics.radius.m }
            Column {
                anchors.centerIn: parent
                width: Math.min(parent.width - Metrics.spacing.xl * 2, 560)
                spacing: Metrics.spacing.xs
                Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    text: "No topology ships for this configuration"
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                    font.weight: Typography.medium
                }
                Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    text: "RocketForge draws only graphs built from a cited drawing or text. None is recorded here, so nothing is drawn."
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }

    // ---- context: recorded for the variant or family -------------------------
    RFPanel {
        objectName: "engineContext"
        Layout.fillWidth: true
        visible: ReferenceEngines.contextCount > 0
        title: "Context  ·  recorded for the variant, family or propulsion unit, not this configuration"
        contentSpacing: 0

        Repeater {
            model: ReferenceEngines.context
            delegate: Rectangle {
                id: ctx
                required property string assertionId
                required property string level
                required property string field
                required property string valueText
                required property string kind
                required property bool nominal
                required property string conditions
                required property bool hasConditions

                readonly property bool inspected: ReferenceEngines.inspectionKind === "assertion"
                                                  && ReferenceEngines.inspectionKey === ctx.assertionId
                objectName: "context_" + ctx.assertionId
                Accessible.role: Accessible.Button
                Accessible.name: ctx.level + " context, " + ctx.field + ": " + ctx.valueText
                Layout.fillWidth: true
                implicitHeight: ctxRow.implicitHeight + Metrics.spacing.s * 2
                radius: Metrics.radius.s
                color: ctx.inspected ? Theme.surfaceHover : ctxArea.containsMouse ? Theme.surfaceSubtle : "transparent"
                activeFocusOnTab: true
                Keys.onReturnPressed: root.inspectAssertion(ctx.assertionId)
                Keys.onSpacePressed: root.inspectAssertion(ctx.assertionId)
                RFProximityEdge { active: parent.activeFocus }

                RowLayout {
                    id: ctxRow
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: Metrics.spacing.s
                    anchors.rightMargin: Metrics.spacing.s
                    spacing: Metrics.spacing.m
                    Text {
                        readonly property real fieldWidth: Math.min(260, root.width * 0.26)
                        Layout.preferredWidth: fieldWidth
                        Layout.maximumWidth: fieldWidth
                        Layout.alignment: Qt.AlignTop
                        text: ctx.level + "  ·  " + ctx.field
                        wrapMode: Text.WrapAnywhere
                        color: Theme.textSecondary
                        font.family: Typography.mono
                        font.pixelSize: Typography.meta
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: ctx.valueText
                            wrapMode: Text.WordWrap
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: ctx.hasConditions
                            text: ctx.conditions
                            wrapMode: Text.WordWrap
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                    Text {
                        Layout.alignment: Qt.AlignTop
                        Layout.preferredWidth: 96
                        horizontalAlignment: Text.AlignRight
                        text: ctx.kind
                        color: ctx.nominal ? Theme.textMuted : Theme.text
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        font.weight: ctx.nominal ? Typography.regular : Typography.medium
                    }
                }
                MouseArea {
                    id: ctxArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.inspectAssertion(ctx.assertionId)
                }
            }
        }
    }

    // ---- sources ------------------------------------------------------------
    RFPanel {
        objectName: "engineSources"
        Layout.fillWidth: true
        title: "Sources  ·  technical authority and shipping, separately"
        contentSpacing: 0

        Repeater {
            model: ReferenceEngines.sources
            delegate: Rectangle {
                id: src
                required property string sourceId
                required property string sourceTitle
                required property string line
                required property string authority
                required property string shipping

                readonly property bool inspected: ReferenceEngines.inspectionKind === "source"
                                                  && ReferenceEngines.inspectionKey === src.sourceId
                objectName: "source_" + src.sourceId
                Accessible.role: Accessible.Button
                Accessible.name: "Source " + src.sourceTitle
                Layout.fillWidth: true
                implicitHeight: srcColumn.implicitHeight + Metrics.spacing.s * 2
                radius: Metrics.radius.s
                color: src.inspected ? Theme.surfaceHover : srcArea.containsMouse ? Theme.surfaceSubtle : "transparent"
                activeFocusOnTab: true
                Keys.onReturnPressed: srcArea.clicked(null)
                Keys.onSpacePressed: srcArea.clicked(null)
                RFProximityEdge { active: parent.activeFocus }

                ColumnLayout {
                    id: srcColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: Metrics.spacing.s
                    anchors.rightMargin: Metrics.spacing.s
                    spacing: 2
                    Text {
                        Layout.fillWidth: true
                        text: src.sourceTitle
                        wrapMode: Text.WordWrap
                        color: Theme.text
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                    Text {
                        Layout.fillWidth: true
                        text: src.sourceId + "  ·  " + src.line
                        wrapMode: Text.WordWrap
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.fillWidth: true
                        text: src.authority + "  ·  " + src.shipping
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
                MouseArea {
                    id: srcArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        ReferenceEngines.inspectSource(src.sourceId)
                        ShellContext.inspectorOpen = true
                    }
                }
            }
        }
    }
}
