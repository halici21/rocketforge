import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The selected point, top to bottom: its source, what is run, step A, step B,
 * every declaration and warning, and what the source does not give. Nothing
 * is behind a tooltip or a collapsed section (display review §4, §7).
 *
 * Step A and step B are two panels, never one table. A point that stopped
 * shows its reason in place of both, never a partial table. Before a run, step
 * A shows the printout with "not run" beside it, and step B says it has not
 * been run.
 */
ColumnLayout {
    id: root

    spacing: Metrics.spacing.l

    component Prose: Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.bodySmall
    }

    component Lines: Repeater {
        delegate: Text {
            required property string line
            Layout.fillWidth: true
            text: "–  " + line
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }
    }

    // ---- the source ---------------------------------------------------------
    RFPanel {
        Layout.fillWidth: true
        contentSpacing: Metrics.spacing.s

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.m

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: ReferenceCases.pointDocument }
                Text {
                    objectName: "referenceCasesTitle"
                    Layout.fillWidth: true
                    text: ReferenceCases.pointTitle
                    wrapMode: Text.WordWrap
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.readoutLarge
                    font.weight: Typography.medium
                }
            }

            RFStatusChip {
                objectName: "referenceCasesPointState"
                Layout.alignment: Qt.AlignTop
                text: ReferenceCases.pointStateWord
                tone: ReferenceCases.pointState === "ok" || ReferenceCases.pointState === "not-run"
                      ? "neutral" : "warning"
            }
        }

        Text {
            objectName: "referenceCasesClass"
            Layout.fillWidth: true
            text: ReferenceCases.classLine
            wrapMode: Text.WordWrap
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.body
            font.weight: Typography.medium
        }
        Prose { objectName: "referenceCasesCitation"; text: ReferenceCases.citation }
        Prose { text: ReferenceCases.codeLine }
        Prose { text: ReferenceCases.databaseLine }
    }

    // ---- what is run ---------------------------------------------------------
    RFPanel {
        Layout.fillWidth: true
        title: ReferenceCases.inputsHeading
        contentSpacing: Metrics.spacing.xs

        Repeater {
            model: ReferenceCases.runInputs
            delegate: RowLayout {
                required property string inputLabel
                required property string inputText
                Layout.fillWidth: true
                spacing: Metrics.spacing.m
                Text {
                    Layout.preferredWidth: 160
                    text: inputLabel
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
                Text {
                    Layout.fillWidth: true
                    text: inputText
                    wrapMode: Text.WordWrap
                    color: Theme.text
                    font.family: Typography.mono
                    font.pixelSize: Typography.bodySmall
                }
            }
        }
    }

    // ---- step A ---------------------------------------------------------------
    RFPanel {
        objectName: "referenceCasesStepA"
        Layout.fillWidth: true
        title: "Step A — TDK printout beside NASA CEA"
        contentSpacing: Metrics.spacing.s

        Prose { text: ReferenceCases.stepANote }
        Prose {
            objectName: "referenceCasesStopA"
            visible: ReferenceCases.stopped
            text: ReferenceCases.stopMessage
            color: Theme.text
        }
        CaseTable {
            objectName: "referenceCasesStepATable"
            Layout.fillWidth: true
            visible: !ReferenceCases.stopped
            heads: ReferenceCases.stepAHeads
            roles: ["quantity", "printed", "computed", "difference", "kind"]
            shares: [2.2, 3, 3.4, 2.4, 1.2]
            model: ReferenceCases.stepA
        }
    }

    // ---- step B ---------------------------------------------------------------
    RFPanel {
        objectName: "referenceCasesStepB"
        Layout.fillWidth: true
        title: "Step B — RocketForge's constant-gamma reduction beside NASA CEA"
        contentSpacing: Metrics.spacing.s

        Prose { text: ReferenceCases.stepBNote }
        Prose {
            visible: !ReferenceCases.hasRun && !ReferenceCases.stopped
            text: "Not run. Both gamma bases are computed on Run, and shown together."
            color: Theme.text
        }
        Prose {
            objectName: "referenceCasesStopB"
            visible: ReferenceCases.stopped
            text: ReferenceCases.stopMessage
            color: Theme.text
        }
        CaseTable {
            objectName: "referenceCasesStepBTable"
            Layout.fillWidth: true
            visible: ReferenceCases.hasRun && !ReferenceCases.stopped
            heads: ReferenceCases.stepBHeads
            roles: ["basis", "rocketforge", "cea", "difference", "kind"]
            shares: [1.6, 2.4, 3.6, 2.6, 1.6]
            model: ReferenceCases.stepB
        }
    }

    // ---- declarations and warnings -------------------------------------------
    RFPanel {
        objectName: "referenceCasesDeclarations"
        Layout.fillWidth: true
        title: "Declarations"
        contentSpacing: Metrics.spacing.xs

        Lines { model: ReferenceCases.declarations }

        RFSectionLabel {
            Layout.topMargin: Metrics.spacing.s
            text: "Provider warnings"
        }
        Prose {
            visible: !ReferenceCases.hasRun || ReferenceCases.stopped
            text: ReferenceCases.stopped ? "None reported: the point stopped before its results."
                                         : "Not run."
        }
        Lines { model: ReferenceCases.warnings }
    }

    // ---- what the source does not give ---------------------------------------
    RFPanel {
        objectName: "referenceCasesMissing"
        Layout.fillWidth: true
        title: "What the source does not give"
        contentSpacing: Metrics.spacing.xs

        Lines { model: ReferenceCases.missing }
        Prose {
            Layout.topMargin: Metrics.spacing.s
            text: ReferenceCases.notes
        }
    }
}
