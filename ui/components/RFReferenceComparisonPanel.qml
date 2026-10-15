import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * RFReferenceComparisonPanel - a compressible table's comparison with its
 * published appendix: the whole-table summary, then the selected row
 * quantity by quantity (RocketForge against the published value, with a
 * PASS / REVIEW chip).
 *
 * `summary` and `rowDetail` come from the controller unchanged; nothing here
 * compares, rounds or interpolates. Used by the Isentropic, Normal Shock and
 * Prandtl-Meyer tables, which pass their own row title and "no published row"
 * sentence, and up to two notes: one above the summary (Isentropic: the
 * citation, or why there is none) and one below it (Normal Shock: what a
 * review means).
 */
RFPanel {
    id: root

    property var summary: ({})
    property var rowDetail: []
    property bool rowSelected: false
    // "Row · M = 2.0000", or "Select a row".
    property string rowTitle: ""
    property string noRowText: ""
    // The "Qty  RocketForge  Anderson" header over the row detail.
    property bool columnHeadings: true
    // The note above the summary; shown only when asked for.
    property bool leadingNoteShown: false
    property string leadingNote: ""
    property bool leadingNoteWarning: false
    // The note below the summary.
    property bool summaryNoteShown: false
    property string summaryNote: ""

    title: "Reference comparison"
    contentSpacing: Metrics.spacing.s

    trailing: Component {
        RFStatusChip {
            text: root.summary.status !== undefined ? root.summary.status : "—"
            tone: root.summary.status === "PASS" ? "success" : "warning"
            showDot: false
        }
    }

    Text {
        Layout.fillWidth: true
        visible: root.leadingNoteShown
        text: root.leadingNote
        wrapMode: Text.WordWrap
        color: root.leadingNoteWarning ? Theme.warning : Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }

    RFSectionLabel { text: "Whole table" }

    Repeater {
        model: [
            { k: "Rows compared", v: root.summary.rows !== undefined ? root.summary.rows : 0 },
            { k: "Values compared", v: root.summary.values !== undefined ? root.summary.values : 0 },
            { k: "Within printed precision", v: root.summary.pass !== undefined ? root.summary.pass : 0 },
            { k: "Needing review", v: root.summary.review !== undefined ? root.summary.review : 0 },
            { k: "Max relative difference", v: root.summary.maxRelative !== undefined ? root.summary.maxRelative : "—" }
        ]

        delegate: RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            Text {
                Layout.fillWidth: true
                text: modelData.k
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
            Text {
                text: String(modelData.v)
                color: Theme.text
                font.family: Typography.mono
                font.pixelSize: Typography.bodySmall
            }
        }
    }

    Text {
        Layout.fillWidth: true
        visible: root.summaryNoteShown
        text: root.summaryNote
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }

    RFDivider {}

    RFSectionLabel {
        text: Notation.sectionRich(root.rowTitle)
        textFormat: Notation.textFormat(root.rowTitle)
    }

    Text {
        Layout.fillWidth: true
        visible: root.rowSelected && root.rowDetail.length === 0
        text: root.noRowText
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }

    RowLayout {
        Layout.fillWidth: true
        visible: root.columnHeadings && root.rowDetail.length > 0
        spacing: Metrics.spacing.s

        Text {
            Layout.preferredWidth: 52
            text: "Qty"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            Layout.fillWidth: true
            text: "RocketForge"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            Layout.preferredWidth: 84
            text: "Anderson"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            Layout.preferredWidth: 44
            text: ""
        }
    }

    Repeater {
        model: root.rowDetail

        delegate: RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            Text {
                Layout.preferredWidth: 52
                text: Notation.rich(modelData.label)
                textFormat: Notation.textFormat(modelData.label)
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
            Text {
                Layout.fillWidth: true
                text: modelData.computed
                color: Theme.text
                font.family: Typography.mono
                font.pixelSize: Typography.bodySmall
            }
            Text {
                Layout.preferredWidth: 84
                text: modelData.reference
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.bodySmall
            }
            RFStatusChip {
                Layout.preferredWidth: 44
                text: modelData.status
                tone: modelData.status === "PASS" ? "success" : "warning"
                showDot: false
            }
        }
    }

    Item { Layout.fillHeight: true }

    Text {
        Layout.fillWidth: true
        text: "Published values are rounded to four significant figures. A difference "
              + "inside that rounding is agreement, not error."
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }
}
