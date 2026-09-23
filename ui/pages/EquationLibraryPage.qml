import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"
import "../data"

/*
 * Equation Library - the reference surface.
 *
 * Entries are static rich text grouped by topic. Nothing is parsed, evaluated
 * or looked up against a solver; the page exists to fix how relations are
 * presented before the modules start pointing at them.
 */
Item {
    id: page

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Equation Library"
            subtitle: "Relations the compressible-flow modules will implement"

            trailing: Component {
                RFStatusChip {
                    text: "Reference only"
                    showDot: false
                }
            }
        }

        RFPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentSpacing: 0

            ScrollView {
                id: scroller
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ScrollBar.vertical: RFScrollBar { policy: ScrollBar.AsNeeded }

                ColumnLayout {
                    // Reference text is held to a readable measure and centred,
                    // rather than stretched across the whole workspace.
                    width: Math.min(880, scroller.availableWidth)
                    x: Math.max(0, (scroller.availableWidth - width) / 2)
                    spacing: Metrics.spacing.s

                    Repeater {
                        model: MockData.equationEntries

                        delegate: ColumnLayout {
                            required property var modelData
                            required property int index

                            readonly property bool startsGroup:
                                index === 0 || MockData.equationEntries[index - 1].group !== modelData.group

                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            RFSectionLabel {
                                visible: parent.startsGroup
                                readonly property string plainText: modelData.group
                                text: Notation.sectionRich(plainText)
                                textFormat: Notation.textFormat(plainText)
                                Layout.topMargin: index === 0 ? 0 : Metrics.spacing.l
                                Layout.bottomMargin: Metrics.spacing.xs
                            }

                            Text {
                                Layout.fillWidth: true
                                text: Notation.rich(modelData.name)
                                textFormat: Notation.textFormat(modelData.name)
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }

                            RFEquationBlock {
                                Layout.fillWidth: true
                                equation: modelData.body
                            }
                        }
                    }

                    Item { Layout.preferredHeight: Metrics.spacing.s }
                }
            }
        }
    }
}
